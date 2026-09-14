# 🧩 Entity Mapping

Lovable 원본 데이터와 Square 데이터를 어떻게 연결하는지 기록한다.

필요한 데이터를 선택하고 Square의 구조로 변환하는 과정과, 구현하면서 배운 점을 함께 정리한다.

---

## 📋 1. 엔티티별 진행 상태

| Lovable Entity | Square Resource | 현재 상태 | 연동 범위 |
|---|---|---|---|
| `products` | Catalog | ✅ 1차 완료 | 상품명·설명·SKU·가격 |
| `customers` | Customers | ✅ 1차 완료 | POS에서 가입한 고객 |
| `customer_addresses` | Customer address | ⚪ 보류 | 주소 연동 필요 시 검토 |
| `stores` | Locations | ⚪ 예정 | 내부 매장 ID와 Square Location ID 연결 |
| `orders` | Orders | ⚪ 예정 | RETAIL 주문만 전송 |
| `order_items` | Order line items | ⚪ 예정 | 선택한 RETAIL 주문의 항목 |
| `payments` | Payments | ⚪ 예정 | 매장 주문의 Sandbox 결제 처리 |
| `loyalty_settings` | 미정 | ⚪ 범위 검토 | Square 연동 필요성 별도 검토 |
| `loyalty_transactions` | 미정 | ⚪ 범위 검토 | 원본 리워드와 Square 연동 범위 결정 |
| `tax_settings` | 직접 연동 제외 | — | 주문에 필요한 세금 처리는 별도 검토 |

상품과 고객의 1차 완료는 기본 생성과 성공 결과 저장을 의미한다.
기존 정보 수정, 전체 대상의 일괄 처리 및 재실행 안정화는 별도로 확인한다.

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
| 매장 데이터 | Square API → GCP → BigQuery |
| 온라인 데이터 | Lovable DB → GCP → BigQuery |

분석을 위해 Square 데이터를 Lovable DB에 다시 복사할 필요는 없다.
각 소스에서 수집한 데이터를 분석 플랫폼에서 연결한다.

Lovable에 남은 RETAIL 주문과 Square에 복사한 주문은 같은 거래이므로 중복 집계하지 않는다.

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
3. 기존 고객이면 생성을 건너뛴다.
4. 신규 고객이면 요청용 딕셔너리로 변환한다.
5. 고객 생성 API를 호출한다.
6. 응답의 고객 ID를 원본 CSV에 저장한다.

---

## 🔑 6. 고객 중복 검색과 멱등성

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

또한 생성 직후에는 검색 반영이 늦을 수 있으므로, 검색 결과만으로 중복 방지를 완전히 보장하지는 않는다.

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

다만 스크립트를 다시 실행할 때마다 새 키가 생기므로, 이후 자동 재시도까지 구현하려면 요청 키와 내용을 유지하는 처리가 필요하다.

**중복 검색은 기존 고객을 찾는 기능이고, 멱등성 키는 같은 요청의 재처리를 관리하는 기능이다.**

---

## 💾 7. 고객 성공 결과 저장과 실패 처리

### 원본 CSV 업데이트

`customers_export.csv` 전체를 읽고 원본 `id`가 일치하는 행만 수정한다.

| 컬럼 | 저장 값 |
|---|---|
| `square_customer_id` | 생성된 Square 고객 ID |
| `square_sync_status` | `SUCCESS` |
| `square_synced_at` | 성공 시각, UTC |
| `square_sync_error` | 성공 시 비움 |

전송 대상만 저장하지 않고 전체 고객 데이터를 유지한다.
그렇지 않으면 온라인 가입 고객이 CSV에서 사라질 수 있다.

로컬 CSV 수정은 Lovable DB에 자동 반영되지 않는다.

### CSV 저장 실패 시 처리

고객 생성 성공 후 CSV 업데이트를 시도한다.

- 저장 성공: 작업 완료
- 저장 실패: 방금 생성한 Square 고객 삭제 시도
- 삭제까지 실패하거나 결과가 불명확함: 고객 ID와 오류를 남기고 중단

기존 고객 검색으로 찾은 고객에는 이 삭제 처리를 적용하지 않는다.

