# from solana.rpc.api import Client
#
# http_client = Client("https://api.devnet.solana.com")

from fastapi import FastAPI
import random

app = FastAPI()

transactions = []

@app.get("/")
def root():
    return {"message": "Welcome to the Test Tube API 🚀"}

@app.post("/pay")
def pay(user: str, amount: float):
    tx_id = f"tx_{random.randint(1000, 9999)}"
    transaction = {"id": tx_id, "user": user, "amount": amount, "status": "confirmed"}
    transactions.append(transaction)
    return {"message": "Payment Simulated", "transaction": transaction}

@app.get("/transactions")
def get_transactions():
    return {"transactions": transactions}

@app.get("analytics")
def analytics():
    total = len(transactions)
    total_amount = sum(tx["amount"] for tx in transactions)
    suspicious = [tx for tx in transactions if tx["amount"] > 1000]
    return {
        "total_transactions": total,
        "total_amount": total_amount,
        "suspicious": suspicious
    }