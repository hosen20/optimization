"""
dom_model.py -- the DOM model in one place.

Objective:  Revenue - Penalty - Shipping cost

    C1  one order goes to one DC only
    C2  you cannot fill more than what was ordered
    C3  stock must be there, and must still cover the next 5 days
    C4  move only if the fill rises 5 points AND 100 cases
    C5  case picks and pallet picks must fit the DC limit that day
    C6  one dock slot per order, and docks are limited
    C7  a penalty applies only if filled cases fall under the order threshold

Everything here is plain numpy and pandas. The solvers live in baseline.py,
greedy.py and classical_milp.py, and all three score their answers with the
objective() and metrics() found below.
"""
import os
import glob
import math
from types import SimpleNamespace

import numpy as np
import pandas as pd

# Every number we can tune. The defaults are the values from the business rules.
CFG = dict(
    MIN_FILL_LIFT_PP   = 0.05,   # C4: the fill must rise 5 points
    MIN_CASE_LIFT      = 100.0,  # C4: and at least 100 cases
    FORWARD_COVER_DAYS = 5,      # C3: stock must last 5 more days
    LEAD_TIME_MILES    = 500.0,  # one transit day per 500 miles
    DOCKS_PER_ORDER    = 1,      # C6: one dock per order
    SAFETY_STOCK_FRAC  = 0.0,    # hold stock back elsewhere (sensitivity only)
    REQUIRE_OBJ_GAIN   = True,   # greedy only: move only if the money improves
)


NEEDLE = "input_order data.csv"


def find_data(start=None):
    """Return the folder that holds input_order data.csv.

    Looks at the folder you pass, then DOM_DATA, then searches downward from the
    current folder and from each of the three folders above it. That last part
    matters: it lets you run from src/ or tests/ while the data sits at the
    repository root.
    """
    if start and os.path.isfile(os.path.join(start, NEEDLE)):
        return start
    env = os.environ.get("DOM_DATA")
    if env and os.path.isfile(os.path.join(env, NEEDLE)):
        return env

    here = os.path.abspath(os.curdir)
    roots = [here] + [os.path.abspath(os.path.join(here, *[".."] * n)) for n in (1, 2, 3)]
    for root in roots:
        for hit in glob.glob(os.path.join(root, "**", NEEDLE), recursive=True):
            return os.path.dirname(hit)

    raise FileNotFoundError(
        f"Could not find '{NEEDLE}'. Pass the folder to load_all(), or set DOM_DATA.")


