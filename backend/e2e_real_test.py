import httpx
from eth_account import Account
from x402 import x402ClientSync
from x402.mechanisms.evm.exact import ExactEvmScheme
from x402.http.utils import encode_payment_signature_header, decode_payment_required_header

def main():
    wallet = Account.create()
    client = x402ClientSync()
    client.register("eip155:84532", ExactEvmScheme(signer=wallet))

    email = "tester@gmail.com"
    httpx.post("http://localhost:8000/auth/signup", json={"email": email, "password": "pass"})

    print("--- Testing /check-fraud-id with user_email ---")
    res = httpx.post(f"http://localhost:8000/check-fraud-id?user_email={email}", json={"identifier": "trigger@upi"})
    
    if res.status_code == 402:
        pr = decode_payment_required_header(res.headers['payment-required'])
        payload = client.create_payment_payload(pr)
        headers = {"Payment-Signature": encode_payment_signature_header(payload)}
        res2 = httpx.post(f"http://localhost:8000/check-fraud-id?user_email={email}", json={"identifier": "trigger@upi"}, headers=headers)
        print("Check result:", res2.json())

    print("--- Checks ---")
    print(httpx.get(f"http://localhost:8000/user/checks?user_email={email}").json())
    
    print("--- Reporting ---")
    httpx.post("http://localhost:8000/report", json={"identifier": "trigger@upi", "reporter_wallet": "w1"})
    httpx.post("http://localhost:8000/report", json={"identifier": "trigger@upi", "reporter_wallet": "w2"})
    
    print("--- Notifications ---")
    print(httpx.get(f"http://localhost:8000/user/notifications?user_email={email}").json())

if __name__ == "__main__":
    main()
