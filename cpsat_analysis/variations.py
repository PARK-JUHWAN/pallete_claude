"""
INFEASIBLE 트리거 조건 탐색:
- z_rule 인코딩 방식 (window ∈ P vs. transition P[v] vs. forbidden EP+IP)
- past_5days 처리 (None / all-X / all-W / all-N / 임의)
- 시작 윈도우 적용 범위 (day 5부터 / day 1부터)
"""
from ortools.sat.python import cp_model
from datetime import date, timedelta
import itertools

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

# Build EP and IP (Forbidden = EP ∪ IP = all 243 \ P)
ALL_Z = set(range(243))
FORBIDDEN = ALL_Z - P_SET
print(f"P={len(P_SET)}, Forbidden(EP+IP)={len(FORBIDDEN)}")

# === Calendar ===
def build_calendar():
    cal = []
    start = date(2026, 5, 1)
    holidays = {date(2026, 5, 5), date(2026, 5, 24), date(2026, 5, 25)}
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

def build_model(num_emp=10, ndays=31,
                with_capacity=True, with_zrule=True,
                past_5days=None,
                zrule_mode='window_in_P',
                start_day_for_zrule=4):
    """
    zrule_mode:
      'window_in_P'           — z_val ∈ P (AddAllowedAssignments)
      'window_not_forbidden'  — z_val ∉ FORBIDDEN (AddForbiddenAssignments with EP+IP)
      'transition'            — for each window v, next duty ∈ P[v] (boolean channeling)
      'both'                  — window∈P + transition (redundant)
    start_day_for_zrule:
      4 = day index 4 (5번째 day) — full window from day 0..4 (no past needed)
      0 = day index 0 — past_5days required for day 0..3
    """
    m = cp_model.CpModel()
    duty = [[m.NewIntVar(0, 2, f'd_e{e}_d{d}') for d in range(ndays)] for e in range(num_emp)]

    # Channeling to bool
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

    if with_capacity:
        for d, (_, _, cap) in enumerate(CAL):
            w_cap, n_cap, x_cap = cap
            m.Add(sum(iW[e][d] for e in range(num_emp)) == w_cap)
            m.Add(sum(iN[e][d] for e in range(num_emp)) == n_cap)
            m.Add(sum(iX[e][d] for e in range(num_emp)) == x_cap)

    if with_zrule:
        weights = [81, 27, 9, 3, 1]
        for e in range(num_emp):
            for d in range(start_day_for_zrule, ndays):
                vals = []
                for off in (-4, -3, -2, -1, 0):
                    di = d + off
                    if di < 0:
                        if past_5days is None:
                            vals = None
                            break
                        vals.append(('c', past_5days[5 + di]))
                    else:
                        vals.append(('v', duty[e][di]))
                if vals is None:
                    continue
                z = m.NewIntVar(0, 242, f'z_e{e}_d{d}')
                terms = []
                for (k, v), w in zip(vals, weights):
                    terms.append(w * v)
                m.Add(z == sum(terms))
                if zrule_mode == 'window_in_P':
                    m.AddAllowedAssignments([z], [[k] for k in sorted(P_SET)])
                elif zrule_mode == 'window_not_forbidden':
                    m.AddForbiddenAssignments([z], [[k] for k in sorted(FORBIDDEN)])
                elif zrule_mode == 'both':
                    m.AddAllowedAssignments([z], [[k] for k in sorted(P_SET)])

    return m, duty, iW, iN, iX

def solve(model, time_limit=30.0, workers=8):
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = time_limit
    s.parameters.num_search_workers = workers
    st = s.Solve(model)
    name = {cp_model.OPTIMAL: 'OPTIMAL', cp_model.FEASIBLE: 'FEASIBLE',
            cp_model.INFEASIBLE: 'INFEASIBLE', cp_model.UNKNOWN: 'UNKNOWN'}.get(st, str(st))
    return name, s.WallTime()

# === Run variation matrix ===
def run_variations():
    scenarios = [
        ('past=None,         mode=window_in_P,         start=day5', None, 'window_in_P', 4),
        ('past=None,         mode=window_not_forbidden, start=day5', None, 'window_not_forbidden', 4),
        ('past=None,         mode=transition,           start=day5', None, 'transition', 4),
        ('past=[X,X,X,X,X],  mode=window_in_P,         start=day0', [2,2,2,2,2], 'window_in_P', 0),
        ('past=[W,W,W,W,W],  mode=window_in_P,         start=day0', [0,0,0,0,0], 'window_in_P', 0),
        ('past=[X,X,X,W,W],  mode=window_in_P,         start=day0', [2,2,2,0,0], 'window_in_P', 0),
        ('past=[W,W,W,W,X],  mode=window_in_P,         start=day0', [0,0,0,0,2], 'window_in_P', 0),
        ('past=[N,N,N,N,N],  mode=window_in_P,         start=day0', [1,1,1,1,1], 'window_in_P', 0),
        ('past=[X,X,X,X,W],  mode=window_in_P,         start=day0', [2,2,2,2,0], 'window_in_P', 0),
    ]
    for desc, past, mode, sd in scenarios:
        # Skip transition mode for simplicity (not implemented full)
        if mode == 'transition':
            print(f"  {desc:60s}  → SKIP (not implemented)")
            continue
        m, *_ = build_model(num_emp=10, ndays=31, with_capacity=True,
                            with_zrule=True, past_5days=past,
                            zrule_mode=mode, start_day_for_zrule=sd)
        name, t = solve(m, time_limit=20.0)
        print(f"  {desc:60s}  → {name}  ({t:.2f}s)")

if __name__ == '__main__':
    print("=== Variation Matrix ===")
    run_variations()
