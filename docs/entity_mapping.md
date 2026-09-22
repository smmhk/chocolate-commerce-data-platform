# 🧩 Entity Mapping

> 업데이트: 2026-09-22 · Lovable → Square Sandbox 연동 학습 기록

Lovable 원본 데이터와 Square 데이터를 어떻게 연결하는지 기록한다.

필요한 데이터를 선택하고 Square의 구조로 변환하는 과정과, 구현하면서 배운 점을 함께 정리한다.

---

## 📋 1. 엔티티별 진행 상태

| Lovable Entity | Square Resource | 현재 상태 | 연동 범위 |
|---|---|---|---|
| `products` | Catalog | ✅ 1차 완료 | 상품명·설명·SKU·가격 |
| `customers` | Customers | ✅ 1차 완료 | POS에서 가입한 고객 |
| `customer_addresses` | Customer의 `address` | 🟡 고객 ID 연결 처리 통합 | 주소 CSV에 Square 고객 ID 기록, 실제 주소 전송은 별도 |
| `stores` | Locations | ✅ 생성 테스트 완료 | 매장 요청 변환·생성, 원본 DB·CSV 우편번호 반영 완료 |
| `orders` | Orders | ⚪ 예정 | RETAIL 주문만 전송 |
| `order_items` | Order line items | ⚪ 예정 | 선택한 RETAIL 주문의 항목 |
| `payments` | Payments | ⚪ 예정 | 매장 주문의 Sandbox 결제 처리 |
| `loyalty_settings` | 미정 | ⚪ 범위 검토 | Square 연동 필요성 검토 |
| `loyalty_transactions` | 미정 | ⚪ 범위 검토 | 원본 리워드와 Square 연동 범위 결정 |
| `tax_settings` | 직접 연동 제외 | — | 주문에 필요한 세금 처리는 별도 검토 |

상품과 고객의 1차 완료는 기본 생성과 성공 결과 저장을 의미한다.
상품 전체 생성은 앞선 테스트에서 완료했다. 기존 정보 수정과 재실행 안정화는 별도로 확인한다.
매장은 생성 테스트까지 완료했으며, 전체 매장의 ID 저장 결과와 일괄 처리 여부는 별도로 확인한다.

> Lovable의 리워드 기능과 Square Loyalty 연동은 별개의 작업이다.

---

## 🌐 2. 테스트 데이터 준비와 분석용 수집

### Square에 데이터를 보내는 이유

현재 Lovable 애플리케이션은 온라인몰과 가상 POS 역할을 동시에 한다.

실제 Square POS에서 등록했다면 이미 Square에 존재했을 상품·고객·거래 데이터를, 이번 프로젝트에서는 Lovable에서 만든 뒤 Square Sandbox로 전송한다.

따라서 Lovable → Square는 가상의 매장 데이터 소스를 준비하는 과정이다.

| 데이터 | Square 전송 기준 |
|---|---|
| 상품 | 온라인·매장 공통 상품 |
| 고객 | `signup_channel = 'POS'` |
| 주문 | `channel = 'RETAIL'` |
| 주문 항목·결제 | 선택한 RETAIL 주문에 연결된 기록 |

### 향후 분석용 수집

| 데이터 | 수집 경로 |
|---|---|
| 매장 고객·주문 | Square API → GCP의 저장소·BigQuery |
| 온라인 고객·주문 | Lovable DB → GCP의 저장소·BigQuery |
| Square에 없는 원본 주소·보조 정보 | 필요에 따라 Lovable DB에서 직접 수집 |

분석을 위해 Square 데이터를 Lovable DB에 다시 복사할 필요는 없다.
각 소스에서 필요한 데이터를 수집하고 분석 플랫폼에서 연결한다.

Lovable에 남은 RETAIL 주문과 Square에 복사한 주문은 같은 거래이므로 중복 집계하지 않는다.

### 운영 시스템의 복제 범위와 분석 범위는 다르다

모든 고객과 주소를 Square에 넣어야 통합 분석이 가능한 것은 아니다.

- 온라인 전용 고객은 Lovable에서 수집할 수 있다.
- Square에 주소가 없어도 Lovable의 주소를 고객 ID로 연결할 수 있다.
- Square에는 매장 시뮬레이션에 필요한 데이터를 준비한다.
- 분석 플랫폼에서는 여러 소스의 데이터를 더 넓은 범위로 통합한다.

