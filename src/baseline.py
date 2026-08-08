"""
baseline.py -- Baseline 1: leave every order where it is.

Every order is filled from its own DC. Nothing moves. This is what a planner
gets if nobody acts, so it is the number every other method has to beat.
"""
import time

from dom_model import load_all, stage_A, metrics, to_frame


def run_baseline(D=None, data_dir=None):
    """Return (records, metrics dict). Also gives the stock the movers start from."""
    D = D or load_all(data_dir)
    t0 = time.time()
    pool, default = stage_A(D)
    runtime = round(time.time() - t0, 3)
    return D, pool, default, metrics(D, default, "Baseline 1 - leave everything", runtime)


if __name__ == "__main__":
    D, pool, default, m = run_baseline()
    for k, v in m.items():
        print(f"{k:17s} {v:,.4f}" if isinstance(v, float) else f"{k:17s} {v}")
    print()
    print(to_frame(D, default, "baseline").head().to_string(index=False))
