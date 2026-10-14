# 📌 프로젝트 진행 로그

이 문서는 **Charlie’s Chocolate Factory — Omnichannel Retail Data Platform Project**의 주요 작업 진행 상황을 기록합니다.

---

## 현재 진행 상태

```text
Phase 1 — Source System Simulation
✅ 완료

Phase 2 — Data Ingestion & Storage
🟡 진행 중

Phase 3 — Data Transformation & Modeling
⬜ 예정

Phase 4 — Analytics & BI
⬜ 예정
```

---

# 2026-10-14

## ✅ 완료한 작업

### Phase 1 — Source System Simulation

- Lovable을 이용해 온라인 스토어 구축
- Lovable을 이용해 POS Simulator 구축
- 테스트용 커머스 데이터 생성
- Square Developer Sandbox 환경 구성
- Square API 연동
  - Products → Square Catalog API
  - Customers → Square Customers API
  - Stores → Square Locations API
  - Retail Orders → Square Orders API
- 내부 ID ↔ Square ID Mapping 구현

---

### Phase 2 — Local Data Environment

- Docker Desktop 설치
- Docker Compose를 이용해 PostgreSQL 환경 구성
- 로컬 데이터베이스 생성

```text
chocolate_db
```

- PostgreSQL과 DBeaver 연결
- PostgreSQL Container가 아래 포트에서 정상 실행되는 것 확인

```text
localhost:5432
```

현재 로컬 구조:

```text
Chocolate Source Data
        ↓
Python / Pandas
        ↓
PostgreSQL
        ↓
DBeaver
```

---

## 🧠 이번 작업에서 이해한 내용

- Docker는 PostgreSQL을 독립된 환경에서 실행하기 위해 사용한다.
- PostgreSQL은 실제 데이터를 저장하는 데이터베이스이다.
- DBeaver는 PostgreSQL에 연결해서 데이터를 조회하고 SQL을 실행하는 도구이다.
- Online 데이터와 Square POS 데이터는 각각 따로 수집한 뒤, 나중에 BigQuery에서 통합한다.

---

## ▶️ 다음 작업

- [ ] `products.csv`를 PostgreSQL에 적재
- [ ] customers 데이터 적재
- [ ] stores 데이터 적재
- [ ] orders 데이터 적재
- [ ] order_items 데이터 적재
- [ ] payments 데이터 적재
- [ ] Python ingestion pipeline 구현
- [ ] Python pipeline Dockerize
- [ ] Square API Extraction Pipeline 구현
- [ ] GCP / BigQuery 환경 구성 시작

---

## 🎯 현재 가장 가까운 목표

```text
products.csv
     ↓
Python / Pandas
     ↓
PostgreSQL
     ↓
DBeaver
```

우선 첫 번째 로컬 데이터 적재 흐름을 완성한 뒤, 다른 데이터셋과 클라우드 환경으로 확장합니다.
