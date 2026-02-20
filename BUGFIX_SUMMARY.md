# PotentialFieldEngine 버그 수정 요약

**작성일**: 2026-02-20  
**작성자**: GNJz (Qquarts)  
**버전**: 0.1.0

---

## ✅ 수정된 버그

### 1. PotentialFieldEngine: dim == 0 분기 로직 버그 ✅

**문제**:
- `dim = len(state_vector) // 2` 방식은 홀수 길이 벡터 대응 불가
- `dim == 0` 분기는 `len == 1`일 때만 작동 (실효성 없음)
- 홀수 길이면 x와 v가 찢어짐

**수정**:
- **짝수 길이 규약 강제**: `state_vector`는 항상 `[x, v]` 쌍이어야 함
- `update()` 시작 시 `n % 2 != 0`이면 `ValueError` 발생
- `dim == 0` 분기 제거 (불필요)

**코드 변경**:
```python
# 수정 전
dim = len(new_state.state_vector) // 2
if dim == 0:
    x = new_state.state_vector
    v = np.zeros_like(x)
else:
    x = new_state.state_vector[:dim]
    v = new_state.state_vector[dim:]

# 수정 후
n = len(new_state.state_vector)
if n % 2 != 0:
    raise ValueError(
        f"state_vector must have even length (got {n}). "
        f"Expected format: [x1, ..., xN, v1, ..., vN] where N = {n//2}"
    )
dim = n // 2
x = new_state.state_vector[:dim]
v = new_state.state_vector[dim:]
```

---

### 2. GridAnalyzer: compute_field_map() epsilon=None 버그 ✅

**문제**:
- `compute_field_map(..., epsilon: float = None)`에서 `epsilon`이 `None`이면 `TypeError` 발생
- `analyze()`에서는 채워서 넘기지만, 직접 호출 시 죽음

**수정**:
- 함수 시작에서 `epsilon = epsilon if epsilon is not None else EPSILON` 처리
- 직접 호출 시에도 안전

**코드 변경**:
```python
# 수정 전
def compute_field_map(..., epsilon: float = None):
    ...
    x_plus[0] += epsilon  # TypeError if epsilon is None

# 수정 후
def compute_field_map(..., epsilon: float = None):
    epsilon = epsilon if epsilon is not None else EPSILON
    ...
    x_plus[0] += epsilon  # 안전
```

---

### 3. GridAnalyzer: grid shape/indexing 순서 버그 ✅

**문제**:
- `meshgrid(x, y)`는 기본 indexing이면 shape이 `(len(y), len(x))` = `(N_y, N_x)`
- `grid_size = (N_x, N_y)`로 정의했는데 실제 shape과 불일치
- 인덱스가 엇갈려서 오차 발생

**수정**:
- `meshgrid(..., indexing='ij')` 사용하여 shape을 `(N_x, N_y)`로 맞춤
- `grid_size`와 일치

**코드 변경**:
```python
# 수정 전
x_grid, y_grid = np.meshgrid(x, y)  # shape: (N_y, N_x)

# 수정 후
x_grid, y_grid = np.meshgrid(x, y, indexing='ij')  # shape: (N_x, N_y)
```

---

### 4. divergence/curl 해석 문구 완화 ✅

**문제**:
- "divergence > 0 불안정 / <0 안정"은 물리적으로 과장됨
- 순수 퍼텐셜 필드는 curl = 0 (수치 오차만)
- 발산은 "안정/불안정"과 직접 연결되지 않음

**수정**:
- **divergence**: "소스/싱크(질량/원천/흡수) 또는 라플라시안 구조"로 수정
- **curl**: "비보존 성분/비퍼텐셜 성분 탐지"로 명확화

**코드 변경**:
```python
# 수정 전
"""
의미:
- ∇·g > 0: 발산 영역 (불안정)
- ∇·g < 0: 수렴 영역 (안정)
"""

# 수정 후
"""
물리적 의미:
- ∇·g > 0: 소스 영역 (질량/원천이 있는 영역)
- ∇·g < 0: 싱크 영역 (흡수/소멸이 있는 영역)
- ∇·g = 0: 라플라시안 구조 (보존 영역)

참고:
- 순수 퍼텐셜 필드(g = -∇V)의 경우 Poisson 방정식: ∇²V = -∇·g
- 발산은 "안정/불안정"과 직접 연결되지 않음 (라플라시안 구조 탐지)
"""
```

---

### 5. PotentialFieldEngine: 해석적 기울기 지원 추가 ✅

**개선**:
- `field_func: Optional[Callable[[x], np.ndarray]]` 파라미터 추가
- 있으면 해석적 필드 사용 (성능/정확도 우수)
- 없으면 수치 미분으로 fallback

**코드 변경**:
```python
# 수정 전
def __init__(self, potential_func, ...):
    self.potential_func = potential_func

def _compute_field(self, x):
    # 항상 수치 미분
    ...

# 수정 후
def __init__(self, potential_func, field_func=None, ...):
    self.potential_func = potential_func
    self.field_func = field_func  # Optional

def _compute_field(self, x):
    if self.field_func is not None:
        return self.field_func(x)  # 해석적 필드
    # 수치 미분 (fallback)
    ...
```

**사용 예시**:
```python
from gravity_field import GravityField

gravity = GravityField(masses)
engine = PotentialFieldEngine(
    potential_func=gravity.potential,
    field_func=gravity.field  # 해석적 필드 사용
)
```

---

## ✅ 검증 완료

### 코드 레벨 검증
- [x] 짝수 길이 규약 강제: 홀수 길이 시 `ValueError` 발생 확인
- [x] epsilon None 처리: 직접 호출 시에도 안전
- [x] meshgrid indexing: shape 일치 확인
- [x] field_func 지원: 해석적 필드 사용 가능

### 물리적 정확성
- [x] divergence 해석: 물리적으로 정확한 의미로 수정
- [x] curl 해석: 비보존 성분 탐지로 명확화

---

## 🎯 결과

**줄기 보호**: ✅
- 단일 GlobalState 유지
- 짝수 길이 규약으로 차원 일관성 보장
- 인덱싱 일관화로 오차 방지

**성능 개선**: ✅
- 해석적 필드 지원으로 수치 미분 비용 감소
- 정확도 향상

**물리적 정확성**: ✅
- 발산/회전 해석 문구 완화
- 물리적으로 정확한 의미로 수정

---

**작성자**: GNJz (Qquarts)  
**상태**: 버그 수정 완료 ✅

