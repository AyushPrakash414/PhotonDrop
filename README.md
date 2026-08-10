<div align="center">

# ⚡ PhotonDrop

### Zero-Network Optical File Transfer Through Screen-to-Camera Visible Light

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.2-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![WebSockets](https://img.shields.io/badge/WebSockets-15Hz-FF6C37?style=for-the-badge&logo=socketdotio&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8%2B-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org)
[![Tests](https://img.shields.io/badge/Tests-54%2F54%20Passing-35A66F?style=for-the-badge&logo=pytest&logoColor=white)](https://docs.pytest.org)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

<br />

> **PhotonDrop** is an air-gapped optical file transfer system that transmits arbitrary binary files from one device screen to another using only visible light — **zero Wi-Fi, zero Bluetooth, zero cellular, zero Internet, and zero cables required.**

</div>

---

## 🌟 Highlights

- 🔒 **100% Offline & Air-Gapped**: Operates purely over physical light emitted by a display and captured by a camera lens.
- ⛲ **LT Fountain Coding**: Uses mathematically sound **Luby Transform (LT) codes** with **Robust Soliton Distribution** for infinite symbol streaming.
- 🛡️ **High Loss Tolerance**: Successfully reconstructs complete files even with **10% to 50% frame drop rates** or duplicate frames.
- 📦 **Arbitrary Binary File Support**: Transmit any file format (PNG, PDF, ZIP, MP4, EXE, DOCX) up to 100 MB.
- ⚡ **Dual Client Options**:
  - 🎨 **Modern React Web Dashboard**: Apple Fitness-inspired UI with Light/Dark mode, smooth progress rings, and base64 WebSocket frame streaming.
  - 🖥️ **Desktop PySide6 GUIs**: Native Python desktop windows for sender and receiver.
- 🔍 **Cryptographic Verification**: Per-packet CRC32 checksums + full file SHA-256 integrity validation.
- 📊 **Real-Time Telemetry**: Real measured Display FPS, Capture FPS, Decode FPS, Goodput (KB/s), Unique Symbols, and Duplicates.

---

## 📐 Architecture & Data Flow

```text
 ┌─────────────────────────────────────────────────────────────────────────────────┐
 │                                SENDER SIDE                                      │
 │                                                                                 │
 │   File  ──►  Block Splitting  ──►  LT Fountain Encoder  ──►  Protocol Packetizer │
 │                                     (Robust Soliton)           (CRC32 Checksum) │
 │                                                                       │         │
 │                                                                       ▼         │
 │  Display Screen  ◄──  Render Engine  ◄──  Base64 / QR Transport ◄─────┘         │
 └─────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                   VISIBLE LIGHT
                                  (Optical Channel)
                                         │
 ┌─────────────────────────────────────────────────────────────────────────────────┐
 │                               RECEIVER SIDE                                     │
 │                                                                                 │
 │   Camera Lens  ──►  Frame Preprocessing  ──►  QR Visual Decoder                 │
 │                      (Grayscale & CLAHE)     (OpenCV / pyzbar)                  │
 │                                                     │                           │
 │                                                     ▼                           │
 │   Saved File  ◄──  SHA-256 Hash Match  ◄──  Belief Propagation  ◄── Packet Filter│
 │  (disk output)     & Reassembly            Graph Peeling           (Session/CRC)│
 └─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎨 UI Design System

Inspired by **Apple Fitness** combined with modern productivity dashboards:

- **Theme Palette**:
  - Background: `#F5F5F3` (Light) / `#111111` (Dark)
  - Cards: `#FFFFFF` (Light) / `#1C1C1C` (Dark)
  - Primary Accent: `#F26A45` (Soft background: `#FDEFEA`)
  - Success: `#35A66F` | Error: `#D9534F` | Warning: `#E6A23C`
- **Typography & Geometry**:
  - `Plus Jakarta Sans` for titles & UI + `JetBrains Mono` for telemetry hashes
  - Large rounded cards (`20px–28px`), glassmorphism, pill buttons, optical ring pulse animations.

---

## 📂 Project Structure

```text
PhotonDrop/
├── shared/           # Core wire protocol, binary serialization, CRC32 & SHA-256
├── fountain/         # LT fountain encoder, belief propagation decoder, degree distribution
├── visual/           # QR transport encoder/decoder, CLAHE preprocessing, renderer
├── sender/           # File reader, block chunking, transmission engine, PySide6 UI
├── receiver/         # OpenCV camera capture QThread, packet processor, reconstruction
├── backend/          # FastAPI REST API + WebSockets telemetry server (15Hz push)
│   └── api/
│       ├── main.py
│       ├── sender_routes.py
│       ├── receiver_routes.py
│       ├── status_routes.py
│       └── websocket.py
├── frontend/         # Modern React 18 + Vite + TypeScript web dashboard
│   ├── src/
│   │   ├── app/      # Routes & main shell layout
│   │   ├── pages/    # Dashboard, SendPage, ReceivePage, ActivityPage, SettingsPage
│   │   ├── features/ # QRViewer, CameraViewer, SenderControl, ReceiverControl
│   │   ├── components/ # Sidebar, Header, MetricCard, StatusBadge, ProgressCard
│   │   ├── hooks/    # useSender, useReceiver, useTransfer
│   │   └── services/ # REST API client & WebSocket singleton
│   ├── vercel.json   # SPA rewrite rules for Vercel
│   └── vite.config.ts
├── tests/            # 54 unit, integration, loss simulation, and E2E test cases
├── render.yaml       # Infrastructure blueprint for Render deployment
├── pyproject.toml
└── requirements.txt
```

---

## 💻 Getting Started

### Prerequisites

- **Python** $\ge$ 3.10
- **Node.js** $\ge$ 18 & **npm** $\ge$ 9

### 1. Clone & Install Dependencies

```bash
# Clone repository
git clone https://github.com/AyushPrakash414/PhotonDrop.git
cd PhotonDrop

# Install Python backend dependencies
pip install -r requirements.txt

# Install React frontend dependencies
cd frontend
npm install
cd ..
```

---

## 🚀 Running the Application

### Option A: React Web Dashboard (Recommended)

Start the FastAPI backend server:
```bash
python -m backend.api.main
```

In a new terminal window, start the Vite frontend:
```bash
cd frontend
npm run dev
```

Open `http://localhost:5173` in your browser.

### Option B: PySide6 Desktop GUIs

```bash
# Launch Desktop Sender GUI
python -m sender.main

# Launch Desktop Receiver GUI
python -m receiver.main
```

---

## ☁️ Cloud Deployment

PhotonDrop is configured for zero-friction cloud deployment:

### 1. Deploy Backend to Render

1. Create a new **Web Service** on [Render](https://render.com).
2. Connect your GitHub repository.
3. Render automatically reads [`render.yaml`](render.yaml):
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT`

### 2. Deploy Frontend to Vercel

1. Import the repository into [Vercel](https://vercel.com).
2. Set **Root Directory** to `frontend`.
3. Add Environment Variables:
   - `VITE_API_BASE_URL` = `https://photondrop-backend.onrender.com`
   - `VITE_WS_BASE_URL` = `wss://photondrop-backend.onrender.com`
4. Click **Deploy**. Vercel uses [`frontend/vercel.json`](frontend/vercel.json) for automatic SPA rewrites.

---

## 🧪 Test Suite

Run the full automated pytest suite:

```bash
python -m pytest tests/ -v
```

```text
============================= 54 passed in 0.36s ==============================
```

- **Protocol Tests** (`test_protocol.py`): Header serialization, magic bytes, CRC32 integrity.
- **Fountain Tests** (`test_fountain.py`): Soliton distribution, symbol generation, XOR identity, graph peeling decoder.
- **Loss Tests** (`test_packet_loss.py`): Recovery under 5%, 10%, 20%, 30%, and 50% packet drop.
- **Integrity Tests** (`test_integrity.py`): Single-bit flips, header corruption, SHA-256 verification.
- **End-to-End Tests** (`test_end_to_end.py`): Full pipeline (file $\rightarrow$ fountain $\rightarrow$ loss $\rightarrow$ decode $\rightarrow$ SHA-256 match).

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
