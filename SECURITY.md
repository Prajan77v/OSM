# 🛡️ Security & Privacy Protocols

This document outlines the security policies, privacy models, and vulnerability reporting procedures for the Object Monitoring System (OMS).

---

## 🔒 Privacy & Local-first Protocol
OMS operates as a **local-first, privacy-respecting** surveillance system. To safeguard physical identities and private telemetry:
1. **Local Face Embeddings**: All biometric vectors (128-dimensional face representations calculated by SFace) are processed locally on the deployment host. No biometric details are ever transmitted to external cloud systems or third-party servers.
2. **Local Frame Buffers**: Live camera feeds (OpenCV video loops) are rendered locally. The Next.js dashboard fetches frames directly from the local host (`localhost:8000`) over private local networking loops.
3. **Complete Git Ignore Rules**: The `faces/` directory (which stores enrolled template photos and captured alarm evidence) and the database file (`logs/`) are completely excluded from git tracking in `.gitignore`. They will never be committed to public GitHub repositories.

---

## 📨 Reporting a Vulnerability
If you discover a security vulnerability (such as API authorization issues, camera feed leaks, or input validation escapes), please **do not open a public GitHub issue**. Instead, follow these steps:
1. Send an email to the lead developer outlining the details of the vulnerability.
2. Include reproduction steps, sample payload requests, or setup configurations.
3. Allow up to 72 hours for our core team to review and provide a patch/resolution.

---

## 🛠️ Secure Deployment Guidelines
When deploying OMS Sentinel in production environments, we recommend applying the following network security layers:
* **Reverse Proxy Integration**: Bind the FastAPI backend behind a secure Nginx reverse proxy using TLS/SSL configurations (`https`).
* **VPC Isolation**: Keep camera RTSP streams inside a private Virtual Private Cloud (VPC) / Local Area Network (LAN) isolated from the public internet.
* **Telemetry Auth**: Restrict access to `/api/` routers by implementing firewalls or API gateway authorization keys.
