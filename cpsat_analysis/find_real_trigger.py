"""
실제 INFEASIBLE 트리거 — past_5days + balance + scenario 조합 매트릭스
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

CAPS = cal()

def build(num_emp=10, ndays=31, per_emp_balance=False, past_5days=None,
          start_day=4, max_consec_W=None, min_X_per_nurse=None,
          per_emp_past=None):
    """per_emp_past: dict {emp_idx: list of 5 duty ints} — 다른 직원마다 다른 past"""
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
    if per_emp_balance:
        for e in range(num_emp):
            m.Add(sum(iW[e][d] for d in range(ndays)) >= 17)
            m.Add(sum(iW[e][d] for d in range(ndays)) <= 18)
            m.Add(sum(iN[e][d] for d in range(ndays)) >= 6)
            m.Add(sum(iN[e][d] for d in range(ndays)) <= 7)
            m.Add(sum(iX[e][d] for d in range(ndays)) >= 7)
            m.Add(sum(iX[e][d] for d in range(ndays)) <= 8)
    if min_X_per_nurse:
        for e in range(num_emp):
            m.Add(sum(iX[e][d] for d in range(ndays)) >= min_X_per_nurse)

    weights = [81, 27, 9, 3, 1]
    for e in range(num_emp):
        e_past = per_emp_past.get(e) if per_emp_past else past_5days
        for d in range(0 if e_past is not None else start_day, ndays):
            vals = []
            for off in (-4, -3, -2, -1, 0):
                di = d + off
                if di < 0:
                    if e_past is None: vals = None; break
                    vals.append(('c', e_past[5+di]))
                else:
                    vals.append(('v', duty[e][di]))
            if vals is None: continue
            z = m.NewIntVar(0, 242, f'z_{e}_{d}')
            terms = [w*v for (k,v),w in zip(vals, weights)]
            m.Add(z == sum(terms))
            m.AddAllowedAssignments([z], [[k] for k in sorted(P_SET)])
    return m, duty

def quick(m, tl=20):
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = tl
    s.parameters.num_search_workers = 8
    st = s.Solve(m)
    return st, s.WallTime()

NAMES = {cp_model.OPTIMAL: 'OPTIMAL', cp_model.FEASIBLE: 'FEASIBLE',
         cp_model.INFEASIBLE: 'INFEASIBLE', cp_model.UNKNOWN: 'UNKNOWN'}

print("=" * 75)
print("Pattern A: 같은 past 모든 직원에 적용 + per_emp_balance")
print("=" * 75)
scenarios = [
    ('past=None,        bal=YES', None, True),
    ('past=[X,X,X,X,X], bal=YES', [2,2,2,2,2], True),
    ('past=[X,X,X,W,W], bal=YES', [2,2,2,0,0], True),
    ('past=[W,X,X,W,W], bal=YES', [0,2,2,0,0], True),
    ('past=[X,W,W,X,X], bal=YES', [2,0,0,2,2], True),
    ('past=[X,X,W,W,X], bal=YES', [2,2,0,0,2], True),
    ('past=[N,X,X,X,W], bal=YES', [1,2,2,2,0], True),
]
for desc, past, bal in scenarios:
    m, _ = build(per_emp_balance=bal, past_5days=past, start_day=0)
    st, t = quick(m, tl=20)
    print(f"  {desc:40s} → {NAMES.get(st):12s} ({t:.2f}s)")

print("\n" + "=" * 75)
print("Pattern B: 직원마다 다른 past + per_emp_balance (실제 운영 시나리오)")
print("=" * 75)
# 10명의 past가 다 다른 경우. 실제로는 이전 달 마지막 5일에서 옴
import random
random.seed(42)
def random_valid_past():
    """P set에서 랜덤 5일 패턴 뽑기"""
    valid_pasts = list(P_SET)
    v = random.choice(valid_pasts)
    return [(v//81)%3, (v//27)%3, (v//9)%3, (v//3)%3, v%3]

per_emp_past = {e: random_valid_past() for e in range(10)}
print("Sample per_emp_past (W=0, N=1, X=2):")
for e in range(10):
    p = per_emp_past[e]
    print(f"  emp{e}: {[['W','N','X'][x] for x in p]}")
m, _ = build(per_emp_balance=True, per_emp_past=per_emp_past)
st, t = quick(m, tl=30)
print(f"  → {NAMES.get(st)} ({t:.2f}s)")

print("\n=== Pattern B': Random pasts, balance OFF ===")
m, _ = build(per_emp_balance=False, per_emp_past=per_emp_past)
st, t = quick(m, tl=30)
print(f"  → {NAMES.get(st)} ({t:.2f}s)")

print("\n=== Pattern C: 직원 모두 W-heavy past + balance ON ===")
# 모든 직원의 past가 W가 많은 패턴 — 예: WXXWW (P=72), XXWWW (P=216)
W_heavy_pasts = [72, 78, 132, 153, 159, 216, 234, 240, 0, 162]
# decode each
W_heavy = []
for v in W_heavy_pasts:
    W_heavy.append([(v//81)%3, (v//27)%3, (v//9)%3, (v//3)%3, v%3])
per_emp_past_W = {e: W_heavy[e] for e in range(10)}
print("All W-heavy pasts:")
for e in range(10):
    p = per_emp_past_W[e]
    print(f"  emp{e}: {[['W','N','X'][x] for x in p]}")
m, _ = build(per_emp_balance=True, per_emp_past=per_emp_past_W)
st, t = quick(m, tl=30)
print(f"  → {NAMES.get(st)} ({t:.2f}s)")

print("\n=== Pattern D: blocked_N=5 + balance? — but X must be 8 each ===")
# blocked_N 5명 → 그 5명은 X+W만. W=18, X=13 정도 필요 → balance 17~18 깨짐
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
blocked = {0,1,2,3,4}
for e in blocked:
    for d in range(ndays):
        m.Add(iN[e][d] == 0)
# blocked_N으로 N=0이면, 그 5명의 N 총합=0이지만 capacity N=62 필요
# 나머지 5명이 N=62 다 부담 → 직원당 12.4 N → z_rule 위반 가능성
print(f"  blocked_N 5명 → N capacity 62는 나머지 5명이 부담: 12.4 N/nurse")
weights = [81, 27, 9, 3, 1]
for e in range(num_emp):
    for d in range(4, ndays):
        vals = [duty[e][d+off] for off in (-4,-3,-2,-1,0)]
        z = m.NewIntVar(0, 242, f'z_{e}_{d}')
        m.Add(z == sum(w*v for w,v in zip(weights, vals)))
        m.AddAllowedAssignments([z], [[k] for k in sorted(P_SET)])
st, t = quick(m, tl=30)
print(f"  → {NAMES.get(st)} ({t:.2f}s)")
