# 🍫 Why I Became Interested in Purdys

## 🇨🇦 How I Became Interested in Purdys

One of the things I found interesting after moving to Canada was the culture of **giving chocolate on special occasions** and seeing **stores that specialize in chocolate** in many places.

Chocolate is also popular in Korea, but while living there for many years, I did not often see chocolate brands like Purdys in everyday life.

In Korea, I was more familiar with buying chocolate made by large food companies or international brands from **supermarkets and convenience stores**.

### 🇰🇷 Korea vs. 🇨🇦 Canada

| 🇰🇷 Korea | 🇨🇦 Canada |
|---|---|
| 🏪 Supermarkets & convenience stores | 🍫 Specialty chocolate stores |
| 🍬 Products from large food companies | 🎁 Chocolate collections from specialty brands |
| 💝 Chocolate gifts on some special occasions | 🎄 Chocolate gifts for many seasons & occasions |
| 🌍 Many international brands | 🇨🇦 Well-known local chocolate brands |

When I first came to Canada, I found it interesting that **stores specializing only in chocolate could be found in many shopping malls and neighborhoods**.

There happened to be a **Purdys store near my home**, so I naturally became interested in the brand.

This made me wonder:

> **"Why are specialty chocolate brands like this so familiar in Canada?"**

That question led me to learn more about Purdys and the chocolate retail business in Canada.

---

# 🔎 Researching Purdys' Business Direction

After becoming interested in Purdys, I wanted to learn more than just the brand itself.

I started researching **how the company has been developing its business and technology environment**.

## 🏪 80+ Stores → ▣ Square

In **2025**, Purdys selected Square as a new technology partner and introduced Square's POS and operational systems across more than 80 stores in Canada.

At first, I thought this was simply a change from:

> `Existing POS → ▣ Square POS`

However, after researching it further, I realized that this change could mean much more than simply replacing a payment system.

---

## 🔗 Connecting Retail Data

This is a simplified version of how I understand the idea:

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

If sales data from different stores can be connected in one environment, the data can be used for much more than simply calculating total sales.

### 📊 What Could Be Analyzed?

| Data | Possible Analysis |
|---|---|
| 🏪 **Store Sales** | Sales and product performance by store |
| 🛒 **Online Sales** | Compare online and offline sales |
| 🍫 **Product** | Popular products by channel and region |
| 👤 **Customer** | Customer purchase and repeat-purchase patterns |
| 📦 **Inventory** | Inventory levels and out-of-stock patterns |
| 🎁 **Gift Cards** | Gift card usage across different channels |
| 🏷️ **Promotions** | Promotion performance |
| 📅 **Seasonality** | Changes in demand by season |

---

# 🎄 Chocolate Is a Highly Seasonal Business

One part of the chocolate business that I found especially interesting is **seasonality**.

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

Demand for chocolate can change significantly depending on the season and special occasions.

By analyzing sales patterns by region and season, data could help answer questions such as:

> **Which products should be prepared, for which stores, and in what quantities?**

This kind of analysis could support better demand forecasting and inventory planning.

---

# 🌐 From Retail to Omnichannel

While researching Purdys, one concept that became especially interesting to me was **Omnichannel Retail**.

This is a simplified version of how I understand the business structure:

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

In simple terms:

### 🏪 Offline + 🛒 Online + 📦 Other Channels → ☁️ Connected Data

Instead of looking at the online store and physical stores separately, an omnichannel approach connects data from **physical stores, the online store, and other sales channels** into one retail environment.

Connected data can then support many types of business decisions, including sales analysis, customer behavior analysis, inventory management, promotion analysis, and seasonal demand forecasting.

---

# 💡 This Led to My Project Idea

While researching Purdys' business and technology environment, I started thinking about one question:

> **"How could data from multiple physical stores and an online store be connected into one data platform?"**

Instead of trying to reproduce Purdys' actual systems or use its real data, I decided to create a fictional chocolate company called **Charlie's Chocolate Factory 🍫** and build a simplified retail environment myself.

The architecture I want to build looks like this:

```text
 🏪 Physical Stores                         🛒 Online Store
         │                                         │
         │ Transactions                            │ Orders
         ▼                                         ▼
   ┌─────────────┐                           ┌───────────────┐
   │ ▣ Square API│                           │ E-commerce DB │
   └──────┬──────┘                           └───────┬───────┘
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

---

## 🎯 Project Goal

> **Build a simplified omnichannel commerce data platform that integrates physical store and online transaction data.**

Through this project, I want to focus on more than simply using different technologies.

I want to understand the full data journey:

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

My goal is to understand how each part connects to the next and how Data Engineering can support real business needs.

---

# 🚀 My Learning Journey

This is how the idea for this project developed:

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
 ⚙️ Designed my own commerce data engineering project
                    │
                    ▼
 📊 Learning Data Engineering through
          a real business scenario
```

### 🍫 Curiosity → 🔎 Research → 💡 Idea → ⚙️ Engineering → 📊 Data

This project is not just about practicing technical skills.

It started with my curiosity about a real business and developed into a **learning project where I can study Data Engineering by designing data structures and pipelines around a realistic business scenario.**
