# 🍫 Phase 3 회고 — Kestra 파이프라인 Logging 개선

> **프로젝트:** Charlie's Chocolate Factory — Omnichannel Retail Data Platform  
> **단계:** Phase 3 (Kestra Orchestration) 품질 개선  
> **기록일:** 2026-11-06  
> **최종 업데이트:** 2026-11-06  
> **진행 상태:** 🟡 Logging Patch **적용 확인(실행 로그 기준)** · Square Catalog **Kestra 성공 테스트 완료** · 나머지 Flow/실패 시나리오 검증 진행 전

## 1. 지금까지 구현한 흐름

온라인 데이터와 Square API에서 수집한 원본 데이터를 Python으로 처리하여 PostgreSQL에 저장했고, Kestra로 이 적재 작업을 실행하도록 구성했다.

```text
Online Data ───────┐
                   ├─> Python ingestion ─> PostgreSQL (raw_online / raw_square)
Square API ────────┘              ▲
                                  │
                          Kestra orchestration
```

Logging Patch의 적용 대상은 다음 **Python 진입점 5개**다. `online_to_postgres.py`는 선택한 온라인 테이블을 적재하는 공통 진입점이다. 따라서 **Python 파일 5개**와 **Kestra에서 실행하는 개별 적재 작업 9개(Online 5개 + Square 4개)**는 서로 다른 집계 단위다.

| Python 파이프라인 | 담당 데이터 |
|---|---|
| `src/pipelines/online_to_postgres.py` | 온라인 데이터 → PostgreSQL |
| `src/pipelines/square_catalog_to_postgres.py` | Square 상품 카탈로그 → PostgreSQL |
| `src/pipelines/square_customers_to_postgres.py` | Square 고객 → PostgreSQL |
| `src/pipelines/square_locations_to_postgres.py` | Square 매장 → PostgreSQL |
| `src/pipelines/square_orders_to_postgres.py` | Square 주문 → PostgreSQL |

이전 Phase 3 작업에서는 **상위 Flow(Parent Flow)**가 Online 5개와 Square 4개의 개별 Flow를 호출하도록 구성하고, 전체 9개 적재 작업의 순차 실행을 확인한 기록이 있다. 이번 Logging Patch 적용 **이후** 상위 Flow 전체를 다시 실행한 결과는 아직 공유되지 않았다.

**아직 진행하지 않은 단계:** PostgreSQL → GCS 업로드, GCS → BigQuery 적재, BigQuery에서 dbt의 Staging → Intermediate → Marts 모델링.

## 2. 문제를 깨달은 계기: “실행됐다”와 “정상적으로 처리됐다”는 다르다

Kestra를 학습하고 실제 파이프라인을 실행하면서, **Kestra UI에서 작업이 성공했는지뿐 아니라 어디서, 왜 실패했는지 바로 알 수 있어야 한다**는 점을 느꼈다.

초기 Python 코드는 `print()` 위주로 다음과 같은 정보를 출력했다.

```python
print("[START] Square orders ingestion")
print(f"[EXTRACT] total orders: {len(orders)}")
print("[DONE] Square orders ingestion")
```

`print()` 자체가 잘못된 것은 아니다. Kestra도 표준 출력으로 전달된 내용을 보여줄 수 있다. 그러나 파이프라인이 늘어나면 다음 정보가 일정한 형식으로 남아야 문제를 추적하기 쉽다.

- **어느 단계에서** 문제가 발생했는지: Extract / Transform / Connect / Load
- **어떤 파이프라인과 실행 ID**에 해당하는지
- 처리한 데이터의 **건수**, **실행시간** 및 **성공·실패 상태**
- 실패했을 때 **오류 유형·요약 메시지·발생 위치**
- 오류가 발생하면 Kestra가 작업을 **실패로 판정**할 수 있는지

### 나의 회고

