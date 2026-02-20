# PotentialFieldEngine 파일 구조

## 📁 메인 디렉토리 (필수 파일만)

```
PotentialField_Engine/
├── README.md                        # 메인 문서 (필수)
├── .gitignore                       # Git 설정
├── __init__.py                      # 모듈 초기화 (필수)
├── CONFIG.py                        # 설정 (모든 상수 정의)
├── potential_field_engine.py        # 핵심 엔진 (필수)
├── gravity_field.py                 # 중력장 구현 (필수)
├── grid_analyzer.py                 # 그리드 분석 (필수)
└── well_formation_integration.py    # WellFormationEngine 연계 (필수)
```

## 📚 docs/ 폴더 (문서)

```
docs/
├── README.md                        # 문서 폴더 안내
├── CONCEPT.md                       # 핵심 개념
├── CONCEPT_REFERENCES.md            # 개념 및 논문 출처
├── IMPLEMENTATION_SUMMARY.md        # 구현 요약
├── BUGFIX_SUMMARY.md                # 버그 수정 요약
├── REFACTORING_SUMMARY.md           # 리팩토링 요약
├── COMPLIANCE_REPORT.md             # 규약 준수 보고서
├── COMPLETENESS_REPORT.md           # 완성도 보고서
├── FINAL_REVIEW.md                  # 최종 검토
├── FINAL_VERIFICATION.md            # 최종 검증
├── PHAM_SIGNATURE.md                # PHAM 블록체인 서명
├── PRE_RELEASE_CHECKLIST.md         # 업로드 전 체크리스트
└── UPLOAD_COMPLETE.md               # 업로드 완료 보고서
```

## 🎯 examples/ 폴더 (예제 및 데모)

```
examples/
├── README.md                        # 예제 폴더 안내
├── test_demo.py                     # 기본 테스트 및 데모
└── demo_analytical_field.py         # 해석적 필드 궤도 운동 데모
```

---

## 📊 파일 통계

- **메인 파일**: 8개 (필수 파일만)
- **문서**: 13개 (docs 폴더)
- **예제**: 3개 (examples 폴더)
- **총 파일 수**: 24개

---

## 🎯 정리 원칙

1. **메인 디렉토리**: 핵심 소스 코드와 메인 README만
2. **docs 폴더**: 모든 문서 파일
3. **examples 폴더**: 예제 및 데모 파일

