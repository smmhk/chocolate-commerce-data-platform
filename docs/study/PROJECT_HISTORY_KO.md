# 🍫 Chocolate Commerce Data Platform — 프로젝트 개발 히스토리

> **프로젝트명:** Charlie's Chocolate Factory — Omnichannel Retail Data Platform  
> **기록 범위:** 2026년 9월 초 ~ 2026-11-09  
> **문서 버전:** 1차 회고 초안 (2026-11-09)  
> **목적:** 프로젝트의 설계·구현·실패·해결·학습 과정을 시간순으로 축적하고, 향후 Data Engineer 취업 포트폴리오와 면접 사례로 활용  
> **목표 릴리스:** `v1.0.0` — End-to-End 파이프라인과 분석 대시보드까지 검증한 첫 번째 버전

## 문서 읽는 법

이 문서는 과거 대화와 프로젝트 진행 문서를 바탕으로 재구성한 **개발 회고 기록**이다. Git 커밋, Kestra Execution, 실제 데이터베이스 상태를 모두 직접 감사한 결과는 아니다. 따라서 당시 대화에서 확인한 사실과 이후에 정리된 내용을 구분한다.

- ✅ **완료/확인:** 당시 실행 결과 또는 프로젝트 기록에서 성공을 확인한 내용
- 🟡 **진행/부분 검증:** 코드 추가·일부 실행은 확인했지만 전체 검증이 남은 내용
- 📘 **학습/설계:** 개념을 학습했거나 구현 방향을 결정했으나, 프로젝트 구현 완료는 아닌 내용
- ⬜ **예정:** 아직 구현 또는 실행 결과가 확인되지 않은 내용
- **날짜 표현:** 정확한 날짜가 불확실하면 `~`, `전후`, `중순` 등으로 표시한다. 한 날짜의 진행 문서가 그날 모든 작업이 최초 수행됐음을 뜻하지는 않는다.

---

## 목차

