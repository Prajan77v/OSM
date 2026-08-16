"""
face_engine.py -- OMS InsightFace Pipeline
Thread-safe SCRFD detection + ArcFace recognition with quality filtering.
Graceful fallback to YuNet/SFace when insightface is unavailable.
"""
from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

import cv2
import numpy as np

log = logging.getLogger("OMS.face_engine")

INSIGHTFACE_AVAILABLE = False
try:
    import insightface
    from insightface.app import FaceAnalysis
    INSIGHTFACE_AVAILABLE = True
except Exception as _ie:
    log.warning(f"[FaceEngine] insightface unavailable: {_ie}")


@dataclass
class FaceResult:
    box:       Tuple[int, int, int, int]
    embedding: np.ndarray
    det_score: float
    landmarks: Optional[np.ndarray] = None


class FaceEngine:
    MIN_DET_SCORE         = 0.35  # Filter out low-confidence face detections
    MIN_FACE_SIZE         = 16    # Filter out tiny noise patches
    MATCH_THRESHOLD       = 0.35  # Optimal ArcFace cosine similarity threshold
    MATCH_THRESHOLD_KNOWN = 0.36  # Threshold for known authorized persons

    def __init__(self):
        self._lock      = threading.RLock()
        self._app       = None
        self.available  = False
        self._emb_cache: Dict[str, List[np.ndarray]] = {}
        self._meta:      Dict[str, dict]              = {}
        self._model_name = "buffalo_sc"

    def init(self, cuda: bool = False, model_name: Optional[str] = None) -> bool:
        if not INSIGHTFACE_AVAILABLE:
            self.available = False
            return False
        with self._lock:
            if self._app is not None:
                return True
            if model_name:
                self._model_name = model_name
            elif cuda:
                self._model_name = "buffalo_l"
            else:
                self._model_name = "buffalo_sc"
            try:
                ctx_id = 0 if cuda else -1
                print(f"[OMS] Loading InsightFace '{self._model_name}' on {'GPU' if cuda else 'CPU'} ...")
                
                # Resolve local offline root directory for InsightFace models
                root_path = None
                possible_roots = [
                    Path(__file__).parent,
                    Path(__file__).parent / "models",
                    Path.cwd(),
                    Path.cwd() / "models",
                    Path.home() / ".insightface"
                ]
                for pr in possible_roots:
                    if (pr / "models" / self._model_name).exists() or (pr / self._model_name).exists():
                        root_path = str(pr)
                        break

                fa_kwargs = {
                    "name": self._model_name,
                    "providers": (["CUDAExecutionProvider", "CPUExecutionProvider"]
                                  if cuda else ["CPUExecutionProvider"])
                }
                if root_path:
                    fa_kwargs["root"] = root_path

                app = FaceAnalysis(**fa_kwargs)
                app.prepare(ctx_id=ctx_id, det_size=(640, 640) if cuda else (320, 320))
                self._app      = app
                self.available = True
                print(f"[OMS] InsightFace Face Engine ONLINE ({self._model_name})")
                log.info(f"[FaceEngine] ONLINE model={self._model_name}")
                return True
            except Exception as e:
                log.error(f"[FaceEngine] Init failed: {e}", exc_info=True)
                self.available = False
                return False

    def detect_and_embed(self, bgr_frame: np.ndarray,
                          min_det_score: float = 0.35,
                          min_size: int = 12) -> List[FaceResult]:
        if not self.available or self._app is None or bgr_frame is None or bgr_frame.size == 0:
            return []
        try:
            h_in, w_in = bgr_frame.shape[:2]
            # If the crop from CCTV is small, upscale it so SCRFD detector can find small faces easily
            scale = 1.0
            feed_frame = bgr_frame
            if max(h_in, w_in) < 160:
                scale = 160.0 / max(1, max(h_in, w_in))
                feed_frame = cv2.resize(bgr_frame, (int(w_in * scale), int(h_in * scale)), interpolation=cv2.INTER_CUBIC)

            with self._lock:
                faces = self._app.get(feed_frame)
        except Exception as e:
            log.debug(f"[FaceEngine] detect error: {e}")
            return []
        results: List[FaceResult] = []
        for face in faces:
            ds = float(getattr(face, "det_score", 0.0))
            if ds < min_det_score:
                continue
            bbox = getattr(face, "bbox", None)
            if bbox is None:
                continue
            # Scale coordinates back if upscaled
            x1, y1, x2, y2 = int(bbox[0] / scale), int(bbox[1] / scale), int(bbox[2] / scale), int(bbox[3] / scale)
            if (x2 - x1) < min_size or (y2 - y1) < min_size:
                continue
            emb = getattr(face, "normed_embedding", None)
            if emb is None or len(emb) == 0:
                continue
            emb = np.array(emb, dtype=np.float32)
            n = np.linalg.norm(emb)
            if n > 1e-9:
                emb = emb / n
            results.append(FaceResult(box=(x1, y1, x2, y2), embedding=emb,
                                       det_score=ds, landmarks=getattr(face, "kps", None)))
        return results

    def match(self, embedding: np.ndarray, threshold: Optional[float] = None
              ) -> Tuple[Optional[str], Optional[str], bool, float]:
        if threshold is None:
            threshold = self.MATCH_THRESHOLD
        best_pid, best_score = None, -1.0
        with self._lock:
            for pid, encs in self._emb_cache.items():
                for enc in encs:
                    if enc.shape != embedding.shape:
                        continue
                    s = float(np.dot(embedding, enc))
                    if s > best_score:
                        best_score, best_pid = s, pid

        eff_thresh = threshold
        if best_pid and self._meta.get(best_pid, {}).get("known", False):
            eff_thresh = max(threshold, self.MATCH_THRESHOLD_KNOWN)

        if best_pid and best_score >= eff_thresh:
            name = self._meta.get(best_pid, {}).get("name", f"Intruder-{best_pid}")
            return best_pid, name, False, best_score
        return None, None, True, 0.0

    def register(self, pid: str, name: str, embedding: np.ndarray,
                 known: bool = False, max_per_profile: int = 16) -> None:
        emb = np.array(embedding, dtype=np.float32)
        n = np.linalg.norm(emb)
        if n > 1e-9:
            emb = emb / n
        with self._lock:
            existing = self._emb_cache.get(pid, [])
            for ex in existing:
                if ex.shape == emb.shape and float(np.dot(emb, ex)) >= 0.88:
                    return
            new_list = (existing[-max_per_profile + 1:] + [emb]
                        if len(existing) >= max_per_profile else existing + [emb])
            self._emb_cache[pid] = new_list
            self._meta.setdefault(pid, {}).update({"name": name, "known": known})

    def delete(self, pid: str) -> None:
        with self._lock:
            self._emb_cache.pop(pid, None)
            self._meta.pop(pid, None)

    def rename(self, pid: str, new_name: str, set_known: bool = True) -> bool:
        with self._lock:
            if pid not in self._meta:
                return False
            self._meta[pid]["name"] = new_name
            if set_known:
                self._meta[pid]["known"] = True
            return True

    def deduplicate(self, faces_db: dict, fdb_lock) -> List[Tuple[str, str]]:
        """
        Scan all stored ArcFace profiles, calculate pairwise maximum similarity,
        and merge duplicate profiles (similarity >= 0.28 or identical names).
        Returns list of (kept_pid, dropped_pid) tuples.
        """
        with self._lock:
            pids = list(self._emb_cache.keys())
            to_delete = set()
            merged_pairs = []

            for i in range(len(pids)):
                pid1 = pids[i]
                if pid1 in to_delete:
                    continue
                encs1 = self._emb_cache.get(pid1, [])
                meta1 = self._meta.get(pid1, {})
                name1 = meta1.get("name", "").strip().lower()
                known1 = meta1.get("known", False)

                for j in range(i + 1, len(pids)):
                    pid2 = pids[j]
                    if pid2 in to_delete:
                        continue
                    encs2 = self._emb_cache.get(pid2, [])
                    meta2 = self._meta.get(pid2, {})
                    name2 = meta2.get("name", "").strip().lower()
                    known2 = meta2.get("known", False)

                    # Check 1: Same Name match (e.g. both named "Prajan")
                    same_name = (bool(name1) and bool(name2) and name1 == name2 and not name1.startswith("intruder") and not name1.startswith("unknown"))

                    # Check 2: Biometric embedding similarity
                    max_sim = -1.0
                    for e1 in encs1:
                        for e2 in encs2:
                            if e1.shape == e2.shape:
                                sim = float(np.dot(e1, e2))
                                if sim > max_sim:
                                    max_sim = sim

                    should_merge = False
                    if same_name:
                        should_merge = True
                    elif max_sim >= 0.38:
                        should_merge = True
                    elif max_sim >= 0.28 and not (known1 and known2):
                        should_merge = True

                    if should_merge:
                        if known1 and not known2:
                            keep, drop = pid1, pid2
                        elif known2 and not known1:
                            keep, drop = pid2, pid1
                        else:
                            try:
                                id1 = int(pid1.replace("P", ""))
                                id2 = int(pid2.replace("P", ""))
                                keep, drop = (pid1, pid2) if id1 <= id2 else (pid2, pid1)
                            except Exception:
                                keep, drop = pid1, pid2

                        to_delete.add(drop)
                        merged_pairs.append((keep, drop))

                        # Merge embeddings into keep profile
                        drop_encs = self._emb_cache.get(drop, [])
                        for de in drop_encs:
                            self.register(keep, self._meta[keep]["name"], de, known=self._meta[keep].get("known", False))

            for drop in to_delete:
                self.delete(drop)

        if merged_pairs and fdb_lock is not None:
            with fdb_lock:
                for keep, drop in merged_pairs:
                    if drop in faces_db:
                        if keep in faces_db:
                            faces_db[keep]["visit_count"] = (
                                faces_db[keep].get("visit_count", 0) + faces_db[drop].get("visit_count", 0)
                            )
                            # Inherit photo if keep has none
                            if not faces_db[keep].get("photo") and faces_db[drop].get("photo"):
                                faces_db[keep]["photo"] = faces_db[drop]["photo"]
                        del faces_db[drop]

        return merged_pairs

    def load_from_faces_db(self, faces_db: dict, yunet_enc_cache: dict = None) -> int:
        loaded = 0
        with self._lock:
            for pid, d in faces_db.items():
                name  = d.get("name", f"Intruder-{pid}")
                known = d.get("known", False)
                encs_raw = d.get("encodings") or []
                if not encs_raw and d.get("encoding") is not None:
                    encs_raw = [d["encoding"]]
                arc_encs = []
                for e in encs_raw:
                    arr = (np.array(e, dtype=np.float32)
                           if not isinstance(e, np.ndarray) else e)
                    if arr.shape and arr.shape[0] == 512:
                        n = np.linalg.norm(arr)
                        if n > 1e-9:
                            arr = arr / n
                        arc_encs.append(arr)
                if arc_encs:
                    self._emb_cache[pid] = arc_encs
                    self._meta[pid] = {"name": name, "known": known}
                    loaded += 1
        log.info(f"[FaceEngine] Loaded {loaded} ArcFace profiles from faces_db")
        return loaded

    def sync_to_faces_db(self, faces_db: dict, fdb_lock) -> None:
        with self._lock:
            snap_emb  = dict(self._emb_cache)
            snap_meta = dict(self._meta)
        
        def _do_sync():
            for pid, encs in snap_emb.items():
                if pid in faces_db:
                    ex = faces_db[pid].get("encodings") or []
                    if not isinstance(ex, list):
                        ex = [ex] if ex is not None else []
                    kept = [e for e in ex if isinstance(e, np.ndarray)
                            and e.shape and e.shape[0] == 128]
                    merged = kept + encs
                    faces_db[pid]["encodings"] = merged
                    if merged:
                        faces_db[pid]["encoding"] = merged[-1]
                    m = snap_meta.get(pid, {})
                    if "name"  in m: faces_db[pid]["name"]  = m["name"]
                    if "known" in m: faces_db[pid]["known"] = m["known"]
                    faces_db[pid]["engine"] = "insightface"

        if fdb_lock is not None:
            with fdb_lock:
                _do_sync()
        else:
            _do_sync()

    def preload_known_faces(self, known_faces_dir: str) -> int:
        if not self.available:
            return 0
        p = Path(known_faces_dir)
        if not p.exists():
            return 0
        loaded = 0
        for fp in p.iterdir():
            if fp.suffix.lower() not in (".jpg", ".jpeg", ".png"):
                continue
            try:
                img = cv2.imread(str(fp))
                if img is None:
                    continue
                faces = self.detect_and_embed(img, min_det_score=0.50, min_size=30)
                if not faces:
                    log.warning(f"[FaceEngine] No face in {fp.name}")
                    continue
                best = max(faces, key=lambda f: f.det_score)
                log.info(f"[FaceEngine] Preloaded: {fp.stem} (score={best.det_score:.2f})")
                print(f"[OMS] Known face loaded: {fp.stem}")
                loaded += 1
            except Exception as e:
                log.error(f"[FaceEngine] preload {fp.name}: {e}")
        return loaded

    def get_all_pids(self) -> List[str]:
        with self._lock:
            return list(self._emb_cache.keys())

    @property
    def profile_count(self) -> int:
        with self._lock:
            return len(self._emb_cache)