def load_all(data_dir=None):
    """Read the files and build everything the rules need.

    Returns a namespace with: orders, head, HEAD, LINES, FOCUS, CLEAN_ORDERS,
    POOL0, SKU_AT_DC, SHIP, DIST, DOCK0, DOCK_HAS, CP0, PP0, DATES, NT, DIX,
    DCS, DCIX.
    """
    IN = find_data(data_dir)

    orders = pd.read_csv(f"{IN}/input_order data.csv")
    cap    = pd.read_csv(f"{IN}/input_capacity_planning.csv")
    dock   = pd.read_csv(f"{IN}/input_dock_capacity.csv")
    ship   = pd.read_csv(f"{IN}/input_shipping_cost_data.csv")
    thru   = pd.read_csv(f"{IN}/input_throughput_capacity.csv")

    # ---- prepare the orders ------------------------------------------------
    orders["PGI"] = pd.to_datetime(orders["transportationplanningdate"], format="%m/%d/%y")
    orders["RDD"] = pd.to_datetime(orders["RequestedDeliveryDate"], format="%m/%d/%y")
    orders["IsInvAvail"] = orders["IsInvAvail"].astype(str).str.strip().str.upper()

    # pallet lines become cases, so everything is in one unit
    orders["cases"] = np.where(orders["ProductPlanningUnitOfMeasure"].eq("PL"),
                               orders["OrderedQty_converted"] * orders["ProductCasesPerPallet"],
                               orders["OrderedQty_converted"]).astype(float)
    orders["price_per_case"] = np.where(orders["cases"] > 0,
                                        orders["Order_SKU_Revenue"] / orders["cases"], 0.0)
    orders["cpp"] = orders["ProductCasesPerPallet"].replace(0, np.nan).fillna(1).astype(float)

    head = orders.groupby("Group_Flag").agg(
        default_dc=("Plant", "first"),
        pgi=("PGI", "first"),
        rdd=("RDD", "first"),
        zipc=("ZipCode", "first"),
        prio=("DeliveryPriority", "min"),
        revenue=("Order_SKU_Revenue", "sum"),
        ordered_cases=("cases", "sum"),
        frt=("FillRateThreshold", "first"),
        ppc=("Penaltyforpotentialcuts", "first"),
    ).reset_index()
    head[["frt", "ppc"]] = head[["frt", "ppc"]].fillna(0.0)
    head["threshold_cases"] = head["frt"] * head["ordered_cases"]

    HEAD  = head.set_index("Group_Flag").to_dict("index")
    LINES = {gf: [(int(r.MaterialNumber), float(r.cases), float(r.price_per_case), float(r.cpp))
                  for r in g.itertuples(index=False)]
             for gf, g in orders.groupby("Group_Flag", sort=False)}

    # ---- the focus orders --------------------------------------------------
    roll = orders.groupby("Group_Flag")["IsInvAvail"].apply(lambda s: (s == "Y").all())
    short = set(roll[~roll].index)

    dock["Date"] = pd.to_datetime(dock["Date"], format="%m/%d/%y")
    zero_days = set(map(tuple, dock.loc[dock["Dock_Remaining"] == 0, ["Plant", "Date"]]
                                  .drop_duplicates().values))
    added = {gf for gf, h in HEAD.items()
             if (h["default_dc"], h["pgi"]) in zero_days} & set(roll[roll].index)

    FOCUS = sorted(short | added)
    CLEAN_ORDERS = sorted(set(HEAD) - set(FOCUS))

    # ---- the day grid ------------------------------------------------------
    cap["DATE"] = pd.to_datetime(cap["DATE"])
    DATES = pd.date_range(cap["DATE"].min(), cap["DATE"].max(), freq="D")
    NT = len(DATES)
    DIX = {d: i for i, d in enumerate(DATES)}
    DCS = sorted(int(x) for x in orders["Plant"].unique())
    DCIX = {d: i for i, d in enumerate(DCS)}

    # ---- stock -------------------------------------------------------------
    cap["AV"] = cap["OpeningStock"] - cap["Total_Reserved_Qty"]
    POOL0 = {}
    for (d, s), g in cap[cap["LocationID"].isin(DCS)].groupby(["LocationID", "MaterialID"],
                                                              sort=False):
        arr = np.zeros(NT)
        ix = g["DATE"].map(DIX).dropna().astype(int).values
        arr[ix] = g["AV"].values[:len(ix)]
        POOL0[(int(d), int(s))] = arr

    SKU_AT_DC = {}
    for (d, s) in POOL0:
        SKU_AT_DC.setdefault(d, set()).add(s)

    # ---- freight -----------------------------------------------------------
    SHIP = {(int(r.Plant), int(r.TargetZip)): float(r.Shipping_Cost)
            for r in ship.itertuples(index=False)}
    DIST = {(int(r.Plant), int(r.TargetZip)): float(r.Distance)
            for r in ship.itertuples(index=False)}

    # ---- docks: two DCs have no rows, so we mark them "no data" -------------
    DOCK0 = np.full((len(DCS), NT), np.nan)
    for r in dock.itertuples(index=False):
        if r.Plant in DCIX and r.Date in DIX:
            DOCK0[DCIX[r.Plant], DIX[r.Date]] = max(0.0, float(r.Dock_Remaining))
    DOCK_HAS = ~np.isnan(DOCK0)
    DOCK0 = np.nan_to_num(DOCK0, nan=0.0)

    # ---- pick capacity: the file gives usage, so peak usage is the limit ----
    thru["transportationplanningdate"] = pd.to_datetime(thru["transportationplanningdate"])
    cp_cap = thru.groupby("Plant")["util_case_picks"].max().to_dict()
    pp_cap = thru.groupby("Plant")["util_pallets"].max().to_dict()
    CP0 = np.zeros((len(DCS), NT))
    PP0 = np.zeros((len(DCS), NT))
    for d in DCS:
        CP0[DCIX[d], :] = cp_cap.get(d, 0.0)
        PP0[DCIX[d], :] = pp_cap.get(d, 0.0)
    for r in thru.itertuples(index=False):
        if r.Plant in DCIX and r.transportationplanningdate in DIX:
            i, j = DCIX[r.Plant], DIX[r.transportationplanningdate]
            CP0[i, j] = max(0.0, cp_cap[r.Plant] - r.util_case_picks)
            PP0[i, j] = max(0.0, pp_cap[r.Plant] - r.util_pallets)

    return SimpleNamespace(
        data_dir=IN, orders=orders, head=head, HEAD=HEAD, LINES=LINES,
        FOCUS=FOCUS, CLEAN_ORDERS=CLEAN_ORDERS,
        POOL0=POOL0, SKU_AT_DC=SKU_AT_DC, SHIP=SHIP, DIST=DIST,
        DOCK0=DOCK0, DOCK_HAS=DOCK_HAS, CP0=CP0, PP0=PP0,
        DATES=DATES, NT=NT, DIX=DIX, DCS=DCS, DCIX=DCIX)


