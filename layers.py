"""Trunk Layer Protocols — 힘/게이지/열역학 레이어

줄기(trunk)가 받아서 적분하는 세 종류의 레이어.
각 레이어는 duck typing으로 동작한다 (상속 불필요).

┌─ Force Layers ────── 힘 항을 추가/교체
│   force(x, v, t) → ndarray
│   potential(x)   → float
│
├─ Gauge Layer ─────── 운동의 공간 규칙
│   rotate(v, dt)  → ndarray  (|v| 보존)
│   check_skew()   → bool     (J^T = -J?)
│
├─ Thermo Layer ────── 소산 + 요동 규칙
│   ou_step(v, h, rng) → ndarray
│   gamma, sigma, temperature, mass
│   check_fdt()    → bool     (σ² = 2γT/m?)
│
└─ TrunkChecker ────── 극한 일관성 자동 검증
    check_conservation, check_skew, check_fdt, check_dimensions
"""

from __future__ import annotations
import numpy as np
from typing import Callable, Optional


# ================================================================== #
#  Force Layers
# ================================================================== #

class GradientForce:
    """보존력: -∇V(x)

    V(x) → -∇V(x) 를 힘으로 반환.
    field_func 가 없으면 수치 중심 차분으로 계산.
    """

    def __init__(
        self,
        potential_func: Callable[[np.ndarray], float],
        field_func: Optional[Callable[[np.ndarray], np.ndarray]] = None,
        epsilon: float = 1e-6,
    ):
        self.potential_func = potential_func
        self.field_func = field_func
        self.epsilon = epsilon

    def force(self, x: np.ndarray, v: np.ndarray, t: float) -> np.ndarray:
        if self.field_func is not None:
            return self.field_func(x)
        grad = np.zeros_like(x)
        for i in range(len(x)):
            x_p = x.copy(); x_p[i] += self.epsilon
            x_m = x.copy(); x_m[i] -= self.epsilon
            grad[i] = (self.potential_func(x_p) - self.potential_func(x_m)) / (2.0 * self.epsilon)
        return -grad

    def potential(self, x: np.ndarray) -> float:
        return self.potential_func(x)


class InjectionForce:
    """비보존 외부 힘: I(x, v, t)

    에너지를 공급하거나 빼는 외부 구동.
    potential() = 0 (비보존이므로 퍼텐셜 없음).
    """

    def __init__(self, injection_func: Callable):
        self.injection_func = injection_func

    def force(self, x: np.ndarray, v: np.ndarray, t: float) -> np.ndarray:
        return np.asarray(self.injection_func(x, v, t))

    def potential(self, x: np.ndarray) -> float:
        return 0.0


class CallbackForce:
    """범용 콜백 힘 (legacy rotational_func 호환)

    f(x, v) 또는 f(x) 형태의 콜백을 힘으로 감싼다.
    symplectic Euler 경로에서만 사용.
    """

    def __init__(self, callback: Callable):
        self._callback = callback

    def force(self, x: np.ndarray, v: np.ndarray, t: float) -> np.ndarray:
        try:
            return np.asarray(self._callback(x, v))
        except TypeError:
            return np.asarray(self._callback(x))

    def potential(self, x: np.ndarray) -> float:
        return 0.0


# ================================================================== #
#  Gauge Layer
# ================================================================== #

class CoriolisGauge:
    """코리올리 회전: exp(ωJdt)·v

    2D 평면 (axis[0], axis[1])에서 정확 회전.
    J = [[0, -1], [1, 0]] → J^T = -J → 에너지 보존 수학적 보장.
    나머지 차원은 불변.
    """

    def __init__(self, omega: float, axis: tuple = (0, 1)):
        self.omega = omega
        self.axis = axis

    def rotate(self, v: np.ndarray, dt: float) -> np.ndarray:
        theta = self.omega * dt
        v_rot = v.copy()
        i, j = self.axis
        c, s = np.cos(theta), np.sin(theta)
        vi, vj = v[i], v[j]
        v_rot[i] = c * vi - s * vj
        v_rot[j] = s * vi + c * vj
        return v_rot

    def check_skew(self) -> bool:
        """J^T = -J 인가? CoriolisGauge는 구조적으로 항상 True."""
        return True


