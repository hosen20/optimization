# Task 3 — Mathematical Formulation of Nestlé DOM

We present two complementary formulations that appear throughout the classical and quantum notebooks:

1. **Deterministic binary (assignment) model** — the natural MILP solved by CBC.  
2. **Weighted exact-cover / column-selection model** — the Restricted Master Problem (RMP) used by the hybrid quantum column-generation notebooks.

Both encode identical business rules; they differ only in the decision-variable space and therefore in the algorithmic toolbox that can be applied.

---

## 1. Deterministic binary optimisation model

### Decision variables

\[
\begin{align*}
x_{o,d} &\in \{0,1\} && \text{order } o \text{ assigned to DC } d,\\
q_{o,d,s} &\ge 0 && \text{cases of SKU } s \text{ filled for order } o \text{ at DC } d,\\
z_o &\in \{0,1\} && \text{1 if order } o \text{ meets its fill-rate threshold (no penalty)},\\
\operatorname{pen}_o &\ge 0 && \text{penalty charged on order } o.
\end{align*}
\]

### Objective (maximise)

\[
\sum_{o,d,s} \operatorname{price}_{o,s}\, q_{o,d,s}
\;-\;
\sum_o \operatorname{pen}_o
\;-\;
\sum_{o,d} S_{o,d}\, x_{o,d}.
\]

This is exactly Revenue − Penalty − Shipping, the expression evaluated by `objective()` in `dom_model.py`.

### Constraints

| Id | Business rule | Mathematical statement |
|----|---------------|------------------------|
| C1 | At most one DC per order | \(\sum_d x_{o,d}=1\quad\forall o\) |
| C2 | Never fill more than ordered; fill only at chosen DC | \(q_{o,d,s}\le\operatorname{dem}_{o,s}\,x_{o,d}\) |
| C3 | Inventory (5-day forward cover) | \(\sum_{o\in\operatorname{draws}(d,s,u)}q_{o,d,s}\le C_{d,s,u}+\operatorname{GIVE}_{d,s,u}\) |
| C4 | Divert gate (≥ 5 pp *or* ≥ 100 cases) | \(\sum_s q_{o,d,s}\ge\operatorname{need}_o\cdot x_{o,d}\) for non-default \(d\) |
| C5 | Daily pick capacity | linearised pallet-pick inequality |
| C6 | One dock slot per order | \(\sum_{o\text{ on }(d,t)}x_{o,d}\le\operatorname{DockAvail}_{d,t}\) |
| C7 | Penalty only below threshold | big-M linearisation of the step function |

### Solution method

The model is written once in PuLP and solved by the open-source CBC branch-and-cut solver (`gapRel=0`, time limit 900 s). On the full 472-focus-order instance the solver returns a proven optimum in 63.7 s (88 k variables, 2.6 k binaries, 149 k rows).

### Trade-offs

- **Accuracy.** Proven global optimum of the chosen model.  
- **Feasibility.** All seven business constraints are hard; post-solve audit confirms zero violations above solver tolerance.  
- **Runtime.** Acceptable for daily batch planning; becomes the bottleneck beyond a few hundred focus orders.  
- **Scalability.** Number of binaries grows as \(O(|\mathcal{O}|\cdot|\mathcal{D}|)\); continuous variables and stock rows grow faster. Column generation or Benders decomposition would be required for multi-day rolling horizons with thousands of orders.

---

## 2. Weighted exact-cover / column-selection model (RMP)

### Columns

A *column* \(j\) is a concrete (order, DC, fill-vector) triple together with its business value

\[
c_j = R_o\cdot f_{o,d}-S_{o,d}-P_o(1-f_{o,d}).
\]

The classical pricing routine generates, for each focus order, the default column plus a small number of high-value alternate-DC columns (typically ≤ 2 alternates per order to keep the qubit count manageable).

### Decision variables

\[
x_j\in\{0,1\}\qquad\text{column }j\text{ is selected}.
\]

