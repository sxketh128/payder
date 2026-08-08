from fastapi import FastAPI, Request, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import traceback
import cv2
import numpy as np

from x402 import x402ResourceServer, VerifyResponse, SettleResponse, SupportedResponse, SupportedKind
from x402.http.middleware.fastapi import payment_middleware
from x402.mechanisms.evm.exact import ExactEvmServerScheme
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

# ----------------- Mock x402 Facilitator -----------------
class MockFacilitatorClient:
    async def verify(self, payload, requirements) -> VerifyResponse:
        return VerifyResponse(is_valid=True)
    async def settle(self, payload, requirements) -> SettleResponse:
        return SettleResponse(success=True, transaction="0xmocktx", network="eip155:84532")
    def get_supported(self) -> SupportedResponse:
        return SupportedResponse(kinds=[
            SupportedKind(x402_version=2, network="eip155:84532", scheme="exact", asset="eth")
        ])

facilitator = MockFacilitatorClient()
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
    """Checks community reports. 2+ reports means flagged."""
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
    """Dummy LLM logic: Flag if contains 'urgent', 'winner', 'click here'."""
    lower_text = req.text.lower()
    suspicious_keywords = ["urgent", "winner", "click here", "lottery", "password", "otp"]
    
    status = "Safe"
    for kw in suspicious_keywords:
        if kw in lower_text:
            status = "Flagged"
            break
            
    # Log the check
    database.log_check(req.text[:20] + "...", status, "message_check")
    receipt = request.scope.get("x402_receipt")
    if receipt:
        database.log_x402_transaction("/check-message", receipt.transaction, "0.01")
    return {"status": status}
