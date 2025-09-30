import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from PIL import Image
import io
import time

# Configuration
API_URL = "http://127.0.0.1:8000"

# Page configuration
st.set_page_config(
    page_title="Test Tube - Campus Payments",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .success-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 10px 0;
    }
    .insight-box {
        padding: 20px;
        border-radius: 10px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin: 20px 0;
    }
    .merchant-card {
        padding: 15px;
        border-radius: 8px;
        background-color: #ffffff;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    .warning-box {
        padding: 15px;
        border-radius: 10px;
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        margin: 10px 0;
    }
    .info-card {
        padding: 20px;
        border-radius: 10px;
        background: white;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'user_wallet' not in st.session_state:
    st.session_state.user_wallet = None
if 'transaction_history' not in st.session_state:
    st.session_state.transaction_history = []
if 'refresh_counter' not in st.session_state:
    st.session_state.refresh_counter = 0


# Helper functions
def fetch_transactions():
    """Fetch transactions from API"""
    try:
        resp = requests.get(f"{API_URL}/transactions")
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception as e:
        st.error(f"Failed to fetch transactions: {e}")
        return None


def fetch_analytics():
    """Fetch analytics summary"""
    try:
        resp = requests.get(f"{API_URL}/analytics/summary")
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception as e:
        return None


def fetch_ai_insights(period="today"):
    """Fetch AI insights"""
    try:
        resp = requests.post(
            f"{API_URL}/ai/insights",
            json={"period": period}
        )
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception as e:
        return None


def fetch_merchants():
    """Fetch merchant list"""
    try:
        resp = requests.get(f"{API_URL}/merchants")
        if resp.status_code == 200:
            return resp.json()["merchants"]
        return []
    except:
        return []


def format_naira(amount):
    """Format amount as Naira"""
    return f"₦{amount:,.2f}"


def get_category_emoji(category):
    """Get emoji for category"""
    emojis = {
        "food": "🍔",
        "transport": "🚌",
        "data": "📱",
        "books": "📚",
        "entertainment": "🎮",
        "utilities": "💡",
        "supplies": "✏️",
        "other": "📦"
    }
    return emojis.get(category, "📦")


# Sidebar navigation
st.sidebar.title("🧪 Test Tube")
st.sidebar.markdown("**Campus Payments + AI Insights**")

# User info (mock)
st.sidebar.markdown("---")
st.sidebar.markdown("👤 **Student Profile**")
st.sidebar.text("Name: Samuel Achilike")
st.sidebar.text("Matric: EEG/2021/053")
st.sidebar.text("Campus: UNILAG")
st.sidebar.text("Wallet: Dev...XYZ")

# Navigation menu
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigation",
    ["📊 Dashboard", "💳 Make Payment", "🤖 AI Insights", "📜 Transactions", "🏪 Merchants", "📈 Analytics"]
)

# Quick actions in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("**Quick Actions**")
if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
    st.session_state.refresh_counter += 1
    st.rerun()

