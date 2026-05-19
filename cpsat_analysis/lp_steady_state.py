"""
z_rule 하 정상상태 W:N:X 비율 LP 분석
- 상태: P set 52개 윈도우
- 전이: 윈도우 v=(d1..d5) → 윈도우 v'=(d2..d6) where d6 ∈ Z_RULES[v]
- 변수: 각 전이 (v,v')의 long-run flow f
- 제약: in-flow = out-flow (각 상태), sum f = 1
- 목적: W/N/X frequency max/min

핵심 질문: 시스템 평균 W=172/310≈55.5%가 z_rule 하 가능 범위 안에 있는가?
"""
from ortools.linear_solver import pywraplp

Z_RULES = {
    0: ['X'], 2: ['X'], 4: ['X'], 8: ['W','N','X'],
    13: ['X'], 14: ['X'], 24: ['W','N'], 25: ['N'], 26: ['W','N','X'],
    40: ['X'], 41: ['X'], 44: ['W','N','X'],
    72: ['W','N','X'], 73: ['N'], 76: ['N','X'], 78: ['W','N'], 79: ['N'], 80: ['W','N','X'],
    121: ['X'], 122: ['X'], 125: ['W','N','X'],
    132: ['W','N'], 133: ['N'], 134: ['W','N','X'],
    153: ['W','N','X'], 154: ['N'], 157: ['N','X'], 159: ['W','N'], 160: ['N'], 161: ['W','N','X'],
    162: ['W','X'], 163: ['N'], 164: ['X'], 166: ['N','X'], 170: ['W','N','X'],
    175: ['N','X'], 176: ['X'],
    202: ['N','X'], 203: ['X'], 206: ['W','N','X'],
    216: ['W','N','X'], 217: ['N'], 218: ['X'], 220: ['N','X'],
    229: ['N','X'], 230: ['X'],
    234: ['W','N','X'], 235: ['N'], 238: ['N','X'], 240: ['W','N'], 241: ['N'], 242: ['W','N','X'],
}
DUTY = {'W': 0, 'N': 1, 'X': 2}
P_SET = sorted(Z_RULES.keys())

