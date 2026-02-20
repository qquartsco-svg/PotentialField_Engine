# Potential Field Engine 개념

**작성일**: 2026-02-20  
**작성자**: GNJz (Qquarts)

---

## 🎯 핵심 개념

### 1. 퍼텐셜 (Potential)

**정의**: 상태공간의 각 점에서의 에너지 값

```
V(x): R^n → R
```

**의미**: 
- 직관적으로, 낮은 퍼텐셜 영역은 에너지 최소점 근처에서 안정적일 수 있음 (예: 우물)
- **주의**: 퍼텐셜의 절대값만으로는 안정성을 판단할 수 없음
  - 새들 포인트(saddle point)는 퍼텐셜이 낮을 수도 있지만 불안정
  - 안정성은 일반적으로 임계점(∇V = 0)에서의 Hessian 고유값(또는 Lyapunov 함수)로 판단함
  - Hessian의 고유값이 모두 양수이면 국소 최소점(안정), 음수이면 국소 최대점(불안정), 혼합이면 새들 포인트

---

### 2. 필드 (Field)

**정의**: 퍼텐셜의 기울기 (음의 기울기)

```
g(x) = -∇V(x)
```

**의미**:
- 필드 방향 = 상태가 이동하는 방향
- 필드 크기 = 가속도의 크기 (속도 변화율)
- 이동 속도는 현재 속도 v의 크기

**수식**:
```
g_i(x) = -∂V/∂x_i
```

---

### 3. 가속도 (Acceleration)

**정의**: 필드에 의한 가속도

```
a = g(x) = -∇V(x)
```

**의미**: 상태가 퍼텐셜을 따라 이동하는 가속도

---

### 4. 동역학 (Dynamics)

**위치-속도 분리**:
```
state_vector = [x1, x2, ..., xN, v1, v2, ..., vN]
```

**업데이트 수식**:
```
v_{t+1} = v_t + dt * a
x_{t+1} = x_t + dt * v_{t+1}
```

**참고**: 위 적분 방식은 semi-implicit (symplectic) Euler 형태이다. 일반 explicit Euler보다 에너지 보존 특성이 우수하다.

**에너지**:
```
E = (1/2) * ||v||^2 + V(x)
```

---

## 🌍 중력장 (Gravity Field)

### 중력 퍼텐셜

**점 질량**:
```
V_gravity(x) = -G * M / ||x - x_center||
```

**여러 질량**:
```
V_gravity(x) = -G * Σ_i (M_i / ||x - x_i||)
```

**연속 분포**:
```
V_gravity(x) = -G * ∫ (ρ(y) / ||x - y||) dy
```

### 중력 필드

**필드 계산**:
```
g_gravity(x) = -∇V_gravity(x)
            = -G * Σ_i (M_i * (x - x_i) / ||x - x_i||^3)
```

---

## 🔍 그리드 기반 분석

### 상태공간 그리드

**2D 그리드**:
```
x_range = [x_min, x_max]
y_range = [y_min, y_max]
grid_size = (N_x, N_y)

grid_points = [(x_i, y_j) for i in range(N_x), j in range(N_y)]
```

### 퍼텐셜 맵

**각 그리드 점에서 퍼텐셜 계산**:
```
V_map[i, j] = V(x_i, y_j)
```

### 필드 맵

**각 그리드 점에서 필드 계산**:
```
g_map[i, j] = -∇V(x_i, y_j)
```

### 벡터장 구조 분석

**필드 발산 (Divergence)**:
```
∇·g = Σ_i (∂g_i/∂x_i)
```

**의미**:
- ∇·g > 0: 소스 영역 (outflow, 플럭스가 외부로 나가는 영역)
- ∇·g < 0: 싱크 영역 (inflow, 플럭스가 내부로 흡수되는 영역)
- ∇·g = 0: 소스/싱크 없음 (locally solenoidal, 발산 0)

**물리적 의미**: 발산은 플럭스/소스·싱크/포아송 구조(라플라시안) 관점입니다. 순수 퍼텐셜 필드(g = -∇V)의 경우 Poisson 방정식 ∇²V = -∇·g로 연결됩니다. **안정성(고정점 안정/불안정)을 바로 판정하는 스칼라가 아닙니다.** 안정성 판단은 보통 고정점에서 Jacobian 고유값, 또는 퍼텐셜의 경우 Hessian(또는 Lyapunov)로 별도 수행합니다.

**필드 회전 (Curl)**:
```
∇×g = (∂g_y/∂x - ∂g_x/∂y)  (2D)
```

**의미**:
- ∇×g ≠ 0: 비보존 성분/비퍼텐셜 성분 (회전 성분 존재)
- ∇×g = 0: 순수 퍼텐셜 필드 (보존력, 수치 오차만 남음)

**물리적 의미**: 순수 퍼텐셜 필드(g = -∇V)는 이론상 curl = 0입니다 (연속/매끄러운 V 가정). 수치 계산에서는 격자 간격, epsilon(기울기 계산), 경계 조건, 특이점(예: r=0 근처 softening)에 의해 잔차가 남을 수 있습니다. curl ≠ 0이면 비퍼텐셜 성분(예: 마그네틱 필드, 비보존력) 탐지 가능합니다.

---

## 🔗 WellFormationEngine 연계

### Hopfield 에너지 → 퍼텐셜

**WellFormationEngine 결과**:
```
W: 가중치 행렬
b: 바이어스 벡터
```

**Hopfield 에너지**:
```
E(x) = -(1/2) * Σ_ij w_ij x_i x_j - Σ_i b_i x_i
```

**퍼텐셜로 사용**:
```
V(x) = E(x)
```

**필드 계산**:
```
g(x) = -∇E(x) = Wx + b
```

**참고**: 여기서는 Hopfield 표준처럼 W를 대칭으로 가정한다 (또는 W ← (W+Wᵀ)/2로 대칭화). 일반적으로 ∇E = -((W+Wᵀ)/2)x - b이고, W가 대칭이면 ∇E = -Wx - b → -∇E = Wx + b가 됩니다.

---

## 📊 필드 합성

### 여러 퍼텐셜 합성

**합성 수식**:
```
V_total(x) = V_gravity(x) + V_wells(x) + V_custom(x)
```

**필드 합성**:
```
g_total(x) = -∇V_total(x)
           = g_gravity(x) + g_wells(x) + g_custom(x)
```

---

## ✅ 설계 원칙

### 1. 불변성 유지

```python
# ❌ 잘못된 방법
state.state_vector = ...

# ✅ 올바른 방법
new_state = state.copy(deep=False)
new_state.state_vector = ...
return new_state
```

### 2. 하드코딩 제거

```python
# ❌ 잘못된 방법
epsilon = 1e-6

# ✅ 올바른 방법
def __init__(self, ..., epsilon: float = 1e-6):
    self.epsilon = epsilon
```

### 3. BrainCore 철학 유지

- GlobalState 하나 (단일 상태 중심)
- 엔진은 `update(state)` → `new_state` 반환
- extensions에 필드 정보 저장

---

**작성자**: GNJz (Qquarts)  
**상태**: 개념 정리 완료