> 처음 ETL 파이프라인을 개발할 때는 **데이터를 정상적으로 가져와 PostgreSQL에 저장하는 것**에 집중했다. 당시에는 작업이 성공하는지만 확인하고, 운영 단계에서 장애를 파악할 수 있도록 로그 구조를 먼저 설계해야 한다는 점은 충분히 고려하지 못했다.
>
> 이후 Kestra를 사용하면서 데이터 파이프라인에는 **처리 로직뿐 아니라 관측 가능성(observability), 오류 처리, 데이터 품질 확인**도 중요하다는 것을 배웠다. 앞으로는 파이프라인을 작성할 때부터 Logging과 실패 처리 기준을 함께 설계하고자 한다.

## 3. 개선 방향: 공통 설정 + 개별 업무 로그

결정한 방식은 **Python 표준 `logging` 모듈을 사용하고, 공통 Logging 기능을 재사용**하는 구조다.

```text
src/pipelines/
├── run_logging.py                  # 공통 Logging 설정·도우미
├── online_to_postgres.py           # 온라인 ETL의 단계별 메시지
├── square_catalog_to_postgres.py   # Square Catalog 메시지
├── square_customers_to_postgres.py # Square Customers 메시지
├── square_locations_to_postgres.py # Square Locations 메시지
└── square_orders_to_postgres.py    # Square Orders 메시지
```

| 구분 | 책임 |
|---|---|
| 공통 `run_logging.py` | 로그 형식/레벨/출력 위치, 단계별 실행시간, 공통 메타데이터, 오류 처리 방식 |
| 개별 `*_to_postgres.py` | 어떤 업무 단계가 시작·완료되었는지, 추출·처리 건수 등 **업무 특화 메시지** |
| Kestra | Python 작업 실행, 태스크 상태 확인, 표준 출력 로그 수집 및 UI 표시 |
| Git / GitHub | 수정된 **실제 Python 소스코드**의 이력 관리 |

**중요:** 공통 설정 파일만 만들어도 모든 업무 로그가 자동 생성되는 것은 아니다. 각 파이프라인에서 기록할 지점과 내용은 명시적으로 작성해야 한다.

## 4. 작성하고 적용한 `.patch` 파일의 역할

기존 파이프라인이 여러 개이므로, 파일을 하나씩 열어 같은 Logging 코드를 반복 추가하는 대신 **변경사항을 한꺼번에 적용할 수 있는 Patch**를 준비했다. 이후 사용자가 Patch 적용을 진행했고, **2026-11-06 Kestra 로그에서 변경된 Python Logger가 실제로 실행된 사실을 확인했다.** 단, 로컬에서 실행한 정확한 `git apply` 명령과 최종 `git diff` 결과는 별도 기록이 필요하다.

- **파일명:** `kestra-pipeline-logging-improved.patch`
- **Patch의 목적:** 기존 Python 소스를 변경하고 `run_logging.py`를 새로 추가하기
- **Patch의 성격:** 실행 로그 파일이나 독립적인 설정 파일이 아닌 **코드 변경 내역(diff)**
- **적용 후:** `.patch`가 지속적으로 실행되는 것이 아니라, **변경된 Python 코드가 Logging을 수행**한다.
- **현재 확인:** Square Catalog 작업의 INFO 로그에서 `run_logging.py` 기반 단계 로그가 출력됨.

### Patch에 포함된 개선 사항

| 개선 내용 | 세부 설명 |
|---|---|
| 공통 로깅 모듈 추가 | `run_logging.py` 생성 |
| 로그 형식 통일 | 타임스탬프, 레벨, 모듈명, 메시지 |
| 단계별 상태 기록 | `stage=...`, `status=started/completed/failed` |
| 실행시간 기록 | `elapsed_seconds` 측정 |
| 실행 메타데이터 | `orchestrator`, `pipeline_run_id` 활용 |
| 오류 진단 정보 | 오류 유형, 요약 메시지, Python 파일·줄·함수 위치 |
| 실패 전파 | CLI에서 오류 발생 시 종료 코드 `1`로 Kestra에 알림 |
| 민감정보 주의 | 기본적인 오류 메시지 마스킹 로직 포함 |

