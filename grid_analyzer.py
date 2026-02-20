"""Grid Analyzer

상태공간을 그리드로 펼쳐 퍼텐셜 필드와 벡터장 구조를 분석합니다.

기능:
- 그리드 생성
- 퍼텐셜 맵 계산
- 필드 맵 계산
- 발산/회전 계산 (벡터장 구조 분석)
- 시각화

수식:
- 발산: ∇·g = ∂g_x/∂x + ∂g_y/∂y
- 회전: ∇×g = ∂g_y/∂x - ∂g_x/∂y (2D)

물리적 의미:
- 발산: 소스/싱크 구조 탐지 (플럭스 구조)
- 회전: 비보존 성분 탐지 (비퍼텐셜 성분)

참고: 이 모듈은 정적 벡터장 분석 도구입니다. 시간 의존성, Navier-Stokes 방정식, 난류 시뮬레이션은 포함하지 않습니다.

개념 및 논문 출처:
- 발산 (Divergence): Vector calculus (Gauss's theorem), Field theory
- 회전 (Curl): Vector calculus (Stokes' theorem), Electromagnetism
- 벡터장 분석: Vector calculus, Field theory
- 그리드 분석: Numerical methods, Finite difference method

참고 문헌:
- Vector calculus: Arfken, G. B., Weber, H. J., & Harris, F. E. (2013). "Mathematical Methods for Physicists" (7th ed.)
- Numerical methods: Press, W. H., Teukolsky, S. A., Vetterling, W. T., & Flannery, B. P. (2007). "Numerical Recipes" (3rd ed.)
- Field theory: Jackson, J. D. (1999). "Classical Electrodynamics" (3rd ed.)
"""

import numpy as np
from typing import Callable, Tuple, Dict, Any, Optional
import logging

# CONFIG: 모든 하드코딩된 상수는 여기서만 정의
try:
    from .CONFIG import EPSILON, DEFAULT_GRID_SIZE, DEFAULT_X_RANGE, DEFAULT_Y_RANGE, DEFAULT_ENABLE_LOGGING
except ImportError:
    # 독립 실행 시 fallback
    from CONFIG import EPSILON, DEFAULT_GRID_SIZE, DEFAULT_X_RANGE, DEFAULT_Y_RANGE, DEFAULT_ENABLE_LOGGING

# matplotlib은 선택적 의존성 (시각화가 필요한 경우만)
try:
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    plt = None


