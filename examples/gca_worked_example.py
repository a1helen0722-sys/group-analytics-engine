"""
GCA 手算可验证示例 —— 从 ami_parser 迁移（旧基线）。

Toy meeting (every number below is computable by hand):

    contribution:   1     2     3     4     5
    speaker:        A     A     B     A     C
    vector:       [1,0] [1,0] [1,0] [0,1] [1,0]
    word count:     1     1     3     4     2

spanning_window = 1, speakers sorted [A, B, C].

Hand-derived expectations
-------------------------
Participation:      A = 3/5 = 0.6,  B = 1/5 = 0.2,  C = 1/5 = 0.2

R_1 (row = respondent, col = initiator) — pairs at lag 1:
    (2<-1) A responds to A, cos = 1  ->  R[A, A] = 1
    (3<-2) B responds to A, cos = 1  ->  R[B, A] = 1
    (4<-3) A responds to B, cos = 0  ->  R[A, B] = 0
    (5<-4) C responds to A, cos = 0  ->  R[C, A] = 0
        ->  R_1 = [[1, 0, 0],
                   [1, 0, 0],
                   [0, 0, 0]]

Internal Cohesion (diagonal):        A = 1.0,  B = 0.0,  C = 0.0
Overall Responsivity (row mean, no diagonal):
    A = (0+0)/2 = 0.0,  B = (1+0)/2 = 0.5,  C = 0.0
Social Impact (column mean, no diagonal):
    A = (1+0)/2 = 0.5,  B = (0+0)/2 = 0.0,  C = 0.0

Newness ||n|| / (||n|| + ||g||):
    t1 -> 1.0  (no previous subspace, deterministic)
    t2 -> 0.0  (identical to history)
    t3 -> 0.0  (identical to history)
    t4 -> 1.0  (orthogonal to the x-axis subspace)
    t5 -> 0.0  (inside span(x, y))
    N(A) = (1+0+1)/3 = 2/3,  N(B) = 0.0,  N(C) = 0.0

Density D_t = ||d_t|| / word_count:
    [1, 1, 1/3, 1/4, 1/2]
    D(A) = total norm / total words = 3 / 6 = 0.5
           (mean of A's per-utterance densities would be 0.75)
    D(B) = 1/3,  D(C) = 1/2

Run:  python examples/gca_worked_example.py
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gca_engine.core.config import GCAConfig
from gca_engine.core.metrics import compute_gca_metrics


def _fmt(d: dict) -> str:
    return ", ".join(f"{k}={v:.6g}" for k, v in sorted(d.items()))


def main() -> None:
    cfg = GCAConfig(spanning_window=1)
    result = compute_gca_metrics(
        "TOY",
        speakers=["A", "A", "B", "A", "C"],
        vectors=np.array(
            [[1.0, 0.0], [1.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 0.0]]
        ),
        word_counts=[1.0, 1.0, 3.0, 4.0, 2.0],
        config=cfg,
    )

    print("Participation         ", _fmt(result.participation),
          " | expected A=0.6 B=0.2 C=0.2")
    print("Responsivity R_bar_w  ", np.array(result.responsivity_matrix).tolist(),
          " | expected [[1,0,0],[1,0,0],[0,0,0]]")
    print("Internal Cohesion     ", _fmt(result.internal_cohesion),
          " | expected A=1 B=0 C=0")
    print("Overall Responsivity  ", _fmt(result.overall_responsivity),
          " | expected A=0 B=0.5 C=0")
    print("Social Impact         ", _fmt(result.social_impact),
          " | expected A=0.5 B=0 C=0")
    print("Newness (per contrib.)", [round(v, 6) for v in result.newness],
          " | expected [1,0,0,1,0]")
    print("Newness by speaker    ", _fmt(result.newness_by_speaker),
          " | expected A=0.666667 B=0 C=0")
    print("Density (per contrib.)", [round(v, 6) for v in result.density],
          " | expected [1,1,0.333333,0.25,0.5]")
    print("Density by speaker    ", _fmt(result.density_by_speaker),
          " | expected A=0.5 B=0.333333 C=0.5")


if __name__ == "__main__":
    main()
