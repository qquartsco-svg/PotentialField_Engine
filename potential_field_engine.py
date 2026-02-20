"""Potential Field Engine

퍼텐셜 필드 엔진: 퍼텐셜 필드를 계산하고 상태를 업데이트합니다.

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

import numpy as np
from typing import Callable, Dict, Any, Optional
import logging

# CONFIG: 모든 하드코딩된 상수는 여기서만 정의
from .CONFIG import EPSILON, DT, DEFAULT_ENABLE_LOGGING

# 독립 모듈: BrainCore의 GlobalState와 SelfOrganizingEngine을 import
# BrainCore가 설치되어 있어야 함
try:
    from brain_core.global_state import GlobalState
    from brain_core.engine_wrappers import SelfOrganizingEngine
except ImportError:
    # 독립 실행을 위한 대체 (선택적)
    try:
        import sys
        from pathlib import Path
        brain_core_path = Path(__file__).parent.parent.parent.parent / "BrainCore" / "src"
        sys.path.insert(0, str(brain_core_path))
        from brain_core.global_state import GlobalState
        from brain_core.engine_wrappers import SelfOrganizingEngine
    except ImportError:
        raise ImportError(
            "BrainCore가 필요합니다. "
            "BrainCore를 설치하거나 PYTHONPATH에 추가하세요."
        )


class PotentialFieldEngine(SelfOrganizingEngine):
    """퍼텐셜 필드 엔진
    
    역할: 퍼텐셜 필드 계산 및 상태 업데이트
    
    수학적 배경:
    - 퍼텐셜: V(x)
    - 필드(기울기): g(x) = -∇V(x)
    - 가속도: a = g(x)
    - 속도 업데이트: v_{t+1} = v_t + dt * a
    - 위치 업데이트: x_{t+1} = x_t + dt * v_{t+1}
    - 에너지: E = (1/2) * v^2 + V(x)
    
    설계 원칙:
    - 불변성 유지: state를 직접 수정하지 않고 copy-and-return
    - 하드코딩 제거: 모든 상수를 파라미터로 받음
    - BrainCore 철학: GlobalState 하나, extensions 활용
    """
    
    def __init__(
        self,
        potential_func: Callable[[np.ndarray], float],
        dt: float = None,
        epsilon: float = None,
        enable_logging: bool = None,
    ):
        """PotentialFieldEngine 초기화
        
        설계 원칙:
        - 하드코딩 금지: 모든 기본값은 CONFIG에서 가져옴
        - 외부 제어 가능: 파라미터로 오버라이드 가능
        
        Args:
            potential_func: 퍼텐셜 함수 V(x) -> float
            dt: 시간 스텝 (None이면 CONFIG.DT 사용)
            epsilon: 수치 기울기 계산용 작은 값 (None이면 CONFIG.EPSILON 사용)
            enable_logging: 로깅 활성화 여부 (None이면 CONFIG.DEFAULT_ENABLE_LOGGING 사용)
        """
        self.potential_func = potential_func
        # CONFIG에서 기본값 가져오기 (하드코딩 금지)
        self.dt = dt if dt is not None else DT
        self.epsilon = epsilon if epsilon is not None else EPSILON
        self.enable_logging = enable_logging if enable_logging is not None else DEFAULT_ENABLE_LOGGING
        
        if enable_logging:
            self.logger = logging.getLogger("PotentialFieldEngine")
        else:
            self.logger = None
    
    def update(self, state: GlobalState) -> GlobalState:
        """필드 계산 및 상태 업데이트
        
        핵심 원칙:
        - state를 직접 수정하지 않음
        - new_state = state.copy() 후 업데이트
        - new_state 반환
        
        수식:
        - 퍼텐셜 계산: V = potential_func(x)
        - 필드 계산: g = -∇V(x)
        - 가속도: a = g
        - 속도 업데이트: v_{t+1} = v_t + dt * a
        - 위치 업데이트: x_{t+1} = x_t + dt * v_{t+1}
        - 에너지: E = (1/2) * v^2 + V(x)
        
        Args:
            state: 현재 상태
            
        Returns:
            업데이트된 상태 (새로운 GlobalState 인스턴스)
        """
        # 상태 복사 (불변성 유지)
        new_state = state.copy(deep=False)
        
        # state_vector를 위치(x)와 속도(v)로 분리
        # 가정: state_vector = [x1, x2, ..., xN, v1, v2, ..., vN]
        dim = len(new_state.state_vector) // 2
        
        if dim == 0:
            # 속도가 없는 경우 (위치만 있는 경우)
            x = new_state.state_vector
            v = np.zeros_like(x)
        else:
            x = new_state.state_vector[:dim]  # 위치
            v = new_state.state_vector[dim:]   # 속도
        
        # 퍼텐셜 계산
        V = self.potential_func(x)
        
        # 필드 계산 (기울기)
        g = self._compute_field(x)
        
        # 가속도
        a = g
        
        # 속도 업데이트
        # 수식: v_{t+1} = v_t + dt * a
        v_new = v + self.dt * a
        
        # 위치 업데이트
        # 수식: x_{t+1} = x_t + dt * v_{t+1}
        x_new = x + self.dt * v_new
        
        # 상태 벡터 업데이트
        if dim == 0:
            # 속도가 없었던 경우, 속도 추가
            new_state.state_vector = np.concatenate([x_new, v_new])
        else:
            new_state.state_vector = np.concatenate([x_new, v_new])
        
        # 에너지 계산 (운동 에너지 + 퍼텐셜 에너지)
        # 수식: E = (1/2) * v^2 + V(x)
        kinetic_energy = 0.5 * np.dot(v_new, v_new)
        new_state.energy = kinetic_energy + V
        
        # 필드 정보 저장 (extensions)
        new_state.set_extension("potential_field", {
            "potential": float(V),
            "field": g.tolist() if isinstance(g, np.ndarray) else g,
            "acceleration": a.tolist() if isinstance(a, np.ndarray) else a,
            "kinetic_energy": float(kinetic_energy),
            "potential_energy": float(V),
            "total_energy": float(kinetic_energy + V),
        })
        
        if self.logger:
            self.logger.debug(
                f"PotentialFieldEngine update: "
                f"V={V:.6f}, E={new_state.energy:.6f}, "
                f"||g||={np.linalg.norm(g):.6f}"
            )
        
        return new_state
    
    def _compute_field(self, x: np.ndarray) -> np.ndarray:
        """필드 계산 (기울기)
        
        수식: g(x) = -∇V(x)
        
        수치적 기울기 계산:
        g_i = (V(x + ε·e_i) - V(x - ε·e_i)) / (2ε)
        
        Args:
            x: 위치 벡터
            
        Returns:
            필드 벡터 (기울기)
        """
        grad = np.zeros_like(x)
        for i in range(len(x)):
            x_plus = x.copy()
            x_plus[i] += self.epsilon
            x_minus = x.copy()
            x_minus[i] -= self.epsilon
            grad[i] = (self.potential_func(x_plus) - self.potential_func(x_minus)) / (2 * self.epsilon)
        return -grad  # g = -∇V
    
    def get_energy(self, state: GlobalState) -> float:
        """상태의 에너지 반환
        
        Args:
            state: 상태
            
        Returns:
            에너지
        """
        return state.energy
    
    def get_state(self) -> Dict[str, Any]:
        """엔진 내부 상태 반환"""
        return {
            "name": "potential_field",
            "dt": self.dt,
            "epsilon": self.epsilon,
        }
    
    def reset(self):
        """상태 리셋"""
        pass

