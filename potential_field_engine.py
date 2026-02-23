"""Potential Field Engine

퍼텐셜 필드 엔진: 퍼텐셜 필드를 계산하고 상태를 업데이트합니다.

수식:
- 퍼텐셜: V(x)
- 필드(기울기): g(x) = -∇V(x)
- 에너지: E = (1/2)||v||² + V(x)

적분 방식 (두 가지):

1) omega_coriolis 설정 시 — Strang splitting (코리올리 회전 + 에너지 정확 보존):
    a = -∇V(x) + ωJv  (코리올리형 자전)
    순서:
      half kick:      v₁ = v + (dt/2) g(x)           g = -∇V
      exact rotation: v₂ = R(ωdt) v₁                  |v| 정확 보존
      stream:         x_new = x + dt v₂
      half kick:      v_new = v₂ + (dt/2) g(x_new)

    왜 이 방식인가:
      dv/dt = ωJv 의 정확해는 v(t) = exp(ωJt)v₀ = 회전행렬 × v₀.
      이를 수치적으로 정확히 적용하면 |v| 보존 → 에너지 보존.
      Strang splitting은 2차 정확도 + symplectic.

2) omega_coriolis 미설정 — semi-implicit (symplectic) Euler:
    v_new = v + dt * a(x, v)
    x_new = x + dt * v_new

Extensions 저장 규약:
- state.set_extension("potential_field", {...}): 필드 정보 저장
"""

import numpy as np
from typing import Callable, Dict, Any, Optional
import logging

try:
    from .CONFIG import EPSILON, DT, DEFAULT_ENABLE_LOGGING
except ImportError:
    from CONFIG import EPSILON, DT, DEFAULT_ENABLE_LOGGING

try:
    from brain_core.global_state import GlobalState
    from brain_core.engine_wrappers import SelfOrganizingEngine