단, GCP가 동일 고객을 자동으로 식별하는 것은 아니다.
원본 ID와 Square ID의 매핑 및 고객 연결 규칙을 유지해야 한다.

---

## 🍫 3. Product Mapping — 1차 완료

### 구현한 흐름

1. 상품 CSV를 Pandas로 읽는다.
2. 컬럼과 값을 확인한다.
3. SKU로 Square의 기존 상품을 검색한다.
4. 신규 상품을 요청 구조로 변환한다.
5. Square Catalog API로 전송한다.
6. 성공한 ID와 sync 정보를 원본 CSV에 저장한다.

### 원본 → Square 매핑

Square 경로는 요청의 `object` 내부를 기준으로 한다.

| Lovable 필드 | Square 필드 | 처리 |
|---|---|---|
| `product_name` | `item_data.name` | 상품명 |
| `description` | `item_data.description` 또는 `description_html` | 실제 변환 코드의 필드 사용 |
| `sku` | `item_data.variations[].item_variation_data.sku` | 판매 단위 식별 |
| `price` | `item_data.variations[].item_variation_data.price_money.amount` | CAD 달러 → 센트 정수 |
| 원본 값 없음 | `item_data.variations[].item_variation_data.price_money.currency` | `CAD` |
| `product_id` | 임시 Item / Variation ID | 요청 객체 식별에 사용 |

예를 들어 `7.25 CAD`는 다음과 같이 변환한다.

```json
{
  "amount": 725,
  "currency": "CAD"
}
```

### 변환 과정에서 생성하는 값

| 필드 | 값 |
|---|---|
| Item `type` | `ITEM` |
| Item 임시 `id` | `#<product_id>-item` |
| Variation `type` | `ITEM_VARIATION` |
| Variation 임시 `id` | `#<product_id>-variation` |
| Variation `name` | `Regular` |
| `pricing_type` | `FIXED_PRICING` |
| `currency` | `CAD` |

### 원본에서 유지하는 값

- `id`
- `is_best_seller`
- `active_status`
- `created_at`
- `updated_at`

`category`와 `image_key`의 Square 객체 연결은 후속 작업이다.

**`active_status`와 `present_at_all_locations`는 직접 매핑하지 않는다.**

상품의 활성 상태와 Square의 매장별 존재 여부는 서로 다른 의미이기 때문이다.

### Item ID와 Variation ID

| ID | 역할 |
|---|---|
| Item ID | 상품 객체 조회·삭제 등에 사용 |
| Item Variation ID | SKU·가격이 연결된 판매 단위, 주문 항목 연결에 사용 |

현재 코드:

```python
square_catalog_object_id = square_variation["id"]
```

현재 `square_catalog_object_id`에는 Variation ID가 저장된다.
이 값을 Item ID로 착각해서 사용하지 않아야 한다.

향후 두 ID를 별도 컬럼으로 관리한다면 기존 저장 데이터와 참조 코드도 함께 수정한다.

---

## 💾 4. 상품 연동 결과 저장

별도 매핑 CSV 대신 `products_export.csv`의 해당 행을 업데이트한다.

| 컬럼 | 저장 값 |
|---|---|
| `square_catalog_object_id` | 현재 코드 기준 Variation ID |
| `square_sync_status` | `SUCCESS` |
| `square_synced_at` | 성공 시각, UTC |
| `square_sync_error` | 실패 정보 저장은 현재 미구현 |

### 처리 기준

- SKU가 정확히 한 행에 해당하는지 확인한다.
- 기존 상품 값을 유지하면서 sync 컬럼만 수정한다.
- API 실패는 콘솔에서 확인한다.
- 생성 후 CSV 저장이 실패하면 방금 생성한 상품 삭제를 시도한다.

### 남은 작업

- 기존 SKU 검색 결과에서 ID를 가져와 CSV 매핑 복구
- 기존 상품의 가격·설명 업데이트
- 중복 검색 시 SKU의 정확한 일치 여부 확인

이미 있는 상품을 건너뛰는 것만으로는 새 CSV의 ID 매핑이 채워지지 않는다.

---

