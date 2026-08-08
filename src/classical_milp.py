"""
classical_milp.py -- the exact model, built and solved with PuLP and CBC.

The greedy decides one order at a time and never goes back. This solves the same
problem exactly, looking at every order together, so the answer is the best that
exists. The distance between the two is how much the greedy leaves behind.

    x[i,j]    binary    order i is served from DC j
    q[i,j,k]  >= 0      cases of SKU k filled for order i at DC j
    z[i]      binary    order i reached its threshold, so no penalty
    pen[i]    >= 0      the penalty charged on order i

Filled cases are variables, not fixed numbers. If each option carried a fixed
quantity the model could not describe a partial fill, and it would score below
the greedy -- which would make the gap meaningless.
"""
import time

import numpy as np

from dom_model import (CFG, picks, penalty_of, objective, revised_pgi)


def candidate_options(D, subset, default):
    """Each order's own DC, plus every DC that stocks all its SKUs and can still
    make the delivery date."""
    cand = {}
    for g in subset:
        base = default[g]
        opts = [(base["dc"], base["t"], True)]      # staying put is always an option
        for d in D.DCS:
            if d == base["dc"]:
                continue
            if not all(s in D.SKU_AT_DC.get(d, set()) for s, _, _, _ in D.LINES[g]):
                continue
            p, err = revised_pgi(D, g, d)
            if err:
                continue
            opts.append((d, D.DIX[p], False))
        cand[g] = opts
    return cand


def build_milp(D, subset, pool_after_stage_a, default, cand=None, cfg=None):
    """Return (problem, x, q, cand, info). Needs pulp."""
    import pulp

    cfg = cfg or CFG
    W = cfg["FORWARD_COVER_DAYS"]
    cand = cand or candidate_options(D, subset, default)

    # stock these orders hand back when they leave their own DC
    GIVE = {}
    for g in subset:
        r = default[g]
        for s, qty, _, _ in r["fills"]:
            if qty > 0:
                GIVE.setdefault((r["dc"], s), np.zeros(D.NT))[r["t"]:] += qty

    # dock room: every order holds a slot, then the focus orders hand theirs back
    dock_av = D.DOCK0.copy()
    for g, r in default.items():
        i, j = D.DCIX[r["dc"]], r["t"]
        if D.DOCK_HAS[i, j]:
            dock_av[i, j] -= cfg["DOCKS_PER_ORDER"]
    dock_av = np.maximum(0.0, dock_av)
    for g in subset:
        r = default[g]
        i, j = D.DCIX[r["dc"]], r["t"]
        if D.DOCK_HAS[i, j]:
            dock_av[i, j] += cfg["DOCKS_PER_ORDER"]

    prob = pulp.LpProblem("DOM", pulp.LpMaximize)

    x = {(g, d): pulp.LpVariable(f"x_{g}_{d}", cat="Binary")
         for g in subset for d, _, _ in cand[g]}
    q = {(g, d, s): pulp.LpVariable(f"q_{g}_{d}_{s}", lowBound=0, upBound=dem)
         for g in subset for d, _, _ in cand[g] for s, dem, _, _ in D.LINES[g] if dem > 0}
    z = {g: pulp.LpVariable(f"z_{g}", cat="Binary") for g in subset if D.HEAD[g]["ppc"] > 0}
    pen = {g: pulp.LpVariable(f"pen_{g}", lowBound=0) for g in subset if D.HEAD[g]["ppc"] > 0}

    # objective: revenue - penalty - shipping
    prob += (pulp.lpSum(price * q[g, d, s] for g in subset for d, _, _ in cand[g]
                        for s, dem, price, _ in D.LINES[g] if dem > 0)
             - pulp.lpSum(pen.values())
             - pulp.lpSum(D.SHIP.get((d, D.HEAD[g]["zipc"]), 0.0) * x[g, d]
                          for g in subset for d, _, _ in cand[g]))

    for g in subset:                                    # C1
        prob += pulp.lpSum(x[g, d] for d, _, _ in cand[g]) == 1

    for g in subset:                                    # C2
        for d, _, _ in cand[g]:
            for s, dem, _, _ in D.LINES[g]:
                if dem > 0:
                    prob += q[g, d, s] <= dem * x[g, d]

    draws = {}                                          # C3
    for g in subset:
        for d, t, isdef in cand[g]:
            w = 0 if isdef else W
            for s, dem, _, _ in D.LINES[g]:
                if dem > 0:
                    draws.setdefault((d, s), []).append((q[g, d, s], t, w))
    for (d, s), items in draws.items():
        arr, giv = pool_after_stage_a.get((d, s)), GIVE.get((d, s))
        days = set()
        for _, t, w in items:
            days |= set(range(t, min(D.NT, t + w + 1)))
        for u in sorted(days):
            active = [v for v, t, w in items if t <= u <= t + w]
            if not active:
                continue
            rhs = (max(0.0, arr[u]) if arr is not None else 0.0) + \
                  (giv[u] if giv is not None else 0.0)
            prob += pulp.lpSum(active) <= rhs

    for g in subset:                                    # C4
        need = default[g]["filled"] + max(cfg["MIN_FILL_LIFT_PP"] * D.HEAD[g]["ordered_cases"],
                                          cfg["MIN_CASE_LIFT"])
        for d, _, isdef in cand[g]:
            if not isdef:
                prob += pulp.lpSum(q[g, d, s] for s, dem, _, _ in D.LINES[g] if dem > 0) \
                        >= need * x[g, d]

    pe = {}                                             # C5
    for g in subset:
        for d, t, isdef in cand[g]:
            if not isdef:
                pe.setdefault((d, t), []).append(g)
    for (d, t), gs in pe.items():
        i = D.DCIX[d]
        if sum(sum(dem / cpp for _, dem, _, cpp in D.LINES[g]) for g in gs) <= D.PP0[i, t]:
            continue                                    # cannot overflow, no row needed
        prob += (pulp.lpSum(q[g, d, s] / cpp for g in gs
                            for s, dem, _, cpp in D.LINES[g] if dem > 0)
                 - pulp.lpSum(len(D.LINES[g]) * x[g, d] for g in gs)) <= float(D.PP0[i, t])

    de = {}                                             # C6
    for g in subset:
        for d, t, _ in cand[g]:
            if D.DOCK_HAS[D.DCIX[d], t]:
                de.setdefault((d, t), []).append(x[g, d])
    for (d, t), vs in de.items():
        capacity = float(dock_av[D.DCIX[d], t])
        if len(vs) > capacity:
            prob += pulp.lpSum(vs) <= capacity

    for g in subset:                                    # C7
        h = D.HEAD[g]
        if h["ppc"] <= 0:
            continue
        full = sum(dem * price for _, dem, price, _ in D.LINES[g]) * h["ppc"]
        prob += (pen[g] + h["ppc"] * pulp.lpSum(price * q[g, d, s] for d, _, _ in cand[g]
                                                for s, dem, price, _ in D.LINES[g] if dem > 0)
                 >= full * (1 - z[g]))
        prob += pulp.lpSum(q[g, d, s] for d, _, _ in cand[g]
                           for s, dem, _, _ in D.LINES[g] if dem > 0) >= h["threshold_cases"] * z[g]

    info = dict(nvars=len(x) + len(q) + len(z) + len(pen), nbin=len(x) + len(z),
                nrows=len(prob.constraints))
    return prob, x, q, cand, info


