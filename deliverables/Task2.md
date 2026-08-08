# Task 2 — Baseline Metrics Report

All figures below are taken from the classical pipeline executed on the full Nestlé DOM data pack (1 109 open orders, 472 focus orders). Metrics are computed by the shared `metrics()` function in `dom_model.py` and are therefore directly comparable.

## Headline table (focus-order view)

| Scenario | Objective (focus) | Fill rate | Orders reassigned | Penalty cost | Shipping cost | Runtime |
|----------|-------------------|-----------|-------------------|--------------|---------------|---------|
| Baseline 1 · default assignment | \$44,365,994 | 90.47 % | 0 | \$84,749 | \$565,479 | 0.21 s |
| Greedy 2A · by order value | \$44,810,604 | 91.28 % | 41 | \$75,259 | \$638,165 | 0.40 s |
| Greedy 2B · by shortage severity | \$44,786,479 | 91.26 % | 39 | \$75,429 | \$636,816 | 0.42 s |
| Classical · MILP (exact, CBC) | **\$46,295,828** | **93.28 %** | **66** | **\$32,333** | **\$622,880** | 63.72 s |

*Objective_all* (including the 637 clean orders that never move) is \$75,082,940 for Baseline 1 and \$77,012,775 for the MILP.

## Lift relative to Baseline 1

| Scenario | Δ Objective (\$) | Δ Fill rate (pts) | Δ Penalty (\$) | Δ Shipping (\$) | Moves |
|----------|-----------------|-------------------|---------------|----------------|-------|
| Greedy 2A | +444,610 | +0.81 | −9,490 | +72,686 | 41 |
| Greedy 2B | +420,485 | +0.79 | −9,320 | +71,337 | 39 |
| Classical MILP | **+1,929,835** | **+2.81** | **−52,416** | **+57,401** | **66** |

## Optimality gap of the best greedy

- MILP objective (ceiling) = \$46,295,828  
- Best greedy (2A)     = \$44,810,604  
- Absolute gap       = \$1,485,224  
- Relative gap       = **3.208 %**  
- Share of reachable gain captured by greedy = **23.0 %**

## Quantum reference points (subset experiments)

Because current quantum solvers operate on far smaller instances, the tables below report results obtained on high-value focus-order subsets under identical business metrics.

### Method-2 exact Ising (Scaled Quantum notebook, 75 high-value focus orders)

| Method | Objective | Δ vs Default | Fill rate | Diverted | Violations |
|--------|-----------|--------------|-----------|----------|------------|
| Default | \$13,612,065 | 0 | 88.6 % | 0 | 0 |
| Subset-Greedy | \$14,970,736 | +\$1,358,671 | 97.3 % | 75 | 0 |
| Quantum + 2-opt | \$14,970,736 | +\$1,358,671 | 97.3 % | 75 | 0 |

Quantum recovers the identical assignment matrix as the classical subset-greedy after local repair; absolute lift on the subset already exceeds the full-data Greedy Δ (\$0.44 M).

### Warm-start QAOA vs Greedy+2-opt (real-data instances, 18–24 qubits)

Across six real planning-date / DC-subset instances the sampling QAOA (best-of-100 repaired samples) produced:

- Aggregate objective delta = **\$0**  
- Per-instance record   = 0 wins / 6 ties / 0 losses  
- Assigned-order counts and diverted counts identical to Greedy+2-opt  

### Hybrid Quantum RMP (15-order batches, QAOA p=1)

QAOA recovered the exact Restricted-Master-Problem optimum on every batch (optimality gap = 0 versus NumPyMinimumEigensolver). Absolute dollars remain limited by the batch size; the architecture is the scalable path.

## Summary for planners

- Doing nothing leaves ≈ \$1.93 M of fulfilment value on the table.  
- A one-pass greedy recovers roughly one-quarter of that value in under half a second.  
- The exact classical model recovers the remainder and simultaneously reduces penalty exposure by more than \$50 k while only modestly increasing freight.  
- Quantum formulations on the same data, at the scales currently accessible, match the classical heuristics exactly; their practical contribution is the slack-free encoding and the hybrid master/pricing skeleton that can absorb larger focus sets as hardware improves.
