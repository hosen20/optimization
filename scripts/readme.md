# scripts

Small standalone pieces used by the quantum notebooks.

| File | What it does |
|---|---|
| `exacdiag.py` | Solves a `QuadraticProgram` to its exact Ising ground state and reports the qubit count and the solve time |

## exacdiag.py

Converts a Qiskit `QuadraticProgram` to a QUBO, then solves it with `NumPyMinimumEigensolver` through
`MinimumEigenOptimizer`. This is exact diagonalisation, so the answer is the true ground state, not a
sample.

It is used as the reference in every quantum notebook: the QAOA result is compared against it to see
whether the variational method found the ground state.

```python
from exacdiag import solve_quantum
x_star, fval = solve_quantum(qp)
```

Exact diagonalisation grows as 2^n, so it is only usable while the batch is small. At 18 qubits it
finishes in about 0.3 seconds, which is why the batches are capped there.

## Requirements

```
qiskit
qiskit-optimization
qiskit-algorithms
```
