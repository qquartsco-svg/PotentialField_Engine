"""인지적 태양계 데모: 코어(중력) - 공간(필드) - 방향(벡터)

개념:
- 필드(Field) = 공간 (시공간 다양체): 데이터가 존재하고 움직일 수 있는 '무대'
- 벡터(Vector) = 방향 (흐름의 가이드): 공간 내의 한 지점에서 다음 지점으로의 방향
- 중력(Gravity) = 코어 (질량과 질서의 원천): 공간을 왜곡시켜 벡터들이 자신을 향하게 만드는 중심점

이 데모는 코어(중력)를 추가하여 공간(필드)의 방향(벡터)이 어떻게 변하는지 시각화합니다.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 백엔드 설정 (GUI 없이 실행)
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# 상위 디렉토리를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from gravity_field import create_gravity_potential
from grid_analyzer import GridAnalyzer, GridVisualizer


def demo_core_space_direction():
    """코어(중력) - 공간(필드) - 방향(벡터) 데모"""
    
    print("=" * 70)
    print("인지적 태양계 데모: 코어(중력) - 공간(필드) - 방향(벡터)")
    print("=" * 70)
    print()
    print("개념:")
    print("  - 필드(Field) = 공간: 데이터가 존재하고 움직일 수 있는 '무대'")
    print("  - 벡터(Vector) = 방향: 공간 내의 한 지점에서 다음 지점으로의 방향")
    print("  - 중력(Gravity) = 코어: 공간을 왜곡시켜 벡터들이 자신을 향하게 만드는 중심점")
    print()
    
    # 출력 디렉토리 생성
    output_dir = Path(__file__).parent / "output" / "cognitive_solar_system"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 시나리오 1: 코어 없음 (평평한 공간)
    print("시나리오 1: 코어 없음 (평평한 공간)")
    print("-" * 70)
    demo_no_core(output_dir / "01_no_core")
    
    # 시나리오 2: 단일 코어 (태양)
    print("\n시나리오 2: 단일 코어 (태양)")
    print("-" * 70)
    demo_single_core(output_dir / "02_single_core")
    
    # 시나리오 3: 이중 코어 (태양계)
    print("\n시나리오 3: 이중 코어 (태양계)")
    print("-" * 70)
    demo_dual_core(output_dir / "03_dual_core")
    
    # 시나리오 4: 다중 코어 (복잡한 인지 공간)
    print("\n시나리오 4: 다중 코어 (복잡한 인지 공간)")
    print("-" * 70)
    demo_multi_core(output_dir / "04_multi_core")
    
    print("\n" + "=" * 70)
    print("데모 완료!")
    print(f"결과물 저장 위치: {output_dir}")
    print("=" * 70)


def demo_no_core(output_dir):
    """코어 없음: 평평한 공간"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 평평한 퍼텐셜 (코어 없음)
    def flat_potential(x):
        return 0.0  # 평평한 공간
    
    # 그리드 분석
    analyzer = GridAnalyzer(
        x_range=(-5.0, 5.0),
        y_range=(-5.0, 5.0),
        grid_size=(100, 100),
    )
    
    analysis = analyzer.analyze(flat_potential, epsilon=1e-6)
    visualizer = GridVisualizer(analyzer)
    
    # 시각화
    visualizer.plot_potential(
        analysis["potential_map"],
        title="공간(필드): 코어 없음 - 평평한 공간",
        save_path=str(output_dir / "potential.png"),
    )
    
    visualizer.plot_field(
        analysis["field_x"],
        analysis["field_y"],
        title="방향(벡터): 코어 없음 - 방향 없음",
        save_path=str(output_dir / "field.png"),
    )
    
    print("  ✅ 평평한 공간: 방향(벡터)이 거의 없음")