## 👤 5. Customer Mapping — 1차 완료

### 확인한 원본 구조

처음 확인한 고객 export는 22행, 15개 컬럼이며 구분자는 `;`였다.
행 수는 테스트 데이터를 추가하면서 달라질 수 있다.

```text
id
customer_number
user_id
email
first_name
last_name
phone
customer_type
square_customer_id
created_at
updated_at
signup_channel
square_sync_status
square_synced_at
square_sync_error
```

### 고객 ID의 역할

| 컬럼 | 의미 |
|---|---|
| `id` | 원본 고객 PK |
| `customer_number` | 사람이 확인하기 위한 회원 번호 |
| `user_id` | 로그인 계정 연결 ID |
| `square_customer_id` | Square 고객 ID |

주문과 원본 고객은 다음 관계로 연결된다.

```text
orders.customer_id = customers.id
```

### 고객 선택 기준을 변경한 이유

처음에는 RETAIL 주문에 연결된 고객을 선택했다.

하지만 이번 단계의 목적은 가상 POS에서 가입한 고객을 Square에 준비하는 것이므로, 현재는 고객의 가입 경로를 사용한다.

```python
target_customers_df = customers_df.loc[
    customers_df["signup_channel"].eq("POS")
].copy()
```

| 조건 | 의미 |
|---|---|
| `customers.signup_channel = 'POS'` | POS에서 가입한 고객 |
| `orders.channel = 'RETAIL'` | 매장에서 발생한 주문 |

가입 경로와 구매 경로는 다르다.

온라인 가입 회원이 매장에서 구매한 경우의 고객 연결은 주문 연동 단계에서 별도로 처리한다.

### 구현한 고객 필드 매핑

| 원본 필드 | Square 요청 필드 | 처리 |
|---|---|---|
| `id` | `reference_id` | 원본 고객 식별값 |
| `first_name` | `given_name` | 이름 |
| `last_name` | `family_name` | 성 |
| `email` | `email_address` | 이메일 |
| `phone` | `phone_number` | 문자열로 전달 |
| `customer_number` | 전송하지 않음 | 원본에 유지 |
| `user_id` | 전송하지 않음 | 원본 로그인 정보 |
| `customer_type` | 전송하지 않음 | 원본에 유지 |
| `signup_channel` | 전송하지 않음 | 연동 대상 선택에 사용 |
| `created_at`, `updated_at` | 전송하지 않음 | 원본 시각 유지 |

`transform_customer()`는 빈 값을 정리하고, 값이 있는 필드만 요청에 포함한다.
전화번호는 문자열로 읽으며, 국가번호 등 형식 정규화는 별도 검증할 부분이다.

### 요청 예시

```json
{
  "reference_id": "<lovable-customer-id>",
  "given_name": "Mandy",
  "family_name": "Shin",
  "email_address": "mandy@example.com",
  "phone_number": "+16045550123",
  "idempotency_key": "<request-key>"
}
```

### 고객 연동 흐름

1. POS 가입 고객을 선택한다.
2. 원본 `id`로 Square의 `reference_id`를 검색한다.
3. 기존 고객이면 신규 생성을 건너뛴다.
4. 신규 고객이면 요청용 딕셔너리로 변환한다.
5. 고객 생성 API를 호출한다.
6. 고객 CSV에 생성 결과를 저장한다.
7. 해당 고객의 주소 행에도 Square 고객 ID를 기록한다.

기존 고객을 건너뛰었는데 로컬 ID가 비어 있다면,
기존 Square ID를 조회해서 CSV에 복구하는 처리가 필요하다.

---

## 🏠 6. 고객과 주소 처리를 함께 관리한 이유

### 고객과 주소는 같은 고객 ID를 기준으로 연결된다

```text
customer_addresses.customer_id = customers.id
```

주소를 Square 고객에 연결하려면 해당 고객의 `square_customer_id`가 필요하다.

따라서 고객 생성 후 얻은 ID를 고객 CSV와 주소 CSV에 함께 기록하도록 처리 흐름을 묶었다.

이것은 두 원본 테이블을 하나의 테이블로 합쳤다는 의미는 아니다.

### 모든 주소를 Square에 복제할 필요는 없다

