import x402
print(dir(x402))
try:
    from x402.fastapi import PaymentMiddleware
    print("FastAPI middleware available")
except Exception as e:
    print(e)
