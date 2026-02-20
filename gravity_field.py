"""Gravity Field

중력장 필드 구현: 중력 퍼텐셜과 필드를 계산합니다.

은유 → 실제 코드 매핑:
- 태양계 은유 → 중력 퍼텐셜 V_gravity(x) = -G * M / ||x - x_center||
- 중력장 → 필드 g_gravity(x) = -G * Σ_i (M_i * (x - x_i) / ||x - x_i||^3)

수식:
- 점 질량: V_gravity(x) = -G * M / ||x - x_center||
- 여러 질량: V_gravity(x) = -G * Σ_i (M_i / ||x - x_i||)
- 필드: g_gravity(x) = -G * Σ_i (M_i * (x - x_i) / ||x - x_i||^3)

개념 및 논문 출처:
- 중력 퍼텐셜: Newtonian mechanics, Universal gravitation law
- 필드 이론: Classical field theory, Electromagnetism
- 다체 문제: N-body problem, Celestial mechanics
- 수치 안정성: Softening parameter (Plummer sphere), Numerical methods

참고 문헌:
- Newton, I. (1687). "Philosophiæ Naturalis Principia Mathematica"
- Poisson, S. D. (1813). "Remarques sur une équation qui se présente dans la théorie des attractions"
"""

import numpy as np
from typing import Callable, List, Tuple, Optional
import logging

# CONFIG: 모든 하드코딩된 상수는 여기서만 정의
try:
    from .CONFIG import GRAVITY_CONSTANT, SOFTENING, DEFAULT_ENABLE_LOGGING
except ImportError:
    # 독립 실행 시 fallback
    from CONFIG import GRAVITY_CONSTANT, SOFTENING, DEFAULT_ENABLE_LOGGING


class GravityField:
    """중력장 필드
    
    역할: 중력 퍼텐셜과 필드를 계산
    
    수식:
    - 점 질량: V(x) = -G * M / ||x - x_center||
    - 여러 질량: V(x) = -G * Σ_i (M_i / ||x - x_i||)
    - 필드: g(x) = -G * Σ_i (M_i * (x - x_i) / ||x - x_i||^3)
    """
    
    def __init__(
        self,
        masses: List[Tuple[np.ndarray, float]],
        G: float = None,
        softening: float = None,
        enable_logging: bool = None,
    ):
        """GravityField 초기화
        
        설계 원칙:
        - 하드코딩 금지: 모든 기본값은 CONFIG에서 가져옴
        
        Args:
            masses: 질량 리스트 [(위치, 질량), ...]
            G: 중력 상수 (None이면 CONFIG.GRAVITY_CONSTANT 사용)
            softening: 수치 안정성을 위한 작은 값 (None이면 CONFIG.SOFTENING 사용)
            enable_logging: 로깅 활성화 여부 (None이면 CONFIG.DEFAULT_ENABLE_LOGGING 사용)
        """
        self.masses = masses
        # CONFIG에서 기본값 가져오기 (하드코딩 금지)
        self.G = G if G is not None else GRAVITY_CONSTANT
        self.softening = softening if softening is not None else SOFTENING
        self.enable_logging = enable_logging if enable_logging is not None else DEFAULT_ENABLE_LOGGING
        
        if enable_logging:
            self.logger = logging.getLogger("GravityField")
        else:
            self.logger = None
    
    def potential(self, x: np.ndarray) -> float:
        """중력 퍼텐셜 계산
        
        수식: V(x) = -G * Σ_i (M_i / ||x - x_i||)
        
        Args:
            x: 위치 벡터
            
        Returns:
            퍼텐셜 값
        """
        V = 0.0
        for x_i, M_i in self.masses:
            r = np.linalg.norm(x - x_i)
            if r < self.softening:
                r = self.softening  # 수치 안정성
            V += -self.G * M_i / r
        
        return V
    
    def field(self, x: np.ndarray) -> np.ndarray:
        """중력 필드 계산
        
        수식: g(x) = -G * Σ_i (M_i * (x - x_i) / ||x - x_i||^3)
        
        Args:
            x: 위치 벡터
            
        Returns:
            필드 벡터
        """
        g = np.zeros_like(x)
        for x_i, M_i in self.masses:
            r_vec = x - x_i
            r = np.linalg.norm(r_vec)
            if r < self.softening:
                r = self.softening  # 수치 안정성
            g += -self.G * M_i * r_vec / (r ** 3)
        
        return g
    
    def potential_and_field(self, x: np.ndarray) -> Tuple[float, np.ndarray]:
        """퍼텐셜과 필드를 동시에 계산 (최적화)
        
        Args:
            x: 위치 벡터
            
        Returns:
            (퍼텐셜, 필드) 튜플
        """
        V = 0.0
        g = np.zeros_like(x)
        
        for x_i, M_i in self.masses:
            r_vec = x - x_i
            r = np.linalg.norm(r_vec)
            if r < self.softening:
                r = self.softening  # 수치 안정성
            
            V += -self.G * M_i / r
            g += -self.G * M_i * r_vec / (r ** 3)
        
        return V, g


def create_gravity_potential(
    masses: List[Tuple[np.ndarray, float]],
    G: float = None,
    softening: float = None,
) -> Callable[[np.ndarray], float]:
    """중력 퍼텐셜 함수 생성
    
    설계 원칙:
    - 하드코딩 금지: 모든 기본값은 CONFIG에서 가져옴
    
    Args:
        masses: 질량 리스트 [(위치, 질량), ...]
        G: 중력 상수 (None이면 CONFIG.GRAVITY_CONSTANT 사용)
        softening: 수치 안정성을 위한 작은 값 (None이면 CONFIG.SOFTENING 사용)
        
    Returns:
        퍼텐셜 함수 V(x) -> float
    """
    # CONFIG에서 기본값 사용 (하드코딩 금지)
    gravity_field = GravityField(
        masses=masses, 
        G=G if G is not None else GRAVITY_CONSTANT,
        softening=softening if softening is not None else SOFTENING
    )
    return gravity_field.potential


def create_composite_potential(
    gravity_func: Optional[Callable[[np.ndarray], float]] = None,
    well_funcs: Optional[List[Callable[[np.ndarray], float]]] = None,
    custom_funcs: Optional[List[Callable[[np.ndarray], float]]] = None,
) -> Callable[[np.ndarray], float]:
    """여러 퍼텐셜을 합성
    
    수식: total_potential = V_gravity + ΣV_wells + ΣV_custom
    
    Args:
        gravity_func: 중력 퍼텐셜 함수
        well_funcs: 우물 퍼텐셜 함수 리스트
        custom_funcs: 커스텀 퍼텐셜 함수 리스트
        
    Returns:
        합성된 퍼텐셜 함수
    """
    def composite_potential(x: np.ndarray) -> float:
        V_total = 0.0
        
        # 중력 퍼텐셜
        if gravity_func:
            V_total += gravity_func(x)
        
        # 우물 퍼텐셜
        if well_funcs:
            for well_func in well_funcs:
                V_total += well_func(x)
        
        # 커스텀 퍼텐셜
        if custom_funcs:
            for custom_func in custom_funcs:
                V_total += custom_func(x)
        
        return V_total
    
    return composite_potential

