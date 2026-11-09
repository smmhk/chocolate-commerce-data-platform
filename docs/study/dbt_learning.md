# 🍫 dbt Learning Notes — Chocolate Commerce Data Platform

> **학습 기록일:** 2026-11-06  
> **주제:** dbt 기초부터 Source · Model · Test · Snapshot까지  
> **학습 맥락:** dbt Core 강의(DuckDB 실습) → Charlie's Chocolate Factory 데이터 엔지니어링 프로젝트(BigQuery 적용 예정)  
> **이 문서의 목적:** 오늘 배운 개념을 *무엇을 위해 쓰는지 → 파일에 어떻게 작성하는지 → 실제로 무엇이 실행되는지* 순서로 복습하기

> [!IMPORTANT]
> **현재 구현 상태와 향후 계획을 구분하자.** 초콜릿 프로젝트는 **온라인/Square → Python → PostgreSQL → Kestra**까지 작업했다. **GCS 업로드·BigQuery Raw 적재·dbt 모델링은 아직 구현 전**이며, 이 문서의 BigQuery SQL·YAML과 상품 가격·주문 예시는 **학습용 가상 예시**다. 실제 컬럼명, 데이터셋명, 상태값, GCP 프로젝트 ID는 구현할 때 확인해야 한다.

---

## 📚 목차