### Restricted Master Problem

\[
\begin{align*}
\max\quad & \sum_j c_j\,x_j \\
\text{s.t.}\quad & \sum_{j\ni o}x_j=1 && \forall o\in\text{batch},\\
& x_j\in\{0,1\}.
\end{align*}
\]

This is a pure set-partitioning / exact-cover integer program. Capacity is either (a) already enforced inside the pricing oracle or (b) dualised and handled by a classical outer loop (Method 5 / Augmented Lagrangian).

### QUBO conversion (for quantum solvers)

Equality constraints are turned into quadratic penalties:

\[
H = -\sum_j c_j x_j + \mu\sum_o\Bigl(\sum_{j\ni o}x_j-1\Bigr)^2.
\]

The binary-to-Ising map \(x=(1-Z)/2\) yields a 2-local Hamiltonian that is handed to QAOA or to an exact eigensolver.

### Solution method

- Classical pricing generates the column pool.  
- Each small batch RMP (≤ 8–12 qubits) is solved by multi-layer QAOA (p=1 or p=2) with COBYLA; the identical QUBO is also solved by `NumPyMinimumEigensolver` to measure the optimality gap.  
- In the executed notebooks the gap is zero on every batch, i.e. QAOA recovers the exact RMP optimum.  
- Feasibility repair and 2-opt local search are applied after measurement.

### Trade-offs relative to the deterministic MILP

| Dimension | Deterministic MILP | Weighted exact-cover RMP |
|-----------|--------------------|--------------------------|
| Variable count | \(O(|\mathcal{O}|\,|\mathcal{D}| + \text{SKUs})\) | \(O(\text{columns})\) — controlled by pricing |
| Capacity handling | Explicit linear inequalities | Pricing or dual outer loop |
| Quantum readiness | Requires slack or Method-2 encoding | Native set-partitioning QUBO |
| Scalability path | Branch-and-cut / decomposition | Column generation + batched quantum RMP |
| Observed quality (small instances) | Optimal | Optimal (gap = 0) |

The exact-cover view is the natural interface to quantum hardware: every qubit corresponds to a business-meaningful column, the Hamiltonian is 2-local, and the classical outer loop can grow to the full focus set while every quantum sub-problem stays inside the simulator / NISQ envelope.

---

## 3. Slack-free capacity encoding (Method 2)

When capacity inequalities must appear *inside* the quantum Hamiltonian, the classical slack-variable construction multiplies the qubit count by \(\lceil\log_2 C\rceil\) per DC. Method 2 replaces the hard inequality by a second-order Taylor expansion of the exponential penalty \(e^{-t}\):

\[
t_d = C_d-\sum_o w_{o,d}x_{o,d},\qquad
\alpha\sum_d\bigl(-t_d+\tfrac12 t_d^2\bigr).
\]

The expansion produces only linear and quadratic terms in the original assignment variables → **zero slack qubits**. A single scalar \(\alpha\sim10^{-4}\) balances business value against capacity pressure. The resulting Ising Hamiltonian is exactly the object solved by the Method-2 notebooks and is directly reusable by QAOA, CVaR-VQE or quantum annealing.

---

## 4. Justification of modelling choices

- **Partial fills as continuous variables** (rather than fixed per column) allow the MILP to express the same feasible region that the greedy explores; otherwise the optimality gap would be meaningless.  
- **C3 implemented as a rolling cover window** (not a strict day-by-day ledger) matches the business document and the greedy’s `avail()` routine; a sensitivity run with the stricter ledger lowers the optimum by ≈ $1.4 M, confirming that inventory modelling is itself a first-order decision.  
- **Warm-start from the classical greedy** biases the QAOA distribution toward a high-quality basin; combined with a shared 2-opt repair it explains why sampling never beats the heuristic on the examined instances. Removing the warm-start (or moving to larger, tightly capacitated batches) is the natural next experiment.