### 이 처리의 한계

Square 생성과 CSV 저장은 하나의 트랜잭션이 아니다.

삭제는 이미 수행한 작업을 되돌리기 위한 별도 API 요청이며, 이 요청도 실패할 수 있다.

또한 원본 CSV에 직접 덮어쓰는 도중 파일이 손상되면, Square 고객을 삭제해도 CSV가 복구되지는 않는다.

---

## 🏪 8. Store / Order Mapping — 예정

| 원본 값 | 연결 대상 |
|---|---|
| 내부 매장 ID | Square Location ID |
| 주문의 `customer_id` | 해당 고객의 Square Customer ID |
| 주문 항목의 상품 참조 | Square Item Variation ID |
| 원본 주문 ID | 생성된 Square Order ID |

주문 전송 전에 상품·매장·필요한 고객의 ID 연결을 준비한다.

- 비회원 주문은 고객 연결 없이 유지한다.
- 온라인 가입 회원의 RETAIL 주문은 해당 고객의 Square 연결 여부를 확인한다.
- 주문 항목의 원본 상품 참조 키는 실제 CSV를 확인한 후 확정한다.

---

## 📁 9. 코드 역할

| 경로 | 역할 |
|---|---|
| `src/extract/load_csv.py` | CSV 읽기 |
| `src/transform/products.py` | 상품 요청 데이터 변환 |
| `src/square/catalog.py` | 상품 검색·생성·삭제 및 결과 저장 |
| `src/transform/customers.py` | 고객 요청 데이터 변환 |
| `src/square/customers.py` | 고객 검색·생성·삭제 및 결과 저장 |
| `tests/test_customers.py` | 고객 한 명 선택부터 생성·저장까지 수동 확인 |
| `src/pipelines/customers_pipeline.py` | 전체 POS 고객 처리 흐름으로 확장할 위치 |

현재는 이해하고 관리하기 쉽게 고객 관련 함수를 함께 둔다.

여러 엔티티에서 같은 CSV 저장 로직이 반복되면 공통 함수로 분리하는 것을 검토한다.

---

## 🧠 10. 작업하면서 배운 점

### 데이터의 의미를 먼저 정해야 한다

가입 경로와 구매 경로는 다르다.
어떤 데이터를 전송할지는 컬럼의 존재보다 작업 목적을 기준으로 결정해야 한다.

### 원본과 대상 구조는 1:1일 필요가 없다

상품 한 행이 Item과 Variation을 포함한 중첩 구조로 바뀔 수 있다.
내부 관리용 컬럼은 원본에 유지하고, 대상에 필요한 값은 변환 과정에서 생성한다.

### ID마다 역할이 다르다

원본 고객 ID, 로그인 계정 ID, Square 고객 ID를 구분해야 한다.
고객 생성 후 ID를 저장해야 이후 주문과 연결할 수 있다.

### 변환과 전송은 별개의 작업이다

`transform_customer()`는 딕셔너리를 만들고,
`create_customer()`는 HTTP 요청과 응답 확인을 담당한다.

변환 결과를 먼저 출력해보면 API 호출 전에 데이터 구조를 확인할 수 있다.

### 검색 결과 없음과 검색 실패를 구분해야 한다

API 호출 실패를 신규 데이터로 판단하지 않도록 예외 처리해야 한다.

### 중복 검색과 멱등성은 다르다

기존 고객 검색만으로 재시도 문제를 해결할 수는 없다.
같은 요청을 재시도할 때는 같은 멱등성 키와 요청 내용을 유지해야 한다.

### API 성공 이후에도 실패할 수 있다

외부 시스템 생성과 로컬 저장은 따로 수행된다.
일부만 성공했을 때의 처리와 복구 한계를 고려해야 한다.

### 현재 규모에 맞게 구현한다

처음부터 파일과 기능을 지나치게 나누기보다,
현재 흐름을 이해할 수 있는 구조로 구현하고 반복되는 부분을 나중에 정리한다.

> 데이터를 전송하는 것뿐 아니라,
> 두 시스템의 관계를 유지하고 다음 작업에서 사용할 수 있는 상태로 남기는 것이 중요하다.