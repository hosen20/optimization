"""
results.py -- every number the dashboard shows.

All values are fixed. They were printed by the notebooks and typed in here, so
the dashboard opens instantly, needs no data files, and cannot break if a path
changes.

Where each block came from:
    classical results, planner view   ->  11_comparison.ipynb
    scaling sweep                     ->  05_classical.ipynb
    rejection reasons                 ->  04_greedy.ipynb
    quantum blocks                    ->  notebooks 06 to 10 and 12
"""
import pandas as pd

# ---------------------------------------------------------------- the data set
DATASET = dict(
    orders=1109, skus=1110, dcs=8,
    window="24 June to 5 July 2024",
    order_lines=25193, stock_rows=377505, freight_lanes=12923,
    dock_rows=480, throughput_rows=531,
    short_of_stock=447, no_dock=25, focus=472, untouched=637,
    focus_cases=1449768, focus_revenue=49_000_000,
)

DC_LIST = [5083, 5385, 5410, 5420, 5490, 5620, 5641, 5773]

FILES = pd.DataFrame([
    ("input_order data.csv", "25,193 rows", "One row per order and SKU. The working order book."),
    ("input_capacity_planning.csv", "377,505 rows", "Daily stock for each DC and SKU."),
    ("input_dock_capacity.csv", "480 rows", "Daily dock appointment slots for each DC."),
    ("input_shipping_cost_data.csv", "12,923 rows", "Cost and distance for each DC to zip lane."),
    ("input_throughput_capacity.csv", "531 rows", "Daily picking work at each DC."),
    ("Output_order_level_data.csv", "1,109 rows", "Earlier model output. Used only to check."),
    ("output_order_sku_level_data.csv", "25,193 rows", "The same, at SKU level. Check only."),
], columns=["File", "Size", "What it holds"])

# ---------------------------------------------------------------- classical
CLASSICAL = pd.DataFrame([
    dict(method="Leave everything alone", short="Baseline",
         objective=44_365_994, fill=90.47, moves=0,
         penalty=84_749, freight=565_479, runtime=0.21),
    dict(method="Greedy 2A - by order value", short="Greedy 2A",
         objective=44_810_604, fill=91.28, moves=41,
         penalty=75_259, freight=638_165, runtime=0.40),
    dict(method="Greedy 2B - by shortage", short="Greedy 2B",
         objective=44_786_479, fill=91.26, moves=39,
         penalty=75_429, freight=636_816, runtime=0.42),
    dict(method="Exact MILP (PuLP + CBC)", short="Exact MILP",
         objective=46_295_828, fill=93.28, moves=66,
         penalty=32_333, freight=622_880, runtime=63.72),
])

BASE_OBJ = 44_365_994
OPT_OBJ = 46_295_828
GREEDY_OBJ = 44_810_604

# ---------------------------------------------------------------- scaling
SCALING = pd.DataFrame([
    dict(orders=50,  binaries=227,   rows=35_830,  wall_s=1.41,  gap_pct=0.835),
    dict(orders=100, binaries=458,   rows=64_976,  wall_s=6.43,  gap_pct=2.078),
    dict(orders=200, binaries=920,   rows=99_153,  wall_s=18.45, gap_pct=3.114),
    dict(orders=300, binaries=1_472, rows=123_972, wall_s=35.13, gap_pct=3.124),
    dict(orders=472, binaries=2_594, rows=148_663, wall_s=63.72, gap_pct=3.208),
])

# ---------------------------------------------------------------- rejections
REJECTIONS = pd.DataFrame([
    ("5% fill gate", 1682), ("SKU not stocked there", 1457),
    ("no feasible DC", 423), ("100-case floor", 37),
    ("ship date too late", 24), ("no dock slot", 17),
    ("no pick capacity", 11), ("no gain in objective", 8),
], columns=["reason", "count"])

# ---------------------------------------------------------------- planner view
PLANNER_TOTALS = pd.DataFrame([
    dict(measure="Cases delivered", leave="1,311,570", apply="1,352,341", change="+40,771"),
    dict(measure="Fill rate", leave="90.47%", apply="93.28%", change="+2.81 points"),
    dict(measure="Customer penalties", leave="$84,749", apply="$32,333", change="-$52,416"),
    dict(measure="Freight cost", leave="$565,479", apply="$622,880", change="+$57,401"),
    dict(measure="Net value", leave="$44,365,994", apply="$46,295,828", change="+$1,929,835"),
])

TOP_MOVES = pd.DataFrame([
    (5484926947, 5420, 5490, 27, 67, 882, 0, 2883, 76497),
    (5485532552, 5490, 5410, 86, 100, 356, 1879, 1064, 46501),
    (5485069375, 5490, 5620, 89, 100, 321, 1713, 2386, 42147),
    (5484650344, 5620, 5420, 10, 34, 732, 0, -4892, 37875),
    (5485525163, 5385, 5641, 91, 99, 212, 1141, -46, 27455),
    (5485613216, 5385, 5641, 68, 97, 303, 1031, 49, 26758),
    (5485496838, 5385, 5420, 92, 98, 142, 1205, 113, 25390),
    (5485108289, 5641, 5620, 84, 99, 497, 0, 3660, 25374),
    (5483875303, 5620, 5410, 62, 100, 1020, 0, 3114, 21807),
    (8029881894, 5420, 5490, 77, 94, 544, 896, 2336, 20951),
], columns=["order", "from_dc", "to_dc", "fill_before", "fill_after",
            "extra_cases", "penalty_saved", "extra_freight", "net_gain"])