# Main content based on selected page
if page == "📊 Dashboard":
    st.title("📊 Dashboard")
    st.markdown("Your campus payment overview at a glance")

    # Fetch analytics
    analytics = fetch_analytics()

    if analytics and analytics.get("stats"):
        # Top metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            daily_ngn = analytics["daily"]["total_ngn"] if "daily" in analytics else 0
            st.metric(
                "Today's Spending",
                format_naira(daily_ngn),
                delta=f"{analytics['daily']['transactions']} transactions" if "daily" in analytics else "0"
            )

        with col2:
            weekly_ngn = analytics["weekly"]["total_ngn"] if "weekly" in analytics else 0
            st.metric(
                "This Week",
                format_naira(weekly_ngn),
                delta=f"{analytics['weekly']['transactions']} transactions" if "weekly" in analytics else "0"
            )

        with col3:
            monthly_ngn = analytics["monthly"]["total_ngn"] if "monthly" in analytics else 0
            st.metric(
                "This Month",
                format_naira(monthly_ngn),
                delta=f"{analytics['monthly']['transactions']} transactions" if "monthly" in analytics else "0"
            )

        with col4:
            avg_ngn = analytics["average_transaction"]["ngn"] if "average_transaction" in analytics else 0
            st.metric(
                "Avg Transaction",
                format_naira(avg_ngn),
                delta="Per payment"
            )

        # Spending by category chart
        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Spending by Category")
            if analytics.get("category_breakdown"):
                categories = []
                amounts = []
                for cat, data in analytics["category_breakdown"].items():
                    categories.append(f"{get_category_emoji(cat)} {cat.title()}")
                    amounts.append(data["ngn"])

                fig = px.pie(
                    values=amounts,
                    names=categories,
                    color_discrete_sequence=px.colors.sequential.Purples_r
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No category data available yet")

        with col2:
            st.subheader("🏪 Top Merchants")
            if analytics.get("top_merchants"):
                merchant_df = pd.DataFrame(analytics["top_merchants"])
                if not merchant_df.empty:
                    merchant_df["amount_formatted"] = merchant_df["amount_ngn"].apply(format_naira)
                    for _, merchant in merchant_df.iterrows():
                        st.markdown(f"""
                        <div class="merchant-card">
                            <strong>{merchant['name']}</strong><br>
                            Total: {merchant['amount_formatted']}
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No merchant data available yet")

        # Recent transactions preview
        st.markdown("---")
        st.subheader("📜 Recent Transactions")
        txs_data = fetch_transactions()
        if txs_data and txs_data["transactions"]:
            recent_txs = txs_data["transactions"][:5]
            for tx in recent_txs:
                col1, col2, col3, col4 = st.columns([1, 2, 2, 2])
                with col1:
                    st.write(get_category_emoji(tx.get("category", "other")))
                with col2:
                    st.write(tx.get("merchant_name", "Unknown"))
                with col3:
                    st.write(format_naira(tx["amount_ngn"]))
                with col4:
                    timestamp = datetime.fromisoformat(tx["timestamp"])
                    st.write(timestamp.strftime("%d/%m %H:%M"))
        else:
            st.info("No transactions yet. Make your first payment to get started!")
    else:
        # Welcome screen for new users
        st.info("👋 Welcome to Test Tube! Make your first payment to see your dashboard.")
        st.markdown("""
        ### Getting Started:
        1. **Make a Payment** - Send SOL to campus merchants
        2. **Track Spending** - Monitor your expenses in real-time
        3. **Get Insights** - AI-powered financial advice
        4. **Export Data** - Download reports for budgeting
        """)

elif page == "💳 Make Payment":
    st.title("💳 Make a Payment")
    st.markdown("Send SOL to campus merchants or fellow students")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Quick Pay")

        # Fetch merchants for dropdown
        merchants = fetch_merchants()
        merchant_options = ["Custom Address"] + [f"{m['name']} - {m['category']}" for m in merchants]

        selected_merchant = st.selectbox("Select Merchant", merchant_options)

        if selected_merchant == "Custom Address":
            recipient = st.text_input("Recipient Address", placeholder="Enter Solana address...")
            category = st.selectbox("Category",
                                    ["food", "transport", "data", "books", "entertainment", "utilities", "supplies",
                                     "other"])
        else:
            # Find selected merchant
            merchant_idx = merchant_options.index(selected_merchant) - 1
            merchant = merchants[merchant_idx]
            recipient = merchant["address"]
            category = merchant["category"]
            st.info(f"📍 {merchant['description']}")

        amount = st.number_input("Amount (SOL)", min_value=0.001, step=0.01, format="%.3f")

        # Show Naira equivalent
        if amount > 0:
            ngn_amount = amount * 100 * 1500  # Mock conversion
            st.markdown(f"**≈ {format_naira(ngn_amount)}**")

        description = st.text_input("Note (optional)", placeholder="What's this payment for?")

        if st.button("Send Payment 🚀", type="primary", use_container_width=True):
            if not recipient:
                st.error("Please enter a recipient address")
            elif amount <= 0:
                st.error("Please enter a valid amount")
            else:
                with st.spinner("Processing payment..."):
                    try:
                        response = requests.post(
                            f"{API_URL}/pay",
                            json={
                                "recipient": recipient,
                                "amount": amount,
                                "category": category,
                                "description": description
                            }
                        )

                        if response.status_code == 200:
                            result = response.json()
                            st.markdown(f"""
                                <div class="success-box">
                                    <h3>✅ Payment Successful!</h3>
                                    <p><strong>Amount:</strong> {result['amount_sol']} SOL ({format_naira(result['amount_ngn'])})</p>
                                    <p><strong>To:</strong> {result.get('merchant_name', 'Unknown')}</p>
                                    <p><strong>Transaction ID:</strong> <code>{result['tx_signature'][:20]}...</code></p>
                                    <p><strong>Time:</strong> {datetime.now().strftime('%H:%M:%S')}</p>
                                </div>
                            """, unsafe_allow_html=True)

                            st.balloons()
                        else:
                            st.error(f"Payment failed: {response.text}")
                    except Exception as e:
                        st.error(f"Error: {e}")

    with col2:
        st.subheader("Scan to Pay")

        # Generate QR code for receiving payments
        qr_address = st.text_input("Your Address (for receiving)", value="11111111111111111111111111111111")
        qr_amount = st.number_input("Request Amount (optional)", min_value=0.0, step=0.01)
        qr_label = st.text_input("Payment Label", value="Campus Payment")

        if st.button("Generate QR Code 📱", use_container_width=True):
            try:
                params = {"recipient": qr_address, "label": qr_label}
                if qr_amount > 0:
                    params["amount"] = qr_amount

                resp = requests.get(f"{API_URL}/qr/generate", params=params)
                if resp.status_code == 200:
                    img = Image.open(io.BytesIO(resp.content))
                    st.image(img, caption="Scan with Solana Pay wallet", width=300)
                    st.info("Show this QR code to receive payments")
            except Exception as e:
                st.error(f"Failed to generate QR: {e}")

elif page == "🤖 AI Insights":
    st.title("🤖 AI Financial Insights")
    st.markdown("Get personalized advice based on your spending patterns")

    # Period selector
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Today", use_container_width=True):
            period = "today"
        else:
            period = None
    with col2:
        if st.button("This Week", use_container_width=True):
            period = "week"
        else:
            period = period
    with col3:
        if st.button("This Month", use_container_width=True):
            period = "month"
        else:
            period = period if period else "today"

    # Fetch insights
    with st.spinner("Analyzing your spending patterns..."):
        insights = fetch_ai_insights(period)

    if insights:
        # Display main insights
        st.markdown(f"""
        <div class="insight-box">
            <h3>💡 Your Financial Insights</h3>
            <p>{insights.get('insights', 'No insights available')}</p>
        </div>
        """, unsafe_allow_html=True)

        # Display suggestions
        if insights.get("suggestions"):
            st.subheader("📌 Recommendations")
            for suggestion in insights["suggestions"]:
                st.markdown(f"• {suggestion}")

        # Period summary
        if insights.get("period_summary"):
            st.markdown("---")
            st.subheader("📊 Period Summary")
            summary = insights["period_summary"]

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Transactions", summary.get("total_transactions", 0))
            with col2:
                st.metric("Total Spent (SOL)", f"{summary.get('total_sol', 0):.3f}")
            with col3:
                st.metric("Total Spent (NGN)", format_naira(summary.get("total_ngn", 0)))

            if summary.get("top_category"):
                st.info(
                    f"🏆 Top spending category: {get_category_emoji(summary['top_category'])} {summary['top_category'].title()}")
    else:
        st.info("Make some transactions to get personalized insights!")

elif page == "📜 Transactions":
    st.title("📜 Transaction History")
    st.markdown("View and export your payment history")

    # Filters
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        category_filter = st.selectbox(
            "Category",
            ["All"] + ["food", "transport", "data", "books", "entertainment", "utilities", "supplies", "other"]
        )
    with col2:
        start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
    with col3:
        end_date = st.date_input("End Date", value=datetime.now())
    with col4:
        if st.button("Apply Filters", use_container_width=True):
            st.session_state.refresh_counter += 1

    # Fetch transactions
    params = {}
    if category_filter != "All":
        params["category"] = category_filter
    if start_date:
        params["start_date"] = start_date.isoformat()
    if end_date:
        params["end_date"] = end_date.isoformat()

    txs_data = fetch_transactions()

    if txs_data and txs_data.get("transactions"):
        # Summary stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Transactions", txs_data.get("total", 0))
        with col2:
            st.metric("Total SOL", f"{txs_data.get('total_sol', 0):.3f}")
        with col3:
            st.metric("Total NGN", format_naira(txs_data.get("total_ngn", 0)))

        # Transaction table
        st.markdown("---")
        transactions_df = pd.DataFrame(txs_data["transactions"])

        # Format the dataframe for display
        display_df = pd.DataFrame({
            "Time": pd.to_datetime(transactions_df["timestamp"]).dt.strftime("%d/%m/%Y %H:%M"),
            "Category": transactions_df["category"].apply(lambda x: f"{get_category_emoji(x)} {x.title()}"),
            "Merchant": transactions_df["merchant_name"].fillna("Unknown"),
            "Amount (SOL)": transactions_df["amount_sol"].apply(lambda x: f"{x:.3f}"),
            "Amount (NGN)": transactions_df["amount_ngn"].apply(format_naira),
            "Description": transactions_df["description"].fillna("-"),
            "TX ID": transactions_df["tx_signature"].apply(lambda x: x[:10] + "..." if len(x) > 10 else x)
        })

        st.dataframe(display_df, use_container_width=True)

        # Export options
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Download CSV", use_container_width=True):
                csv = display_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV file",
                    data=csv,
                    file_name=f"transactions_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )

        with col2:
            if st.button("📊 Download Full Report", use_container_width=True):
                st.info("Full report generation coming soon!")
    else:
        st.info("No transactions found for the selected filters.")

elif page == "🏪 Merchants":
    st.title("🏪 Campus Merchants")
    st.markdown("Registered merchants accepting Solana payments")

    merchants = fetch_merchants()

    if merchants:
        # Group merchants by category
        categories = {}
        for merchant in merchants:
            cat = merchant["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(merchant)

        # Display merchants by category
        for category, merchant_list in categories.items():
            st.subheader(f"{get_category_emoji(category)} {category.title()}")

            cols = st.columns(2)
            for i, merchant in enumerate(merchant_list):
                with cols[i % 2]:
                    st.markdown(f"""
                    <div class="info-card">
                        <h4>{merchant['name']}</h4>
                        <p>{merchant['description']}</p>
                        <p><small>Address: <code>{merchant['address'][:8]}...{merchant['address'][-8:]}</code></small></p>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("No merchants registered yet.")

    # Add merchant section
    st.markdown("---")
    st.subheader("🆕 Register as Merchant")
    st.info("Want to accept Solana payments on campus? Contact the Test Tube team to get registered!")

elif page == "📈 Analytics":
    st.title("📈 Advanced Analytics")
    st.markdown("Deep dive into your spending patterns")

    analytics = fetch_analytics()
    txs_data = fetch_transactions()

    if analytics and txs_data and txs_data.get("transactions"):
        # Time series analysis
        st.subheader("📊 Spending Trends")

        transactions_df = pd.DataFrame(txs_data["transactions"])
        transactions_df["timestamp"] = pd.to_datetime(transactions_df["timestamp"])
        transactions_df["date"] = transactions_df["timestamp"].dt.date

        # Daily spending
        daily_spending = transactions_df.groupby("date")["amount_ngn"].sum().reset_index()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily_spending["date"],
            y=daily_spending["amount_ngn"],
            mode='lines+markers',
            name='Daily Spending',
            line=dict(color='purple', width=2),
            marker=dict(size=8)
        ))

        fig.update_layout(
            title="Daily Spending Trend",
            xaxis_title="Date",
            yaxis_title="Amount (NGN)",
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)

        # Category comparison
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Category Distribution")
            if analytics.get("category_breakdown"):
                cat_df = pd.DataFrame([
                    {"Category": cat, "Amount": data["ngn"], "Count": data["count"]}
                    for cat, data in analytics["category_breakdown"].items()
                ])

                fig = px.bar(
                    cat_df,
                    x="Category",
                    y="Amount",
                    color="Count",
                    color_continuous_scale="Purples"
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("⏰ Spending by Hour")
            transactions_df["hour"] = transactions_df["timestamp"].dt.hour
            hourly_spending = transactions_df.groupby("hour")["amount_ngn"].sum().reset_index()

            fig = px.line(
                hourly_spending,
                x="hour",
                y="amount_ngn",
                markers=True,
                line_shape="spline"
            )
            fig.update_layout(
                xaxis_title="Hour of Day",
                yaxis_title="Total Spent (NGN)"
            )
            st.plotly_chart(fig, use_container_width=True)

        # Budget tracking
        st.markdown("---")
        st.subheader("💰 Budget Tracking")

        col1, col2, col3 = st.columns(3)

        with col1:
            daily_budget = st.number_input("Daily Budget (NGN)", min_value=0, value=5000, step=500)
            daily_spent = analytics["daily"]["total_ngn"]
            daily_remaining = max(0, daily_budget - daily_spent)

            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=daily_spent,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Today's Spending"},
                gauge={
                    'axis': {'range': [None, daily_budget]},
                    'bar': {'color': "purple"},
                    'steps': [
                        {'range': [0, daily_budget * 0.5], 'color': "lightgray"},
                        {'range': [daily_budget * 0.5, daily_budget * 0.8], 'color': "yellow"},
                        {'range': [daily_budget * 0.8, daily_budget], 'color': "orange"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': daily_budget
                    }
                }
            ))
            fig.update_layout(height=250)
            st.plotly_chart(fig, use_container_width=True)

            if daily_spent > daily_budget:
                st.markdown(f"""
                <div class="warning-box">
                    ⚠️ Over budget by {format_naira(daily_spent - daily_budget)}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.success(f"✅ {format_naira(daily_remaining)} remaining today")

        with col2:
            weekly_budget = st.number_input("Weekly Budget (NGN)", min_value=0, value=25000, step=1000)
            weekly_spent = analytics["weekly"]["total_ngn"]
            weekly_progress = (weekly_spent / weekly_budget * 100) if weekly_budget > 0 else 0

            st.metric(
                "Weekly Progress",
                f"{weekly_progress:.1f}%",
                delta=format_naira(weekly_spent)
            )
            st.progress(min(weekly_progress / 100, 1.0))

        with col3:
            monthly_budget = st.number_input("Monthly Budget (NGN)", min_value=0, value=80000, step=5000)
            monthly_spent = analytics["monthly"]["total_ngn"]
            monthly_progress = (monthly_spent / monthly_budget * 100) if monthly_budget > 0 else 0

            st.metric(
                "Monthly Progress",
                f"{monthly_progress:.1f}%",
                delta=format_naira(monthly_spent)
            )
            st.progress(min(monthly_progress / 100, 1.0))

        # Predictions
        st.markdown("---")
        st.subheader("🔮 Spending Predictions")

        # Simple projection based on average daily spending
        if len(daily_spending) > 0:
            avg_daily = daily_spending["amount_ngn"].mean()
            days_in_month = 30
            projected_monthly = avg_daily * days_in_month

            col1, col2 = st.columns(2)
            with col1:
                st.info(
                    f"📈 Based on your current spending pattern, you're likely to spend {format_naira(projected_monthly)} this month")
            with col2:
                if projected_monthly > monthly_budget:
                    overspend = projected_monthly - monthly_budget
                    st.warning(f"⚠️ You may exceed your monthly budget by {format_naira(overspend)}")
                else:
                    st.success(f"✅ You're on track to stay within budget!")
    else:
        st.info("Start making transactions to see advanced analytics!")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <small>
        Test Tube 🧪 - Campus Payments Powered by Solana & AI<br>
        Making Web3 simple for African students
    </small>
</div>
""", unsafe_allow_html=True)