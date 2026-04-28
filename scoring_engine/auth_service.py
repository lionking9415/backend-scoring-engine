"""
Authentication Service Module
Handles user registration, login, and session management with Supabase backend.
"""

import logging
import hashlib
import re
import secrets
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class DuplicateEmailError(Exception):
    """Raised when a signup attempt collides with an existing account.

    Distinct from generic creation failures so the API layer can return
    a precise 409 instead of an ambiguous 400.
    """


# RFC-pragmatic email check — good enough to reject obvious garbage at the
# service boundary; the real source of truth is the DB UNIQUE constraint.
_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def normalize_email(email: Optional[str]) -> Optional[str]:
    """Trim surrounding whitespace and lowercase the email.

    Returns None if the input is None/empty after stripping. We treat
    `Foo@Bar.com`, ` foo@bar.com `, and `foo@bar.com` as the same account
    so users can't accidentally double-register or fail to log in because
    of casing/whitespace differences.
    """
    if email is None:
        return None
    cleaned = email.strip().lower()
    return cleaned or None


def is_valid_email(email: Optional[str]) -> bool:
    """Lightweight syntactic validation. Run AFTER normalize_email()."""
    if not email:
        return False
    return bool(_EMAIL_RE.match(email))


def hash_password(password: str) -> str:
    """
    Hash a password using SHA-256 with salt.
    Note: In production, use bcrypt or argon2. This is simplified for now.
    """
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}${pwd_hash}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    try:
        salt, pwd_hash = password_hash.split('$')
        test_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return test_hash == pwd_hash
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def create_session_token() -> str:
    """Generate a secure session token."""
    return secrets.token_urlsafe(32)


def create_user(email: str, password: str, name: str = None, demographics: dict = None) -> Optional[dict]:
    """Create a new user account.

    Args:
        email: User's email address (will be normalized to lower-case + trimmed)
        password: Plain text password (will be hashed)
        name: User's display name
        demographics: Optional demographic information

    Returns:
        User object on success.

    Raises:
        DuplicateEmailError: if an account with this email already exists.
        Other exceptions are logged and converted to None for backwards-compat
        with callers expecting None on generic failure.
    """
    normalized = normalize_email(email)
    if not normalized or not is_valid_email(normalized):
        logger.warning("create_user called with invalid email: %r", email)
        return None

    try:
        from scoring_engine.supabase_client import get_supabase_client

        supabase = get_supabase_client()
        if not supabase:
            logger.error("Supabase not available")
            return None

        # Pre-check: case-insensitive lookup so `Foo@Bar.com` and
        # `foo@bar.com` map to the same account. The DB UNIQUE constraint
        # is still the final authority — see the insert handler below for
        # the race-window safety net.
        existing = (
            supabase.table('users')
            .select('email')
            .ilike('email', normalized)
            .execute()
        )
        if existing.data:
            logger.warning("User already exists: %s", normalized)
            raise DuplicateEmailError(normalized)

        password_hash = hash_password(password)

        user_data = {
            'email': normalized,
            'password_hash': password_hash,
            'name': name or normalized.split('@')[0],
            'demographics': demographics or {},
            'created_at': datetime.now(timezone.utc).isoformat(),
        }

        try:
            result = supabase.table('users').insert(user_data).execute()
        except Exception as insert_err:
            # Race-window safety net: between the pre-check above and this
            # insert, another request may have created the same email. The
            # DB UNIQUE constraint catches it; surface as DuplicateEmailError.
            err_text = str(insert_err).lower()
            if (
                'duplicate' in err_text
                or 'unique' in err_text
                or '23505' in err_text  # Postgres unique_violation
            ):
                logger.warning("Duplicate-email race lost on insert: %s", normalized)
                raise DuplicateEmailError(normalized) from insert_err
            raise

        if result.data:
            user = result.data[0]
            logger.info("User created successfully: %s", normalized)
            return {
                'id': user['id'],
                'email': user['email'],
                'name': user['name'],
                'demographics': user['demographics'],
            }

        return None

    except DuplicateEmailError:
        raise
    except Exception as e:
        logger.error("Error creating user: %s", e, exc_info=True)
        return None


def authenticate_user(email: str, password: str) -> Optional[dict]:
    """Authenticate a user with email and password.

    Email is normalized (lower-case, trimmed) and matched case-insensitively
    so users can log in even if they registered with mixed casing.
    """
    normalized = normalize_email(email)
    if not normalized:
        return None

    try:
        from scoring_engine.supabase_client import get_supabase_client

        supabase = get_supabase_client()
        if not supabase:
            logger.error("Supabase not available")
            return None

        # Case-insensitive lookup — covers historical rows that were stored
        # before email normalization was introduced.
        result = (
            supabase.table('users')
            .select('*')
            .ilike('email', normalized)
            .limit(1)
            .execute()
        )

        rows = result.data or []
        if not rows:
            logger.warning("User not found: %s", normalized)
            return None

        user = rows[0]

        if not verify_password(password, user['password_hash']):
            logger.warning("Invalid password for user: %s", normalized)
            return None

        supabase.table('users').update({
            'last_login_at': datetime.now(timezone.utc).isoformat(),
        }).eq('id', user['id']).execute()

        session_token = create_session_token()

        logger.info("User authenticated successfully: %s", normalized)

        return {
            'id': user['id'],
            'email': user['email'],
            'name': user['name'],
            'demographics': user['demographics'],
            'session_token': session_token,
        }

    except Exception as e:
        logger.error("Error authenticating user: %s", e, exc_info=True)
        return None


def get_user_by_email(email: str) -> Optional[dict]:
    """Get user information by email (case-insensitive)."""
    normalized = normalize_email(email)
    if not normalized:
        return None

    try:
        from scoring_engine.supabase_client import get_supabase_client

        supabase = get_supabase_client()
        if not supabase:
            return None

        result = (
            supabase.table('users')
            .select('id, email, name, demographics, created_at')
            .ilike('email', normalized)
            .limit(1)
            .execute()
        )

        rows = result.data or []
        return rows[0] if rows else None

    except Exception as e:
        logger.error("Error fetching user: %s", e)
        return None


def update_user_demographics(email: str, demographics: dict) -> bool:
    """Update a user's demographic information (case-insensitive lookup)."""
    normalized = normalize_email(email)
    if not normalized:
        return False

    try:
        from scoring_engine.supabase_client import get_supabase_client

        supabase = get_supabase_client()
        if not supabase:
            return False

        result = (
            supabase.table('users')
            .update({'demographics': demographics})
            .ilike('email', normalized)
            .execute()
        )

        return bool(result.data)

    except Exception as e:
        logger.error("Error updating user demographics: %s", e)
        return False
