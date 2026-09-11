# Learning Notes

This file documents what I learned while building the project
이 프로젝트를 진행하며 내가 직접 이해한 내용을 내언어로 정리합니다.

# 🍫 Why I Became Interested in Purdys

## 🇨🇦 How I Became Interested in Purdys

캐나다에 와서 흥미롭게 느낀 것 중 하나는 **특별한 날에 초콜릿을 주고받는 문화**와 **초콜릿을 전문적으로 판매하는 브랜드 매장**을 일상에서 쉽게 볼 수 있다는 점이었습니다.

한국에서도 많은 사람들이 초콜릿을 좋아하지만, 제가 한국에서 오랫동안 생활하면서 **Purdys와 같은 초콜릿 전문 브랜드를 일상에서 자주 접하지는 못했습니다.**

한국에서는 보통 여러 제과회사에서 만든 초콜릿이나 해외 브랜드 제품을 **대형마트와 편의점에서 구매하는 방식**이 더 익숙했습니다.

### 🇰🇷 Korea vs. 🇨🇦 Canada

| 🇰🇷 Korea | 🇨🇦 Canada |
|---|---|
| 🏪 편의점·마트 중심 | 🍫 초콜릿 전문 브랜드 매장 |
| 🍬 대형 제과회사 제품 | 🎁 브랜드별 초콜릿 컬렉션 |
| 💝 일부 특별한 날 선물 | 🎄 다양한 시즌·기념일 선물 |
| 🌍 해외 브랜드 비중이 높음 | 🇨🇦 로컬 초콜릿 브랜드 존재 |

캐나다에 처음 왔을 때는 이렇게 **초콜릿만 전문적으로 판매하는 브랜드 매장이 여러 지역과 쇼핑몰에 있다는 사실**이 꽤 신기했습니다.

마침 집 근처에 **Purdys 매장**이 있었기 때문에 자연스럽게 브랜드에 관심을 가지게 되었고,

> **"왜 캐나다에서는 이런 초콜릿 전문 브랜드가 이렇게 익숙할까?"**

라는 궁금증에서 Purdys와 캐나다의 초콜릿 시장을 조금씩 찾아보기 시작했습니다.

---

# 🔎 Researching Purdys' Business Direction

Purdys에 관심을 가지게 된 후에는 단순히 초콜릿 브랜드 자체보다 **회사가 최근 어떤 방향으로 비즈니스와 기술 환경을 발전시키고 있는지**가 궁금해졌습니다.

## 🏪 80+ Stores → ▣ Square

Purdys는 **2025년 Square를 새로운 기술 파트너로 선정**하고, 캐나다 전역의 80개 이상의 매장에 Square의 POS 및 운영 시스템을 도입했습니다.

처음에는 단순히

> `기존 POS → ▣ Square POS`

로 변경하는 프로젝트라고 생각했습니다.

하지만 조금 더 조사하면서 이 변화가 단순한 결제 시스템 교체 이상의 의미를 가질 수 있다고 생각했습니다.

---

## 🔗 Connecting Retail Data

제가 이해한 구조를 간단하게 표현하면 다음과 같습니다.

```text
                🍫 Purdys Retail Ecosystem

                   🏪 Physical Stores
                           │
                           ▼
                    ┌─────────────┐
                    │  ▣ Square   │
                    │ POS / Data  │
                    └──────┬──────┘
                           │
                           ▼
                  ☁️ Unified Data Platform
                           │
                  ┌────────┼────────┐
                  ▼        ▼        ▼
                 📦       👤       📊
             Inventory  Customer  Analytics
```

각 매장에서 발생하는 데이터를 하나의 환경에서 연결할 수 있다면 단순한 매출 집계를 넘어 훨씬 다양한 분석이 가능해집니다.

### 📊 What Could Be Analyzed?

| Data | Possible Analysis |
|---|---|
| 🏪 **Store Sales** | 매장별 매출 및 상품 판매량 |
| 🛒 **Online Sales** | 온라인과 오프라인 판매 비교 |
| 🍫 **Product** | 채널·지역별 인기 상품 |
| 👤 **Customer** | 고객 구매 패턴 및 재구매 행동 |
| 📦 **Inventory** | 매장별 재고 및 품절 패턴 |
| 🎁 **Gift Cards** | 채널 간 기프트카드 사용 |
| 🏷️ **Promotions** | 프로모션 성과 |
| 📅 **Seasonality** | 시즌별 수요 변화 |

