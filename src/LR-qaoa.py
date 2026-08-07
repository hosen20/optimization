def build_ising(data, alpha=None):
    n_o, n_d = data["n_orders"], data["n_dcs"]
    n = n_o * n_d
    if alpha is None:
        typ_val = np.mean(data["revenue"] * np.max(data["fillable"], axis=1))
        typ_w = np.mean(data["cases"]) + 1
        alpha = max(5e-5, typ_val / (typ_w ** 2 * 20))
    Q = {}
    def add_q(i, j, c):
        if i > j: i, j = j, i
        Q[(i, j)] = Q.get((i, j), 0.0) + c
    for o in range(n_o):
        for d in range(n_d):
            idx = o * n_d + d
            v = (data["revenue"][o]*data["fillable"][o,d] - data["ship_cost"][o,d]
                 - data["penalty_if_not"][o]*(1 - data["fillable"][o,d]))
            add_q(idx, idx, -v)
    P = 5e5
    for o in range(n_o):
        idxs = [o*n_d + d for d in range(n_d)]
        for i in idxs: add_q(i, i, P*(1 - 2))
        for a in range(n_d):
            for b in range(a+1, n_d): add_q(idxs[a], idxs[b], 2*P)
    for d in range(n_d):
        w = data["cases"] * data["fillable"][:, d]
        C = data["capacity"][d]
        idxs = [o*n_d + d for o in range(n_o)]
        for o in range(n_o): add_q(idxs[o], idxs[o], alpha*(w[o] - C*w[o]))
        for o1 in range(n_o):
            for o2 in range(o1, n_o):
                coef = 0.5 * w[o1] * w[o2]
                if o1 == o2: add_q(idxs[o1], idxs[o1], alpha*coef)
                else: add_q(idxs[o1], idxs[o2], alpha*2*coef)
    h = np.zeros(n); J = {}; offset = 0.0
    for (i, j), q in Q.items():
        if i == j:
            offset += q/2; h[i] -= q/2
        else:
            offset += q/4; h[i] -= q/4; h[j] -= q/4
            J[(i, j)] = J.get((i, j), 0.0) + q/4
    ising = {}
    for i in range(n):
        if abs(h[i]) > 1e-12: ising[(i, i)] = h[i]
    for (i, j), c in J.items():
        if abs(c) > 1e-12: ising[(i, j)] = c
    return ising, offset, n, alpha
def ws_angles_from_greedy(data, A_gr, epsilon=0.1):
    n_o, n_d = data["n_orders"], data["n_dcs"]
    angles = []
    for o in range(n_o):
        for d in range(n_d):
            x = float(A_gr[o, d]); x = min(max(x, epsilon), 1 - epsilon)
            angles.append(2*np.arcsin(np.sqrt(x)))
    return angles
def build_lr_qaoa_circuit(n_qubits, ising, p, ws_angles=None):
    gammas = ParameterVector("g", p); betas = ParameterVector("b", p)
    qc = QuantumCircuit(n_qubits)
    if ws_angles is not None:
        for i, th in enumerate(ws_angles): qc.ry(th, i)
    else:
        qc.h(range(n_qubits))
    for layer in range(p):
        for (i, j), coef in ising.items():
            if i == j: qc.rz(2*gammas[layer]*float(coef), i)
            else: qc.rzz(2*gammas[layer]*float(coef), i, j)
        if ws_angles is not None:
            for i, th in enumerate(ws_angles): qc.ry(-th, i)
            qc.rz(-2*betas[layer], range(n_qubits))
            for i, th in enumerate(ws_angles): qc.ry(th, i)
        else:
            qc.rx(-2*betas[layer], range(n_qubits))
    qc.measure_all()
    return qc, gammas, betas
def sample_qaoa(qc, gammas, betas, delta_g, delta_b, p, backend, shots):
    g_vals = np.arange(1, p+1) * delta_g / p
    b_vals = np.arange(1, p+1)[::-1] * delta_b / p
    bind = {gammas[i]: g_vals[i] for i in range(p)}
    bind.update({betas[i]: b_vals[i] for i in range(p)})
    bound = qc.assign_parameters(bind)
    tqc = transpile(bound, backend=backend, optimization_level=1)
    result = backend.run(tqc, shots=shots).result()
    return result.get_counts()
def bitstring_to_A(bitstr, data):
    n_o, n_d = data["n_orders"], data["n_dcs"]
    n = n_o * n_d
    bits = bitstr[::-1] if len(bitstr) == n else bitstr
    if len(bits) < n: bits = bits.zfill(n)
    A = np.zeros((n_o, n_d))
    for o in range(n_o):
        chunk = bits[o*n_d:(o+1)*n_d]
        vals = [int(c) for c in chunk]
        if sum(vals) == 0: continue
        A[o, int(np.argmax(vals))] = 1
    return A
def best_of_n(counts, data, top_k=100):
    ranked = sorted(counts.items(), key=lambda kv: -kv[1])[:top_k]
    best_obj, best_A, best_m, n_feas = -1e99, None, None, 0
    for bitstr, cnt in ranked:
        A = bitstring_to_A(bitstr, data)
        A = two_opt(A, data, passes=4)
        A = force_feasible(A, data)
        m = metrics(A, data)
        if m["violations"] > 1e-6: continue
        n_feas += 1
        if m["objective"] > best_obj:
            best_obj, best_A, best_m = m["objective"], A, m
    return best_A, best_m, n_feas, len(ranked)
def energy_from_counts(counts, ising, offset):
    total = sum(counts.values()); e = 0.0
    for bitstr, cnt in counts.items():
        bits = bitstr[::-1]
        n = max((max(i, j) for (i, j) in ising.keys()), default=-1) + 1
        if len(bits) < n: bits = bits.zfill(n)
        zs = [1 - 2*int(bits[i]) for i in range(n)]
        v = offset
        for (i, j), c in ising.items():
            if i == j: v += c*zs[i]
            else: v += c*zs[i]*zs[j]
        e += v * cnt / total
    return e
print("QUBO / Ising / LR-QAOA functions defined.")