DESTINATIONS = pd.DataFrame([
    (5385, 4, 27143), (5410, 13, 133009), (5420, 11, 142980), (5490, 22, 208059),
    (5620, 7, 92866), (5641, 4, 65859), (5773, 5, 44498),
], columns=["dc", "orders_received", "net_gain"])

DISAGREEMENT = pd.DataFrame([
    ("Moved by the exact solver only", 37),
    ("Moved by both, same DC", 26),
    ("Moved by the greedy only", 12),
    ("Moved by both, different DC", 3),
], columns=["case", "orders"])

# ---------------------------------------------------------------- quantum
QUANTUM_SMALL = pd.DataFrame([
    dict(method="Leave everything alone", objective=721_191.3, fill=82.97, moves=0),
    dict(method="Greedy best DC", objective=760_517.9, fill=87.97, moves=3),
    dict(method="Every combination (true best)", objective=760_517.9, fill=87.97, moves=3),
    dict(method="QUBO ground state (exact)", objective=760_517.9, fill=87.97, moves=3),
    dict(method="QAOA, best of 5 runs", objective=760_517.9, fill=87.97, moves=3),
    dict(method="QAOA, mean of 5 runs", objective=760_341.3, fill=87.97, moves=3),
])

QAOA_RUNS = pd.DataFrame([
    (1, 760_517.9, 0.0, False), (2, 760_517.9, 0.0, False), (3, 759_634.9, 883.0, False),
    (4, 760_517.9, 0.0, False), (5, 760_517.9, 0.0, False),
], columns=["run", "objective", "gap", "needed_repair"])

QUANTUM_BATCHED = pd.DataFrame([
    dict(method="Leave everything alone", objective=13_612_065, fill=88.60,
         moves=0, violations=0),
    dict(method="Greedy on the same 75", objective=14_970_736, fill=97.27,
         moves=75, violations=0),
    dict(method="Quantum + 2-opt repair", objective=14_970_736, fill=97.27,
         moves=75, violations=0),
])

BATCHES = pd.DataFrame({
    "batch": list(range(1, 16)),
    "qubits": [18, 18, 9, 12, 18, 15, 15, 15, 15, 18, 15, 18, 12, 12, 15],
    "default": [1_928_200, 1_751_226, 783_691, 777_122, 906_965, 813_861, 833_941,
                815_538, 648_570, 918_804, 755_283, 871_868, 573_044, 554_230, 679_723],
    "quantum": [2_119_248, 1_959_404, 869_247, 865_964, 1_015_163, 913_401, 901_764,
                896_210, 709_231, 1_009_284, 813_069, 942_291, 622_060, 603_579, 730_821],
})
BATCHES["lift"] = BATCHES["quantum"] - BATCHES["default"]

HYBRID = pd.DataFrame([
    dict(batch=i, orders=3, columns=6, binaries=6, status="SUCCESS", gap=0.0)
    for i in range(1, 6)])

QUBIT_NOTE = dict(qubits_per_batch=18, linear_terms=18, quadratic_terms=63,
                  slack_qubits=0, total_solve_s=1.07, batches=15, orders=90,
                  hybrid_total_s=35.3)

# ---------------------------------------------------------------- runtime
RUNTIME = pd.DataFrame([
    dict(method="Leave everything alone", seconds=0.21, group="classical"),
    dict(method="Greedy 2A", seconds=0.40, group="classical"),
    dict(method="Greedy 2B", seconds=0.42, group="classical"),
    dict(method="Exact MILP (472 orders)", seconds=63.72, group="classical"),
    dict(method="Quantum, 15 batches", seconds=1.07, group="quantum"),
    dict(method="QUBO exact, one batch", seconds=0.28, group="quantum"),
    dict(method="QAOA, one run", seconds=1.30, group="quantum"),
    dict(method="Hybrid QAOA, 5 batches", seconds=35.30, group="quantum"),
])

# ---------------------------------------------------------------- assumptions
ASSUMPTIONS = pd.DataFrame([
    ("No demand forecast", "Nothing holds stock back at the receiving DC, so every method "
                           "moves more orders than a planner would accept."),
    ("No throughput limit", "The file reports usage only. We use the highest usage ever seen "
                            "as the limit."),
    ("No holiday calendar", "Revised ship dates avoid weekends but not public holidays."),
    ("Two DCs have no dock data", "5083 and 5773 have no dock rows, so the dock check is "
                                  "skipped there."),
    ("Quantum covers 75 orders", "Not the full 472, and it runs on noise-free simulation."),
], columns=["Limit", "What it means"])
