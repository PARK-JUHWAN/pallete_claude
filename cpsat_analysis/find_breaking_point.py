"""
per-nurse 균형 (wallet) 강도를 조절하면서 INFEASIBLE 트리거 지점 찾기.
- balance_tol=k: 모든 직원의 W count가 평균 17.2 ± k 이내
- balance_tol=k도 적용하면서 capacity + z_rule 같이 풀기
- INFEASIBLE 되는 가장 느슨한 k 찾기
"""
from ortools.sat.python import cp_model
from datetime import date, timedelta

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
P_SET = set(Z_RULES.keys())

def cal():
    c = []
    start = date(2026, 5, 1)
    hol = {date(2026, 5, 5), date(2026, 5, 24), date(2026, 5, 25)}
    for i in range(31):
        d = start + timedelta(days=i)
        cap = (6,2,2) if (d in hol or d.weekday() in (3,4,5)) else (5,2,3)
        c.append(cap)
    return c

CAPS = cal()  # 31 days of (W, N, X)

def build(num_emp=10, ndays=31, balance_tol_W=None, balance_tol_N=None, balance_tol_X=None,
          past_5days=None, start_day=4):
    m = cp_model.CpModel()
    duty = [[m.NewIntVar(0, 2, f'd_{e}_{d}') for d in range(ndays)] for e in range(num_emp)]
    iW = [[m.NewBoolVar(f'W_{e}_{d}') for d in range(ndays)] for e in range(num_emp)]
    iN = [[m.NewBoolVar(f'N_{e}_{d}') for d in range(ndays)] for e in range(num_emp)]
    iX = [[m.NewBoolVar(f'X_{e}_{d}') for d in range(ndays)] for e in range(num_emp)]
    for e in range(num_emp):
        for d in range(ndays):
            m.Add(duty[e][d] == 0).OnlyEnforceIf(iW[e][d])
            m.Add(duty[e][d] != 0).OnlyEnforceIf(iW[e][d].Not())
            m.Add(duty[e][d] == 1).OnlyEnforceIf(iN[e][d])
            m.Add(duty[e][d] != 1).OnlyEnforceIf(iN[e][d].Not())
            m.Add(duty[e][d] == 2).OnlyEnforceIf(iX[e][d])
            m.Add(duty[e][d] != 2).OnlyEnforceIf(iX[e][d].Not())
            m.AddExactlyOne([iW[e][d], iN[e][d], iX[e][d]])
    for d in range(ndays):
        w, n, x = CAPS[d]
        m.Add(sum(iW[e][d] for e in range(num_emp)) == w)
        m.Add(sum(iN[e][d] for e in range(num_emp)) == n)
        m.Add(sum(iX[e][d] for e in range(num_emp)) == x)

    # per-nurse balance (using floor/ceil bounds around 172/10=17.2)
    if balance_tol_W is not None:
        # avg = 17.2; tol k means each in [17-k, 18+k]
        for e in range(num_emp):
            cnt = sum(iW[e][d] for d in range(ndays))
            m.Add(cnt >= 17 - balance_tol_W)
            m.Add(cnt <= 18 + balance_tol_W)
    if balance_tol_N is not None:
        for e in range(num_emp):
            cnt = sum(iN[e][d] for d in range(ndays))
            m.Add(cnt >= 6 - balance_tol_N)
            m.Add(cnt <= 7 + balance_tol_N)
    if balance_tol_X is not None:
        for e in range(num_emp):
            cnt = sum(iX[e][d] for d in range(ndays))
            m.Add(cnt >= 7 - balance_tol_X)
            m.Add(cnt <= 8 + balance_tol_X)

    weights = [81, 27, 9, 3, 1]
    for e in range(num_emp):
        for d in range(start_day, ndays):
            vals = []
            for off in (-4, -3, -2, -1, 0):
                di = d + off
                if di < 0:
                    if past_5days is None: vals = None; break
                    vals.append(('c', past_5days[5+di]))
                else:
                    vals.append(('v', duty[e][di]))
            if vals is None: continue
            z = m.NewIntVar(0, 242, f'z_{e}_{d}')
            terms = [w*v for (k,v),w in zip(vals, weights)]
            m.Add(z == sum(terms))
            m.AddAllowedAssignments([z], [[k] for k in sorted(P_SET)])
    return m, duty, iW, iN, iX

def solve_quiet(m, tl=20):
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = tl
    s.parameters.num_search_workers = 8
    st = s.Solve(m)
    return st, s.WallTime()

print("=" * 70)
print("balance_tol_W (각 직원 W count가 17~18 ± tol)")
print("=" * 70)
for tol in [None, 5, 4, 3, 2, 1, 0]:
    m, *_ = build(balance_tol_W=tol)
    st, t = solve_quiet(m, tl=30)
    name = {cp_model.OPTIMAL: 'OPTIMAL', cp_model.FEASIBLE: 'FEASIBLE',
            cp_model.INFEASIBLE: 'INFEASIBLE', cp_model.UNKNOWN: 'UNKNOWN'}.get(st, str(st))
    print(f"  balance_tol_W={tol}: {name} ({t:.2f}s)")

