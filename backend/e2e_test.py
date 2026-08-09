import httpx
import asyncio

async def test_flow():
    async with httpx.AsyncClient() as client:
        print("1. Signup")
        await client.post("http://127.0.0.1:8000/auth/signup", json={"email": "saket@gmail.com", "password": "password123"})
        
        print("2. Login")
        res = await client.post("http://127.0.0.1:8000/auth/login", json={"email": "saket@gmail.com", "password": "password123"})
        print(res.json())
        
        print("3. Check UPI ID (Safe initially)")
        # This will be logged to saket@gmail.com
        res = await client.post("http://127.0.0.1:8000/check-fraud-id?user_email=saket@gmail.com", json={"identifier": "testmerchant@upi"})
        print(res.json())
        
        print("4. Get User Checks")
        res = await client.get("http://127.0.0.1:8000/user/checks?user_email=saket@gmail.com")
        print(res.json())
        
        print("5. Get User Insights")
        res = await client.get("http://127.0.0.1:8000/user/insights?user_email=saket@gmail.com")
        print(res.json())
        
        print("6. Report from Wallet 1")
        await client.post("http://127.0.0.1:8000/report", json={"identifier": "testmerchant@upi", "reporter_wallet": "wallet1"})
        
        print("7. Report from Wallet 2 (Triggers notification)")
        await client.post("http://127.0.0.1:8000/report", json={"identifier": "testmerchant@upi", "reporter_wallet": "wallet2"})
        
        print("8. Check Notifications for saket@gmail.com")
        res = await client.get("http://127.0.0.1:8000/user/notifications?user_email=saket@gmail.com")
        print(res.json())
        
        print("9. Mark Notifications Read")
        await client.post("http://127.0.0.1:8000/user/notifications/read", json={"user_email": "saket@gmail.com"})
        
        print("10. Check Notifications again")
        res = await client.get("http://127.0.0.1:8000/user/notifications?user_email=saket@gmail.com")
        print(res.json())

if __name__ == "__main__":
    asyncio.run(test_flow())
