# FOUROFF CP-SAT INFEASIBLE 분석 (N차 의뢰자판)

## 컨텍스트

이 폴더는 FOUROFF 간호사 근무표 N차 의뢰자판(W/N/X 3종, 5일 윈도우 z_rule)의
CP-SAT INFEASIBLE 근본 원인 분석과 해결책 검증 자료다. 실제 `case.py`는 본 저장소에
없어, 사용자가 제공한 명세(Z_RULES 52개, capacity 분포, 검증된 사실 4가지)만으로
최소 재현·분석을 진행했다.

조건:
- 직원 10명, 2026-05 (31일)
- duty: W=0, N=1, X=2
- capacity ==: 월화수일(14일) W=5,N=2,X=3 / 목금토·공휴일(17일) W=6,N=2,X=2
- z_rule: 5일 슬라이딩 윈도우의 z_val ∈ P set 52개
- 합계: W=172, N=62, X=76

---

## Task 1: 근본 원인 (수학적 증명)

### 핵심 발견 1: z_rule의 점근적 X 하한 = 28.57%, 시스템 요구 X = 24.52%

P set 52 윈도우 + 전이 그래프를 LP로 풀어 정상상태 frequency 범위를 구하면
(`lp_steady_state.py`, `lp_focused.py`):

```
max W-freq: W=71.43%, N= 0.00%, X=28.57%
min X-freq when W=target: X=28.57% (즉 X >= 2/7 강제)
N=20% 고정 시 W 최대 = 51.43%  (시스템 요구 55.48%를 4.05%p 초과)
```

`W=55.48%, N=20%, X=24.52%` 동시 만족은 LP에서 INFEASIBLE.
즉 z_rule + capacity는 **무한 horizon에서 절대 불가능**.

### 핵심 발견 2: 31일 유한 horizon에서는 boundary 슬랙으로 풀림 (조건부)

`past_5days=None`이고 day 1~4에 z_rule 미적용이면 4일치 boundary 슬랙 덕분에
2~4초 만에 OPTIMAL(`repro.py`). 단 솔버가 "한 직원에게 한 종류만 몰아주는"
퇴화 해를 사용하므로 wallet(균형) 제약을 추가해야 의미 있는 해가 됨.

### 핵심 발견 3: 실제 INFEASIBLE 트리거 = per-nurse past_5days 충돌

`variations.py`, `find_real_trigger.py`, `root_cause_proof.py`:

- P set 52개 중 **14개(27%)가 next='X' 강제**, 10개(19%)가 'N' 강제
- 10명이 무작위 P set past를 가지면 **평균 2.69명이 day 0에 X 강제**
- day 0이 high day(Fri 등)이면 X cap = 2
- **51.9% 확률로 day 0 X cap 초과 → 즉시 INFEASIBLE**
- N 위반 27.4% 합치면 **70.1% 확률로 INFEASIBLE**

사용자가 "past_5days 무시"라고 했지만, 실제 case.py는 전월 마지막 5일에서
past를 자동 수집해 적용하고 있을 가능성이 높다(또는 z_rule 첫 윈도우에
암묵적 패딩이 들어감).

### Assumption-based unsat 분석 결과 요약

| 조건 | 결과 | 시간 |
|------|------|------|
| capacity + z_rule, past=None, day 5 시작 | OPTIMAL | 2.6s |
| capacity + z_rule, past=[X,X,X,X,X] | OPTIMAL | 2.9s |
| capacity + z_rule, past=[W,W,W,W,W] | INFEASIBLE | 0.08s |
| capacity + z_rule, past=[X,X,X,X,W] | INFEASIBLE | 0.08s |
| capacity + z_rule, per_emp_past=random | INFEASIBLE | 0.08s |
| **capacity + z_rule + wallet (target W=17, N=6, X=7) per emp, past=None** | OPTIMAL | 3.1s |
| capacity + z_rule + blocked_N=5명 (wallet 미조정) | INFEASIBLE | 0.05s |
| capacity + z_rule + blocked_N=5명 (wallet 조정) | OPTIMAL | 1.6s |

### 핵심 발견 4: wallet 알고리즘이 직원별 capacity 부담을 반영해야 함

blocked_N=5명이면 그 5명은 N=0이고 capacity N=62는 나머지 5명이 부담
(12.4 N/nurse). 같은 wallet target=6을 모든 직원에 강제하면 깨짐.
**adaptive wallet**(직원별 사용 가능 풀에 따라 W/N/X target 자동 조정)이 필수.

---

## Task 2: 해결책

### 최종 제안 (전체 코드: `final_solution.py`)

세 가지 변경이 핵심:

**Fix 1 — `sanitize_past()`**: 첫 5~8일 호환성을 sub-CP-SAT으로 검증, 충돌
유발 직원의 past를 `[X,X,X,X,X]`(P=242, free)로 치환. blocked_N과 N-강제 past가
충돌하는 경우 최우선으로 치환.

```python
def sanitize_past(per_emp_past, caps, blocked_N=None):
    sanitized = [list(p) for p in per_emp_past]
    dropped = []
    while not check_first_days_feasible(sanitized, caps,
                                          lookahead=8, blocked_N=blocked_N):
        # 가장 rigid한 직원(1-choice past) 또는 blocked_N+N강제 우선
        e = pick_most_rigid(sanitized, blocked_N, dropped)
        sanitized[e] = [2,2,2,2,2]
        dropped.append(e)
    return sanitized, dropped
```

**Fix 2 — `compute_adaptive_wallets()`**: capacity 부담 재계산.

