"""
근본 원인 정밀 증명:
1) 각 P-set window가 day 0를 어떤 듀티로 강제하는지 매핑
2) 운영 환경에서 past_5days가 어떻게 수집되는지 시뮬레이션
3) day 0/1/2에서 capacity 위반 가능성 정량화
"""
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
P_SET = set(Z_RULES.keys())
DUTY_NAMES = ['W', 'N', 'X']

def decode(v): return ((v//81)%3, (v//27)%3, (v//9)%3, (v//3)%3, v%3)
def encode(*d): return d[0]*81+d[1]*27+d[2]*9+d[3]*3+d[4]

# 분류: P set 윈도우 v에서 next duty가 1개로 강제되는 것 vs 2개 vs 3개
forced_W = []  # next 강제 = W
forced_N = []
forced_X = []
two_choice = []  # 2가지
free = []  # 3가지

for v, nxt in Z_RULES.items():
    if len(nxt) == 1:
        d = nxt[0]
        if d == 'W': forced_W.append(v)
        elif d == 'N': forced_N.append(v)
        elif d == 'X': forced_X.append(v)
    elif len(nxt) == 2:
        two_choice.append((v, nxt))
    else:
        free.append(v)

print(f"P set = {len(P_SET)} patterns")
print(f"  → forced next = W: {len(forced_W)} patterns")
print(f"  → forced next = N: {len(forced_N)} patterns")
print(f"  → forced next = X: {len(forced_X)} patterns")
print(f"  → 2-choice: {len(two_choice)} patterns")
print(f"  → 3-choice (free): {len(free)} patterns")

print(f"\nP windows forcing X (count={len(forced_X)}):")
for v in forced_X:
    print(f"  z_val={v:3d}  pattern={'-'.join([DUTY_NAMES[x] for x in decode(v)])}")
print(f"\nP windows forcing N (count={len(forced_N)}):")
for v in forced_N:
    print(f"  z_val={v:3d}  pattern={'-'.join([DUTY_NAMES[x] for x in decode(v)])}")
print(f"\nP windows forcing W (count={len(forced_W)}):")
for v in forced_W:
    print(f"  z_val={v:3d}  pattern={'-'.join([DUTY_NAMES[x] for x in decode(v)])}")

print("\n" + "=" * 70)
print("운영 시나리오: 10명의 past_5days가 각각 P set에서 자연 분포")
print("=" * 70)
import random

def simulate_pasts(seed, num_emp=10):
    random.seed(seed)
    pasts = [random.choice(list(P_SET)) for _ in range(num_emp)]
    return pasts

day0_cap = (6, 2, 2)  # May 1 = Fri = high day

trials = 1000
conflicts = 0
forced_counts_dist = []
for trial in range(trials):
    pasts = simulate_pasts(seed=trial)
    forced_day0 = []
    for v in pasts:
        nxt = Z_RULES[v]
        if len(nxt) == 1:
            forced_day0.append(nxt[0])
    cnt = Counter(forced_day0)
    forced_counts_dist.append((cnt.get('W', 0), cnt.get('N', 0), cnt.get('X', 0)))
    # check conflict with day0 capacity (W=6, N=2, X=2)
    if cnt.get('W', 0) > 6 or cnt.get('N', 0) > 2 or cnt.get('X', 0) > 2:
        conflicts += 1

print(f"1000 random trials with day 0 cap = (W=6, N=2, X=2):")
print(f"  Direct conflicts (forced > cap): {conflicts}/{trials} ({conflicts/trials*100:.1f}%)")
# Distribution of forced X count
x_dist = Counter([f[2] for f in forced_counts_dist])
n_dist = Counter([f[1] for f in forced_counts_dist])
print(f"  Forced X count distribution: {dict(sorted(x_dist.items()))}")
print(f"  Forced N count distribution: {dict(sorted(n_dist.items()))}")

# What's the probability of >2 X forced
x_over = sum(c for k, c in x_dist.items() if k > 2)
n_over = sum(c for k, c in n_dist.items() if k > 2)
print(f"  P(forced X > 2) = {x_over/trials*100:.1f}%")
print(f"  P(forced N > 2) = {n_over/trials*100:.1f}%")

print("\n" + "=" * 70)
print("같은 분석, day 0 = May 1 high day: 결론")
print("=" * 70)
print(f"P set 52개 중 next='X' 강제 = {len(forced_X)}개 ({len(forced_X)/52*100:.0f}%)")
print(f"P set 52개 중 next='N' 강제 = {len(forced_N)}개 ({len(forced_N)/52*100:.0f}%)")
print(f"P set 52개 중 next='W' 강제 = {len(forced_W)}개 ({len(forced_W)/52*100:.0f}%)")

# what fraction of P set windows have forced-X next?
print(f"\n랜덤 직원 1명의 past가 X-강제 윈도우일 확률 ≈ {len(forced_X)/52*100:.0f}%")
print(f"10명 중 X-강제 직원 수 E[X] = 10 × {len(forced_X)/52:.3f} = {10*len(forced_X)/52:.2f}")
print(f"Day 0 X capacity = 2 → 평균적으로 INFEASIBLE 가능성 매우 높음")
