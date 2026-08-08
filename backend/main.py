from fastapi import FastAPI, Request, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import traceback
import cv2
import numpy as np
import hashlib
import os
import requests

from x402 import x402ResourceServer, VerifyResponse, SettleResponse, SupportedResponse, SupportedKind
from x402.http.middleware.fastapi import payment_middleware
from x402 import x402Facilitator
from x402.mechanisms.evm.exact import ExactEvmServerScheme, ExactEvmFacilitatorScheme
from eth_account import Account
import database
import agent

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Database Initialization -----------------
database.init_db()

# ----------------- Genuine x402 Facilitator -----------------
# For hackathon validation, the backend MUST verify transactions against the real blockchain.
receiver_pk = os.getenv("RECEIVER_PRIVATE_KEY")
receiver_wallet = Account.from_key(receiver_pk) if receiver_pk else Account.create()

facilitator = x402Facilitator()
facilitator.register(["eip155:84532"], ExactEvmFacilitatorScheme(receiver_wallet))

server = x402ResourceServer(facilitator)
server.register("eip155:84532", ExactEvmServerScheme())

# ----------------- Global Exception Handler -----------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Exception: {exc}")
    traceback.print_exc()
    return JSONResponse(status_code=500, content={"message": str(exc)})

# ----------------- Pydantic Models -----------------
class ReportRequest(BaseModel):
    identifier: str
    reporter_wallet: str

class CheckFraudIdRequest(BaseModel):
    identifier: str

class CheckMessageRequest(BaseModel):
    text: str

class AuthRequest(BaseModel):
    email: str
    password: str

class AdminAuthRequest(BaseModel):
    username: str
    password: str

app.include_router(agent.router)

# ----------------- Public Endpoints -----------------
@app.post("/report")
async def report(req: ReportRequest):
    """Free endpoint to report an identifier (UPI ID, phone number, etc)."""
    success = database.add_report(req.identifier, req.reporter_wallet)
    return {"success": success}

@app.get("/admin/stats")
async def admin_stats():
    """Free endpoint for admin dashboard."""
    return database.get_admin_stats()

@app.post("/auth/signup")
async def auth_signup(req: AuthRequest):
    pw_hash = hashlib.sha256(req.password.encode()).hexdigest()
    success = database.create_user(req.email, pw_hash)
    if success:
        return {"success": True}
    return JSONResponse(status_code=400, content={"message": "User already exists"})

@app.post("/auth/login")
async def auth_login(req: AuthRequest):
    pw_hash = hashlib.sha256(req.password.encode()).hexdigest()
    success = database.verify_user(req.email, pw_hash)
    if success:
        return {"success": True}
    return JSONResponse(status_code=401, content={"message": "Invalid credentials"})

@app.post("/admin/login")
async def admin_login(req: AdminAuthRequest):
    if req.username == "admin" and req.password == "admin123":
        return {"success": True}
    return JSONResponse(status_code=401, content={"message": "Invalid admin credentials"})

# ----------------- x402 Gated Routes Configuration -----------------
routes = {
    "POST /check-fraud-id": {
        "accepts": {
            "network": "eip155:84532",
            "scheme": "exact",
            "price": "0.01",
            "payTo": "0x0000000000000000000000000000000000000000",
        }
    },
    "POST /check-qr-tamper": {
        "accepts": {
            "network": "eip155:84532",
            "scheme": "exact",
            "price": "0.01",
            "payTo": "0x0000000000000000000000000000000000000000",
        }
    },
    "POST /check-message": {
        "accepts": {
            "network": "eip155:84532",
            "scheme": "exact",
            "price": "0.01",
            "payTo": "0x0000000000000000000000000000000000000000",
        }
    },
    # The old test-payment endpoint for backwards compatibility during testing
    "GET /test-payment": {
        "accepts": {
            "network": "eip155:84532",
            "scheme": "exact",
            "price": "0.01",
            "payTo": "0x0000000000000000000000000000000000000000",
        }
    }
}

app.middleware("http")(payment_middleware(routes, server, sync_facilitator_on_start=True))

# ----------------- x402 Gated Endpoints -----------------
@app.get("/test-payment")
async def test_payment(request: Request):
    receipt = request.scope.get("x402_receipt")
    if receipt:
        receipt_data = {
            "transaction_id": receipt.transaction,
            "amount": receipt.amount or "$0.01"
        }
    else:
        receipt_data = {}
    return {"status": "success", "message": "Payment verified", "receipt": receipt_data}

