"""Independent interval/bitstream oracle plus explicit partition vectors."""
from fractions import Fraction
import itertools
import unittest
import numpy as np
from imagecalgacus.arithmetic_coding import partition, narrow_and_emit, ArithmeticCoder
from imagecalgacus.entropy_coding import RankCoder, entropy_eligible, calibrate_median

D = (np.arange(4), np.array([.5,.25,.125,.125]), np.arange(4))


def fractional_step(lo,hi,offset_low,offset_high,range_size):
    width = hi-lo
    a,b = lo+width*Fraction(offset_low,range_size), lo+width*Fraction(offset_high,range_size)
    output = ""
    while b <= Fraction(1,2) or a >= Fraction(1,2):
        if b <= Fraction(1,2):
            output += "0"
            a,b = 2*a,2*b
        else:
            output += "1"
            a,b = 2*a-1,2*b-1
    return a,b,output


class ArithmeticTests(unittest.TestCase):
    def test_handwritten_half_open_vectors(self):
        bound=1<<32
        self.assertEqual(narrow_and_emit(0,bound,0,bound//2), (0,bound,"0"))
        self.assertEqual(narrow_and_emit(0,bound,bound//2,bound), (0,bound,"1"))
        self.assertEqual(narrow_and_emit(0,bound,bound//4,3*bound//4), (bound//4,3*bound//4,""))
        self.assertEqual(narrow_and_emit(0,bound,5,6), (0,bound,format(5,"032b")))
        with self.assertRaises(ValueError):
            narrow_and_emit(0,bound,2,2)

    def test_nearest_even_overflow_residual_and_small_support(self):
        ids=np.arange(3); q=np.full(3,1/3)
        sy,cdf,_=partition(ids,q,ids,5)
        self.assertEqual(sy.tolist(),[0,1]); self.assertEqual(cdf.tolist(),[0,3,5])
        sy,cdf,_=partition(ids,q,ids,4)
        self.assertEqual(cdf.tolist(),[0,2,3,4])
        sy,cdf,_=partition(np.arange(2),np.array([.5,.5]),np.arange(2),1)
        self.assertEqual(sy.tolist(),[0]); self.assertEqual(cdf.tolist(),[0,1])
        sy,cdf,_=partition(np.arange(2),np.array([.5,.5]),np.arange(2),5)
        self.assertEqual(cdf.tolist(),[0,3,5])  # 2.5 rounds to 2, then residual goes first

    def test_fractional_oracle_all_small_intervals(self):
        for precision in (3,4,5):
            bound=1<<precision
            for lower in range(bound):
                for upper in range(lower+1,bound+1):
                    # Oracle uses fractions and iterative half comparisons, not XOR/shifts.
                    actual=narrow_and_emit(0,bound,lower,upper,precision)
                    a,b,bits=fractional_step(Fraction(0),Fraction(1),lower,upper,bound)
                    self.assertEqual(actual,(int(a*bound),int(b*bound),bits))

    def test_enumerated_finite_messages_changing_distributions(self):
        distributions=[D,(np.arange(3),np.array([.55,.3,.15]),np.arange(3)),(np.arange(2),np.array([.5,.5]),np.arange(2))]
        for length in range(1,9):
            for value in range(1<<length):
                source=format(value,"0%db"%length)
                enc=ArithmeticCoder(bit_length=length,source_bits=source)
                dec=ArithmeticCoder(bit_length=length)
                lo,hi=Fraction(0),Fraction(1)
                oracle_bits=""
                for position in range(100):
                    dist=distributions[position%len(distributions)]
                    step=enc.prepare(*dist)
                    symbol=enc.select(step)
                    bucket=list(step["symbols"]).index(symbol)
                    lo,hi,bits=fractional_step(lo,hi,int(step["cdf"][bucket]),int(step["cdf"][bucket+1]),enc.upper-enc.lower)
                    oracle_bits+=bits
                    enc.consume(step,symbol)
                    dec.consume(dec.prepare(*dist),symbol)
                    self.assertEqual(enc.bits,oracle_bits)
                    self.assertEqual(dec.bits,oracle_bits)
                    self.assertEqual((enc.lower,enc.upper),(int(lo*(1<<32)),int(hi*(1<<32))))
                    if enc.done:
                        break
                self.assertTrue(enc.done and dec.done)
                self.assertEqual(oracle_bits[:length],source)
                self.assertTrue(set(oracle_bits[length:]) <= {"0"})
                self.assertLessEqual(enc.termination_suffix_bits,31)

    def test_final_suffix_validation_zero_steps_and_truncation(self):
        # Uniform four-symbol bins emit two bits; a one-bit target must discard a zero.
        dist=(np.arange(4),np.full(4,.25),np.arange(4))
        coder=ArithmeticCoder(bit_length=1,source_bits="1")
        step=coder.prepare(*dist)
        self.assertEqual(coder.select(step),2)  # binary .10... not .11...
        coder.consume(step,2)
        self.assertEqual((coder.bits,coder.termination_suffix_bits),("10",1))
        bad=ArithmeticCoder(bit_length=1)
        with self.assertRaisesRegex(ValueError,"suffix"):
            bad.consume(bad.prepare(*dist),3)
        unary=(np.array([7]),np.array([1.0]),np.array([7]))
        stuck=ArithmeticCoder(packet=b"\x00",bit_length=8)
        for _ in range(20):
            step=stuck.prepare(*unary); stuck.consume(step,stuck.select(step))
        self.assertFalse(stuck.done); self.assertEqual(stuck.zero_bit_positions,20)
        with self.assertRaisesRegex(ValueError,"incomplete"):
            stuck.packet()
        short=ArithmeticCoder(packet=b"\xff",bit_length=8)
        for _ in range(3):
            step=short.prepare(*dist); short.consume(step,short.select(step))
        with self.assertRaisesRegex(ValueError,"incomplete"):
            short.packet()

    def test_quantized_midpoint_stagnation_is_capacity_not_flush(self):
        # Explicit independent boundary: width three and uniform-32 -> rounded
        # widths [2,2], second bin overflows, first receives all three integers.
        # The interval straddles 1/2 forever; known finite length cannot flush it.
        bound=1<<32
        dist=(np.arange(32),np.full(32,1/32),np.arange(32))
        symbols,cdf,_=partition(*dist,3)
        self.assertEqual(symbols.tolist(),[0])
        self.assertEqual(cdf.tolist(),[0,3])
        lo,hi=bound//2-2,bound//2+1
        self.assertEqual(narrow_and_emit(lo,hi,0,3),(lo,hi,""))
        a,b,bits=fractional_step(Fraction(lo,bound),Fraction(hi,bound),0,3,3)
        self.assertEqual((a,b,bits),(Fraction(lo,bound),Fraction(hi,bound),""))

    def test_full_packet_with_finite_termination(self):
        packet=bytes(range(256))+bytes(range(36))
        enc,dec=ArithmeticCoder(packet),ArithmeticCoder()
        for _ in range(3000):
            step=enc.prepare(*D); symbol=enc.select(step); enc.consume(step,symbol)
            dec.consume(dec.prepare(*D),symbol)
            if enc.done: break
        self.assertEqual(dec.packet(),packet)
        with self.assertRaisesRegex(ValueError,"already complete"):
            dec.prepare(*D)


class GateTests(unittest.TestCase):
    def test_strict_boundary_and_development_median(self):
        self.assertFalse(entropy_eligible(2,2))
        self.assertFalse(entropy_eligible(np.nextafter(2,-np.inf),2))
        self.assertTrue(entropy_eligible(np.nextafter(2,np.inf),2))
        frozen=calibrate_median([1,2,3,4])
        self.assertEqual(frozen["threshold_bits"],2.5)
        self.assertEqual(float.fromhex(frozen["threshold_hex"]),2.5)

    def test_independent_skip_synchronization_and_capacity(self):
        packet=bytes(292); enc,dec=RankCoder(packet,threshold=3),RankCoder(threshold=3)
        uniform=(np.arange(16),np.full(16,1/16),np.arange(16))
        low=(np.arange(16),np.array([.985]+[.001]*15),np.arange(16))
        rng=np.random.Generator(np.random.PCG64(99))
        for i in range(1200):
            dist=uniform if i%2 else low
            step=enc.prepare(*dist); symbol=enc.select(step,rng); enc.consume(step,symbol)
            dec.consume(dec.prepare(*dist),symbol)
            self.assertEqual(enc.done,dec.done)
            if enc.done: break
        self.assertEqual(dec.packet(),packet)
        self.assertEqual(enc.skipped_positions,584)
        stuck=RankCoder(packet,threshold=4)
        for _ in range(40):
            step=stuck.prepare(*uniform); stuck.consume(step,stuck.select(step,rng))
        self.assertFalse(stuck.done)
        with self.assertRaises(ValueError): stuck.packet()
        with self.assertRaises(ValueError):
            stuck.prepare(np.arange(15),np.full(15,1/15),np.arange(15))


if __name__ == "__main__":
    unittest.main()
