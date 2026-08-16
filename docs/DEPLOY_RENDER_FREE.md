# OMS Free Cloud Deployment Guide (Render Free + RTX 4060)

Complete step-by-step guide to deploying the **Object Monitoring System (OMS)** on **Render Free Tier ($0/mo)** while running all heavy AI models locally on your **NVIDIA GeForce RTX 4060**.

---

## 1. Architecture Overview

- **Frontend**: Render Static Site (Global CDN) built from `frontend/`
- **Backend Cloud API**: Render Free Web Service running `cloud_api:app` (512MB RAM / 0.1 CPU, zero GPU required)
- **Local AI Engine**: Runs locally on Windows with CUDA (`python main.py` or `start_oms_ai.bat`) and pushes telemetry to the Cloud API.

---

## 2. Step 1: Push Repository to GitHub

Ensure all new files and decoupled configurations are committed and pushed:

```bash
git add .
git commit -m "feat(deploy): decouple cloud API and local AI engine for Render Free deployment"
git push origin main
```

---

## 3. Step 2: Deploy OMS Cloud API on Render (Free Web Service)

1. Log into your [Render Dashboard](https://dashboard.render.com).
2. Click **New +** $\rightarrow$ **Web Service**.
3. Connect your GitHub repository: `Prajan77v/OSM` (or select from your repo list).
4. Fill in the exact settings below:

| Field | Value |
| :--- | :--- |
| **Name** | `osm-cloud-api` *(or your preferred name)* |
| **Region** | Singapore / Frankfurt / Oregon *(closest to you)* |
| **Branch** | `main` |
| **Root Directory** | *(Leave empty)* |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements-cloud.txt` |
| **Start Command** | `uvicorn cloud_api:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | **Free (512 MB RAM, 0.1 CPU)** |

5. Under **Environment Variables**, add:

| Key | Value | Description |
| :--- | :--- | :--- |
| `OSM_OPERATOR` | `Prajan` | Operator Name |
| `OMS_API_KEY` | *(Generate a random secret key, e.g. `oms_sec_77v`)* | Authenticates local engine sync requests |
| `PYTHON_VERSION` | `3.11.9` | Matches `.python-version` |

6. Click **Create Web Service**.
7. Once deployed, copy your Render URL:
   `https://osm-cloud-api.onrender.com`

---

## 4. Step 3: Deploy OMS Dashboard on Render (Static Site)

1. In Render Dashboard, click **New +** $\rightarrow$ **Static Site**.
2. Select your repository `Prajan77v/OSM`.
3. Configure the exact static build settings:

| Field | Value |
| :--- | :--- |
| **Name** | `osm-dashboard` |
| **Branch** | `main` |
| **Root Directory** | `frontend` |
| **Build Command** | `npm install && npm run build` |
| **Publish Directory** | `out` |

4. Under **Environment Variables**, add:

| Key | Value |
| :--- | :--- |
| `NEXT_PUBLIC_OMS_API_URL` | `https://osm-cloud-api.onrender.com` *(your Cloud API URL from Step 2)* |

5. Click **Create Static Site**.
6. Render will build the Next.js site and provide your live dashboard URL (e.g. `https://osm-dashboard.onrender.com`).

---

## 5. Step 4: Configure Local RTX 4060 AI Engine

On your local Windows machine:

1. Open `.env` in the root of `OMS_Sentinel` (or copy from `.env.example`):
   ```env
   OMS_CLOUD_API_URL=https://osm-cloud-api.onrender.com
   OMS_API_KEY=oms_sec_77v
   OSM_OPERATOR=Prajan
   PORT=8000
   ```
2. Start the AI Engine:
   ```powershell
   .\start_oms_ai.bat
   ```
   *(or run `python main.py`)*

3. Verify the terminal output displays:
   ```text
   [✦] Hardware Profile:  MEDIUM
   [✦] CUDA Acceleration: ENABLED (NVIDIA GeForce RTX 4060)
   [✦] YOLO Engine:       ✔ ONLINE (ultralytics)
   [✦] Face Recognition:  ✔ ONLINE (buffalo_sc)
   [CLOUD SYNC] Initialized target: https://osm-cloud-api.onrender.com
   [CLOUD SYNC] Render Cloud API ONLINE. Sync active.
   ```

---

## 6. Step 5: Optional Cloudflare Tunnel Setup (For Remote Control)

If you wish to control your local CCTV cameras remotely through the cloud without port forwarding:

1. Download [`cloudflared.exe`](https://github.com/cloudflare/cloudflared/releases) on Windows.
2. In PowerShell, create a tunnel:
   ```powershell
   cloudflared tunnel --url http://localhost:8000
   ```
3. Cloudflare will generate a secure `https://<random-subdomain>.trycloudflare.com` URL that maps to your local machine.

---

## 7. Operational Modes

### 🌐 Cloud Mode (Anywhere in the World)
- Open your Render Dashboard URL: `https://osm-dashboard.onrender.com`.
- Telemetry, active detections, threat levels, and events stream directly from your RTX 4060 through the Cloud API.

### 🏠 Local Offline Mode
- Run `python main.py` or `start_oms_ai.bat`.
- Open `http://localhost:8000`.
- Operates 100% locally with zero internet dependency.

---

## 8. Troubleshooting

### Render Free Cold Starts (Spin-down)
- Render Free puts web services to sleep after 15 minutes of inactivity.
- **How OMS handles this**: Your local AI engine automatically buffers events locally and retries with exponential backoff. As soon as you open the dashboard or the Cloud API wakes up, all buffered events flush automatically in one batch.