@app.post("/check-fraud-id")
async def check_fraud_id(req: CheckFraudIdRequest, request: Request):
    """Checks hardcoded bad list, then community reports. 2+ reports means flagged."""
    KNOWN_BAD_IDS = {"scammer@upi", "fraud@okicici", "fake@ybl", "test@upi"}
    
    if req.identifier in KNOWN_BAD_IDS:
        status = "Flagged"
        reason = "Matched against known-bad database."
    else:
        count = database.count_reports(req.identifier)
        status = "Flagged" if count >= 2 else "Safe"
        reason = f"Reported by {count} distinct wallets."
    
    # Log the check and the x402 transaction
    database.log_check(req.identifier, status, "fraud_id")
    receipt = request.scope.get("x402_receipt")
    if receipt:
        database.log_x402_transaction("/check-fraud-id", receipt.transaction, "0.01")
    return {"status": status, "reason": reason}

@app.post("/check-qr-tamper")
async def check_qr_tamper(request: Request, file: UploadFile = File(...)):
    """Runs a basic OpenCV check to see if a QR is readable."""
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    status = "Safe"
    if img is None:
        status = "Flagged"
    else:
        detector = cv2.QRCodeDetector()
        data, bbox, _ = detector.detectAndDecode(img)
        # If no QR code could be decoded, we flag it as potential tampering or invalid
        if not data:
            status = "Flagged"
            
    # Log the check
    database.log_check("qr_upload", status, "qr_tamper")
    receipt = request.scope.get("x402_receipt")
    if receipt:
        database.log_x402_transaction("/check-qr-tamper", receipt.transaction, "0.01")
    return {"status": status}

@app.post("/check-message")
async def check_message(req: CheckMessageRequest, request: Request):
    """LLM logic: Send text to Gemini to classify as SCAM, SPAM, or SAFE."""
    api_key = os.getenv("GEMINI_API_KEY")
    status = "Safe"
    reason = "No explanation provided."
    
    if not api_key:
        # Fallback if no API key is provided
        lower_text = req.text.lower()
        suspicious = ["urgent", "winner", "click here", "lottery", "password", "otp"]
        if any(kw in lower_text for kw in suspicious):
            status = "Flagged"
            reason = "Matched generic suspicious keywords (No API key found)."
    else:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        prompt = (
            "You are a fraud detection assistant. Classify this message as SCAM, SPAM, or SAFE. "
            "Look for: urgency/pressure tactics, requests for OTP/PIN/personal info, suspicious links, "
            "impersonation of banks/companies, prize/lottery claims, unusual payment requests. "
            f"Respond with ONLY a JSON object in this format: {{\"classification\": \"SCAM\", \"reason\": \"...\"}}. Message: '{req.text}'"
        )
        try:
            res = requests.post(url, json={
                "contents": [{"parts": [{"text": prompt}]}]
            })
            if res.status_code == 200:
                data = res.json()
                text_response = data['candidates'][0]['content']['parts'][0]['text']
                # basic parsing of JSON response from LLM
                import json
                try:
                    # Strip any markdown backticks if present
                    clean_text = text_response.replace('```json', '').replace('```', '').strip()
                    parsed = json.loads(clean_text)
                    cls = parsed.get("classification", "SAFE").upper()
                    status = "Flagged" if cls in ["SCAM", "SPAM"] else "Safe"
                    reason = parsed.get("reason", "Analyzed by AI.")
                except Exception:
                    # fallback if LLM didn't return perfect JSON
                    status = "Flagged" if "SCAM" in text_response.upper() or "SPAM" in text_response.upper() else "Safe"
                    reason = text_response
            else:
                status = "Flagged"
                reason = "Error communicating with AI service."
        except Exception as e:
            status = "Flagged"
            reason = f"AI Service Error: {str(e)}"
            
    # Log the check
    database.log_check(req.text[:20] + "...", status, "message_check")
    receipt = request.scope.get("x402_receipt")
    if receipt:
        database.log_x402_transaction("/check-message", receipt.transaction, "0.01")
    return {"status": status, "reason": reason}
