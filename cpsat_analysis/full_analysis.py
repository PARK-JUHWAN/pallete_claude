"""
종합 분석:
1) FEASIBLE 솔루션의 per-nurse 분포 (z_rule 한계에 어떻게 적응했는지)
2) Capacity X 증가 시 안정성
3) past_5days 다양화 시 INFEASIBLE 트리거 패턴
4) 시나리오 A/B/C 검증 (blocked_N 포함)
"""
from ortools.sat.python import cp_model
from datetime import date, timedelta
from collections import Counter

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
INV = {0: 'W', 1: 'N', 2: 'X'}
P_SET = set(Z_RULES.keys())

def build_calendar(holidays=None):
    if holidays is None:
        holidays = {date(2026, 5, 5), date(2026, 5, 24), date(2026, 5, 25)}
    cal = []
    start = date(2026, 5, 1)
    for i in range(31):
        d = start + timedelta(days=i)
        wd = d.weekday()
        if d in holidays or wd in (3, 4, 5):
            cap = (6, 2, 2)
        else:
            cap = (5, 2, 3)
        cal.append((d, wd, cap))
    return cal

CAL = build_calendar()

def build_model(num_emp=10, ndays=31, capacity_override=None,
                blocked_N=None, special=None, with_zrule=True,
                past_5days=None, start_day=4):
    """
    capacity_override: list of (W, N, X) per day, or None to use CAL
    blocked_N: set of employee indices that cannot do N
    special: dict {emp: {'N_allowed': bool, 'extra_X': int}} — extra X days
    """
    m = cp_model.CpModel()
    duty = [[m.NewIntVar(0, 2, f'd_e{e}_d{d}') for d in range(ndays)] for e in range(num_emp)]
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

    caps = capacity_override if capacity_override else [c[2] for c in CAL]
    for d in range(ndays):
        w_cap, n_cap, x_cap = caps[d]
        m.Add(sum(iW[e][d] for e in range(num_emp)) == w_cap)
        m.Add(sum(iN[e][d] for e in range(num_emp)) == n_cap)
        m.Add(sum(iX[e][d] for e in range(num_emp)) == x_cap)

    if blocked_N:
        for e in blocked_N:
            for d in range(ndays):
                m.Add(iN[e][d] == 0)

    if with_zrule:
        weights = [81, 27, 9, 3, 1]
        for e in range(num_emp):
            for d in range(start_day, ndays):
                vals = []
                for off in (-4, -3, -2, -1, 0):
                    di = d + off
                    if di < 0:
                        if past_5days is None:
                            vals = None; break
                        vals.append(('c', past_5days[5 + di]))
                    else:
                        vals.append(('v', duty[e][di]))
                if vals is None: continue
                z = m.NewIntVar(0, 242, f'z_e{e}_d{d}')
                terms = []
                for (k, v), w in zip(vals, weights):
                    terms.append(w * v)
                m.Add(z == sum(terms))
                m.AddAllowedAssignments([z], [[k] for k in sorted(P_SET)])

    return m, duty, iW, iN, iX

def solve(model, time_limit=30.0, workers=8):
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = time_limit
    s.parameters.num_search_workers = workers
    st = s.Solve(model)
    name = {cp_model.OPTIMAL: 'OPTIMAL', cp_model.FEASIBLE: 'FEASIBLE',
            cp_model.INFEASIBLE: 'INFEASIBLE', cp_model.UNKNOWN: 'UNKNOWN'}.get(st, str(st))
    return st, name, s

def analyze_solution(s, duty, num_emp, ndays):
    per_nurse = []
    for e in range(num_emp):
        sched = [s.Value(duty[e][d]) for d in range(ndays)]
        c = Counter(sched)
        per_nurse.append({'W': c[0], 'N': c[1], 'X': c[2], 'sched': sched})
    return per_nurse

def verify_zrule(sched, past_5days=None):
    """Verify a single nurse's schedule respects z_rule (5-day windows ∈ P)."""
    violations = 0
    for d in range(len(sched)):
        if d - 4 < 0:
            if past_5days is None: continue
            window = [past_5days[5 + d + off] if d + off < 0 else sched[d + off]
                      for off in (-4, -3, -2, -1, 0)]
        else:
            window = sched[d-4:d+1]
        z_val = sum(w * v for w, v in zip([81, 27, 9, 3, 1], window))
        if z_val not in P_SET:
            violations += 1
    return violations

print("=" * 70)
print("STEP 1: Pure capacity + z_rule (past=None) — baseline")
print("=" * 70)
m, duty, iW, iN, iX = build_model(num_emp=10, with_zrule=True, past_5days=None)
st, name, s = solve(m, time_limit=30.0)
print(f"Result: {name}  ({s.WallTime():.2f}s)")
if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    per_nurse = analyze_solution(s, duty, 10, 31)
    print(f"\nPer-nurse distribution:")
    Ws = [n['W'] for n in per_nurse]; Ns = [n['N'] for n in per_nurse]; Xs = [n['X'] for n in per_nurse]
    print(f"  W: min={min(Ws)} max={max(Ws)} avg={sum(Ws)/10:.1f}  → range={max(Ws)-min(Ws)}")
    print(f"  N: min={min(Ns)} max={max(Ns)} avg={sum(Ns)/10:.1f}  → range={max(Ns)-min(Ns)}")
    print(f"  X: min={min(Xs)} max={max(Xs)} avg={sum(Xs)/10:.1f}  → range={max(Xs)-min(Xs)}")
    print(f"\n  Per-nurse W%: {[f'{w/31*100:.0f}%' for w in Ws]}")
    print(f"  Per-nurse N%: {[f'{n/31*100:.0f}%' for n in Ns]}")
    print(f"  Per-nurse X%: {[f'{x/31*100:.0f}%' for x in Xs]}")
    viols = sum(verify_zrule(n['sched']) for n in per_nurse)
    print(f"\n  z_rule violations: {viols} (should be 0)")

