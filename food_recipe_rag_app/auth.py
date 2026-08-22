import hashlib
import hmac
import os
import secrets
import streamlit as st

def make_password_hash(password: str, iterations: int = 310_000) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"

def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, iterations, salt_hex, digest_hex = encoded.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations)
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False

def _get_secret(name, default=None):
    try:
        value = st.secrets.get(name)
        if value is not None:
            return value
    except Exception:
        pass
    return os.getenv(name, default)

def require_login() -> bool:
    if st.session_state.get("authenticated"):
        return True

    st.title("🔐 Recipe RAG Kitchen")
    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", type="primary")

    if submitted:
        expected_user = _get_secret("AUTH_USERNAME", "admin")
        password_hash = _get_secret("AUTH_PASSWORD_HASH", "")
        if password_hash and hmac.compare_digest(username, expected_user) and verify_password(password, password_hash):
            st.session_state.authenticated = True
            st.rerun()
        st.error("Invalid username or password.")

    return False