def decode(D, subset, cand, x, q, default):
    """Solver variables back into the same per-order record the other methods make."""
    res = {}
    for g in subset:
        h = D.HEAD[g]
        for d, t, isdef in cand[g]:
            if (x[g, d].value() or 0.0) <= 0.5:
                continue
            by = {s: ((q[g, d, s].value() or 0.0) if (g, d, s) in q else 0.0)
                  for s, dem, _, _ in D.LINES[g]}
            fills = [(s, by.get(s, 0.0), price, cpp) for s, dem, price, cpp in D.LINES[g]]
            tot = sum(by.values())
            rev = sum(by[s] * price for s, dem, price, _ in D.LINES[g])
            cp, pp = picks(fills)
            res[g] = dict(dc=d, t=t, fills=fills, by=by, filled=tot, revenue=rev, cp=cp, pp=pp,
                          pen=penalty_of(D, g, by, tot), ship=D.SHIP.get((d, h["zipc"]), 0.0),
                          cof=tot / h["ordered_cases"] if h["ordered_cases"] else 0.0,
                          diverted=not isdef, chosen_dc=d, lift=tot - default[g]["filled"])
            break
    return res


def solve_exact(D, pool_after_stage_a, default, subset=None, time_limit=900, msg=0):
    """Build, solve and decode. Returns (records, info)."""
    import pulp

    subset = subset or D.FOCUS
    prob, x, q, cand, info = build_milp(D, subset, pool_after_stage_a, default)

    t0 = time.time()
    prob.solve(pulp.PULP_CBC_CMD(msg=msg, timeLimit=time_limit, gapRel=0.0))
    info["wall_s"] = time.time() - t0
    info["status"] = pulp.LpStatus[prob.status]
    info["solver_objective"] = pulp.value(prob.objective)

    res = decode(D, subset, cand, x, q, default)
    for g in D.CLEAN_ORDERS:                      # orders that never move
        res[g] = dict(default[g])
    return res, info


if __name__ == "__main__":
    from baseline import run_baseline
    from dom_model import metrics

    D, pool, default, mb = run_baseline()
    res, info = solve_exact(D, pool, default)
    m = metrics(D, res, "Classical - exact MILP", round(info["wall_s"], 2))

    print(f"status {info['status']} | {info['nvars']:,} variables "
          f"({info['nbin']:,} binary) | {info['nrows']:,} rows")
    print(f"baseline  {mb['objective_focus']:>14,.0f}")
    print(f"exact     {m['objective_focus']:>14,.0f}  "
          f"{m['orders_moved']} moves  {info['wall_s']:.1f}s")
