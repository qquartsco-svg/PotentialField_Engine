# PotentialFieldEngine

**퍼텐셜 필드 엔진** - 상태공간에 퍼텐셜 필드를 펼쳐 중력장, 우물, 커스텀 필드를 구현하고 발산/회전 분석을 수행합니다.

[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](README.md)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)

---

## 🎯 핵심 기능

- ✅ 퍼텐셜 필드 계산
- ✅ 중력장 구현
- ✅ 상태공간 그리드 분석
- ✅ 필드 분석 (발산/회전 계산)
- ✅ WellFormationEngine 연계
- ✅ 필드 합성

---

## 📐 수식

### 기본 수식

**퍼텐셜**:
```
V(x): R^n → R
```

**필드 (기울기)**:
```
g(x) = -∇V(x)
```

**가속도**:
```
a = g(x)
```

**동역학**:
```
v_{t+1} = v_t + dt * a
x_{t+1} = x_t + dt * v_{t+1}
```

**에너지**:
```
E = (1/2) * ||v||^2 + V(x)
```

### 중력장 수식

**점 질량**:
```
V_gravity(x) = -G * M / ||x - x_center||
```

**여러 질량**:
```
V_gravity(x) = -G * Σ_i (M_i / ||x - x_i||)
```

**필드**:
```
g_gravity(x) = -G * Σ_i (M_i * (x - x_i) / ||x - x_i||^3)
```

**수치 안정성 (softening)**:
- `gravity_field.py`의 `GravityField` 클래스에서 구현
- `r < softening`일 때 `r = softening`으로 클램프하여 수치 안정성 확보
- 기본값: `CONFIG.SOFTENING = 1e-6`
- 참고: 현재는 급격한 절단 방식이며, 천체물리 수준 정밀도가 필요한 경우 Plummer softening (`r = sqrt(|x - x_i|^2 + epsilon^2)`)으로 교체 가능

### 필드 분석 (발산/회전)

**발산 (Divergence)**: 소스/싱크 및 라플라시안 구조 탐지
```
∇·g = ∂g_x/∂x + ∂g_y/∂y
```

- ∇·g > 0: 소스 영역 (outflow, 플럭스가 외부로 나가는 영역)
- ∇·g < 0: 싱크 영역 (inflow, 플럭스가 내부로 흡수되는 영역)
- ∇·g = 0: 소스/싱크 없음 (locally solenoidal, 발산 0)

**참고**: 중력장의 경우 Poisson 방정식 ∇²V = -4πGρ에 의해, 질량 밀도(ρ > 0)가 있는 곳은 ∇·g < 0 (싱크)가 됩니다. 즉, 중력은 싱크 영역입니다.

**물리적 의미**: 발산은 플럭스/소스·싱크/포아송 구조(라플라시안) 관점입니다. 순수 퍼텐셜 필드(g = -∇V)의 경우 Poisson 방정식 ∇²V = -∇·g로 연결됩니다. **안정성(고정점 안정/불안정)을 바로 판정하는 스칼라가 아닙니다.** 안정성 판단은 보통 고정점에서 Jacobian 고유값, 또는 퍼텐셜의 경우 Hessian(또는 Lyapunov)로 별도 수행합니다.

**회전 (Curl)**: 비보존 성분 탐지
```
∇×g = ∂g_y/∂x - ∂g_x/∂y  (2D)
```

- ∇×g ≠ 0: 비보존 성분/비퍼텐셜 성분 (회전 성분 존재)
- ∇×g = 0: 순수 퍼텐셜 필드 (보존력, 수치 오차만 남음)

**물리적 의미**: 순수 퍼텐셜 필드(g = -∇V)는 이론상 curl = 0입니다. curl ≠ 0이면 비퍼텐셜 성분(예: 마그네틱 필드, 난류) 탐지 가능합니다.

---

## 🚀 설치

### 의존성

```bash
pip install numpy matplotlib
```

### BrainCore 연동 (선택적)

PotentialFieldEngine은 독립적으로 사용할 수 있으며, BrainCore와도 연동 가능합니다.

**독립 사용**:
- 모든 파일을 현재 디렉토리에 두고 직접 import하여 사용

