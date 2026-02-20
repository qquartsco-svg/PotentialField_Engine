# GridAnalyzer 축/간격 버그 수정

**작성일**: 2026-02-20  
**작성자**: GNJz (Qquarts)  
**버전**: 0.1.0

---

## 🐛 발견된 버그

### 문제점

`grid_analyzer.py`에서 `np.meshgrid(..., indexing='ij')`를 사용했지만, `compute_divergence()`와 `compute_curl()`에서 축과 간격 계산이 잘못되어 있었습니다.

### 잘못된 코드

```python
# indexing='ij' 기준으로는 틀림
dx = (x_max - x_min) / (self.grid_size[1] - 1)  # ❌ grid_size[0]이어야 함
dy = (y_max - y_min) / (self.grid_size[0] - 1)  # ❌ grid_size[1]이어야 함

dgx_dx = np.gradient(gx_map, axis=1) / dx  # ❌ axis=0이어야 함
dgy_dy = np.gradient(gy_map, axis=0) / dy  # ❌ axis=1이어야 함
```

### 올바른 코드

```python
# indexing='ij' 기준: axis=0이 x 방향, axis=1이 y 방향
# grid_size = (N_x, N_y)
dx = (x_max - x_min) / (self.grid_size[0] - 1)  # ✅ grid_size[0] = N_x
dy = (y_max - y_min) / (self.grid_size[1] - 1)  # ✅ grid_size[1] = N_y

# ∂/∂x → axis=0, ∂/∂y → axis=1
dgx_dx = np.gradient(gx_map, axis=0) / dx  # ✅ axis=0 (x 방향)
dgy_dy = np.gradient(gy_map, axis=1) / dy  # ✅ axis=1 (y 방향)
```

---

## 📐 indexing='ij' 규약

### meshgrid indexing='ij' 의미

```python
x_grid, y_grid = np.meshgrid(x, y, indexing='ij')
```

**결과**:
- `x_grid.shape = (N_x, N_y)`
- `y_grid.shape = (N_x, N_y)`
- `x_grid[i, j] = x[i]` (axis=0이 x 방향)
- `y_grid[i, j] = y[j]` (axis=1이 y 방향)

### 축 매핑

| 방향 | axis | grid_size 인덱스 |
|------|------|------------------|
| x 방향 | 0 | grid_size[0] = N_x |
| y 방향 | 1 | grid_size[1] = N_y |

### 미분 축 매핑

| 미분 | axis | 간격 계산 |
|------|------|----------|
| ∂/∂x | 0 | dx = (x_max - x_min) / (grid_size[0] - 1) |
| ∂/∂y | 1 | dy = (y_max - y_min) / (grid_size[1] - 1) |

---

## ✅ 수정 내용

### compute_divergence()

**수정 전**:
```python
dx = (x_max - x_min) / (self.grid_size[1] - 1)  # ❌
dy = (y_max - y_min) / (self.grid_size[0] - 1)  # ❌
dgx_dx = np.gradient(gx_map, axis=1) / dx  # ❌
dgy_dy = np.gradient(gy_map, axis=0) / dy  # ❌
```

**수정 후**:
```python
dx = (x_max - x_min) / (self.grid_size[0] - 1)  # ✅
dy = (y_max - y_min) / (self.grid_size[1] - 1)  # ✅
dgx_dx = np.gradient(gx_map, axis=0) / dx  # ✅
dgy_dy = np.gradient(gy_map, axis=1) / dy  # ✅
```

### compute_curl()

**수정 전**:
```python
dx = (x_max - x_min) / (self.grid_size[1] - 1)  # ❌
dy = (y_max - y_min) / (self.grid_size[0] - 1)  # ❌
dgy_dx = np.gradient(gy_map, axis=1) / dx  # ❌
dgx_dy = np.gradient(gx_map, axis=0) / dy  # ❌
```

**수정 후**:
```python
dx = (x_max - x_min) / (self.grid_size[0] - 1)  # ✅
dy = (y_max - y_min) / (self.grid_size[1] - 1)  # ✅
dgy_dx = np.gradient(gy_map, axis=0) / dx  # ✅
dgx_dy = np.gradient(gx_map, axis=1) / dy  # ✅
```

---

## 🧪 검증

### 수학적 검증

**발산 (Divergence)**:
```
∇·g = ∂g_x/∂x + ∂g_y/∂y
```

**회전 (Curl, 2D)**:
```
∇×g = ∂g_y/∂x - ∂g_x/∂y
```

### 수치 검증

- `indexing='ij'` 기준으로 축과 간격이 일치하는지 확인
- 순수 퍼텐셜 필드에서 curl ≈ 0 확인
- 발산 값이 물리적으로 의미 있는지 확인

---

## 📊 영향 범위

### 영향받는 기능

- ✅ `compute_divergence()`: 발산 계산
- ✅ `compute_curl()`: 회전 계산
- ✅ `analyze()`: 전체 분석 (위 두 함수 사용)

### 영향받지 않는 기능

- ✅ `compute_potential_map()`: 퍼텐셜 맵 계산
- ✅ `compute_field_map()`: 필드 맵 계산
- ✅ 시각화 함수들: 데이터만 사용하므로 영향 없음

---

## ✅ 최종 확인

### 수정 완료

- ✅ `compute_divergence()`: 축/간격 수정 완료
- ✅ `compute_curl()`: 축/간격 수정 완료
- ✅ 주석 추가: indexing='ij' 규약 명시

### 검증 필요

- ⚠️ 실제 데이터로 발산/회전 값 검증 권장
- ⚠️ 순수 퍼텐셜 필드에서 curl ≈ 0 확인

---

**작성자**: GNJz (Qquarts)  
**상태**: 버그 수정 완료 ✅