적용된 코드는 `log_stage()`, `run_metadata()`, `run_cli()` 같은 공통 함수를 사용하도록 구성된다.

```python
# 개념 예시: 실제 코드에서는 기존 데이터 처리 함수를 그대로 사용
with log_stage(LOGGER, "extract", source="square", resource="orders"):
    orders = extract_orders()

LOGGER.info("stage=extract extracted_rows=%d", len(orders))
```

> **주의:** 기존 Patch의 오류 메시지 마스킹은 **최선의 노력(best effort)** 방식이다. 모든 민감정보를 완벽하게 가리지 못할 수 있으므로 API 토큰, 고객정보, 전체 요청/응답 본문 등을 로그에 기록하지 않는 것이 우선이다.

## 5. 왜 Patch와 공통 설정을 함께 쓰는가?

**Patch는 “어떻게 기존 코드를 바꿀까?”에 대한 답**이고, **공통 Logging 설정은 “변경된 코드를 앞으로 어떻게 일관되게 운영할까?”에 대한 답**이다.

```text
[한 번의 변경 작업]
Improved .patch ──git apply──> run_logging.py + 기존 5개 Python 소스 수정
                                             │
                                             ▼
[이후 매번 실행되는 구조]
Kestra ──> Python 파이프라인 ──> 공통 Logging 사용 ──> Kestra UI Logs
```

따라서 Patch를 적용한 뒤에는 별도의 Patch 파일을 계속 관리하거나 실행할 필요가 없다. 이후 기능 수정과 개선은 **실제 Python 파일을 수정하고 Git 커밋으로 관리**한다.

## 6. Patch 적용 후 Kestra 실전 테스트 (2026-11-06)

### 6.1 현재까지 확인된 상태

| 점검 항목 | 상태 | 근거 또는 남은 검증 |
|---|---|---|
| 개선 Patch 파일 준비 | ✅ 완료 | `kestra-pipeline-logging-improved.patch` |
| Patch 변경사항의 Python 실행 반영 | ✅ 확인 | Square Catalog에서 새 공통 Logging 형식 출력 |
| `git apply --check`, `git diff` 및 변경 이력 | ⚪ 추가 확인 | 구체적인 로컬 명령 결과는 전달받지 않음 |
| Kestra Docker Task Runner 실행 | ✅ 확인 | `io.kestra.plugin.scripts.runner.docker.Docker` |
| Square Catalog API 추출 및 DB Upsert | ✅ 실행 성공 | Extract 15개, Upsert 완료 메시지, exit code 0 |
| 단계별 INFO 및 실행시간 로그 | ✅ 확인 | Extract / Connect / Load / Dispose |
| Online, Square 나머지 4개 Python 진입점 재검증 | ⬜ 미확인 | 개별 Flow 실행 로그 필요 |
| Parent Flow(Online 5 + Square 4) 회귀 테스트 | ⬜ 미확인 | Patch 적용 후 새 실행 필요 |
| 오류 발생 시 실패 단계·메시지·종료 코드 1 | ⬜ 미검증 | 테스트용 안전한 실패 시나리오 필요 |
| 실제 DB 행 수/값의 별도 대조 | ⬜ 미검증 | 실행 성공 로그만으로 완전성 판단 불가 |
| Git Commit 및 Push | ⬜ 미확인 | `git status` 확인 후 수행 |

### 6.2 Square Catalog 실행 증거

**실행일:** 2026-11-06 (아래 로그 시각은 UTC)  
**Kestra 작업:** Square Catalog → PostgreSQL (`python -m src.pipelines.square_catalog_to_postgres`)  
**Task Runner:** Docker  
**실행 식별자:** `4WfkXOhKPINBTWmATTiSbx` (해당 실행에서 기록한 `pipeline_run_id`)

