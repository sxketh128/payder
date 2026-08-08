import asyncio
import os
from cdp import CdpClient

async def main():
    agent_address = "0xeaa69f306b43F8F10CD3E6a04cDe4bd9B31624FB"
    print(f"Requesting funds from Base Sepolia testnet faucet for {agent_address}...")
    
    try:
        # Initialize the client (automatically picks up env variables)
        async with CdpClient() as cdp:
            # Request funds from the faucet
            print("Initiating faucet request...")
            faucet_tx = await cdp.evm.request_faucet(
                address=agent_address,
                network="base-sepolia",
                token="eth"
            )
            
            print("SUCCESS! Faucet transaction initiated.")
            print(f"Transaction Hash: {faucet_tx.transaction_hash}")
            
    except Exception as e:
        print(f"Error during funding process: {e}")

if __name__ == "__main__":
    asyncio.run(main())
