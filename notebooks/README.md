# Notebooks

Twelve notebooks. **Each one runs on its own** — it reads the CSV data, does its own work, and prints
its results. No notebook reads another notebook's output, and none of them saves a file.

## Order to read them

| # | Notebook | What it does |
|---|---|---|
| 01 | `01_data_exploration.ipynb` | Describes the seven data files and rebuilds the order funnel |
| 02 | `02_data_cleaning.ipynb` | Prepares the data and states the objective and the seven rules |
| 03 | `03_baseline.ipynb` | Baseline 1: leave every order where it is |
| 04 | `04_greedy.ipynb` | Baseline 2: greedy move heuristic, two orderings, sensitivity |
| 05 | `05_classical.ipynb` | Exact model solved with PuLP and CBC — the accuracy ceiling |
| 06 | `06_Nestle_DOM_Quantum_Investigation_executed.ipynb` | 9-qubit instance checked against every possible answer |
| 07 | `07_Nestle_DOM_Quantum_Method2_executed.ipynb` | The slack-free QUBO encoding |
| 08 | `08_Nestle_DOM_Quantum_Detailed_Method2_executed.ipynb` | The same encoding, one batch shown step by step |
| 09 | `09_Nestle_DOM_Scaled_Quantum_Detailed_executed.ipynb` | 15 batches, 90 orders |
| 10 | `10_DOM_QAOA_vs_Greedy_RealData_executed.ipynb` | QAOA against the greedy on real data |
| 11 | `11_comparison.ipynb` | All results side by side — **no computing, results only** |
| 12 | `12_Nestle_DOM_Hybrid_Quantum_RMP.ipynb` | Hybrid: a classical step proposes options, QAOA picks |

## Getting the data in

Notebooks 01 to 05 look for `input_order data.csv` under the current folder. If it is somewhere else,
set the path at the top of the notebook:

```python
DATA_DIR = "/path/to/DOM-data/input data"
```

Nothing is uploaded from inside a notebook, and nothing is written to disk.

## Running them

Locally:

```bash
pip install -r ../Requirement.txt
jupyter lab
```

In Colab, upload the data folder to `/content` and run the cells top to bottom. Notebook 05 installs
PuLP by itself if it is missing.

## Which notebooks need what

| Notebook | Needs |
|---|---|
| 01 – 04 | numpy, pandas, matplotlib |
| 05 | + pulp (installs itself in Colab) |
| 06 – 10, 12 | + qiskit, qiskit-aer, qiskit-optimization, qiskit-algorithms |
| 11 | pandas, matplotlib only — no data files |

## Notes

Notebooks 02 to 05 repeat the same load-and-prepare section. That repetition is deliberate: it is
what lets each notebook run alone. The numbers they produce are identical because the code is
identical.

Notebook 11 holds the results as typed-in numbers. Nothing is recomputed there, so it opens
instantly and cannot break if a data path changes.
