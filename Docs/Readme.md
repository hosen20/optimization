# Docs

The written deliverables for the challenge.

| File | What it is | Length |
|---|---|---|
| `Technical_Report_Wiser.pdf` | The full technical report | 9 pages |
| `Business_Summary.pdf` | Business and technical summary | 2 pages |

## Technical report

Covers the whole piece of work:

1. Problem and business context
2. The data pack and the order funnel
3. The mathematical formulation — variables, objective, and the seven constraints
4. The four solvers: default, greedy, exact MILP, and the QUBO batch solver
5. Results, including the optimality gap and where the methods disagree
6. Sensitivity checks
7. Scaling, with wall-clock time at five problem sizes
8. Limitations
9. Reproducibility
10. Conclusion

## Business summary

Written for a reader who wants the decision, not the derivation. It explains what DOM is, why it is a
combinatorial optimization problem, and the three trade-offs the challenge asks about: solution
quality against runtime, exact solvers against heuristics, and noisy hardware against simulators.

## Source

Both documents are written in LaTeX and live in the same Overleaf project as the slides and the
planner view. They share `domstyle.sty` and read their figures from `../Figures/`.

## The numbers in these documents

Every figure quoted comes from an executed notebook. Nothing is estimated. The headline is that the
exact model raises the objective on the 472 focus orders from \$44,365,994 to \$46,295,828 and the
fill rate from 90.47% to 93.28%, by reassigning 66 orders, solved to proven optimality in 63.72
seconds.
