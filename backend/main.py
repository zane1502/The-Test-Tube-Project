import os
import json
import asyncio
import qrcode
import io
import base64
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solders.message import MessageV0
from solders.transaction import VersionedTransaction
from openai import OpenAI
import pandas as pd
from enum import Enum

# Configuration
RPC_URL = "https://api.devnet.solana.com"
PAYER_FILE = "payer.json"
TRANSACTIONS_FILE = "transactions.json"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-api-key-here")

app = FastAPI(title="Test Tube API", version="1.0.0")

# Initialize OpenAI client for AI insights
ai_client = OpenAI(api_key=OPENAI_API_KEY)


# Transaction categories for campus spending
class TransactionCategory(str, Enum):
    FOOD = "food"
    TRANSPORT = "transport"
    DATA = "data"
    BOOKS = "books"
    ENTERTAINMENT = "entertainment"
    UTILITIES = "utilities"
    SUPPLIES = "supplies"
    OTHER = "other"


# Enhanced transaction storage
transactions_db = []

# Merchant database (mock - would be a real DB in production)
MERCHANTS = {
    "11111111111111111111111111111111": {
        "name": "Campus Cafeteria",
        "category": TransactionCategory.FOOD,
        "description": "Main campus dining hall"
    },
    "22222222222222222222222222222222": {
        "name": "Cab Car Park",
        "category": TransactionCategory.TRANSPORT,
        "description": "Campus transport service"
    },
    "33333333333333333333333333333333": {
        "name": "Data Reseller",
        "category": TransactionCategory.DATA,
        "description": "Mobile data and airtime"
    },
    "44444444444444444444444444444444": {
        "name": "Campus Bookstore",
        "category": TransactionCategory.BOOKS,
        "description": "Academic materials and stationery"
    }
}


# Utility functions
def save_keypair_json(kp: Keypair, path: str = PAYER_FILE):
    raw = list(bytes(kp))
    with open(path, "w") as f:
        json.dump(raw, f)


def load_keypair_json(path: str = PAYER_FILE) -> Keypair:
    with open(path, "r") as f:
        arr = json.load(f)
    return Keypair.from_bytes(bytes(arr))


def get_or_create_payer(path: str = PAYER_FILE) -> Keypair:
    if os.path.exists(path):
        return load_keypair_json(path)
    kp = Keypair()
    save_keypair_json(kp, path)
    print("Created new payer: ", kp.pubkey())
    return kp


def load_transactions():
    global transactions_db
    if os.path.exists(TRANSACTIONS_FILE):
        with open(TRANSACTIONS_FILE, "r") as f:
            transactions_db = json.load(f)


def save_transactions():
    with open(TRANSACTIONS_FILE, "w") as f:
        json.dump(transactions_db, f, indent=2)


def sol_to_naira(sol_amount: float) -> float:
    """Convert SOL to Naira (mock rate - would use real oracle in production)"""
    SOL_TO_USD = 100  # Mock rate
    USD_TO_NGN = 1500  # Mock rate
    return sol_amount * SOL_TO_USD * USD_TO_NGN


def format_naira(amount: float) -> str:
    """Format amount as Naira currency"""
    return f"₦{amount:,.2f}"


PAYER = get_or_create_payer(PAYER_FILE)
load_transactions()


# Pydantic models
class PaymentRequest(BaseModel):
    recipient: str
    amount: float = Field(gt=0, description="Amount in SOL")
    category: Optional[TransactionCategory] = TransactionCategory.OTHER
    description: Optional[str] = ""
    metadata: Optional[Dict[str, Any]] = {}


class TransactionRecord(BaseModel):
    id: str
    sender: str
    recipient: str
    merchant_name: Optional[str]
    amount_sol: float
    amount_ngn: float
    category: TransactionCategory
    description: str
    timestamp: datetime
    tx_signature: str
    metadata: Dict[str, Any]


class BudgetSettings(BaseModel):
    daily_limit: Optional[float] = None
    weekly_limit: Optional[float] = None
    monthly_limit: Optional[float] = None
    category_limits: Optional[Dict[TransactionCategory, float]] = {}


