# 🚚 Phase 2 — Online → PostgreSQL Data Ingestion

이 문서는 **Charlie’s Chocolate Factory — Omnichannel Retail Data Platform** 프로젝트의 Phase 2에서 구현한  
**Online Store 데이터 → PostgreSQL 적재 과정**을 정리한 문서이다.

나중에 프로젝트를 다시 열었을 때도

- 왜 PostgreSQL을 사용했는지
- 어떤 데이터를 적재했는지
- ONLINE 데이터만 어떻게 분리했는지
- PostgreSQL Schema를 왜 직접 정의했는지
- Python Pipeline이 어떻게 동작하는지

를 쉽게 이해할 수 있도록 기록한다.

---

# 1. 🎯 이번 단계의 목표

Phase 1에서는 실제 리테일 환경을 시뮬레이션하기 위해 다음 Source System을 만들었다.

```text
ONLINE CHANNEL
Online Store (Lovable)

RETAIL CHANNEL
POS Simulator
    ↓
Square Sandbox
```

Phase 2에서는 각 Source System에서 발생한 데이터를 Data Platform으로 수집한다.

이번 작업에서는 먼저 **Online Channel 데이터**를 대상으로 Local PostgreSQL ingestion pipeline을 구현했다.

```text
Online Store
     ↓
CSV Export
     ↓
Python / Pandas
     ↓
ONLINE Data Filtering
     ↓
PostgreSQL
     ↓
SQL Validation
```

PostgreSQL은 최종 Data Warehouse가 아니라  
**Cloud 환경으로 이동하기 전에 ingestion 과정을 개발하고 테스트하기 위한 Local Database**로 사용한다.

최종 Data Warehouse는 이후 **BigQuery**를 사용할 예정이다.

---

# 2. 🐳 Local Data Environment

PostgreSQL은 Docker Container에서 실행한다.

```text
Docker Desktop
      ↓
PostgreSQL Container
      ↓
chocolate_db
```

현재 PostgreSQL 접속 정보:

```text
Host     : localhost
Port     : 5432
Database : chocolate_db
User     : chocolate
```

DBeaver를 PostgreSQL Client로 사용한다.

```text
PostgreSQL
     ↓
DBeaver
     ↓
Table 확인 / SQL 실행 / Validation
```

DBeaver 자체가 데이터를 저장하는 것은 아니다.

실제 데이터는 PostgreSQL에 저장된다.

---

# 3. 📦 Python PostgreSQL 연결

Python Pipeline에서 PostgreSQL과 연결하기 위해 다음 라이브러리를 사용한다.

```text
Pandas
SQLAlchemy
psycopg2-binary
```

연결 구조:

```text
Python
  ↓
SQLAlchemy
  ↓
psycopg2
  ↓
PostgreSQL
```

PostgreSQL 연결 코드는 다음 파일에서 관리한다.

```text
src/
└── load/
    └── postgres/
        └── connection.py
```

---

# 4. 📂 현재 관련 프로젝트 구조

```text
chocolate-commerce-data-platform/
│
├── data/
│   └── raw/
│       ├── products_export.csv
│       ├── customers_export.csv
│       ├── customer_addresses_export.csv
│       ├── orders_export.csv
│       └── order_items_export.csv
│
├── src/
│   ├── extract/
│   │   └── load_csv.py
│   │
│   ├── load/
│   │   └── postgres/
│   │       ├── connection.py
│   │       └── load_table.py
│   │
│   └── pipelines/
│       └── online_to_postgres.py
│
├── sql/
│   ├── schema/
│   │   └── create_raw_online_tables.sql
│   │
│   └── validation/
│       └── validate_online_ingestion.sql
│
└── docker-compose.yml
```

---

# 5. 📥 Online Source Data

현재 Online Pipeline에서 사용하는 데이터는 다음과 같다.

```text
products
customers
customer_addresses
orders
order_items
```