print("\n" + "=" * 70)
print("balance_tol_W=0 (W=17~18 정확) + balance_tol_N (N=6~7 ± tol)")
print("=" * 70)
for tol_n in [None, 5, 4, 3, 2, 1, 0]:
    m, *_ = build(balance_tol_W=0, balance_tol_N=tol_n)
    st, t = solve_quiet(m, tl=30)
    name = {cp_model.OPTIMAL: 'OPTIMAL', cp_model.FEASIBLE: 'FEASIBLE',
            cp_model.INFEASIBLE: 'INFEASIBLE', cp_model.UNKNOWN: 'UNKNOWN'}.get(st, str(st))
    print(f"  balance_tol_N={tol_n}: {name} ({t:.2f}s)")

print("\n" + "=" * 70)
print("최대 균형 (W=17~18, N=6~7, X=7~8 모두) — wallet 같은 효과")
print("=" * 70)
for tol_x in [None, 3, 2, 1, 0]:
    m, *_ = build(balance_tol_W=0, balance_tol_N=0, balance_tol_X=tol_x)
    st, t = solve_quiet(m, tl=30)
    name = {cp_model.OPTIMAL: 'OPTIMAL', cp_model.FEASIBLE: 'FEASIBLE',
            cp_model.INFEASIBLE: 'INFEASIBLE', cp_model.UNKNOWN: 'UNKNOWN'}.get(st, str(st))
    print(f"  balance_tol_X={tol_x}: {name} ({t:.2f}s)")

print("\n" + "=" * 70)
print("wallet >=2 rule equivalent — (target - actual >= 2 → fail) → actual >= target - 2")
print("=" * 70)
# target_W = 17.2 → actual >= 17.2 - 2 = 15.2 → actual >= 16
# target_N = 6.2 → actual >= 4.2 → actual >= 5
# target_X = 7.6 → actual >= 5.6 → actual >= 6
# (실제 >2 차이가 fail이라는 wallet 검사는 lower bound로 해석)
print("Adding wallet>=2: W>=16, N>=5, X>=6 per nurse")
m = cp_model.CpModel()
num_emp = 10; ndays = 31
duty = [[m.NewIntVar(0, 2, f'd_{e}_{d}') for d in range(ndays)] for e in range(num_emp)]
iW = [[m.NewBoolVar(f'W_{e}_{d}') for d in range(ndays)] for e in range(num_emp)]
iN = [[m.NewBoolVar(f'N_{e}_{d}') for d in range(ndays)] for e in range(num_emp)]
iX = [[m.NewBoolVar(f'X_{e}_{d}') for d in range(ndays)] for e in range(num_emp)]
for e in range(num_emp):
    for d in range(ndays):
        m.Add(duty[e][d] == 0).OnlyEnforceIf(iW[e][d])
        m.Add(duty[e][d] != 0).OnlyEnforceIf(iW[e][d].Not())
        m.Add(duty[e][d] == 1).OnlyEnforceIf(iN[e][d])
        m.Add(duty[e][d] != 1).OnlyEnforceIf(iN[e][d].Not())
        m.Add(duty[e][d] == 2).OnlyEnforceIf(iX[e][d])
        m.Add(duty[e][d] != 2).OnlyEnforceIf(iX[e][d].Not())
        m.AddExactlyOne([iW[e][d], iN[e][d], iX[e][d]])
for d in range(ndays):
    w, n, x = CAPS[d]
    m.Add(sum(iW[e][d] for e in range(num_emp)) == w)
    m.Add(sum(iN[e][d] for e in range(num_emp)) == n)
    m.Add(sum(iX[e][d] for e in range(num_emp)) == x)
for e in range(num_emp):
    m.Add(sum(iW[e][d] for d in range(ndays)) >= 16)
    m.Add(sum(iN[e][d] for d in range(ndays)) >= 5)
    m.Add(sum(iX[e][d] for d in range(ndays)) >= 6)
weights = [81, 27, 9, 3, 1]
for e in range(num_emp):
    for d in range(4, ndays):
        vals = [duty[e][d+off] for off in (-4,-3,-2,-1,0)]
        z = m.NewIntVar(0, 242, f'z_{e}_{d}')
        m.Add(z == sum(w*v for w,v in zip(weights, vals)))
        m.AddAllowedAssignments([z], [[k] for k in sorted(P_SET)])
st, t = solve_quiet(m, tl=60)
name = {cp_model.OPTIMAL: 'OPTIMAL', cp_model.FEASIBLE: 'FEASIBLE',
        cp_model.INFEASIBLE: 'INFEASIBLE', cp_model.UNKNOWN: 'UNKNOWN'}.get(st, str(st))
print(f"  Result: {name} ({t:.2f}s)")