class GridAnalyzer:
    """그리드 분석기
    
    역할: 상태공간을 그리드로 펼쳐 퍼텐셜 필드 및 벡터장 구조 분석
    
    기능:
    - 그리드 생성
    - 퍼텐셜 맵 계산
    - 필드 맵 계산
    - 발산/회전 계산 (벡터장 구조 분석)
    """
    
    def __init__(
        self,
        x_range: Tuple[float, float] = None,
        y_range: Tuple[float, float] = None,
        grid_size: Tuple[int, int] = None,
        enable_logging: bool = None,
    ):
        """GridAnalyzer 초기화
        
        설계 원칙:
        - 하드코딩 금지: 모든 기본값은 CONFIG에서 가져옴
        - 연구용 도구: 실행 루프와 분리된 시각화 유틸리티
        
        Args:
            x_range: x 범위 (None이면 CONFIG.DEFAULT_X_RANGE 사용)
            y_range: y 범위 (None이면 CONFIG.DEFAULT_Y_RANGE 사용)
            grid_size: 그리드 크기 (None이면 CONFIG.DEFAULT_GRID_SIZE 사용)
            enable_logging: 로깅 활성화 여부 (None이면 CONFIG.DEFAULT_ENABLE_LOGGING 사용)
        """
        # CONFIG에서 기본값 가져오기 (하드코딩 금지)
        self.x_range = x_range if x_range is not None else DEFAULT_X_RANGE
        self.y_range = y_range if y_range is not None else DEFAULT_Y_RANGE
        self.grid_size = grid_size if grid_size is not None else DEFAULT_GRID_SIZE
        self.enable_logging = enable_logging if enable_logging is not None else DEFAULT_ENABLE_LOGGING
        
        if enable_logging:
            self.logger = logging.getLogger("GridAnalyzer")
        else:
            self.logger = None
        
        # 그리드 생성
        self.x_grid, self.y_grid = self._create_grid()
    
    def _create_grid(self) -> Tuple[np.ndarray, np.ndarray]:
        """그리드 생성
        
        Returns:
            (x_grid, y_grid) 튜플
        """
        x_min, x_max = self.x_range
        y_min, y_max = self.y_range
        N_x, N_y = self.grid_size
        
        x = np.linspace(x_min, x_max, N_x)
        y = np.linspace(y_min, y_max, N_y)
        # indexing="ij"로 shape을 (N_x, N_y)로 맞춤 (grid_size와 일치)
        x_grid, y_grid = np.meshgrid(x, y, indexing='ij')
        
        return x_grid, y_grid
    
    def _central_difference(
        self,
        f: np.ndarray,
        axis: int,
        dx: float = None,
        dy: float = None,
    ) -> np.ndarray:
        """중심차분 계산 (일관된 수치 미분 scheme)
        
        수식:
        - 내부 점: (f[i+1] - f[i-1]) / (2*dx)
        - 첫 번째 점: (f[1] - f[0]) / dx (전진 차분)
        - 마지막 점: (f[N-1] - f[N-2]) / dx (후진 차분)
        
        Args:
            f: 미분할 배열
            axis: 미분 방향 (0: x 방향, 1: y 방향)
            dx: x 방향 간격 (axis=0일 때 사용)
            dy: y 방향 간격 (axis=1일 때 사용)
            
        Returns:
            미분 결과 배열
        """
        if axis == 0:
            # x 방향 미분 (axis=0)
            h = dx
            df = np.zeros_like(f)
            N = f.shape[0]
            
            # 내부 점: 중심차분
            if N > 2:
                df[1:N-1, :] = (f[2:N, :] - f[0:N-2, :]) / (2 * h)
            
            # 경계 점: 전진/후진 차분
            if N > 1:
                df[0, :] = (f[1, :] - f[0, :]) / h  # 첫 번째 점: 전진 차분
                df[N-1, :] = (f[N-1, :] - f[N-2, :]) / h  # 마지막 점: 후진 차분
            elif N == 1:
                df[0, :] = 0.0  # 단일 점: 미분 불가
            
        elif axis == 1:
            # y 방향 미분 (axis=1)
            h = dy
            df = np.zeros_like(f)
            N = f.shape[1]
            
            # 내부 점: 중심차분
            if N > 2:
                df[:, 1:N-1] = (f[:, 2:N] - f[:, 0:N-2]) / (2 * h)
            
            # 경계 점: 전진/후진 차분
            if N > 1:
                df[:, 0] = (f[:, 1] - f[:, 0]) / h  # 첫 번째 점: 전진 차분
                df[:, N-1] = (f[:, N-1] - f[:, N-2]) / h  # 마지막 점: 후진 차분
            elif N == 1:
                df[:, 0] = 0.0  # 단일 점: 미분 불가
        
        else:
            raise ValueError(f"axis must be 0 or 1, got {axis}")
        
        return df
    
    def compute_potential_map(
        self,
        potential_func: Callable[[np.ndarray], float],
    ) -> np.ndarray:
        """퍼텐셜 맵 계산
        
        Args:
            potential_func: 퍼텐셜 함수 V(x) -> float
            
        Returns:
            퍼텐셜 맵 (2D 배열)
        """
        V_map = np.zeros(self.grid_size)
        
        for i in range(self.grid_size[0]):
            for j in range(self.grid_size[1]):
                x = np.array([self.x_grid[i, j], self.y_grid[i, j]])
                V_map[i, j] = potential_func(x)
        
        if self.logger:
            self.logger.debug(f"Potential map computed: shape={V_map.shape}")
        
        return V_map
    
    def compute_field_map(
        self,
        potential_func: Callable[[np.ndarray], float],
        epsilon: float = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """필드 맵 계산
        
        수식: g(x) = -∇V(x)
        
        설계 원칙:
        - 하드코딩 금지: epsilon은 CONFIG에서 가져옴
        
        Args:
            potential_func: 퍼텐셜 함수 V(x) -> float
            epsilon: 수치 기울기 계산용 작은 값 (None이면 CONFIG.EPSILON 사용)
            
        Returns:
            (gx_map, gy_map) 튜플 (필드 x, y 성분)
        """
        # CONFIG에서 기본값 사용 (하드코딩 금지, 직접 호출 시에도 안전)
        epsilon = epsilon if epsilon is not None else EPSILON
        
        gx_map = np.zeros(self.grid_size)
        gy_map = np.zeros(self.grid_size)
        
        for i in range(self.grid_size[0]):
            for j in range(self.grid_size[1]):
                x = np.array([self.x_grid[i, j], self.y_grid[i, j]])
                
                # 수치적 기울기 계산
                x_plus = x.copy()
                x_plus[0] += epsilon
                x_minus = x.copy()
                x_minus[0] -= epsilon
                gx_map[i, j] = -(potential_func(x_plus) - potential_func(x_minus)) / (2 * epsilon)
                
                x_plus = x.copy()
                x_plus[1] += epsilon
                x_minus = x.copy()
                x_minus[1] -= epsilon
                gy_map[i, j] = -(potential_func(x_plus) - potential_func(x_minus)) / (2 * epsilon)
        
        if self.logger:
            self.logger.debug(f"Field map computed: shape={gx_map.shape}")
        
        return gx_map, gy_map
    
    def compute_divergence(
        self,
        gx_map: np.ndarray,
        gy_map: np.ndarray,
    ) -> np.ndarray:
        """발산 계산
        
        수식: ∇·g = ∂g_x/∂x + ∂g_y/∂y
        
        물리적 의미:
        - ∇·g > 0: 소스 영역 (outflow, 플럭스가 외부로 나가는 영역)
        - ∇·g < 0: 싱크 영역 (inflow, 플럭스가 내부로 흡수되는 영역)
        - ∇·g = 0: 소스/싱크 없음 (locally solenoidal, 발산 0)
        
        참고:
        - 순수 퍼텐셜 필드(g = -∇V)의 경우 Poisson 방정식: ∇²V = -∇·g
        - 중력장의 경우 Poisson 방정식 ∇²V = -4πGρ에 의해, 질량 밀도(ρ > 0)가 있는 곳은 ∇·g < 0 (싱크)가 됩니다
        - 발산은 "안정/불안정"과 직접 연결되지 않음 (소스/싱크/라플라시안 구조 탐지)
        
        Args:
            gx_map: 필드 x 성분 맵
            gy_map: 필드 y 성분 맵
            
        Returns:
            발산 맵
        """
        # 그리드 간격 계산
        # indexing='ij' 기준: axis=0이 x 방향, axis=1이 y 방향
        # grid_size = (N_x, N_y)
        x_min, x_max = self.x_range
        y_min, y_max = self.y_range
        dx = (x_max - x_min) / (self.grid_size[0] - 1)  # grid_size[0] = N_x
        dy = (y_max - y_min) / (self.grid_size[1] - 1)  # grid_size[1] = N_y
        
        # 수치적 미분 (중심차분, compute_field_map과 일관성 유지)
        # ∂/∂x → axis=0, ∂/∂y → axis=1
        # 내부 점: 중심차분 (f[i+1] - f[i-1]) / (2*dx)
        # 경계 점: 전진/후진 차분
        dgx_dx = self._central_difference(gx_map, axis=0, dx=dx)
        dgy_dy = self._central_difference(gy_map, axis=1, dy=dy)
        
        divergence = dgx_dx + dgy_dy
        
        if self.logger:
            self.logger.debug(f"Divergence computed: shape={divergence.shape}")
        
        return divergence
    
    def compute_curl(
        self,
        gx_map: np.ndarray,
        gy_map: np.ndarray,
    ) -> np.ndarray:
        """회전 계산
        
        수식: ∇×g = ∂g_y/∂x - ∂g_x/∂y  (2D)
        
        물리적 의미:
        - ∇×g ≠ 0: 비보존 성분/비퍼텐셜 성분 (회전 성분 존재)
        - ∇×g = 0: 순수 퍼텐셜 필드 (보존력, 수치 오차만 남음)
        
        참고:
        - 순수 퍼텐셜 필드(g = -∇V)는 이론상 curl = 0 (연속/매끄러운 V 가정)
        - 수치 계산에서는 격자 간격(dx, dy), epsilon(기울기 계산), 경계 조건, 특이점(예: r=0 근처 softening)에 의해 잔차가 남을 수 있음
        - curl ≠ 0이면 비퍼텐셜 성분(예: 마그네틱 필드, 비보존력) 탐지 가능
        
        Args:
            gx_map: 필드 x 성분 맵
            gy_map: 필드 y 성분 맵
            
        Returns:
            회전 맵
        """
        # 그리드 간격 계산
        # indexing='ij' 기준: axis=0이 x 방향, axis=1이 y 방향
        # grid_size = (N_x, N_y)
        x_min, x_max = self.x_range
        y_min, y_max = self.y_range
        dx = (x_max - x_min) / (self.grid_size[0] - 1)  # grid_size[0] = N_x
        dy = (y_max - y_min) / (self.grid_size[1] - 1)  # grid_size[1] = N_y
        
        # 수치적 미분 (중심차분, compute_field_map과 일관성 유지)
        # ∂/∂x → axis=0, ∂/∂y → axis=1
        # 내부 점: 중심차분 (f[i+1] - f[i-1]) / (2*dx)
        # 경계 점: 전진/후진 차분
        dgy_dx = self._central_difference(gy_map, axis=0, dx=dx)
        dgx_dy = self._central_difference(gx_map, axis=1, dy=dy)
        
        curl = dgy_dx - dgx_dy
        
        if self.logger:
            self.logger.debug(f"Curl computed: shape={curl.shape}")
        
        return curl
    
    def analyze(
        self,
        potential_func: Callable[[np.ndarray], float],
        epsilon: float = None,
    ) -> Dict[str, np.ndarray]:
        """전체 분석 수행
        
        설계 원칙:
        - 하드코딩 금지: epsilon은 CONFIG에서 가져옴
        
        Args:
            potential_func: 퍼텐셜 함수 V(x) -> float
            epsilon: 수치 기울기 계산용 작은 값 (None이면 CONFIG.EPSILON 사용)
            
        Returns:
            분석 결과 딕셔너리
        """
        # CONFIG에서 기본값 사용 (하드코딩 금지)
        epsilon = epsilon if epsilon is not None else EPSILON
        
        # 퍼텐셜 맵
        V_map = self.compute_potential_map(potential_func)
        
        # 필드 맵
        gx_map, gy_map = self.compute_field_map(potential_func, epsilon)
        
        # 발산
        divergence = self.compute_divergence(gx_map, gy_map)
        
        # 회전
        curl = self.compute_curl(gx_map, gy_map)
        
        return {
            "potential_map": V_map,
            "field_x": gx_map,
            "field_y": gy_map,
            "divergence": divergence,
            "curl": curl,
            "x_grid": self.x_grid,
            "y_grid": self.y_grid,
        }


class GridVisualizer:
    """그리드 시각화기
    
    역할: 그리드 분석 결과를 시각화
    """
    
    def __init__(self, analyzer: GridAnalyzer):
        """GridVisualizer 초기화
        
        Args:
            analyzer: GridAnalyzer 인스턴스
        """
        self.analyzer = analyzer
    
    def plot_potential(
        self,
        V_map: np.ndarray,
        title: str = "Potential Map",
        save_path: Optional[str] = None,
    ):
        """퍼텐셜 맵 시각화
        
        Args:
            V_map: 퍼텐셜 맵
            title: 제목
            save_path: 저장 경로 (None이면 표시만)
        """
        if not HAS_MATPLOTLIB:
            raise ImportError("matplotlib이 필요합니다. pip install matplotlib")
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        im = ax.contourf(
            self.analyzer.x_grid,
            self.analyzer.y_grid,
            V_map,
            levels=50,
            cmap='viridis',
        )
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_title(title)
        plt.colorbar(im, ax=ax, label='Potential V(x)')
        ax.grid(True, alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        else:
            plt.show()
        
        plt.close()
    
    def plot_field(
        self,
        gx_map: np.ndarray,
        gy_map: np.ndarray,
        title: str = "Field Map",
        save_path: Optional[str] = None,
        scale: float = 1.0,
    ):
        """필드 맵 시각화
        
        Args:
            gx_map: 필드 x 성분 맵
            gy_map: 필드 y 성분 맵
            title: 제목
            save_path: 저장 경로 (None이면 표시만)
            scale: 화살표 크기 조절
        """
        if not HAS_MATPLOTLIB:
            raise ImportError("matplotlib이 필요합니다. pip install matplotlib")
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # 화살표 간격 조절
        step = max(1, min(self.analyzer.grid_size) // 20)
        
        ax.quiver(
            self.analyzer.x_grid[::step, ::step],
            self.analyzer.y_grid[::step, ::step],
            gx_map[::step, ::step],
            gy_map[::step, ::step],
            scale=scale,
            angles='xy',
            scale_units='xy',
        )
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        else:
            plt.show()
        
        plt.close()
    
    def plot_divergence(
        self,
        divergence: np.ndarray,
        title: str = "Divergence Map (Source/Sink Structure)",
        save_path: Optional[str] = None,
    ):
        """발산 맵 시각화 (소스/싱크 구조 분석)
        
        Args:
            divergence: 발산 맵
            title: 제목
            save_path: 저장 경로 (None이면 표시만)
        """
        if not HAS_MATPLOTLIB:
            raise ImportError("matplotlib이 필요합니다. pip install matplotlib")
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        im = ax.contourf(
            self.analyzer.x_grid,
            self.analyzer.y_grid,
            divergence,
            levels=50,
            cmap='RdBu_r',
        )
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_title(title)
        plt.colorbar(im, ax=ax, label='∇·g (Divergence)')
        ax.grid(True, alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        else:
            plt.show()
        
        plt.close()
    
    def plot_curl(
        self,
        curl: np.ndarray,
        title: str = "Curl Map (Non-Conservative Component)",
        save_path: Optional[str] = None,
    ):
        """회전 맵 시각화 (비보존 성분 분석)
        
        Args:
            curl: 회전 맵
            title: 제목
            save_path: 저장 경로 (None이면 표시만)
        """
        if not HAS_MATPLOTLIB:
            raise ImportError("matplotlib이 필요합니다. pip install matplotlib")
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        im = ax.contourf(
            self.analyzer.x_grid,
            self.analyzer.y_grid,
            curl,
            levels=50,
            cmap='RdBu_r',
        )
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_title(title)
        plt.colorbar(im, ax=ax, label='∇×g (Curl)')
        ax.grid(True, alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        else:
            plt.show()
        
        plt.close()
    
    def plot_all(
        self,
        analysis_result: Dict[str, np.ndarray],
        save_dir: Optional[str] = None,
    ):
        """전체 분석 결과 시각화
        
        Args:
            analysis_result: GridAnalyzer.analyze() 결과
            save_dir: 저장 디렉토리 (None이면 표시만)
        """
        # 퍼텐셜 맵
        self.plot_potential(
            analysis_result["potential_map"],
            title="Potential Map",
            save_path=f"{save_dir}/potential_map.png" if save_dir else None,
        )
        
        # 필드 맵
        self.plot_field(
            analysis_result["field_x"],
            analysis_result["field_y"],
            title="Field Map",
            save_path=f"{save_dir}/field_map.png" if save_dir else None,
        )
        
        # 발산 맵
        self.plot_divergence(
            analysis_result["divergence"],
            title="Divergence Map (Source/Sink Structure)",
            save_path=f"{save_dir}/divergence_map.png" if save_dir else None,
        )
        
        # 회전 맵
        self.plot_curl(
            analysis_result["curl"],
            title="Curl Map (Non-Conservative Component)",
            save_path=f"{save_dir}/curl_map.png" if save_dir else None,
        )

