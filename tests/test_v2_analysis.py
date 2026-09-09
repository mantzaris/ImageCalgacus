"""Independent small-vector checks for CPU-only frozen statistical analysis."""
import math
from pathlib import Path
import runpy
import unittest
import numpy as np
helpers=runpy.run_path(str(Path(__file__).resolve().parents[1]/"scripts/analyze_v2.py"))


class ProspectiveAnalysis(unittest.TestCase):
    def test_boundary_binomial_intervals_and_interior_symmetry(self):
        cp=helpers["clopper_pearson"]
        self.assertAlmostEqual(cp(0,1)[1],.975)
        self.assertAlmostEqual(cp(1,1)[0],.025)
        self.assertAlmostEqual(cp(0,20)[1],1-.025**(1/20))
        self.assertAlmostEqual(cp(20,20)[0],.025**(1/20))
        low,high=cp(5,10)
        self.assertAlmostEqual(low,0.1870860284473985)
        self.assertAlmostEqual(high,1-low)
        with self.assertRaises(ValueError):cp(1,0)

    def test_auc_direction_ties_and_weights(self):
        auc=helpers["auc"]
        self.assertEqual(auc([3,4],[1,2]),1)
        self.assertEqual(auc([1,2],[3,4]),0)
        self.assertEqual(auc([1,1],[1,1]),.5)
        self.assertAlmostEqual(auc([1,3],[2],[2,1],[1]),1/3)
        self.assertIsNone(auc([],[]))

    def test_group_draws_keep_strata_and_paired_values(self):
        groups=[dict(stratum=s) for s in ("a","a","b","b")]
        draws=helpers["group_draws"](groups,100,72)
        self.assertEqual(draws.shape,(100,4))
        self.assertTrue(np.all((draws<2).sum(axis=1)==2))
        a=np.array([1,2,3,4]);b=a+5
        self.assertTrue(np.all(a[draws]-b[draws]==-5))
        result=helpers["mean_interval"]([None,0,0,0],draws)
        self.assertEqual(result["n"],3);self.assertEqual(result["mean"],0)
        self.assertEqual(result["grouped_95_interval"],[0,0])

    def test_control_duplicates_owned_once_and_failed_carriers_scored(self):
        groups=[dict(id=g,direction="image-to-text",stratum="one") for g in ("a","b")]
        rows={(g,"fixed"):dict(work_id=g,artifact_saved=True,evidence_valid=True,exact_complete=0,
               diagnostics={"whole":{"log_rank_mean":value}}) for g,value in (("a",1),("b",3))}
        links={g:dict(available=True,scores={"log_rank_mean":2},matched_sha256="same-bytes",trace_id=g) for g in ("a","b")}
        draws=np.array([[0,1],[0,0],[1,1]])
        result=helpers["detection_cell"](groups,"fixed","log_rank_mean",rows,links,draws)
        self.assertEqual(result["auc"],.5)
        self.assertEqual(result["n_stego"],2)
        self.assertEqual(result["n_unique_control_artifacts"],1)
        self.assertEqual(result["failed_deliveries_included"],2)
        self.assertEqual(result["valid_bootstrap_replicates"],2)
        self.assertEqual(result["control_duplicates"][0]["owner_group"],"a")
        links["b"]["scores"]["log_rank_mean"]=3
        with self.assertRaises(ValueError):
            helpers["detection_cell"](groups,"fixed","log_rank_mean",rows,links,draws)


if __name__=="__main__":unittest.main()
