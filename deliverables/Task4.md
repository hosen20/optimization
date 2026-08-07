# Task 4 — Scaling and Noise Analysis

## 1. Growth of variables / qubits

### Deterministic assignment model

Let \(n=|\mathcal{O}|\) (focus orders), \(m=|\mathcal{D}|\) (candidate DCs), \(s\) average SKUs per order, \(T\) planning days.

| Quantity | Asymptotic growth | Concrete Nestlé numbers (n=472) |
|----------|-------------------|---------------------------------|
| Binary assignment vars \(x_{o,d}\) | \(O(nm)\) | ≈ 2 300 candidate options |
| Continuous fill vars \(q_{o,d,s}\) | \(O(nms)\) | ≈ 85 000 |
| Stock rows (C3) | \(O(nms\cdot W)\) (W = cover window) | ≈ 60 000 |
| Total MIP variables | \(O(nms)\) | 88 342 |
| Total MIP rows | \(O(nms)\) | 148 663 |

### Exact-cover / column model

| Quantity | Growth | Control knob |
|----------|--------|--------------|
| Columns generated per order | \(1+k\) (k alternates) | pricing depth |
| Qubits per batch RMP | \(O(b\cdot k)\) where b = batch size | batch size & column reduction |
| Observed | 8–12 qubits per batch | max_qubits = 8 in the hybrid notebook |

### Method-2 (slack-free) Ising

Qubit count = number of pure assignment variables = \(n_{\text{batch}}\times m_{\text{batch}}\).  
A conventional binary-expanded slack formulation would multiply this figure by \(3\)–\(5\times\) (capacities \(10^4\)–\(10^5\)), rendering even a 6-order × 3-DC instance intractable on a laptop simulator.

---

## 2. Observed performance versus size

### Classical MILP (CBC)

| Focus orders | Binaries | Wall-clock | Status | Gap vs same-size greedy |
|--------------|----------|------------|--------|-------------------------|
| 50 | 227 | 1.4 s | Optimal | +0.84 % |
| 100 | 458 | 6.4 s | Optimal | +2.08 % |
| 200 | 920 | 18.5 s | Optimal | +3.11 % |
| 300 | 1 472 | 35.1 s | Optimal | +3.12 % |
| 472 | 2 594 | 63.7 s | Optimal | +3.21 % |

Wall-clock grows roughly linearly with binaries on this data; the optimality gap of the greedy *widens* with size, confirming that coordination value increases.

### Quantum exact diagonalisation

Feasible up to ≈ 20–24 qubits (state-vector / dense NumPy). Beyond that memory and time become prohibitive. All Method-2 notebooks therefore batch the focus set.

### QAOA sampling

- Depth p=1–2, COBYLA, StatevectorSampler.  
- On every 3-order batch the measured optimality gap versus the exact eigensolver is **zero**.  
- Warm-started Linear-Ramp QAOA on 18–24-qubit real-data instances recovers exactly the Greedy+2-opt assignment (0 wins / 6 ties / 0 losses).  
- Runtime per batch is already higher than classical exact on the same small QP; the advantage, if any, can appear only when the batch size exceeds the reach of classical exact solvers while remaining inside the quantum device’s coherence window.

---

## 3. Practical limitations

1. **Qubit / variable explosion**  
   Full 472-order assignment model exceeds current quantum hardware by more than an order of magnitude. Even the classical MILP becomes inconvenient for multi-day rolling horizons or stochastic demand.

2. **Noise on real hardware**  
   Current NISQ error rates (gate ~10⁻³, limited coherence) broaden the QAOA output distribution. Because the warm-start already concentrates probability mass near the classical greedy solution, additional noise increases the fraction of samples that fail capacity or one-hot constraints and must be repaired classically—eroding any potential quantum advantage.

3. **Myopic pricing / batching**  
   Independent batch RMPs ignore capacity coupling *across* batches. A pure batch-and-aggregate scheme can therefore produce globally infeasible solutions or leave value on the table; a dual outer loop (Lagrangian / Augmented Lagrangian) is required to restore coordination.

4. **Parameter sensitivity**  
   The Method-2 penalty weight \(\alpha\), the exact-cover penalty \(\mu\), and the divert gate (5 pp / 100 cases) all affect both feasibility and objective. No automatic tuning loop is present in the current notebooks.

5. **Inventory modelling ambiguity**  
   The business document’s 5-day cover window versus a strict day-by-day ledger changes the MILP optimum by ≈ $1.4 M. Any quantum encoding inherits the same modelling choice.

---

## 4. Concrete improvement proposals

### A. Classical pre-processing & column reduction (immediate)

- Rank candidate (order, DC) pairs by a fast proxy (revenue × expected COF − shipping − penalty).  
- Keep only the top-k columns per order (k=2 already used in the hybrid RMP notebook).  
- Eliminate columns that violate the divert gate a priori.  
→ Reduces qubits per batch and tightens the LP relaxation of the RMP.

### B. Sliding-window / overlapping batches + dual coordination

- Process focus orders in overlapping windows of 8–12 orders.  
- Dualise capacity constraints; pass dual prices to the next window (or to a global dual-ascent loop).  
- This is precisely the Method-5 / Cutting-Slack architecture already sketched in the theoretical sections of the Method-2 notebooks.

### C. Hybrid “Greedy residual → quantum core”

- Run the full-scale greedy (or a fast LP relaxation).  
- Identify the residual set of orders that are capacity-critical or that the greedy left poorly filled.  
- Hand only that residual core (typically ≪ 50 orders) to a Method-2 quantum solver or a small MILP.  
- Empirically the absolute lift on the top 75 high-value focus orders already exceeds the full-data greedy improvement; concentrating quantum effort on that core is therefore high-leverage.

### D. Parameter & feasibility co-optimisation

- Treat \(\alpha\) (Method 2) and \(\mu\) (exact-cover) as hyperparameters; outer Bayesian optimisation or simple grid search on a validation set of historical days.  
- After quantum sampling, apply a *shared* classical repair (2-opt + force-feasible) identical to the one used by the pure classical heuristic—guaranteeing that every returned solution is business-feasible and enabling a fair quality comparison.

### E. Hardware-aware compilation (medium-term)

- Map the 2-local Ising Hamiltonian onto the native connectivity of the target QPU (or annealer) with a modest number of SWAP networks.  
- Use error-mitigation (zero-noise extrapolation, readout calibration) and CVaR aggregation of the lowest-energy fraction of shots.  
- Because Method 2 already minimises qubit count, the same Hamiltonian can be moved unchanged from the laptop eigensolver onto a future larger device.

---

## 5. Summary

The classical MILP supplies the accuracy ceiling and the scaling baseline. Quantum methods, at the scales examined, match the best classical heuristics exactly while demonstrating a clean, slack-free encoding and a hybrid master/pricing skeleton. The dominant remaining obstacles are (i) capacity coordination across batches and (ii) noise resilience on real hardware. The five concrete techniques above—column reduction, dualised sliding windows, residual-core extraction, automated parameter search, and hardware-aware compilation—address those obstacles without abandoning the formulations already validated on real Nestlé data.
