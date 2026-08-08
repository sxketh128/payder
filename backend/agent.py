import httpx
import asyncio
from eth_account import Account
from fastapi import APIRouter
from pydantic import BaseModel
from x402 import x402Client
from x402.mechanisms.evm.exact import ExactEvmScheme
from x402.http.utils import encode_payment_signature_header, decode_payment_required_header
import base64

router = APIRouter()

# The Agent has its own funded wallet (in this test, a random one)
agent_wallet = Account.create()
x402_client = x402Client()
x402_client.register("eip155:84532", ExactEvmScheme(signer=agent_wallet))

class AgentCheckRequest(BaseModel):
    # Depending on what the user checked
    type: str  # "upi", "qr", "message"
    value: str # The UPI ID, the base64 image data, or the text message

async def call_gated_service(url: str, method: str, data: dict = None, files: dict = None):
    async with httpx.AsyncClient() as client:
        if method == "POST":
            response = await client.post(url, json=data, files=files)
        else:
            response = await client.get(url)
            
        if response.status_code != 402:
            return {"error": f"Expected 402, got {response.status_code}"}
            
        payment_required = decode_payment_required_header(response.headers['payment-required'])
        payload = await x402_client.create_payment_payload(payment_required)
        
        headers = {
            "Payment-Signature": encode_payment_signature_header(payload)
        }
        
        if method == "POST":
            retry_response = await client.post(url, json=data, files=files, headers=headers)
        else:
            retry_response = await client.get(url, headers=headers)
            
        if retry_response.status_code == 200:
            receipt = retry_response.headers.get("payment-response", "")
            return {"result": retry_response.json(), "receipt": receipt}
        else:
            return {"error": f"Failed with {retry_response.status_code}: {retry_response.text}"}

@router.post("/agent/check")
async def agent_check(req: AgentCheckRequest):
    """
    The Payment Agent orchestrates the checking process.
    For MVP, depending on type, it will call the relevant microservice(s).
    """
    verdict = "Safe"
    receipts = []
    
    if req.type == "upi":
        res = await call_gated_service("http://localhost:8000/check-fraud-id", "POST", data={"identifier": req.value})
        if "error" not in res:
            if res["result"]["status"] == "Flagged":
                verdict = "Flagged"
            receipts.append({"service": "check-fraud-id", "receipt": res["receipt"]})
            
    elif req.type == "qr":
        # Decode base64 to bytes
        try:
            # handle 'data:image/png;base64,...' prefix if present
            b64_data = req.value
            if "," in b64_data:
                b64_data = b64_data.split(",")[1]
            img_bytes = base64.b64decode(b64_data)
        except Exception:
            return {"verdict": "Flagged", "reason": "Invalid image"}
            
        files = {"file": ("upload.png", img_bytes, "image/png")}
        res = await call_gated_service("http://localhost:8000/check-qr-tamper", "POST", files=files)
        if "error" not in res:
            if res["result"]["status"] == "Flagged":
                verdict = "Flagged"
            receipts.append({"service": "check-qr-tamper", "receipt": res["receipt"]})
            
    elif req.type == "message":
        res = await call_gated_service("http://localhost:8000/check-message", "POST", data={"text": req.value})
        if "error" not in res:
            if res["result"]["status"] == "Flagged":
                verdict = "Flagged"
            receipts.append({"service": "check-message", "receipt": res["receipt"]})
            
    return {
        "verdict": verdict,
        "receipts": receipts
    }