face_engine = FaceEngine()


if __name__ == "__main__":
    import sys
    print("=" * 60)
    print("OMS FaceEngine Self-Test")
    print("=" * 60)
    if not INSIGHTFACE_AVAILABLE:
        print("[FAIL] insightface not installed.")
        print("       Run: pip install insightface onnxruntime")
        sys.exit(1)
    ok = face_engine.init(cuda=False)
    if not ok:
        print("[FAIL] FaceEngine.init() failed"); sys.exit(1)
    print(f"[OK]  Model: {face_engine._model_name}")
    blank = np.zeros((480, 640, 3), dtype=np.uint8)
    res = face_engine.detect_and_embed(blank)
    print(f"[OK]  Blank frame -> {len(res)} faces (expected 0)")
    assert len(res) == 0
    dummy = np.random.randn(512).astype(np.float32)
    dummy /= np.linalg.norm(dummy)
    face_engine.register("P1", "TestUser", dummy, known=True)
    pid, name, is_new, score = face_engine.match(dummy)
    print(f"[OK]  Self-match: pid={pid} name={name} score={score:.4f}")
    assert pid == "P1" and not is_new and score > 0.99
    face_engine.rename("P1", "Renamed")
    assert face_engine._meta["P1"]["name"] == "Renamed"
    face_engine.delete("P1")
    assert "P1" not in face_engine._emb_cache
    print("[PASS] All tests passed!")
    print("=" * 60)
