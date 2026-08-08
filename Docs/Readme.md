# Docs

The three written deliverables for the challenge.

| File | What it is | Length | Written for |
|---|---|---|---|
| `Technical_Report_Wiser.pdf` | The full write-up | 9 pages | A technical reviewer |
| `Business_Summary.pdf` | Business and technical summary | 2 pages | A business reader |
| `Planner_view.pdf` | The recommended reassignments | 1 page | A warehouse planner |

---

## Technical report

Covers the whole piece of work, from the data to the conclusion.

| Section | What it holds |
|---|---|
| 1 – 2 | The problem, the data pack, and the order funnel |
| 3 | The formulation: variables, objective, and the seven rules, with the equations |
| 4 | The four solvers: default, greedy, exact MILP, and the QUBO batch solver |
| 5 | Results, the optimality gap, and where the methods disagree |
| 6 | Sensitivity checks |
| 7 | Scaling, with solve time at five problem sizes |
| 8 – 10 | Limits, reproducibility, and what we conclude |

It also reports one negative result in full: the weighted exact-cover model scored *below* the greedy heuristic, which is impossible for something meant to be an upper bound. Section 3.5 explains why and what we changed.

---

## Business summary

For a reader who wants the decision rather than the derivation. Two pages covering what DOM is, why it is a combinatorial optimization problem, and the three trade-offs the challenge asks about:

- solution quality against runtime
- exact solvers against heuristics
- noisy quantum hardware against simulators

---

## Planner view

One page, no mathematics. It says what to do and what it is worth.

| | Leave everything | Apply the 66 moves | Difference |
|---|---|---|---|
| Cases delivered | 1,311,570 | 1,352,341 | +40,771 |
| Fill rate | 90.47% | 93.28% | +2.81 points |
| Customer penalties | $84,749 | $32,333 | −$52,416 |
| Freight cost | $565,479 | $622,880 | +$57,401 |
| **Net value** | **$44,365,994** | **$46,295,828** | **+$1,929,835** |

It lists the largest recommendations one by one with the fill rate before and after, shows which warehouses receive the volume, and ends with three things to check before releasing the plan.

---

## Where the numbers come from

Every figure in these documents was printed by an executed notebook. Nothing is estimated.

| Number | Notebook |
|---|---|
| Baseline, greedy and MILP results | `11_comparison` |
| Solve time and model size | `05_classical` |
| Why moves were rejected | `04_greedy` |
| Quantum results | `06` – `10`, `12` |

Headline: the exact model raises the objective on the 472 focus orders from **$44,365,994** to **$46,295,828** and the fill rate from **90.47%** to **93.28%**, by reassigning **66** orders, solved to the proven best answer in **63.72 seconds**.

---

## Source

All three documents are written in LaTeX and live in the same Overleaf project as the slide deck. They share one style file and read their charts from `../Figures/`.

To rebuild any of them: open the Overleaf project, set the main document to the file you want, and compile with pdfLaTeX.