class AIInsightRequest(BaseModel):
    period: str = "today"  # today, week, month
    focus: Optional[str] = None  # specific category or general


# API Endpoints
@app.get("/")
def root():
    return {
        "message": "Welcome to Test Tube API 🧪",
        "description": "Campus payments powered by Solana + AI insights",
        "version": "1.0.0"
    }


@app.post("/pay", response_model=TransactionRecord)
async def process_payment(payment: PaymentRequest):
    """Process a payment on Solana blockchain"""
    try:
        recipient_pub = Pubkey.from_string(payment.recipient)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid recipient address: {e}")

    lamports = int(payment.amount * 1_000_000_000)

    async_client = AsyncClient(RPC_URL)
    try:
        # Check balance and airdrop if needed (devnet only)
        bal_resp = await async_client.get_balance(PAYER.pubkey())
        bal_lamports = bal_resp.value if hasattr(bal_resp, "value") else bal_resp["result"]["value"]

        if bal_lamports < lamports:
            print("Requesting airdrop...")
            await async_client.request_airdrop(PAYER.pubkey(), 2_000_000_000)
            await asyncio.sleep(3)

        # Get recent blockhash
        blockhash_resp = await async_client.get_latest_blockhash()
        recent_blockhash = blockhash_resp.value.blockhash

        # Create and send transaction
        ix = transfer(TransferParams(
            from_pubkey=PAYER.pubkey(),
            to_pubkey=recipient_pub,
            lamports=lamports
        ))

        message = MessageV0.try_compile(
            payer=PAYER.pubkey(),
            instructions=[ix],
            address_lookup_table_accounts=[],
            recent_blockhash=recent_blockhash
        )

        tx = VersionedTransaction(message, [PAYER])
        send_resp = await async_client.send_transaction(tx)

        # Extract transaction signature
        tx_sig = send_resp.value if hasattr(send_resp, "value") else str(send_resp)

        # Get merchant info
        merchant_info = MERCHANTS.get(payment.recipient, {})

        # Create transaction record
        tx_record = TransactionRecord(
            id=f"tx_{len(transactions_db) + 1}",
            sender=str(PAYER.pubkey()),
            recipient=payment.recipient,
            merchant_name=merchant_info.get("name"),
            amount_sol=payment.amount,
            amount_ngn=sol_to_naira(payment.amount),
            category=payment.category or merchant_info.get("category", TransactionCategory.OTHER),
            description=payment.description or merchant_info.get("description", ""),
            timestamp=datetime.now(),
            tx_signature=str(tx_sig),
            metadata=payment.metadata or {}
        )

        # Store transaction
        transactions_db.append(tx_record.dict())
        save_transactions()

        return tx_record

    finally:
        await async_client.close()


