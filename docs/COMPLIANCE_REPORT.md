# PotentialFieldEngine 규약 준수 보고서

**작성일**: 2026-02-20  
**작성자**: GNJz (Qquarts)  
**버전**: 0.1.0

---

## ✅ 핵심 정체성 유지

### "수액과 에너지" 기술적 실체

#### (A) 수액 = GlobalState 순환 ✅

**정의**: 모든 엔진이 같은 형태의 상태를 읽고/쓰기

**구현 확인**:
- ✅ `GlobalState`는 `state_vector`, `energy`, `risk`, `extensions` 공통 필드
- ✅ 모든 엔진이 `update(state: GlobalState) -> GlobalState` 인터페이스
- ✅ 엔진 간 직접 호출 없음, 상태를 매개로 한 간접 결합

**PotentialFieldEngine 준수**:
- ✅ `new_state = state.copy(deep=False)`: 상태 복사
- ✅ `new_state.set_extension("potential_field", {...})`: extensions에 저장
- ✅ `return new_state`: 새 상태 반환

#### (B) 에너지 = 방향성을 만드는 스칼라/함수 ✅

**정의**: 상태가 어디로 가려는지를 만드는 장치

**구현 확인**:
- ✅ `energy: float`로 기록
- ✅ 잠재함수 `V(x)` 계산
- ✅ 필드 `g(x) = -∇V(x)`로 상태 업데이트
- ✅ 에너지: `E = (1/2) * ||v||^2 + V(x)`

**PotentialFieldEngine 준수**:
- ✅ `V = self.potential_func(x)`: 퍼텐셜 계산
- ✅ `g = self._compute_field(x)`: 필드 계산
- ✅ `new_state.energy = kinetic_energy + V`: 에너지 업데이트

---

## ✅ 태양계/중력장 메타포 → 코드 매핑

### 구조적 매핑 ✅

**최소 구현 수식**:
- ✅ 잠재함수: `V(x)`
- ✅ 필드(가속도): `a(x) = -∇V(x)`
- ✅ 업데이트: `v_{t+1} = v_t + Δt * a(x_t)`
- ✅ 위치: `x_{t+1} = x_t + Δt * v_{t+1}`

**PotentialFieldEngine 구현**:
```python
# 퍼텐셜 계산
V = self.potential_func(x)

# 필드 계산 (기울기)
g = self._compute_field(x)  # g = -∇V(x)

# 가속도
a = g

# 속도 업데이트
v_new = v + self.dt * a

# 위치 업데이트
x_new = x + self.dt * v_new

# 에너지
E = (1/2) * ||v_new||^2 + V
```

---

## ✅ 난류 메타포 → 코드 매핑

### 난류 지형 위에서의 운전/항해 ✅

**정의**: Navier-Stokes 직접 해결이 아니라, 난류 지형 위에서의 운전/항해

**구현 확인**:
- ✅ `GridAnalyzer`: 발산/회전 계산 (왜곡 탐지)
- ✅ 발산: `∇·g = ∂g_x/∂x + ∂g_y/∂y` (소스/싱크 구조 탐지)
- ✅ 회전: `∇×g = ∂g_y/∂x - ∂g_x/∂y` (비보존력 영역 탐지)
- ✅ 연구용 도구: 실행 루프와 분리된 시각화 유틸리티

**PotentialFieldEngine 준수**:
- ✅ `GridAnalyzer`는 실행 루프 밖에서 사용
- ✅ `risk_map`으로 위험 영역 표현 가능
- ✅ `well`로 안정 경로 학습 가능

---

## ✅ 줄기 보호 (위험 포인트 제거)

### (1) MultiScaleGlobalState 배제 ✅

**문제**: 단일 GlobalState 철학을 깨고, 디버깅/일관성 비용 폭증

**해결**:
- ✅ 단일 `GlobalState` 유지
- ✅ `extensions`로 스케일/엔진별 산출물 축적
- ✅ MultiScaleGlobalState 도입 안 함

### (2) GlobalState Extensions API ✅

**요구사항**: `set_extension()`, `get_extension()` 표준 메서드

**확인 결과**:
- ✅ `BrainCore/src/brain_core/global_state.py`에 이미 구현됨
- ✅ `set_extension(engine_name, data)`: 확장 데이터 설정
- ✅ `get_extension(engine_name, default)`: 확장 데이터 조회
- ✅ `update_extension(engine_name, **kwargs)`: 부분 업데이트

**PotentialFieldEngine 사용**:
- ✅ `new_state.set_extension("potential_field", {...})`: 필드 정보 저장

### (3) 하드코딩 금지 규약 ✅

**문제**: `epsilon=1e-6`, `dt=0.01` 등이 여러 파일에 하드코딩됨

**해결**:
- ✅ `CONFIG.py` 생성: 모든 상수를 한 곳에서 관리
- ✅ 모든 파일에서 CONFIG import하여 기본값 사용
- ✅ 파라미터로 오버라이드 가능하도록 유지

**변경 파일**:
- ✅ `potential_field_engine.py`: `dt`, `epsilon` → CONFIG 사용
- ✅ `gravity_field.py`: `G`, `softening` → CONFIG 사용
- ✅ `grid_analyzer.py`: `epsilon`, `grid_size`, `x_range`, `y_range` → CONFIG 사용

---

## ✅ 설계 원칙 준수

### 불변성 유지 ✅

- ✅ `new_state = state.copy(deep=False)`: 상태 복사
- ✅ 직접 mutate 없음
- ✅ `new_state` 반환

### 하드코딩 제거 ✅

- ✅ 모든 상수를 CONFIG로 이동
- ✅ 기본값은 CONFIG에서만 정의
- ✅ 파라미터로 오버라이드 가능

### BrainCore 철학 유지 ✅

- ✅ 단일 GlobalState (MultiScaleGlobalState 배제)
- ✅ extensions에 필드 정보 저장
- ✅ 엔진은 `update(state)` → `new_state` 반환

---

## 📊 최종 검증

### 코드 품질
- [x] 하드코딩 제거: 모든 상수를 CONFIG로 이동
- [x] GlobalState Extensions API: 이미 구현되어 있음
- [x] 불변성 유지: copy-and-return 패턴 준수
- [x] 단일 GlobalState: MultiScaleGlobalState 배제
- [x] 설계 원칙 일관성: 모든 파일에서 준수

### 메타포 → 코드 매핑
- [x] 수액 (GlobalState 순환): 구현 완료
- [x] 에너지 (방향성): 구현 완료
- [x] 태양계/중력장: 구조적 매핑 완료
- [x] 난류: 지형 위에서의 운전/항해로 구현

### 줄기 보호
- [x] MultiScaleGlobalState 배제
- [x] Extensions API 표준화
- [x] 하드코딩 금지 규약 일관성

---

## 🎯 결론

**핵심 정체성 유지**: ✅
- BrainCore는 컨트롤러가 아니라, 단일 GlobalState 위에서 엔진들이 perturb를 누적하는 상태계

**방향성 유지**: ✅
- "큰 줄기 + 언제든 디테일 확장"
- 줄기를 보호하며 가지를 뻗는 구조

**규약 준수**: ✅
- 모든 설계 원칙 일관되게 준수
- 하드코딩 제거 완료
- Extensions API 표준화 완료

---

**작성자**: GNJz (Qquarts)  
**상태**: 규약 준수 확인 완료 ✅

