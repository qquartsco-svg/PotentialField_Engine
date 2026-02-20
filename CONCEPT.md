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
- 높은 퍼텐셜 = 불안정한 영역
- 낮은 퍼텐셜 = 안정된 영역 (우물)

---

### 2. 필드 (Field)

**정의**: 퍼텐셜의 기울기 (음의 기울기)

```
g(x) = -∇V(x)
```

**의미**:
- 필드 방향 = 상태가 이동하는 방향
- 필드 크기 = 이동 속도

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

### 왜곡 탐지

**필드 발산 (Divergence)**:
```
∇·g = Σ_i (∂g_i/∂x_i)
```

**의미**:
- ∇·g > 0: 발산 영역 (불안정)
- ∇·g < 0: 수렴 영역 (안정)
- ∇·g = 0: 중성 영역

**필드 회전 (Curl)**:
```
∇×g = (∂g_y/∂x - ∂g_x/∂y)  (2D)
```

**의미**:
- ∇×g ≠ 0: 왜곡 영역 (비보존력)
- ∇×g = 0: 보존력 영역

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

