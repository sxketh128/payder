<div align="center">
  <img src="https://raw.githubusercontent.com/sxketh128/payder/main/stitch_payder_fraud_detection_ui/screen.png" alt="Payder Banner" width="100%" />
</div>

<h1 align="center">Payder: AI-Powered UPI Fraud Protection</h1>

<p align="center">
  <strong>Secure, decentralized fraud detection powered by x402 micro-payments and AI.</strong>
</p>

<p align="center">
  <a href="#overview">Overview</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#features">Features</a> •
  <a href="#getting-started">Getting Started</a> •
  <a href="#deployment">Deployment</a>
</p>

---

## 📖 Overview

**Payder** is an advanced UPI scam-protection web application designed to instantly verify the legitimacy of UPI IDs, QR codes, and suspicious messages. 

Instead of relying on a centralized, monolithic subscription model, Payder utilizes a decentralized network of **x402-gated microservices**. Each check is paid for instantaneously by an internal **AI Payment Agent**, shielding the end-user from the friction of web3 crypto transactions while providing cryptographic proof of payment for every API call.

If a check returns a `Safe` verdict, Payder securely generates a native UPI deep-link (`upi://pay?...`) to seamlessly hand off the transaction to GPay, PhonePe, or Paytm. If a check is `Flagged`, the transaction is blocked, protecting the user from potential fraud.

---

## 🏗 Architecture

Payder operates on a split architecture consisting of three primary layers:

1. **The Static Frontend (Netlify Ready):** 
   A lightning-fast, static HTML/Tailwind interface that runs completely in the browser. It communicates directly with the Payment Agent.
2. **The AI Payment Agent (Orchestrator):** 
   A funded backend orchestrator built with FastAPI. It intercepts user requests, manages the x402 handshakes, signs cryptographic payment proofs on the Base Sepolia testnet, and returns the aggregated verdict.
3. **The x402 Microservices (Verifiers):**
   Gated FastAPI endpoints that charge `$0.01` per invocation. 
   - `Fraud ID Checker`: Cross-references reported malicious UPI IDs.
   - `QR Tamper Engine`: Uses OpenCV heuristics to detect modified or overlaid QR codes.
   - `Message Analyzer`: Analyzes text for common spam and phishing patterns.

---

## ✨ Features

- 🛡️ **Real-Time Fraud Prevention**: Instantly checks UPI IDs, QR codes, and messages.
- ⚡ **Seamless Handoff**: Generates verified native deep-links to popular payment apps.
- 💸 **x402 Micro-Payments**: Leverages the `x402` protocol for programmatic, per-request payments.
- 📊 **Live Admin Dashboard**: Real-time statistics, transaction tracking, and flagged number telemetry powered by SQLite.
- 📸 **Computer Vision QR Checking**: OpenCV integration to detect pixel manipulation in uploaded QR codes.

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- **Node.js** (Optional, for deploying via Netlify CLI)
- **Git**

### 1. Clone the Repository
```bash
git clone https://github.com/sxketh128/payder.git
cd payder
```

### 2. Backend Setup
The backend is powered by FastAPI and requires a Python virtual environment.

```bash
# Navigate to the backend directory
cd backend

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the local server
uvicorn main:app --host 127.0.0.1 --port 8000
```
*The API and AI Payment Agent will now be running on `http://127.0.0.1:8000`.*

### 3. Frontend Setup
The frontend consists of statically served HTML/JSX files and requires no complex build step for local development. 

Simply open the files directly in your browser:
- **Mobile Client**: Open `public/MobileHome.html` in your web browser.
- **Admin Dashboard**: Open `public/AdminDashboard.html` in your web browser.

*(Ensure the backend is running so the frontend can successfully fetch from `localhost:8000`)*

---

## 🌐 Deployment Strategy

Payder is built to be deployed across two specialized platforms:

### Frontend (Netlify)
The `public/` directory contains all necessary static files and a `netlify.toml` configuration.
```bash
# Deploy instantly using the Netlify CLI
npx netlify-cli deploy --dir=public --prod
```

### Backend (Render / Fly.io)
The `backend/` directory is equipped with a `requirements.txt` and a standard `Procfile` (`web: uvicorn main:app --host 0.0.0.0 --port $PORT`).
- Connect this repository to your preferred Python hosting provider (e.g., Render, Heroku).
- Set the root directory to `backend/`.
- **Note:** Remember to update the hardcoded `localhost:8000` URLs in the frontend HTML files to your new production backend URL before deploying the frontend.

---

## 🛠 Technologies Used

- **FastAPI**: High-performance asynchronous backend framework.
- **x402 Protocol**: Programmatic machine-to-machine crypto payments (Base Sepolia).
- **SQLite**: Lightweight database for storing reports and transaction telemetry.
- **OpenCV (`opencv-python`)**: Image processing heuristics for QR tampering.
- **Tailwind CSS**: Utility-first CSS framework for rapid UI styling.

---
*Built with precision for the modern decentralized web.*