def demo_single_core(output_dir):
    """단일 코어: 태양"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 단일 코어 (중심에 질량)
    masses = [
        (np.array([0.0, 0.0]), 2.0),  # 중심에 큰 질량
    ]
    gravity_potential = create_gravity_potential(masses, G=1.0)
    
    # 그리드 분석
    analyzer = GridAnalyzer(
        x_range=(-5.0, 5.0),
        y_range=(-5.0, 5.0),
        grid_size=(100, 100),
    )
    
    analysis = analyzer.analyze(gravity_potential, epsilon=1e-6)
    visualizer = GridVisualizer(analyzer)
    
    # 시각화
    visualizer.plot_potential(
        analysis["potential_map"],
        title="공간(필드): 단일 코어 - 중심으로 굴곡",
        save_path=str(output_dir / "potential.png"),
    )
    
    visualizer.plot_field(
        analysis["field_x"],
        analysis["field_y"],
        title="방향(벡터): 단일 코어 - 중심으로 수렴",
        save_path=str(output_dir / "field.png"),
    )
    
    visualizer.plot_divergence(
        analysis["divergence"],
        title="코어 탐지: 발산 분석 (싱크 영역)",
        save_path=str(output_dir / "divergence.png"),
    )
    
    print("  ✅ 단일 코어: 모든 방향(벡터)이 코어(중심)로 수렴")
    print("  ✅ 발산 분석: 코어 위치에서 싱크 영역 탐지")


def demo_dual_core(output_dir):
    """이중 코어: 태양계"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 이중 코어 (두 개의 질량)
    masses = [
        (np.array([-2.0, 0.0]), 2.0),  # 왼쪽 코어
        (np.array([2.0, 0.0]), 1.5),  # 오른쪽 코어
    ]
    gravity_potential = create_gravity_potential(masses, G=1.0)
    
    # 그리드 분석
    analyzer = GridAnalyzer(
        x_range=(-5.0, 5.0),
        y_range=(-5.0, 5.0),
        grid_size=(100, 100),
    )
    
    analysis = analyzer.analyze(gravity_potential, epsilon=1e-6)
    visualizer = GridVisualizer(analyzer)
    
    # 시각화
    visualizer.plot_potential(
        analysis["potential_map"],
        title="공간(필드): 이중 코어 - 두 개의 우물",
        save_path=str(output_dir / "potential.png"),
    )
    
    visualizer.plot_field(
        analysis["field_x"],
        analysis["field_y"],
        title="방향(벡터): 이중 코어 - 경쟁하는 수렴",
        save_path=str(output_dir / "field.png"),
    )
    
    visualizer.plot_divergence(
        analysis["divergence"],
        title="코어 탐지: 발산 분석 (두 개의 싱크)",
        save_path=str(output_dir / "divergence.png"),
    )
    
    print("  ✅ 이중 코어: 방향(벡터)이 두 코어 중 가까운 쪽으로 수렴")
    print("  ✅ 발산 분석: 두 개의 싱크 영역 탐지")