원본 CSV에는 ONLINE과 RETAIL 데이터가 함께 존재하는 경우가 있기 때문에  
Pipeline에서 Online Channel 데이터만 선택해서 적재한다.

---

# 6. 🍫 Products

상품 데이터는 Online Store와 POS에서 공통으로 사용하는 Product Master 성격의 데이터이다.

현재는 전체 상품 데이터를 적재한다.

```text
products_export.csv
        ↓
Pandas
        ↓
raw_online.products
```

주요 컬럼:

```text
id
product_id
sku
product_name
category
price
description
is_best_seller
active_status
created_at
updated_at
```

Square 연동 과정에서 생성된 다음 컬럼도 원본에 포함되어 있다.

```text
square_catalog_object_id
square_sync_status
square_synced_at
square_sync_error
```

Raw Layer에서는 원본 데이터를 최대한 유지하기 위해 해당 컬럼들도 함께 저장한다.

---

# 7. 👤 Customers

`customers_export.csv`에는 POS 가입 고객과 ONLINE 가입 고객이 함께 존재한다.

구분 컬럼:

```text
signup_channel
```

예:

```text
POS
ONLINE
```

Online Pipeline에서는 다음 조건으로 필터링한다.

```python
online_customers_df = customers_df[
    customers_df["signup_channel"]
    .str.strip()
    .str.upper()
    == "ONLINE"
].copy()
```

흐름:

```text
customers_export.csv
        ↓
signup_channel == ONLINE
        ↓
Online Customers
        ↓
raw_online.customers
```

---

# 8. 🏠 Customer Addresses

`customer_addresses_export.csv`에는 ONLINE / POS 채널 정보가 직접 존재하지 않는다.

대신 Customer와 다음 관계를 가지고 있다.

```text
customers.id
      ↕
customer_addresses.customer_id
```

따라서 먼저 ONLINE Customer의 ID를 가져온다.

```python
online_customer_ids = online_customers_df["id"]
```

그리고 해당 Customer ID를 가진 주소만 선택한다.

```python
online_addresses_df = addresses_df[
    addresses_df["customer_id"].isin(
        online_customer_ids
    )
].copy()
```

흐름:

```text
ONLINE Customers
       ↓
Customer ID 목록
       ↓
customer_addresses
       ↓
customer_id 비교
       ↓
Online Customer Addresses
       ↓
raw_online.customer_addresses
```

---

# 9. 🛒 Orders

`orders_export.csv`에는 ONLINE 주문과 RETAIL 주문이 함께 존재한다.

구분 컬럼:

```text
channel
```

Online 주문만 다음 조건으로 선택한다.

```python
online_orders_df = orders_df[
    orders_df["channel"]
    .str.strip()
    .str.upper()
    == "ONLINE"
].copy()
```

흐름:

```text
orders_export.csv
       ↓
channel == ONLINE
       ↓
Online Orders
       ↓
raw_online.orders
```

---

# 10. 🍫 Order Items

`order_items_export.csv`에는 `channel` 컬럼이 존재하지 않는다.

따라서 Online Order와의 관계를 이용한다.

여기서 중요한 점은 Orders 테이블에 ID가 두 종류 존재한다는 것이다.

```text
orders.id
= UUID

orders.order_id
= Business Order ID
  예: CCF-WEB-000001
```

`order_items.order_id`는 UUID인 `orders.id`가 아니라  
**`orders.order_id`와 연결된다.**

정확한 관계:

```text
orders.order_id
       ↕
order_items.order_id
```

따라서 Online Order Items 필터링은 다음과 같이 한다.

```python
online_order_ids = online_orders_df["order_id"]

online_order_items_df = order_items_df[
    order_items_df["order_id"].isin(
        online_order_ids
    )
].copy()
```

흐름:

```text
Online Orders
      ↓
order_id 목록
      ↓
Order Items
      ↓
order_id 비교
      ↓
Online Order Items
      ↓
raw_online.order_items
```

---