print("\n" + "=" * 70)
print("STEP 2: 시나리오 A — 단순 (현재 capacity 유지)")
print("=" * 70)
m, duty, iW, iN, iX = build_model(num_emp=10, with_zrule=True, past_5days=None)
st, name, s = solve(m, time_limit=30.0)
print(f"A) Result: {name}  ({s.WallTime():.2f}s)")

print("\n" + "=" * 70)
print("STEP 3: 시나리오 B — blocked_N=5명 (가/나/다/라/마)")
print("=" * 70)
m, duty, iW, iN, iX = build_model(num_emp=10, with_zrule=True,
                                    past_5days=None, blocked_N={0,1,2,3,4})
st, name, s = solve(m, time_limit=30.0)
print(f"B) Result: {name}  ({s.WallTime():.2f}s)")
if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    per_nurse = analyze_solution(s, duty, 10, 31)
    Ws = [n['W'] for n in per_nurse]; Ns = [n['N'] for n in per_nurse]; Xs = [n['X'] for n in per_nurse]
    print(f"  Per-nurse: W min/max/avg = {min(Ws)}/{max(Ws)}/{sum(Ws)/10:.1f}")
    print(f"  Per-nurse: N min/max/avg = {min(Ns)}/{max(Ns)}/{sum(Ns)/10:.1f}")
    print(f"  Per-nurse: X min/max/avg = {min(Xs)}/{max(Xs)}/{sum(Xs)/10:.1f}")
    print(f"  blocked_N nurses' N: {[per_nurse[e]['N'] for e in range(5)]}")
    print(f"  z_rule violations: {sum(verify_zrule(n['sched']) for n in per_nurse)}")

print("\n" + "=" * 70)
print("STEP 4: 시나리오 C — B + special (가 +2 N불가, 바 +3 N가능)")
print("=" * 70)
# special: 가(0)에게 추가 X 2일 (0의 X 카운트 +2), 바(5)에게 추가 X 3일
# 모델링: 시스템 capacity에서 X를 빼지 않고, 직원별 min/max를 사용하긴 어렵다.
# 대신 명시적 special_X 변수로 추가
def build_with_special(num_emp=10, ndays=31, blocked_N=None,
                        extra_X={}, past_5days=None, start_day=4):
    """extra_X: {emp_idx: additional X days requested beyond average}"""
    m = cp_model.CpModel()
    duty = [[m.NewIntVar(0, 2, f'd_e{e}_d{d}') for d in range(ndays)] for e in range(num_emp)]
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
    for d, (_, _, cap) in enumerate(CAL):
        m.Add(sum(iW[e][d] for e in range(num_emp)) == cap[0])
        m.Add(sum(iN[e][d] for e in range(num_emp)) == cap[1])
        m.Add(sum(iX[e][d] for e in range(num_emp)) == cap[2])
    if blocked_N:
        for e in blocked_N:
            for d in range(ndays):
                m.Add(iN[e][d] == 0)
    # special: enforce per-nurse min X count
    base_X = 76 // 10  # 7
    for e, extra in extra_X.items():
        m.Add(sum(iX[e][d] for d in range(ndays)) >= base_X + extra)
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
            z = m.NewIntVar(0, 242, f'z_e{e}_d{d}')
            terms = [w*v for (k,v), w in zip(vals, weights)]
            m.Add(z == sum(terms))
            m.AddAllowedAssignments([z], [[k] for k in sorted(P_SET)])
    return m, duty, iW, iN, iX

m, duty, iW, iN, iX = build_with_special(blocked_N={0,1,2,3,4}, extra_X={0: 2, 5: 3})
st, name, s = solve(m, time_limit=30.0)
print(f"C) Result: {name}  ({s.WallTime():.2f}s)")
if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    per_nurse = analyze_solution(s, duty, 10, 31)
    print(f"  가(0) X count: {per_nurse[0]['X']} (special +2, base 7 → expected >=9)")
    print(f"  바(5) X count: {per_nurse[5]['X']} (special +3, base 7 → expected >=10)")
    print(f"  blocked_N N counts: {[per_nurse[e]['N'] for e in range(5)]}")
    Xs_non_special = [per_nurse[e]['X'] for e in range(10) if e not in (0, 5)]
    print(f"  non-special X range: {max(Xs_non_special) - min(Xs_non_special)} (target <=1)")
    print(f"  z_rule violations: {sum(verify_zrule(n['sched']) for n in per_nurse)}")
