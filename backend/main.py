import os
import json
import asyncio


from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solders.message import MessageV0
from solders.transaction import Transaction, VersionedTransaction


RPC_URL = "https://api.devnet.solana.com"
PAYER_FILE = "payer.json"

app = FastAPI()

transactions = []

def save_keypair_json(kp: Keypair, path: str = PAYER_FILE):
    raw = list(bytes(kp))
    with open(path, "w") as f:
        json.dump(raw, f)

def load_keypair_json(path: str = PAYER_FILE) -> Keypair:
    with open(path, "r") as f:
        arr = json.load(f)

    return  Keypair.from_bytes(bytes(arr))

def get_or_create_payer(path: str = PAYER_FILE) -> Keypair:
    if os.path.exists(path):
        return load_keypair_json(path)

    kp = Keypair()
    save_keypair_json(kp, path)
    print("Created new payer: ", kp.pubkey())
    return kp

PAYER = get_or_create_payer(PAYER_FILE)

class PayIn(BaseModel):
    recipient: str
    amount: float


@app.get("/")
def root():
    return {"message": "Welcome to the Test Tube API 🚀"}

@app.post("/pay")
async def pay(input_val: PayIn):

    try:
        recipient_pub = Pubkey.from_string(input_val.recipient)
    except Exception as e:
        raise HTTPException(status_code= 400, detail= f"Invalid recipient public key: {e}")

    lamports = int(input_val.amount * 1_000_000_000)
    async_client = AsyncClient(RPC_URL)

    try:
        bal_resp = await async_client.get_balance(PAYER.pubkey())
        bal_lamports = bal_resp.value if hasattr(bal_resp, "value") else bal_resp["result"]["value"]
        if bal_lamports == 0:
            await  async_client.request_airdrop(PAYER.pubkey(), 1_000_000_000)
            await asyncio.sleep(2)

        blockhash_resp = await async_client.get_latest_blockhash()
        recent_blockhash = blockhash_resp.value.blockhash

        ix = transfer(TransferParams(
            from_pubkey=PAYER.pubkey(),
            to_pubkey=recipient_pub,
            lamports=lamports
        ))

        message = MessageV0.try_compile(
            payer= PAYER.pubkey(),
            instructions=[ix],
            address_lookup_table_accounts=[],
            recent_blockhash=recent_blockhash
        )

        tx = VersionedTransaction(message, [PAYER])

        send_resp = await async_client.send_transaction(tx)

        tx_sig = None

        try:
            tx_sig = send_resp.value if hasattr(send_resp, "value") else (send_resp["result"] if isinstance(send_resp, dict) else str(send_resp))
        except Exception:
            tx_sig = str(send_resp)

        return {"tx_sig": tx_sig, "raw_send_resp": str(send_resp)}

    finally:
        await async_client.close()


@app.get("/transactions")
def get_transactions():
    return {"transactions": transactions}

@app.get("/analytics")
def analytics():
    total = len(transactions)
    total_amount = sum(tx["amount"] for tx in transactions)
    suspicious = [tx for tx in transactions if tx["amount"] > 1000]
    return {
        "total_transactions": total,
        "total_amount": total_amount,
        "suspicious": suspicious
    }