1. [프로젝트 개요와 비즈니스 문제](#1-프로젝트-개요와-비즈니스-문제)
2. [전체 개발 타임라인](#2-전체-개발-타임라인)
3. [9월 — 프로젝트 시작과 Square API 연동](#3-9월--프로젝트-시작과-square-api-연동)
4. [10월 — 로컬 데이터 플랫폼과 Kestra 자동화](#4-10월--로컬-데이터-플랫폼과-kestra-자동화)
5. [11월 — GCP, 데이터 품질 및 dbt 준비](#5-11월--gcp-데이터-품질-및-dbt-준비)
6. [기술별 성장 기록](#6-기술별-성장-기록)
7. [문제 해결 사례 모음](#7-문제-해결-사례-모음)
8. [2026-11-09 기준 실제 완료 범위](#8-2026-11-09-기준-실제-완료-범위)
9. [v1.0.0 도착지와 후속 버전](#9-v100-도착지와-후속-버전)
10. [취업 포트폴리오 관점에서 얻은 경험](#10-취업-포트폴리오-관점에서-얻은-경험)
11. [이후 히스토리 작성 템플릿](#11-이후-히스토리-작성-템플릿)

---

## 1. 프로젝트 개요와 비즈니스 문제

### 1.1 시작 배경

캐나다 이커머스·리테일 기업의 Data Engineer 직무를 목표로, 기존 이커머스 백엔드 개발 경험을 데이터 엔지니어링으로 연결할 수 있는 개인 포트폴리오를 기획했다. Purdys Chocolatier 등 실제 리테일 비즈니스에서 발생할 법한 문제를 참고하여 **가상의 초콜릿 브랜드**를 구축했다.

**핵심 질문:** 온라인 쇼핑몰과 오프라인 POS에 나뉘어 있는 상품·고객·주문·매장 데이터를 하나의 분석 플랫폼에 통합하려면 어떻게 설계하고 구현해야 할까?

### 1.2 목표 아키텍처

```text
┌──────────────────────────┐       ┌──────────────────────────┐
│ Online Store (Lovable)   │       │ Square POS Sandbox       │
│ Products, Customers,     │       │ Catalog, Customers,      │
│ Orders, Order Items      │       │ Locations, Orders        │
└───────────┬──────────────┘       └────────────┬─────────────┘
            │ CSV / data extract                │ REST API
            └──────────────────┬────────────────┘
                               ▼
                     Python ingestion
                               ▼
                PostgreSQL raw_online/raw_square
                               ▲
                   Kestra orchestration
                               │
                               ▼
                  Python export → GCS
                               ▼
                       BigQuery raw
                               ▼
                  dbt Transformation
              Staging → Intermediate → Marts
                               ▼
                    Analytics Dashboard
```

> **주의:** 위 그림은 `v1.0.0`의 목표 구조를 포함한다. 2026-11-09 현재 BigQuery 상품 원본 적재는 확인했지만 dbt와 대시보드는 아직 완성되지 않았다.

### 1.3 프로젝트 원칙 (2026-11-09 확정)

1. **실무에서 Data Engineer가 어떻게 처리하는가**를 기본 설계 기준으로 삼는다.
2. 단, 개인 포트폴리오의 비용·시간에 맞춰 과도한 복잡도는 피한다.
3. **실무 권장 방식**과 **현재 학습용/포트폴리오 구현 방식**을 구분한다.
4. 새로운 아이디어가 생겨도 `v1.0.0`의 필수 목표를 먼저 달성한다. 나머지는 GitHub Issues와 후속 버전으로 관리한다.
5. 코드는 계속 Commit/Push하고, 첫 번째 End-to-End 완성 시점에 Git Tag `v1.0.0` 및 GitHub Release를 발행한다.

---

## 2. 전체 개발 타임라인

| 날짜/기간 | 핵심 활동 | 기술 | 당시 확인된 단계 |
|---|---|---|---|
| **9월 초~9/9** | 비즈니스 목표 설정, 가상 초콜릿 브랜드 및 데이터 플랫폼 기획 | E-commerce Domain, Architecture | 📘 설계 |
| **9/9~10** | 온라인 스토어/POS 설계, 주문 채널·엔티티 정의, 저장소 분리 | Lovable, GitHub | ✅ 소스 시스템 기반 마련 |
| **9/11~12** | 상품 CSV를 Square Catalog API용 JSON으로 변환·등록 | Python, Pandas, REST API | ✅ 상품 연동 |
| **9/13~14** | Square 응답 ID, 중복 처리, 보상 삭제, 고객 ID 매핑 검토 | Square API, Mapping | 🟡 개선/검증 |
| **9/22 전후** | Locations, Retail Orders, SKU–Variation 및 Location ID 연동 | Square Locations/Orders | 🟡 단계별 구현 |
| **9월 하순** | 최종 클라우드 데이터 플랫폼 방향 구상 | GCP, BigQuery, Docker | 📘 학습/설계 |
| **10/8 전후** | 남은 작업과 기술 학습 일정 재정리 | Roadmap | 📘 계획 |
| **10/13~14** | Docker PostgreSQL 구성, DBeaver 연결 | Docker, PostgreSQL | ✅ 로컬 DB 구축 |
| **10월 중순~10/22** | Online 5개 CSV ETL, 스키마 버그 수정, 모듈 리팩토링 | Python, SQLAlchemy, SQL | ✅ 기본 ETL 동작 |
| **10/22 전후** | Square API → `raw_square` 수집, JSONB 저장 | REST API, PostgreSQL JSONB | ✅ 기본 수집 구현 |
| **10/26~28** | Kestra 환경 설치, Flow·Task 등 학습 | Kestra, Docker Compose | ✅ 기본 실행 환경 |
| **10/29** | Kestra에서 상품 Python 파이프라인 실행, 네트워크·볼륨 문제 해결 | Kestra, Docker, Python | ✅ 온라인 상품 실행 |
| **10/29~30** | 실행 메타데이터 및 9개 개별 Flow, 이후 Parent Flow | Kestra, SQL Migration | ✅ 순차 실행 기록 |
| **10/31** | PostgreSQL → GCS → BigQuery 경로와 ELT 방향 확정 | GCS, BigQuery, ELT | 📘 설계 |
| **11/1~3** | BigQuery Federated Query 및 GCP 개념 학습 | BigQuery, AlloyDB, IAM | 📘 별도 실습 |
| **11/3~5** | dbt 계층 및 테스트 방향 확정 | dbt, SQL | 📘 설계 |
| **11/4~6** | 공통 Python Logging Patch 및 Square Catalog 실행 검증 | Python logging, Kestra | 🟡 부분 검증 |
| **11/6~7** | 클라우드·데이터 모델링 심화 학습, ML 기능 보류 | GCP, BigLake, dbt | 📘 학습 |
| **11/8** | PostgreSQL 상품 Export 및 Kestra → GCS 업로드 성공 | Python, GCS, Kestra | ✅ GCS 업로드 |
| **11/9** | BigQuery 상품 수동 적재 및 15행·19컬럼 비교 검증 | BigQuery, Python, IAM | ✅ 로컬 검증 통과 |
| **11/9** | Kestra BigQuery 작업 추가, 패키지 다운로드 장애로 전체 재실행 보류 | Kestra, pip, Network | 🟡 최종 실행 미확인 |
| **11/9** | `v1.0.0` 릴리스 기준 및 실무 중심 개발 원칙 확정 | Git Tag, GitHub Release | 📘 프로젝트 관리 결정 |

---

## 3. 9월 — 프로젝트 시작과 Square API 연동

### 2026-09-09 — 프로젝트 출발: 리테일 비즈니스 문제 정의

**문제/목표**
- 기존 이커머스 개발 경험을 DE 직무로 연결할 수 있는 포트폴리오가 필요했다.
- 이미 준비된 CSV만 분석하기보다 데이터가 생성되는 시스템부터 만들기로 했다.

**수행**
- 가상 브랜드 *Charlie's Chocolate Factory* 설정.
- 온라인몰과 POS의 두 데이터 소스 정의.
- 향후 상품, 주문, 고객, 매장, 매출을 통합 분석하는 플랫폼을 장기 목표로 설정.

**배운 점**
- 데이터 플랫폼은 기술 목록보다 **비즈니스 문제와 데이터 발생 위치**부터 정의하는 편이 설득력 있다.

### 2026-09-09~10 — Lovable 온라인몰 및 POS 소스 시스템 설계

**수행**
- Lovable 기반 온라인 스토어와 POS Simulator 구축 방향 설정.
- 상품 15개 및 고객·주문·주문상품·매장·결제·로열티·세금 데이터 구조 논의.
- 초기 오프라인 매장을 Downtown Vancouver, Burnaby, Richmond로 설정.
- `ONLINE`과 `RETAIL` 주문 채널 구분, 온라인몰과 Square의 역할 구분.
- 웹사이트 코드와 데이터 플랫폼 코드를 별도 GitHub 저장소로 관리하기로 결정.

**당시 주요 규칙**
- 회원의 구매 포인트 적립률: 1%.
- 온라인 구매와 매장 구매는 다른 데이터 소스에서 수집하되, 향후 공통 분석 모델에서 통합한다.
- 동일 주문을 양쪽에서 중복 집계하지 않도록 채널 기준을 명확히 한다.

**배운 점**
- 데이터 수집 전 **소스 시스템 책임과 비즈니스 키**를 분리해야 이후 통합 시 혼선이 줄어든다.

### 2026-09-11~12 — 첫 Python 상품 매핑과 Square Catalog 연동

**수행**
- Lovable CSV Export → Python/Pandas → Square Catalog API 연계.
- `;` 구분자로 내보낸 CSV 파싱 및 필드 매핑.
- 가격을 Square에서 요구하는 통화/최소 화폐 단위로 변환.
- `ITEM` / `ITEM_VARIATION` 구조와 SKU 매핑 처리.
- 이미 생성된 상품을 다시 만들지 않도록 중복 검사 진행.
- 결과를 Square API Explorer 등에서 확인.

**장벽**
- 원본 CSV 구조와 Square API 요청 JSON 구조가 달랐다.
- 상품 ID, Variation ID, SKU 각각의 역할이 달라 단순 1:1 컬럼 복사로 해결할 수 없었다.

**대응**
- Source-to-Target Mapping을 명시하고, API 요청/응답 구조를 나누어 처리.
- 중복 여부 확인과 등록 후 ID 저장 작업을 분리.

**배운 점**
- API 기반 Data Integration에는 타입 변환, 식별자 매핑, 중복 검사, 응답 검증이 필수다.

### 2026-09-13~14 — Square ID/중복/실패 처리 문제

**발생한 문제**
1. Square 상품 생성 후 응답에서 ID를 잘못 참조하여 `KeyError: 'id'` 발생.
2. Square 생성은 성공했지만 로컬 매핑 CSV 저장이 실패하면 재실행 시 중복 생성 위험 존재.
3. 오래된 `matched_variation_ids` 값 때문에 존재하지 않는 상품을 기존 상품으로 잘못 판정하는 문제.

**대응**
- 응답의 실제 중첩 경로(예: `catalog_object.id`)에 맞춰 ID 추출.
- 기존 SKU와 Square 활성 상품을 비교하여 중복 판정.
- 생성 성공 후 로컬 저장이 실패할 경우 Square 객체 삭제 등 보상 처리 흐름 검토·개선.
- 고객 및 주소 CSV의 내부 ID ↔ Square ID 연결 확장 검토.

**배운 점**
- 외부 API 처리에서는 **부분 성공(partial success)** 상태가 발생한다.
- 멱등성, 중복 방지, 실패 복구는 추후 Kestra 재실행에서도 반복될 중요한 설계 주제다.

### 2026-09-14 전후 — 프로젝트 범위 및 서비스 주소 정리

- 온라인몰: `https://chocoflavor.dev`
- POS: `https://chocoflavor.dev/pos`
- 별도 DE 저장소: `chocolate-commerce-data-platform`
- README의 포지셔닝을 단순 POS 예제가 아닌 **Omnichannel Retail Data Platform**으로 정리.

### 2026-09-22 전후 — Locations와 RETAIL Orders 확장

**수행**
- Square Locations 생성 요청에 필요한 매장 데이터 매핑.
- `RETAIL` 주문과 `ONLINE` 주문의 분리 기준 정리.
- 매장별 Square Location ID와 주문의 연결.
- SKU → Variation ID → Square Order line item 연결.
- 주문 단건 및 일괄 변환/생성 코드 작업, 금액·응답·ID 검증 과정 정리.

**장벽: Square Locations API HTTP 400**

```text
BAD_REQUEST
address.postal_code is required
```

**대응**
- 매장 원본 CSV 및 요청 매핑에 `postal_code` 추가.
- 이후 Location 생성 테스트 및 Square Location ID 저장 흐름 확인.

**당시 진행 상태 주의**
- 당시 엔티티 매핑 문서에서는 Products/Customers 1차 완료, Locations 생성 테스트 완료로 기록.
- Orders는 단건·일괄 처리 코드 작성 단계였으며, 모든 주문의 최종 성공을 9월 22일에 확정하지 않았다.
- Payments와 Square Loyalty 전체 통합은 이후 범위로 남겼다.

**배운 점**
- 외부 서비스의 필수 필드 검증과 여러 엔티티 간 참조 무결성은 소스 데이터 모델 설계에 영향을 준다.

### 2026-09-22~23 및 9월 하순 — GCP 방향 탐색

- Data Engineering Zoomcamp 내용을 참고해 Docker, GCP, GCS, BigQuery 등 학습.
- 장기 파이프라인 방향을 수집 → 저장 → 변환 → 분석으로 구체화.
- 이 시기의 상당 부분은 개념 학습/설계였고, 실제 로컬 DB와 클라우드 구현은 10월 이후 본격적으로 진행.

---

## 4. 10월 — 로컬 데이터 플랫폼과 Kestra 자동화

### 2026-10-08 전후 — 프로젝트 로드맵 재정비

**상황**
- Square 연동 작업이 예상보다 길어지면서 남은 작업과 학습 순서를 재정리할 필요가 생겼다.

**결정**
- Square 수집 범위를 정리한 후 로컬 DB, 클라우드 적재, 변환 및 오케스트레이션으로 이어지는 경로 유지.
- 일정 자체를 지키기보다 실제 실행과 검증 결과를 기준으로 진행.

### 2026-10-13~14 — Docker PostgreSQL 환경 구축

**도입 기술**
- Docker Desktop / Compose, PostgreSQL, DBeaver, SQLAlchemy, `psycopg2-binary`.

**수행**
- 로컬 데이터베이스 `chocolate_db` 생성.
- Docker의 PostgreSQL 서비스 실행, DBeaver 연결.
- Python에서 CSV를 PostgreSQL에 넣는 초기 경로 구현.
- 초기 상품 데이터 15행 적재 확인.

**장벽**
- `ModuleNotFoundError: psycopg2` 등 Python DB 드라이버 관련 오류.

**대응**
- 올바른 가상환경에 드라이버 설치, SQLAlchemy와 DB 접속 설정 확인.

**배운 점**
- Docker 컨테이너, 데이터베이스, DB 클라이언트, Python 실행 환경은 각각 역할이 다르다.

### 2026-10월 중순~10-22 — Online CSV 5개 테이블 ETL 및 리팩토링

**수행**
- 다음 온라인 데이터를 `raw_online` 스키마에 적재하는 ETL 구현:

| 대상 테이블 | CSV 원본 행 | 필터 후 행 | 선별 규칙 |
|---|---:|---:|---|
| `products` | 15 | 15 | 전체 |
| `customers` | 20 | 10 | `signup_channel = ONLINE` |
| `customer_addresses` | 20 | 10 | 선별 고객과 연결된 주소 |
| `orders` | 36 | 14 | `channel = ONLINE` |
| `order_items` | 92 | 37 | 선별 주문과 연결된 상품 |

- `Extract` / `Transform` / `Load` 역할을 파일별로 분리:
  - `src/extract/online/read_source_tables.py`
  - `src/transform/online/select_channel_records.py`
  - `src/load/postgres/connection.py`
  - `src/load/postgres/online/replace_table.py`
  - `src/pipelines/ingestion/online/load_tables_to_postgres.py`
- SQL Schema와 Validation SQL 작성.
- 원본 필터 조건과 엔티티 연결 관계 검토.

**장벽: 성공 로그가 출력됐는데 DBeaver의 `raw_online` 테이블이 비어 보임**
- `df.to_sql()`에서 `schema`를 명시하지 않아 의도한 스키마가 아닌 DB 기본 스키마로 적재될 가능성이 있었음.

**대응**
- `schema="raw_online"` 명시.
- `if_exists="replace"`에서 **기존 테이블 유지 + DELETE 후 APPEND**로 변경.
- 테이블별 `engine.begin()` 트랜잭션으로 삭제와 삽입 묶기.
- 허용한 테이블명만 적재하도록 제한.

**현재 구현 특성/한계**
- 온라인 적재는 테이블별 Full Refresh. 재실행 시 동일 데이터가 무한 누적되지 않음.
- 테이블 전체 5개를 하나의 원자적 트랜잭션으로 처리하지는 않음.
- 빈 DataFrame 보호, 전체 데이터 검증, 이력 관리 등은 추가 개선 가능.
- 주문상품 연결은 `orders.id`가 아닌 비즈니스 주문 키 `orders.order_id` 사용.
- 고객의 가입 채널과 주문의 판매 채널은 다른 기준이므로, 향후 고객 통합 분석 시 주의 필요.

**배운 점**
- **실행 성공 ≠ 기대한 스키마에 올바른 데이터가 저장됨**.
- 재실행 정책과 트랜잭션 범위를 명확히 정해야 한다.

### 2026-10-22 전후 — Square API → PostgreSQL `raw_square`

**수행**
- Square Catalog/Customers/Locations/Orders API에서 데이터를 조회.
- 원본 중첩 JSON을 PostgreSQL `JSONB` 형태로 저장하는 방향 선택.
- 일부 API 적재 작업에 Upsert 패턴 적용.

**당시 공유된 Sandbox 조회 수치**

| 항목 | 조회 값 |
|---|---:|
| Catalog | 15개 상품 |
| Customers | 20명 |
| Active Locations | 5곳 |
| Orders | 총 19건, 3개 매장 기준 |
| Order Line Items | 47개 (당시 공유된 조회 결과) |

**문제 및 대응**
- 고객 테이블 준비 부족, API 응답 중첩 구조, 주문과 상품·매장 참조 연결 등을 단계적으로 점검.
- 데이터를 모두 즉시 평탄화하기보다는 raw 단계에서는 원본 payload를 남기고 분석용 정제는 이후 BigQuery/dbt에서 수행하기로 함.

> **중요:** 9월의 Lovable → Square **데이터 등록**과 10월의 Square → PostgreSQL **분석용 데이터 추출**은 반대 방향의 작업이다.

### 2026-10-26~28 — Kestra 환경 구성과 기본 개념 학습

**문제**
- Python 모듈을 매번 터미널에서 개별 실행하는 방식은 반복 실행, 순서 관리, 실패 추적에 비효율적이었다.

**수행**
- Docker Compose에 `kestra` 및 Kestra 전용 `kestra_postgres` 서비스 추가.
- Kestra UI에서 예제 Flow를 생성·실행하고 `SUCCESS` 확인.
- Flow / Task / Execution / Input / Output / Trigger / Concurrency 개념 학습.

**배운 점**
- **Kestra는 실행과 상태를 관리**하고, 기존 Python 코드는 실제 데이터 수집·적재를 담당한다.
- Docker Compose YAML과 Kestra Flow YAML의 역할이 다르다.

### 2026-10-29 — 첫 Kestra → Python → PostgreSQL 실행 성공

**수행**
- `online_to_postgres.py`에 `--tables products` 등 선택 실행 옵션 도입.
- `requirements.txt` 준비 및 작업 컨테이너의 Python 의존성 설치.
- Kestra Docker Task Runner로 프로젝트 Python 모듈 실행.
- 온라인 상품 15행 적재 성공.

**장벽 A — 컨테이너 DB 접속 주소**
- 로컬 Windows에서 쓰던 `localhost:5432`는 Python 작업 컨테이너 자신을 의미했다.
- 해결: 같은 Docker 네트워크에 작업 컨테이너 연결, `postgres:5432` 사용.

**장벽 B — Windows 바인드 마운트 경로**
- `C:/...:/project:ro` 형태에서 Docker Bind 파서 오류.
- 해결: Docker Desktop Linux 측 `/run/desktop/mnt/host/c/...` 경로로 프로젝트 파일 마운트.

**장벽 C — 로컬 가상환경과 작업 컨테이너 차이**
- Windows `.venv`가 자동으로 Linux 컨테이너에 전달되지 않음.
- 해결: `requirements.txt` 설치 단계 준비, 작업 컨테이너 패키지 실행 확인.

**배운 점**
- 로컬/컨테이너 실행 환경의 네트워크·파일시스템·의존성을 각각 관리해야 한다.

### 2026-10-29~30 — 적재 메타데이터 도입

**문제**
- 로컬 실행과 Kestra 실행에서 동일한 15행이 저장되면, 행 수만으로 어느 실행에서 저장됐는지 구분할 수 없었다.

**대응**
- 다음 메타데이터 컬럼 추가:

| 컬럼 | 목적 |
|---|---|
| `ingested_at` | 이번 파이프라인 적재 시각 |
| `orchestrator` | 실행 경로 (`local` 또는 `kestra`) |
| `pipeline_run_id` | 로컬 UUID 또는 Kestra Execution ID |

- PostgreSQL `ALTER TABLE` 마이그레이션 관리 방식 검토.
- Kestra Flow에서 실행 식별값을 Python에 전달.

**배운 점**
- 원본 `updated_at`과 파이프라인 `ingested_at`은 서로 다르며, **실행 관측성**을 위해 적재 메타데이터가 필요하다.

### 2026-10-30 및 이후 — 9개 개별 Flow, Parent Flow

**수행**
- 온라인 5개 개별 Flow 수동 실행 성공.
- Square 4개 개별 Flow 수동 실행 성공.
- 이후 기록에서 개별 9개 Flow를 호출하는 Parent Flow의 순차 실행 성공 확인.

**장벽**
- Square Flow 실행 시 Python `requests` 패키지 누락 오류.

**대응**
- `requirements.txt`에 `requests` 추가 후 재실행.

**남은 검증**
- 모든 테이블의 최종 행 수·관계·메타데이터 검증 결과 및 반복 실행 전후 비교.
- 이후 Logging 개선을 반영한 Parent Flow 전체 회귀 테스트.
- 예약 Schedule Trigger는 별도 검토 대상.

### 2026-10-31 — Phase 4 클라우드 ELT 방향 확정

**문제/질문**
- 이미 PostgreSQL raw 테이블이 있는데 GCS를 다시 거쳐야 하는가?
- 데이터 정제는 GCS 전/후, BigQuery 전/후 중 어디서 해야 하는가?

**결정**
- 현재는 PostgreSQL을 클라우드 수집 원천으로 활용.
- PostgreSQL의 raw 테이블을 파일로 Export → GCS 보관 → BigQuery raw 적재.
- 본격적인 분석용 정제와 소스 통합은 BigQuery + dbt에서 수행.
- GCS를 데이터 정제 엔진이 아닌 파일 저장 계층으로 구분.

**배운 점**
- ETL과 ELT의 차이는 어디에서 변환이 수행되는지에 있다.
- 실제 최적 아키텍처는 환경과 비용에 따라 달라지며, PostgreSQL은 GCS의 필수 선행 서비스가 아니다.

---

## 5. 11월 — GCP, 데이터 품질 및 dbt 준비

### 2026-11-01~03 — BigQuery/GCP 학습 및 Federated Query 실습

**수행**
- GCP Data Engineering 강의와 실습.
- BigQuery에서 AlloyDB 데이터를 `EXTERNAL_QUERY()`로 조회하고 BigQuery 테이블과 JOIN하는 Federated Query 실습.
- IAM, OLTP/OLAP, Lakehouse 등 학습.

**프로젝트 적용 여부**
- 📘 강의·실습 경험으로 기록. **초콜릿 프로젝트에 AlloyDB를 도입한 것은 아님**.
- 초콜릿 프로젝트는 PostgreSQL → GCS → BigQuery 설계를 유지.

### 2026-11-03~05 — dbt 모델링 방향 확정

**배경**
- DataCamp dbt 및 데이터 엔지니어링 강의를 통해 SQL 기반 변환과 테스트 구조 이해.
- 과거 Pandas 클리닝 경험과 데이터 웨어하우스 내부의 ELT 변환 차이 비교.

**결정**
- BigQuery와 dbt를 사용하고, dbt 프로젝트 파일을 기존 GitHub Repository에서 관리.
- 다음 세 계층을 직접 구현:
  1. **Staging:** 원본 데이터 표준화, 타입 정리, 기본 정제.
  2. **Intermediate:** Online/Square 통합, 비즈니스 로직.
  3. **Marts:** 매출·상품·매장 등 분석용 테이블.
- dbt 테스트 (`not_null`, `unique`, `relationships` 등) 포함.
- 이전 Phase 명칭을 갱신하여 **Phase 4A: Cloud Ingestion / Phase 4B: dbt Transformation**으로 구분.

**현재 상태:** 📘 설계 확정, 실제 프로젝트의 dbt 모델 실행 및 결과 검증은 예정.

### 2026-11-04~06 — Kestra 실행 로그의 한계 발견, 공통 Logging 개선

**문제**
- 초기 Python 파이프라인은 주로 `print()`를 사용했고, 다수 Flow에서 실패 원인·실행 시간·단계별 처리 건수를 일관되게 추적하기 어려웠음.

**개선**
- Python 표준 `logging` 도입.
- 공통 `run_logging.py`와 개별 파이프라인의 단계별 로그 구분.
- `stage=extract/connect/load`, `status=started/completed/failed`, 실행 ID, 소요 시간 등의 공통 기록 설계.
- `.patch`는 **로그 저장 파일이 아니라 소스 변경사항(diff)**을 일괄 적용하는 파일이라는 점 학습.

**2026-11-06 실제 검증**
- 개선된 Python Logger가 Square Catalog의 Kestra 실행에 반영된 사실 확인.
- Square Catalog 15개 추출/Upsert 성공 로그, 파이프라인 내부 실행 시간 약 `0.541s`, 종료 코드 0 확인.

**미확인 항목**
- 전체 개별 Flow 및 Parent Flow 재검증.
- 의도적 실패 시나리오의 `FAILED` 전파.
- 실제 DB 내용의 독립적 정합성 검사.
- 모든 내부 `print()`의 Logging 통일.

**배운 점**
- **오케스트레이션 SUCCESS 로그 ≠ 데이터 완전성 보장**.
- 운영 관점에서는 오류 위치, 실행 ID, 데이터 건수, 보안이 중요하다.

### 2026-11-06~07 — 클라우드/데이터 모델링 심화 학습

- BigQuery Distributed Query, Data Lake/Warehouse/Lakehouse, BigLake, Apache Iceberg 등 비교.
- IAM과 데이터베이스/클라우드 서비스의 책임 분리 학습.
- BigQuery ML을 추가할지 검토했지만 **데이터량·비용을 고려하여 보류**.
- 기술을 배웠다는 이유만으로 `v1.0.0`에 무조건 추가하지 않기로 판단.

### 2026-11-08 — PostgreSQL → CSV → GCS 성공

**수행**
- GCP 프로젝트, GCS 버킷, BigQuery Raw Dataset과 인증 방식 준비.
- PostgreSQL `raw_online.products`의 CSV Export 경로 구현.
- Kestra에서 Export 파일을 다음 작업으로 전달하고 GCS에 업로드하는 흐름 실행 성공.

**배운 점**
- 작업 컨테이너의 로컬 파일과 Kestra Output File, GCS 객체는 서로 다른 저장 범위다.
- GCS 업로드 성공은 BigQuery 테이블 로드 성공과 별개의 단계다.

### 2026-11-09 — GCS → BigQuery 상품 수동 적재 및 데이터 비교

**수행/확인**
- GCS 상품 CSV를 BigQuery `raw_online.products`로 **수동 적재 성공**.
- 로컬 Python 검증으로 **GCS 15행과 BigQuery 15행, 19개 컬럼 데이터 비교 통과**.
- 로컬 Python용 `google-cloud-storage`, `google-cloud-bigquery` 라이브러리 및 인증 경로 정리.

**장벽 A — GCP 인증 파일을 찾지 못함**
- `DefaultCredentialsError` 발생.
- Kestra Secret의 서비스 계정 인증정보와 로컬 Python의 `GOOGLE_APPLICATION_CREDENTIALS`가 자동으로 공유되지 않음을 파악.
- JSON 인증정보를 적절한 로컬 경로로 복원하고 환경변수로 경로 지정하여 해결.

**보안 주의**
- Base64는 암호화가 아니므로 `.env.kestra`, 서비스 계정 JSON 원본 및 복원 파일은 Git에 커밋하지 않는다.
- 서비스 계정 IAM 권한은 필요한 작업에 맞게 최소화한다.

**장벽 B — Kestra 검증 작업 중 의존성 설치 장애**

```text
Connection timed out while downloading
No address associated with hostname
```

- 패키지 다운로드 중 네트워크/이름 해석 오류가 발생.
- 도서관 공용 네트워크 영향 가능성을 고려해 집에서 재실행하기로 함.
- 네트워크 문제로 단정하지는 않음.

**2026-11-09 구분해서 기록할 결과**
- ✅ PostgreSQL → CSV → GCS: Kestra 실행 성공.
- ✅ GCS → BigQuery: **수동 적재 성공**.
- ✅ GCS ↔ BigQuery: **로컬 Python 비교 통과**.
- 🟡 BigQuery 적재/검증 Kestra Task 추가: 코드/Flow 추가는 확인했으나 **전체 Kestra 재실행 성공은 미확인**.

### 2026-11-09 — 포트폴리오 관리 방향과 릴리스 기준 확정

**결정**
- 개인 프로젝트는 계속 개선될 수 있으므로 '완벽한 최종 상태'가 아니라 첫 번째 **검증 가능한 도착지**를 `v1.0.0`으로 정의.
- 데이터 수집 → GCS → BigQuery → dbt → Dashboard → End-to-End 검증/README까지 연결한 뒤 Tag/Release.
- 그 전까지 계속 Commit/Push, 새로운 개선 아이디어는 Issues 또는 다음 버전으로 관리.
- 모든 설계 검토는 **실무에서 사용하는 데이터 엔지니어링 방식**을 기준으로 하되, 범위와 비용을 관리.

---

## 6. 기술별 성장 기록

| 분야 | 시작점 | 2026-11-09까지 발전 | 다음 과제 |
|---|---|---|---|
| **Domain Modeling** | 상품·주문·고객 데이터 기획 | Online / Retail 채널 및 ID 관계 구분 | 통합 비즈니스 키 확정 |
| **Lovable** | 쇼핑몰·POS 시뮬레이터 | 실제 수집 가능한 테스트 소스 제공 | 필수 범위 외 기능 추가 보류 |
| **Square REST API** | 상품 등록 | 고객·매장·주문·카탈로그 연동 및 Raw 추출 | API 오류·재실행 정책 보완 |
| **Python/Pandas** | CSV 변환 | ETL 모듈화, JSON 처리, Export, 검증 | 예외 처리·테스트 확장 |
| **PostgreSQL** | 로컬 데이터 저장 | `raw_online` 5개, `raw_square` 4개 테이블 | 최종 DB 정합성/재실행 검증 |
| **Docker** | DB 환경 구성 | Kestra 및 Python Task Runner 연결 | 실행 환경 재현성 개선 |
| **Kestra** | 수동 Python 실행 대체 | 9개 개별 Flow, Parent Flow, 로깅 | Cloud Flow 전체 실행 검증 |
| **GCS** | Raw 파일 저장 | 상품 CSV 업로드 성공 | 나머지 필수 데이터 확장 |
| **BigQuery** | 분석용 Warehouse 설계 | 상품 Raw 적재 및 데이터 비교 통과 | Kestra 자동 로드/추가 테이블 |
| **dbt** | SQL 모델링 학습 | Staging/Intermediate/Marts 구조 설계 | 실제 모델·테스트 구현 |
| **GitHub** | 코드 백업/버전 관리 | 지속적 Commit, README·Phase 문서 | `v1.0.0` Tag/Release |

---

## 7. 문제 해결 사례 모음

| 시기 | 증상/문제 | 원인 또는 판단 | 해결/대응 | 실무에서 연결되는 역량 |
|---|---|---|---|---|
| 9월 | Square API `KeyError: 'id'` | 중첩 응답 경로 오인 | `catalog_object.id` 등 실제 응답 구조에 맞게 파싱 | API Contract 이해 |
| 9월 | 상품 중복/부분 성공 가능성 | 외부 API 성공과 로컬 ID 기록 실패의 분리 | SKU 검사, 응답 저장, 보상 처리 검토 | Idempotency / Recovery |
| 9/22 | Square Location HTTP 400 | `postal_code` 필수 | 원본 CSV와 API 매핑 보완 | Schema Validation |
| 10월 | `psycopg2` 모듈 오류 | DB 드라이버 설치 누락 | 가상환경 의존성 설치 | Environment Management |
| 10월 | `raw_online`에 데이터가 안 보임 | `to_sql` schema 미지정 | 스키마 명시, DELETE + APPEND | Data Correctness / Transaction |
| 10월 | Square 중첩 JSON 저장 | Orders/Catalog 구조 복잡 | `JSONB` raw 보관, 변환 단계 분리 | Raw vs Transformation |
| 10/29 | Kestra DB 접속 문제 | 컨테이너 `localhost` 오해 | Docker 네트워크 및 `postgres` 호스트 사용 | Container Networking |
| 10/29 | Docker 폴더 경로 오류 | Windows 경로와 Linux Docker 경로 차이 | Docker Desktop Linux 호스트 경로 사용 | Runtime Portability |
| 10/30 | Square Flow 패키지 누락 | `requests` 미설치 | `requirements.txt` 보완 | Dependency Management |
| 10/30 | 실행 주체 구분 어려움 | 동일 행 수만으로 실행 추적 불가 | `ingested_at`, `orchestrator`, `pipeline_run_id` | Observability |
| 11/4~6 | Kestra 로그 진단 부족 | `print()` 중심의 불균일한 로그 | 공통 `run_logging.py`, 단계별 INFO/ERROR 구조 | Monitoring / Incident Analysis |
| 11/9 | 로컬 GCP 인증 오류 | 지정된 JSON 파일 경로 부재 | `GOOGLE_APPLICATION_CREDENTIALS` 연결 | IAM / Auth / Secrets |
| 11/9 | pip Timeout/DNS 오류 | 패키지 다운로드 단계 네트워크 실패 | 재실행 환경 재검토 예정 | Environment Reliability |

**반복해서 얻은 교훈**

1. **데이터를 보냈다는 사실**과 **대상에 정확히 저장됐다는 사실**은 다르다.
2. **실행 성공**과 **데이터 품질/정합성 통과**는 다르다.
3. **로컬 실행 환경**과 **컨테이너 실행 환경**은 다르다.
4. 재실행, 로깅, 보안, 데이터 품질을 초기 설계에 포함할수록 운영 부담이 줄어든다.
5. 개인 포트폴리오라도 설계 선택의 **이유와 한계**를 명확하게 설명하는 것이 중요하다.

---

## 8. 2026-11-09 기준 실제 완료 범위

### 완료 또는 부분 검증된 항목

| 구성 요소 | 상태 | 검증 메모 |
|---|---|---|
| Lovable 온라인몰 및 POS 시뮬레이션 | ✅ | 테스트 데이터 소스 구축 |
| Square Sandbox Catalog/Customers/Locations/Orders 연동 | ✅ | 세부 엔티티별 최종 품질 검증은 별도 |
| PostgreSQL `raw_online` 5개 테이블 | ✅ | Python 적재 성공 기록 |
| PostgreSQL `raw_square` 4개 테이블 | ✅ | 개별 수집/실행 성공 기록 |
| Kestra 9개 개별 Flow 및 Parent Flow | ✅ | 과거 실행 성공 기록; Logging 적용 이후 전체 재검증 필요 |
| Kestra 공통 Logging | 🟡 | Square Catalog에서 새 로깅 확인; 전체 재검증 필요 |
| PostgreSQL Products Export → GCS | ✅ | Kestra 업로드 성공 |
| GCS Products CSV → BigQuery | ✅ | **수동 적재 성공** |
| GCS ↔ BigQuery 상품 15행·19컬럼 비교 | ✅ | 로컬 Python 검증 통과 |
| Kestra BigQuery 적재/검증 Flow 전체 | 🟡 | Task 추가, 다운로드 오류 발생, 최종 성공 미확인 |
| BigQuery 나머지 필수 테이블 | ⬜ | 구현/검증 예정 |
| dbt Staging → Intermediate → Marts | ⬜ | 설계 결정, 구현 예정 |
| Analytics Dashboard | ⬜ | 구현 예정 |

### 주의: 아직 검증했다고 말하면 안 되는 것

- 모든 9개 테이블의 최신 DB 건수와 관계/무결성 검사가 통과했다는 주장.
- Logging 개선 이후 Kestra Parent Flow 전체가 다시 성공했다는 주장.
- BigQuery 데이터 적재가 처음부터 끝까지 **Kestra만으로 자동 실행**되었다는 주장.
- dbt 변환 모델과 대시보드가 이미 완성되었다는 주장.
- 실운영 기업 데이터 및 대규모 트래픽에서 안정성을 입증했다는 주장.

---

## 9. v1.0.0 도착지와 후속 버전

### 9.1 v1.0.0 목표

**완료 정의:** 온라인과 오프라인 소스에서 수집한 주요 상품/주문/매장 데이터가 GCS·BigQuery로 전달되고, dbt 변환을 통해 분석용 데이터로 통합되어 대시보드에서 조회 가능하며, 전체 흐름의 실행·검증 방법을 설명할 수 있는 상태.

| 순서 | 필요 작업 | 완료 기준 |
|---|---|---|
| 1 | **Products Cloud Flow 검증** | Kestra의 Export → GCS → BigQuery 및 비교 검증 전체 성공 |
| 2 | 필수 Online/Square 데이터 확장 | BigQuery Raw 테이블 적재와 건수/스키마 확인 |
| 3 | dbt Staging | 주요 Raw 소스 표준화·기본 테스트 성공 |
| 4 | dbt Intermediate | 온라인/매장 주문 연결, 주요 비즈니스 규칙 적용 |
| 5 | dbt Marts | 상품·매출·매장 등 분석용 결과 생성 |
| 6 | Analytics Dashboard | 통합 매출 등 핵심 지표 시각화 |
| 7 | 문서/검증 | README, 아키텍처, 실행 방법, 테스트 및 알려진 한계 정리 |
| 8 | 버전 마킹 | Git Tag `v1.0.0` 및 GitHub Release 발행 |

### 9.2 v1.0.0 이후 개선 후보

- 증분 적재 및 변경 데이터 처리
- 더 엄격한 중복 방지와 재실행 정책
- CI/CD, 자동 테스트, Terraform 등 인프라 재현성
- 정기 Scheduling/알림/모니터링 강화
- Square Payments 및 Loyalty 등 데이터 범위 확장
- 비용 최적화와 BigQuery 성능 개선
- BigQuery ML 등 고급 분석 기능 (필요성·데이터량·비용 검토 후 결정)

> **개발 원칙:** 새로운 기능은 무조건 추가하지 않고, V1.0의 핵심 동작과 비즈니스 목표를 우선한다.

---

## 10. 취업 포트폴리오 관점에서 얻은 경험

### 10.1 프로젝트의 차별점

- CSV 분석만 하는 프로젝트가 아니라 **온라인몰/POS 데이터 발생 지점부터 구성**.
- 두 데이터 소스의 상품, 고객, 주문, 매장 식별자를 연결해보며 실제 커머스 도메인 문제 경험.
- Python, PostgreSQL, Kestra, GCS, BigQuery, dbt를 **하나의 비즈니스 목표**에 연결하는 End-to-End 프로젝트로 발전 중.
- 성공한 기능뿐 아니라 문제 발생·원인 분석·설계 변경 이력이 존재.

### 10.2 면접에서 활용할 수 있는 기술 사례

**사례 A — API 재실행과 중복 문제**
- 상황: Square에 상품은 생성됐지만 매핑 파일 저장에 실패할 수 있음.
- 행동: 실제 응답 구조 파악, SKU/ID 매핑, 중복 확인, 보상 처리 검토.
- 보여줄 역량: API Integration, Idempotency, Failure Handling.

**사례 B — DB 적재 스키마 버그**
- 상황: 적재 성공 로그 후 원하는 Raw 테이블에 데이터가 보이지 않음.
- 행동: `to_sql`의 Schema 설정을 확인하고 트랜잭션형 DELETE + APPEND로 변경.
- 보여줄 역량: Data Validation, SQL, Transaction Awareness.

**사례 C — Kestra와 Docker 실행 환경 분리**
- 상황: Python 코드 자체는 동작하지만 컨테이너에서 DB/프로젝트 파일 접근 실패.
- 행동: Docker Network/Volume/환경 변수 및 의존성 경로 해결.
- 보여줄 역량: Orchestration, Container Networking, Reproducibility.

**사례 D — 로깅과 데이터 검증 고도화**
- 상황: Flow 성공 여부만으로 실패 단계와 결과 정확성을 판단하기 어려움.
- 행동: 공통 Logger, Execution ID, 적재 건수, GCS/BigQuery 값 비교 도입.
- 보여줄 역량: Observability, Data Quality, Operations.

### 10.3 취업용 설명 문장 초안

> I have a background in e-commerce backend development, and I'm building an end-to-end retail data platform that integrates online store and POS data for analytics. The project covers API-based ingestion, workflow orchestration, cloud data loading, and SQL-based data modeling. I've also worked through real implementation issues involving data mapping, container networking, logging, and validation.

> **표기 원칙:** 완료하지 않은 기술은 `I'm building`, `planned`, `in progress` 등으로 정확하게 설명한다.

---

## 11. 이후 히스토리 작성 템플릿

프로젝트를 진행할 때마다 아래 블록을 복사해 누적한다. 작은 커밋마다 반드시 작성할 필요는 없으며, **의미 있는 기능 완료·버그 해결·설계 결정·검증 성공** 시 작성한다.

```markdown
### YYYY-MM-DD — [작업 제목]

**Phase / 기술**
- Phase:
- Stack:

**목표 / 발생한 문제**
- 

**원인 분석 / 의사결정**
- 

**실제 수행한 작업**
- 

**실행 및 검증 결과**
- [ ] 실행 성공
- [ ] 데이터 검증
- [ ] 재실행/실패 시나리오
- 증거: [Git Commit / Kestra Execution / SQL 결과 / 스크린샷]

**배운 점과 한계**
- 

**다음 작업**
- 
```

### 함께 관리할 문서

| 문서 | 역할 |
|---|---|
| `README.md` | 처음 방문한 사람을 위한 프로젝트 개요, 아키텍처, 사용 방법 |
| `PROJECT_PROGRESS_KO.md` | 현재 Phase, 오늘의 진행 상황, 다음 할 일 |
| **`PROJECT_HISTORY_KO.md`** | 날짜별 문제 해결과 기술적 의사결정의 누적 기록 |
| Phase별 `.md` | 해당 단계의 기술 구현·검증 상세 자료 |

---

## 참고 및 검증 근거

이 문서는 다음 자료와 과거 대화 내용을 바탕으로 작성했다.

- `ENTITY_MAPPING_UPDATED.md` (2026-09-22 시점 Square 엔티티 연동 기록)
- `PROJECT_PROGRESS_KO.md`, `chocolate-project-progress-log.md` (10월 로컬 DB/ETL 진행)
- `phase-3-kestra-orchestration-ko(3).md` (10월 29~30일 Kestra 개발·실행 상세 기록)
- `phase-3-kestra-logging-retrospective-ko-updated.md` (11월 6일 Logging 개선 검증)
- `phase-4-gcs-bigquery-dbt-progress-ko-updated.md` (Phase 4 설계 및 dbt 방향)
- `chocolate-gcp-auth-guide-ko.pdf` (11월 9일 GCS/BigQuery 인증 및 검증 결과)
- 2026년 9월~11월의 Chocolate Commerce Data Platform 관련 대화

> **추후 정밀화 방법:** GitHub 커밋 날짜·Diff, 실제 Kestra Execution 시간, DB Validation 결과와 대조하여 기록을 보완한다. 날짜가 불명확한 초기 작업은 커밋 기록을 확인한 후 조정한다.

---

_이 문서는 프로젝트가 발전할수록 업데이트되는 개발 히스토리다. 완벽한 프로젝트를 만드는 것보다, 실무적인 관점에서 설계·구현·검증한 과정을 정확하게 기록하는 것을 목표로 한다._