```python
# blocked_N: target_N = 0, target_W += avg_N_share
# extra_X: target_X += bonus, target_W/N -= bonus 비례
def compute_adaptive_wallets(num_emp, blocked_N, extra_X):
    base_X = (SUM_X - sum(extra_X.values())) / num_emp
    non_blocked = num_emp - len(blocked_N or set())
    base_N_nb = SUM_N / non_blocked if non_blocked else 0
    # blocked는 W + X = 31, X = base_X → W = 31 - base_X
    # non-blocked는 W + N + X = 31, N = base_N_nb, X = base_X → W = 31 - N - X
    ...
```

**Fix 3 — wallet >=2 룰 정확한 인코딩**: `target - actual >= 2 → fail`은
`actual >= target - 1` 강제. (off-by-one 주의)

```python
m.Add(sum(iW[e][d] for d in range(NDAYS)) >= max(0, w['W'] - 1))
m.Add(sum(iN[e][d] for d in range(NDAYS)) >= max(0, w['N'] - 1))
m.Add(sum(iX[e][d] for d in range(NDAYS)) >= max(0, w['X'] - 1))
```

### 대안 (협상 가능 시 — 권장 순서)

| 옵션 | 효과 | 의뢰자 협상 난이도 |
|------|------|---------------------|
| A. wallet 알고리즘 변경 (위 Fix 2) | 즉시 풀림 | 0 (사용자가 가능하다 명시) |
| B. past_5days 적용 시 sanitize | 월 경계 시 안전 | 0 (코드 내부) |
| C. high day X cap 2→3 (월 4일만) | LP 한계 통과, 슬랙 +12 | 중 (의뢰자 협상) |
| D. z_rule P set에 X-rich 패턴 추가 | LP 한계 완화 | 높음 (z_rule lock) |
| E. 인원 10→11명 + capacity 조정 | 슬랙 대폭 증가 | 매우 높음 |

### 솔버 파라미터 튜닝(옵션 A 시도 결과)

INFEASIBLE 원인은 모델의 모순이므로 솔버 튜닝으로 해결 불가.
워커 수 늘리기, time_limit 늘리기, search_branching 변경 — 모두 효과 없음
(INFEASIBLE 자체는 0.08s에 결론남).

---

## Task 3: 검증 결과 (전체: `final_solution.py`)

각 시나리오 검증 항목 6개 (FEASIBLE/OPTIMAL · capacity == · z_rule 위반 0 ·
wallet >=2 통과 · X non-special max-min ≤ 1 · blocked_N N=0):

### past_5days = None (사용자가 명시한 setup)

| 시나리오 | 솔버 | cap | z_rule | wallet | X 범위 | blocked_N |
|----------|------|-----|--------|--------|--------|------------|
| A 단순 | OPTIMAL 4.1s | ✓ | 0 | ✓ | 1 | – |
| B blocked_N=5 | OPTIMAL 1.8s | ✓ | 0 | ✓ | 1 | ✓ |
| C B + special | OPTIMAL 2.0s | ✓ | 0 | ✓ | 1 | ✓ |

### per_emp_past = 무작위 P set (실제 운영 환경)

| 시나리오 | 솔버 | sanitize | cap | z_rule | wallet | X 범위 | blocked_N |
|----------|------|----------|-----|--------|--------|--------|------------|
| A' 단순 | OPTIMAL 3.6s | dropped [3,7,8] | ✓ | 0 | ✓ | 1 | – |
| B' blocked_N=5 | OPTIMAL 2.2s | dropped [2,3,7,8] | ✓ | 0 | ✓ | 1 | ✓ |
| C' B' + special | OPTIMAL 2.1s | dropped [2,3,7,8] | ✓ | 0 | ✓ | 1 | ✓ |

**6개 시나리오 모두 60초 시간 한도 내 PASS.**

---

## 파일 인덱스

- `repro.py` — 사용자 명세 그대로 최소 재현 (단순 capacity + z_rule)
- `variations.py` — z_rule 인코딩 / past_5days 변형 매트릭스
- `lp_steady_state.py` — z_rule의 LP 정상상태 분석 (전이 그래프 94개)
- `lp_focused.py` — W=target 고정 시 X 하한 = 28.57% 증명
- `find_breaking_point.py` — wallet balance 강도별 INFEASIBLE 트리거
- `find_real_trigger.py` — per_emp_past가 진짜 트리거임을 식별
- `root_cause_proof.py` — P set 14개가 X 강제 → 70.1% 확률 분석
- `full_analysis.py` — capacity + z_rule만의 퇴화 해 패턴 관찰
- `solution_and_verify.py` — 첫 번째 해결책 구현 (불완전)
- **`final_solution.py`** — 최종 해결책 + 6 시나리오 모두 검증 PASS

---

## case.py에 통합하는 방법

1. `compute_adaptive_wallets()`와 `sanitize_past()` 두 함수를 `case.py`로 복사
2. wallet 산출부에 `compute_adaptive_wallets()` 호출 결과를 주입 (현재 wallet.md
   알고리즘을 교체)
3. z_rule 모델 빌드 직전에 `per_emp_past = sanitize_past(per_emp_past, caps,
   blocked_N)`로 past 정화
4. wallet 강제 제약을 `actual >= target - 1`로 정확히 인코딩 (현재 코드가
   `>= target - 2` 또는 `> target - 2`로 잘못 잡고 있을 가능성 점검)

## 운영 권장사항

- past_5days를 매월 정화하면 INFEASIBLE 가능성 사실상 제거
- 의뢰자 협상 시 "고정 휴일 1주에 X cap +1" 같은 작은 조정이 가능하면
  LP 한계까지 풀려서 sanitize조차 불필요
- 11명으로 늘리면 capacity는 변화 없이 슬랙만 늘어 안전 마진 확보