class NullGauge:
    """회전 없음. Strang splitting의 R 스텝이 no-op."""

    def rotate(self, v: np.ndarray, dt: float) -> np.ndarray:
        return v

    def check_skew(self) -> bool:
        return True


# ================================================================== #
#  Thermo Layer
# ================================================================== #

class LangevinThermo:
    """Langevin 소산 + 요동: O-U exact step

    v → e^{-γh} v + amp(h)·ξ

    amp(h) = σ √((1 - e^{-2γh}) / (2γ)),  γ→0: σ√h

    FDT: σ² = 2γT/m  (temperature 설정 시)
    Manual: noise_sigma_override > 0 이면 σ 직접 지정
    Off: 둘 다 없으면 σ = 0
    """

    def __init__(
        self,
        gamma: float = 0.0,
        temperature: Optional[float] = None,
        mass: float = 1.0,
        noise_sigma_override: float = 0.0,
    ):
        self._gamma = float(gamma)
        self._temperature = temperature
        self._mass = float(mass)
        self._noise_sigma_override = float(noise_sigma_override)

    @property
    def gamma(self) -> float:
        return self._gamma

    @property
    def sigma(self) -> float:
        if self._noise_sigma_override > 0:
            return self._noise_sigma_override
        if self._temperature is not None and self._temperature > 0 and self._gamma > 0:
            return float(np.sqrt(2.0 * self._gamma * self._temperature / self._mass))
        return 0.0

    @property
    def noise_mode(self) -> str:
        if self._noise_sigma_override > 0:
            return "manual"
        if self._temperature is not None and self._temperature > 0 and self._gamma > 0:
            return "fdt"
        return "off"

    @property
    def temperature(self) -> Optional[float]:
        return self._temperature

    @property
    def mass(self) -> float:
        return self._mass

    def ou_step(self, v: np.ndarray, h: float, rng: np.random.Generator) -> np.ndarray:
        """O-U exact step for time interval h."""
        sigma = self.sigma
        gamma = self._gamma

        decay = np.exp(-gamma * h) if gamma > 0 else 1.0
        v_new = v * decay

        if sigma > 0:
            if gamma > 0:
                amp = sigma * np.sqrt((1.0 - np.exp(-2.0 * gamma * h)) / (2.0 * gamma))
            else:
                amp = sigma * np.sqrt(h)
            v_new = v_new + amp * rng.standard_normal(v.shape)

        return v_new

    def check_fdt(self) -> bool:
        """σ² = 2γT/m 인지 검증. manual이면 FDT 미적용."""
        if self.noise_mode == "manual":
            return True
        if self.noise_mode == "off":
            return True
        expected = np.sqrt(2.0 * self._gamma * self._temperature / self._mass)
        return abs(self.sigma - expected) < 1e-12


class NullThermo:
    """소산/요동 없음. 결정론적 보존계."""

    gamma = 0.0
    sigma = 0.0
    noise_mode = "off"
    temperature = None
    mass = 1.0

    def ou_step(self, v: np.ndarray, h: float, rng: np.random.Generator) -> np.ndarray:
        return v

    def check_fdt(self) -> bool:
        return True


# ================================================================== #
#  극한 일관성 자동 검증 (TrunkChecker)
# ================================================================== #

