def solve_quantum(qp: QuadraticProgram):
    qubo = QuadraticProgramToQubo().convert(qp)
    print(f"Ising / QUBO size : {qubo.get_num_vars()} qubits")
    solver = NumPyMinimumEigensolver()
    algo   = MinimumEigenOptimizer(solver)
    t0 = time.time()
    result = algo.solve(qubo)
    elapsed = time.time() - t0
    print(f"Exact diagonalisation finished in {elapsed:.2f} s")
    print(f"Status : {result.status}")
    return result.x, result.fval

x_star, fval = solve_quantum(qp)
print(f"\nGround-state bit-string (first 18 bits):\n{x_star.astype(int)}")
