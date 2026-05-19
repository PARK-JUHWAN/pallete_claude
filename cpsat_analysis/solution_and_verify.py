"""
해결책 구현 + 시나리오 A/B/C 검증

핵심 해결책:
  Fix 1: past_5days를 즉시 강제하지 않고 "soft 시작 윈도우" 처리
         → day 0에서 z_rule이 충돌하면 그 직원의 past를 안전한 패턴(예: 모두 X)으로 대체
  Fix 2: 직원당 capacity 차이를 wallet으로 흡수 (wallet.md 알고리즘 변경)
  Fix 3: high day X capacity를 2 → 3으로 늘릴 수 없는 경우, week 단위로 휴일 조정

이 파일에서는 Fix 1을 구현하고 시나리오 A/B/C 검증:
  (A) 단순: 10명, 제약 최소
  (B) blocked_N=5명
  (C) (B) + special: emp0 +2 (N불가, X bonus), emp5 +3 (N가능, X bonus)
검증 항목:
  1. 솔버 FEASIBLE/OPTIMAL
  2. capacity ==
  3. z_rule 위반 0
  4. wallet >=2 (target - actual >= 2 → fail)
  5. X (non-special) max-min ≤ 1
  6. blocked_N 직원의 N = 0
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

# === Fix 1: past_5days 호환성 사전 체크 ===
def is_past_compatible_with_capacity(per_emp_past, caps, max_days=4):
    """
    각 직원의 past로부터 day 0..max_days-1까지의 z_rule 강제 듀티가
    capacity와 충돌하지 않는지 확인.
    충돌 시 (day_idx, duty, count, cap) 반환.
    """
    forced = []  # list of (emp_idx, day_idx, forced_duty)
    # day 0: each emp's past determines next
    for e, past in enumerate(per_emp_past):
        if past is None: continue
        # simulate forward up to max_days
        seq = list(past) + [None] * max_days
        for d in range(max_days):
            # compute z_val at position 5 + d - 4 .. 5 + d (i.e., past[d+1..4] + ... ?)
            # window for "next day" prediction at position 5+d-1: past[d..4] (if d<5) and seq[5..5+d-1]
            window = seq[d:d+5]  # 5 elements
            if any(x is None for x in window): break
            v = window[0]*81 + window[1]*27 + window[2]*9 + window[3]*3 + window[4]
            if v not in Z_RULES: break  # past itself is invalid
            allowed = Z_RULES[v]
            if len(allowed) == 1:
                d_next = DUTY[allowed[0]]
                seq[5+d] = d_next
                forced.append((e, d, d_next))
            else:
                break  # free, stop simulating
    # check conflicts per day
    by_day = {}
    for e, d, dn in forced:
        by_day.setdefault(d, []).append((e, dn))
    conflicts = []
    for d, lst in by_day.items():
        c = Counter([dn for _, dn in lst])
        cap = caps[d]
        if c.get(0, 0) > cap[0]: conflicts.append((d, 'W', c[0], cap[0], [e for e, dn in lst if dn==0]))
        if c.get(1, 0) > cap[1]: conflicts.append((d, 'N', c[1], cap[1], [e for e, dn in lst if dn==1]))
        if c.get(2, 0) > cap[2]: conflicts.append((d, 'X', c[2], cap[2], [e for e, dn in lst if dn==2]))
    return conflicts, forced

def sanitize_past(per_emp_past, caps):
    """충돌하는 직원의 past를 안전한 패턴 [X,X,X,X,X] (v=242, free next)로 치환."""
    conflicts, forced = is_past_compatible_with_capacity(per_emp_past, caps)
    if not conflicts:
        return per_emp_past, []
    # 가장 적게 흔드는 방식: 충돌이 가장 큰 day의 over-quota만큼 직원 선택해 past 무효화
    to_drop = set()
    for d, duty_name, cnt, cap, emp_list in conflicts:
        excess = cnt - cap
        # drop `excess` employees from this forced group
        # pick those whose past is most "rigid" (next has 1 choice = forced)
        # 일단 순서대로
        for e in emp_list[:excess]:
            to_drop.add(e)
    sanitized = list(per_emp_past)
    for e in to_drop:
        sanitized[e] = [2,2,2,2,2]  # v=242, free
    # 재귀 체크
    conflicts2, _ = is_past_compatible_with_capacity(sanitized, caps)
    if conflicts2:
        # 더 많이 drop
        for d, dn, cnt, cap, emp_list in conflicts2:
            excess = cnt - cap
            for e in emp_list[:excess]:
                sanitized[e] = [2,2,2,2,2]
    return sanitized, sorted(to_drop)

# === 모델 빌더 ===
def build_solver_model(num_emp=10, ndays=31, per_emp_past=None,
                       blocked_N=None, extra_X=None,
                       wallet_target_W=None, wallet_target_N=None, wallet_target_X=None,
                       balance_X_range=None):
    """
    wallet_target_*: 직원당 목표 카운트, lower bound = target - 2
    balance_X_range: max(X) - min(X) ≤ value (non-special만)
    """
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
    if blocked_N:
        for e in blocked_N:
            for d in range(ndays):
                m.Add(iN[e][d] == 0)
    # wallet lower bound (>=2 rule equivalent)
    if wallet_target_W is not None:
        for e in range(num_emp):
            target = wallet_target_W[e] if isinstance(wallet_target_W, dict) else wallet_target_W
            m.Add(sum(iW[e][d] for d in range(ndays)) >= max(0, target - 2))
    if wallet_target_N is not None:
        for e in range(num_emp):
            target = wallet_target_N[e] if isinstance(wallet_target_N, dict) else wallet_target_N
            if e in (blocked_N or set()): continue
            m.Add(sum(iN[e][d] for d in range(ndays)) >= max(0, target - 2))
    if wallet_target_X is not None:
        for e in range(num_emp):
            target = wallet_target_X[e] if isinstance(wallet_target_X, dict) else wallet_target_X
            m.Add(sum(iX[e][d] for d in range(ndays)) >= max(0, target - 2))
    if extra_X:
        for e, extra in extra_X.items():
            base = wallet_target_X[e] if isinstance(wallet_target_X, dict) else (wallet_target_X or 7)
            m.Add(sum(iX[e][d] for d in range(ndays)) >= base + extra - 2)  # special's wallet 가용
    # balance X range (non-special만)
    if balance_X_range is not None:
        special_emps = set(extra_X.keys()) if extra_X else set()
        non_special = [e for e in range(num_emp) if e not in special_emps]
        if non_special:
            X_counts = [m.NewIntVar(0, ndays, f'Xcnt_{e}') for e in non_special]
            for i, e in enumerate(non_special):
                m.Add(X_counts[i] == sum(iX[e][d] for d in range(ndays)))
            mx = m.NewIntVar(0, ndays, 'X_max')
            mn = m.NewIntVar(0, ndays, 'X_min')
            m.AddMaxEquality(mx, X_counts)
            m.AddMinEquality(mn, X_counts)
            m.Add(mx - mn <= balance_X_range)
    # z_rule with per_emp_past
    weights = [81, 27, 9, 3, 1]
    for e in range(num_emp):
        past = per_emp_past[e] if per_emp_past else None
        start = 0 if past is not None else 4
        for d in range(start, ndays):
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
    return m, duty, iW, iN, iX

def verify_solution(s, duty, iW, iN, iX, num_emp, ndays,
                    blocked_N=None, extra_X=None,
                    wallet_target_W=17, wallet_target_N=6, wallet_target_X=7,
                    per_emp_past=None):
    """검증 5개 항목 통과 여부."""
    results = {}
    # 1. solver status (caller checks)
    # 2. capacity
    cap_ok = True
    for d in range(ndays):
        w, n, x = CAPS[d]
        W = sum(s.Value(iW[e][d]) for e in range(num_emp))
        N = sum(s.Value(iN[e][d]) for e in range(num_emp))
        X = sum(s.Value(iX[e][d]) for e in range(num_emp))
        if (W, N, X) != (w, n, x):
            cap_ok = False
            break
    results['capacity=='] = cap_ok
    # 3. z_rule violations
    weights = [81, 27, 9, 3, 1]
    viols = 0
    for e in range(num_emp):
        past = per_emp_past[e] if per_emp_past else None
        for d in range(ndays):
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
            if v not in P_SET:
                viols += 1
    results['z_rule_violations'] = viols
    # 4. wallet >=2
    wallet_ok = True
    wallet_detail = []
    for e in range(num_emp):
        W_cnt = sum(s.Value(iW[e][d]) for d in range(ndays))
        N_cnt = sum(s.Value(iN[e][d]) for d in range(ndays))
        X_cnt = sum(s.Value(iX[e][d]) for d in range(ndays))
        tw = wallet_target_W if not isinstance(wallet_target_W, dict) else wallet_target_W[e]
        tn = wallet_target_N if not isinstance(wallet_target_N, dict) else wallet_target_N[e]
        tx = wallet_target_X if not isinstance(wallet_target_X, dict) else wallet_target_X[e]
        if e in (blocked_N or set()): tn = 0
        if extra_X and e in extra_X: tx = (wallet_target_X if not isinstance(wallet_target_X, dict) else wallet_target_X[e]) + extra_X[e]
        if tw - W_cnt >= 2 or tn - N_cnt >= 2 or tx - X_cnt >= 2:
            wallet_ok = False
            wallet_detail.append(f"emp{e}: W={W_cnt}/t{tw}, N={N_cnt}/t{tn}, X={X_cnt}/t{tx}")
    results['wallet>=2'] = wallet_ok
    results['wallet_detail'] = wallet_detail
    # 5. X (non-special) max-min ≤ 1
    special = set(extra_X.keys()) if extra_X else set()
    non_sp = [e for e in range(num_emp) if e not in special]
    if non_sp:
        Xs = [sum(s.Value(iX[e][d]) for d in range(ndays)) for e in non_sp]
        results['X_nonspecial_range'] = max(Xs) - min(Xs)
        results['X_nonspecial_counts'] = Xs
    # 6. blocked_N
    if blocked_N:
        bn_ok = True
        for e in blocked_N:
            N_cnt = sum(s.Value(iN[e][d]) for d in range(ndays))
            if N_cnt > 0: bn_ok = False
        results['blocked_N=0'] = bn_ok
    return results

def run_scenario(name, num_emp=10, blocked_N=None, extra_X=None, per_emp_past=None,
                 wallet_target_W=17, wallet_target_N=6, wallet_target_X=7,
                 balance_X_range=1):
    print(f"\n{'='*70}\n{name}\n{'='*70}")
    # Fix 1: sanitize past
    sanitized_past = None
    dropped = []
    if per_emp_past:
        sanitized_past, dropped = sanitize_past(per_emp_past, CAPS)
        if dropped:
            print(f"  Sanitized: dropped past for emps {dropped} (X/N forcing → replaced by [X,X,X,X,X])")

    # blocked_N의 wallet target N은 0
    wN_dict = {e: 0 for e in (blocked_N or set())}
    for e in range(num_emp):
        if e not in (blocked_N or set()):
            wN_dict[e] = wallet_target_N

    m, duty, iW, iN, iX = build_solver_model(
        num_emp=num_emp, per_emp_past=sanitized_past,
        blocked_N=blocked_N, extra_X=extra_X,
        wallet_target_W=wallet_target_W,
        wallet_target_N=wN_dict, wallet_target_X=wallet_target_X,
        balance_X_range=balance_X_range,
    )
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = 60.0
    s.parameters.num_search_workers = 8
    st = s.Solve(m)
    name_st = {cp_model.OPTIMAL: 'OPTIMAL', cp_model.FEASIBLE: 'FEASIBLE',
               cp_model.INFEASIBLE: 'INFEASIBLE', cp_model.UNKNOWN: 'UNKNOWN'}.get(st, str(st))
    print(f"  Solver: {name_st} ({s.WallTime():.2f}s)")
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return False
    r = verify_solution(s, duty, iW, iN, iX, num_emp, 31,
                        blocked_N=blocked_N, extra_X=extra_X,
                        wallet_target_W=wallet_target_W,
                        wallet_target_N=wN_dict, wallet_target_X=wallet_target_X,
                        per_emp_past=sanitized_past)
    print(f"  [✓] capacity == :       {r['capacity==']}")
    print(f"  [✓] z_rule violations:  {r['z_rule_violations']}")
    print(f"  [✓] wallet >=2:         {r['wallet>=2']}")
    if not r['wallet>=2']:
        for d in r['wallet_detail'][:3]:
            print(f"        FAIL {d}")
    print(f"  [✓] X non-sp range:     {r.get('X_nonspecial_range', 'N/A')}  (counts={r.get('X_nonspecial_counts')})")
    if 'blocked_N=0' in r:
        print(f"  [✓] blocked_N N=0:      {r['blocked_N=0']}")
    all_ok = (st in (cp_model.OPTIMAL, cp_model.FEASIBLE)
              and r['capacity==']
              and r['z_rule_violations'] == 0
              and r['wallet>=2']
              and r.get('X_nonspecial_range', 0) <= 1
              and r.get('blocked_N=0', True))
    return all_ok

# === 시나리오 실행 ===
print("\n" + "▓"*70)
print("VERIFICATION: 시나리오 A, B, C")
print("▓"*70)

# Test with past=None (사용자 명세대로 "1일부터 자유")
print("\n--- past=None (사용자 stated setup) ---")
a_ok = run_scenario("Scenario A (단순): past=None, no special",
                    blocked_N=None, extra_X=None, per_emp_past=None,
                    balance_X_range=1)
b_ok = run_scenario("Scenario B (blocked_N=5명): past=None",
                    blocked_N={0,1,2,3,4}, extra_X=None, per_emp_past=None,
                    balance_X_range=1)
c_ok = run_scenario("Scenario C (B + special)",
                    blocked_N={0,1,2,3,4}, extra_X={0: 2, 5: 3}, per_emp_past=None,
                    balance_X_range=1)

# Test with random per-nurse past (real-world scenario)
print("\n--- per_emp_past = random P-set (real-world) ---")
import random
random.seed(42)
random_past = []
for e in range(10):
    v = random.choice(list(P_SET))
    random_past.append([(v//81)%3, (v//27)%3, (v//9)%3, (v//3)%3, v%3])
print(f"per_emp_past samples (W/N/X):")
for e in range(10):
    print(f"  emp{e}: {[INV[x] for x in random_past[e]]}")
a2_ok = run_scenario("Scenario A' (random past, 단순)",
                     blocked_N=None, extra_X=None, per_emp_past=random_past,
                     balance_X_range=1)
b2_ok = run_scenario("Scenario B' (random past, blocked_N=5)",
                     blocked_N={0,1,2,3,4}, extra_X=None, per_emp_past=random_past,
                     balance_X_range=1)
c2_ok = run_scenario("Scenario C' (random past, B + special)",
                     blocked_N={0,1,2,3,4}, extra_X={0: 2, 5: 3}, per_emp_past=random_past,
                     balance_X_range=1)

print("\n" + "▓"*70)
print("FINAL VERIFICATION SUMMARY")
print("▓"*70)
print(f"past=None — A: {a_ok}, B: {b_ok}, C: {c_ok}")
print(f"random past — A': {a2_ok}, B': {b2_ok}, C': {c2_ok}")
