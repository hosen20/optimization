# Dashboard

A small Streamlit app that walks through the planner workflow.

Everything it shows is **fixed**. The numbers live in `results.py` and were produced by the
notebooks, so the app opens instantly, needs no data files, and cannot break if a path changes.

## Running it

```bash
pip install streamlit plotly pandas numpy
cd dashboard
streamlit run app.py
```

It opens at `http://localhost:8501`. Press `Ctrl+C` in the terminal to stop it.

If you already installed the project requirements, streamlit and plotly are included:

```bash
pip install -r ../Requirement.txt
```

## The six pages

| Page | What it shows |
|---|---|
| **Dataset overview** | The seven files, the eight DCs, and the funnel from 1,109 orders to 472 |
| **Method comparison** | Baseline, greedy and exact side by side, plus the three quantum results |
| **Planner view** | The 66 recommended moves in business language |
| **Fill rate and objective** | What each method buys, what it costs, and why most moves are blocked |
| **Runtime** | How long each method takes and how the exact model grows |
| **Order and DC flow** | Where orders come from and go, with a flow diagram and a per-order lookup |

## Files

| File | What it is |
|---|---|
| `app.py` | The whole app. One file, one page at a time from the sidebar. |
| `results.py` | Every number the app shows, with a note on which notebook produced it. |

The app also reads the charts in `../Figures/` when they are present, and falls back to drawing its
own if they are not.

## Changing a number

Edit `results.py`. Every block is a small pandas DataFrame or a dict with a comment saying where it
came from. Nothing is computed at run time, so a change appears as soon as the page reloads.

## Headline numbers

| | |
|---|---|
| Leave everything alone | \$44,365,994 · 90.47% fill |
| Greedy 2A | \$44,810,604 · 91.28% fill · 41 moves · 0.40s |
| Exact MILP | \$46,295,828 · 93.28% fill · 66 moves · 63.72s |
| Quantum, 15 batches | +\$1,358,671 on 75 orders · 0 violations · 1.07s |