# ---------------------------------------------------------------- C2 and C3
def avail(D, P, d, s, t, window=0):
    """How many cases we may take. With a window, the tightest day decides."""
    a = P.get((d, s))
    if a is None:
        return 0.0
    hi = min(D.NT, t + window + 1)
    return max(0.0, a[t:hi].min()) if hi > t else 0.0


def take(P, d, s, t, q):
    a = P.get((d, s))
    if a is not None and q > 0:
        a[t:] -= q


def give(P, d, s, t, q):
    a = P.get((d, s))
    if a is not None and q > 0:
        a[t:] += q


def evaluate(D, P, gf, d, t, window=0, reserve=0.0):
    """C2 and C3: how much of this order this DC can fill on this day."""
    fills, by, tot, rev = [], {}, 0.0, 0.0
    for s, dem, price, cpp in D.LINES[gf]:
        q = min(dem, avail(D, P, d, s, t, window) * (1.0 - reserve))
        fills.append((s, q, price, cpp))
        by[s] = q
        tot += q
        rev += q * price
    return fills, by, tot, rev


# ---------------------------------------------------------------- C5
def picks(fills):
    """Full pallets are pallet picks, the rest are case picks."""
    cp = pp = 0.0
    for _, q, _, cpp in fills:
        if q <= 0:
            continue
        full = math.floor(q / cpp)
        pp += full
        cp += q - full * cpp
    return cp, pp


# ---------------------------------------------------------------- C7
def penalty_of(D, gf, by, tot):
    """No penalty at or above the threshold, otherwise charge for what is missing."""
    h = D.HEAD[gf]
    if h["ppc"] <= 0 or tot >= h["threshold_cases"]:
        return 0.0
    return max(0.0, sum((dem - by.get(s, 0.0)) * price * h["ppc"]
                        for s, dem, price, _ in D.LINES[gf]))


# ---------------------------------------------------------------- objective
def objective(rec):
    """Revenue minus penalty minus shipping."""
    return rec["revenue"] - rec["pen"] - rec["ship"]


# ---------------------------------------------------------------- dates + C4
def lead_time(D, d, z, cfg=None):
    cfg = cfg or CFG
    dd = D.DIST.get((d, z))
    return None if dd is None else max(1, int(math.ceil(dd / cfg["LEAD_TIME_MILES"])))