---

# 🎄 Chocolate Is a Highly Seasonal Business

초콜릿 비즈니스에서 특히 흥미로운 부분은 **Seasonality**라고 생각했습니다.

```text
💕 Valentine's Day
        │
        ▼
🐰 Easter
        │
        ▼
💐 Mother's Day
        │
        ▼
🎃 Halloween
        │
        ▼
🎄 Christmas
        │
        ▼
   🍫 Demand Changes
        │
        ▼
 📊 Sales Forecasting
        │
        ▼
 📦 Inventory Planning
```

초콜릿은 특정 기념일과 시즌에 따라 수요가 크게 달라질 수 있습니다.

따라서 지역과 시즌에 따른 판매 패턴을 분석한다면,

> **어떤 매장에 → 어떤 상품을 → 얼마나 준비해야 하는지**

예측하고 재고를 계획하는 데에도 데이터를 활용할 수 있다고 생각했습니다.

---

# 🌐 From Retail to Omnichannel

이러한 내용을 조사하면서 제가 가장 흥미롭게 느낀 부분은 **Omnichannel Retail**이었습니다.

제가 이해한 Purdys의 비즈니스 구조를 단순화하면 다음과 같습니다.

```text
                       👤 Customer
                            │
               ┌────────────┼────────────┐
               ▼            ▼            ▼
            🏪 Store     🛒 Online     📦 Other
              POS           Store       Channels
               │            │            │
               └────────────┼────────────┘
                            ▼
                    ☁️ Data Platform
                            │
                ┌───────────┼───────────┐
                ▼           ▼           ▼
             📊 Sales    📦 Inventory  👤 Customer
             Analysis      Planning      Insights
                └───────────┼───────────┘
                            ▼
                    💡 Better Decisions
```

즉,

### 🏪 Offline + 🛒 Online + 📦 Other Channels → ☁️ Connected Data

온라인몰을 별도로 운영하는 것이 아니라 **오프라인 매장, 온라인몰, 그리고 다양한 판매 채널에서 발생하는 데이터를 연결하여 하나의 리테일 환경으로 바라보는 것**입니다.

이렇게 연결된 데이터는 매출 분석뿐만 아니라 고객 행동 분석, 재고 관리, 프로모션 분석, 시즌별 수요 예측 등 다양한 비즈니스 의사결정에 활용될 수 있습니다.

---

# 💡 This Led to My Project Idea

Purdys의 비즈니스와 기술 환경을 조사하면서 한 가지 질문이 생겼습니다.

> **"여러 매장과 온라인몰에서 발생하는 데이터를 실제로 하나의 데이터 플랫폼으로 연결한다면 어떻게 설계할 수 있을까?"**

그래서 실제 Purdys의 시스템이나 데이터를 사용하는 대신, 가상의 초콜릿 브랜드인 **Charlie's Chocolate Factory 🍫**를 만들어 비슷한 비즈니스 환경을 직접 구성해보기로 했습니다.

---

## 🍫 Charlie's Chocolate Factory

Purdys를 조사하면서 이해한 리테일 비즈니스 구조를 직접 실험해보기 위해 만든 **가상의 초콜릿 판매 플랫폼**입니다.

Lovable을 활용하여 온라인 쇼핑몰과 오프라인 매장을 가진 가상의 초콜릿 브랜드 환경을 만들었습니다.

### 🌐 Live Demo

> ### 🍫 [Charlie's Chocolate Factory 방문하기 →](https://choco-magic-shop.lovable.app/)
>
> **온라인스토어/POS 를 직접 둘러보고 가상의 초콜릿 리테일 환경을 확인할 수 있습니다.**

현재 프로젝트에서는 다음과 같은 비즈니스 환경을 가정하고 있습니다.

