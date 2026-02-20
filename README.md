# PotentialFieldEngine

**Version**: 0.1.0  
**Status**: 소프트웨어 벤치마킹 단계 (물리적 하드웨어 테스트 미완)  
**License**: MIT License  
**Author**: GNJz (Qquarts)

---

## ⚠️ 중요 안내

**현재 상태**: 본 엔진은 소프트웨어 시뮬레이션 및 벤치마킹 단계에 있습니다.  
**테스트 환경**: 맥북에어에서 간단한 소프트웨어 테스트 후 업로드되었습니다.  
**물리적 하드웨어 테스트는 아직 완료되지 않았으며**, 실제 산업 환경에 적용하기 전에 추가 검증이 필요합니다.

본 프로젝트는 **계속 발전하는 구조**이며, 테스트 과정과 계획된 업그레이드를 통해 확장되어 갑니다.

---

## 📋 개요

**PotentialFieldEngine**은 상태공간에 퍼텐셜 필드를 펼쳐 중력장, 우물, 커스텀 필드를 구현하고 벡터장 구조를 분석하는 연구용 도구입니다.

### 핵심 기능

- ✅ **퍼텐셜 필드 계산**: 상태공간의 각 점에서 퍼텐셜 에너지 값 계산
- ✅ **중력장 구현**: 점 질량 및 여러 질량에 대한 중력 퍼텐셜 및 필드 계산
- ✅ **상태공간 그리드 분석**: 그리드 기반 벡터장 구조 분석
- ✅ **벡터장 분석**: 발산/회전 계산을 통한 소스/싱크 및 비보존 성분 탐지
- ✅ **WellFormationEngine 연계**: Hopfield 에너지를 퍼텐셜로 변환
- ✅ **필드 합성**: 여러 퍼텐셜 필드의 합성 지원

자세한 내용은 [CONCEPT.md](docs/CONCEPT.md) 참조

---

## 🎯 예상 활용 분야

**참고**: 아래는 본 엔진의 잠재적 활용 분야이며, 실제 적용을 위해서는 추가 검증이 필요합니다.

### 1. 상태 동역학 시뮬레이션 (예상)
- 퍼텐셜 기반 상태 공간 탐색 (시뮬레이션 검증)
- 에너지 지형 분석 (이론적 검증)
- 안정점 및 새들 포인트 탐지 (이론적 검증)

### 2. 벡터장 구조 분석 (예상)
- 소스/싱크 구조 탐지 (시뮬레이션 검증)
- 비보존 성분 분석 (이론적 검증)
- 플럭스 구조 시각화 (이론적 검증)

### 3. 중력장 시뮬레이션 (예상)
- 다체 문제 시뮬레이션 (시뮬레이션 검증)
- 궤도 역학 분석 (이론적 검증)
- 중력 왜곡 탐지 (이론적 검증)

### 4. 연구 및 교육 (예상)
- 벡터 해석 교육 도구 (시뮬레이션 검증)
- 퍼텐셜 필드 이론 연구 (이론적 검증)
- 수치 해석 방법론 연구 (이론적 검증)

자세한 활용 사례는 [IMPLEMENTATION_SUMMARY.md](docs/IMPLEMENTATION_SUMMARY.md) 참조

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

**참고**: 위 적분 방식은 semi-implicit (symplectic) Euler 형태이다. 일반 explicit Euler보다 에너지 보존 특성이 우수하다.

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

### 벡터장 구조 분석

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

**물리적 의미**: 순수 퍼텐셜 필드(g = -∇V)는 이론상 curl = 0입니다 (연속/매끄러운 V 가정). 수치 계산에서는 격자 간격, epsilon(기울기 계산), 경계 조건, 특이점(예: r=0 근처 softening)에 의해 잔차가 남을 수 있습니다. curl ≠ 0이면 비퍼텐셜 성분(예: 마그네틱 필드, 비보존력) 탐지 가능합니다.

자세한 수식 설명은 [CONCEPT.md](docs/CONCEPT.md) 참조

---

## 🚀 빠른 시작

### 설치

```bash
# 저장소 클론
git clone https://github.com/qquartsco-svg/PotentialField_Engine.git
cd PotentialField_Engine

# 의존성 설치
pip install numpy matplotlib
```

### BrainCore 연동 (선택적)

PotentialFieldEngine은 독립적으로 사용할 수 있으며, BrainCore와도 연동 가능합니다.

**독립 사용**:
- 모든 파일을 현재 디렉토리에 두고 직접 import하여 사용

**BrainCore 연동**:
- BrainCore가 설치되어 있어야 함
- BrainCore 경로를 PYTHONPATH에 추가하거나 BrainCore를 설치

### 기본 사용법

```python
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

자세한 사용법은 [examples/](examples/) 참조

---

## 🔍 그리드 분석

```python
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

