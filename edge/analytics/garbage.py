"""
OMS Edge — Abandoned Object & Garbage Dumping Analytics
Monitors object-to-person proximity and flags unmaintained stationary items.
"""

from __future__ import annotations
import math
import time
from typing import Dict, List, Tuple, Any, Optional


class ObjectOwnershipAnalytics:
    """
    Detects abandoned bags, luggage, and garbage dumping.
    Tracks distance between stationary objects and candidate human owners.
    """

    def __init__(self, abandonment_secs: float = 12.0, proximity_pixel_dist: float = 180.0):
        self.abandonment_secs = abandonment_secs
        self.proximity_pixel_dist = proximity_pixel_dist
        self.tracked_objects: Dict[int, Dict[str, Any]] = {}

    def update(
        self,
        objects_list: List[Dict[str, Any]],
        persons_list: List[Dict[str, Any]],
        now: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Correlates object centroids with person centroids.
        Returns list of newly triggered abandonment / dumping incidents.
        """
        t = now or time.time()
        anomalies: List[Dict[str, Any]] = []

        person_centers = []
        for p in persons_list:
            bx = p.get("box", [0, 0, 0, 0])
            cx = (bx[0] + bx[2]) / 2.0
            cy = (bx[1] + bx[3]) / 2.0
            person_centers.append((cx, cy))

        current_obj_ids = set()

        for obj in objects_list:
            oid = obj.get("track_id")
            if oid is None:
                continue

            current_obj_ids.add(oid)
            bx = obj.get("box", [0, 0, 0, 0])
            ocx = (bx[0] + bx[2]) / 2.0
            ocy = (bx[1] + bx[3]) / 2.0

            # Find distance to closest person
            min_dist = float("inf")
            for pcx, pcy in person_centers:
                dist = math.hypot(ocx - pcx, ocy - pcy)
                if dist < min_dist:
                    min_dist = dist

            has_owner_nearby = min_dist <= self.proximity_pixel_dist

            if oid not in self.tracked_objects:
                self.tracked_objects[oid] = {
                    "first_seen": t,
                    "last_near_owner": t if has_owner_nearby else 0.0,
                    "alerted": False,
                    "label": obj.get("label", "object")
                }

            record = self.tracked_objects[oid]
            if has_owner_nearby:
                record["last_near_owner"] = t
            else:
                # Object is isolated from all humans
                time_alone = t - (record["last_near_owner"] or record["first_seen"])
                if time_alone >= self.abandonment_secs and not record["alerted"]:
                    record["alerted"] = True
                    label = record["label"]
                    event_type = "garbage_dump" if label in ("bottle", "trash", "cup") else "object_abandoned"
                    anomalies.append({
                        "event_type": event_type,
                        "severity": "medium",
                        "confidence": 0.82,
                        "track_id": oid,
                        "box": bx,
                        "detail": f"Unattended {label} for {int(time_alone)}s"
                    })

        # Purge objects no longer visible
        expired = [k for k in self.tracked_objects if k not in current_obj_ids]
        for k in expired:
            del self.tracked_objects[k]

        return anomalies