| 관찰 항목 | 확인된 값 |
|---|---|
| Square API 추출 | **15 items** |
| PostgreSQL 대상 | `raw_square.catalog_objects` |
| 적재 출력 | `upsert completed (15 items)` |
| 파이프라인 기록 | `processed_rows=15` |
| Extract 시간 | `0.355s` |
| Connect 시간 | `0.108s` |
| Load 시간 | `0.076s` |
| Dispose 시간 | `0.001s` |
| Python 파이프라인 전체 시간 | **`0.541s`** |
| Docker 명령 종료 | **exit code 0 (성공)** |
| Kestra output files | `Captured 0 output file(s)` — 파일 생성 작업이 아니므로 정상 |

로그 일부(실제 출력에서 핵심만 발췌):

```text
2026-11-06 23:20:05,156 INFO src.pipelines.square_catalog_to_postgres status=started orchestrator=kestra pipeline_run_id=4WfkXOhKPINBTWmATTiSbx
2026-11-06 23:20:05,156 INFO src.pipelines.square_catalog_to_postgres stage=extract status=started source=square resource=catalog
[EXTRACT] total items: 15
2026-11-06 23:20:05,511 INFO src.pipelines.square_catalog_to_postgres stage=extract status=completed source=square resource=catalog elapsed_seconds=0.355
2026-11-06 23:20:05,620 INFO src.pipelines.square_catalog_to_postgres stage=connect status=completed elapsed_seconds=0.108
[SUCCESS] raw_square.catalog_objects upsert completed (15 items)
2026-11-06 23:20:05,697 INFO src.pipelines.square_catalog_to_postgres stage=load status=completed table=raw_square.catalog_objects elapsed_seconds=0.076
2026-11-06 23:20:05,698 INFO src.pipelines.square_catalog_to_postgres status=completed pipeline_run_id=4WfkXOhKPINBTWmATTiSbx elapsed_seconds=0.541
Command succeed with exit code 0
```

> **해석:** `processed_rows=15`와 `upsert completed (15 items)`는 15개 Square 객체가 처리됐음을 나타낸다. **신규 DB 행 15개가 추가되었다는 의미는 아니다.** Upsert 특성상 기존 행이 갱신되었을 수 있으므로 DB 행 수와 주요 값을 별도로 확인해야 한다.
>
> **시간 범위:** `elapsed_seconds=0.541`은 Python 파이프라인 내부 측정 시간이다. Docker 컨테이너 생성이나 `pip install -r /project/requirements.txt` 실행 시간은 포함하지 않는다.

### 6.3 실행하면서 새로 발견한 개선 포인트

**일부 하위 모듈은 여전히 `print()`를 사용한다.** 로그에 다음 출력이 섞여 있었다.

```text
[EXTRACT] page 1: 15 items
[EXTRACT] total items: 15
[SUCCESS] raw_square.catalog_objects upsert completed (15 items)
```

이는 **상위 Python 파이프라인의 Logging 적용 실패가 아니다**. API 추출·DB 적재 내부 모듈은 여전히 이전 형식의 `print()`를 사용한 것으로 보인다. 즉시 동작에 문제는 없지만 장기적으로 해당 내부 모듈에도 `logging.getLogger(__name__)`를 적용하면 출력 형식과 로그 레벨을 통일할 수 있다.

추가 개선 후보:

- **정보성 로그와 오류 로그의 구분:** 정상 실행만 확인했으므로 `ERROR` 발생 시 로깅 및 Kestra `FAILED` 전환은 안전한 환경에서 별도 확인한다.
- **적재 건수 정밀화:** `extracted_rows`, `processed_rows`, `inserted_rows`, `updated_rows`, DB 실제 행 수는 서로 의미가 다르므로 혼동하지 않는다.
- **실행 환경 효율:** 이번 Docker Task Runner는 매번 `pip install`을 수행했다. 추후 반복 실행 비용이 커지면 검증된 의존성이 들어 있는 이미지/환경을 검토한다.
- **로그 보안:** 오류 메시지에 고객 데이터·전체 payload·인증값이 남지 않도록 검토한다. 현재 마스킹은 최선의 노력 수준이다.

