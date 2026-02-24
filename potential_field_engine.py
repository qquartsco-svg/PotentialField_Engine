"""Potential Field Engine

퍼텐셜 필드 엔진: 퍼텐셜 필드를 계산하고 상태를 업데이트합니다.

수식 (일반):
  ẍ = -∇V(x) + ωJv - γv + I(x,v,t) + σξ(t)

  각 항의 역할:
    -∇V(x)   : 퍼텐셜 gradient (보존력)
    ωJv       : 코리올리 회전 (에너지 보존, 방향만 변경)
    -γv       : 감쇠 (에너지 소산, γ>0 → 망각/피로)
    I(x,v,t)  : 외부 주입 (에너지 공급, 자극/각성)
    σξ(t)     : 확률적 요동 (Langevin noise, 비결정론적 전이)

  에너지 밸런스 (결정론 부분):
    E = ½||v||² + V(x)
    dE/dt = -γ||v||² + v·I(x,v,t)  (+ 노이즈로 인한 확률적 기여)
    γ=0, I=0, σ=0 → 에너지 보존

적분 방식:

1) omega_coriolis 설정 시 — Modified Strang splitting:
    O(dt/2) → S(dt/2) → K(dt/2) → R(dt) → K(dt/2) → S(dt/2) → O(dt/2)

    여기서:
      O: O-U exact 반스텝 (감쇠 + 노이즈 결합)
         v = e^{-γh} v + σ√((1-e^{-2γh})/(2γ)) · ξ,  h=dt/2
         γ→0 limit: v = v + σ√h · ξ
      S: 드리프트 x += (dt/2)·v
      K: 킥 v += (dt/2)·(g(x) + I)
      R: 정확 회전 v = R(ωdt)·v  — |v| 보존

    γ=0, σ=0, I=0이면 기존 Strang splitting과 동일 (하위 호환).
    대칭 분할 → 결정론 부분 2차 정확도 유지.

2) omega_coriolis 미설정 — semi-implicit Euler + O-U exact noise:
    a = -∇V(x) + rotational(x,v) + I(x,v,t)
    v_new = e^{-γdt}(v + dt·a) + amp(dt)·ξ
    x_new = x + dt·v_new
    amp(dt) = σ√((1-e^{-2γdt})/(2γ)),  γ→0: σ√dt

Extensions 저장 규약:
- state.set_extension("potential_field", {...}): 필드/에너지/감쇠/주입/노이즈 정보
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
        gamma: float = 0.0,
        injection_func: Optional[Callable] = None,
        noise_sigma: float = 0.0,
        noise_seed: Optional[int] = None,
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
            gamma: 감쇠 계수 γ ≥ 0. 운동 방정식에 -γv 항 추가.
                   γ=0이면 감쇠 없음 (기존 동작). γ>0이면 에너지 소산.
                   정확해 exp(-γt) 적용 (수치적으로 무조건 안정).
            injection_func: 외부 입력 I(x, v, t) -> np.ndarray.
                   상태 공간과 같은 차원의 힘 벡터 반환.
                   None이면 외부 입력 없음.
            noise_sigma: 요동 세기 σ ≥ 0. σξ(t) 항 추가 (Langevin noise).
                   σ=0이면 결정론적 (기존 동작). σ>0이면 확률적 전이 가능.
                   Wiener increment: σ·√dt·N(0,1) 스케일링.
            noise_seed: 난수 시드. None이면 비결정적 (매 실행 다름).
                   정수 설정 시 재현 가능한 결과.
            dt: 시간 스텝
            epsilon: 수치 기울기용 ε
            enable_logging: 로깅
        """
        self.potential_func = potential_func
        self.field_func = field_func
        self.rotational_func = rotational_func
        self.omega_coriolis = omega_coriolis
        self.rotation_axis = rotation_axis
        self.gamma = float(gamma)
        self.injection_func = injection_func
        self.noise_sigma = float(noise_sigma)
        self._rng = np.random.default_rng(noise_seed)
        self.dt = dt if dt is not None else DT
        self.epsilon = epsilon if epsilon is not None else EPSILON
        self.enable_logging = enable_logging if enable_logging is not None else DEFAULT_ENABLE_LOGGING
        self._time = 0.0

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

        self._time += self.dt

        V_new = self.potential_func(x_new)
        K_new = 0.5 * np.dot(v_new, v_new)

        new_state.state_vector = np.concatenate([x_new, v_new])
        new_state.energy = K_new + V_new

        # 에너지 밸런스: dE/dt = -γ||v||² + v·I
        dissipation_power = -self.gamma * np.dot(v_new, v_new)
        injection_power = 0.0
        if self.injection_func is not None:
            I_vec = np.asarray(
                self.injection_func(x_new, v_new, self._time)
            )
            injection_power = float(np.dot(v_new, I_vec))

        g_new = self._compute_gradient(x_new)
        new_state.set_extension("potential_field", {
            "potential": float(V_new),
            "field": g_new.tolist() if isinstance(g_new, np.ndarray) else g_new,
            "kinetic_energy": float(K_new),
            "potential_energy": float(V_new),
            "total_energy": float(K_new + V_new),
            "time": float(self._time),
            "gamma": float(self.gamma),
            "noise_sigma": float(self.noise_sigma),
            "dissipation_power": float(dissipation_power),
            "injection_power": float(injection_power),
        })

        if self.logger:
            self.logger.debug(
                f"PotentialFieldEngine: V={V_new:.6f}, E={K_new + V_new:.6f}, "
                f"γ={self.gamma}, P_diss={dissipation_power:.6f}"
            )

        return new_state

    # ------------------------------------------------------------------ #
    #  적분기
    # ------------------------------------------------------------------ #
    def _symplectic_euler_step(self, x, v):
        """Semi-implicit Euler + O-U exact noise

        a = -∇V(x) + rotational(x,v) + I(x,v,t)
        v_tmp = v + dt·a
        v_new = e^{-γdt} v_tmp + amp(dt)·ξ
        x_new = x + dt·v_new

        amp(dt) = σ √((1 - e^{-2γdt}) / (2γ)),  γ→0: σ√dt
        """
        a = self._compute_acceleration(x, v)
        if self.injection_func is not None:
            I_vec = np.asarray(
                self.injection_func(x, v, self._time)
            )
            a = a + I_vec
        v_new = v + self.dt * a
        decay = np.exp(-self.gamma * self.dt) if self.gamma > 0 else 1.0
        v_new = v_new * decay
        noise_amp = self._ou_noise_amplitude(self.dt)
        if noise_amp > 0:
            v_new = v_new + noise_amp * self._rng.standard_normal(v_new.shape)
        x_new = x + self.dt * v_new
        return x_new, v_new

    def _strang_splitting_step(self, x, v):
        """Modified Strang splitting: O-S-K-R-K-S-O

        ẍ = g(x) + ωJv - γv + I(x,v,t) + σξ(t)

        순서 (대칭 분할):
            1) half O-U exact:   v = e^{-γdt/2} v + amp(dt/2)·ξ₁
            2) half drift:       x_half = x + (dt/2)v
            3) force at midpoint: F = g(x_half) + I(x_half, v, t_mid)
            4) half kick:        v⁻ = v + (dt/2)·F
            5) exact rotation:   v_rot = R(ωdt)·v⁻    — |v| 정확 보존
            6) half kick:        v_new = v_rot + (dt/2)·F
            7) half drift:       x_new = x_half + (dt/2)·v_new
            8) half O-U exact:   v_new = e^{-γdt/2} v_new + amp(dt/2)·ξ₂

        O-U exact noise amplitude for half-step h = dt/2:
            amp(h) = σ √((1 - e^{-2γh}) / (2γ))
            γ→0 limit: amp(h) = σ √h

        γ=0, σ=0, I=None이면 기존 Strang splitting과 동일 (하위 호환).
        """
        dt = self.dt
        gamma = self.gamma

        noise_amp_half = self._ou_noise_amplitude(dt / 2.0)
        decay_half = np.exp(-gamma * dt / 2.0) if gamma > 0 else 1.0

        # (1) Half O-U exact
        v = v * decay_half
        if noise_amp_half > 0:
            v = v + noise_amp_half * self._rng.standard_normal(v.shape)

        # (2) Half drift
        x_half = x + (dt / 2.0) * v

        # (3) Force at midpoint: gradient + injection
        force = self._compute_gradient(x_half)
        if self.injection_func is not None:
            t_mid = self._time + dt / 2.0
            I_vec = np.asarray(self.injection_func(x_half, v, t_mid))
            force = force + I_vec

        # (4)-(6) Half kick → rotation → half kick
        v_minus = v + (dt / 2.0) * force
        v_rot = self._exact_rotate(v_minus, self.omega_coriolis * dt)
        v_new = v_rot + (dt / 2.0) * force

        # (7) Half drift
        x_new = x_half + (dt / 2.0) * v_new

        # (8) Half O-U exact
        v_new = v_new * decay_half
        if noise_amp_half > 0:
            v_new = v_new + noise_amp_half * self._rng.standard_normal(v_new.shape)

        return x_new, v_new

    def _ou_noise_amplitude(self, h):
        """O-U exact noise coefficient for time step h.

        dv = -γv dt + σ dW  →  v(t+h) = e^{-γh} v(t) + amp · ξ

        amp = σ √((1 - e^{-2γh}) / (2γ))
        γ→0 limit: amp = σ √h
        """
        if self.noise_sigma <= 0:
            return 0.0
        if self.gamma > 0:
            return self.noise_sigma * np.sqrt(
                (1.0 - np.exp(-2.0 * self.gamma * h)) / (2.0 * self.gamma)
            )
        return self.noise_sigma * np.sqrt(h)

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
            "gamma": self.gamma,
            "noise_sigma": self.noise_sigma,
            "has_injection": self.injection_func is not None,
            "time": self._time,
        }

    def reset(self):
        self._time = 0.0
