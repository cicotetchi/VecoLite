"""
Shared JWT authentication utilities for VecoLite.

Two FastAPI dependencies:
  - require_auth  → any authenticated user (admin or operator)
  - require_admin → admin role only
"""

import os
import bcrypt
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from fastapi import Header, HTTPException

# ── Config ────────────────────────────────────────────────────────────────────
JWT_SECRET    = os.environ.get("JWT_SECRET", "vecolite-jwt-secret-2024")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24


# ── Password utils ────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ── Token utils ───────────────────────────────────────────────────────────────

def create_token(username: str, role: str) -> str:
    payload = {
        "sub":  username,
        "role": role,
        "exp":  datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


# ── FastAPI dependencies ──────────────────────────────────────────────────────

def _extract_payload(authorization: Optional[str]) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Non autorisé — token manquant")
    raw_token = authorization.split(" ", 1)[1]
    try:
        return decode_token(raw_token)
    except JWTError:
        raise HTTPException(401, "Token invalide ou expiré")


def require_auth(authorization: Optional[str] = Header(None)) -> dict:
    """Dependency : any authenticated user (admin or operator)."""
    return _extract_payload(authorization)


def require_admin(authorization: Optional[str] = Header(None)) -> dict:
    """Dependency : admin role only."""
    payload = _extract_payload(authorization)
    if payload.get("role") != "admin":
        raise HTTPException(403, "Accès réservé aux administrateurs")
    return payload
