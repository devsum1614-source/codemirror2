"""
Authentication & Session Management Module for CodeMirror 2.0
Implements:
- Cryptographically secure password hashing (PBKDF2-HMAC-SHA256 with 16-byte salt)
- Server-side session store in SQLite with expiration
- HTTP-only session cookies and Authorization: Bearer <token> support
- Role-Based Access Control (RBAC) dependencies for FastAPI
- Strict role boundaries (Students cannot escalate privileges or register as admin)
"""

import hashlib
import secrets
import datetime
from typing import Optional, Dict, Any, List
from fastapi import Request, HTTPException, Depends

from app.database import get_db

SESSION_EXPIRY_DAYS = 7


def hash_password(password: str) -> str:
    """Hashes a password with a unique 16-byte hex salt and 100,000 PBKDF2-HMAC-SHA256 iterations."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"{salt}${key.hex()}"


def verify_password(password: str, hashed: Optional[str]) -> bool:
    """Verifies a password against a salt$hash string."""
    if not hashed or "$" not in hashed:
        return False
    try:
        salt, hex_key = hashed.split("$", 1)
        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
        return secrets.compare_digest(key.hex(), hex_key)
    except Exception:
        return False


def create_session(account_id: str, role: str) -> str:
    """Creates a new secure session token stored in SQLite."""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=SESSION_EXPIRY_DAYS)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sessions (token, account_id, role, expires_at)
        VALUES (?, ?, ?, ?)
    """, (token, account_id, role, expires_at.isoformat()))
    conn.commit()
    conn.close()
    return token


def get_session_account(token: str) -> Optional[Dict[str, Any]]:
    """Resolves an account from an active session token."""
    if not token:
        return None
    
    conn = get_db()
    cursor = conn.cursor()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    cursor.execute("""
        SELECT s.token, s.account_id, s.role, s.expires_at,
               a.id, a.display_name, a.email, a.role as account_role, a.class_id
        FROM sessions s
        JOIN accounts a ON s.account_id = a.id
        WHERE s.token = ? AND s.expires_at > ?
    """, (token, now_iso))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
        
    return {
        "id": row["id"],
        "display_name": row["display_name"],
        "email": row["email"],
        "role": row["account_role"],
        "class_id": row["class_id"],
        "session_token": row["token"]
    }


def delete_session(token: str) -> None:
    """Invalidates and deletes a session."""
    if not token:
        return
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()


def extract_token_from_request(request: Request) -> Optional[str]:
    """Extracts session token from Authorization header, Cookie, or X-Session-Token header."""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if token:
            return token

    cookie_token = request.cookies.get("cm_session")
    if cookie_token:
        return cookie_token.strip()

    custom_header = request.headers.get("X-Session-Token")
    if custom_header:
        return custom_header.strip()

    return None


def get_optional_account(request: Request) -> Optional[Dict[str, Any]]:
    """Dependency that returns the account if authenticated, or None if guest."""
    token = extract_token_from_request(request)
    if not token:
        return None
    return get_session_account(token)


def get_current_account(request: Request) -> Dict[str, Any]:
    """Dependency that strictly requires an authenticated session."""
    account = get_optional_account(request)
    if not account:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please sign in to continue."
        )
    return account


def require_role(allowed_roles: List[str]):
    """Dependency factory enforcing role membership."""
    def role_dependency(account: Dict[str, Any] = Depends(get_current_account)):
        if account["role"] not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Requires one of roles: {', '.join(allowed_roles)} (current role: '{account['role']}')"
            )
        return account
    return role_dependency
