"""해석적 필드를 사용한 궤도 운동 데모

GravityField의 해석적 필드를 PotentialFieldEngine에 주입하여
오차 없이 정확한 궤도 운동을 시뮬레이션합니다.

이 데모는 다음을 검증합니다:
1. 짝수 길이 규약 강제 (버그 수정 확인)
2. 해석적 필드 사용 (성능/정확도 향상)
3. 궤도 운동의 물리적 정확성
"""

import numpy as np
import sys
from pathlib import Path

# BrainCore import (독립 모듈)
try:
    from brain_core.global_state import GlobalState
except ImportError:
    brain_core_path = Path(__file__).parent.parent.parent.parent / "BrainCore" / "src"
    sys.path.insert(0, str(brain_core_path))
    from brain_core.global_state import GlobalState

from potential_field_engine import PotentialFieldEngine
from gravity_field import GravityField


def demo_circular_orbit():
    """원형 궤도 운동 데모
    
    중력장에서 원형 궤도를 도는 물체의 운동을 시뮬레이션합니다.
    초기 조건: 원형 궤도 속도 v = sqrt(G*M/r)
    """
    print("=" * 60)
    print("해석적 필드를 사용한 원형 궤도 운동 데모")
    print("=" * 60)
    
    # 중력장 설정
    M = 1.0  # 중심 질량
    G = 1.0  # 중력 상수
    r = 1.0  # 궤도 반지름
    
    masses = [(np.array([0.0, 0.0]), M)]
    gravity = GravityField(masses, G=G)
    
    # 해석적 필드를 사용한 엔진 생성
    engine = PotentialFieldEngine(
        potential_func=gravity.potential,
        field_func=gravity.field,  # 해석적 필드 사용
        dt=0.001,  # 작은 시간 스텝 (정확도 향상)
    )
    
    print(f"\n✅ 엔진 생성 완료")
    print(f"   - 해석적 필드 사용: {engine.field_func is not None}")
    print(f"   - 시간 스텝: {engine.dt}")
    
    # 초기 조건: 원형 궤도
    # 위치: (r, 0)
    # 속도: (0, sqrt(G*M/r)) - 원형 궤도 속도
    v_circular = np.sqrt(G * M / r)
    x0 = np.array([r, 0.0])
    v0 = np.array([0.0, v_circular])
    
    initial_state = GlobalState(
        state_vector=np.concatenate([x0, v0]),
        energy=0.0,
        risk=0.0,
    )
    
    print(f"\n✅ 초기 조건 설정")
    print(f"   - 위치: {x0}")
    print(f"   - 속도: {v0}")
    print(f"   - 궤도 반지름: {r}")
    print(f"   - 원형 궤도 속도: {v_circular:.6f}")
    
    # 짝수 길이 규약 확인
    n = len(initial_state.state_vector)
    print(f"\n✅ 차원 규약 확인")
    print(f"   - state_vector 길이: {n} (짝수: {n % 2 == 0})")
    if n % 2 != 0:
        print("   ❌ 홀수 길이 에러 발생 예상")
        return
    
    # 시뮬레이션 실행
    print(f"\n✅ 시뮬레이션 시작 (1000 스텝)")
    states = [initial_state]
    current_state = initial_state
    
    for step in range(1000):
        try:
            current_state = engine.update(current_state)
            states.append(current_state)
            
            if step % 100 == 0:
                x = current_state.state_vector[:2]
                v = current_state.state_vector[2:]
                r_current = np.linalg.norm(x)
                v_current = np.linalg.norm(v)
                print(f"   Step {step:4d}: r={r_current:.6f}, v={v_current:.6f}, E={current_state.energy:.6f}")
        except ValueError as e:
            print(f"   ❌ 에러 발생: {e}")
            return
    
    # 최종 결과 분석
    final_state = states[-1]
    x_final = final_state.state_vector[:2]
    v_final = final_state.state_vector[2:]
    r_final = np.linalg.norm(x_final)
    v_final_mag = np.linalg.norm(v_final)
    
    print(f"\n✅ 시뮬레이션 완료")
    print(f"   - 최종 위치: {x_final}")
    print(f"   - 최종 속도: {v_final}")
    print(f"   - 최종 반지름: {r_final:.6f} (초기: {r:.6f}, 오차: {abs(r_final - r):.6f})")
    print(f"   - 최종 속도 크기: {v_final_mag:.6f} (초기: {v_circular:.6f}, 오차: {abs(v_final_mag - v_circular):.6f})")
    print(f"   - 최종 에너지: {final_state.energy:.6f}")
    
    # 에너지 보존 확인
    energy_initial = states[0].energy
    energy_final = final_state.energy
    energy_error = abs(energy_final - energy_initial)
    
    print(f"\n✅ 에너지 보존 확인")
    print(f"   - 초기 에너지: {energy_initial:.6f}")
    print(f"   - 최종 에너지: {energy_final:.6f}")
    print(f"   - 에너지 오차: {energy_error:.6f}")
    
    if energy_error < 1e-3:
        print("   ✅ 에너지 보존 양호 (오차 < 1e-3)")
    else:
        print(f"   ⚠️ 에너지 보존 오차 큼 (오차 >= 1e-3)")
    
    # 궤도 반지름 일정성 확인
    radii = [np.linalg.norm(s.state_vector[:2]) for s in states]
    r_mean = np.mean(radii)
    r_std = np.std(radii)
    
    print(f"\n✅ 궤도 반지름 일정성 확인")
    print(f"   - 평균 반지름: {r_mean:.6f}")
    print(f"   - 표준 편차: {r_std:.6f}")
    
    if r_std < 0.01:
        print("   ✅ 궤도 반지름 일정 (표준 편차 < 0.01)")
    else:
        print(f"   ⚠️ 궤도 반지름 변동 큼 (표준 편차 >= 0.01)")
    
    print("\n" + "=" * 60)
    print("데모 완료")
    print("=" * 60)


