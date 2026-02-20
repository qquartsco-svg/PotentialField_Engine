# Potential Field Engine 개념 및 논문 출처

**작성일**: 2026-02-20  
**작성자**: GNJz (Qquarts)

---

## 🎯 은유 → 실제 코드 매핑

### 태양계 은유

**은유**: 태양계, 중력, 궤도

**실제 코드**:
- `GravityField`: 중력 퍼텐셜 `V_gravity(x) = -G * M / ||x - x_center||`
- `PotentialFieldEngine`: 필드 계산 `g(x) = -∇V(x)`
- 상태 업데이트: `v_{t+1} = v_t + dt * a`, `x_{t+1} = x_t + dt * v_{t+1}`

**출처**:
- Newtonian mechanics
- Classical field theory

---

### 우물 은유

**은유**: 우물, 안정점, 수렴

**실제 코드**:
- `WellFormationEngine`: Hopfield 에너지 `E(x) = -(1/2) * Σ_ij w_ij x_i x_j - Σ_i b_i x_i`
- `NeuralDynamicsCore`: 동역학 `τ · dx/dt = -x + f(Wx + I + b)`
- 수렴: `|E_{t+1} - E_t| < ε`

**출처**:
- Hopfield, J. J. (1982). "Neural networks and physical systems with emergent collective computational abilities"
- Lyapunov stability theory

---

### 난류 은유

**은유**: 난류, 혼돈, 비선형

**실제 코드**:
- `GridAnalyzer`: 발산 `∇·g = ∂g_x/∂x + ∂g_y/∂y`, 회전 `∇×g = ∂g_y/∂x - ∂g_x/∂y`
- 벡터장 구조 분석: 발산 (소스/싱크 구조), 회전 (비보존 성분)

**출처**:
- Navier-Stokes equations
- Fluid dynamics
- Chaos theory

---

## 📚 개념 및 논문 출처

### 퍼텐셜 필드

**개념**: 상태공간의 각 점에서의 에너지 값

**수식**: `V(x): R^n → R`

**출처**:
- Classical mechanics (Lagrangian/Hamiltonian formalism)
- Field theory

**참고 문헌**:
- Lagrange, J. L. (1788). "Mécanique Analytique"
- Hamilton, W. R. (1834). "On a General Method in Dynamics"

---

### 필드 (기울기)

**개념**: 퍼텐셜의 음의 기울기

**수식**: `g(x) = -∇V(x)`

**출처**:
- Vector calculus
- Gradient descent theory

**참고 문헌**:
- Cauchy, A. L. (1847). "Méthode générale pour la résolution des systèmes d'équations simultanées"

---

### 중력 퍼텐셜

**개념**: 중력에 의한 퍼텐셜 에너지

**수식**: `V_gravity(x) = -G * M / ||x - x_center||`

**출처**:
- Newtonian mechanics
- Universal gravitation law

**참고 문헌**:
- Newton, I. (1687). "Philosophiæ Naturalis Principia Mathematica"
- Poisson, S. D. (1813). "Remarques sur une équation qui se présente dans la théorie des attractions"

---

### Hopfield 에너지

**개념**: 신경망의 에너지 함수

**수식**: `E(x) = -(1/2) * Σ_ij w_ij x_i x_j - Σ_i b_i x_i`

**출처**:
- Hopfield, J. J. (1982). "Neural networks and physical systems with emergent collective computational abilities"
- Cohen, M. A., & Grossberg, S. (1983). "Absolute stability of global pattern formation"

**참고 문헌**:
- Hopfield, J. J. (1982). "Neural networks and physical systems with emergent collective computational abilities"
- Cohen, M. A., & Grossberg, S. (1983). "Absolute stability of global pattern formation"
- Hebb, D. O. (1949). "The Organization of Behavior: A Neuropsychological Theory"

---

### Lyapunov 안정성

**개념**: 동역학 시스템의 안정성

**수식**: `dE/dt ≤ 0` (에너지 감소)

**출처**:
- Lyapunov, A. M. (1892). "The General Problem of the Stability of Motion"
- Khalil, H. K. (2002). "Nonlinear Systems"

**참고 문헌**:
- Lyapunov, A. M. (1892). "The General Problem of the Stability of Motion"
- Khalil, H. K. (2002). "Nonlinear Systems" (3rd ed.)

---

### 발산 (Divergence)

**개념**: 벡터장의 발산 정도

**수식**: `∇·g = ∂g_x/∂x + ∂g_y/∂y`

**출처**:
- Vector calculus (Gauss's theorem)
- Fluid dynamics

**참고 문헌**:
- Arfken, G. B., Weber, H. J., & Harris, F. E. (2013). "Mathematical Methods for Physicists" (7th ed.). Academic Press.
- Vector calculus (Gauss's theorem): 표준 벡터 해석 교과서 참조
- Navier, C. L. M. H. (1822). "Mémoire sur les lois du mouvement des fluides"

---

### 회전 (Curl)

**개념**: 벡터장의 회전 정도

**수식**: `∇×g = ∂g_y/∂x - ∂g_x/∂y` (2D)

**출처**:
- Vector calculus (Stokes' theorem)
- Electromagnetism

**참고 문헌**:
- Arfken, G. B., Weber, H. J., & Harris, F. E. (2013). "Mathematical Methods for Physicists" (7th ed.). Academic Press.
- Vector calculus (Stokes' theorem): 표준 벡터 해석 교과서 참조
- Maxwell, J. C. (1865). "A dynamical theory of the electromagnetic field"

---

### 난류 (Turbulence)

**개념**: 비선형 유체 동역학의 혼돈 현상

**수식**: Navier-Stokes equations

**출처**:
- Navier-Stokes equations
- Chaos theory
- Nonlinear dynamics

**참고 문헌**:
- Navier, C. L. M. H. (1822). "Mémoire sur les lois du mouvement des fluides"
- Lorenz, E. N. (1963). "Deterministic nonperiodic flow"
- Feigenbaum, M. J. (1978). "Quantitative universality for a class of nonlinear transformations"

---

## 🔗 표준 API

### Extensions 저장 규약

**위치**: `GlobalState.extensions`

**규약**:
```python
# 저장
state.set_extension(engine_name: str, data: Dict[str, Any])

# 조회
data = state.get_extension(engine_name: str, default: Any = None)

# 업데이트
state.update_extension(engine_name: str, updates: Dict[str, Any])
```

**규칙**:
- 엔진 이름을 키로 사용
- 데이터는 딕셔너리 형태
- 각 엔진은 자신의 extension만 수정

---

### 엔진 호출 메서드 이름

**표준 메서드**:
```python
class SelfOrganizingEngine:
    def update(self, state: GlobalState) -> GlobalState:
        """상태 업데이트 (필수)"""
        pass
    
    def get_energy(self, state: GlobalState) -> float:
        """에너지 반환 (선택)"""
        pass
    
    def get_state(self) -> Dict[str, Any]:
        """엔진 내부 상태 반환 (선택)"""
        pass
    
    def reset(self):
        """상태 리셋 (선택)"""
        pass
```

**불변성 원칙**:
```python
# ✅ 올바른 방법
def update(self, state: GlobalState) -> GlobalState:
    new_state = state.copy(deep=False)  # 복사
    new_state.state_vector = ...  # 새 상태 수정
    return new_state  # 새 상태 반환
```

---

**작성자**: GNJz (Qquarts)  
**상태**: 개념 및 논문 출처 정리 완료