1. [오늘 배운 내용 한눈에 보기](#1-오늘-배운-내용-한눈에-보기)
2. [dbt는 무슨 일을 할까?](#2-dbt는-무슨-일을-할까)
3. [Staging → Intermediate → Marts](#3-staging--intermediate--marts)
4. [dbt 프로젝트 파일 구조와 YAML의 역할](#4-dbt-프로젝트-파일-구조와-yaml의-역할)
5. [Source: 원본 데이터 위치를 등록하기](#5-source-원본-데이터-위치를-등록하기)
6. [Model: SQL로 분석용 데이터 만들기](#6-model-sql로-분석용-데이터-만들기)
7. [Jinja, `ref()`, `source()`, Macro](#7-jinja-ref-source-macro)
8. [Test: Generic Test와 Singular Test](#8-test-generic-test와-singular-test)
9. [테스트 실패 로그와 컴파일 SQL 디버깅](#9-테스트-실패-로그와-컴파일-sql-디버깅)
10. [Snapshot: 변경 이력 남기기](#10-snapshot-변경-이력-남기기)
11. [dbt 명령어와 실제 실행 흐름](#11-dbt-명령어와-실제-실행-흐름)
12. [Documentation · Lineage · CI/CD와 Kestra](#12-documentation--lineage--cicd와-kestra)
13. [초콜릿 프로젝트에 적용할 설계 초안](#13-초콜릿-프로젝트에-적용할-설계-초안)
14. [헷갈렸던 질문 Q&A](#14-헷갈렸던-질문-qa)
15. [복습 체크리스트 & 다음 실습](#15-복습-체크리스트--다음-실습)
16. [공식 참고 링크](#16-공식-참고-링크)

---

## 1. 오늘 배운 내용 한눈에 보기

| 개념 | 한 문장 정의 | 초콜릿 프로젝트 예시 |
|---|---|---|
| **Source** | dbt 외부에서 이미 존재하는 원본 테이블의 **위치/메타데이터를 등록** | BigQuery `raw_online.orders` |
| **Model** | SQL로 원본/기존 모델을 **변환하여 분석용 결과를 만드는 로직** | `stg_online_orders`, `fct_daily_sales` |
| **Generic Data Test** | YAML에서 재사용 가능한 데이터 품질 규칙 선언 | `order_id`는 `not_null`, `unique` |
| **Singular Data Test** | `tests/*.sql`에 **문제 행을 반환하는 SELECT** 작성 | 음수 주문 금액 찾기 |
| **Snapshot** | 시간에 따라 **행의 값이 어떻게 바뀌었는지 버전별 보관** | 상품 가격 $5 → $6 기록 |
| **`source()`** | 등록된 원본 테이블 참조 | `source('raw_online', 'orders')` |
| **`ref()`** | 다른 dbt 모델 참조 및 의존 관계 생성 | `ref('stg_online_orders')` |
| **`dbt run`** | 모델 생성/갱신 | Staging → Intermediate → Marts |
| **`dbt test`** | 정의한 데이터 테스트 실행 | Generic + Singular Test |
| **`dbt snapshot`** | Snapshot 생성/갱신 | 상품 변경 이력 유지 |
| **`dbt build`** | 모델·테스트·Snapshot·Seed 등을 의존 순서에 맞춰 빌드 | 선택한 파이프라인 함께 실행 |

### 🗺️ 전체 데이터 흐름

```mermaid
flowchart TD
    A[Online Store / Square API] --> B[Python 수집·적재]
    B --> C[(PostgreSQL Raw)]
    C -. "향후: Kestra + export" .-> D[(GCS Raw Files)]
    D -. "향후: load" .-> E[(BigQuery Raw Tables)]

    E --> S["dbt Source<br/>원본 테이블 등록·참조"]
    S --> F["dbt Staging<br/>컬럼 정리 / 타입 변환"]
    F --> G["dbt Intermediate<br/>Online + Square 통합"]
    G --> H["dbt Marts<br/>주문 팩트 / 일별 매출"]
    H --> I[BI Dashboard]

    S -.-> T["Data Tests<br/>원본 품질 확인"]
    F -.-> U["Data Tests<br/>모델 품질 확인"]
    E -.-> V["Snapshot<br/>변경 이력 추적"]
    V -.-> G

    classDef done fill:#d8f2e2,stroke:#218557,color:#163d2b;
    classDef future fill:#fff0d5,stroke:#c98a26,color:#68430c;
    class A,B,C done;
    class D,E,S,F,G,H,I,T,U,V future;
```

> **핵심:** Source는 데이터 저장 장소가 아니라 **이미 저장된 원본을 dbt에 알려주는 정의**다. Model은 **SQL 변환**, Test는 **검증**, Snapshot은 **변경 이력**이다.

---

## 2. dbt는 무슨 일을 할까?

### 2-1. dbt의 역할은 ELT의 **T(Transform)**

- **Extract / Load:** Python과 Kestra가 온라인 주문·Square 데이터를 가져와 저장한다.
- **Transform:** dbt가 BigQuery 안에서 SQL을 실행해 원본을 정리하고 분석용 테이블/뷰를 만든다.
- dbt 자체가 Square API를 호출해서 데이터를 수집하거나 GCS에 파일을 업로드하는 도구는 아니다.

**요리 비유**

- **Source:** 냉장고에 어떤 재료가 어느 칸에 있는지 적은 목록
- **Staging Model:** 재료 씻기, 손질하기, 단위 통일하기
- **Intermediate Model:** 여러 재료를 조합해 공통 중간 재료 만들기
- **Mart Model:** 손님에게 제공할 완성 요리
- **Test:** 재료와 완성 요리에 문제가 없는지 검사
- **Snapshot:** 재료 정보(예: 가격)가 언제 어떻게 바뀌었는지 기록

### 2-2. 그럼 pandas로 데이터 클리닝하는 것은 잘못된 방식일까?

아니야. **데이터의 위치와 처리 요구에 따라 다른 도구를 선택**하는 거야.

| pandas | dbt + BigQuery |
|---|---|
| Python 메모리 기반 정제·탐색에 유리 | 데이터 웨어하우스 안에서 SQL 기반 변환에 유리 |
| 외부 API 데이터 가공, 특수 로직에 적합 | 모델 의존성, 재사용, 테스트, 문서화에 강점 |
| Python 파이프라인으로 배포 | SQL 중심 ELT 모델로 배포 |

**이번 프로젝트의 선택:** 수집·적재는 Python/Kestra, **BigQuery에 적재된 후의 주요 변환은 dbt**로 진행한다.

---

## 3. Staging → Intermediate → Marts

```mermaid
flowchart LR
    RAW[(Raw)] --> STG["STAGING<br/>한 소스씩 정리"]
    STG --> INT["INTERMEDIATE<br/>소스 통합/비즈니스 로직"]
    INT --> MRT["MARTS<br/>분석에 바로 쓰는 결과"]
    MRT --> BI[대시보드]
```

| 계층 | 핵심 목적 | 초콜릿 프로젝트 가상 예시 |
|---|---|---|
| **Staging** (`stg_`) | 컬럼명·데이터 타입·형식 표준화, 기본 정제 | `stg_online_orders`, `stg_square_orders` |
| **Intermediate** (`int_`) | 여러 Staging 모델을 조합, 공통 비즈니스 규칙 적용 | `int_unified_orders` |
| **Marts** (`fct_`, `dim_`) | 리포팅과 의사결정에 바로 사용할 Fact/Dimension | `fct_orders`, `fct_daily_sales`, `dim_products` |

### ⚠️ `staging`이라는 단어가 두 가지로 쓰인다!

| 구분 | 의미 |
|---|---|
| **배포 환경 `dev → stg → prod`** | 개발 → 운영 전 검증 → 실제 운영 환경 |
| **dbt 모델 계층 `staging → intermediate → marts`** | 데이터를 정리 → 통합 → 분석용으로 변환하는 논리적 구조 |

둘은 서로 다른 축이다. **운영 환경(prod) 안에도 Staging 모델이 존재할 수 있다.**

---

## 4. dbt 프로젝트 파일 구조와 YAML의 역할

### 4-1. 우리 프로젝트에 도입할 폴더 구조(계획)

```text
chocolate-commerce-data-platform/
└── chocolate_dbt/
    ├── dbt_project.yml             # 프로젝트 전체 설정
    ├── models/
    │   ├── staging/
    │   │   ├── staging.yml          # Source/모델 속성/Generic Tests
    │   │   ├── stg_online_orders.sql
    │   │   ├── stg_square_orders.sql
    │   │   └── stg_online_products.sql
    │   ├── intermediate/
    │   │   ├── intermediate.yml     # 이 계층 모델 속성/테스트
    │   │   └── int_unified_orders.sql
    │   └── marts/
    │       ├── marts.yml            # 이 계층 모델 속성/테스트
    │       ├── fct_orders.sql
    │       └── fct_daily_sales.sql
    ├── tests/
    │   ├── assert_no_negative_order_amount.sql
    │   └── assert_order_totals_match.sql
    ├── macros/
    │   └── cents_to_dollars.sql
    └── snapshots/
        └── products_snapshot.yml
```

> **오늘 정한 운영 방식:** 모델 속성 YAML은 우선 `staging.yml`, `intermediate.yml`, `marts.yml` **세 파일**로 관리한다. **모델 SQL 파일마다 YAML을 하나씩 만들 필요는 없다.** Source 전용 `sources.yml`을 별도로 분리하는 방식도 가능하다.

### 4-2. 주요 파일 비교

| 파일 | dbt가 읽어서 하는 일 | 개발자가 수정하나? |
|---|---|---|
| `dbt_project.yml` | 프로젝트 이름, 모델 경로, 모델 기본 설정 등 | ✅ |
| `~/.dbt/profiles.yml` | BigQuery/DuckDB 등 데이터 플랫폼 연결 정보 | ✅ (비밀키는 주의) |
| `models/**/*.sql` | SQL 모델 정의 | ✅ |
| `models/**/*.yml` | Source, 모델 설명, Generic Test 등 | ✅ |
| `tests/*.sql` | Singular Test 정의 | ✅ |
| `snapshots/*.yml` | Snapshot 정의(dbt 1.9 이상) | ✅ |
| `target/compiled/**` | Jinja가 해석된 **컴파일 결과 SQL** | ❌ (자동 생성) |

**오해 교정:** dbt는 `staging.yml`을 위에서 아래로 읽으며 SQL을 차례대로 실행하는 프로그램이 아니다. 프로젝트 전체 리소스를 파싱하고, `ref()`·`source()`로 의존 관계(DAG)를 구성한 뒤 **명령어가 선택한 리소스**를 실행한다.

### 4-3. 프로젝트 처음 만들기(향후)

```bash
# 기존 GitHub 리포지토리 안에서 실행하는 계획
# dbt-bigquery 어댑터를 사용할 예정
dbt init chocolate_dbt

# 설정을 끝낸 다음 연결 확인
dbt debug
```

강의의 DuckDB는 **학습용 로컬 데이터베이스**이고, 우리 프로젝트의 목표 플랫폼은 **BigQuery**다. 실제 연결 방법과 `profiles.yml`은 실습 시 확정한다.

---

## 5. Source: 원본 데이터 위치를 등록하기

### 5-1. Source = 데이터를 dbt에 업로드하는 기능이 아님

이미 BigQuery에 존재하는 테이블을 **이름, 위치, 설명, 품질 규칙과 함께 등록**하는 메타데이터다.

- `database`: BigQuery **GCP 프로젝트 ID**
- `schema`: BigQuery **Dataset 이름**
- `tables`: 그 Dataset 안의 **테이블 이름 목록**
- `name`: dbt SQL에서 `source()`로 부를 논리적 Source 이름

### 5-2. `models/staging/staging.yml` 예시

```yaml
version: 2

sources:
  - name: raw_online
    database: your-gcp-project-id  # 실제 GCP 프로젝트 ID로 교체
    schema: raw_online            # 예시 Dataset 이름
    description: "온라인 쇼핑몰의 원본 테이블"
    tables:
      - name: orders
        description: "온라인 주문 원본"
        columns:
          - name: id              # 실제 PK 컬럼명 확인 필요
            data_tests:
              - not_null
              - unique
      - name: customers
      - name: products

  - name: raw_square
    database: your-gcp-project-id
    schema: raw_square
    description: "Square API에서 추출한 원본 데이터"
    tables:
      - name: orders
      - name: customers
      - name: locations
      - name: catalog_objects
```

> 실제 `raw_square` 데이터는 JSON 구조를 포함할 수 있어. BigQuery 적재 후 스키마/중첩 필드를 확인하고 모델 SQL을 작성해야 한다.

### 5-3. 모델에서 원본 참조

```sql
-- models/staging/stg_online_orders.sql
SELECT *
FROM {{ source('raw_online', 'orders') }}
```

BigQuery에서 실행할 때는 dbt가 `source()`를 실제 테이블 식별자로 치환한다(예: `` `your-gcp-project-id.raw_online.orders` ``).

**추가 장점:** Source 자체에 데이터 테스트를 정의할 수 있고, 설정을 추가하면 **Source Freshness(원본이 얼마나 최근에 갱신되었는지)**도 검사할 수 있다. 강의의 dbt 1.9 계열에서는 `dbt source freshness`를 사용한다. Freshness는 자동으로 원본을 갱신하지 않는다.

---

## 6. Model: SQL로 분석용 데이터 만들기

### 6-1. Model은 단순한 테이블 설계도가 아니다

**SQL 변환 로직을 정의한 파일**이다. dbt는 해당 SQL을 실행해 설정에 따라 BigQuery **VIEW / TABLE / INCREMENTAL** 등의 형태로 결과를 만든다.

#### Staging SQL(설명용)

```sql
-- models/staging/stg_online_orders.sql
-- id, total_amount는 학습용 가상 컬럼명: 실제 스키마 확인 필요
SELECT
    id AS order_id,
    SAFE_CAST(total_amount AS NUMERIC) AS total_amount
FROM {{ source('raw_online', 'orders') }}
```

#### Intermediate SQL(개념 예시)

```sql
-- models/intermediate/int_unified_orders.sql
-- 실제 Square 모델 컬럼을 통일한 뒤 사용한다는 가정
SELECT 'online' AS sales_channel, order_id, total_amount
FROM {{ ref('stg_online_orders') }}

UNION ALL

SELECT 'square' AS sales_channel, order_id, total_amount
FROM {{ ref('stg_square_orders') }}
```

#### Mart SQL(개념 예시)

```sql
-- models/marts/fct_orders.sql
SELECT
    sales_channel,
    order_id,
    total_amount
FROM {{ ref('int_unified_orders') }}
```

### 6-2. `ref()`로 이어지는 DAG

```mermaid
flowchart TD
    O[("source: raw_online.orders")] --> SO[stg_online_orders]
    Q[("source: raw_square.orders")] --> SQ[stg_square_orders]
    SO --> IU[int_unified_orders]
    SQ --> IU
    IU --> FO[fct_orders]
    IU --> FS[fct_daily_sales]
```

**중요:** `dbt run`은 YAML에 적힌 순서가 아니라 **이 의존 관계**를 이용해 실행한다. 서로 독립된 모델은 병렬 실행할 수 있다.

---

## 7. Jinja, `ref()`, `source()`, Macro

### 7-1. `{{ ... }}`는 SQL에 값을 끼워 넣는 Jinja 표현식

```sql
FROM {{ source('raw_online', 'orders') }}
FROM {{ ref('stg_online_orders') }}
```

| 문법 | 역할 |
|---|---|
| `{{ ... }}` | 식/함수 결과를 SQL에 삽입 |
| `{% ... %}` | macro, for, if 등 실행 제어/선언 |
| `{# ... #}` | Jinja 주석 |

### 7-2. `source()` vs `ref()`

| `source()` | `ref()` |
|---|---|
| **외부에서 이미 로드한** Raw 테이블 | **dbt가 관리하는** 다른 모델 |
| Source YAML에 선언되어야 함 | 해당 이름의 dbt 모델이 있어야 함 |
| 예: `source('raw_online', 'orders')` | 예: `ref('stg_online_orders')` |
| 계보상 **원본 진입점** 표시 | 계보상 **모델 간 의존성** 표시 |

### 7-3. Macro = 반복되는 SQL 로직의 재사용

```sql
-- macros/cents_to_dollars.sql
{% macro cents_to_dollars(column_name) %}
    ({{ column_name }} / 100.0)
{% endmacro %}
```

```sql
-- 모델에서 사용
SELECT {{ cents_to_dollars('price_cents') }} AS price_cad
FROM {{ ref('stg_square_catalog') }}
```

- Macro는 **SQL을 생성하는 재사용 함수**이지 자체 데이터 테이블이 아니다.
- 위 코드는 `price_cents` 컬럼이 **정수 센트**이고 값의 통화가 **CAD**라는 가정이 있어야만 의미가 정확하다. Square의 실제 금액 필드/통화는 확인해야 한다.
- `{% for ... %}`는 반복문이고 `{% macro ... %}`는 재사용 코드를 **정의**하는 문법이므로 다른 역할이다.

---

## 8. Test: Generic Test와 Singular Test

### 8-1. 핵심 원리

**dbt 데이터 테스트는 대개 '문제 있는 데이터'를 조회하는 SQL**이다.

- 결과가 **0행** → PASS
- 기본 설정에서 결과가 **1행 이상** → FAIL
- `dbt test`는 데이터를 **고치거나 자동 클리닝하지 않는다.**

### 8-2. Generic Test — YAML에 규칙 선언

```yaml
# models/staging/staging.yml (models 항목만 발췌)
models:
  - name: stg_online_orders
    description: "온라인 주문 기본 정리 모델"
    columns:
      - name: order_id
        description: "온라인 주문 식별자"
        data_tests:
          - not_null
          - unique
      - name: total_amount
        data_tests:
          - not_null
```

대표 내장 Generic Test:

| 테스트 | 검증할 것 |
|---|---|
| `not_null` | NULL이 없는가? |
| `unique` | 중복 값이 없는가? |
| `accepted_values` | 허용 목록에 없는 값이 존재하는가? |
| `relationships` | 참조 무결성이 유지되는가? |

**중요:** YAML은 **'어떤 모델의 어떤 컬럼에 어떤 테스트'**인지 정의한다. YAML 파일 한 개에 여러 모델의 테스트를 적어도 된다.

### 8-3. Singular Test — SQL 자체를 작성

파일: `tests/assert_no_negative_order_amount.sql`

```sql
SELECT order_id, total_amount
FROM {{ ref('stg_online_orders') }}
WHERE total_amount < 0
```

이 테스트는 `ref('stg_online_orders')`로 **검사 대상을 명시**한다. 특정 모델만 대상으로 할 수도 있고, 여러 모델/Source를 조인해 검사할 수도 있다.

> **비즈니스 규칙 주의:** 환불 등이 음수로 기록되는 모델이라면 '모든 음수 = 오류'는 틀릴 수 있다. 해당 컬럼의 의미와 취소/환불 정책을 확인하고 규칙을 정해야 한다.

### 8-4. 테스트를 실행하는 명령어

```bash
# 활성화된 Generic + Singular 데이터 테스트 모두 실행
dbt test

# 특정 테스트 하나만 실행
dbt test --select assert_no_negative_order_amount

# 특정 모델과 연결된 데이터 테스트 실행
dbt test --select stg_online_orders

# Source에 정의한 데이터 테스트만 실행
dbt test --select "source:*"
```

**오해 교정:** `tests/*.sql`을 만들었다고 해서 **별도의 실행 명령어가 필요한 것은 아니다.** `dbt test`가 자동으로 찾는다. 또한 테스트 SQL 파일을 YAML의 `data_tests:`에 다시 등록할 필요는 없다.

### 8-5. 테스트는 언제 실행할까?

```mermaid
flowchart TD
    A[데이터/비즈니스 규칙 확인] --> B[Model SQL 작성]
    B --> C[Generic/Singular Test 작성]
    C --> D[dbt build 또는 dbt run + dbt test]
    D --> E{테스트 통과?}
    E -- 예 --> F[다음 모델/계층 개발]
    E -- 아니오 --> G[실패 데이터 조회]
    G --> H[원본 문제? 모델 로직 문제? 테스트 기대값 문제?]
    H --> B
```

- 테스트는 **Staging에서만** 하는 것이 아니라 **Source / Staging / Intermediate / Marts** 각 단계에 걸쳐 작성할 수 있다.
- 매번 `dbt run` 후 `dbt test`를 **반드시** 따로 입력해야 하는 것은 아니다. 모델을 갱신하고 연결된 테스트도 실행하려면 `dbt build`를 쓸 수 있다.
- **주의:** `dbt test` 단독 실행은 이미 존재하는 DB 테이블/뷰를 검사한다. 모델 SQL을 고쳤다면 먼저 모델을 새로 빌드해야 수정 결과를 검사할 수 있다.

---

## 9. 테스트 실패 로그와 컴파일 SQL 디버깅

### 9-1. 오늘 강의에서 본 실패 예시

```text
FAIL accepted_values_taxi_rides_raw_payment_type__1__2__3__4__5__6
PASS not_null_taxi_rides_raw_fare_amount
PASS not_null_taxi_rides_raw_payment_type

Failure in test accepted_values_... (models/taxi_rides/model_properties.yml)
Got 1 result, configured to fail if != 0
compiled code at target/compiled/.../accepted_values_....sql

[WARNING] Unused config path models.nyc_yellow_taxi
```

| 로그 | 해석 |
|---|---|
| `FAIL accepted_values...payment_type` | `payment_type`에 허용값 1~6 이외의 값이 존재했거나 테스트 기대값과 맞지 않음 |
| `PASS not_null...` | NULL 검사 통과 |
| `(models/taxi_rides/model_properties.yml)` | **테스트가 정의된 YAML 위치**. 이 파일 자체가 반드시 잘못된 건 아님 |
| `Got 1 result` | 테스트 SQL이 반환한 **실패 결과 1행**. 원본 데이터 딱 1건이 잘못됐다는 뜻은 아님 |
| `target/compiled/...sql` | dbt가 만들어낸 **실제 검사 SQL** 파일 |
| `Unused config path ...` | `dbt_project.yml`에 사용되지 않는 설정 경로가 있음. 테스트 실패와는 별개의 경고 |

> `accepted_values` 같은 테스트는 잘못된 값을 **그룹화해 출력**할 수도 있다. '결과 1행' 안에 실제 오류 원본 데이터는 수십 건이 들어 있을 수 있다.

### 9-2. 컴파일 SQL을 DB Tool에서 직접 실행해 보기

1. `dbt test` 로그에서 **FAIL 테스트 이름** 확인
2. `target/compiled/` 아래 **컴파일된 `.sql` 파일** 열기
3. DuckDB용 DB Tool 또는 BigQuery SQL Editor에 복사해서 실행
4. 잘못된 값과 발생 건수를 추가로 확인

```sql
-- 강의의 DuckDB 테이블 경로에 맞게 수정한 디버깅 SQL 예시
SELECT
    payment_type,
    COUNT(*) AS row_count
FROM main.taxi_rides_raw
WHERE payment_type NOT IN (1, 2, 3, 4, 5, 6)
  AND payment_type IS NOT NULL
GROUP BY payment_type
ORDER BY row_count DESC
```

**가상 결과:**

| payment_type | row_count |
|---:|---:|
| 0 | 23 |
| 7 | 5 |

→ 허용되지 않은 **두 종류의 값**이 있고, **원본 행 총 28건**이 해당한다는 뜻이다.

### 9-3. 실패를 발견했다고 바로 데이터를 고칠까?

아니. **실패 원인을 구분**해야 한다.

1. **원본 오류:** 실제로 데이터에 비정상 코드가 들어옴
2. **모델 로직 오류:** 잘못된 CAST, JOIN, 필터 등이 발생
3. **테스트 기대값 오류:** 업무상 유효한 새로운 상태/코드인데 허용 목록이 오래됨

### 9-4. 재실행하면 컴파일 SQL은 어떻게 될까?

- 모델 또는 테스트를 수정한 후 `dbt test`를 다시 실행하면 **선택된 테스트 SQL이 다시 컴파일**된다.
- **같은 경로의 결과물은 일반적으로 갱신/덮어쓰기**된다.
- 테스트 이름이나 경로가 바뀌면 **이전 생성 파일이 남을 수 있으므로** `target/compiled/`를 변경 이력 보관 장소로 생각하면 안 된다.
- **직접 고칠 파일은 `models/*.sql`, `models/*.yml`, `tests/*.sql`** 등 소스 파일이다.
- `target/`은 일반적으로 Git 추적에서 제외한다.

---

## 10. Snapshot: 변경 이력 남기기

### 10-1. Snapshot은 왜 필요할까?

원본 테이블의 한 행을 **UPDATE로 덮어쓰면 이전 값이 사라질 수 있다.** dbt Snapshot은 관측한 변경을 버전별로 기록한다. 흔히 **SCD Type 2** 방식이라고 한다.

**초콜릿 가격 변경 예시(가상):**

| 시점 | `products`의 상품 101 가격 |
|---|---:|
| 11/01 | $5.00 |
| 11/06 | $6.00 (UPDATE) |

일반적인 현재 상태 테이블에는 **$6.00만** 남을 수 있다.

Snapshot 결과 예시:

| product_id | price | dbt_valid_from | dbt_valid_to |
|---:|---:|---|---|
| 101 | $5.00 | 2026-11-01 | 2026-11-06 |
| 101 | $6.00 | 2026-11-06 | NULL (현재) |

```mermaid
sequenceDiagram
    participant Raw as Raw products
    participant DBT as dbt snapshot
    participant Hist as products_snapshot
    Note over Raw,Hist: 학습용 가상 일정
    Raw->>DBT: 11/01 상품 101 = $5
    DBT->>Hist: 최초 버전 저장 ($5, valid_to=NULL)
    Raw->>Raw: 11/06 가격 $6으로 UPDATE
    Raw->>DBT: 11/06 상품 101 = $6
    DBT->>Hist: $5 버전 종료 + $6 신규 버전 추가
```

**주의:** 실제 `dbt_valid_from`/`dbt_valid_to` 값은 선택한 Snapshot 전략, 원본 `updated_at` 존재 여부, 관측 시점에 따라 달라진다. 위 표의 날짜는 개념 설명이다.

### 10-2. Snapshot은 반드시 원본 데이터로만 만드나?

아니. Snapshot은 **Source** 또는 **dbt Model**을 기반으로 만들 수 있다.

```yaml
relation: source('raw_online', 'products')
# 또는
relation: ref('stg_online_products')
```

보통 **Raw Source나 아주 가볍게 정리된 Staging 모델**을 기준으로 변경 이력을 관리하는 것이 이해하기 쉽다. Marts의 복잡한 계산 결과는 로직 수정만으로도 값이 달라질 수 있으므로 신중히 선택한다.

### 10-3. dbt 1.9+ YAML Snapshot 예시

파일: `snapshots/products_snapshot.yml`

```yaml
snapshots:
  - name: products_snapshot
    relation: source('raw_online', 'products')
    config:
      schema: snapshots
      unique_key: id        # 가상 상품 고유 컬럼
      strategy: check
      check_cols:
        - price             # 가상 가격 컬럼
```

```bash
# 최초 실행: 현재 데이터를 기준으로 이력 테이블 생성
# 다음 실행: 이전 버전과 비교해 변경/신규 행 반영
dbt snapshot
```

**두 가지 감지 전략**

| 전략 | 어떻게 변경을 찾나? | 언제 사용? |
|---|---|---|
| `timestamp` | 신뢰할 수 있는 `updated_at`이 바뀌었는지 확인 | `updated_at` 품질이 좋다면 우선 고려 |
| `check` | 지정한 컬럼(`check_cols`) 값을 비교 | 신뢰할 `updated_at`이 없을 때 |

**반드시 기억할 한계**

- Snapshot을 **처음 실행하기 전의 과거 변경 이력은 자동 복원되지 않는다.**
- 하루에 한 번 Snapshot을 실행하면, 그 사이에 여러 번 바뀌었다가 원래 값으로 돌아온 변경은 놓칠 수 있다.
- 변경을 관측하려면 **BigQuery Source의 데이터도 실제로 갱신되어야** 한다.
- 모든 테이블에 Snapshot이 필요한 것은 아니다. 상품 가격, 고객 등급, 주문 상태처럼 **과거 상태가 분석에 중요할 때** 선택한다.
- 주문 당시 단가가 `order_items`에 정확히 보관되어 있다면, 과거 매출 계산에 상품 가격 Snapshot이 반드시 필요하지 않을 수 있다.

### 10-4. GCS Raw Snapshot과 dbt Snapshot은 다른 것!

| GCS에 저장하는 Raw 파일 스냅샷 | dbt Snapshot |
|---|---|
| 특정 시점의 **파일 전체 복사본/적재 기록** | **행별 컬럼 값 변경 이력** |
| 보통 파일·배치 단위 | 보통 키(`unique_key`)별 버전 관리 |
| 수집·재처리·백업 용도 | SCD Type 2 / 이력 분석 용도 |

---

## 11. dbt 명령어와 실제 실행 흐름

| 명령어 | 무엇을 하나? | 주의할 점 |
|---|---|---|
| `dbt init chocolate_dbt` | 새 dbt 프로젝트 생성 | 연결/프로젝트 설정 필요 |
| `dbt debug` | 프로필과 연결 상태 점검 | 데이터 모델 생성 아님 |
| `dbt run` | SQL Model 실행하여 Relation 생성/갱신 | **데이터 테스트 자동 실행 X** |
| `dbt test` | Generic + Singular Data Test 실행 | 기존 Relation 검사, **모델 재생성 X** |
| `dbt build` | 모델·테스트·Snapshot·Seed 등 선택된 리소스 빌드 | DAG에 따라 실행, Snapshot도 포함될 수 있음 |
| `dbt snapshot` | 변경 이력 스냅샷 반영 | 주기적으로 실행해야 변경 관측 가능 |
| `dbt compile` | Jinja가 반영된 SQL 생성/검토 | 별도의 선행 필수 단계 아님 |
| `dbt source freshness` | Source의 최신 적재 시점 점검(dbt 1.9 계열) | 적절한 Freshness 설정 필요 |
| `dbt docs generate` | 프로젝트 문서/계보 메타데이터 생성 | 파일만 만들고 온라인에 자동 공개 X |
| `dbt docs serve` | 로컬 문서 웹 화면 실행 | 기본 포트가 다른 서비스와 충돌할 수 있음 |

### 🧭 `dbt run`과 `dbt test`를 꼭 매번 따로 해야 할까?

**아니야.**

```bash
# 방법 1: 수동으로 나누기
dbt run
dbt test

# 방법 2: 모델 빌드와 관련 테스트를 연결해 실행
dbt build
```

단, `dbt build`는 **프로젝트에 정의한 Snapshot/Seed 등도 포함할 수 있으므로** 전체 또는 선택 범위를 확인하는 습관이 좋다.

### 🧭 특정 테스트/모델만 실행

```bash
dbt run --select stg_online_orders
dbt test --select stg_online_orders
dbt test --select assert_no_negative_order_amount
dbt build --select stg_online_orders
```

### 🧭 SQL 한 파일 = 실행 쿼리 한 개?

- 보통 `models/*.sql` 한 개가 **dbt 모델 하나**다.
- 한 모델 SQL 내부에 여러 **CTE(`WITH`)**나 JOIN이 있을 수 있다.
- dbt가 모델 간 실행 순서를 결정하는 핵심은 **파일 이름순이 아니라 `ref()`로 연결한 DAG**다.

---

## 12. Documentation · Lineage · CI/CD와 Kestra

### 12-1. dbt Documentation

`models/*.yml`에 모델과 컬럼의 의미를 기록할 수 있다.

```yaml
models:
  - name: stg_online_orders
    description: "온라인 주문 Raw 데이터를 정리한 Staging 모델"
    columns:
      - name: order_id
        description: "온라인 주문을 식별하는 ID"
      - name: total_amount
        description: "분석에서 사용할 주문 총액(단위/환불 기준은 확인 필요)"
```

```bash
dbt docs generate
dbt docs serve
```

- 문서는 **프로젝트가 끝난 뒤 한 번에 작성하기보다 모델을 만들면서 함께 작성**한다.
- dbt Docs는 모델 설명, 컬럼, 테스트, **Lineage 그래프(DAG)**를 이해하는 데 유용하다.
- `docs generate` 결과가 GitHub에 자동 공개되는 것은 아니다. 별도 배포/호스팅이 필요하다.

### 12-2. Kestra와 CI/CD 역할 분리

| 도구 | 주로 하는 일 |
|---|---|
| **Kestra** | 매일/매월 **데이터 파이프라인 실행 일정과 작업 순서** 관리 |
| **dbt** | BigQuery에서 SQL 모델 변환·검증·변경 이력 기록 |
| **Git/GitHub** | SQL/YAML/Python 등 **소스코드 버전 관리** |
| **GitHub Actions(CI/CD)** | 코드 변경 시 자동 검증, 배포 프로세스 등 |
| **Power BI / Looker Studio** | Mart를 연결해 대시보드 표시/새로고침 |

```mermaid
flowchart TD
    K["Kestra schedule / 수동 실행"] --> P[Python: 원본 수집]
    P --> L[PostgreSQL + 향후 BigQuery Raw 업데이트]
    L --> F[dbt source freshness 선택 사항]
    F --> B[dbt build / 선택된 모델·테스트·스냅샷]
    B --> BI[BI 데이터 새로고침·조회]
    GH["GitHub Actions<br/>코드 변경 CI/CD"] -. "SQL/YAML 검증·배포" .-> B
```

> BI 대시보드가 **어떤 시점에 실제로 새 데이터를 표시하는지**는 BI 도구의 연결 방식과 새로고침 설정에 달려 있다.

---

## 13. 초콜릿 프로젝트에 적용할 설계 초안

### 13-1. Phase 4를 둘로 나눠 생각하기

| 구간 | 할 일 | 상태 |
|---|---|---|
| **Phase 4A — Cloud Ingestion** | PostgreSQL export → GCS → BigQuery Raw | 🔜 아직 구현 전, 잠시 보류 |
| **Phase 4B — dbt Transformation** | BigQuery Raw → Staging → Intermediate → Marts | 📖 개념 학습 중 |

### 13-2. 우선 모델링할 만한 데이터(안)

| 계층 | 모델 후보 | 변환 목적 |
|---|---|---|
| Source | `raw_online.orders` | 온라인 주문 원본 등록 |
| Source | `raw_square.orders` | Square 주문 원본 등록 |
| Staging | `stg_online_orders` | 주문 ID/날짜/금액 형식 통일 |
| Staging | `stg_square_orders` | Square 주문 JSON 구조 파악, 필요한 필드 추출 |
| Intermediate | `int_unified_orders` | 온라인·오프라인 주문 결합 및 중복/취소 정책 정의 |
| Marts | `fct_orders` | 채널별 주문 팩트 |
| Marts | `fct_daily_sales` | 날짜·채널별 매출 집계 |

### 13-3. 계층별 테스트 후보

| 위치 | 테스트 예시 | 주의할 점 |
|---|---|---|
| Source | 주문 PK `not_null`, `unique` | Raw에 중복 수집이 허용되는 설계인지 먼저 확인 |
| Staging | 날짜/금액 변환 실패 시 NULL 점검 | 원본 타입과 빈 문자열 규칙 고려 |
| Intermediate | 온라인·Square 주문 통합 시 중복 키 검사 | 채널이 다르면 같은 주문 ID가 가능할 수 있음 → 복합 키 필요 |
| Marts | 주문 상세 합계와 일별 매출 합계 대조 | 취소·환불·세금·배송비 포함 범위 정의 |
| Snapshot | 상품 가격·상태 변경 이력 | 실제 Raw 갱신 방식 확인 |

### 13-4. 우리 프로젝트에서 미리 결정해야 할 비즈니스 질문

1. **주문 총액**은 세금·할인·배송비를 포함할까?
2. **취소 및 환불**은 매출에 어떻게 반영할까?
3. **Square 주문과 온라인 주문**의 ID 중복 가능성은 없을까?
4. **상품 가격 변경 이력**을 별도로 보관할 필요가 있을까?
5. **원본 적재 방식**이 `TRUNCATE + INSERT`라면, Snapshot 실행 시 원본 테이블에 어떤 레코드들이 관측되는가?

> dbt를 잘 쓰려면 **SQL 기술뿐 아니라 원본 구조와 비즈니스 규칙을 먼저 이해하는 것**이 중요하다.

---

## 14. 헷갈렸던 질문 Q&A

<details>
<summary><strong>Q1. dbt Model은 분석용 테이블을 구조화한다는 뜻인가?</strong></summary>

**거의 맞다.** 정확하게는 어떤 데이터를 읽고 어떤 SQL 변환을 수행해 어떤 분석용 결과(Table/View 등)를 생성할지 정의한 **실행 로직**이다.
</details>

<details>
<summary><strong>Q2. Source는 원본 데이터를 dbt에 올리는(업로드하는) 건가?</strong></summary>

**아니다.** BigQuery 등에 이미 존재하는 원본의 **위치와 이름을 등록**하고 `source()`로 참조한다.
</details>

<details>
<summary><strong>Q3. dbt는 YAML을 맨 먼저 읽고 적힌 대로 SQL을 순서대로 실행하나?</strong></summary>

**그렇게 실행되지 않는다.** 프로젝트의 YAML·SQL 등을 파싱하고 의존성을 구성한 뒤 `run`/`test`/`build`에 맞는 리소스를 실행한다.
</details>

<details>
<summary><strong>Q4. Singular Test를 작성하면 어떤 SQL 모델이 테스트 대상인지 알아야 하나?</strong></summary>

**그렇다.** 테스트 작성자는 대상 데이터와 비즈니스 규칙을 알아야 한다. 보통 `{{ ref('모델명') }}` 또는 `{{ source('소스명', '테이블명') }}`를 사용해서 SQL에서 검사 대상을 지정한다.
</details>

<details>
<summary><strong>Q5. `dbt test`는 YAML에 적힌 Generic Test만 실행하나?</strong></summary>

**아니다.** `models/*.yml`에 정의한 Generic Data Test와 `tests/*.sql`에 작성한 Singular Data Test를 모두 실행한다.
</details>

<details>
<summary><strong>Q6. `dbt test` 전에 항상 `dbt run`을 해야 하나?</strong></summary>

**항상은 아니다.** 대상 모델이 이미 DB에 존재하면 `dbt test`를 단독 실행할 수 있다. 모델 변경을 반영해 검사하려면 먼저 갱신하거나 `dbt build`를 사용한다.
</details>

<details>
<summary><strong>Q7. FAIL 로그의 YAML 경로가 잘못된 파일이라는 뜻인가?</strong></summary>

**반드시 그렇지는 않다.** 보통 **실패한 테스트가 선언된 위치**를 뜻한다. 실제 원본 데이터, 모델 SQL, 테스트 기대값 중 어디가 문제인지 추가로 조사해야 한다.
</details>

<details>
<summary><strong>Q8. 정확히 어떤 데이터 때문에 실패했는지 확인하려면?</strong></summary>

`target/compiled/`에 생성된 테스트 SQL을 살펴보고 **DB Tool 또는 BigQuery SQL Editor에서 직접 실행**한다. 필요하면 원본 행 확인용 SELECT를 추가로 작성한다.
</details>

<details>
<summary><strong>Q9. `dbt test`를 다시 실행하면 컴파일 SQL은 덮어쓰기 되나?</strong></summary>

**일반적으로 선택된 테스트의 같은 경로 결과물은 갱신된다.** 다만 테스트의 이름/경로가 바뀌면 오래된 산출물이 남을 수 있다. **컴파일 결과물이 아닌 소스 SQL/YAML을 수정**한다.
</details>

<details>
<summary><strong>Q10. Snapshot은 반드시 원본 데이터 기준인가?</strong></summary>

**아니다.** `source()` 또는 `ref()`로 Source나 Model을 참조할 수 있다. 과거 값 보존 목적이라면 보통 원본 또는 가볍게 정리된 Staging 모델을 우선 고려한다.
</details>

<details>
<summary><strong>Q11. Snapshot을 쓰면 모든 과거 데이터를 복원할 수 있나?</strong></summary>

**아니다.** Snapshot을 실행하면서 **관측한 변경**만 저장한다. 실행 이전의 이력이나 실행 간 놓친 변경은 자동 복구할 수 없다.
</details>

<details>
<summary><strong>Q12. 문서는 언제 작성하나?</strong></summary>

모델을 만들면서 **설명과 데이터 품질 기준을 함께 기록**한다. `dbt docs generate`/`serve`로 로컬에서 확인할 수 있다.
</details>

---

## 15. 복습 체크리스트 & 다음 실습

### ✅ 오늘 이해했는지 스스로 확인하기

- [ ] Source는 원본 업로드가 아닌 **원본 테이블 등록**이라는 차이를 설명할 수 있다.
- [ ] `source()`와 `ref()`의 역할을 설명할 수 있다.
- [ ] Staging/Intermediate/Marts와 dev/stg/prod 환경을 구분할 수 있다.
- [ ] `models/*.sql`, `models/*.yml`, `tests/*.sql`의 역할을 구분할 수 있다.
- [ ] Generic Test와 Singular Test를 각각 하나씩 작성할 수 있다.
- [ ] FAIL 로그에서 테스트 이름·선언 파일·컴파일 SQL 경로를 찾을 수 있다.
- [ ] 컴파일된 테스트 SQL을 DB에서 실행해 실패 값을 조사할 수 있다.
- [ ] `dbt run`, `dbt test`, `dbt build`, `dbt snapshot`의 차이를 말할 수 있다.
- [ ] Snapshot이 현재 값뿐 아니라 **관측한 과거 값**을 보존하는 방식을 이해한다.
- [ ] Snapshot과 GCS 파일 스냅샷의 차이를 설명할 수 있다.

### 🚀 초콜릿 프로젝트 적용 순서(학습 계획)

1. **강의의 DuckDB 예제로 `source()`·`ref()`·테스트·Snapshot 반복 실습**
2. 기존 GitHub 리포지토리 내부에 `chocolate_dbt/` 프로젝트 초기화
3. `staging.yml`, `intermediate.yml`, `marts.yml` 세 파일 규칙 적용
4. **BigQuery Raw 준비 시점에** 실제 컬럼 구조를 확인하고 `sources:` 등록
5. `stg_online_orders` → `stg_square_orders` → `int_unified_orders` → Marts 순서로 모델 구현
6. 계층별 Generic/Singular Test 작성, 실패 SQL 직접 조회해 확인
7. 필요할 때만 상품 등 변경 이력 Snapshot 추가
8. dbt Docs와 Kestra 실행 흐름 연결

---

## 16. 공식 참고 링크

이 문서는 **오늘 학습한 질문과 초콜릿 프로젝트 설계 방향**을 중심으로 정리했고, dbt 기능/명령어는 공식 문서를 참고해 점검했다.

- [dbt 공식 문서 — Sources](https://docs.getdbt.com/docs/build/sources)
- [dbt 공식 문서 — Data Tests (Generic / Singular)](https://docs.getdbt.com/docs/build/data-tests)
- [dbt 공식 문서 — Snapshots (dbt 1.9+ YAML)](https://docs.getdbt.com/docs/build/snapshots)
- [dbt 공식 문서 — `dbt build`](https://docs.getdbt.com/reference/commands/build)
- [dbt 공식 문서 — `dbt compile`](https://docs.getdbt.com/reference/commands/compile)
- [dbt 공식 문서 — `dbt init`](https://docs.getdbt.com/reference/commands/init)

---

> ### ✨ 오늘의 한 줄 결론
> **Source로 원본을 연결하고 → Model로 데이터를 정리·통합·집계하고 → Test로 품질을 확인하고 → Snapshot으로 중요한 변경 이력을 보존한다.**  
> 이 모든 작업을 dbt가 이해할 수 있는 **SQL + YAML + 의존 관계(DAG)**로 관리하는 것이 핵심이다. 🍫
