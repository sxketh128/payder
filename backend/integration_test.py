import subprocess
import time
import sys
import os

print("Starting server...")
server_process = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "main:app", "--port", "8000"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Wait for server to start
time.sleep(3)

print("Starting client...")
client_process = subprocess.run(
    [sys.executable, "test_client.py"],
    capture_output=True,
    text=True
)

print("\n--- Client Output ---")
print(client_process.stdout)

if client_process.stderr:
    print("\n--- Client Errors ---")
    print(client_process.stderr)

print("\n--- Server Errors (if any) ---")
server_process.terminate()
stdout, stderr = server_process.communicate()
if stderr:
    print(stderr)
