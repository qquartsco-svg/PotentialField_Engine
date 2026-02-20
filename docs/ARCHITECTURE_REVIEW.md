# PotentialFieldEngine 구조 재검토 보고서

**작성일**: 2026-02-20  
**작성자**: GNJz (Qquarts)  
**버전**: 0.1.0

---

## 🔵 전체 판단

### 현재 상태

**구조**: ✅ 안정화 단계에 들어감

**완성도**:
- 🔴 "물리엔진급 완성도"는 아직 아님
- 🟢 "상태 동역학 + 퍼텐셜 필드 실험 플랫폼"으로는 충분히 일관성 있음

**줄기 흔들림**: ✅ 없음

---

## 1️⃣ 전체 구조 재확인

### 3계층 구조

```
GlobalState (BrainCore)
    ↑
PotentialFieldEngine  ← 상태 업데이트
    ↑
Potential 함수 (gravity / well / composite)
    ↑
GridAnalyzer (연구용 분석)
```

### 책임 분리

- ✅ **실행 루프**: PotentialFieldEngine
- ✅ **분석/시각화**: GridAnalyzer (실행 루프와 분리)
- ✅ **물리식**: gravity_field
- ✅ **상수**: CONFIG

**결론**: ✅ 책임 분리 완벽함, 줄기 흔들림 없음

---

## 2️⃣ PotentialFieldEngine 재검토

### ✅ 좋은 점

- ✅ copy-and-return 유지
- ✅ CONFIG 사용
- ✅ extensions 사용
- ✅ 수학식 일관성 있음
- ✅ BrainCore 철학 유지

**결론**: ✅ 잘 정리됨

### ⚠️ 남은 구조 리스크

#### (1) state_vector 차원 규약 명문화 필요

**현재 상태**:
- ✅ 코드에서 `n % 2 != 0` 체크 구현됨
- ⚠️ 문서에 명시되어 있지 않음

**필요 작업**:
- README.md에 규약 명시
- `__init__.py` docstring에 규약 명시

**규약**:
```
GlobalState.state_vector MUST be 2N dimensional.
- First N: position [x1, x2, ..., xN]
- Last N: velocity [v1, v2, ..., vN]
```

#### (2) 수치 gradient 비용 문제

**현재 상태**:
- ✅ `field_func` 파라미터 추가됨
- ✅ 해석적 필드 우선 사용, 없으면 수치 미분 fallback

**결론**: ✅ 이미 해결됨

---

## 3️⃣ GridAnalyzer 재검토

### ✅ 좋은 점

- ✅ 실행 루프와 분리
- ✅ 연구용 도구로 명확히 구분
- ✅ 시각화 optional
- ✅ CONFIG 사용

**결론**: ✅ 설계적으로 좋음

### ⚠️ 중요한 부분

#### meshgrid indexing 문제

**현재 상태**:
- ✅ `np.meshgrid(..., indexing='ij')` 사용됨
- ✅ shape 일치 확인됨

**결론**: ✅ 이미 수정됨

#### divergence 해석 문구

**현재 상태**:
- ✅ 물리적으로 정확한 의미로 수정됨
- ✅ "소스/싱크 또는 라플라시안 구조"로 완화됨

**결론**: ✅ 이미 수정됨

---

## 4️⃣ gravity_field 재확인

### ✅ 좋은 점

- ✅ softening 도입 (수치 안정성)
- ✅ potential + field 동시 계산 가능
- ✅ composite 함수 있음
- ✅ CONFIG 사용

**결론**: ✅ 깔끔함

### ⚠️ 미세한 수학적 디테일

#### Softening 방식

**현재**:
```python
if r < softening:
    r = softening  # 급격한 절단
```

**정확한 Plummer softening**:
```python
r = sqrt(|x - x_i|^2 + epsilon^2)
```

**판단**:
- ✅ 지금 단계에서는 문제 없음
- ⚠️ 천체물리 수준 정확도 필요 시 교체 필요

---

## 5️⃣ CONFIG 구조

### ✅ 좋은 점

- ✅ 모든 상수 한 곳에서 관리
- ✅ 파라미터로 오버라이드 가능

### ⚠️ 로깅 전략

**현재**: `DEFAULT_ENABLE_LOGGING = True`

**권장**:
- production 모드: False
- research 모드: True
- BrainCore 모드와 연동

---

## 6️⃣ 전체 일관성 평가

| 항목 | 상태 | 비고 |
|------|------|------|
| 단일 GlobalState 유지 | ✅ | 완벽 |
| copy-and-return | ✅ | 완벽 |
| extensions 규약 | ✅ | 완벽 |
| 하드코딩 제거 | ✅ | 완벽 |
| 모듈 책임 분리 | ✅ | 완벽 |
| 수학적 정합성 | ⚠️ | 약간의 개선 여지 |
| 수치 안정성 | ⚠️ | gradient 비용 / meshgrid |

---

## 🎯 핵심 결론

### 현재 상태

🟢 **"연구용 퍼텐셜 기반 상태 동역학 실험 플랫폼"**으로는 충분히 안정적

🔵 **"물리 엔진"**이라고 부르기엔 수치 최적화가 덜 됨

✅ **줄기 흔들림은 전혀 없음**

---

## 🔥 다음 단계 제안

### 이미 완료된 작업 ✅

1. ✅ meshgrid indexing 수정 (`indexing='ij'`)
2. ✅ field_func 옵션 추가 (해석적 필드 지원)
3. ✅ divergence 문구 완화 (물리적으로 정확한 의미)
4. ✅ state_vector 차원 규약 강제 (코드 레벨)

### 남은 작업 ⚠️

1. ⚠️ **state_vector 규약 명문화** (문서에 명시)
2. ⚠️ **로깅 전략 개선** (BrainCore 모드 연동)
3. ⚠️ **Plummer softening** (선택적, 천체물리 수준 필요 시)

---

## 🚀 안정화 단계 완료를 위한 최소 작업

### 필수 작업

1. **README.md에 state_vector 규약 명시**
   - 형식: `[x1, ..., xN, v1, ..., vN]` (2N 차원)
   - 홀수 길이 시 `ValueError` 발생

2. **`__init__.py` docstring에 규약 명시**
   - 모듈 레벨에서 규약 확인 가능

### 선택적 작업

1. **로깅 전략 개선** (BrainCore 연동)
2. **Plummer softening** (정밀도 향상 필요 시)

---

## 📊 최종 평가

### 구조 안정성: ✅ 매우 안정적

- 줄기 흔들림 없음
- 책임 분리 완벽
- 설계 원칙 일관성

### 수학적 정합성: ⚠️ 대부분 완료, 문서화 필요

- 코드 레벨 수정 완료
- 문서 명시 필요

### 수치 안정성: ⚠️ 기본 완료, 선택적 개선 가능

- 해석적 필드 지원 완료
- Plummer softening은 선택적

---

**작성자**: GNJz (Qquarts)  
**상태**: 구조 안정화 단계 ✅