이번 결정에 중요한 영향을 준 점은,
Square에 고객이나 주소가 없어도 나중에 GCP에서 필요한 데이터를 통합할 수 있다는 것이었다.

온라인 전용 고객은 Lovable에서 수집하고,
Square에 없는 주소도 원본 고객 ID를 기준으로 연결할 수 있다.

따라서 고객·주소의 연결 정보를 함께 관리하되,
Square로 실제 전송할 범위와 분석에 사용할 범위는 구분하기로 했다.

### 원본 주소 구조

처음 확인한 주소 CSV는 20건이며 고객마다 주소가 한 개씩 있었다.

```text
id
customer_id
label
address_line1
address_line2
city
province
postal_code
country
is_default
created_at
```

고객 연동 결과를 함께 저장하면서 `square_customer_id` 컬럼을 추가한다.

### 주소 전송이 필요할 때 사용할 매핑

Square에서는 기존 고객의 `address`를 업데이트하는 방식으로 처리한다.

| 원본 필드 | Square `address` 내부 필드 |
|---|---|
| `address_line1` | `address_line_1` |
| `address_line2` | `address_line_2` |
| `city` | `locality` |
| `province` | `administrative_district_level_1` |
| `postal_code` | `postal_code` |
| `country` | `country` — `Canada` → `CA` |

`label`, `is_default`, 원본 주소 ID는 원본 관리와 주소 선택에 사용한다.

주소가 여러 개라면 어떤 주소를 Square에 사용할지 정해야 한다.
현재 테스트에서는 기본 주소를 선택하는 기준을 사용했다.

### 고객 ID 기록과 주소 전송 성공은 다르다

| 작업 | 의미 |
|---|---|
| 주소 CSV에 `square_customer_id` 저장 | 어느 Square 고객과 연결되는지 기록 |
| Square 고객의 `address` 업데이트 | 실제 주소 내용을 Square에 반영 |

고객 생성이 성공했다고 주소의 sync 상태까지 `SUCCESS`로 기록하지 않는다.

실제 주소 전송 완료 여부는 별도로 확인한다.

---

## 🔑 7. 고객 중복 검색과 멱등성

### 기존 고객 검색

`search_customer_by_reference_id()`는 다음 값을 비교한다.

```text
Lovable customers.id = Square customer.reference_id
```

| 결과 | 처리 |
|---|---|
| 기존 고객 발견 | 신규 생성하지 않음 |
| 검색 결과 없음 | 신규 생성 단계로 진행 |
| API 검색 실패 | 예외로 중단 |

검색 실패를 고객이 없는 것으로 처리하면 잘못된 신규 생성으로 이어질 수 있다.

생성 직후에는 검색 반영이 늦을 수 있으므로,
검색 결과만으로 중복 방지를 완전히 보장하지는 않는다.

### 직접 경험한 오류

```text
IDEMPOTENCY_KEY_REUSED
The idempotency key can only be retried with the same request data.
```

고객 ID로 고정한 키를 사용하면서 요청 내용이 달라져 오류가 발생했다.

### 키 사용 기준

| 상황 | 처리 |
|---|---|
| 동일한 생성 요청 재시도 | 같은 키와 같은 요청 내용 사용 |
| 요청 내용을 변경한 새 요청 | 새 키 사용 |
| 삭제 완료 후 새로 생성 | 새 키 사용 |
| 타임아웃으로 성공 여부 불명확 | 새 키로 즉시 생성하지 않고 기존 요청 확인 |

현재 테스트에서는 새 생성 요청의 키를 `uuid4()`로 만든다.

스크립트를 다시 실행할 때마다 새 키가 생기므로,
자동 재시도를 구현할 때는 요청 키와 내용을 유지하는 처리가 필요하다.

> 중복 검색은 기존 고객을 찾는 기능이고,
> 멱등성 키는 같은 요청의 재처리를 관리하는 기능이다.

---

## 💾 8. 고객·주소 CSV 저장과 실패 처리

### 고객 CSV 업데이트

`customers_export.csv` 전체를 읽고 원본 `id`가 일치하는 행을 수정한다.

| 컬럼 | 저장 값 |
|---|---|
| `square_customer_id` | 생성된 Square 고객 ID |
| `square_sync_status` | `SUCCESS` |
| `square_synced_at` | 성공 시각, UTC |
| `square_sync_error` | 성공 시 비움 |

