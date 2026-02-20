"""PotentialFieldEngine Configuration

모든 하드코딩된 상수를 여기로 모아서 관리합니다.

설계 원칙:
- 하드코딩 금지: 모든 상수는 CONFIG에서만 정의
- 기본값 제공: 엔진 초기화 시 기본값 사용 가능
- 외부 제어 가능: CONFIG를 수정하여 동작 변경 가능
"""

# 수치 계산 상수
EPSILON = 1e-6  # 수치 기울기 계산용 작은 값
DT = 0.01  # 시간 스텝 (기본값)

# 중력장 상수
GRAVITY_CONSTANT = 1.0  # 중력 상수 (기본값)
SOFTENING = 1e-6  # 수치 안정성을 위한 작은 값

# 그리드 분석 상수
DEFAULT_GRID_SIZE = (100, 100)  # 기본 그리드 크기
DEFAULT_X_RANGE = (-5.0, 5.0)  # 기본 x 범위
DEFAULT_Y_RANGE = (-5.0, 5.0)  # 기본 y 범위

# 로깅
DEFAULT_ENABLE_LOGGING = True  # 기본 로깅 활성화 여부