**BrainCore 연동**:
- BrainCore가 설치되어 있어야 함
- BrainCore 경로를 PYTHONPATH에 추가하거나 BrainCore를 설치

---

## 📖 사용법

### 설치

```bash
# 저장소 클론
git clone https://github.com/qquartsco-svg/PotentialField_Engine.git
cd PotentialField_Engine

# 의존성 설치
pip install numpy matplotlib
```

### ⚠️ 중요: GlobalState 규약

**PotentialFieldEngine은 다음 규약을 요구합니다:**

```
GlobalState.state_vector MUST be 2N dimensional:
- First N elements: position [x1, x2, ..., xN]
- Last N elements: velocity [v1, v2, ..., vN]
```

**예시**:
- 2D: `state_vector = [x1, x2, v1, v2]` (길이 4)
- 3D: `state_vector = [x1, x2, x3, v1, v2, v3]` (길이 6)

**홀수 길이 입력 시**: `ValueError` 발생

### 기본 사용

```python
# 방법 1: 패키지로 설치/import (권장)
# 이 모듈은 상대 import를 사용하므로 패키지로 설치하거나 PYTHONPATH에 추가해야 합니다.
# pip install -e . 또는 PYTHONPATH에 추가 후
from potential_field_engine import PotentialFieldEngine
from gravity_field import create_gravity_potential
import numpy as np

# 중력 퍼텐셜 생성
masses = [(np.array([0.0, 0.0]), 1.0)]
gravity_potential = create_gravity_potential(masses, G=1.0)

# PotentialFieldEngine 생성
field_engine = PotentialFieldEngine(
    potential_func=gravity_potential,
    dt=0.01,
    epsilon=1e-6,
)

# BrainCore와 연동 (선택적)
# BrainCore가 설치되어 있어야 함
try:
    from brain_core import BrainCore, GlobalState
    
    core = BrainCore()
    core.register_engine("potential_field", field_engine, priority=30)
    
    # 실행
    initial_state = GlobalState(
        state_vector=np.concatenate([
            np.array([1.0, 0.0]),  # 위치
            np.array([0.0, 0.0]),  # 속도
        ]),
        energy=0.0,
        risk=0.0,
    )
    
    result = core.run_cycle(initial_state=initial_state)
except ImportError:
    print("BrainCore가 설치되지 않았습니다. 독립적으로 사용할 수 있습니다.")
    
    # 독립 사용 예시
    from brain_core.global_state import GlobalState  # 또는 직접 상태 생성
    
    # 상태 직접 생성 (예시)
    state_vector = np.concatenate([
        np.array([1.0, 0.0]),  # 위치
        np.array([0.0, 0.0]),  # 속도
    ])
    
    # 엔진 업데이트
    # new_state = field_engine.update(state)
```

### 그리드 분석

```python
# 현재 디렉토리에서 직접 import
from grid_analyzer import GridAnalyzer, GridVisualizer

# 그리드 분석기 생성
analyzer = GridAnalyzer(
    x_range=(-5.0, 5.0),
    y_range=(-5.0, 5.0),
    grid_size=(100, 100),
)

# 분석 수행
analysis_result = analyzer.analyze(
    potential_func=gravity_potential,
    epsilon=1e-6,
)

# 시각화
visualizer = GridVisualizer(analyzer)
visualizer.plot_all(analysis_result, save_dir="./output")
```

---

## 🔗 WellFormationEngine 연계

### Hopfield 에너지 → 퍼텐셜 변환

```python
# 현재 디렉토리에서 직접 import
from well_formation_integration import create_potential_from_wells

# WellFormationEngine 결과 (W, b)
well_result = well_engine.generate_well(episodes)

# 퍼텐셜 함수로 변환
potential_func = create_potential_from_wells(well_result)

# PotentialFieldEngine 생성
field_engine = PotentialFieldEngine(potential_func=potential_func)
```

---

## 📊 필드 합성

### 여러 퍼텐셜 합성

```python
# 현재 디렉토리에서 직접 import
from gravity_field import create_composite_potential

# 여러 퍼텐셜 합성
composite_potential = create_composite_potential(
    gravity_func=gravity_potential,
    well_funcs=[well_potential_1, well_potential_2],
    custom_funcs=[custom_potential],
)

# PotentialFieldEngine 생성
field_engine = PotentialFieldEngine(potential_func=composite_potential)
```

