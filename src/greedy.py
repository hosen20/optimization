"""
greedy.py -- Baseline 2: the greedy move heuristic.

For each order that needs a decision, look at the other DCs. If one fills the
order better and the rules allow it, move the order there. One order at a time,
and never go back. That is what greedy means.

Two orderings are usually run: by order value, and by shortage size.
"""
import pandas as pd

from dom_model import (CFG, evaluate, take, give, picks, penalty_of, objective,
                       revised_pgi, passes_gate)


def greedy(D, pool_after_stage_a, default, key, cfg=None):
    """Return (records, rejection log).

    `key` decides who is considered first, for example
    ``lambda g: -D.HEAD[g]["revenue"]`` for biggest revenue first.
    """
    cfg = {**CFG, **(cfg or {})}
    P = {k: v.copy() for k, v in pool_after_stage_a.items()}
    dk, cp_r, pp_r = D.DOCK0.copy(), D.CP0.copy(), D.PP0.copy()

    # every order already holds a dock slot at its own DC
    for gf, r in default.items():
        i, j = D.DCIX[r["dc"]], r["t"]
        if D.DOCK_HAS[i, j]:
            dk[i, j] = max(0.0, dk[i, j] - cfg["DOCKS_PER_ORDER"])

    res = {g: dict(default[g]) for g in default}
    log = []

    for gf in sorted(D.FOCUS, key=key):
        h, base = D.HEAD[gf], default[gf]
        d0, t0 = base["dc"], base["t"]
        best = None

        for d in D.DCS:
            if d == d0:
                continue
            if not all(s in D.SKU_AT_DC.get(d, set()) for s, _, _, _ in D.LINES[gf]):
                log.append((gf, d, "sku_not_carried"))
                continue
            p, err = revised_pgi(D, gf, d, cfg)
            if err:
                log.append((gf, d, err))
                continue
            t = D.DIX[p]
            fills, by, tot, rev = evaluate(D, P, gf, d, t,
                                           cfg["FORWARD_COVER_DAYS"], cfg["SAFETY_STOCK_FRAC"])
            why = passes_gate(tot - base["filled"], h["ordered_cases"], cfg)
            if why:
                log.append((gf, d, why))
                continue
            i = D.DCIX[d]
            if D.DOCK_HAS[i, t] and dk[i, t] < cfg["DOCKS_PER_ORDER"]:
                log.append((gf, d, "no_dock"))
                continue
            cp, pp = picks(fills)
            if cp > cp_r[i, t] or pp > pp_r[i, t]:
                log.append((gf, d, "no_pick_capacity"))
                continue
            cand = dict(dc=d, t=t, fills=fills, by=by, filled=tot, revenue=rev,
                        pen=penalty_of(D, gf, by, tot), ship=D.SHIP.get((d, h["zipc"]), 0.0),
                        cp=cp, pp=pp, lift=tot - base["filled"],
                        cof=tot / h["ordered_cases"] if h["ordered_cases"] else 0.0)
            if best is None or objective(cand) > objective(best):
                best = cand

        if best is None:
            log.append((gf, None, "no_feasible_alternate"))
            continue
        if cfg["REQUIRE_OBJ_GAIN"] and objective(best) <= objective(base):
            log.append((gf, best["dc"], "no_objective_gain"))
            continue

        # hand the stock and the dock back, then take them at the new DC
        for s, q, _, _ in base["fills"]:
            give(P, d0, s, t0, q)
        if D.DOCK_HAS[D.DCIX[d0], t0]:
            dk[D.DCIX[d0], t0] += cfg["DOCKS_PER_ORDER"]
        for s, q, _, _ in best["fills"]:
            take(P, best["dc"], s, best["t"], q)
        i = D.DCIX[best["dc"]]
        if D.DOCK_HAS[i, best["t"]]:
            dk[i, best["t"]] -= cfg["DOCKS_PER_ORDER"]
        cp_r[i, best["t"]] -= best["cp"]
        pp_r[i, best["t"]] -= best["pp"]

        res[gf] = dict(best, diverted=True, chosen_dc=best["dc"])

    return res, pd.DataFrame(log, columns=["order", "dc", "reason"])


if __name__ == "__main__":
    from baseline import run_baseline
    from dom_model import metrics

    D, pool, default, _ = run_baseline()
    for name, key in [("by order value", lambda g: -D.HEAD[g]["revenue"]),
                      ("by shortage", lambda g: -(D.HEAD[g]["ordered_cases"]
                                                  - default[g]["filled"]))]:
        res, log = greedy(D, pool, default, key)
        m = metrics(D, res, f"Greedy - {name}")
        print(f"{name:16s} moved {m['orders_moved']:3d}  "
              f"objective {m['objective_focus']:,.0f}  fill {m['fill_rate']*100:.2f}%")
    print()
    print(log.reason.value_counts().to_string())
