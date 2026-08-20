# OMS Cloud Gateway — API Reference

## Base URLs
- **Production Cloud**: `https://oms-sentinel-cloud.onrender.com`
- **Local Edge Hub**: `http://localhost:8000`
- **Swagger Documentation**: `/docs`
- **ReDoc Interactive Docs**: `/redoc`

---

## 1. Edge Ingestion Endpoints

### `POST /api/edge/heartbeat`
Lightweight diagnostic health ping sent by Edge Agents every 10 seconds.
- **Headers**: `X-Edge-Token: <token>`
- **Request Body**:
```json
{
  "engine_id": "edge-node-1",
  "status": "ONLINE",
  "gpu": "CPU Mode",
  "cuda_available": false,
  "hardware_profile": "CPU",
  "cpu": 18.5,
  "ram": 42.0,
  "version": "9.0.0"
}
```

### `POST /api/events/batch`
Flushes batched surveillance events from the Edge's persistent SQLite queue.
- **Headers**: `X-Edge-Token: <token>`
- **Request Body**:
```json
{
  "engine_id": "edge-node-1",
  "events": [
    {
      "event_id": "evt_abc123",
      "camera_id": "Diamond Silicate",
      "event_type": "loitering",
      "severity": "medium",
      "confidence": 0.88,
      "location": "Diamond Silicate Facility",
      "track_ids": [4],
      "snapshot_base64": "<base64_jpg>",
      "metadata": { "detail": "Subject stationary for 28s" }
    }
  ]
}
```

---

## 2. Dashboard Query Endpoints

### `GET /api/events`
Returns historical events with optional pagination and severity filtering.
- **Query Params**:
  - `severity`: `info` | `low` | `medium` | `high` | `critical`
  - `event_type`: `person_detected` | `loitering` | `running` | `fall_detected` | `object_abandoned`
  - `limit`: `1..500` (default 50)
  - `offset`: integer

### `GET /api/cameras`
Returns list of all configured camera channels with real-time online status and FPS.

### `GET /api/telemetry`
Returns aggregated hardware statistics (CPU, RAM, GPU, Net bandwidth, FPS).

### `GET /api/system/health`
Returns system-wide health matrix (Cloud DB, Edge Nodes online, Camera counts).
