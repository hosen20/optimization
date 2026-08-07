def build_method2_qubo(data, alpha=1.2e-4):
    n_o, n_d = data["n_orders"], data["n_dcs"]
    qp = QuadraticProgram("DOM_Method2")
    for o in range(n_o):
        for d in range(n_d):
            qp.binary_var(name=f"x_{o}_{d}")
    linear, quadratic = {}, {}
    for o in range(n_o):
        for d in range(n_d):
            var = f"x_{o}_{d}"
            val = data["revenue"][o] * data["fillable"][o, d]
            cost = data["ship_cost"][o, d]
            unmet = data["penalty_if_not"][o] * (1.0 - data["fillable"][o, d])
            linear[var] = linear.get(var, 0.0) - (val - cost - unmet)
    P = 4.0e5
    for o in range(n_o):
        vars_o = [f"x_{o}_{d}" for d in range(n_d)]
        for v in vars_o:
            linear[v] = linear.get(v, 0.0) + P * (1 - 2)
        for i in range(n_d):
            for j in range(i+1, n_d):
                pair = (vars_o[i], vars_o[j])
                quadratic[pair] = quadratic.get(pair, 0.0) + 2 * P
    for d in range(n_d):
        w = data["cases"] * data["fillable"][:, d]
        cap = data["capacity"][d]
        for o in range(n_o):
            var = f"x_{o}_{d}"
            linear[var] = linear.get(var, 0.0) + alpha * (w[o] - cap * w[o])
        for o1 in range(n_o):
            for o2 in range(o1, n_o):
                v1, v2 = f"x_{o1}_{d}", f"x_{o2}_{d}"
                coef = 0.5 * w[o1] * w[o2]
                if o1 == o2:
                    linear[v1] = linear.get(v1, 0.0) + alpha * coef
                else:
                    pair = tuple(sorted([v1, v2]))
                    quadratic[pair] = quadratic.get(pair, 0.0) + alpha * 2 * coef
    qp.minimize(linear=linear, quadratic=quadratic)
    return qp

qp_demo = build_method2_qubo(demo_data)
print(f"QUBO variables (qubits): {qp_demo.get_num_vars()}  (NO slack)")
print(f"Linear terms: {len(qp_demo.objective.linear.to_dict())}")
print(f"Quadratic terms: {len(qp_demo.objective.quadratic.to_dict())}")
print("→ Method 2 confirmed: qubit count = pure assignment variables only.")
