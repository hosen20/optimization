# Hybrid Classical–Quantum Optimization for Distributed Order Management (DOM)

> A reproducible optimization framework for Distributed Order Management (DOM) that models order reassignment as a constrained combinatorial optimization problem. The project benchmarks classical heuristics, exact optimization, and hybrid quantum-classical approaches (QAOA) on challenge-approved, anonymized Nestlé-style fulfillment data.

---

# In 60 Seconds

## What it is

This project studies **Distributed Order Management (DOM)**, where customer orders must be assigned to distribution centers (DCs) while balancing inventory availability, fulfillment rate, shipping cost, operational constraints, and business penalties.

The optimization problem is formulated as a constrained binary optimization problem and solved using multiple approaches including:

- Default business allocation
- Classical Greedy heuristic
- Exact optimization (QUBO subset)
- Hybrid Quantum-Classical QAOA

---

## What this project does NOT claim

- No quantum advantage claim is made.
- The study does not claim current quantum hardware outperforms classical optimization.
- The objective is to evaluate where quantum optimization is competitive, where it matches classical methods, and where current limitations remain.

---

# Key Findings

| Finding | Summary |
|----------|---------|
| Classical heuristics provide strong baselines | Greedy reassignment significantly improves fulfillment compared to default allocation while maintaining feasible solutions. |
| QAOA reaches near-optimal solutions | On benchmark QUBO instances, QAOA consistently converges within a very small gap of the exact optimum. |
| Warm-start QAOA matches Greedy | On real DOM instances (18–24 qubits), warm-started QAOA consistently reproduced the Greedy+2-opt solution across all evaluated instances. |
| Business objectives improve | Optimized assignments increase fulfillment while reducing shortages and penalties compared to default planning. |
| Real operational constraints matter | Inventory, throughput capacity, shipping costs, and feasibility repair dominate practical solution quality. |

---

# Project Status

This repository contains the complete implementation submitted for the WISER 2026 Quantum Challenge.

Current implementation includes:

- Data preprocessing
- Baseline business allocation
- Classical Greedy reassignment
- Mathematical optimization formulation
- QUBO generation
- Ising Hamiltonian construction
- Warm-start QAOA implementation
- Classical feasibility repair
- Solution comparison framework
- Planner recommendation generation
- Business performance evaluation

Additional documentation, dashboard, and hardware benchmarking are included in this repository.

---

# Challenge Context

Distributed Order Management (DOM) determines how customer orders should be fulfilled across multiple distribution centers.

A planner must simultaneously balance:

- Inventory availability
- Warehouse capacity
- Shipping cost
- Customer service level
- Penalty costs
- Operational feasibility

This naturally becomes a constrained combinatorial optimization problem where every reassignment decision affects many others.

---

# Repository Structure

```
.
├── data/
├── notebooks/
│   ├── 01_data_understanding.ipynb
│   ├── 02_baseline.ipynb
│   ├── 03_greedy.ipynb
│   ├── 04_quantum.ipynb
│   ├── 05_comparison.ipynb
│   └── 06_dashboard.ipynb
│
├── src/
│   ├── preprocessing/
│   ├── classical/
│   ├── quantum/
│   ├── optimization/
│   └── utils/
│
├── dashboard/
│   └── streamlit_app.py
│
├── results/
│
├── docs/
│
└── README.md
```

---

# Methodology

The workflow follows five major stages.

## 1. Data Understanding

- Orders
- SKUs
- Distribution Centers
- Inventory
- Throughput Capacity
- Shipping Costs
- Default Assignments

---

## 2. Classical Baselines

Two benchmark methods are implemented.

### Default Assignment

Business default allocation without optimization.

### Greedy Reassignment

Sequential heuristic that reallocates eligible orders while respecting inventory and operational constraints.

---

## 3. Mathematical Formulation

The optimization problem is formulated as a constrained binary optimization model.

Decision variables represent candidate order-to-DC assignments.

The objective maximizes business value while minimizing penalties and transportation costs subject to:

- Inventory constraints
- Capacity constraints
- Assignment constraints
- Business rules

For tractable subsets, the formulation is converted into a QUBO representation suitable for quantum optimization.

---

## 4. Quantum Optimization

Hybrid quantum-classical optimization is performed using:

- QAOA
- Warm-start initialization
- CVaR objective
- Classical parameter optimization
- Feasibility repair
- Best-of-N sampling

Solutions are compared directly against the classical baselines.

---

## 5. Business Evaluation

Each solution is evaluated using identical business metrics.

- Objective value
- Fill rate
- Orders reassigned
- Shipping cost
- Penalty cost
- Runtime
- Constraint feasibility

---

# Results

The project compares

- Default Assignment
- Classical Greedy
- Exact Optimization
- Hybrid QAOA

using a common objective function and feasibility checks.

Highlights include:

- Significant improvement over default allocation
- Near-optimal quantum solutions on benchmark QUBO instances
- Stable quantum performance across multiple independent runs
- Warm-start QAOA consistently matching Greedy+2-opt on tested real-world subsets

---

# Planner View

The optimization recommends only operationally feasible reassignment decisions.

Each recommendation includes:

- Original Distribution Center
- Recommended Distribution Center
- Expected fulfillment improvement
- Shipping impact
- Business benefit

The planner view translates optimization outputs into actionable logistics decisions.

---

# Dashboard

A Streamlit dashboard provides interactive visualization of:

- Dataset overview
- Baseline comparison
- Classical vs Quantum results
- Planner recommendations
- Fill-rate improvements
- Runtime comparison

---

# Scalability

The project discusses how optimization complexity grows with:

- Number of Orders
- Distribution Centers
- Candidate assignments
- Inventory constraints
- Decision variables (QUBO size)

The report also evaluates:

- Runtime scaling
- Quantum resource requirements
- Practical limitations of current hardware
- Potential decomposition strategies

---

# Limitations

Current limitations include:

- Small QUBO subsets due to available quantum resources
- Warm-start QAOA biases exploration toward classical solutions
- Current noisy quantum hardware limits circuit depth
- Larger industrial-scale instances require decomposition and hybrid workflows

---

# Future Work

Potential extensions include:

- Cold-start QAOA
- Larger benchmark instances
- Improved decomposition strategies
- Advanced feasibility repair
- Robust optimization under demand uncertainty
- Hardware execution on larger quantum devices
- Learning-based candidate generation

---

# Reproducibility

The repository contains:

- Source code
- Jupyter notebooks
- Instructions to reproduce experiments
- Challenge-approved anonymized datasets
- Configuration files
- Result generation scripts

All reported metrics are generated using the same evaluation pipeline and objective function.

---

# Team

(Add team members and individual contributions.)

Example:

| Member | Contribution |
|----------|-------------|
| Member 1 | Classical optimization, mathematical formulation |
| Member 2 | Quantum implementation, QAOA experiments |
| Member 3 | Dashboard, documentation, visualization |

---

# License

This project is intended for the WISER 2026 Quantum Challenge.

Challenge datasets remain subject to the organizer's data usage and confidentiality requirements.

Public submissions include only challenge-approved anonymized data and aggregate metrics.
