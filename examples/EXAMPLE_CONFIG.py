"""Examples Configuration

데모 및 예제에서 사용하는 설정값들을 정의합니다.

설계 원칙:
- 하드코딩 금지: 모든 상수는 여기서만 정의
- CONFIG 기본값 사용: 가능한 한 CONFIG의 기본값 사용
- 데모 전용 값: 데모에만 필요한 값만 여기서 정의
"""

from CONFIG import EPSILON, DEFAULT_GRID_SIZE, DEFAULT_X_RANGE, DEFAULT_Y_RANGE, GRAVITY_CONSTANT

# 데모 전용 그리드 설정
DEMO_GRID_SIZE = DEFAULT_GRID_SIZE  # (100, 100)
DEMO_X_RANGE = DEFAULT_X_RANGE  # (-5.0, 5.0)
DEMO_Y_RANGE = DEFAULT_Y_RANGE  # (-5.0, 5.0)

# 고해상도 그리드 (다중 코어 시나리오용)
DEMO_HIGH_RES_GRID_SIZE = (150, 150)

# 데모 전용 중력 설정
DEMO_G = GRAVITY_CONSTANT  # 1.0

# 데모 전용 질량 설정
DEMO_SINGLE_CORE_MASS = 2.0
DEMO_DUAL_CORE_MASSES = [
    ([-2.0, 0.0], 2.0),  # 왼쪽 코어
    ([2.0, 0.0], 1.5),   # 오른쪽 코어
]
DEMO_MULTI_CORE_MASSES = [
    ([-2.0, -2.0], 1.5),  # 좌하단 코어
    ([2.0, -2.0], 1.0),   # 우하단 코어
    ([0.0, 2.0], 2.0),    # 상단 코어 (가장 강함)
    ([-1.0, 0.0], 0.8),   # 좌측 코어
    ([1.0, 0.0], 0.8),    # 우측 코어
]

# epsilon은 반드시 CONFIG.EPSILON 사용 (하드코딩 금지)
DEMO_EPSILON = EPSILON  # 1e-6

