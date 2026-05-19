"""
LP focused analysis:
- W = 55.48% 고정 시 N/X 가능 범위
- X = 24.52% 고정 시 W/N 가능 범위
- 핵심: X_min = 28.57% (2/7) — 시스템 요구 X=24.52%가 z_rule이 허용하는 X 최소치를 깨고 있는가?
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

def decode(v): return ((v//81)%3, (v//27)%3, (v//9)%3, (v//3)%3, v%3)
def encode(d1,d2,d3,d4,d5): return d1*81+d2*27+d3*9+d4*3+d5

TRANS = []
for v in P_SET:
    d1,d2,d3,d4,d5 = decode(v)
    for d6_name in Z_RULES[v]:
        d6 = DUTY[d6_name]
        v_next = encode(d2,d3,d4,d5,d6)
        if v_next in Z_RULES:
            TRANS.append((v, v_next, d6))

def lp_with_fixed(fixed_W=None, fixed_N=None, fixed_X=None, objective='max_X'):
    s = pywraplp.Solver.CreateSolver('GLOP')
    f = [s.NumVar(0, 1, f'f_{i}') for i in range(len(TRANS))]
    in_flow = {v: [] for v in P_SET}
    out_flow = {v: [] for v in P_SET}
    for i, (u, v, d) in enumerate(TRANS):
        out_flow[u].append(f[i])
        in_flow[v].append(f[i])
    for v in P_SET:
        s.Add(sum(in_flow[v]) == sum(out_flow[v]))
    s.Add(sum(f) == 1)
    W = sum(f[i] for i, (u,v,d) in enumerate(TRANS) if d == 0)
    N = sum(f[i] for i, (u,v,d) in enumerate(TRANS) if d == 1)
    X = sum(f[i] for i, (u,v,d) in enumerate(TRANS) if d == 2)
    if fixed_W is not None: s.Add(W == fixed_W)
    if fixed_N is not None: s.Add(N == fixed_N)
    if fixed_X is not None: s.Add(X == fixed_X)
    if objective == 'max_W': s.Maximize(W)
    elif objective == 'min_W': s.Minimize(W)
    elif objective == 'max_N': s.Maximize(N)
    elif objective == 'min_N': s.Minimize(N)
    elif objective == 'max_X': s.Maximize(X)
    elif objective == 'min_X': s.Minimize(X)
    else: s.Maximize(0)
    st = s.Solve()
    if st != pywraplp.Solver.OPTIMAL: return None
    return (sum(f[i].solution_value() for i, (u,v,d) in enumerate(TRANS) if d == 0),
            sum(f[i].solution_value() for i, (u,v,d) in enumerate(TRANS) if d == 1),
            sum(f[i].solution_value() for i, (u,v,d) in enumerate(TRANS) if d == 2))

target_W = 172/310
target_N = 62/310
target_X = 76/310
print(f"System target: W={target_W:.4f}, N={target_N:.4f}, X={target_X:.4f}")

print("\n=== W = target 고정 시 ===")
res = lp_with_fixed(fixed_W=target_W, objective='min_X')
print(f"min X: W={res[0]:.4f}, N={res[1]:.4f}, X={res[2]:.4f}")
res = lp_with_fixed(fixed_W=target_W, objective='max_X')
print(f"max X: W={res[0]:.4f}, N={res[1]:.4f}, X={res[2]:.4f}")
res = lp_with_fixed(fixed_W=target_W, objective='max_N')
print(f"max N: W={res[0]:.4f}, N={res[1]:.4f}, X={res[2]:.4f}")
res = lp_with_fixed(fixed_W=target_W, objective='min_N')
print(f"min N: W={res[0]:.4f}, N={res[1]:.4f}, X={res[2]:.4f}")

print("\n=== N = target 고정 시 ===")
res = lp_with_fixed(fixed_N=target_N, objective='min_X')
print(f"min X: W={res[0]:.4f}, N={res[1]:.4f}, X={res[2]:.4f}")
res = lp_with_fixed(fixed_N=target_N, objective='max_W')
print(f"max W: W={res[0]:.4f}, N={res[1]:.4f}, X={res[2]:.4f}")

print("\n=== X = target 고정 시 ===")
res = lp_with_fixed(fixed_X=target_X, objective='max_W')
print(f"max W: W={res[0]:.4f}, N={res[1]:.4f}, X={res[2]:.4f}")
res = lp_with_fixed(fixed_X=target_X, objective='min_W')
print(f"min W: W={res[0]:.4f}, N={res[1]:.4f}, X={res[2]:.4f}")

print("\n=== W=target & N=target 동시 ===")
res = lp_with_fixed(fixed_W=target_W, fixed_N=target_N)
if res is None:
    print(f"INFEASIBLE: W={target_W:.4f} AND N={target_N:.4f} 동시 만족 불가 (LP)")
else:
    print(f"FEASIBLE: W={res[0]:.4f}, N={res[1]:.4f}, X={res[2]:.4f}")

# Check the boundary
print("\n=== W=target 고정 X-target 차이 ===")
# X = 1 - W - N
# N min ↔ X max, N max ↔ X min
res = lp_with_fixed(fixed_W=target_W, objective='min_X')
x_min_lp = res[2]
print(f"X_min (LP) at W=target: {x_min_lp:.4f}")
print(f"X required: {target_X:.4f}")
diff = target_X - x_min_lp
print(f"Gap: {diff:+.4f} (target - LP_min)")
if diff < 0:
    print(f"  → INFEASIBLE in LP: need X={target_X:.4f} but z_rule requires X >= {x_min_lp:.4f}")
else:
    print(f"  → LP OK")

print("\n=== W=target 고정 N-target 차이 ===")
res = lp_with_fixed(fixed_W=target_W, objective='max_N')
n_max_lp = res[1]
print(f"N_max (LP) at W=target: {n_max_lp:.4f}")
print(f"N required: {target_N:.4f}")
diff = target_N - n_max_lp
print(f"Gap: {diff:+.4f} (target - LP_max)")

# Find the exact W_max where N = target is achievable
print("\n=== W가 어디까지 가면 N=target이 가능한가 ===")
# binary search
lo, hi = 0.0, 0.7143
for _ in range(40):
    mid = (lo + hi) / 2
    res = lp_with_fixed(fixed_W=mid, fixed_N=target_N)
    if res is None:
        hi = mid
    else:
        lo = mid
print(f"max W s.t. N={target_N:.4f} achievable: {lo:.4f}")
print(f"즉, z_rule 하 W <= {lo*100:.2f}%일 때만 N=20%가 가능")
print(f"시스템 요구 W={target_W*100:.2f}% > {lo*100:.2f}%면 INFEASIBLE")