---

## 📚 개념 및 논문 출처

### 은유 → 실제 코드 매핑

- **태양계 은유**: 중력 퍼텐셜 `V_gravity(x) = -G * M / ||x - x_center||`
- **우물 은유**: Hopfield 에너지 `E(x) = -(1/2) * Σ_ij w_ij x_i x_j - Σ_i b_i x_i`
- **난류 은유**: 발산/회전 계산 (필드 분석)

### 주요 출처

- **퍼텐셜 필드**: Classical mechanics (Lagrangian/Hamiltonian formalism)
- **중력**: Newton (1687), Poisson (1813)
- **발산/회전**: Gauss (1813), Stokes (1854)
- **난류**: Navier-Stokes equations, Chaos theory

자세한 내용은 `CONCEPT_REFERENCES.md` 참조

---

## 📁 파일 구조

```
PotentialField_Engine/
├── README.md                        # 이 파일 (메인 문서)
├── __init__.py                      # 모듈 초기화
├── CONFIG.py                        # 설정 (모든 상수 정의)
├── potential_field_engine.py        # 핵심 엔진
├── gravity_field.py                # 중력장 구현
├── grid_analyzer.py                # 그리드 분석 및 시각화
├── well_formation_integration.py   # WellFormationEngine 연계
├── docs/                            # 문서 폴더
│   ├── CONCEPT.md                   # 개념 정리
│   ├── CONCEPT_REFERENCES.md        # 개념 및 논문 출처
│   ├── IMPLEMENTATION_SUMMARY.md    # 구현 요약
│   ├── PHAM_SIGNATURE.md            # PHAM 블록체인 서명 정보
│   ├── BUGFIX_SUMMARY.md            # 버그 수정 요약
│   ├── COMPLIANCE_REPORT.md         # 규약 준수 보고서
│   └── ... (기타 문서)
└── examples/                        # 예제 및 데모
    ├── test_demo.py                 # 기본 테스트 및 데모
    └── demo_analytical_field.py     # 해석적 필드 궤도 운동 데모
```

**총 코드 라인 수**: 약 1,325줄 (Python)

---

## ✅ 설계 원칙

### 1. 불변성 유지

- state를 직접 수정하지 않음
- `new_state = state.copy()` 후 업데이트
- `new_state` 반환

### 2. 하드코딩 제거

- 모든 상수를 파라미터로 받음
- CONFIG 기반

### 3. BrainCore 철학 유지

- GlobalState 하나 (단일 상태 중심)
- 엔진은 `update(state)` → `new_state` 반환
- extensions에 필드 정보 저장

---

## 🔍 필드 분석 예시

### 발산 분석: 소스/싱크 및 라플라시안 구조

**소스 영역 (∇·g > 0)**: 플럭스가 외부로 나가는 영역입니다. 순수 퍼텐셜 필드의 경우 Poisson 방정식 ∇²V = -∇·g로 연결됩니다.

**싱크 영역 (∇·g < 0)**: 플럭스가 내부로 흡수되는 영역입니다.

**소스/싱크 없음 (∇·g = 0)**: locally solenoidal 영역으로, 발산이 0인 영역입니다.

### 회전 분석: 비보존 성분 탐지

**비보존 성분 (∇×g ≠ 0)**: 순수 퍼텐셜 필드(g = -∇V)는 이론상 curl = 0이므로, curl ≠ 0이면 비퍼텐셜 성분(예: 마그네틱 필드, 난류) 탐지 가능합니다.

**순수 퍼텐셜 필드 (∇×g = 0)**: 보존력 영역으로, 수치 오차만 남습니다.

---

## 📝 표준 API

### Extensions 저장 규약

```python
state.set_extension("potential_field", {
    "potential": V,
    "field": g,
    "acceleration": a,
})
```

### 엔진 호출 메서드

```python
def update(state: GlobalState) -> GlobalState:  # 필수
def get_energy(state: GlobalState) -> float:    # 선택
def get_state() -> Dict[str, Any]:              # 선택
def reset():                                     # 선택
```

---

**작성자**: GNJz (Qquarts)  
**버전**: 0.1.0  
**상태**: 독립 모듈로 이동 완료 ✅