@app.get("/qr/generate")
async def generate_qr_code(
        recipient: str = Query(..., description="Recipient Solana address"),
        amount: Optional[float] = Query(None, description="Pre-filled amount"),
        label: Optional[str] = Query(None, description="Payment label")
):
    """Generate Solana Pay QR code for merchants"""
    try:
        # Validate address
        Pubkey.from_string(recipient)
    except:
        raise HTTPException(status_code=400, detail="Invalid Solana address")

    # Create Solana Pay URL
    solana_pay_url = f"solana:{recipient}"
    params = []
    if amount:
        params.append(f"amount={amount}")
    if label:
        params.append(f"label={label}")
    if params:
        solana_pay_url += "?" + "&".join(params)

    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(solana_pay_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to bytes
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    return StreamingResponse(img_byte_arr, media_type="image/png")


@app.get("/transactions")
def get_transactions(
        category: Optional[TransactionCategory] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = Query(50, le=100)
):
    """Get transaction history with filtering"""
    filtered_txs = transactions_db.copy()

    # Filter by category
    if category:
        filtered_txs = [tx for tx in filtered_txs if tx.get("category") == category]

    # Filter by date range
    if start_date:
        start = datetime.fromisoformat(start_date)
        filtered_txs = [tx for tx in filtered_txs if datetime.fromisoformat(tx["timestamp"]) >= start]

    if end_date:
        end = datetime.fromisoformat(end_date)
        filtered_txs = [tx for tx in filtered_txs if datetime.fromisoformat(tx["timestamp"]) <= end]

    # Sort by timestamp (newest first) and limit
    filtered_txs.sort(key=lambda x: x["timestamp"], reverse=True)

    return {
        "transactions": filtered_txs[:limit],
        "total": len(filtered_txs),
        "total_sol": sum(tx["amount_sol"] for tx in filtered_txs),
        "total_ngn": sum(tx["amount_ngn"] for tx in filtered_txs)
    }


@app.post("/ai/insights")
async def get_ai_insights(request: AIInsightRequest):
    """Generate AI-powered spending insights"""

    # Get transactions for the specified period
    now = datetime.now()
    if request.period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif request.period == "week":
        start_date = now - timedelta(days=7)
    elif request.period == "month":
        start_date = now - timedelta(days=30)
    else:
        start_date = now - timedelta(days=1)

    period_txs = [
        tx for tx in transactions_db
        if datetime.fromisoformat(tx["timestamp"]) >= start_date
    ]

    if not period_txs:
        return {
            "insights": "No transactions found for this period. Start making payments to get personalized insights!",
            "suggestions": []
        }

    # Prepare spending summary for AI
    category_spending = {}
    for tx in period_txs:
        cat = tx.get("category", "other")
        if cat not in category_spending:
            category_spending[cat] = {"count": 0, "total_sol": 0, "total_ngn": 0}
        category_spending[cat]["count"] += 1
        category_spending[cat]["total_sol"] += tx["amount_sol"]
        category_spending[cat]["total_ngn"] += tx["amount_ngn"]

    # Create AI prompt
    prompt = f"""
    You are a friendly financial advisor for Nigerian university students. 
    Analyze this spending data and provide insights in simple, relatable language:

    Period: {request.period}
    Total transactions: {len(period_txs)}
    Total spent: {sum(tx['amount_sol'] for tx in period_txs):.2f} SOL (₦{sum(tx['amount_ngn'] for tx in period_txs):,.2f})

    Category breakdown:
    {json.dumps(category_spending, indent=2)}

    Provide:
    1. A brief, friendly summary of spending patterns
    2. Any concerns about spending habits
    3. Practical tips specific to campus life

    Keep it conversational, use Nigerian context, and be encouraging but honest. Preferably One or two lines.
    """

    try:
        response = ai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )

        insights = response.choices[0].message.content

    except Exception as e:
        # Fallback to rule-based insights if AI fails
        insights = generate_fallback_insights(category_spending, period_txs)

    # Generate suggestions
    suggestions = generate_suggestions(category_spending)

    return {
        "insights": insights,
        "suggestions": suggestions,
        "period_summary": {
            "total_transactions": len(period_txs),
            "total_sol": sum(tx["amount_sol"] for tx in period_txs),
            "total_ngn": sum(tx["amount_ngn"] for tx in period_txs),
            "top_category": max(category_spending.items(), key=lambda x: x[1]["total_sol"])[
                0] if category_spending else None
        }
    }


def generate_fallback_insights(category_spending: Dict, transactions: List) -> str:
    """Generate rule-based insights when AI is unavailable"""
    total_sol = sum(tx["amount_sol"] for tx in transactions)
    total_ngn = sum(tx["amount_ngn"] for tx in transactions)

    insights = f"You've made {len(transactions)} transactions totaling {total_sol:.2f} SOL ({format_naira(total_ngn)}). "

    if category_spending:
        top_category = max(category_spending.items(), key=lambda x: x[1]["total_sol"])[0]
        top_amount = category_spending[top_category]["total_ngn"]

        insights += f"Most of your spending ({format_naira(top_amount)}) was on {top_category}. "

        if top_category == "food" and top_amount > 50000:
            insights += "Your food budget seems high - consider cooking more often. "
        elif top_category == "data" and top_amount > 20000:
            insights += "Data expenses are significant - look for student bundles or campus WiFi. "
        elif top_category == "transport" and top_amount > 30000:
            insights += "Transport costs are adding up - try sharing rides with classmates. "

    return insights