### 주소 CSV 업데이트

`customer_addresses_export.csv`에서 `customer_id`가 일치하는 행들을 수정한다.

| 컬럼 | 저장 값 |
|---|---|
| `square_customer_id` | 해당 고객의 Square 고객 ID |

주소가 없는 고객은 주소 행을 새로 만들지 않는다.

두 파일 모두 전체 데이터를 유지하면서 대상 행만 수정한다.
로컬 CSV 수정은 Lovable DB에 자동 반영되지 않는다.

### 고객 CSV를 연결 기준으로 사용한다

같은 Square 고객 ID를 두 파일에 저장하므로 값이 달라지지 않도록 관리해야 한다.

현재 주소 테스트에서는 고객 CSV의 ID를 기준으로 연결한다.
주소 CSV의 같은 컬럼은 merge 전에 제외해 `_x`, `_y` 컬럼이 생기지 않도록 한다.

### 실패 처리 방식을 변경한 이유

처음에는 CSV 저장 실패 시 방금 생성한 Square 고객을 삭제하도록 했다.

하지만 두 CSV를 업데이트하면 다음과 같은 부분 성공이 발생할 수 있다.

1. Square 고객 생성 성공
2. 고객 CSV 저장 성공
3. 주소 CSV 저장 실패

이때 Square 고객을 삭제하면 고객 CSV에 삭제된 ID가 남게 된다.

따라서 현재 두 파일 저장 흐름에서는:

- Square 고객을 유지한다.
- 저장 오류와 Square 고객 ID를 남기고 중단한다.
- 파일 상태를 확인한 뒤 같은 ID로 저장만 재시도한다.
- 고객을 다시 생성하지 않는다.

두 CSV 저장은 하나의 트랜잭션이 아니다.
직접 덮어쓰다가 파일이 손상된 경우에는 먼저 파일 복구가 필요하다.

### 테스트 중 확인한 문제

| 출력 결과 | 먼저 확인할 내용 |
|---|---|
| Square ID가 있는 고객 수가 0 | 읽은 고객 CSV 경로와 sync 저장 결과 |
| Square 고객은 있지만 주소 대상이 0 | 해당 고객의 주소 존재 여부와 기본 주소 조건 |

Square에 고객이 존재하는 것과,
현재 읽은 로컬 CSV에 고객 ID가 기록된 것은 별개다.

---

## 🏪 9. Store Mapping — 생성 테스트 완료

### 이번에 진행한 작업

상품과 고객 다음으로 Lovable의 매장 데이터를 Square Location 생성 요청으로 변환했다.
`tests/test_locations.py`에서 payload를 확인하고, `src/square/location.py`의 `create_location()`을 호출하는 흐름으로 테스트했다.

매장 생성 중 HTTP 400 `BAD_REQUEST`를 확인했고, 필수 주소 값과 우편번호를 점검했다.

이후 Lovable의 기존 매장 DB를 수정해 `postal_code`를 추가하고 값을 저장했다.
CSV에도 우편번호가 포함되도록 반영했으며, 매장 생성 작업을 완료했다.

우편번호는 원본 DB와 CSV에 반영된 값을 사용한다.

### 테스트 요청에서 사용한 매핑

아래 표는 테스트 payload에서 확인한 구조다.
왼쪽은 원본 값의 의미이며, 실제 CSV 컬럼명은 변환 코드와 맞춰 사용한다.

| 원본 값 또는 설정 | Square 요청 필드 | 처리 |
|---|---|---|
| 매장명 | `location.name` | 매장 이름 전달 |
| 매장 유형 설정 | `location.type` | `PHYSICAL` |
| 시간대 설정 | `location.timezone` | `America/Vancouver` |
| 도로명 주소 | `location.address.address_line_1` | 주소 전달 |
| 도시 | `location.address.locality` | 예: `Vancouver` |
| 주 | `location.address.administrative_district_level_1` | 예: `BC` |
| 국가 코드 | `location.address.country` | `CA` |
| `postal_code` | `location.address.postal_code` | 원본 DB·CSV에 반영한 우편번호 전달 |