자세한 그리드 분석 방법은 [docs/CONCEPT.md](docs/CONCEPT.md#벡터장-구조-분석) 참조

---

## 🔗 WellFormationEngine 연계

### Hopfield 에너지 → 퍼텐셜 변환

```python
from well_formation_integration import create_potential_from_wells

# WellFormationEngine 결과 (W, b)
well_result = well_engine.generate_well(episodes)

# 퍼텐셜 함수로 변환
potential_func = create_potential_from_wells(well_result)

# PotentialFieldEngine 생성
field_engine = PotentialFieldEngine(potential_func=potential_func)
```

자세한 연계 방법은 [docs/CONCEPT.md](docs/CONCEPT.md#wellformationengine-연계) 참조

---

## 📊 필드 합성

### 여러 퍼텐셜 합성

```python
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
- **벡터장 분석**: 발산/회전 계산 (벡터장 구조 분석)

### 주요 출처

- **퍼텐셜 필드**: Classical mechanics (Lagrangian/Hamiltonian formalism)
- **벡터 해석**: Arfken, G. B., Weber, H. J., & Harris, F. E. (2013). "Mathematical Methods for Physicists" (7th ed.)
- **수치 해석**: Press, W. H., et al. (2007). "Numerical Recipes" (3rd ed.)
- **Field theory**: Jackson, J. D. (1999). "Classical Electrodynamics" (3rd ed.)

자세한 내용은 [CONCEPT_REFERENCES.md](docs/CONCEPT_REFERENCES.md) 참조

---

## 🔐 PHAM 블록체인 서명

본 엔진은 **PHAM (Proof of Hash and Merit) v4** 블록체인 시스템을 통해 코드 무결성을 보장합니다.

### 서명 정보

- **Master Hash**: `82d7d2c63c9914affe68bb1dd1af364f9b3986827d3ddedb5d13592ea5e3024f`
- **버전**: v0.1.0 (물리적 정확성 개선 후)
- **서명 일시**: 2026-02-21

### 블록체인 서명의 의미

PHAM 블록체인 서명은 다음을 보장합니다:
- **코드 무결성**: 모든 파일의 해시가 블록체인에 기록되어 변경 사항 추적 가능
- **기여도 추적**: 코드 변경에 대한 객관적 기여도 평가 (4-Signal Scoring)
- **투명성**: 모든 변경 이력이 블록체인에 영구 기록

### 4-Signal Scoring

각 코드 변경은 다음 4가지 신호로 평가됩니다:
- **Byte Signal (25%)**: 바이트 레벨 변경 비율
- **Text Signal (35%)**: 텍스트 유사도
- **AST Signal (30%)**: AST 구조 변경 분석
- **Exec Signal (10%)**: 실행 결과 변화

자세한 내용은 [PHAM_SIGNATURE.md](docs/PHAM_SIGNATURE.md) 참조

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

자세한 설계 원칙은 [docs/CONCEPT.md](docs/CONCEPT.md#설계-원칙) 참조

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

자세한 API 문서는 코드 내 docstring 참조

---

## 🔍 필드 분석 예시

### 발산 분석: 소스/싱크 및 라플라시안 구조

**소스 영역 (∇·g > 0)**: 플럭스가 외부로 나가는 영역입니다. 순수 퍼텐셜 필드의 경우 Poisson 방정식 ∇²V = -∇·g로 연결됩니다.

**싱크 영역 (∇·g < 0)**: 플럭스가 내부로 흡수되는 영역입니다.

**소스/싱크 없음 (∇·g = 0)**: locally solenoidal 영역으로, 발산이 0인 영역입니다.

### 회전 분석: 비보존 성분 탐지

**비보존 성분 (∇×g ≠ 0)**: 순수 퍼텐셜 필드(g = -∇V)는 이론상 curl = 0입니다 (연속/매끄러운 V 가정). 수치 계산에서는 격자 간격, epsilon, 경계 조건, 특이점에 의해 잔차가 남을 수 있습니다. curl ≠ 0이면 비퍼텐셜 성분(예: 마그네틱 필드, 비보존력) 탐지 가능합니다.

**순수 퍼텐셜 필드 (∇×g = 0)**: 보존력 영역으로, 수치 오차만 남습니다.

자세한 분석 예시는 [docs/CONCEPT.md](docs/CONCEPT.md#벡터장-구조-분석) 참조

---

## 📄 라이선스

MIT License

---

## 👤 작성자

GNJz (Qquarts)

---

## 🔗 관련 링크

- **GitHub 저장소**: https://github.com/qquartsco-svg/PotentialField_Engine
- **개념 문서**: [docs/CONCEPT.md](docs/CONCEPT.md)
- **논문 출처**: [docs/CONCEPT_REFERENCES.md](docs/CONCEPT_REFERENCES.md)
- **블록체인 서명**: [docs/PHAM_SIGNATURE.md](docs/PHAM_SIGNATURE.md)
- **구현 요약**: [docs/IMPLEMENTATION_SUMMARY.md](docs/IMPLEMENTATION_SUMMARY.md)

---

**버전**: 0.1.0  
**최종 업데이트**: 2026-02-21 (물리적 정확성 개선 후)