# 11. 🗄️ PostgreSQL Raw Schema

처음에는 Pandas의 `to_sql()`이 자동으로 PostgreSQL 테이블을 생성하도록 사용했다.

하지만 이 방식은 Pandas가 데이터 타입을 자동 추론하기 때문에  
원하는 Database Schema를 명확하게 관리하기 어렵다.

예:

```text
price
→ NUMERIC

quantity
→ INTEGER

created_at
→ TIMESTAMPTZ

phone
→ VARCHAR
```

따라서 PostgreSQL Schema를 SQL로 직접 정의하도록 변경했다.

Schema 생성 파일:

```text
sql/schema/create_raw_online_tables.sql
```

PostgreSQL에는 별도의 Raw Schema를 생성한다.

```text
raw_online
```

현재 구조:

```text
PostgreSQL
└── raw_online
    ├── products
    ├── customers
    ├── customer_addresses
    ├── orders
    └── order_items
```

이 Schema는 DBeaver SQL Editor에서 직접 생성했다.

---

# 12. 🔄 데이터 적재 방식 변경

초기 Pipeline에서는:

```python
if_exists="replace"
```

방식을 사용했다.

하지만 `replace` 방식은 기존 PostgreSQL 테이블을 삭제한 후  
Pandas가 새로운 테이블을 다시 생성한다.

```text
replace

기존 Table
   ↓
DROP
   ↓
Pandas가 새 Table 생성
```

이 경우 직접 정의한 PostgreSQL Schema와 Data Type이 사라질 수 있다.

따라서 적재 방식을 다음과 같이 변경했다.

```text
TRUNCATE
   +
APPEND
```

흐름:

```text
기존 PostgreSQL Table
        ↓
TRUNCATE
        ↓
기존 데이터만 삭제
        ↓
Table Structure 유지
        ↓
Pandas append
        ↓
새 데이터 INSERT
```

이 방식의 장점:

```text
Table Structure 유지
Data Type 유지
중복 적재 방지
Pipeline 재실행 가능
```

현재 `load_table.py`가 이 역할을 담당한다.

---

# 13. 🧱 Raw Layer 설계 원칙

현재 PostgreSQL은 Raw Layer 성격으로 사용한다.

따라서 원본 데이터를 지나치게 정제하거나 삭제하지 않는다.

기본 원칙:

```text
Source Data
      ↓
Raw Layer
      ↓
원본 최대한 보존
      ↓
Validation
      ↓
Transformation
```

따라서 현재 Raw Schema에는 강한 Constraint를 많이 걸지 않았다.

예:

```text
PRIMARY KEY
FOREIGN KEY
UNIQUE
NOT NULL
```

등은 최소화했다.

보다 엄격한 데이터 품질 관리와 정제는 이후  
**Staging / Transformation Layer**에서 수행할 예정이다.

---

# 14. 🔎 Post-load Validation

현재는 Source 데이터를 먼저 PostgreSQL에 적재한 뒤  
DBeaver SQL Editor에서 Validation을 수행한다.

Validation 파일:

```text
sql/validation/validate_online_ingestion.sql
```

주요 검증 항목:

```text
Row Count
ID NULL 확인
ID 중복 확인
ONLINE Channel 확인
Customer 관계 확인
Order 관계 확인
```

예:

```sql
SELECT channel, COUNT(*)
FROM raw_online.orders
GROUP BY channel;
```

Online Pipeline이므로 정상 결과에는 ONLINE만 존재해야 한다.

Order Item 관계 검증:

```sql
SELECT oi.*
FROM raw_online.order_items oi
LEFT JOIN raw_online.orders o
    ON oi.order_id = o.order_id
WHERE o.order_id IS NULL;
```

결과가 0건이면 모든 Order Item이 정상적인 Online Order와 연결되어 있다는 의미이다.

---

# 15. 🔁 현재 Online Ingestion Pipeline

현재 완성된 전체 흐름:

```text
ONLINE STORE
     ↓
CSV Export
     ↓
Python / Pandas
     ↓
Channel Filtering
     ↓
PostgreSQL
     ↓
raw_online Schema
     ↓
Post-load SQL Validation
```

조금 더 자세히 표현하면:

```text
products_export.csv
        ↓
raw_online.products


customers_export.csv
        ↓
ONLINE Filtering
        ↓
raw_online.customers


customer_addresses_export.csv
        ↓
ONLINE Customer ID Filtering
        ↓
raw_online.customer_addresses


orders_export.csv
        ↓
ONLINE Filtering
        ↓
raw_online.orders


order_items_export.csv
        ↓
Online Order ID Filtering
        ↓
raw_online.order_items
```

---

# 16. 📌 주요 설계 결정

## Online / Retail 데이터를 분리한다

최종 프로젝트에서는 Online Channel과 Square POS 데이터를 처음부터 섞지 않는다.

```text
ONLINE
   ↓
raw_online

RETAIL
   ↓
raw_square
```

나중에 BigQuery Transformation 단계에서 두 데이터를 통합한다.

```text
raw_online
      \
       \
        → Unified Model
       /
      /
raw_square
```

---

## Raw Layer에서는 원본을 최대한 보존한다

이 단계에서는 데이터를 완벽하게 정제하기보다 Source Data를 보존하는 것을 우선한다.

```text
Raw
 ↓
Staging
 ↓
Intermediate
 ↓
Mart
```

Data Cleaning과 Standardization은 이후 Transformation 단계에서 수행한다.

---

## PostgreSQL은 최종 목적지가 아니다

PostgreSQL은 Local Data Engineering 환경이다.

최종 구조는 다음과 같다.

```text
Online Store
      ↓
Python Pipeline
      ↓
GCS
      ↓
BigQuery Raw Layer
      ↓
Transformation
      ↓
Unified Omnichannel Model
      ↓
Power BI
```

---

# 17. ✅ 현재 완료 상태

```text
Phase 2 — Online Data Ingestion

[x] Docker Desktop 설치
[x] PostgreSQL Container 구성
[x] chocolate_db 생성
[x] DBeaver 연결

[x] Python → PostgreSQL Connection
[x] Products Ingestion
[x] Online Customers Filtering
[x] Customer Addresses 관계 기반 Filtering
[x] Online Orders Filtering
[x] Order Items 관계 기반 Filtering

[x] raw_online Schema 설계
[x] PostgreSQL Data Type 정의
[x] create_raw_online_tables.sql 작성
[x] TRUNCATE + APPEND 적재 방식 적용
[x] Post-load Validation SQL 작성
```

---

# 18. ▶️ 다음 단계

다음 작업:

```text
Pipeline 구조 리팩토링
```

현재 `online_to_postgres.py`에 여러 Dataset 처리 로직이 한 파일에 존재한다.

다음 단계에서는 코드를 재사용하기 쉽고 관리하기 편하도록 구조를 정리한다.

그 이후:

```text
Pipeline Refactoring
        ↓
Square API Extraction Pipeline
        ↓
GCP Project Setup
        ↓
Google Cloud Storage
        ↓
BigQuery Raw Layer
```

순서로 진행할 예정이다.

---

# 🎯 현재 위치

```text
Phase 1
Source System Simulation
✅ 완료

       ↓

Phase 2
Data Ingestion & Storage
🟡 진행 중

       ├── Online → PostgreSQL ✅
       │
       ├── Pipeline Refactoring ← NEXT
       │
       ├── Square API Extraction
       │
       ├── GCS
       │
       └── BigQuery Raw Layer

       ↓

Phase 3
Transformation & Modeling

       ↓

Phase 4
Analytics & BI
```

현재까지 **Online Source 데이터를 PostgreSQL Raw Layer로 적재하는 Local Ingestion Pipeline을 구축하고, Schema 관리와 Post-load Validation까지 구현했다.**