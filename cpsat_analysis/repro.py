"""
FOUROFF N차 의뢰자판 INFEASIBLE 최소 재현
- 10명, 31일 (2026-05)
- duty: W=0, N=1, X=2
- capacity: M/T/W/Su = (W=5, N=2, X=3), Th/F/Sa/Holiday = (W=6, N=2, X=2)
- z_rule: 5일 윈도우, P set 52개만 허용
"""
from ortools.sat.python import cp_model
from datetime import date, timedelta

# === z_rule ===
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
INV_DUTY = {0: 'W', 1: 'N', 2: 'X'}

P_SET = set(Z_RULES.keys())

# P set의 모든 5일 윈도우 → 그 윈도우에서 다음 듀티가 가능한 d (P[v]) → 즉 새 5일 윈도우 (d2..d6)
# 윈도우 자체가 P set에 있어야 함. P 외 v는 EP/IP로 발생 금지.

def decode(v):
    """v → (d1,d2,d3,d4,d5)"""
    return ((v//81)%3, (v//27)%3, (v//9)%3, (v//3)%3, v%3)

def encode(d1,d2,d3,d4,d5):
    return d1*81 + d2*27 + d3*9 + d4*3 + d5

# 5일 윈도우 → P set 인지 boolean
ALLOWED_WINDOWS = set(P_SET)

# === 캘린더 (May 2026) ===
def build_calendar():
    """31일 각 일자의 (W, N, X) capacity 반환."""
    # 2026-05-01 = Friday
    # Mon=0, Sun=6
    cal = []
    start = date(2026, 5, 1)
    holidays = {date(2026, 5, 5),   # 어린이날 (화)
                date(2026, 5, 24),  # 부처님오신날 (일)
                date(2026, 5, 25)}  # 대체휴일 (월)
    high_day_count = 0
    low_day_count = 0
    for i in range(31):
        d = start + timedelta(days=i)
        wd = d.weekday()  # Mon=0..Sun=6
        is_holiday = d in holidays
        # Thu(3)/Fri(4)/Sat(5)/Holiday = high
        if is_holiday or wd in (3, 4, 5):
            cap = (6, 2, 2)
            high_day_count += 1
        else:
            cap = (5, 2, 3)
            low_day_count += 1
        cal.append((d, wd, is_holiday, cap))
    return cal, high_day_count, low_day_count

CAL, HIGH, LOW = build_calendar()
print(f"Calendar: HIGH(W=6) days = {HIGH}, LOW(W=5) days = {LOW}")
sumW = sum(c[3][0] for c in CAL)
sumN = sum(c[3][1] for c in CAL)
sumX = sum(c[3][2] for c in CAL)
print(f"System totals: W={sumW}, N={sumN}, X={sumX} (sum={sumW+sumN+sumX})")
print(f"Expected vs assumption: W=172, N=62, X=76 (sum=310)")

# === CP-SAT model ===
def build_model(num_emp=10, ndays=31, with_capacity=True, with_zrule=True, past_5days=None):
    """
    past_5days: list of 5 ints (duty values W=0/N=1/X=2) for the 5 days BEFORE day 1.
                If None, no past — first windows start at day 5.
    """
    model = cp_model.CpModel()
    # duty[e][d] in {0=W, 1=N, 2=X}
    duty = [[model.NewIntVar(0, 2, f'duty_e{e}_d{d}') for d in range(ndays)] for e in range(num_emp)]
    is_W = [[model.NewBoolVar(f'iW_e{e}_d{d}') for d in range(ndays)] for e in range(num_emp)]
    is_N = [[model.NewBoolVar(f'iN_e{e}_d{d}') for d in range(ndays)] for e in range(num_emp)]
    is_X = [[model.NewBoolVar(f'iX_e{e}_d{d}') for d in range(ndays)] for e in range(num_emp)]
    for e in range(num_emp):
        for d in range(ndays):
            model.Add(duty[e][d] == 0).OnlyEnforceIf(is_W[e][d])
            model.Add(duty[e][d] != 0).OnlyEnforceIf(is_W[e][d].Not())
            model.Add(duty[e][d] == 1).OnlyEnforceIf(is_N[e][d])
            model.Add(duty[e][d] != 1).OnlyEnforceIf(is_N[e][d].Not())
            model.Add(duty[e][d] == 2).OnlyEnforceIf(is_X[e][d])
            model.Add(duty[e][d] != 2).OnlyEnforceIf(is_X[e][d].Not())
            model.AddExactlyOne([is_W[e][d], is_N[e][d], is_X[e][d]])

    # capacity (==)
    if with_capacity:
        for d, (_, _, _, cap) in enumerate(CAL):
            w_cap, n_cap, x_cap = cap
            model.Add(sum(is_W[e][d] for e in range(num_emp)) == w_cap)
            model.Add(sum(is_N[e][d] for e in range(num_emp)) == n_cap)
            model.Add(sum(is_X[e][d] for e in range(num_emp)) == x_cap)

    # z_rule: 5일 슬라이딩 윈도우의 z_val ∈ P_SET
    if with_zrule:
        # 윈도우 정의: 시작일이 day 0이면 past_5days 사용; day 1~4도 past 활용
        for e in range(num_emp):
            for d in range(ndays):
                # 윈도우의 5일: (d-4, d-3, d-2, d-1, d)
                vals = []
                for off in (-4, -3, -2, -1, 0):
                    day_idx = d + off
                    if day_idx < 0:
                        if past_5days is None:
                            vals = None
                            break
                        # past_5days[i] is i-th past day; for day_idx = -1 → past_5days[-1] (last)
                        # past_5days has 5 entries, day_idx = -5 → past_5days[0], -1 → past_5days[4]
                        vals.append(('const', past_5days[5 + day_idx]))
                    else:
                        vals.append(('var', duty[e][day_idx]))
                if vals is None:
                    continue
                # build z_val variable
                z_expr = []
                weights = [81, 27, 9, 3, 1]
                # If all const, skip — but they should be const window check
                z_val = model.NewIntVar(0, 242, f'zval_e{e}_d{d}')
                # construct sum
                terms = []
                for (kind, v), w in zip(vals, weights):
                    if kind == 'const':
                        terms.append(w * v)
                    else:
                        # v is IntVar 0..2
                        terms.append(w * v)
                model.Add(z_val == sum(terms))
                model.AddAllowedAssignments([z_val], [[k] for k in sorted(P_SET)])

    return model, duty, is_W, is_N, is_X

def solve(model, time_limit=60.0, workers=8, verbose=True):
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = time_limit
    s.parameters.num_search_workers = workers
    if verbose:
        s.parameters.log_search_progress = False
    st = s.Solve(model)
    status = {cp_model.OPTIMAL: 'OPTIMAL', cp_model.FEASIBLE: 'FEASIBLE',
              cp_model.INFEASIBLE: 'INFEASIBLE', cp_model.MODEL_INVALID: 'MODEL_INVALID',
              cp_model.UNKNOWN: 'UNKNOWN'}.get(st, str(st))
    return st, status, s

if __name__ == '__main__':
    print("\n=== Repro: capacity + z_rule, 10명, no past ===")
    m, *_ = build_model(num_emp=10, ndays=31, with_capacity=True, with_zrule=True, past_5days=None)
    st, name, s = solve(m, time_limit=60.0, workers=8)
    print(f"Result: {name}  (time: {s.WallTime():.2f}s)")

    print("\n=== Sanity: capacity only ===")
    m, *_ = build_model(num_emp=10, ndays=31, with_capacity=True, with_zrule=False)
    st, name, s = solve(m, time_limit=15.0, workers=8)
    print(f"Result: {name}  (time: {s.WallTime():.2f}s)")

    print("\n=== Sanity: z_rule only, 1명 ===")
    m, *_ = build_model(num_emp=1, ndays=31, with_capacity=False, with_zrule=True)
    st, name, s = solve(m, time_limit=15.0, workers=8)
    print(f"Result: {name}  (time: {s.WallTime():.2f}s)")