| Channel | 역할 |
|---|---|
| 🏪 **Physical Stores** | Vancouver, Burnaby, Richmond 매장 |
| ▣ **Square POS** | 오프라인 매장의 상품 및 거래 데이터 |
| 🛒 **Online Store** | 고객 온라인 주문 |
| 👤 **Customer** | 회원 및 구매 데이터 |
| 🎁 **Rewards** | 구매 금액 기반 리워드 |
| 📦 **Products** | 온라인·오프라인에서 판매되는 상품 |

이 웹사이트 자체를 만드는 것이 프로젝트의 최종 목적은 아닙니다.

**실제 리테일 비즈니스와 비슷한 데이터가 발생하는 환경을 만들고, 그 데이터를 Data Engineering 관점에서 수집하고 연결하는 것**이 이 프로젝트의 핵심 목표입니다.

---

# 🏗️ From Chocolate Store to Data Platform

제가 만들고 싶은 전체 구조는 다음과 같습니다. (Online store/ POS 두가지버전 구현)

```text
 🏪 Physical Stores                         🛒 Online Store
         │                                         │
         │ Transactions                            │ Orders
         ▼                                         ▼
   ┌───────────────┐                           ┌───────────────┐
   │ ▣ Square API │                           │ E-commerce DB │
   └──────┬────────┘                           └─────┬─────────┘
          │                                          │
          └────────────────────┬─────────────────────┘
                               ▼
                        ⚙️ Data Pipeline
                               │
                               ▼
                        ☁️ Data Platform
                               │
                    ┌──────────┼──────────┐
                    ▼          ▼          ▼
                   📊         📦         👤
                 Sales     Inventory   Customer
                Analysis    Analysis   Analysis
```

### 🔗 Business Flow

```text
🍫 Charlie's Chocolate Factory
             │
      ┌──────┴──────┐
      ▼             ▼
 🏪 Offline       🛒 Online
    Stores           Store
      │               │
      ▼               ▼
 ▣ Square API    E-commerce DB
      │               │
      └───────┬───────┘
              ▼
        ⚙️ Data Engineering
              ▼
        ☁️ Data Platform
              ▼
        📊 Business Insights
```
# ⚙️ From Lovable DB to Square

가상의 초콜릿 판매 환경을 만든 후, 다음 단계로 **Lovable DB에 저장된 상품 데이터를 Square로 가져오는 작업**을 진행했습니다.

처음부터 Square에 상품을 직접 입력하는 대신, 기존 Lovable DB의 데이터를 활용하여 **데이터를 추출하고, 변환하고, Square API를 통해 전송하는 과정**을 직접 구현해보기로 했습니다.

## 1️⃣ Export Data from Lovable DB

먼저 Lovable DB에 저장되어 있던 상품 데이터를 `.csv` 파일로 Export했습니다.

```text
🍫 Lovable DB
      │
      ▼
📄 CSV Export
(; delimiter)
```



---

## 2️⃣ Read & Inspect Data with Pandas

다음으로 Python의 **Pandas**를 사용하여 CSV 파일을 읽었습니다.

이 단계에서는 단순히 데이터를 불러오는 것뿐만 아니라,

- 어떤 column들이 존재하는지
- 데이터 타입은 무엇인지
- 값이 정상적으로 들어왔는지
- Square에서 사용할 수 있도록 어떤 데이터를 변환해야 하는지

확인했습니다.

```text
📄 CSV
   │
   ▼
🐼 Pandas
   │
   ▼
🔍 Inspect Data
   │
   ├── Columns
   ├── Data Types
   └── Values
```

---

## 3️⃣ Transform Data for Square API

Lovable DB의 데이터 구조와 Square API가 요구하는 데이터 구조는 서로 다르기 때문에, 데이터를 그대로 전송할 수는 없었습니다.

따라서 Python/Pandas를 사용하여 **Lovable의 데이터 구조를 Square API가 이해할 수 있는 형태로 변환하고 mapping하는 과정**을 진행했습니다.

```text
🍫 Lovable Data
       │
       ▼
   🐼 Pandas
       │
       ▼
⚙️ Clean / Transform / Map
       │
       ▼
   📦 Square API Format
       │
       ▼
    ▣ Square
```

