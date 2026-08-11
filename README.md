<div align="center">

# ⚡ PhotonDrop

### Zero-Network Optical File Transfer Through Screen-to-Camera Visible Light

[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Vite](https://img.shields.io/badge/Vite-6.2-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-4.2-38B2AC?style=for-the-badge&logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

<br />

> **PhotonDrop** is an air-gapped, zero-network optical file transfer system. It transmits arbitrary binary files from one device screen to another using visible light — **zero Wi-Fi, zero Bluetooth, zero cellular, zero Internet, and zero cables required.**

</div>

---

## 🌟 Key Features

- 🔒 **100% Air-Gapped & Offline**: Operates purely over physical light emitted by a display screen and captured by a camera lens.
- ⛲ **LT Fountain Coding**: Uses mathematically sound Luby Transform (LT) codes with a robust soliton degree distribution and systematic prefix for high-speed symbol streaming.
- 🛡️ **Loss-Tolerant Reconstruction**: Successfully recovers complete files even under high frame drop rates, out-of-order delivery, or flickering optical channels.
- 📦 **Arbitrary File Support**: Transmit any file format (PNG, PDF, ZIP, MP4, DOCX, binary files) seamlessly.
- ⚡ **High-Speed Browser Performance**: Client-side HTML5 canvas QR rendering (30–60 FPS) and zero-latency `jsQR` camera frame scanning.
- 🔍 **Cryptographic Integrity**: SHA-256 digest validation ensures byte-identical file reconstruction.
- 🌙 **Modern Dark / Light System**: Sleek Apple-inspired UI with real-time transfer progress, telemetry, and activity logs.

---

## 📐 Architecture & Data Flow

```text
 ┌─────────────────────────────────────────────────────────────────────────────────┐
 │                                SENDER SIDE                                      │
 │                                                                                 │
 │   File  ──►  Chunking & Manifest  ──►  LT Fountain Encoder ──► 24-Byte Header   │
 │              (SHA-256 Digest)           (Mulberry32 PRNG)         & Base64      │
 │                                                                       │         │
 │                                                                       ▼         │
 │  Display Screen  ◄──  HTML5 Canvas  ◄──  QRCode.toCanvas() ◄──────────┘         │
 └─────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                   VISIBLE LIGHT
                                  (Optical Channel)
                                         │
 ┌─────────────────────────────────────────────────────────────────────────────────┐
 │                               RECEIVER SIDE                                     │
 │                                                                                 │
 │   Camera Lens  ──►  Video Frame Scan  ──►  jsQR Optical Decoder                 │
 │                      (30 FPS WebCam)        (Base64 Frame Parsing)              │
 │                                                     │                           │
 │                                                     ▼                           │
 │   Download File  ◄──  SHA-256 Verification ◄──  Peeling Decoder ◄── Header Check  │
 │  (Blob Object URL)   (Byte-Identical)        (Belief Propagation)  (FileId/Seed)│
 └─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Node.js** $\ge$ 18.0.0
- **npm** $\ge$ 9.0.0

### Installation & Development

```bash
# Clone repository
git clone https://github.com/AyushPrakash414/PhotonDrop.git
cd PhotonDrop

# Install dependencies
npm install

# Start development server
npm run dev
```

Open `http://localhost:3000` in your browser.

---

## 📦 Build & Deployment

### Production Build

```bash
npm run build
```

This compiles the client application to the `dist/` directory using Vite.

### Preview Production Build

```bash
npm run preview
```

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
