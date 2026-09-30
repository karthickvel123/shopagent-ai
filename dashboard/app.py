"""ShopAgent AI — Streamlit Real-Time Monitoring & Telemetry Dashboard."""

import os
import time
import requests
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

API_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="ShopAgent AI — Telemetry Dashboard",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Dark Fintech Styling
st.markdown("""
<style>
    .reportview-container, .main .block-container {
        background-color: #0b0f19;
        color: #f1f5f9;
        font-family: 'Inter', -apple-system, sans-serif;
    }
    .metric-card {
        background: linear-gradient(135deg, #131b2e 0%, #17223b 100%);
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    .metric-val {
        font-size: 28px;
        font-weight: 700;
        color: #38bdf8;
    }
    .metric-lbl {
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94a3b8;
    }
    .badge-paid {
        background-color: #065f46;
        color: #34d399;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 12px;
    }
    .badge-created {
        background-color: #1e3a8a;
        color: #60a5fa;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)


def fetch_stats():
    try:
        r = requests.get(f"{API_URL}/api/stats", timeout=3)
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}


def fetch_products():
    try:
        r = requests.get(f"{API_URL}/api/products", timeout=3)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []


def fetch_orders():
    try:
        r = requests.get(f"{API_URL}/api/orders", timeout=3)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []


def fetch_sessions():
    try:
        r = requests.get(f"{API_URL}/api/sessions", timeout=3)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []


def fetch_optimization():
    try:
        r = requests.get(f"{API_URL}/api/catalog/optimization", timeout=3)
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}


# ── Sidebar ──
with st.sidebar:
    st.image("https://cdn.razorpay.com/static/assets/logo/rzp.svg", width=160)
    st.title("ShopAgent AI")
    st.caption("Track 01: AI Growth & Agentic Commerce")
    st.markdown("---")

    st.subheader("⚡ Gateway Controls")
    auto_refresh = st.checkbox("Auto-refresh (10s)", value=False)
    if st.button("🌱 Seed Demo Catalog", use_container_width=True):
        try:
            res = requests.post(f"{API_URL}/api/seed-catalog", timeout=5)
            if res.status_code == 200:
                st.success("20 Products Seeded!")
                time.sleep(1)
                st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

    if st.button("🔄 Reset Environment", use_container_width=True):
        try:
            res = requests.post(f"{API_URL}/api/reset", timeout=5)
            if res.status_code == 200:
                st.warning("Database reset and seeded!")
                time.sleep(1)
                st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

    st.markdown("---")
    st.caption("Engine: **Google Gemini 3.8 Flash**")
    st.caption("Payments: **Razorpay Test API v1**")
    st.caption("Latency SLA: **<15ms Execution**")


# ── Header & KPI Metrics ──
st.title("🛒 ShopAgent AI — Autonomous Operations Cockpit")
st.markdown("Real-time telemetry monitoring autonomous AI buyers, Razorpay order pipeline, and catalog discoverability.")

stats = fetch_stats()

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-lbl">Total Orders</div>
        <div class="metric-val">{stats.get('total_orders', 0)}</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    rev_inr = stats.get('total_revenue_paise', 0) / 100
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-lbl">Captured Revenue</div>
        <div class="metric-val">₹{rev_inr:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-lbl">Agent Sessions</div>
        <div class="metric-val">{stats.get('total_sessions', 0)}</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-lbl">Autonomous Tool Calls</div>
        <div class="metric-val">{stats.get('total_tool_calls', 0)}</div>
    </div>
    """, unsafe_allow_html=True)

with c5:
    disc_score = stats.get('avg_discoverability_score', 0.0)
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-lbl">Catalog Readiness</div>
        <div class="metric-val">{disc_score}%</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ──
tab_chat, tab_orders, tab_audit, tab_catalog, tab_opt = st.tabs([
    "💬 AI Buyer Copilot",
    "💳 Razorpay Order Stream",
    "🛡️ Immutable Audit Trail",
    "📦 Merchant Catalog",
    "📈 AI-Discoverability Auditor"
])

# ── Tab 1: AI Buyer Copilot ──
with tab_chat:
    st.subheader("Autonomous Shopping Assistant (Gemini 3.8 Flash)")
    st.caption("Interact with the autonomous buyer agent to search, compare, check stock, and place test-mode Razorpay orders.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"sess_{int(time.time())}"

    # Render previous conversation
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "tools" in msg and msg["tools"]:
                st.caption(f"🔧 **Tools Dispatched:** {', '.join(msg['tools'])}")

    # User Input
    user_prompt = st.chat_input("Ask: 'I need wireless earbuds under ₹3500' or 'Buy Sony WF-C500'")
    if user_prompt:
        st.session_state.chat_history.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        with st.chat_message("assistant"):
            with st.spinner("ShopAgent AI planning and dispatching tools..."):
                try:
                    payload = {"message": user_prompt, "session_id": st.session_state.session_id}
                    r = requests.post(f"{API_URL}/api/chat", json=payload, timeout=20)
                    if r.status_code == 200:
                        resp_data = r.json()
                        resp_text = resp_data.get("response", "Done.")
                        tools = resp_data.get("tools_used", [])
                        st.markdown(resp_text)
                        if tools:
                            st.caption(f"🔧 **Tools Dispatched:** {', '.join(tools)}")
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": resp_text,
                            "tools": tools
                        })
                    else:
                        err_msg = f"Backend error: {r.text}"
                        st.error(err_msg)
                        st.session_state.chat_history.append({"role": "assistant", "content": err_msg})
                except Exception as ex:
                    err_msg = f"Failed to reach backend at {API_URL}: {ex}"
                    st.error(err_msg)
                    st.session_state.chat_history.append({"role": "assistant", "content": err_msg})

