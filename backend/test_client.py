import httpx
from eth_account import Account
from x402 import x402ClientSync
from x402.mechanisms.evm.exact import ExactEvmScheme
from x402.http.utils import encode_payment_signature_header, decode_payment_required_header
import json

def test_endpoint(client, wallet, endpoint_url, method="POST", data=None, files=None):
    print(f"\n--- Testing {endpoint_url} ---")
    if method == "POST":
        response = httpx.post(endpoint_url, json=data, files=files)
    else:
        response = httpx.get(endpoint_url)
        
    print(f"Status Code: {response.status_code}")
    if response.status_code != 402:
        print(f"Expected 402 Payment Required. Got {response.status_code}: {response.text}")
        return
        
    print("Received 402 Payment Required. Parsing challenge...")
    payment_required = decode_payment_required_header(response.headers['payment-required'])
    print(f"Challenge Accepts: {payment_required.accepts}")
    
    print("Signing the payment...")
    payload = client.create_payment_payload(payment_required)
    
    headers = {
        "Payment-Signature": encode_payment_signature_header(payload)
    }
    
    print("Retrying request with the payment proof attached...")
    if method == "POST":
        retry_response = httpx.post(endpoint_url, json=data, files=files, headers=headers)
    else:
        retry_response = httpx.get(endpoint_url, headers=headers)
        
    print(f"Retry Status Code: {retry_response.status_code}")
    if retry_response.status_code == 200:
        print(f"Success! Response: {retry_response.json()}")
    else:
        print(f"Failed! Error: {retry_response.text}")

def main():
    wallet = Account.create()
    print(f"Created test wallet: {wallet.address}")

    client = x402ClientSync()
    client.register("eip155:84532", ExactEvmScheme(signer=wallet))
    
    # Test Public Report Endpoint
    print("\n--- Testing Public /report Endpoint ---")
    res = httpx.post("http://localhost:8000/report", json={"identifier": "test@upi", "reporter_wallet": wallet.address})
    print(f"Report Response: {res.json()}")

    # Test /check-fraud-id
    test_endpoint(client, wallet, "http://localhost:8000/check-fraud-id", data={"identifier": "test@upi"})
    
    # Test /check-message
    test_endpoint(client, wallet, "http://localhost:8000/check-message", data={"text": "Hello click here for your urgent lottery!"})
    
    # For /check-qr-tamper we need a dummy image
    print("\n--- Creating dummy QR image for testing ---")
    import cv2
    import numpy as np
    dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.imwrite("dummy_qr.png", dummy_img)
    
    with open("dummy_qr.png", "rb") as f:
        files = {"file": ("dummy_qr.png", f, "image/png")}
        test_endpoint(client, wallet, "http://localhost:8000/check-qr-tamper", method="POST", data=None, files=files)

    # Test Admin Stats
    print("\n--- Testing Public /admin/stats Endpoint ---")
    res = httpx.get("http://localhost:8000/admin/stats")
    print(f"Admin Stats Response: {res.json()}")

if __name__ == "__main__":
    main()
