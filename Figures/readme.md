# Figures

Charts used in the report, the slides and the dashboard. All are generated from the executed
notebooks — none is drawn by hand.

| File | Shows | Comes from |
|---|---|---|
| `funnel.png` | How 1,109 open orders become 472 focus orders | `01_data_exploration` |
| `comparison.png` | Objective, fill rate, penalty and freight for the four classical methods | `11_comparison` |
| `scaling.png` | Solve time, model size and greedy gap at five problem sizes | `05_classical` |
| `rejects.png` | Why candidate moves were rejected | `04_greedy` |
| `destinations.png` | Which DCs receive the reassigned orders, and the gain each brings | `11_comparison` |
| `quantum.png` | Objective per batch and running total across the 15 quantum batches | `09_..._Scaled_Quantum` |
| `quantum_validation.png` | Small-instance agreement, QAOA stability, qubits with and without slack | `06_..._Investigation` |

## Numbers behind the figures

| | |
|---|---|
| Leave everything alone | \$44,365,994 · 90.47% fill |
| Greedy 2A | \$44,810,604 · 91.28% fill · 41 moves |
| Exact MILP | \$46,295,828 · 93.28% fill · 66 moves · 63.72s |
| Quantum, 15 batches | +\$1,358,671 on 75 orders · 0 rule violations |

## Rebuilding them

The figures are plotted inside the notebooks listed above. Run the notebook and save the figure, or
call `matplotlib.pyplot.savefig` on the cell output. Sizes are set for a letter-width page at 200
dpi.
