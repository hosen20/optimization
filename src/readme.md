# src

Reusable code. The notebooks are the place to read the work; these modules are the same logic
packaged so it can be imported, tested, or used by the dashboard.

| File | What it holds |
|---|---|
| `dom_model.py` | Loading, preparation, the objective, and the seven rules |
| `baseline.py` | Baseline 1 — leave every order at its own DC |
| `greedy.py` | Baseline 2 — the greedy move heuristic |
| `classical_milp.py` | The exact model, built and solved with PuLP and CBC |
| `No-slack.py` | The QUBO encoding that uses no slack variables (Method 2) |
| `LR-qaoa.py` | The Ising build and the QAOA schedule used on the batched runs |

## The model in one line

```
Objective = Revenue − Penalty − Shipping cost
```

Maximised, subject to seven rules:

| Rule | Meaning |
|---|---|
| C1 | One order goes to one DC only |
| C2 | You cannot fill more than what was ordered |
| C3 | Stock must be there, and must still cover the next 5 days |
| C4 | Move only if the fill rises 5 points **and** 100 cases |
| C5 | Case picks and pallet picks must fit the DC limit that day |
| C6 | One dock slot per order, and docks are limited |
| C7 | A penalty applies only if filled cases fall under the order threshold |

## Using it

```python
from dom_model import load_all, stage_A, objective, metrics
from greedy import greedy
from classical_milp import solve_exact

D = load_all("path/to/DOM-data/input data")   # everything the rules need
pool, default = stage_A(D)                     # Baseline 1
moved, log = greedy(D, pool, default, key=lambda g: -D.HEAD[g]["revenue"])
best, info = solve_exact(D, pool, default)     # exact answer
```

Every method is scored by the same `objective()` and the same `metrics()`, which is what makes the
comparison fair rather than merely claimed.

## Note on the two quantum files

`No-slack.py` and `LR-qaoa.py` are extracted from the quantum notebooks and expect a `data` dict with
keys `n_orders`, `n_dcs`, `revenue`, `fillable`, `ship_cost`, `penalty_if_not`, `cases` and
`capacity`. The notebooks show how that dict is built from the CSV files.
