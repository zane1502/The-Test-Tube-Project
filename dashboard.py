import streamlit as st
import requests

API_URL  = "http://127.0.0.1:8000"

st.title("Test Tube Dashboard")
st.write("Simulated Solana Pay + AI Analytics")

st.subheader("💳 Make a Payment")
with st.form("payment_form"):
    user = st.text_input("User", "Samuel")
    amount = st.number_input("Amount", min_value=0.0, step= 0.01)
    submitted = st.form_submit_button("Send Payment")

    if submitted:
        response = requests.post(url= f"{API_URL}/pay",
                                 params= {"user": user, "amount":amount})

        if response.status_code == 200:
            st.success(f"Payment Successful: {response.json()['transaction']}")

        else:
            st.error("Payment Failed")


st.subheader("📜 Transactions")
transactions = requests.get(f"{API_URL}/transactions").json().get("transactions", [])

if transactions:
    st.table(transactions)
else:
    st.info("No transactions yet.")


st.subheader("📊 Analytics")
analytics = requests.get(f"{API_URL}/analytics").json()
st.json(analytics)