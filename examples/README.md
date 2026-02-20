# PotentialFieldEngine 예제

이 폴더에는 PotentialFieldEngine의 사용 예제와 데모가 포함되어 있습니다.

## 📖 예제 목록

### test_demo.py
기본 테스트 및 데모:
- 중력장 데모
- 그리드 분석 데모
- 왜곡 탐지 데모

**실행 방법**:
```bash
python3 test_demo.py
```

### demo_analytical_field.py
해석적 필드를 사용한 궤도 운동 데모:
- 원형 궤도 운동 시뮬레이션
- 타원 궤도 운동 시뮬레이션
- 에너지 보존 확인
- 궤도 반지름 일정성 확인

**실행 방법**:
```bash
python3 demo_analytical_field.py
```

**검증 항목**:
1. 짝수 길이 규약 강제 확인
2. 해석적 필드 사용 확인
3. 궤도 운동의 물리적 정확성
4. 에너지 보존 확인

### demo_cognitive_solar_system.py
**인지적 태양계 데모**: 코어(중력) - 공간(필드) - 방향(벡터) 개념 시각화

**개념**:
- **필드(Field) = 공간**: 데이터가 존재하고 움직일 수 있는 '무대' 그 자체
- **벡터(Vector) = 방향**: 공간 내의 한 지점에서 다음 지점으로의 방향
- **중력(Gravity) = 코어**: 공간을 왜곡시켜 벡터들이 자신을 향하게 만드는 중심점

**시나리오**:
1. **코어 없음**: 평평한 공간에서 방향(벡터)이 거의 없음
2. **단일 코어**: 모든 방향(벡터)이 코어(중심)로 수렴
3. **이중 코어**: 방향(벡터)이 두 코어 중 가까운 쪽으로 수렴
4. **다중 코어**: 복잡한 인지 공간에서 여러 기억/의도가 경쟁하는 구조

**실행 방법**:
```bash
python3 examples/demo_cognitive_solar_system.py
```

**결과물**: `examples/output/cognitive_solar_system/` 디렉토리에 저장됩니다.

---

**참고**: 메인 README.md는 프로젝트 루트에 있습니다.