### 6.4 다음에 실행할 검증 체크리스트

- [x] 개선 Patch를 반영한 Square Catalog의 단계 로그 확인
- [x] Kestra Task 종료 코드 0 및 정상 완료 확인
- [ ] `git status`, `git diff --check`, 신규 `run_logging.py` 추적 상태 확인
- [ ] **상위 Parent Flow**를 한 번 실행하여 Online 5개 + Square 4개 전체 결과 확인
- [ ] 각 **개별 Flow 실행 로그**에서 `stage=...` 및 최종 `status=completed` 확인
- [ ] 실행 후 PostgreSQL 실제 테이블/건수/샘플 데이터 검증
- [ ] 테스트 환경에서 의도적인 오류를 발생시켜 `stage=... status=failed`와 Kestra `FAILED` 확인
- [ ] 내부 추출·적재 모듈의 잔여 `print()` 정리 여부 결정
- [ ] 최종 변경사항 커밋/푸시 (미반영 문서 변경사항도 함께 점검)

**PowerShell 점검 명령(이미 Patch 적용된 경우 `git apply` 재실행 금지):**

```powershell
git status
git diff --check
git diff --stat
python -m compileall -q src/pipelines
```

> 전체 Parent Flow를 다시 실행하면 PostgreSQL의 기존 데이터가 갱신될 수 있다. 사용 중인 DB, Upsert/Truncate-Insert 정책 및 테스트용 데이터인지 먼저 확인한다.

## 7. 다음 개발에 적용할 원칙

1. **처음부터 Logging 설계하기:** 새로운 GCS 업로드·BigQuery 적재 파이프라인도 개발 초기부터 단계별 로그와 실패 처리를 넣는다.
2. **공통 기능 재사용하기:** 프로젝트에서 이미 만든 `run_logging.py`의 설정과 도우미를 활용한다.
3. **의미 있는 정보를 기록하기:** 시작/완료 여부뿐 아니라 소요시간, 건수, 실행 식별자, 실패 단계도 남긴다.
4. **오류를 조용히 무시하지 않기:** 실패를 기록하고, Kestra가 실패 상태를 인식하도록 종료 코드와 예외 흐름을 관리한다.
5. **관측과 검증을 구분하기:** 성공 로그만으로 데이터 정합성이 보장되지는 않는다. DB 결과와 데이터 품질도 별도로 검증한다.
6. **보안 고려하기:** 인증정보·개인정보·불필요한 원본 payload는 로그에 남기지 않는다.

## 8. 다음 Phase와의 연결

```text
[완료] Online / Square → PostgreSQL
          │
          ├─ [부분 검증 완료] Logging Patch 반영 · Square Catalog 성공
          ├─ [검증 예정] 나머지 Flow + Parent Flow + 실패 테스트
          ▼
[미진행] PostgreSQL → GCS (Python + Kestra)
          ▼
[미진행] GCS → BigQuery (Raw 데이터 적재)
          ▼
[미진행] BigQuery + dbt
          └─ Staging → Intermediate → Marts + Tests
```

## 9. 핵심 배움

**이전에는 “데이터가 잘 저장되면 파이프라인 개발이 끝났다”고 생각했다. 지금은 “성공과 실패를 설명할 수 있어야 운영 가능한 데이터 파이프라인”이라는 점을 이해했다.**

Logging은 개발 후에 추가하는 부가 작업이 아니라, 앞으로 데이터 엔지니어링 파이프라인을 설계할 때 처음부터 함께 고려해야 할 요소다.

---

**참고 파일:** `kestra-pipeline-logging-improved.patch`  
**다음 실습 목표:** Parent Flow 9개 적재 작업 재실행 및 단계 로그 확인 → PostgreSQL 데이터 검증 → 안전한 실패 테스트 → Git Commit
