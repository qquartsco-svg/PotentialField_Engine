"""WellFormationEngine Integration

WellFormationEngine 결과를 퍼텐셜 함수로 변환합니다.

은유 → 실제 코드 매핑:
- 우물 은유 → Hopfield 에너지 E(x) = -(1/2) * Σ_ij w_ij x_i x_j - Σ_i b_i x_i
- 우물 형성 → WellFormationEngine이 W, b 생성
- 퍼텐셜 변환 → E(x)를 V(x)로 사용

수식:
- WellFormationEngine 결과: W (가중치 행렬), b (바이어스 벡터)
- Hopfield 에너지: E(x) = -(1/2) * Σ_ij w_ij x_i x_j - Σ_i b_i x_i
- 퍼텐셜로 사용: V(x) = E(x)
- 필드: g(x) = -∇E(x) = Wx + b

개념 및 논문 출처:
- Hopfield 에너지: Hopfield, J. J. (1982). "Neural networks and physical systems with emergent collective computational abilities"
- Hebbian 학습: Hebb, D. O. (1949). "The Organization of Behavior"
- 안정성 제약: Lyapunov stability theory, Cohen & Grossberg (1983)

참고 문헌:
- Hopfield, J. J. (1982). "Neural networks and physical systems with emergent collective computational abilities"
- Cohen, M. A., & Grossberg, S. (1983). "Absolute stability of global pattern formation"
- Hebb, D. O. (1949). "The Organization of Behavior: A Neuropsychological Theory"
"""

import numpy as np
from typing import Callable, Any, Dict


def create_potential_from_wells(well_result: Any) -> Callable[[np.ndarray], float]:
    """WellFormationEngine 결과를 퍼텐셜 함수로 변환
    
    WellFormationEngine이 만든 W, b를 Hopfield 에너지로 변환:
    E(x) = -(1/2) Σ_ij w_ij x_i x_j - Σ_i b_i x_i
    
    이걸 퍼텐셜로 사용:
    V(x) = E(x)
    
    Args:
        well_result: WellFormationEngine.generate_well() 결과
                    (W, b 속성을 가진 객체 또는 딕셔너리)
        
    Returns:
        퍼텐셜 함수 V(x) -> float
    """
    # well_result에서 W, b 추출
    if isinstance(well_result, dict):
        W = np.array(well_result.get("W", well_result.get("weights")))
        b = np.array(well_result.get("b", well_result.get("bias")))
    else:
        # 객체인 경우
        W = np.array(getattr(well_result, "W", getattr(well_result, "weights", None)))
        b = np.array(getattr(well_result, "b", getattr(well_result, "bias", None)))
    
    if W is None or b is None:
        raise ValueError("well_result must have W and b attributes")
    
    # W가 리스트인 경우 numpy 배열로 변환
    W = np.array(W)
    b = np.array(b)
    
    def potential(x: np.ndarray) -> float:
        """Hopfield 에너지를 퍼텐셜로 사용
        
        수식: E(x) = -(1/2) * Σ_ij w_ij x_i x_j - Σ_i b_i x_i
        
        Args:
            x: 상태 벡터
            
        Returns:
            퍼텐셜 값 (에너지)
        """
        # 차원 맞추기
        if len(x) != len(b):
            raise ValueError(f"Dimension mismatch: x has {len(x)} elements, b has {len(b)}")
        
        # 이차항: -(1/2) * x^T W x
        quadratic = -0.5 * np.dot(x, np.dot(W, x))
        
        # 일차항: -b^T x
        linear = -np.dot(b, x)
        
        return quadratic + linear
    
    return potential


def create_field_from_wells(well_result: Any) -> Callable[[np.ndarray], np.ndarray]:
    """WellFormationEngine 결과를 필드 함수로 변환
    
    수식: g(x) = -∇E(x) = Wx + b
    
    Args:
        well_result: WellFormationEngine.generate_well() 결과
        
    Returns:
        필드 함수 g(x) -> np.ndarray
    """
    # well_result에서 W, b 추출
    if isinstance(well_result, dict):
        W = np.array(well_result.get("W", well_result.get("weights")))
        b = np.array(well_result.get("b", well_result.get("bias")))
    else:
        W = np.array(getattr(well_result, "W", getattr(well_result, "weights", None)))
        b = np.array(getattr(well_result, "b", getattr(well_result, "bias", None)))
    
    if W is None or b is None:
        raise ValueError("well_result must have W and b attributes")
    
    W = np.array(W)
    b = np.array(b)
    
    def field(x: np.ndarray) -> np.ndarray:
        """필드 계산
        
        수식: g(x) = Wx + b
        
        Args:
            x: 상태 벡터
            
        Returns:
            필드 벡터
        """
        if len(x) != len(b):
            raise ValueError(f"Dimension mismatch: x has {len(x)} elements, b has {len(b)}")
        
        return np.dot(W, x) + b
    
    return field

