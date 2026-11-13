# 초콜릿 프로젝트 dbt 실습 노트

## 1. 이번 실습에서 확인한 것

- Windows의 PyCharm 가상환경에 dbt와 BigQuery 어댑터를 설치했다.
- 기존 저장소 바로 아래에 `chocolate_dbt/` 프로젝트를 만들었다.
- Google 계정으로 로컬 인증을 설정하고 `dbt debug`에서 연결 성공을 확인했다.
- BigQuery에서 첫 Staging 뷰 `chocolate-data-platform.dbt_dev.stg_online_orders`가 생성된 것을 확인했다.
- 데이터 클리닝 규칙은 dbt Staging SQL에 작성하기로 했다. 상태값 점검과 클리닝 적용, 데이터 테스트는 다음 실습이다.

## 2. 각 도구가 하는 일

| 도구 | 역할 |
|---|---|
| Kestra | 데이터를 BigQuery의 raw 데이터셋까지 적재한다. |
| PyCharm과 Git | 모델 SQL과 설정을 작성하고 변경 이력을 관리한다. |
| dbt | 모델의 SQL을 준비하고 실행 순서를 관리하며 BigQuery에 실행을 요청한다. |
| BigQuery | SQL을 실행하고 뷰나 테이블을 만든다. 콘솔에서 결과를 확인한다. |

이번 모델은 `raw_online.orders`를 읽어 개발용 데이터셋 `dbt_dev`에 뷰를 만들었다. **Staging**은 원본을 정리하는 모델 계층이고, **`dbt_dev`**는 모델 결과를 저장하는 개발용 데이터셋이다.

## 3. 설치와 프로젝트 설정

PyCharm에서 가상환경을 활성화한 상태로 실행한다.

```powershell
python -m pip install dbt-bigquery
dbt --version
```

프로젝트를 처음 만들 때만 저장소 루트에서 실행한다.

```powershell
dbt init chocolate_dbt
```

| 항목 | 실습 값 |
|---|---|
| 인증 방식 | `oauth` |
| BigQuery 프로젝트 | `chocolate-data-platform` |
| 결과 데이터셋 | `dbt_dev` |
| 위치 | `us-east1` |
| 개별 BigQuery 작업 대기 시간 | `job_execution_timeout_seconds: 300` |

`chocolate_dbt/dbt_project.yml`은 Git으로 관리하는 프로젝트 설정이다. Windows의 `$HOME\.dbt\profiles.yml`은 사용자 폴더에 두는 로컬 연결 설정이다. `dbt debug` 로그에서 실제로 읽은 두 파일의 경로를 확인할 수 있다.

저장소 루트의 `chocolate_dbt/`를 실습에 사용한다. `src/chocolate_dbt/`에 필요한 SQL이나 설정이 있다면 옮긴 뒤 중복 폴더를 정리할 수 있다. 초기 샘플인 `models/example/`을 제거할 경우 `dbt_project.yml`에 있는 `example:` 설정 블록도 함께 정리한다. 생성된 `logs/dbt.log`는 커밋에서 제외한다.

## 4. 로컬 인증과 연결 확인

Google Cloud CLI를 설치한 뒤 새 PowerShell이나 Cloud SDK 창에서 실행한다. 아래 두 명령은 어느 폴더에서든 실행할 수 있다.

```powershell
gcloud --version
gcloud auth application-default login
```

브라우저에서 BigQuery 프로젝트에 접근할 수 있는 Google 계정을 선택하고 Google Cloud 권한에 동의한다. 그다음 PyCharm의 `chocolate_dbt/` 터미널에서 실행한다.

```powershell
dbt debug
```

| 만난 상황 | 확인하거나 해결한 내용 |
|---|---|
| PowerShell이 `gcloud`를 찾지 못함 | Windows에 Google Cloud CLI를 설치하고 새 터미널에서 명령을 확인했다. |
| `gcloud init` 중 Compute Engine API 오류 | CLI 기본 프로젝트 설정은 완료됐다. dbt의 BigQuery 연결에는 Compute Engine API를 켤 필요가 없었다. |
| 연결 설정에 `location: US`가 표시됨 | `profiles.yml`의 위치를 원본 데이터셋과 같은 `us-east1`로 맞췄다. |
| `cloud-platform scope is required but not consented` | ADC 로그인을 다시 실행하고 브라우저의 Google Cloud 권한 동의를 완료했다. |
| 인증 후 기본 프로젝트 감지 경고 | 프로필에 명시한 프로젝트로 연결됐다. `Connection test: [OK connection ok]`와 `All checks passed!`를 확인했다. |

## 5. 첫 Staging 모델 다시 만들어 보기

`chocolate_dbt/models/staging/_online__sources.yml`에 원본 테이블을 등록한다.

```yaml
version: 2

sources:
  - name: online
    database: chocolate-data-platform
    schema: raw_online
    tables:
      - name: orders
```

`chocolate_dbt/models/staging/stg_online_orders.sql`에 모델을 작성한다.

```sql
{{ config(materialized='view') }}

select
    order_id,
    channel,
    order_status,
    total_amount,
    created_at as order_created_at
from {{ source('online', 'orders') }}
```

`source('online', 'orders')`는 YAML에 등록한 BigQuery 원본을 가리킨다. 이 모델은 주문 행을 유지하면서 필요한 컬럼을 고르고, `created_at`에 `order_created_at`이라는 이름을 붙인다.

`chocolate_dbt/` 터미널에서 실행한다.

```powershell
dbt run --select stg_online_orders
```

BigQuery 탐색기에서 `chocolate-data-platform → dbt_dev → stg_online_orders`를 찾거나, 아래 SQL로 결과를 확인한다.

```sql
SELECT *
FROM `chocolate-data-platform.dbt_dev.stg_online_orders`
LIMIT 10;
```

## 6. 다음 실습에서 할 일

1. BigQuery 콘솔에서 `raw_online.orders`의 상태값과 건수를 확인한다.

   ```sql
   SELECT
     COALESCE(CONCAT('[', order_status, ']'), '<NULL>') AS raw_status,
     COUNT(*) AS order_count
   FROM `chocolate-data-platform.raw_online.orders`
   GROUP BY 1
   ORDER BY order_count DESC;
   ```

2. 앞뒤 공백이나 빈 문자열이 확인되면 Staging 모델의 `order_status` 표현을 아래처럼 바꾼다.

   ```sql
   nullif(trim(order_status), '') as order_status
   ```

3. 모델을 다시 실행하고 `dbt_dev`의 뷰에서 변환 결과를 확인한다. 원본과 뷰의 행 수를 비교해 이번 컬럼 변환으로 행이 달라지지 않았는지도 확인한다.
4. 주문 한 건당 한 행이라는 기준을 확인한 뒤 `order_id`에 `not_null`과 `unique` 테스트를 추가하고 `dbt test --select stg_online_orders`로 실행한다.

> 복습할 때는 `dbt debug`로 연결을, `dbt run`으로 모델 생성을, `dbt test`로 작성해 둔 데이터 규칙을 확인한다는 차이를 떠올리면 된다.
