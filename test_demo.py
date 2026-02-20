"""Potential Field Engine 테스트 및 데모

중력장을 그리드로 펼쳐 왜곡을 탐지하는 데모입니다.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 백엔드 설정 (GUI 없이 실행)
import matplotlib.pyplot as plt
from pathlib import Path

from .potential_field_engine import PotentialFieldEngine
from .gravity_field import create_gravity_potential, create_composite_potential
from .grid_analyzer import GridAnalyzer, GridVisualizer

# BrainCore import
try:
    from brain_core.global_state import GlobalState
except ImportError:
    import sys
    from pathlib import Path
    brain_core_path = Path(__file__).parent.parent.parent.parent / "BrainCore" / "src"
    sys.path.insert(0, str(brain_core_path))
    from brain_core.global_state import GlobalState


def demo_gravity_field():
    """중력장 데모"""
    print("=" * 60)
    print("중력장 데모")
    print("=" * 60)
    
    # 중력 퍼텐셜 생성 (중심에 질량 1.0)
    masses = [
        (np.array([0.0, 0.0]), 1.0),
    ]
    gravity_potential = create_gravity_potential(masses, G=1.0)
    
    # PotentialFieldEngine 생성
    field_engine = PotentialFieldEngine(
        potential_func=gravity_potential,
        dt=0.01,
        epsilon=1e-6,
    )
    
    # 초기 상태
    initial_state = GlobalState(
        state_vector=np.concatenate([
            np.array([1.0, 0.0]),  # 위치
            np.array([0.0, 0.0]),  # 속도
        ]),
        energy=0.0,
        risk=0.0,
    )
    
    # 업데이트
    updated_state = field_engine.update(initial_state)
    
    print(f"초기 위치: {initial_state.state_vector[:2]}")
    print(f"업데이트 위치: {updated_state.state_vector[:2]}")
    print(f"퍼텐셜: {updated_state.get_extension('potential_field')['potential']:.6f}")
    print(f"에너지: {updated_state.energy:.6f}")
    print()


def demo_grid_analysis():
    """그리드 분석 데모"""
    print("=" * 60)
    print("그리드 분석 데모 (중력 왜곡 탐지)")
    print("=" * 60)
    
    # 중력 퍼텐셜 생성
    masses = [
        (np.array([0.0, 0.0]), 1.0),  # 중심에 질량 1.0
    ]
    gravity_potential = create_gravity_potential(masses, G=1.0)
    
    # 그리드 분석기 생성
    analyzer = GridAnalyzer(
        x_range=(-5.0, 5.0),
        y_range=(-5.0, 5.0),
        grid_size=(100, 100),
    )
    
    # 분석 수행
    print("분석 수행 중...")
    analysis_result = analyzer.analyze(
        potential_func=gravity_potential,
        epsilon=1e-6,
    )
    
    print(f"퍼텐셜 맵: {analysis_result['potential_map'].shape}")
    print(f"필드 맵: {analysis_result['field_x'].shape}")
    print(f"발산 맵: {analysis_result['divergence'].shape}")
    print(f"회전 맵: {analysis_result['curl'].shape}")
    
    # 발산 통계
    divergence = analysis_result['divergence']
    print(f"\n발산 통계:")
    print(f"  최소값: {divergence.min():.6f}")
    print(f"  최대값: {divergence.max():.6f}")
    print(f"  평균값: {divergence.mean():.6f}")
    print(f"  표준편차: {divergence.std():.6f}")
    
    # 회전 통계
    curl = analysis_result['curl']
    print(f"\n회전 통계:")
    print(f"  최소값: {curl.min():.6f}")
    print(f"  최대값: {curl.max():.6f}")
    print(f"  평균값: {curl.mean():.6f}")
    print(f"  표준편차: {curl.std():.6f}")
    
    # 시각화
    output_dir = Path("./output")
    output_dir.mkdir(exist_ok=True)
    
    print(f"\n시각화 저장 중... ({output_dir})")
    visualizer = GridVisualizer(analyzer)
    visualizer.plot_all(analysis_result, save_dir=str(output_dir))
    
    print("완료!")
    print()


def demo_multiple_masses():
    """여러 질량 데모"""
    print("=" * 60)
    print("여러 질량 데모")
    print("=" * 60)
    
    # 여러 질량 생성
    masses = [
        (np.array([-2.0, 0.0]), 1.0),  # 왼쪽 질량
        (np.array([2.0, 0.0]), 1.0),    # 오른쪽 질량
    ]
    gravity_potential = create_gravity_potential(masses, G=1.0)
    
    # 그리드 분석
    analyzer = GridAnalyzer(
        x_range=(-5.0, 5.0),
        y_range=(-5.0, 5.0),
        grid_size=(100, 100),
    )
    
    print("분석 수행 중...")
    analysis_result = analyzer.analyze(
        potential_func=gravity_potential,
        epsilon=1e-6,
    )
    
    # 시각화
    output_dir = Path("./output")
    output_dir.mkdir(exist_ok=True)
    
    print(f"시각화 저장 중... ({output_dir})")
    visualizer = GridVisualizer(analyzer)
    visualizer.plot_all(analysis_result, save_dir=str(output_dir))
    
    print("완료!")
    print()


def demo_composite_potential():
    """합성 퍼텐셜 데모"""
    print("=" * 60)
    print("합성 퍼텐셜 데모")
    print("=" * 60)
    
    # 중력 퍼텐셜
    gravity_masses = [
        (np.array([0.0, 0.0]), 1.0),
    ]
    gravity_potential = create_gravity_potential(gravity_masses, G=1.0)
    
    # 커스텀 퍼텐셜 (단순 조화 진동)
    def harmonic_potential(x: np.ndarray) -> float:
        """조화 진동 퍼텐셜: V(x) = (1/2) * k * ||x||^2"""
        k = 0.1
        return 0.5 * k * np.dot(x, x)
    
    # 합성 퍼텐셜
    composite_potential = create_composite_potential(
        gravity_func=gravity_potential,
        custom_funcs=[harmonic_potential],
    )
    
    # 그리드 분석
    analyzer = GridAnalyzer(
        x_range=(-5.0, 5.0),
        y_range=(-5.0, 5.0),
        grid_size=(100, 100),
    )
    
    print("분석 수행 중...")
    analysis_result = analyzer.analyze(
        potential_func=composite_potential,
        epsilon=1e-6,
    )
    
    # 시각화
    output_dir = Path("./output")
    output_dir.mkdir(exist_ok=True)
    
    print(f"시각화 저장 중... ({output_dir})")
    visualizer = GridVisualizer(analyzer)
    visualizer.plot_all(analysis_result, save_dir=str(output_dir))
    
    print("완료!")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Potential Field Engine 데모")
    print("=" * 60 + "\n")
    
    # 1. 중력장 데모
    demo_gravity_field()
    
    # 2. 그리드 분석 데모
    demo_grid_analysis()
    
    # 3. 여러 질량 데모
    demo_multiple_masses()
    
    # 4. 합성 퍼텐셜 데모
    demo_composite_potential()
    
    print("=" * 60)
    print("모든 데모 완료!")
    print("=" * 60)