def decode(v):
    return ((v//81)%3, (v//27)%3, (v//9)%3, (v//3)%3, v%3)

def encode(d1,d2,d3,d4,d5):
    return d1*81 + d2*27 + d3*9 + d4*3 + d5

# Build transitions: (v, d6) → v'
TRANS = []
for v in P_SET:
    d1,d2,d3,d4,d5 = decode(v)
    for d6_name in Z_RULES[v]:
        d6 = DUTY[d6_name]
        v_next = encode(d2,d3,d4,d5,d6)
        # v_next must be in P (else it's an "edge to nowhere")
        if v_next in Z_RULES:
            TRANS.append((v, v_next, d6))

print(f"Total transitions: {len(TRANS)}")
print(f"  → W transitions: {sum(1 for _,_,d in TRANS if d==0)}")
print(f"  → N transitions: {sum(1 for _,_,d in TRANS if d==1)}")
print(f"  → X transitions: {sum(1 for _,_,d in TRANS if d==2)}")

def solve_freq(maximize_duty=None, minimize_duty=None):
    """
    maximize_duty / minimize_duty: 0=W, 1=N, 2=X, or None
    Returns: (status, W_freq, N_freq, X_freq)
    """
    solver = pywraplp.Solver.CreateSolver('GLOP')
    f = {}
    for i, (u, v, d) in enumerate(TRANS):
        f[i] = solver.NumVar(0, 1, f'f_{i}')

    # flow conservation per state
    in_flow = {v: [] for v in P_SET}
    out_flow = {v: [] for v in P_SET}
    for i, (u, v, d) in enumerate(TRANS):
        out_flow[u].append(f[i])
        in_flow[v].append(f[i])
    for v in P_SET:
        solver.Add(sum(in_flow[v]) == sum(out_flow[v]))

    # total flow (per step) = 1
    solver.Add(sum(f[i] for i in range(len(TRANS))) == 1)

    # objective: freq of specific duty
    W_freq = sum(f[i] for i, (u,v,d) in enumerate(TRANS) if d == 0)
    N_freq = sum(f[i] for i, (u,v,d) in enumerate(TRANS) if d == 1)
    X_freq = sum(f[i] for i, (u,v,d) in enumerate(TRANS) if d == 2)

    if maximize_duty == 0:
        solver.Maximize(W_freq)
    elif minimize_duty == 0:
        solver.Minimize(W_freq)
    elif maximize_duty == 1:
        solver.Maximize(N_freq)
    elif minimize_duty == 1:
        solver.Minimize(N_freq)
    elif maximize_duty == 2:
        solver.Maximize(X_freq)
    elif minimize_duty == 2:
        solver.Minimize(X_freq)
    else:
        solver.Maximize(W_freq)

    status = solver.Solve()
    if status != pywraplp.Solver.OPTIMAL:
        return (status, None, None, None)
    return (status, W_freq.solution_value() if hasattr(W_freq, 'solution_value') else sum(f[i].solution_value() for i, (u,v,d) in enumerate(TRANS) if d == 0),
            sum(f[i].solution_value() for i, (u,v,d) in enumerate(TRANS) if d == 1),
            sum(f[i].solution_value() for i, (u,v,d) in enumerate(TRANS) if d == 2))

print("\n=== z_rule 정상상태 frequency 범위 ===")
target = 172/310  # 0.555
target_N = 62/310
target_X = 76/310
print(f"시스템 평균 target: W={target:.4f} ({target*100:.2f}%), N={target_N:.4f}, X={target_X:.4f}")

for d_name, d in DUTY.items():
    st, w, n, x = solve_freq(maximize_duty=d)
    w_pct = sum(0 if v is None else 0 for v in [w])  # unused
    if w is None:
        print(f"max {d_name}: INFEASIBLE")
        continue
    print(f"max {d_name}-freq: W={w:.4f}, N={n:.4f}, X={x:.4f}")
    st, w, n, x = solve_freq(minimize_duty=d)
    print(f"min {d_name}-freq: W={w:.4f}, N={n:.4f}, X={x:.4f}")

# Constrained: enforce W = target, check feasibility
print("\n=== 시스템 target 만족 가능 여부 ===")
solver = pywraplp.Solver.CreateSolver('GLOP')
f = {i: solver.NumVar(0, 1, f'f_{i}') for i in range(len(TRANS))}
in_flow = {v: [] for v in P_SET}
out_flow = {v: [] for v in P_SET}
for i, (u, v, d) in enumerate(TRANS):
    out_flow[u].append(f[i])
    in_flow[v].append(f[i])
for v in P_SET:
    solver.Add(sum(in_flow[v]) == sum(out_flow[v]))
solver.Add(sum(f[i] for i in range(len(TRANS))) == 1)
W_freq = sum(f[i] for i, (u,v,d) in enumerate(TRANS) if d == 0)
N_freq = sum(f[i] for i, (u,v,d) in enumerate(TRANS) if d == 1)
X_freq = sum(f[i] for i, (u,v,d) in enumerate(TRANS) if d == 2)
# Exact target
solver.Add(W_freq == target)
solver.Add(N_freq == target_N)
solver.Add(X_freq == target_X)
solver.Maximize(0)
st = solver.Solve()
if st == pywraplp.Solver.OPTIMAL:
    print(f"YES — z_rule이 시스템 target (W=55.5%, N=20.0%, X=24.5%) 정확히 만족 가능 (LP)")
else:
    print(f"NO — LP infeasible")

# Looser: ε tolerance
print("\n=== ε tolerance ===")
for eps in [0.0, 0.001, 0.01, 0.05, 0.1]:
    solver = pywraplp.Solver.CreateSolver('GLOP')
    f = {i: solver.NumVar(0, 1, f'f_{i}') for i in range(len(TRANS))}
    in_flow = {v: [] for v in P_SET}
    out_flow = {v: [] for v in P_SET}
    for i, (u, v, d) in enumerate(TRANS):
        out_flow[u].append(f[i])
        in_flow[v].append(f[i])
    for v in P_SET:
        solver.Add(sum(in_flow[v]) == sum(out_flow[v]))
    solver.Add(sum(f[i] for i in range(len(TRANS))) == 1)
    W_freq = sum(f[i] for i, (u,v,d) in enumerate(TRANS) if d == 0)
    solver.Add(W_freq >= target - eps)
    solver.Add(W_freq <= target + eps)
    solver.Maximize(0)
    st = solver.Solve()
    result = 'OK' if st == pywraplp.Solver.OPTIMAL else 'FAIL'
    print(f"  W ∈ [{target-eps:.4f}, {target+eps:.4f}] → {result}")
