"""Potential Field Engine

독립 모듈: 퍼텐셜 필드 엔진

⚠️ 중요: GlobalState 규약

GlobalState.state_vector MUST be 2N dimensional:
- First N elements: position [x1, x2, ..., xN]
- Last N elements: velocity [v1, v2, ..., vN]

홀수 길이 입력 시 ValueError 발생.

은유 → 실제 코드 매핑:
- 태양계 은유 → 중력 퍼텐셜 V_gravity(x) = -G * M / ||x - x_center||
- 우물 은유 → Hopfield 에너지 E(x) = -(1/2) * Σ_ij w_ij x_i x_j - Σ_i b_i x_i
- 난류 은유 → 발산/회전 계산 (왜곡 탐지)

수식:
- 퍼텐셜: V(x)
- 필드(기울기): g(x) = -∇V(x)
- 가속도: a = g(x)
- 속도 업데이트: v_{t+1} = v_t + dt * a
- 위치 업데이트: x_{t+1} = x_t + dt * v_{t+1}
- 에너지: E = (1/2) * v^2 + V(x)

개념 및 논문 출처:
- 퍼텐셜 필드: Classical mechanics (Lagrangian/Hamiltonian formalism), Field theory
- 필드 (기울기): Vector calculus, Gradient descent theory
- 동역학: Newtonian mechanics, Classical field theory
- 에너지 보존: Hamiltonian mechanics, Conservation laws

표준 API:
- update(state: GlobalState) -> GlobalState: 상태 업데이트 (필수)
- get_energy(state: GlobalState) -> float: 에너지 반환 (선택)
- get_state() -> Dict[str, Any]: 엔진 내부 상태 반환 (선택)
- reset(): 상태 리셋 (선택)

Extensions 저장 규약:
- state.set_extension("potential_field", {...}): 필드 정보 저장
"""

from .potential_field_engine import PotentialFieldEngine
from .gravity_field import GravityField, create_gravity_potential, create_composite_potential
from .grid_analyzer import GridAnalyzer, GridVisualizer
from .well_formation_integration import create_potential_from_wells, create_field_from_wells

__version__ = "0.1.0"
__all__ = [
    "PotentialFieldEngine",
    "GravityField",
    "create_gravity_potential",
    "create_composite_potential",
    "GridAnalyzer",
    "GridVisualizer",
    "create_potential_from_wells",
    "create_field_from_wells",
]
