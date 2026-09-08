import os
import struct
import tempfile
import unittest
from pathlib import Path

import numpy as np
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from imagecalgacus.packet import *
from imagecalgacus.fixed_rank import *


class Foundation(unittest.TestCase):
    def setUp(self):
        self.key = bytes(range(32))
        self.nonce = bytes(range(12))
        self.payload = Payload(TEXT, b"Meet me beside the old oak tree.")

    def test_all_byte_vectors(self):
        for byte in range(256):
            expected = [byte // 16 + 1, byte % 16 + 1]
            self.assertEqual(encode_bytes_to_bounded_ranks(bytes([byte])), expected)
            self.assertEqual(decode_bounded_ranks_to_bytes(expected, 1), bytes([byte]))
        self.assertEqual(encode_bytes_to_bounded_ranks(b"\x00\x0f\xf0\xff"), [1, 1, 1, 16, 16, 1, 16, 16])

    def test_packet_offsets_and_sizes(self):
        clear = plaintext(self.payload)
        self.assertEqual(clear[:8], b"\x01\x01\x00\x20\x00\x00\x00\x00")
        self.assertEqual(len(clear), 264)
        self.assertEqual(clear[8:40], self.payload.data)
        self.assertEqual(clear[40:], bytes(224))
        packet = seal(self.payload, self.key, self.nonce)
        self.assertEqual(len(packet), 292)
        self.assertEqual(len(packet_ranks(packet)), 584)
        self.assertEqual(open_packet(packet, self.key, TEXT), self.payload)
        gray = Payload(GRAYSCALE, bytes(range(256)), 16, 16)
        self.assertEqual(plaintext(gray)[:8], b"\x01\x02\x01\x00\x00\x10\x00\x10")
        self.assertEqual(open_packet(seal(gray, self.key, self.nonce), self.key, GRAYSCALE), gray)
        for bad in [packet[:-1], packet + b"x"]:
            with self.assertRaises(ValueError):
                open_packet(bad, self.key, TEXT)

    def test_standard_gcm_vector_and_authentication(self):
        # NIST AES-256 GCM, zero key/IV, one zero plaintext block, no AAD.
        result = AESGCM(bytes(32)).encrypt(bytes(12), bytes(16), b"")
        self.assertEqual(result.hex(), "cea7403d4d606b6e074ec5d3baf39d18d0d1c8a799996bf0265b98b5d48ab919")
        packet = seal(self.payload, self.key, self.nonce)
        for position in [0, 12, 291]:
            bad = bytearray(packet)
            bad[position] ^= 1
            with self.assertRaises(InvalidTag):
                open_packet(bytes(bad), self.key, TEXT)
        with self.assertRaises(InvalidTag):
            open_packet(packet, bytes(32), TEXT)
        with self.assertRaises(InvalidTag):
            AESGCM(self.key).decrypt(packet[:12], packet[12:], b"wrong AAD")

    def test_authenticated_parser_errors(self):
        clear = plaintext(self.payload)
        for bad in [b"\x02" + clear[1:], clear[:2] + b"\xff\xff" + clear[4:],
                    clear[:4] + b"\x00\x10" + clear[6:], clear[:-1] + b"\x01"]:
            packet = self.nonce + AESGCM(self.key).encrypt(self.nonce, bad, AAD)
            with self.assertRaises(ValueError):
                open_packet(packet, self.key, TEXT)
        packet = seal(self.payload, self.key, self.nonce)
        with self.assertRaises(ValueError):
            open_packet(packet, self.key, GRAYSCALE)

    def test_payload_bounds_and_utf8(self):
        for length in [31, 129, 256]:
            with self.assertRaises(ValueError):
                Payload(TEXT, b"a" * length).validate()
        with self.assertRaises(UnicodeDecodeError):
            Payload(TEXT, b"a" * 31 + b"\xff").validate()
        for length in [32, 128]:
            Payload(TEXT, b"a" * length).validate()

    def test_nonce_lifecycle(self):
        outputs = iter([b"k" * 32, b"n" * 12, b"n" * 12, b"m" * 12])
        with tempfile.TemporaryDirectory() as root:
            run = NewRun(Path(root) / "new", lambda count: next(outputs))
            a, b = run.encrypt(self.payload), run.encrypt(self.payload)
            self.assertNotEqual(a[:12], b[:12])
            self.assertEqual((run.directory / "run.key").stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                NewRun(run.directory)
            second = NewRun(Path(root) / "other")
            self.assertNotEqual(second.key, run.key)

    def test_order_support_and_rank_bounds(self):
        self.assertEqual(stable_order([0.1, 2, 2, -1, 0.1]).tolist(), [1, 2, 0, 4, 3])
        ids = np.arange(16)[::-1]
        for rank in range(1, 17):
            self.assertEqual(recover_rank(ids, choose_rank(ids, rank)), rank)
        for bad in [[1] * 583, [1] * 585, [0] * 584, [17] * 584, [1.0] * 584]:
            with self.assertRaises(ValueError):
                decode_bounded_ranks_to_bytes(bad)
        with self.assertRaises(ValueError):
            choose_rank(np.arange(15), 1)
        for bad in [[np.nan], [np.inf], [-np.inf]]:
            with self.assertRaises(ValueError):
                normalized(bad)
        self.assertEqual(normalized([0, -np.inf]).tolist(), [1, 0])


if __name__ == "__main__":
    unittest.main()