이 표는 프로젝트에서 사용하는 필드 정리이며,
Square API의 전체 필수 항목 목록을 의미하지 않는다.

### 우편번호를 원본 DB와 CSV에 반영한 이유

기존에 확인한 요청에는 매장명·유형·시간대·주소·도시·주·국가가 있었지만 우편번호가 없었다.

기존 DB에 우편번호를 저장하고 CSV에도 포함시켰다.
이렇게 하면 다음 CSV 추출과 재실행에서도 원본에 저장한 같은 값을 사용할 수 있다.

- 이번 매장과 주소는 개인 프로젝트용 가상 데이터다.
- 테스트 우편번호를 원본 매장 DB에 저장했다.
- 형식에 맞는 임의 값이 실제 존재하는 우편번호나 주소 일치를 보장하는 것은 아니다.
- CSV의 `postal_code` 반영도 완료했다.

### 주문 연동에 필요한 매장 ID 연결

매장 생성 다음에는 원본 매장 ID와 생성된 Square Location ID를 연결해야 한다.
매장 이름은 표시용으로 두고, 주문 처리에는 ID 매핑을 사용한다.

| 확인할 항목 | 목적 |
|---|---|
| 원본 매장 ID ↔ Square Location ID | 주문이 발생한 지점을 연결 |
| 로컬 CSV의 매핑 저장 여부 | 다음 실행에서도 같은 Location 사용 |
| 각 테스트 매장의 연결 상태 | 주문을 잘못된 매장으로 전송하지 않도록 확인 |
| 이미 생성한 매장 처리 | 재실행 시 불필요한 추가 생성 방지 |

매장 생성 성공과 로컬 매핑 저장 완료는 구분해서 확인한다.
매장 ID 저장 컬럼명과 저장 실패 복구 방식은 별도 확인 항목으로 남긴다.

### 다음 단계: Order / Order Item Mapping

| 원본 값 | 연결 대상 |
|---|---|
| 주문의 매장 참조 | 해당 매장의 Square Location ID |
| 주문의 `customer_id` | 해당 고객의 Square Customer ID |
| 주문 항목의 상품 참조 | Square Item Variation ID |
| 원본 주문 ID | 생성된 Square Order ID |

주문 전송 전에 상품·매장·필요한 고객의 ID 연결을 준비한다.

- `channel = 'RETAIL'`인 주문만 선택한다.
- 선택한 주문에 속한 `order_items`를 함께 가져온다.
- 비회원 주문은 고객 연결 없이 유지한다.
- 온라인 가입 회원의 RETAIL 주문은 고객 연결 방식을 확인한다.
- 주문 항목의 원본 상품 참조 키와 매장 참조 키는 실제 CSV를 확인한 후 확정한다.
- 수량·단가·할인·세금·리워드 사용액을 확인하고 원본 주문 합계와 비교한다.
- 주문 생성과 결제 처리는 별개로 테스트한다.

---

## 📁 10. 코드 역할

| 경로 | 역할 |
|---|---|
| `src/extract/load_csv.py` | CSV 읽기 |
| `src/transform/products.py` | 상품 요청 데이터 변환 |
| `src/square/catalog.py` | 상품 검색·생성·삭제 및 결과 저장 |
| `src/transform/customers.py` | 고객 요청 데이터 변환 |
| `src/square/customers.py` | 고객 API 함수와 고객·주소 CSV 연결 정보 저장 |
| `tests/test_customers.py` | 고객 한 명의 생성·결과 저장 확인 |
| `tests/test_customer_address.py` | 고객과 기본 주소 연결 확인 |
| `src/square/location.py` | 매장 생성 API 함수 |
| `tests/test_locations.py` | 매장 payload 확인과 생성 테스트 |
| `src/pipelines/customers_pipeline.py` | 전체 POS 고객 처리 흐름으로 확장할 위치 |

고객 삭제 함수가 존재하더라도,
두 CSV 저장 실패 시 자동 삭제하는 흐름에서는 사용하지 않는다.

현재는 이해하고 관리하기 쉽게 관련 함수를 함께 두고,
반복되는 저장 로직은 이후 공통화 여부를 검토한다.

---

## 🧠 11. 작업하면서 배운 점

### 가입 경로와 구매 경로를 구분해야 한다

