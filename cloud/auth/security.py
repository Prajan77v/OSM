"""
OMS Cloud — Authentication, Tokens, and Secret Masking
"""

import os
import hashlib
import re
from typing import Optional
from fastapi import Header, HTTPException, status

OMS_API_KEY = os.getenv("OMS_API_KEY", "").strip()
EDGE_TOKEN = os.getenv("OMS_EDGE_TOKEN", "").strip()


def mask_rtsp_url(url: str) -> str:
    """
    Masks credentials in RTSP URLs to prevent secret exposure.
    Example: rtsp://admin:pass@192.168.1.200:554/ch1 -> rtsp://admin:***@192.168.1.200:554/ch1
    """
    if not url or not isinstance(url, str):
        return str(url)
    return re.sub(r"://([^:]+):([^@]+)@", r"://\1:***@", url)


def verify_edge_token(x_edge_token: Optional[str] = Header(None)) -> bool:
    """
    Validates Edge Node token. If OMS_EDGE_TOKEN is configured,
    requests missing or mismatched tokens are rejected with 401.
    """
    if not EDGE_TOKEN:
        return True
    if not x_edge_token or x_edge_token != EDGE_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid Edge Agent Token (X-Edge-Token)"
        )
    return True


def verify_dashboard_api_key(x_api_key: Optional[str] = Header(None)) -> bool:
    """
    Validates API key for dashboard control requests.
    """
    if not OMS_API_KEY:
        return True
    if not x_api_key or x_api_key != OMS_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid API Key (X-API-Key)"
        )
    return True
