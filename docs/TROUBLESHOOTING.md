# OMS Sentinel — Production Troubleshooting & Diagnostics

## 1. Camera Disconnections / Offline Status

### Symptom: Dashboard shows "CAMERA OFFLINE"
- **Cause 1: Local Edge Agent is not running**
  - **Fix**: The cloud control plane reports cameras offline if the on-site Edge Agent is stopped. Run `python edge/agent.py` or `start_oms_ai.bat` on the Edge PC.
- **Cause 2: RTSP Port 554 Timeout**
  - **Fix**: Check if the camera IP is reachable from the Edge PC:
    ```bash
    python -c "import socket; s = socket.create_connection(('117.247.103.114', 554), timeout=3); print('PORT 554 OK')"
    ```
- **Cause 3: Special Characters in RTSP Password**
  - **Fix**: URL-encode characters like `@` (`%40`), `#` (`%23`), `$` (`%24`) in `config.yaml`.

---

## 2. High CPU Usage / Frame Lag

### Symptom: Edge CPU usage exceeds 90%
- **Automatic Protection**: The `AdaptiveController` will automatically downscale detection resolution and increase frame skipping.
- **Manual Optimizations**:
  1. Switch cameras to their Sub-Stream channel (`102` instead of `101` in RTSP URL).
  2. Set `process_every_n: 4` in `config.yaml` under `detection`.
  3. Ensure `det_w: 480` and `det_h: 288` in `config.yaml`.

---

## 3. Render Free Tier Spin-Down (Cold Start)

### Symptom: API takes 30-40 seconds to respond on first load
- **Cause**: Render Free tier Web Services spin down after 15 minutes of inactivity.
- **Fix**: Once the Edge Agent is running, it pings the Cloud API every 10 seconds, which **prevents Render from spinning down** and keeps it hot 24/7!

---

## 4. Viewing System Logs

- **Edge Agent Log**: `logs/oms-edge.log`
- **Cloud SQLite Database**: `logs/oms_cloud.db`
- **Local Event Queue DB**: `logs/oms_event_queue.db`