class TrunkChecker:
    """줄기의 물리적 무결성을 검증한다.

    4대 체크:
      A. conservation — γ=0, σ=0, I=0 → dE ≈ 0
      B. skew        — J^T = -J  (gauge가 에너지를 만들지 않는가)
      C. fdt         — σ² = 2γT/m  (열적 일관성)
      D. dimensions  — state 크기와 layer 출력 크기 정합

    A는 시뮬레이션이 필요하므로 명시적 호출.
    B, C, D는 생성 시 자동 실행 가능.
    """

    @staticmethod
    def check_skew(gauge_layer) -> dict:
        """게이지 레이어의 스큐 대칭성 검증."""
        ok = gauge_layer.check_skew()
        return {"check": "skew_symmetry", "pass": ok,
                "detail": "J^T = -J (energy-preserving)" if ok else "WARNING: gauge may break energy conservation"}

    @staticmethod
    def check_fdt(thermo_layer) -> dict:
        """열역학 레이어의 FDT 일관성 검증."""
        ok = thermo_layer.check_fdt()
        return {"check": "fdt_consistency", "pass": ok,
                "detail": f"mode={thermo_layer.noise_mode}, σ={thermo_layer.sigma:.6f}, γ={thermo_layer.gamma:.4f}"}

    @staticmethod
    def check_dimensions(state_dim: int, force_layers: list, gauge_layer, thermo_layer) -> dict:
        """차원 정합성 검증."""
        x_test = np.zeros(state_dim)
        v_test = np.zeros(state_dim)
        rng = np.random.default_rng(0)

        errors = []
        for i, fl in enumerate(force_layers):
            try:
                f = fl.force(x_test, v_test, 0.0)
                if len(f) != state_dim:
                    errors.append(f"force_layer[{i}]: output dim {len(f)} != state dim {state_dim}")
            except Exception as e:
                errors.append(f"force_layer[{i}]: {e}")

        try:
            v_rot = gauge_layer.rotate(v_test, 0.01)
            if len(v_rot) != state_dim:
                errors.append(f"gauge_layer: output dim {len(v_rot)} != state dim {state_dim}")
        except Exception as e:
            errors.append(f"gauge_layer: {e}")

        try:
            v_ou = thermo_layer.ou_step(v_test, 0.01, rng)
            if len(v_ou) != state_dim:
                errors.append(f"thermo_layer: output dim {len(v_ou)} != state dim {state_dim}")
        except Exception as e:
            errors.append(f"thermo_layer: {e}")

        ok = len(errors) == 0
        return {"check": "dimensions", "pass": ok,
                "detail": "all layers agree on dim" if ok else "; ".join(errors)}

    @staticmethod
    def check_conservation(engine, initial_state, n_steps: int = 500) -> dict:
        """에너지 보존 검증 (보존계 극한).

        원본 engine의 thermo를 NullThermo로, injection forces를 제거한 뒤
        에너지 drift를 측정한다. 기존 engine을 변경하지 않는다.

        이 검증은 비용이 높으므로 명시적 호출만.
        """
        from copy import deepcopy

        eng_copy = deepcopy(engine)
        eng_copy._thermo = NullThermo()
        eng_copy._force_layers = [fl for fl in eng_copy._force_layers
                                  if isinstance(fl, GradientForce)]

        state = initial_state.copy(deep=False)
        E0 = state.energy
        energies = [E0]

        for _ in range(n_steps):
            state = eng_copy.update(state)
            energies.append(state.energy)

        energies = np.array(energies)
        max_drift = float(np.max(np.abs(energies - E0)))
        rel_drift = max_drift / abs(E0) if abs(E0) > 1e-12 else max_drift

        ok = rel_drift < 0.01
        return {"check": "conservation", "pass": ok,
                "detail": f"max |ΔE|/E₀ = {rel_drift:.2e} (n={n_steps})"}

    @staticmethod
    def run_all(engine, initial_state=None) -> list:
        """모든 정적 체크 실행. conservation은 initial_state가 있을 때만."""
        results = []
        results.append(TrunkChecker.check_skew(engine._gauge))
        results.append(TrunkChecker.check_fdt(engine._thermo))

        if initial_state is not None:
            dim = len(initial_state.state_vector) // 2
            results.append(TrunkChecker.check_dimensions(
                dim, engine._force_layers, engine._gauge, engine._thermo))
            results.append(TrunkChecker.check_conservation(engine, initial_state))

        return results