def generate_suggestions(category_spending: Dict) -> List[str]:
    """Generate actionable suggestions based on spending"""
    suggestions = []

    for category, data in category_spending.items():
        if category == "food" and data["total_ngn"] > 50000:
            suggestions.append("Join a cooking group or meal prep on Sundays to save on food")
        elif category == "data" and data["total_ngn"] > 20000:
            suggestions.append("Check if your department has free WiFi access codes")
        elif category == "transport" and data["total_ngn"] > 30000:
            suggestions.append("Form a carpool group with coursemates living in your area")

    if not suggestions:
        suggestions.append("You're managing your budget well! Keep tracking your expenses")

    return suggestions[:3]  # Return top 3 suggestions


@app.get("/analytics/summary")
def get_analytics_summary():
    """Get comprehensive analytics for dashboard"""
    if not transactions_db:
        return {
            "message": "No transactions yet",
            "stats": {}
        }

    now = datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    # Calculate metrics
    today_txs = [tx for tx in transactions_db if datetime.fromisoformat(tx["timestamp"]) >= today]
    week_txs = [tx for tx in transactions_db if datetime.fromisoformat(tx["timestamp"]) >= week_ago]
    month_txs = [tx for tx in transactions_db if datetime.fromisoformat(tx["timestamp"]) >= month_ago]

    # Category breakdown
    category_totals = {}
    for tx in month_txs:
        cat = tx.get("category", "other")
        if cat not in category_totals:
            category_totals[cat] = {"count": 0, "sol": 0, "ngn": 0}
        category_totals[cat]["count"] += 1
        category_totals[cat]["sol"] += tx["amount_sol"]
        category_totals[cat]["ngn"] += tx["amount_ngn"]

    # Top merchants
    merchant_spending = {}
    for tx in month_txs:
        merchant = tx.get("merchant_name", "Unknown")
        if merchant not in merchant_spending:
            merchant_spending[merchant] = 0
        merchant_spending[merchant] += tx["amount_ngn"]

    top_merchants = sorted(merchant_spending.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "daily": {
            "transactions": len(today_txs),
            "total_sol": sum(tx["amount_sol"] for tx in today_txs),
            "total_ngn": sum(tx["amount_ngn"] for tx in today_txs)
        },
        "weekly": {
            "transactions": len(week_txs),
            "total_sol": sum(tx["amount_sol"] for tx in week_txs),
            "total_ngn": sum(tx["amount_ngn"] for tx in week_txs)
        },
        "monthly": {
            "transactions": len(month_txs),
            "total_sol": sum(tx["amount_sol"] for tx in month_txs),
            "total_ngn": sum(tx["amount_ngn"] for tx in month_txs)
        },
        "category_breakdown": category_totals,
        "top_merchants": [{"name": name, "amount_ngn": amount} for name, amount in top_merchants],
        "average_transaction": {
            "sol": sum(tx["amount_sol"] for tx in month_txs) / len(month_txs) if month_txs else 0,
            "ngn": sum(tx["amount_ngn"] for tx in month_txs) / len(month_txs) if month_txs else 0
        }
    }


@app.get("/export/csv")
def export_transactions_csv(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
):
    """Export transactions as CSV for Excel"""
    filtered_txs = transactions_db.copy()

    if start_date:
        start = datetime.fromisoformat(start_date)
        filtered_txs = [tx for tx in filtered_txs if datetime.fromisoformat(tx["timestamp"]) >= start]

    if end_date:
        end = datetime.fromisoformat(end_date)
        filtered_txs = [tx for tx in filtered_txs if datetime.fromisoformat(tx["timestamp"]) <= end]

    if not filtered_txs:
        raise HTTPException(status_code=404, detail="No transactions found")

    # Create DataFrame
    df = pd.DataFrame(filtered_txs)

    # Format for Excel
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["amount_ngn_formatted"] = df["amount_ngn"].apply(lambda x: f"₦{x:,.2f}")

    # Convert to CSV
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    return StreamingResponse(
        io.BytesIO(csv_buffer.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"}
    )


@app.get("/merchants")
def list_merchants():
    """Get list of registered merchants"""
    return {
        "merchants": [
            {
                "address": addr,
                "name": info["name"],
                "category": info["category"],
                "description": info["description"]
            }
            for addr, info in MERCHANTS.items()
        ]
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)