def demo_multi_core(output_dir):
    """다중 코어: 복잡한 인지 공간"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 다중 코어 (여러 개의 질량)
    masses = [
        (np.array([-2.0, -2.0]), 1.5),  # 좌하단 코어
        (np.array([2.0, -2.0]), 1.0),   # 우하단 코어
        (np.array([0.0, 2.0]), 2.0),    # 상단 코어 (가장 강함)
        (np.array([-1.0, 0.0]), 0.8),   # 좌측 코어
        (np.array([1.0, 0.0]), 0.8),    # 우측 코어
    ]
    gravity_potential = create_gravity_potential(masses, G=1.0)
    
    # 그리드 분석
    analyzer = GridAnalyzer(
        x_range=(-5.0, 5.0),
        y_range=(-5.0, 5.0),
        grid_size=(150, 150),  # 더 높은 해상도
    )
    
    analysis = analyzer.analyze(gravity_potential, epsilon=1e-6)
    visualizer = GridVisualizer(analyzer)
    
    # 시각화
    visualizer.plot_potential(
        analysis["potential_map"],
        title="공간(필드): 다중 코어 - 복잡한 지형",
        save_path=str(output_dir / "potential.png"),
    )
    
    visualizer.plot_field(
        analysis["field_x"],
        analysis["field_y"],
        title="방향(벡터): 다중 코어 - 복잡한 흐름",
        save_path=str(output_dir / "field.png"),
    )
    
    visualizer.plot_divergence(
        analysis["divergence"],
        title="코어 탐지: 발산 분석 (다중 싱크)",
        save_path=str(output_dir / "divergence.png"),
    )
    
    visualizer.plot_curl(
        analysis["curl"],
        title="비보존 성분: 회전 분석",
        save_path=str(output_dir / "curl.png"),
    )
    
    print("  ✅ 다중 코어: 방향(벡터)이 가장 가까운/강한 코어로 수렴")
    print("  ✅ 발산 분석: 여러 개의 싱크 영역 탐지")
    print("  ✅ 복잡한 인지 공간: 여러 기억/의도가 경쟁하는 구조")


def demo_core_addition_comparison(output_dir):
    """코어 추가 전후 비교"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 코어 없음
    def flat_potential(x):
        return 0.0
    
    # 코어 추가
    masses = [
        (np.array([0.0, 0.0]), 2.0),
    ]
    gravity_potential = create_gravity_potential(masses, G=1.0)
    
    analyzer = GridAnalyzer(
        x_range=(-5.0, 5.0),
        y_range=(-5.0, 5.0),
        grid_size=(100, 100),
    )
    
    # 코어 없음 분석
    analysis_no_core = analyzer.analyze(flat_potential, epsilon=1e-6)
    
    # 코어 추가 분석
    analysis_with_core = analyzer.analyze(gravity_potential, epsilon=1e-6)
    
    visualizer = GridVisualizer(analyzer)
    
    # 비교 시각화
    fig, axes = plt.subplots(2, 2, figsize=(16, 16))
    
    # 코어 없음 - 필드
    ax = axes[0, 0]
    step = 5
    ax.quiver(
        analyzer.x_grid[::step, ::step],
        analyzer.y_grid[::step, ::step],
        analysis_no_core["field_x"][::step, ::step],
        analysis_no_core["field_y"][::step, ::step],
        scale=1.0,
        angles='xy',
        scale_units='xy',
    )
    ax.set_title("코어 없음: 방향(벡터) 거의 없음")
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')
    
    # 코어 추가 - 필드
    ax = axes[0, 1]
    ax.quiver(
        analyzer.x_grid[::step, ::step],
        analyzer.y_grid[::step, ::step],
        analysis_with_core["field_x"][::step, ::step],
        analysis_with_core["field_y"][::step, ::step],
        scale=1.0,
        angles='xy',
        scale_units='xy',
    )
    ax.set_title("코어 추가: 방향(벡터)이 코어로 수렴")
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')
    
    # 코어 없음 - 발산
    ax = axes[1, 0]
    im = ax.contourf(
        analyzer.x_grid,
        analyzer.y_grid,
        analysis_no_core["divergence"],
        levels=50,
        cmap='RdBu_r',
    )
    ax.set_title("코어 없음: 발산 거의 없음")
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    plt.colorbar(im, ax=ax, label='∇·g')
    ax.grid(True, alpha=0.3)
    
    # 코어 추가 - 발산
    ax = axes[1, 1]
    im = ax.contourf(
        analyzer.x_grid,
        analyzer.y_grid,
        analysis_with_core["divergence"],
        levels=50,
        cmap='RdBu_r',
    )
    ax.set_title("코어 추가: 싱크 영역 탐지 (코어 위치)")
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    plt.colorbar(im, ax=ax, label='∇·g')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(str(output_dir / "comparison.png"), dpi=150, bbox_inches='tight')
    plt.close()
    
    print("  ✅ 코어 추가 전후 비교 완료")


if __name__ == "__main__":
    # 메인 데모 실행
    demo_core_space_direction()
    
    # 코어 추가 전후 비교
    print("\n" + "=" * 70)
    print("코어 추가 전후 비교")
    print("=" * 70)
    output_dir = Path(__file__).parent / "output" / "cognitive_solar_system" / "00_comparison"
    demo_core_addition_comparison(output_dir)
    
    print("\n" + "=" * 70)
    print("모든 데모 완료!")
    print("=" * 70)