POS 가입 고객과 매장 구매 고객은 서로 다른 대상이다.
이번 단계의 목적에 맞춰 가입 경로를 연동 기준으로 선택했다.

### 원본과 대상 구조는 1:1일 필요가 없다

상품 한 행은 Item과 Variation으로 변환되고,
별도 주소 테이블의 값은 Square 고객의 `address`로 연결될 수 있다.

### 운영 시스템에 모든 데이터를 복제할 필요는 없다

온라인 전용 고객과 Square에 없는 주소도 Lovable에서 수집해 GCP에서 연결할 수 있다.

운영 시스템 간 복제 범위와 분석 플랫폼의 통합 범위는 다르게 설계할 수 있다.

### ID 연결이 통합의 기반이다

원본 고객 ID, 로그인 ID, Square 고객 ID는 역할이 다르다.
각 소스의 데이터를 연결하려면 대응 관계를 유지해야 한다.

### 연결 준비와 실제 연동 성공은 다르다

주소 CSV에 Square 고객 ID가 있어도 주소 내용이 전송된 것은 아니다.
각 작업의 성공 상태를 구분해서 기록해야 한다.

### 변환과 전송은 별개의 작업이다

요청용 딕셔너리를 먼저 확인하고 API를 호출하면,
데이터 구조 문제와 통신 문제를 나누어 확인할 수 있다.

### 검색 실패를 신규 데이터로 판단하면 안 된다

검색 결과 없음과 API 오류를 구분해야 불필요한 생성을 막을 수 있다.

### 중복 검색과 멱등성은 다르다

기존 고객 확인과 동일 요청 재시도는 서로 다른 문제다.
같은 요청을 재시도할 때는 같은 키와 내용을 유지해야 한다.

### 여러 저장 작업은 일부만 성공할 수 있다

외부 API와 두 CSV는 함께 성공하는 하나의 작업이 아니다.
실패 시 무조건 삭제하기보다 어디까지 저장됐는지 확인하고 복구해야 한다.

### 중복 저장은 관리 책임도 늘린다

같은 ID를 두 파일에 저장하면 편리하지만 값이 어긋날 수 있다.
어느 파일을 기준으로 연결할지 정해야 한다.

### 원본 필드가 빠졌다면 원본 구조도 보완한다

매장 생성에서 우편번호를 확인하면서,
변환 로직뿐 아니라 원본 테이블과 export 파일에도 필요한 값이 있는지 점검해야 한다는 것을 배웠다.

이번에는 기존 DB에 `postal_code`를 추가하고 CSV에도 반영했다.
DB를 수정해도 기존 로컬 CSV는 자동으로 바뀌지 않으므로 다시 추출한 파일을 확인해야 한다.

### 현재 규모에 맞게 구현한다

현재 흐름을 이해할 수 있는 구조로 구현하고,
반복과 복잡성이 실제로 생겼을 때 공통화하거나 분리한다.

> 필요한 데이터를 선택하고 연결 정보를 유지해,
> 이후 통합 분석에 사용할 수 있도록 만드는 것이 중요하다.

---

## ▶️ 12. 다음 작업 순서

1. **매장 연결 마무리** — 우편번호의 DB·CSV 반영은 완료했으므로, 원본 매장 ID ↔ Square Location ID 매핑을 확인한다.
2. **RETAIL 주문 한 건 선택** — 주문, 주문 항목, 매장, 고객, 상품 데이터를 연결한다.
3. **주문 payload 변환** — 상품 Variation ID와 수량·금액을 연결하고 원본 합계와 비교한다.
4. **Square 주문 생성 테스트** — 응답을 확인하고 원본 주문 ID와 Square Order ID를 저장한다.
5. **Sandbox 결제 테스트** — 생성한 주문과 결제를 연결하는 흐름을 구현한다.
6. **일괄 처리와 재실행 확인** — 한 건의 흐름이 확인되면 여러 매장의 주문으로 확장한다.
7. **분석용 수집으로 이동** — Square 매장 데이터와 Lovable 온라인 데이터를 GCP·BigQuery로 수집한다.

현재까지는 **분석에 사용할 가상의 매장 데이터 소스를 준비하는 단계**다.
주문·결제 연동과 GCP 적재는 아직 완료 항목에 포함하지 않는다.