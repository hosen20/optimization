# tests

Checks that the model behaves the way the rules say it should. They run on the real data files, so
point them at the data first.

| File | Checks |
|---|---|
| `test_dom_model.py` | Data reading, the funnel counts, the seven rules, and the objective |

## Running them

```bash
pip install pytest
cd tests
DOM_DATA="/path/to/DOM-data/input data" pytest -v
```

If `DOM_DATA` is not set, the tests search for `input_order data.csv` under the current folder. If no
data is found they are skipped rather than failed, so the suite still runs in a fresh clone.

## What is checked

**Reading the data**

* The order file is already filtered — every row is full truckload and every delivery note is open
* Pallet lines convert to cases correctly
* Every DC-to-zip lane the orders need exists in the freight file

**The funnel**

* 447 orders short of stock plus 25 with no dock gives 472 focus orders
* The focus orders and the untouched orders together make 1,109

**The rules**

* C2 — a fill never exceeds what was ordered
* C3 — availability over a window is never more than availability on the tightest day
* C4 — the gate rejects a lift below 5 points or below 100 cases
* C7 — no penalty at or above the threshold, and a positive penalty below it

**The objective**

* Baseline 1 reproduces \$44,365,994 on the 472 focus orders
* Every method is scored by the same function
