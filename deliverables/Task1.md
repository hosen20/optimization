# Task 1 — Key Trade-offs in Nestlé DOM Optimisation

**Distributed Order Management (DOM)** decides, for every focus order that cannot be fully filled at its default Distribution Centre (DC), whether to keep the order or divert it to an alternate DC. The objective maximises fulfilment value:

$$
\sum_{o,d}\bigl(R_o\cdot f_{o,d}-S_{o,d}-P_o(1-f_{o,d})\bigr)x_{o,d}
$$

subject to one-DC-per-order, inventory, dock and throughput capacity constraints.

This note distils the central trade-offs observed across the classical pipeline (Baseline / Greedy / MILP) and the quantum notebooks (Method-2 exact Ising, warm-started QAOA, hybrid RMP).

---

## 1. Solution quality versus runtime

| Method | Focus objective | Δ vs Baseline | Fill rate | Diverted | Runtime | Quality / cost characterisation |
|--------|-----------------|---------------|-----------|----------|---------|---------------------------------|
| Baseline 1 (do-nothing) | \$44,365,994 | 0 | 90.47 % | 0 | 0.21 s | Reference; zero search cost |
| Greedy 2A (revenue sort) | \$44,810,604 | +\$444,610 | 91.28 % | 41 | 0.40 s | Captures ~23 % of reachable gain |
| Greedy 2B (shortfall sort) | \$44,786,479 | +\$420,485 | 91.26 % | 39 | 0.42 s | Slightly weaker ordering |
| Classical MILP (CBC) | **\$46,295,828** | **+\$1,929,835** | **93.28 %** | **66** | 63.72 s | Proven optimum on 472 focus orders |
| Quantum Method-2 (exact Ising, small batches) | matches Greedy on batch | ~+\$1.36 M on 75-order subset | ~97 % on subset | all diverted in batch | < 1 s quantum | Exact ground state of slack-free QUBO |
| Warm-start QAOA + 2-opt (real-data instances) | ties Greedy | \$0 aggregate delta | identical assignment counts | identical | minutes (sim) | Sampling recovers the same local optimum |

**Observations**

- The greedy already extracts the majority of *easy* lift in a fraction of a second. The remaining 3.2 % optimality gap (relative to MILP) requires a global view of capacity coupling and is correspondingly expensive.
- Wall-clock for the exact MILP grows roughly linearly with the number of binaries on this data (≈ 1.4 s → 64 s from 50 to 472 orders). Beyond a few hundred focus orders the CBC branch-and-cut tree becomes the dominant cost.
- Quantum exact diagonalisation (NumPyMinimumEigensolver) is essentially free once the Hamiltonian is built, but is limited to ≤ 20–24 qubits on a laptop. Beyond that one must switch to approximate sampling (QAOA / CVaR-VQE), whose classical optimisation overhead quickly exceeds the MILP runtime for the same instance size.

**Trade-off summary.** For operational daily re-planning the greedy (or a modest local-search improvement of it) is the rational default: near-optimal quality at interactive latency. The MILP is the offline accuracy ceiling and the only method that can certify the residual gap. Quantum formulations become interesting only when (a) the instance is small enough for exact ground-state extraction or (b) a hybrid column-generation / Lagrangian outer loop keeps every quantum sub-problem inside the NISQ / simulator envelope while still coordinating the full focus set.

---

## 2. Exact solvers versus heuristics

**Exact (MILP / Ising ground state)**

- Guarantees global optimality (or a proven bound) for the chosen mathematical model.
- Exposes the true value of coordination: the greedy’s 3.2 % gap widens with instance size because earlier irrevocable decisions leave later high-value moves infeasible.
- Cost: exponential worst-case scaling; on Nestlé data the practical limit for a single CBC solve is a few hundred focus orders.

**Heuristics (Greedy + 2-opt, warm-started QAOA sampling)**

- Linear or low-polynomial runtime; easily re-run under what-if parameter changes (gate thresholds, safety-stock fractions).
- Myopic: once an order is assigned, its stock and dock consumption are never reconsidered. Consequently the rejection log is dominated by the 5 %-lift gate and “SKU not carried” rather than by global capacity contention.
- On the 18–24-qubit real-data instances examined in the QAOA notebook, warm-started sampling + shared 2-opt repair converges to *exactly* the same assignment matrix as Greedy+2-opt. The warm start and the common repair pipeline leave essentially no room for differentiation.

**Implication.** An exact solver is indispensable for measuring the residual opportunity and for generating training / warm-start data. A well-engineered heuristic (or a quantum sampler that is itself warm-started from that heuristic) is the work-horse for production. The two are complementary, not competitors.

---

## 3. Noisy quantum hardware versus simulators

| Aspect | Ideal simulator (Statevector / NumPy) | Current NISQ hardware |
|--------|---------------------------------------|-----------------------|
| Noise | None | Gate errors ~10⁻³, readout errors, decoherence |
| Circuit depth | Unlimited (limited only by classical memory) | Practical depth ≪ 100 two-qubit gates for reliable results |
| Sampling | Exact probability distribution or perfect shots | Finite shots + noise → biased empirical distribution |
| Scalability | 20–25 qubits state-vector; 40–50 qubits tensor-network | 50–100+ physical qubits, but effective logical qubits far fewer |
| Observed outcome on DOM | Exact ground state or zero-gap QAOA on every small batch | Not yet demonstrated; noise would degrade the already-tight warm-start distribution further |

**Consequences for the Nestlé formulation**

- Method 2 (slack-free quadratic penalty) keeps the qubit count equal to the number of pure assignment variables. This is essential: a conventional slack encoding multiplies the qubit requirement by 3–5× and immediately exceeds both simulator and NISQ limits.
- Even with a perfect encoding, the warm-started QAOA distribution is already concentrated near the classical greedy solution. Hardware noise broadens that distribution and increases the fraction of infeasible samples that must be repaired classically, eroding any potential advantage.
- Therefore the only currently realistic quantum contribution is (a) exact ground-state extraction on carefully batched sub-problems (≤ 20 qubits) or (b) a hybrid architecture in which a classical outer loop (column generation, dual averaging, augmented Lagrangian) repeatedly hands a small, high-value Restricted Master Problem to a quantum solver.

**Bottom line.** On the real Nestlé data, at the scales examined, and with the warm-started methodology of the original PoC, quantum sampling does not outperform classical Greedy+2-opt; it reproduces it at far higher computational cost. The scientific value of the quantum notebooks lies in the *formulation* (slack-free capacity encoding, Ising Hamiltonian ready for QAOA / annealing) and in the verification that the classical heuristic is already near-optimal on modest instances. Scaling the hybrid architecture to the full 472-focus-order set while preserving feasibility remains the open engineering challenge.