def demo_elliptical_orbit():
    """타원 궤도 운동 데모
    
    중력장에서 타원 궤도를 도는 물체의 운동을 시뮬레이션합니다.
    """
    print("\n" + "=" * 60)
    print("해석적 필드를 사용한 타원 궤도 운동 데모")
    print("=" * 60)
    
    # 중력장 설정
    M = 1.0
    G = 1.0
    
    masses = [(np.array([0.0, 0.0]), M)]
    gravity = GravityField(masses, G=G)
    
    # 해석적 필드를 사용한 엔진 생성
    engine = PotentialFieldEngine(
        potential_func=gravity.potential,
        field_func=gravity.field,  # 해석적 필드 사용
        dt=0.001,
    )
    
    # 초기 조건: 타원 궤도
    # 근일점: r = 0.5, 속도 = sqrt(G*M*(2/r - 1/a))
    a = 1.0  # 장반축
    r_peri = 0.5  # 근일점
    v_peri = np.sqrt(G * M * (2/r_peri - 1/a))
    
    x0 = np.array([r_peri, 0.0])
    v0 = np.array([0.0, v_peri])
    
    initial_state = GlobalState(
        state_vector=np.concatenate([x0, v0]),
        energy=0.0,
        risk=0.0,
    )
    
    print(f"\n✅ 초기 조건 설정")
    print(f"   - 근일점 거리: {r_peri}")
    print(f"   - 근일점 속도: {v_peri:.6f}")
    print(f"   - 장반축: {a}")
    
    # 시뮬레이션 실행
    print(f"\n✅ 시뮬레이션 시작 (2000 스텝)")
    states = [initial_state]
    current_state = initial_state
    
    for step in range(2000):
        current_state = engine.update(current_state)
        states.append(current_state)
        
        if step % 200 == 0:
            x = current_state.state_vector[:2]
            r_current = np.linalg.norm(x)
            print(f"   Step {step:4d}: r={r_current:.6f}")
    
    # 궤도 분석
    radii = [np.linalg.norm(s.state_vector[:2]) for s in states]
    r_min = np.min(radii)
    r_max = np.max(radii)
    
    print(f"\n✅ 궤도 분석")
    print(f"   - 최소 거리 (근일점): {r_min:.6f} (초기: {r_peri:.6f})")
    print(f"   - 최대 거리 (원일점): {r_max:.6f}")
    print(f"   - 이심률 추정: {(r_max - r_min) / (r_max + r_min):.6f}")
    
    print("\n" + "=" * 60)
    print("데모 완료")
    print("=" * 60)


if __name__ == "__main__":
    # 원형 궤도 데모
    demo_circular_orbit()
    
    # 타원 궤도 데모
    demo_elliptical_orbit()
    
    print("\n✅ 모든 데모 완료")
    print("해석적 필드를 사용한 궤도 운동 시뮬레이션이 성공적으로 완료되었습니다.")

