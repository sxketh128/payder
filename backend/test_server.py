import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from x402 import x402ResourceServer
from x402.http.middleware.fastapi import payment_middleware
from x402.mechanisms.evm.exact import ExactEvmServerScheme
import uvicorn
import httpx
import threading
import time

app = FastAPI()
server = x402ResourceServer()
server.register("eip155:84532", ExactEvmServerScheme())

routes = {
    "GET /test-payment": {
        "accepts": {
            "scheme": "exact",
            "payTo": "0x0000000000000000000000000000000000000000",
            "price": "$0.01",
            "network": "eip155:84532",
        }
    }
}

app.middleware("http")(payment_middleware(routes, server, sync_facilitator_on_start=False))

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"message": str(exc)})

@app.get("/test-payment")
async def test_payment():
    return {"status": "success"}

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="error")

threading.Thread(target=run_server, daemon=True).start()
time.sleep(2)

try:
    resp = httpx.get("http://127.0.0.1:8001/test-payment")
    print("STATUS", resp.status_code)
    print("HEADERS", resp.headers)
    print("BODY", resp.text)
except Exception as e:
    print(e)
