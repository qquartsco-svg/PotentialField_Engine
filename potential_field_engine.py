"""Potential Field Engine — Trunk

줄기(trunk): 레이어를 받아서 적분하는 물리 엔진.

수식 (일반):
  m ẍ = Σ F_i(x,v,t) + G(v,dt) - γv + σξ(t)

  여기서:
    F_i    : Force Layers (보존력, 비보존력, 상호작용 등)
    G(v,dt): Gauge Layer  (코리올리, 게이지 회전 등 — |v| 보존)
    -γv    : Thermo Layer (소산)
    σξ(t)  : Thermo Layer (요동)

  줄기가 고정하는 것 (물리의 뼈대):
    1. 상태공간: (x, v, t) — 확장 가능한 벡터
    2. 업데이트: 힘 → 가속도 → 속도/위치 (Newton 구조)
    3. 보존/소산/요동 분리 (Strang splitting)
    4. 극한 일관성:
       - σ→0 → 결정론계
       - γ→0 → 보존/준보존 극한
       - (I=0, FDT) → Boltzmann 정상 분포
       - N→∞ → 동일 인터페이스

  줄기가 고정하지 않는 것 (레이어에서 교체):
    - 특정 퍼텐셜 V
    - 특정 차원
    - 특정 노이즈 형태
    - 특정 상호작용
    - 특정 인지 해석

적분 방식:

  Strang splitting (gauge 있을 때):
    O(dt/2) → S(dt/2) → K(dt/2) → R(dt) → K(dt/2) → S(dt/2) → O(dt/2)

    O: Thermo Layer — O-U exact 반스텝
    S: drift — x += (dt/2)·v
    K: kick  — v += (dt/2)·Σ F_i(x,v,t)
    R: Gauge Layer — 정확 회전

  Semi-implicit Euler (gauge 없을 때, 하위 호환):
    a = Σ F_i(x,v,t)
    v_new = Thermo(v + dt·a, dt)
    x_new = x + dt·v_new

하위 호환:
  기존 API (potential_func, omega_coriolis, gamma 등) 100% 유지.
  내부에서 자동으로 레이어 객체로 변환.

Extensions 저장 규약:
  state.set_extension("potential_field", {...})
"""

import numpy as np
from typing import Callable, Dict, Any, Optional, List
import logging

try:
    from .CONFIG import EPSILON, DT, DEFAULT_ENABLE_LOGGING
except ImportError:
    from CONFIG import EPSILON, DT, DEFAULT_ENABLE_LOGGING

try:
    from .layers import (
        GradientForce, InjectionForce, CallbackForce,
        CoriolisGauge, NullGauge,
        LangevinThermo, NullThermo,
        TrunkChecker,
    )
