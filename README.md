# ShopAgent AI 🛒🤖

> **Autonomous AI Buyer Agent for Razorpay Merchants**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![Google Gemini](https://img.shields.io/badge/Google%20GenAI-Gemini%203.8%20Flash-orange.svg)](https://ai.google.dev/)
[![Razorpay](https://img.shields.io/badge/Razorpay-Payment%20Gateway-blueviolet.svg)](https://razorpay.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red.svg)](https://streamlit.io/)

**Hackathon Track:** `01 — AI Growth & Agentic Commerce | Razorpay AI Builders`  
**Built by:** Karthickvel C ([GitHub](https://github.com/karthickvel) | [LinkedIn](https://www.linkedin.com/in/karthickvel/))

---

## 📌 Problem Statement

Modern e-commerce shopping is often fragmented, overwhelming, and manual. Buyers spend excessive time browsing hundreds of SKUs, comparing feature matrices, locating valid coupon codes, and navigating multi-step checkout funnels.

Meanwhile, merchants lose high-intent customers at conversion friction points. As the commerce landscape shifts from human-driven browsing to **Agentic Commerce**, merchants need intelligent interfaces that empower autonomous AI agents to discover, negotiate, and seamlessly execute transactions on behalf of users with zero friction and guaranteed security.

---

## 💡 Solution: ShopAgent AI

**ShopAgent AI** is an autonomous AI buyer copilot and merchant agent built on Google's next-generation **Gemini 3.8 Flash** model utilizing the Google GenAI Interactions API and 10 dedicated function-calling tools.

Key capabilities:
- 🔎 **Autonomous Catalog Discovery**: Natural language semantic search across catalog inventory with budget, category, and feature filtering.
- ⚖️ **Objective Product Comparison**: Side-by-side feature, price, review, and specification analysis.
- 🏷️ **Smart Discount Optimization**: Automatic validation and application of merchant coupons to guarantee optimal pricing.
- 💳 **Seamless Razorpay Checkout**: Autonomous creation of Razorpay payment orders and hosted Payment Links via Razorpay Test APIs.
- 🔒 **End-to-End Auditability & Integrity**: Cryptographic HMAC-SHA256 signature verification and complete transactional audit logging.
- 📊 **Merchant Intelligence Dashboard**: Streamlit-based merchant control tower to monitor buyer agent sessions, conversions, and product telemetry.

---

## 🏗️ Architecture

```
+---------------------------------------------------------------------------------+
|                                SHOPAGENT AI                                     |
+---------------------------------------------------------------------------------+

                      +-------------------+
                      |    Shopper / UI   |
                      | (Web / Streamlit) |
                      +---------+---------+
                                |
                                | HTTP / JSON Requests
                                v
                   +---------------------------+
                   |    FastAPI Backend API    |
                   |   (backend.main:app)      |
                   +-------------+-------------+
                                 |
                                 | Prompts & Interaction Session
                                 v
                +---------------------------------+
                |   Google Gemini 3.8 Flash Agent |
                |  (google-genai Interactions API)|
                +----------------+----------------+
                                 |
       +-------------------------+-------------------------+
       | Function Calling Tool Executions                  |
       v                                                   v
+---------------+                                   +--------------+
| 10 AI Tools   |                                   |  Order & DB  |
| - Search      |                                   |  Management  |
| - Compare     |                                   +-------+------+
| - Coupon      |                                           |
| - Payment     |                                           v
+-------+-------+                              +-----------------------+
        |                                      | SQLite / SQLAlchemy   |
        | API Calls                            | - Products, Orders    |
        v                                      | - Payments, AuditLogs |
+-------------------------------+              +-----------------------+
|    Razorpay Test API SDK      |
| - Create Orders               |
| - Create Payment Links        |
| - Signature Verification      |
+-------------------------------+
```

---

## 🛠️ Tech Stack

- **AI Model & SDK**: Google Gemini 3.8 Flash (`google-genai` >= 2.3.0 Interactions API)
- **Backend**: FastAPI, Uvicorn, Pydantic v2
- **Database & ORM**: SQLite, SQLAlchemy
- **Payments Engine**: Razorpay Python SDK (Test Mode)
- **Frontend / Merchant Ops**: Streamlit Dashboard
- **DevOps & CI/CD**: Docker, Docker Compose, GitHub Actions

---

## 🧰 10 Function-Calling Tools

ShopAgent AI equips the Gemini 3.8 Flash agent with 10 tools:

| # | Tool Name | Description | Key Parameters |
|---|-----------|-------------|----------------|
| 1 | `search_products` | Searches catalog by query keyword, category, price bounds, and stock status. | `query`, `category`, `min_price`, `max_price`, `in_stock` |
| 2 | `get_product_details` | Retrieves full specs, inventory count, pricing, and ratings for a product. | `product_id` |
| 3 | `compare_products` | Compares features, pricing, ratings, and specifications of multiple products side-by-side. | `product_ids` |
| 4 | `apply_coupon` | Validates promotional coupons and calculates discounts on an order. | `order_id`, `coupon_code` |
| 5 | `create_order` | Creates an order in the database with customer details and line items. | `items`, `customer_name`, `customer_email`, `customer_phone` |
| 6 | `create_razorpay_payment` | Creates a standard Razorpay payment order for in-app checkout. | `order_id`, `amount`, `customer_email`, `customer_phone` |
| 7 | `create_razorpay_payment_link`| Generates a hosted Razorpay payment link with SMS/email notification support. | `order_id`, `amount`, `customer_name`, `customer_email`, `description` |
| 8 | `verify_razorpay_payment` | Validates HMAC signature (`razorpay_signature`) to verify payment authenticity. | `razorpay_order_id`, `razorpay_payment_id`, `razorpay_signature` |
| 9 | `track_order_status` | Retrieves real-time fulfillment, shipping status, and payment state for an order. | `order_id` |
| 10| `get_store_recommendations` | Generates intelligent product recommendations based on preferences and budget. | `user_preferences`, `budget`, `category` |

> *Note: All monetary amounts are handled in paise (INR × 100) to adhere to standard financial precision.*

---

## ⚡ Quick Start

### 1. Clone & Set Up Environment

```bash
git clone https://github.com/karthickvel/shopagent-ai.git
cd shopagent-ai

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your_gemini_api_key_here
RAZORPAY_KEY_ID=rzp_test_your_key_id
RAZORPAY_KEY_SECRET=your_razorpay_secret
DATABASE_URL=sqlite:///./data/shopagent.db
ENVIRONMENT=development
```

### 3. Run Application

Start the FastAPI backend:
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

In a separate terminal, launch the Streamlit Merchant Dashboard:
```bash
streamlit run dashboard/app.py --server.port 8501
```

Access:
- **API Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Merchant Dashboard**: [http://localhost:8501](http://localhost:8501)

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat` | Send natural language shopping goal to Gemini autonomous buyer agent |
| `GET` | `/api/products` | Browse and filter merchant product catalog |
| `GET` | `/api/products/{id}` | Retrieve individual product specifications |
| `POST` | `/api/orders` | Create a new purchase order |
| `GET` | `/api/orders/{id}` | Get status and line items for an order |
| `POST` | `/api/payments/create-order` | Generate a Razorpay order ID |
| `POST` | `/api/payments/payment-link` | Generate an instant Razorpay payment link |
| `POST` | `/api/payments/verify` | Verify payment signature and complete transaction |
| `GET` | `/api/analytics/insights` | Aggregate merchant store analytics and audit telemetry |
| `GET` | `/api/health` | Service health status check |

---

## 🔄 Demo Flow Walkthrough

```
1. User Request:
   "Find me the best wireless noise-cancelling headphones under ₹5,000 and buy them."
       │
       ▼
2. Catalog Search:
   Agent invokes `search_products(query="wireless noise cancelling", max_price=500000)`
       │
       ▼
3. Comparison & Decision:
   Agent invokes `compare_products(product_ids=[101, 104])` to evaluate sound profile & battery
       │
       ▼
4. Order Preparation:
   Agent invokes `create_order(items=[{"product_id": 101, "quantity": 1}], ...)`
       │
       ▼
5. Discount Application:
   Agent invokes `apply_coupon(order_id=42, coupon_code="WELCOME10")` -> saves 10%
       │
       ▼
6. Razorpay Payment Link Generation:
   Agent invokes `create_razorpay_payment_link(order_id=42, amount=405000, ...)`
   -> Returns active Razorpay checkout URL: `https://rzp.io/i/xxxxxx`
       │
       ▼
7. Verification & Confirmation:
   Webhook or user completes checkout -> Agent invokes `verify_razorpay_payment`
   -> Order marked PAID, inventory updated, audit log persisted.
```

---

## 🧪 Testing

Run test suite using `pytest`:

```bash
# Run all tests with short traceback
pytest tests/ -v --tb=short

# Run specific agent interaction tests
pytest tests/test_agent.py -v
```

---

## 🐳 Docker Deployment

Run the complete stack (FastAPI backend + Streamlit dashboard) with Docker Compose:

```bash
# Build and run containers
docker-compose up --build

# Run in background
docker-compose up -d

# Stop containers
docker-compose down
```

---

## 📂 Project Structure

```
shopagent-ai/
├── backend/
│   ├── __init__.py               # Package initializer
│   ├── config.py                 # Pydantic environment configurations
│   ├── database.py               # SQLAlchemy SQLite engine & session management
│   ├── models.py                 # Database models (Product, Order, Payment, AuditLog)
│   ├── schemas.py                # Pydantic request and response schemas
│   ├── agent.py                  # Gemini 3.8 Flash agent loop & Interactions API
│   ├── tools.py                  # 10 function-calling tools implementations
│   ├── razorpay_client.py        # Razorpay Test SDK integration
│   └── main.py                   # FastAPI REST API endpoints & route handlers
├── dashboard/
│   └── app.py                    # Streamlit merchant analytics & buyer interface
├── tests/
│   ├── __init__.py
│   ├── test_agent.py             # Agent reasoning & function calling tests
│   ├── test_api.py               # FastAPI endpoints test suite
│   └── test_tools.py             # Tools logic & signature verification tests
├── .github/
│   └── workflows/
│       └── ci.yml                # GitHub Actions automated CI workflow
├── .gitignore                    # Git ignore file
├── docker-compose.yml            # Multi-container orchestration
├── Dockerfile                    # Container build configuration
├── LICENSE                       # MIT License
├── README.md                     # Project documentation
└── requirements.txt              # Python project dependencies
```

---

## 👥 Authors & Acknowledgments

- **Built by:** Karthickvel C
- **GitHub:** [@karthickvel](https://github.com/karthickvel)
- **LinkedIn:** [linkedin.com/in/karthickvel](https://www.linkedin.com/in/karthickvel/)
- **Hackathon:** [Razorpay AI Builders Hackathon 2026](https://razorpay.com)
- **Track:** `01 — AI Growth & Agentic Commerce`
- **License:** [MIT License](LICENSE)