except ImportError:
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
    설계 원칙: 불변성 유지 (copy-and-return), 하드코딩 제거, BrainCore GlobalState 활용
    """

    def __init__(
        self,
        potential_func: Callable[[np.ndarray], float],
        field_func: Optional[Callable[[np.ndarray], np.ndarray]] = None,
        rotational_func: Optional[Callable] = None,
        omega_coriolis: Optional[float] = None,
        rotation_axis: tuple = (0, 1),
        dt: float = None,
        epsilon: float = None,
        enable_logging: bool = None,
    ):
        """
        Args:
            potential_func: V(x) -> float
            field_func: g(x) = -∇V(x) -> np.ndarray (없으면 수치 미분)
            rotational_func: 범용 회전 항 (fallback, symplectic Euler에서만 사용)
            omega_coriolis: 코리올리 각속도 ω (설정 시 Strang splitting 사용)
            rotation_axis: 회전 평면 축 인덱스 (기본 (0,1) = xy)
            dt: 시간 스텝
            epsilon: 수치 기울기용 ε
            enable_logging: 로깅
        """
        self.potential_func = potential_func
        self.field_func = field_func
        self.rotational_func = rotational_func
        self.omega_coriolis = omega_coriolis
        self.rotation_axis = rotation_axis
        self.dt = dt if dt is not None else DT
        self.epsilon = epsilon if epsilon is not None else EPSILON
        self.enable_logging = enable_logging if enable_logging is not None else DEFAULT_ENABLE_LOGGING

        if enable_logging:
            self.logger = logging.getLogger("PotentialFieldEngine")
        else:
            self.logger = None

    # ------------------------------------------------------------------ #
    #  update
    # ------------------------------------------------------------------ #
    def update(self, state: GlobalState) -> GlobalState:
        """상태 업데이트 (메인 루프에서 매 스텝 호출)"""
        new_state = state.copy(deep=False)

        n = len(new_state.state_vector)
        if n % 2 != 0:
            raise ValueError(
                f"state_vector must have even length (got {n}). "
                f"Expected format: [x1, ..., xN, v1, ..., vN]"
            )

        dim = n // 2
        x = new_state.state_vector[:dim]
        v = new_state.state_vector[dim:]

        if self.omega_coriolis is not None:
            x_new, v_new = self._strang_splitting_step(x, v)
        else:
            x_new, v_new = self._symplectic_euler_step(x, v)

        V_new = self.potential_func(x_new)
        K_new = 0.5 * np.dot(v_new, v_new)

        new_state.state_vector = np.concatenate([x_new, v_new])
        new_state.energy = K_new + V_new

        g_new = self._compute_gradient(x_new)
        new_state.set_extension("potential_field", {
            "potential": float(V_new),
            "field": g_new.tolist() if isinstance(g_new, np.ndarray) else g_new,
            "kinetic_energy": float(K_new),
            "potential_energy": float(V_new),
            "total_energy": float(K_new + V_new),
        })

        if self.logger:
            self.logger.debug(
                f"PotentialFieldEngine: V={V_new:.6f}, E={K_new + V_new:.6f}, "
                f"||g||={np.linalg.norm(g_new):.6f}"
            )

        return new_state

    # ------------------------------------------------------------------ #
    #  적분기
    # ------------------------------------------------------------------ #
    def _symplectic_euler_step(self, x, v):
        """Semi-implicit (symplectic) Euler

        v_new = v + dt * a(x, v)
        x_new = x + dt * v_new
        """
        a = self._compute_acceleration(x, v)
        v_new = v + self.dt * a
        x_new = x + self.dt * v_new
        return x_new, v_new

    def _strang_splitting_step(self, x, v):
        """Drift-Kick/Rotate-Drift (velocity Verlet + Boris rotation)

        순서:
            1) half drift:     x_half = x + (dt/2) v
            2) full kick+rot:  g = -∇V(x_half)
                               v⁻ = v + (dt/2) g
                               v_rot = R(ωdt) v⁻     (|v| 정확 보존)
                               v_new = v_rot + (dt/2) g
            3) half drift:     x_new = x_half + (dt/2) v_new

        에너지 보존:
            drift 단계는 위치만 변경 (운동에너지 불변).
            kick은 대칭 (양쪽 dt/2, 같은 위치 x_half).
            rotation은 |v| 정확 보존.
            → secular drift 없음, 2차 정확도.
        """
        dt = self.dt

        x_half = x + (dt / 2.0) * v

        g = self._compute_gradient(x_half)
        v_minus = v + (dt / 2.0) * g
        v_rot = self._exact_rotate(v_minus, self.omega_coriolis * dt)
        v_new = v_rot + (dt / 2.0) * g

        x_new = x_half + (dt / 2.0) * v_new

        return x_new, v_new

    def _exact_rotate(self, v, theta):
        """회전 평면 (i,j) 에서 v를 각도 θ 만큼 정확히 회전

        exp(θJ) v   where J[i,j]=-1, J[j,i]=1
        나머지 차원 불변. |v| 정확 보존.
        """
        v_rot = v.copy()
        i, j = self.rotation_axis
        c, s = np.cos(theta), np.sin(theta)
        vi, vj = v[i], v[j]
        v_rot[i] = c * vi - s * vj
        v_rot[j] = s * vi + c * vj
        return v_rot

    # ------------------------------------------------------------------ #
    #  필드 계산
    # ------------------------------------------------------------------ #
    def _compute_gradient(self, x):
        """순수 gradient 계산: g(x) = -∇V(x)"""
        if self.field_func is not None:
            return self.field_func(x)
        grad = np.zeros_like(x)
        for i in range(len(x)):
            x_plus = x.copy()
            x_plus[i] += self.epsilon
            x_minus = x.copy()
            x_minus[i] -= self.epsilon
            grad[i] = (self.potential_func(x_plus) - self.potential_func(x_minus)) / (2 * self.epsilon)
        return -grad

    def _compute_acceleration(self, x, v):
        """전체 가속도: gradient + 회전 항 (symplectic Euler용)"""
        g = self._compute_gradient(x)
        if self.rotational_func is not None:
            try:
                r = self.rotational_func(x, v)
            except TypeError:
                r = self.rotational_func(x)
            if len(g) != len(r):
                raise ValueError(
                    f"field and rotational dimension mismatch: {len(g)} vs {len(r)}"
                )
            g = g + r
        return g

    # ------------------------------------------------------------------ #
    #  유틸리티
    # ------------------------------------------------------------------ #
    def get_energy(self, state: GlobalState) -> float:
        return state.energy

    def get_state(self) -> Dict[str, Any]:
        return {
            "name": "potential_field",
            "dt": self.dt,
            "epsilon": self.epsilon,
            "omega_coriolis": self.omega_coriolis,
        }

    def reset(self):
        pass
