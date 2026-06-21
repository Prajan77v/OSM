# 🗺️ OMS Sentinel — Future Engineering Roadmap

This document outlines the strategic milestones and technical specifications for the evolution of the Object Monitoring System (OMS).

---

## 🚀 Strategic Overview
The roadmap focuses on scaling the system from a localized single-node computer vision gateway into a highly available, cloud-native, edge-accelerated surveillance mesh capable of processing hundreds of camera feeds with millisecond latency.

```
[Current State: v9.0] ──> [Phase 1: Advanced Edge AI] ──> [Phase 2: Decentralized Mesh] ──> [Phase 3: Cloud Sentinel Orchestrator]
```

---

## 📅 Timeline & Milestones

### Phase 1: Gaze, Attention & Pose Mesh (Q3 2026)
* **Goal**: Transition from simple bounding box proxies to fine-grained human state estimation.
* **Technical Deliverables**:
  - Integrate **MediaPipe Face Mesh** for sub-pixel eye-gaze and iris-tracking (estimating high/medium/low attention based on active ocular fixation vectors).
  - Deploy **YOLOv8-pose** to capture human skeletons, enabling fall detection, physical distress signs, and advanced gesture triggers.
  - Implement head-pose angles (yaw, pitch, roll) using YuNet landmark alignments to lock attention states.

### Phase 2: Hardware Acceleration & Local Compilation (Q4 2026)
* **Goal**: Reduce inference latency by 75% on low-power consumer devices.
* **Technical Deliverables**:
  - Add **NVIDIA TensorRT** execution providers for all YOLO and SFace models, compiling weights dynamically to FP16 engines.
  - Integrate **Intel OpenVINO** fallback engines to accelerate CPU execution by up to 4x on Intel NUC configurations.
  - Support Raspberry Pi 5 / Jetson Nano 4GB edge configurations with quantized Int8 models.

### Phase 3: Multi-node Decentralized Video Mesh (Q1 2027)
* **Goal**: Orchestrate and merge telemetry streams across separate physical monitoring nodes.
* **Technical Deliverables**:
  - Develop the **OMS Edge Agent** — a headless python service that processes local camera inputs and posts metadata payloads to a central server.
  - Deploy **gRPC communication channels** between edge nodes and the analytics dashboard, guaranteeing sub-10ms telemetry updates.
  - Create a federated Re-ID (Re-Identification) module to track the same subject ID (`P1`, `P2`) across multiple physical camera nodes.

### Phase 4: Cloud Sentinel SaaS Architecture (Q2 2027)
* **Goal**: Support global deployments with multi-tenant hosting, secure user accounts, and billing structures.
* **Technical Deliverables**:
  - Wrap backend services in **Docker containers** orchestrated by lightweight Kubernetes (K3s).
  - Transition local storage from SQLite to a hybrid **PostgreSQL (for telemetry)** + **MongoDB (for event lists)** cluster.
  - Deploy secure JWT-based role-based access control (RBAC) separating Operators, Security Admins, and Site Managers.

---

## 📈 Long-term Research & Development
* **Zero-shot Anomaly Prompts**: Integrating lightweight Visual-Language Models (VLMs) like Moondream or PaliGemma to allow operators to type alerts in plain English (e.g. *"alert if anyone holds a box"*).
* **Thermal Image Support**: Porting YOLO weights to infrared / thermal camera bands to enable advanced night security.
* **Predictive Behavior Modelling**: Running sequential LSTM / Transformer models over tracked coordinate paths to predict potential security entries before they happen.