def revised_pgi(D, gf, d, cfg=None):
    """A farther DC needs more transit time, so the ship day moves earlier."""
    h = D.HEAD[gf]
    lt = lead_time(D, d, h["zipc"], cfg)
    if lt is None:
        return None, "no_lane"
    p = min(h["pgi"], h["rdd"] - pd.Timedelta(days=lt))
    while p.weekday() >= 5:                     # step back off the weekend
        p -= pd.Timedelta(days=1)
    return (None, "pgi_out_of_horizon") if p not in D.DIX else (p, None)


def gate_lift(D, gf, cfg=None):
    """C4: the extra cases a move must deliver. One definition, used everywhere."""
    cfg = cfg or CFG
    h = D.HEAD[gf]
    return max(cfg["MIN_FILL_LIFT_PP"] * h["ordered_cases"], cfg["MIN_CASE_LIFT"])


def passes_gate(lift, ordered, cfg=None):
    """Same rule as gate_lift, but says which half failed."""
    cfg = cfg or CFG
    if lift < cfg["MIN_FILL_LIFT_PP"] * ordered:
        return "fail_5pct"
    if lift < cfg["MIN_CASE_LIFT"]:
        return "fail_100cases"
    return None


# ---------------------------------------------------------------- C1, stage A
def stage_A(D):
    """Put every order at its own DC. Protected orders first, then biggest revenue.

    Returns (pool left over, per-order record). This is also Baseline 1.
    """
    P = {k: v.copy() for k, v in D.POOL0.items()}
    seq = D.head.sort_values(["prio", "revenue"], ascending=[True, False])["Group_Flag"]
    out = {}
    for gf in seq:
        h = D.HEAD[gf]
        d, t = h["default_dc"], D.DIX[h["pgi"]]
        fills, by, tot, rev = evaluate(D, P, gf, d, t, window=0)
        for s, q, _, _ in fills:
            take(P, d, s, t, q)
        cp, pp = picks(fills)
        out[gf] = dict(dc=d, t=t, fills=fills, by=by, filled=tot, revenue=rev, cp=cp, pp=pp,
                       pen=penalty_of(D, gf, by, tot), ship=D.SHIP.get((d, h["zipc"]), 0.0),
                       cof=tot / h["ordered_cases"] if h["ordered_cases"] else 0.0,
                       diverted=False, chosen_dc=d, lift=0.0)
    return P, out


# ---------------------------------------------------------------- scorecard
def metrics(D, res, label, runtime=None):
    """The same scorecard for every method, measured on the focus orders."""
    oc = sum(D.HEAD[g]["ordered_cases"] for g in D.FOCUS)
    fl = sum(res[g]["filled"] for g in D.FOCUS)
    return dict(scenario=label,
                objective_focus=sum(objective(res[g]) for g in D.FOCUS),
                objective_all=sum(objective(res[g]) for g in res),
                fill_rate=fl / oc,
                cases_filled=fl,
                orders_moved=sum(1 for g in D.FOCUS if res[g]["diverted"]),
                penalty_cost=sum(res[g]["pen"] for g in D.FOCUS),
                shipping_cost=sum(res[g]["ship"] for g in D.FOCUS),
                runtime_s=runtime)


def to_frame(D, res, label):
    """Per-order answer as a table."""
    return pd.DataFrame([
        dict(scenario=label, order=g, is_focus=g in set(D.FOCUS),
             default_dc=D.HEAD[g]["default_dc"], assigned_dc=res[g]["chosen_dc"],
             moved=bool(res[g]["diverted"]),
             ordered_cases=D.HEAD[g]["ordered_cases"], filled_cases=res[g]["filled"],
             cof=res[g]["cof"], revenue=res[g]["revenue"],
             penalty=res[g]["pen"], shipping=res[g]["ship"],
             objective=objective(res[g]))
        for g in sorted(res)])
