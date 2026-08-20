# OMS Sentinel — Camera Configuration & RTSP Guide

## Supported Camera Protocols
- **RTSP Streams** (H.264 / H.265 via TCP)
- **USB Webcams / Integrated Cameras** (Device index `0`, `1`, etc.)
- **IP Cameras & HTTP MJPEG Streams**
- **Offline Video Files for Testing** (`.mp4`, `.mkv`, `.avi`)

---

## 1. RTSP Stream URL Formats

### Hikvision NVR / IP Cameras:
```text
rtsp://<username>:<password>@<ip_address>:554/Streaming/Channels/<channel_number>01
```
*Note: Channel `101` = Main Stream (High Res), `102` = Sub Stream (Standard Res).*

**Special Characters in Password:**
If your password contains special characters (such as `@`, `#`, `$`), URL-encode them:
- `@` ➔ `%40`
- `#` ➔ `%23`
- `$` ➔ `%24`

*Example:* `admin:eltec@123` ➔ `rtsp://admin:eltec%40123@192.168.1.200:554/Streaming/Channels/101`

### Dahua / Lorex NVRs:
```text
rtsp://<username>:<password>@<ip_address>:554/cam/realmonitor?channel=<ch>&subtype=0
```

### Uniview / Tiandy / Axis:
```text
rtsp://<username>:<password>@<ip_address>:554/media/video1
```

---

## 2. Troubleshooting Camera Disconnections

1. **Test Port 554 Reachability:**
   ```bash
   python -c "import socket; s = socket.create_connection(('117.247.103.114', 554), timeout=3); print('PORT 554 OPEN')"
   ```
2. **Sub-Stream Recommendation for CPU Edge:**
   For low-power CPUs, configuring cameras to use the sub-stream (`102` or `subtype=1` e.g. 720p/1080p) reduces CPU decoding load while maintaining 99%+ AI tracking accuracy.