# ── Tab 2: Razorpay Order Stream ──
with tab_orders:
    st.subheader("Live Razorpay Orders & Verification Pipeline")
    orders = fetch_orders()
    if orders:
        df_orders = pd.DataFrame(orders)
        df_orders["amount_inr"] = df_orders["amount"].apply(lambda a: f"₹{a/100:,.0f}")
        display_cols = ["id", "razorpay_order_id", "product_id", "quantity", "amount_inr", "status", "customer_email", "created_at"]
        st.dataframe(df_orders[display_cols], use_container_width=True)

        col_left, col_right = st.columns(2)
        with col_left:
            status_counts = df_orders["status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            fig_pie = px.pie(status_counts, names="Status", values="Count", title="Orders by Status", color="Status",
                             color_discrete_map={"paid": "#10b981", "created": "#3b82f6", "failed": "#ef4444"})
            fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#cbd5e1")
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_right:
            st.markdown("#### 🔐 Cryptographic Verification Guarantee")
            st.markdown("""
            Every autonomous payment executed by **ShopAgent AI** adheres to Razorpay security protocols:
            - **HMAC-SHA256 Signature Verification** prevents MITM payment tampering.
            - **Atomic Order-to-Payment Mapping** guarantees idempotency and stops double-charges.
            - **Real-time Stock Decrement** ensures instant inventory synchronization.
            """)
    else:
        st.info("No orders placed yet. Interact with the AI Buyer Copilot or VoltStore to trigger an order!")

# ── Tab 3: Immutable Audit Trail ──
with tab_audit:
    st.subheader("Agent Session Audit Trail & Telemetry")
    sessions = fetch_sessions()
    if sessions:
        sess_ids = [s["session_id"] for s in sessions]
        selected_sess = st.selectbox("Select Session to inspect:", sess_ids)

        if selected_sess:
            try:
                audit_res = requests.get(f"{API_URL}/api/sessions/{selected_sess}/audit", timeout=3)
                if audit_res.status_code == 200:
                    logs = audit_res.json()
                    if logs:
                        for l in logs:
                            with st.expander(f"⚙️ [{l['action'].upper()}] {l.get('tool_name', 'N/A')} — {l.get('latency_ms', 0):.1f}ms"):
                                st.write("**Input Parameters:**")
                                st.json(l.get("input_data", {}))
                                st.write("**Tool Output / Result:**")
                                st.json(l.get("output_data", {}))
                    else:
                        st.info("No tool audit logs for this session.")
            except Exception as e:
                st.error(f"Failed to fetch audit logs: {e}")
    else:
        st.info("No sessions recorded yet.")

# ── Tab 4: Merchant Catalog ──
with tab_catalog:
    st.subheader("VoltStore Live Product Catalog")
    products = fetch_products()
    if products:
        p_df = pd.DataFrame(products)
        p_df["price_inr"] = p_df["price"].apply(lambda p: f"₹{p/100:,.0f}")
        st.dataframe(p_df[["id", "name", "category", "brand", "price_inr", "stock", "rating", "review_count"]], use_container_width=True)
    else:
        st.warning("Catalog is empty. Click 'Seed Demo Catalog' in the sidebar.")

# ── Tab 5: AI-Discoverability Auditor ──
with tab_opt:
    st.subheader("AI Buyer Discoverability Readiness Engine")
    st.markdown("Autonomous agents query catalogs using semantic vectors and natural language requirements. This auditor scores catalog readiness.")

    opt_data = fetch_optimization()
    if opt_data:
        o1, o2, o3 = st.columns(3)
        with o1:
            st.metric("Average Discoverability", f"{opt_data.get('average_score', 0)}%")
        with o2:
            st.metric("Total Products Audited", opt_data.get("total_products", 0))
        with o3:
            tiers = opt_data.get("tier_distribution", {})
            st.metric("Agent-Ready (Tier 1)", tiers.get("Tier 1", 0))

        st.markdown("#### 💡 Top Optimization Recommendations for Sellers")
        for rec in opt_data.get("top_recommendations", []):
            st.markdown(f"- 🚀 {rec}")

if auto_refresh:
    time.sleep(10)
    st.rerun()
