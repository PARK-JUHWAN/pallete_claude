"""
최종 해결책 — wallet 알고리즘 재설계:

핵심 원칙:
1) wallet_target은 직원별 사용 가능 듀티 풀에 따라 ADAPT
   - blocked_N 직원: N target=0, W target += avg_N_share, X target는 유지
   - extra_X 직원: X target += bonus, W/N target에서 비례 차감
2) past_5days로 인한 day 0/1/2 강제 듀티를 사전 시뮬레이션 → 충돌하면 past 재배치 또는 capacity 보정
3) z_rule은 그대로 유지 (의뢰자 lock)
4) capacity는 그대로 유지

알고리즘:
  step 1: compute per-nurse targets (W, N, X) — adaptive
  step 2: sanitize per_emp_past for day 0..3 forced-duty conflicts
  step 3: solve with adaptive wallets + balance(X) within homogeneous group
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
NDAYS = 31
SUM_W = sum(c[0] for c in CAPS)  # 172
SUM_N = sum(c[1] for c in CAPS)  # 62
SUM_X = sum(c[2] for c in CAPS)  # 76

def compute_adaptive_wallets(num_emp, blocked_N=None, extra_X=None):
    """직원별 wallet target (W, N, X) 자동 산출."""
    blocked = blocked_N or set()
    extras = extra_X or {}

    # extra_X bonus 합계
    bonus_X = sum(extras.values())
    # 남은 X = SUM_X - bonus_X, non-special에게 분배
    non_special_count = num_emp  # all are part of "non-special" for X base
    # 더 정확히: extras 받은 직원도 base 7 + extra
    base_X = (SUM_X - bonus_X) / num_emp  # 76 - 5 = 71 / 10 = 7.1

    # N: blocked는 N=0, non-blocked가 SUM_N 모두 부담
    non_blocked = num_emp - len(blocked)
    if non_blocked == 0:
        base_N_for_nonblocked = 0
    else:
        base_N_for_nonblocked = SUM_N / non_blocked  # 62/5 = 12.4 (if 5 blocked)

    # W: total W = SUM_W - sum(other duties)
    # 각 직원: W + N + X = NDAYS = 31
    # blocked: W + X = 31. 평균 X 인지 모름.
    # non-blocked: W + N + X = 31, N = 12.4 (avg), X = 7.1 (avg) → W = 31 - 12.4 - 7.1 = 11.5
    # blocked: X 평균을 non-blocked와 같게 두려면 X = 7.1 → W = 31 - 7.1 = 23.9
    # 검산: sum W = 5×23.9 + 5×11.5 = 119.5 + 57.5 = 177 (≠ 172, gap because non-integer)
    # 정확히: SUM_W = sum_blocked_W + sum_nonblocked_W
    # sum_blocked_W = blocked × (31 - base_X)  (since N=0)
    # sum_nonblocked_W = SUM_W - sum_blocked_W
    # base_W_nonblocked = sum_nonblocked_W / non_blocked
    if blocked:
        sum_blocked_W = len(blocked) * (NDAYS - base_X)
        sum_nb_W = SUM_W - sum_blocked_W
        base_W_blocked = NDAYS - base_X  # = 23.9
        base_W_nonblocked = sum_nb_W / non_blocked if non_blocked else 0
    else:
        base_W_blocked = SUM_W / num_emp
        base_W_nonblocked = SUM_W / num_emp

    targets = {}
    for e in range(num_emp):
        is_blocked = e in blocked
        extra = extras.get(e, 0)
        if is_blocked:
            t_W = base_W_blocked
            t_N = 0
            t_X = base_X + extra
            t_W -= extra  # extra X means less W
        else:
            t_W = base_W_nonblocked
            t_N = base_N_for_nonblocked
            t_X = base_X + extra
            # extra X: reduce W or N proportionally
            t_W -= extra * (t_W / (t_W + t_N)) if (t_W + t_N) > 0 else 0
            t_N -= extra * (t_N / (t_W + t_N)) if (t_W + t_N) > 0 else 0
        targets[e] = {'W': round(t_W), 'N': round(t_N), 'X': round(t_X)}
    return targets

def check_first_days_feasible(per_emp_past, caps, lookahead=8, blocked_N=None):
    """첫 N일 호환성을 sub-CP-SAT으로 체크."""
    n = len(per_emp_past)
    blocked = blocked_N or set()
    m = cp_model.CpModel()
    duty = [[m.NewIntVar(0, 2, f't_{e}_{d}') for d in range(lookahead)] for e in range(n)]
    iW = [[m.NewBoolVar(f'tW_{e}_{d}') for d in range(lookahead)] for e in range(n)]
    iN = [[m.NewBoolVar(f'tN_{e}_{d}') for d in range(lookahead)] for e in range(n)]
    iX = [[m.NewBoolVar(f'tX_{e}_{d}') for d in range(lookahead)] for e in range(n)]
    for e in range(n):
        for d in range(lookahead):
            m.Add(duty[e][d] == 0).OnlyEnforceIf(iW[e][d])
            m.Add(duty[e][d] != 0).OnlyEnforceIf(iW[e][d].Not())
            m.Add(duty[e][d] == 1).OnlyEnforceIf(iN[e][d])
            m.Add(duty[e][d] != 1).OnlyEnforceIf(iN[e][d].Not())
            m.Add(duty[e][d] == 2).OnlyEnforceIf(iX[e][d])
            m.Add(duty[e][d] != 2).OnlyEnforceIf(iX[e][d].Not())
            m.AddExactlyOne([iW[e][d], iN[e][d], iX[e][d]])
    for d in range(lookahead):
        w, nn, x = caps[d]
        m.Add(sum(iW[e][d] for e in range(n)) == w)
        m.Add(sum(iN[e][d] for e in range(n)) == nn)
        m.Add(sum(iX[e][d] for e in range(n)) == x)
    for e in blocked:
        for d in range(lookahead):
            m.Add(iN[e][d] == 0)
    weights = [81,27,9,3,1]
    for e in range(n):
        past = per_emp_past[e]
        for d in range(lookahead):
            vals = []
            for off in (-4,-3,-2,-1,0):
                di = d + off
                if di < 0:
                    vals.append(past[5+di])
                else:
                    vals.append(duty[e][di])
            z = m.NewIntVar(0, 242, f'tz_{e}_{d}')
            terms = []
            for v, w in zip(vals, weights):
                terms.append(w*v)
            m.Add(z == sum(terms))
            m.AddAllowedAssignments([z], [[k] for k in sorted(P_SET)])
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = 5.0
    s.parameters.num_search_workers = 4
    st = s.Solve(m)
    return st in (cp_model.OPTIMAL, cp_model.FEASIBLE)

def sanitize_past(per_emp_past, caps, blocked_N=None):
    """첫 5일 호환성을 검증; 불가능하면 가장 rigid한 직원의 past를 [X,X,X,X,X]로 교체.
    반복하면서 호환될 때까지 진행."""
    if per_emp_past is None:
        return None, []
    sanitized = [list(p) for p in per_emp_past]
    dropped = []
    max_iter = len(per_emp_past)
    for it in range(max_iter):
        if check_first_days_feasible(sanitized, caps, lookahead=8, blocked_N=blocked_N):
            return sanitized, sorted(dropped)
        # 호환 안됨 → 가장 rigid한 직원 찾기 (P[v]가 1-choice인 직원 우선)
        candidates = []
        for e, past in enumerate(sanitized):
            if e in dropped: continue
            v = past[0]*81 + past[1]*27 + past[2]*9 + past[3]*3 + past[4]
            if v not in Z_RULES:
                rigidity = 0
            else:
                rigidity = 4 - len(Z_RULES[v])
            # blocked_N 직원이고 past가 N을 강제하면 우선순위 max
            if blocked_N and e in blocked_N:
                if v in Z_RULES and 'N' in Z_RULES[v] and len(Z_RULES[v]) == 1:
                    rigidity = 100
            candidates.append((rigidity, e))
        candidates.sort(reverse=True)
        if not candidates: break
        _, e = candidates[0]
        sanitized[e] = [2,2,2,2,2]
        dropped.append(e)
    return sanitized, sorted(dropped)

def solve_with_fix(num_emp=10, blocked_N=None, extra_X=None,
                   per_emp_past=None, balance_X_range_per_group=1,
                   time_limit=60.0, verbose=False):
    """
    Returns: (status_name, solver, duty_vars, iW, iN, iX, wallets, sanitized_past, dropped)
    """
    sanitized, dropped = sanitize_past(per_emp_past, CAPS, blocked_N=blocked_N)
    wallets = compute_adaptive_wallets(num_emp, blocked_N, extra_X)
    if verbose:
        print(f"  Adaptive wallets (target W/N/X):")
        for e in range(num_emp):
            w = wallets[e]
            print(f"    emp{e}: W={w['W']}, N={w['N']}, X={w['X']}")
        if dropped:
            print(f"  Sanitized past: dropped emps {dropped}")

    m = cp_model.CpModel()
    duty = [[m.NewIntVar(0, 2, f'd_{e}_{d}') for d in range(NDAYS)] for e in range(num_emp)]
    iW = [[m.NewBoolVar(f'W_{e}_{d}') for d in range(NDAYS)] for e in range(num_emp)]
    iN = [[m.NewBoolVar(f'N_{e}_{d}') for d in range(NDAYS)] for e in range(num_emp)]
    iX = [[m.NewBoolVar(f'X_{e}_{d}') for d in range(NDAYS)] for e in range(num_emp)]
    for e in range(num_emp):
        for d in range(NDAYS):
            m.Add(duty[e][d] == 0).OnlyEnforceIf(iW[e][d])
            m.Add(duty[e][d] != 0).OnlyEnforceIf(iW[e][d].Not())
            m.Add(duty[e][d] == 1).OnlyEnforceIf(iN[e][d])
            m.Add(duty[e][d] != 1).OnlyEnforceIf(iN[e][d].Not())
            m.Add(duty[e][d] == 2).OnlyEnforceIf(iX[e][d])
            m.Add(duty[e][d] != 2).OnlyEnforceIf(iX[e][d].Not())
            m.AddExactlyOne([iW[e][d], iN[e][d], iX[e][d]])

    # capacity
    for d in range(NDAYS):
        w, n, x = CAPS[d]
        m.Add(sum(iW[e][d] for e in range(num_emp)) == w)
        m.Add(sum(iN[e][d] for e in range(num_emp)) == n)
        m.Add(sum(iX[e][d] for e in range(num_emp)) == x)

    # blocked_N
    if blocked_N:
        for e in blocked_N:
            for d in range(NDAYS):
                m.Add(iN[e][d] == 0)

    # wallet >=2: target - actual >= 2 → fail. 따라서 actual >= target - 1
    for e in range(num_emp):
        w = wallets[e]
        m.Add(sum(iW[e][d] for d in range(NDAYS)) >= max(0, w['W'] - 1))
        m.Add(sum(iN[e][d] for d in range(NDAYS)) >= max(0, w['N'] - 1))
        m.Add(sum(iX[e][d] for d in range(NDAYS)) >= max(0, w['X'] - 1))

    # X balance: non-special 전체에서 max-min ≤ balance_X_range_per_group
    blocked = blocked_N or set()
    extras = set(extra_X.keys()) if extra_X else set()
    non_special = [e for e in range(num_emp) if e not in extras]
    if len(non_special) >= 2:
        X_cnts = [m.NewIntVar(0, NDAYS, f'Xc_{e}') for e in non_special]
        for i, e in enumerate(non_special):
            m.Add(X_cnts[i] == sum(iX[e][d] for d in range(NDAYS)))
        mx = m.NewIntVar(0, NDAYS, 'X_max_all')
        mn = m.NewIntVar(0, NDAYS, 'X_min_all')
        m.AddMaxEquality(mx, X_cnts)
        m.AddMinEquality(mn, X_cnts)
        m.Add(mx - mn <= balance_X_range_per_group)

    # z_rule (sanitized past)
    weights = [81, 27, 9, 3, 1]
    for e in range(num_emp):
        past = sanitized[e] if sanitized else None
        start = 0 if past is not None else 4
        for d in range(start, NDAYS):
            vals = []
            for off in (-4, -3, -2, -1, 0):
                di = d + off
                if di < 0:
                    if past is None: vals = None; break
                    vals.append(past[5+di])
                else:
                    vals.append(duty[e][di])
            if vals is None: continue
            z = m.NewIntVar(0, 242, f'z_{e}_{d}')
            m.Add(z == sum(w*v for w,v in zip(weights, vals)))
            m.AddAllowedAssignments([z], [[k] for k in sorted(P_SET)])

    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = time_limit
    s.parameters.num_search_workers = 8
    st = s.Solve(m)
    name = {cp_model.OPTIMAL: 'OPTIMAL', cp_model.FEASIBLE: 'FEASIBLE',
            cp_model.INFEASIBLE: 'INFEASIBLE', cp_model.UNKNOWN: 'UNKNOWN'}.get(st, str(st))
    return name, s, duty, iW, iN, iX, wallets, sanitized, dropped

def verify_full(s, duty, iW, iN, iX, num_emp, wallets, blocked_N=None,
                extra_X=None, per_emp_past=None):
    blocked = blocked_N or set()
    extras = extra_X or {}
    res = {}
    # capacity
    cap_ok = True
    for d in range(NDAYS):
        w, n, x = CAPS[d]
        W = sum(s.Value(iW[e][d]) for e in range(num_emp))
        N = sum(s.Value(iN[e][d]) for e in range(num_emp))
        X = sum(s.Value(iX[e][d]) for e in range(num_emp))
        if (W, N, X) != (w, n, x):
            cap_ok = False; break
    res['cap=='] = cap_ok
    # z_rule
    weights = [81,27,9,3,1]
    viols = 0
    for e in range(num_emp):
        past = per_emp_past[e] if per_emp_past else None
        for d in range(NDAYS):
            vals = []
            for off in (-4,-3,-2,-1,0):
                di = d + off
                if di < 0:
                    if past is None: vals = None; break
                    vals.append(past[5+di])
                else:
                    vals.append(s.Value(duty[e][di]))
            if vals is None: continue
            v = sum(w*x for w,x in zip(weights, vals))
            if v not in P_SET: viols += 1
    res['z_viols'] = viols
    # wallet
    wallet_ok = True
    fails = []
    counts = []
    for e in range(num_emp):
        Wc = sum(s.Value(iW[e][d]) for d in range(NDAYS))
        Nc = sum(s.Value(iN[e][d]) for d in range(NDAYS))
        Xc = sum(s.Value(iX[e][d]) for d in range(NDAYS))
        counts.append((Wc, Nc, Xc))
        w = wallets[e]
        if (w['W'] - Wc >= 2) or (w['N'] - Nc >= 2) or (w['X'] - Xc >= 2):
            wallet_ok = False
            fails.append(f"emp{e}: actual W={Wc}/t{w['W']} (gap {w['W']-Wc}), N={Nc}/t{w['N']} (gap {w['N']-Nc}), X={Xc}/t{w['X']} (gap {w['X']-Xc})")
    res['wallet_ok'] = wallet_ok
    res['wallet_fails'] = fails
    res['counts'] = counts
    # X non-special range — non-special = not in extras
    non_sp = [e for e in range(num_emp) if e not in extras]
    Xs = [counts[e][2] for e in non_sp]
    res['X_nonsp_range'] = max(Xs) - min(Xs) if Xs else 0
    res['X_nonsp_counts'] = Xs
    # blocked_N
    if blocked:
        bn_ok = all(counts[e][1] == 0 for e in blocked)
        res['blocked_N=0'] = bn_ok
    return res

# ============================================================
# 시나리오 실행
# ============================================================
print("\n" + "▓"*72)
print("FIX 적용 — 시나리오 A/B/C, past=None")
print("▓"*72)

def run(name, blocked_N=None, extra_X=None, per_emp_past=None,
        balance_X_range_per_group=1):
    print(f"\n=== {name} ===")
    res_name, s, duty, iW, iN, iX, wallets, sanitized, dropped = solve_with_fix(
        num_emp=10, blocked_N=blocked_N, extra_X=extra_X,
        per_emp_past=per_emp_past, balance_X_range_per_group=balance_X_range_per_group,
        time_limit=60.0, verbose=True)
    print(f"  Solver: {res_name} ({s.WallTime():.2f}s)")
    if res_name not in ('OPTIMAL', 'FEASIBLE'):
        return False, None
    r = verify_full(s, duty, iW, iN, iX, 10, wallets,
                    blocked_N=blocked_N, extra_X=extra_X,
                    per_emp_past=sanitized)
    print(f"  [{'✓' if r['cap==']             else '✗'}] capacity == :        {r['cap==']}")
    print(f"  [{'✓' if r['z_viols']==0          else '✗'}] z_rule violations:   {r['z_viols']}")
    print(f"  [{'✓' if r['wallet_ok']           else '✗'}] wallet >=2:          {r['wallet_ok']}")
    for f in r['wallet_fails']:
        print(f"        FAIL: {f}")
    rng = r['X_nonsp_range']
    print(f"  [{'✓' if rng <= 1                 else '✗'}] X non-sp range:      {rng}   counts={r['X_nonsp_counts']}")
    if 'blocked_N=0' in r:
        print(f"  [{'✓' if r['blocked_N=0']     else '✗'}] blocked_N N=0:       {r['blocked_N=0']}")
    all_ok = (res_name in ('OPTIMAL','FEASIBLE') and r['cap=='] and r['z_viols']==0
              and r['wallet_ok'] and r['X_nonsp_range'] <= 1
              and r.get('blocked_N=0', True))
    return all_ok, r

a_ok, _ = run("Scenario A: 단순 (past=None)",
              blocked_N=None, extra_X=None, per_emp_past=None)
b_ok, _ = run("Scenario B: blocked_N=5명 (past=None)",
              blocked_N={0,1,2,3,4}, extra_X=None, per_emp_past=None)
c_ok, _ = run("Scenario C: blocked_N=5 + special",
              blocked_N={0,1,2,3,4}, extra_X={0:2, 5:3}, per_emp_past=None)

print("\n" + "▓"*72)
print("FIX 적용 — 시나리오 A/B/C, per_emp_past = random (real-world)")
print("▓"*72)
import random
random.seed(42)
random_past = []
for e in range(10):
    v = random.choice(list(P_SET))
    random_past.append([(v//81)%3, (v//27)%3, (v//9)%3, (v//3)%3, v%3])

a2_ok, _ = run("Scenario A': 단순 (random past)",
               blocked_N=None, extra_X=None, per_emp_past=random_past)
b2_ok, _ = run("Scenario B': blocked_N=5 (random past)",
               blocked_N={0,1,2,3,4}, extra_X=None, per_emp_past=random_past)
c2_ok, _ = run("Scenario C': blocked_N=5 + special (random past)",
               blocked_N={0,1,2,3,4}, extra_X={0:2, 5:3}, per_emp_past=random_past)

print("\n" + "▓"*72)
print("최종 결과")
print("▓"*72)
print(f"past=None      — A: {'PASS' if a_ok else 'FAIL'} | B: {'PASS' if b_ok else 'FAIL'} | C: {'PASS' if c_ok else 'FAIL'}")
print(f"random past    — A': {'PASS' if a2_ok else 'FAIL'} | B': {'PASS' if b2_ok else 'FAIL'} | C': {'PASS' if c2_ok else 'FAIL'}")
