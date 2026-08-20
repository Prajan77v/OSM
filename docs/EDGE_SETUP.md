# OMS Edge Agent — Deployment & Installation Guide

## System Requirements
- **OS**: Windows 10/11, Ubuntu 20.04+, Debian 11+, or macOS
- **CPU**: Dual-Core 2.0 GHz or higher (Intel Core i3/i5/i7, AMD Ryzen, ARM64)
- **RAM**: Minimum 4 GB (8 GB recommended)
- **GPU**: Optional (CUDA 11.8/12.X supported automatically if available)
- **Python**: Python 3.10, 3.11, or 3.12

---

## 1. Quick Start Installation

```bash
# 1. Clone repository
git clone https://github.com/Prajan77v/OSM.git
cd OSM

# 2. Create Python virtual environment
python -m venv venv

# Windows activate:
venv\Scripts\activate

# Linux/macOS activate:
source venv/bin/activate

# 3. Install Edge dependencies
pip install -r requirements-edge.txt
```

---

## 2. Configuration (`config.yaml` & `.env`)

### Camera Feeds (`config.yaml`):
```yaml
operator:
  username: Prajan

cameras:
  - id: 0
    source: 0
    name: LOCAL WEBCAM
    location: Control Desk
    enabled: true

  - id: 1
    source: rtsp://admin:a1b2c3d4%405@117.247.103.113:554/Streaming/Channels/101
    name: Diamond Silicate
    location: Diamond Silicate Facility
    enabled: true

  - id: 2
    source: rtsp://admin:a1b2c3d4%405@117.247.103.114:554/Streaming/Channels/101
    name: Narimanam Silicate
    location: Narimanam Silicate Facility
    enabled: true
```

### Cloud Endpoint (`.env`):
```env
OMS_CLOUD_API_URL=https://oms-sentinel-cloud.onrender.com
OMS_EDGE_TOKEN=your_secure_edge_token_here
OMS_OPERATOR=Prajan
```

---

## 3. Running the Edge Agent

```bash
# Run modular Edge orchestrator
python edge/agent.py

# Or 1-click on Windows:
start_oms_ai.bat
```

---

## 4. 24/7 Production Service (Auto-Start on Boot)

### Linux (Systemd):
```bash
sudo cp deployment/systemd/oms-edge.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable oms-edge
sudo systemctl start oms-edge
```
