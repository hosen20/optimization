# Presentation

`Wiser_Nestle_presentation.pdf` — the slide deck for the challenge submission, 7 slides, 16:9.

## What is on each slide

| # | Slide | Content |
|---|---|---|
| 1 | Title | The headline numbers for the classical and the quantum work |
| 2 | The problem, and why it is hard | The funnel, and why orders cannot be decided one at a time |
| 3 | Two ways to write the same model | The binary model and the QUBO side by side |
| 4 | Classical results, and how they scale | The comparison table and the scaling chart |
| 5 | Quantum: the encoding, and proving it is right | No slack qubits, and the check against every possible answer |
| 6 | Quantum at scale | Batching, the 15-batch result, and the hybrid method |
| 7 | Limits and next steps | What is missing from the data, and what to do next |

## Source

The deck is written in LaTeX Beamer. The source file and its figures are in the Overleaf project
that also holds the report, the business summary and the planner view. Figures come from
`../Figures/`.

To rebuild: open the Overleaf project, set the main document to the slides file, and compile with
pdfLaTeX.

## Two things the deck states plainly

The exact solver moves 66 orders against the greedy's 41 and still pays \$15,285 less in extra
freight, because planning all orders together allows cheaper lanes and connected moves.

The quantum solver **matches** the greedy on the batched run — the difference is \$0 on every batch.
At 18 qubits both methods find the same best answer, so the result shows the encoding is correct, not
that quantum is faster.