except ImportError:
    from layers import (
        GradientForce, InjectionForce, CallbackForce,
        CoriolisGauge, NullGauge,
        LangevinThermo, NullThermo,
        TrunkChecker,
    )

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
    """줄기(trunk) 엔진 — 레이어를 받아서 적분한다.

    두 가지 API:

    1) Classic API (하위 호환):
        eng = PotentialFieldEngine(
            potential_func=V, field_func=g,
            omega_coriolis=0.3, gamma=0.5,
            temperature=1.0, mass=1.0,
            noise_seed=42, dt=0.01,
        )

    2) Layer API (확장용):
        eng = PotentialFieldEngine(
            force_layers=[GradientForce(V, g), InjectionForce(I_func)],
            gauge_layer=CoriolisGauge(omega=0.3),
            thermo_layer=LangevinThermo(gamma=0.5, temperature=1.0),
            noise_seed=42, dt=0.01,
        )

    내부에서는 모두 레이어 객체로 통합 처리된다.
    """

    def __init__(
        self,
        # --- Classic API (하위 호환) ---
        potential_func: Optional[Callable[[np.ndarray], float]] = None,
        field_func: Optional[Callable[[np.ndarray], np.ndarray]] = None,
        rotational_func: Optional[Callable] = None,
        omega_coriolis: Optional[float] = None,
        rotation_axis: tuple = (0, 1),
        gamma: float = 0.0,
        injection_func: Optional[Callable] = None,
        noise_sigma: float = 0.0,
        temperature: Optional[float] = None,
        mass: float = 1.0,
        # --- Layer API (확장용) ---
        force_layers: Optional[List] = None,
        gauge_layer=None,
        thermo_layer=None,
        # --- Common ---
        noise_seed: Optional[int] = None,
        dt: float = None,
        epsilon: float = None,
        enable_logging: bool = None,
    ):
        self.dt = dt if dt is not None else DT
        self.epsilon = epsilon if epsilon is not None else EPSILON
        self.enable_logging = enable_logging if enable_logging is not None else DEFAULT_ENABLE_LOGGING
        self._rng = np.random.default_rng(noise_seed)
        self._time = 0.0

        # ----- Build layers ----- #
        self._build_layers(
            potential_func=potential_func,
            field_func=field_func,
            rotational_func=rotational_func,
            omega_coriolis=omega_coriolis,
            rotation_axis=rotation_axis,
            gamma=gamma,
            injection_func=injection_func,
            noise_sigma=noise_sigma,
            temperature=temperature,
            mass=mass,
            force_layers=force_layers,
            gauge_layer=gauge_layer,
            thermo_layer=thermo_layer,
        )

        # ----- Classic API 호환 속성 ----- #
        self.potential_func = potential_func
        self.field_func = field_func
        self.rotational_func = rotational_func
        self.omega_coriolis = omega_coriolis
        self.rotation_axis = rotation_axis
        self.injection_func = injection_func
        self._noise_sigma_override = float(noise_sigma)

        # ----- Logger ----- #
        if self.enable_logging:
            self.logger = logging.getLogger("PotentialFieldEngine")
        else:
            self.logger = None

    def _build_layers(self, *, potential_func, field_func, rotational_func,
                      omega_coriolis, rotation_axis, gamma, injection_func,
                      noise_sigma, temperature, mass,
                      force_layers, gauge_layer, thermo_layer):
        """Classic params → Layer objects 변환.

        Layer API가 주어지면 그것을 우선 사용.
        Classic API만 주어지면 자동 변환.
        """
        # Force layers
        if force_layers is not None:
            self._force_layers = list(force_layers)
        else:
            self._force_layers = []
            if potential_func is not None:
                self._force_layers.append(
                    GradientForce(potential_func, field_func, self.epsilon)
                )
            if injection_func is not None:
                self._force_layers.append(InjectionForce(injection_func))
            if rotational_func is not None and omega_coriolis is None:
                self._force_layers.append(CallbackForce(rotational_func))

        # Gauge layer
        if gauge_layer is not None:
            self._gauge = gauge_layer
        elif omega_coriolis is not None:
            self._gauge = CoriolisGauge(omega_coriolis, rotation_axis)
        else:
            self._gauge = NullGauge()

        # Thermo layer
        if thermo_layer is not None:
            self._thermo = thermo_layer
        else:
            self._thermo = LangevinThermo(
                gamma=gamma,
                temperature=temperature,
                mass=mass,
                noise_sigma_override=noise_sigma,
            )

        self._use_strang = not isinstance(self._gauge, NullGauge)

    # ------------------------------------------------------------------ #
    #  하위 호환 Properties
    # ------------------------------------------------------------------ #
    @property
    def gamma(self) -> float:
        return self._thermo.gamma

    @property
    def noise_sigma(self) -> float:
        return self._thermo.sigma

    @property
    def noise_mode(self) -> str:
        return self._thermo.noise_mode

    @property
    def temperature(self) -> Optional[float]:
        return self._thermo.temperature

    @property
    def mass(self) -> float:
        return self._thermo.mass

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

        if self._use_strang:
            x_new, v_new = self._strang_step(x, v)
        else:
            x_new, v_new = self._euler_step(x, v)

        self._time += self.dt

        V_new = self._total_potential(x_new)
        K_new = 0.5 * self.mass * np.dot(v_new, v_new)

        new_state.state_vector = np.concatenate([x_new, v_new])
        new_state.energy = K_new + V_new

        dissipation_power = -self.gamma * np.dot(v_new, v_new)
        injection_power = self._injection_power(x_new, v_new)

        g_new = self._total_force(x_new, v_new, self._time)
        new_state.set_extension("potential_field", {
            "potential": float(V_new),
            "field": g_new.tolist() if isinstance(g_new, np.ndarray) else g_new,
            "kinetic_energy": float(K_new),
            "potential_energy": float(V_new),
            "total_energy": float(K_new + V_new),
            "time": float(self._time),
            "gamma": float(self.gamma),
            "noise_sigma": float(self.noise_sigma),
            "noise_mode": self.noise_mode,
            "temperature": self.temperature,
            "mass": self.mass,
            "dissipation_power": float(dissipation_power),
            "injection_power": float(injection_power),
            "n_force_layers": len(self._force_layers),
            "gauge_type": type(self._gauge).__name__,
            "thermo_type": type(self._thermo).__name__,
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
    def _strang_step(self, x, v):
        """Modified Strang splitting: O-S-K-R-K-S-O

        O: Thermo Layer (O-U exact 반스텝)
        S: drift        (x += h·v)
        K: kick         (v += h·Σ F_i)
        R: Gauge Layer  (정확 회전)
        """
        dt = self.dt
        h = dt / 2.0

        # (1) Half O-U: thermo
        v = self._thermo.ou_step(v, h, self._rng)

        # (2) Half drift
        x_half = x + h * v

        # (3) Force at midpoint
        t_mid = self._time + h
        force = self._total_force(x_half, v, t_mid)

        # (4)-(6) Half kick → Gauge rotation → Half kick
        v_minus = v + h * force
        v_rot = self._gauge.rotate(v_minus, dt)
        v_new = v_rot + h * force

        # (7) Half drift
        x_new = x_half + h * v_new

        # (8) Half O-U: thermo
        v_new = self._thermo.ou_step(v_new, h, self._rng)

        return x_new, v_new

    def _euler_step(self, x, v):
        """Semi-implicit Euler + O-U (하위 호환 fallback)

        a = Σ F_i(x, v, t)
        v_new = Thermo(v + dt·a, dt)
        x_new = x + dt·v_new
        """
        dt = self.dt
        a = self._total_force(x, v, self._time)

        v_tmp = v + dt * a

        decay = np.exp(-self.gamma * dt) if self.gamma > 0 else 1.0
        v_new = v_tmp * decay

        sigma = self.noise_sigma
        if sigma > 0:
            if self.gamma > 0:
                amp = sigma * np.sqrt((1.0 - np.exp(-2.0 * self.gamma * dt)) / (2.0 * self.gamma))
            else:
                amp = sigma * np.sqrt(dt)
            v_new = v_new + amp * self._rng.standard_normal(v_new.shape)

        x_new = x + dt * v_new
        return x_new, v_new

    # ------------------------------------------------------------------ #
    #  힘 합산
    # ------------------------------------------------------------------ #
    def _total_force(self, x: np.ndarray, v: np.ndarray, t: float) -> np.ndarray:
        """모든 Force Layer의 힘을 합산."""
        f = np.zeros_like(x)
        for layer in self._force_layers:
            f = f + layer.force(x, v, t)
        return f

    def _total_potential(self, x: np.ndarray) -> float:
        """모든 Force Layer의 퍼텐셜을 합산."""
        V = 0.0
        for layer in self._force_layers:
            V += layer.potential(x)
        return V

    def _injection_power(self, x: np.ndarray, v: np.ndarray) -> float:
        """주입 파워: Σ v·I_i (InjectionForce만)"""
        power = 0.0
        for layer in self._force_layers:
            if isinstance(layer, InjectionForce):
                I_vec = layer.force(x, v, self._time)
                power += float(np.dot(v, I_vec))
        return power

    # ------------------------------------------------------------------ #
    #  극한 일관성 체크
    # ------------------------------------------------------------------ #
    def check_limits(self, state: GlobalState = None) -> list:
        """극한 일관성 체크 실행.

        state 없으면 정적 체크만 (skew, fdt).
        state 있으면 차원 + 보존계 체크도 포함.
        """
        return TrunkChecker.run_all(self, state)

    # ------------------------------------------------------------------ #
    #  유틸리티 (하위 호환)
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
            "noise_mode": self.noise_mode,
            "temperature": self.temperature,
            "mass": self.mass,
            "has_injection": self.injection_func is not None,
            "time": self._time,
            "n_force_layers": len(self._force_layers),
            "gauge_type": type(self._gauge).__name__,
            "thermo_type": type(self._thermo).__name__,
        }

    def reset(self):
        self._time = 0.0