개념적으로는 다음과 같은 **Source → Target Mapping** 과정입니다.

| Source: Lovable | Target: Square |
|---|---|
| Product Name | Item Name |
| Description | Description |
| Price | Money / Amount |
| Category | Category Mapping |

이 과정을 통해 기존 시스템의 데이터를 새로운 시스템에서 사용할 수 있도록 변환하는 **Data Transformation과 Schema Mapping**의 기본 개념을 직접 경험할 수 있었습니다.

---

## 4️⃣ Send Data through Square API

변환된 데이터는 Square API가 받을 수 있는 request 형태로 구성한 후 API를 통해 Square로 전송했습니다.

전체 흐름을 정리하면 다음과 같습니다.

```text
🍫 Lovable DB
      │
      ▼
📄 CSV Export
      │
      ▼
🐼 Pandas
      │
      ▼
🔍 Data Inspection
      │
      ▼
⚙️ Transformation & Mapping
      │
      ▼
📦 API Request
      │
      ▼
▣ Square API
      │
      ▼
✅ Square Catalog
```

---

## 💻 Implementation

Learning Notes에는 전체 코드 대신 **무엇을 했고 왜 그렇게 했는지**를 중심으로 기록했습니다.

실제 Python 구현은 아래 소스 코드에서 확인할 수 있습니다.

👉 **[View Python implementation →](./src/square/load_products.py)**

> 💡 As I continue developing the project, I plan to separate data extraction, transformation, and Square API integration into smaller modules.

---

## 🧠 What I Learned

이번 작업을 통해 단순히 API를 호출하는 것뿐만 아니라,

**Source Data → Inspection → Transformation → Schema Mapping → API → Target System**

으로 데이터가 이동하는 전체 과정을 이해할 수 있었습니다.

```text
Raw Data
   ↓
Understand the Data
   ↓
Transform the Data
   ↓
Match the Target Schema
   ↓
Send through API
   ↓
Validate the Result
```

이 과정은 앞으로 더 큰 Data Pipeline을 설계하기 위한 기초 단계라고 생각합니다.
---

## 🎯 Project Goal

> **Build a simplified omnichannel commerce data platform that integrates physical store and online transaction data.**

이 프로젝트를 통해 단순히 여러 기술을 사용하는 것보다,

### Why → How → Business Value

```text
❓ Why collect the data?
          ↓
🔗 How can different data sources be connected?
          ↓
⚙️ How should the data pipeline be designed?
          ↓
☁️ How should the data be stored and transformed?
          ↓
📊 How can the data support business decisions?
```

이 전체 흐름을 직접 이해하는 것을 목표로 하고 있습니다.

---

# 🚀 My Learning Journey

이 프로젝트가 시작된 과정을 정리하면 다음과 같습니다.

```text
🍫 Curiosity about Canadian chocolate culture
                    │
                    ▼
           🏪 Discovered Purdys
                    │
                    ▼
     🔎 Researched its business direction
                    │
                    ▼
       ▣ Learned about Square integration
                    │
                    ▼
 🌐 Became interested in omnichannel retail data
                    │
                    ▼
 🍫 Built Charlie's Chocolate Factory
                    │
                    ▼
 ⚙️ Building an omnichannel data platform
                    │
                    ▼
 📊 Learning Data Engineering through
          a real business scenario
```

### 🍫 Curiosity → 🔎 Research → 💡 Idea → 🛒 Business Simulation → ⚙️ Engineering → 📊 Data

이 프로젝트는 단순히 기술을 연습하기 위한 프로젝트라기보다, **실제 비즈니스에 대한 궁금증에서 시작하여 가상의 리테일 환경을 만들고, 그 환경에서 발생하는 데이터를 활용해 Data Engineering을 공부하는 Learning Project**입니다.

---

## 🔗 Project Links

🍫 **Live E-commerce Demo**  
[Charlie's Chocolate Factory →](https://choco-magic-shop.lovable.app/)

💻 **Data Engineering Repository**  
현재 보고 있는 GitHub Repository

📝 **Learning Notes**  
이 프로젝트를 진행하면서 이해한 내용과 기술적인 의사결정을 지속적으로 기록합니다.



