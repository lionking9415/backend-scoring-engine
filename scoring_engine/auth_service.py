"""
Authentication Service Module
Handles user registration, login, and session management with Supabase backend.
"""

import logging
import hashlib
import secrets
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


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
    """
    Create a new user account.
    
    Args:
        email: User's email address
        password: Plain text password (will be hashed)
        name: User's display name
        demographics: Optional demographic information
    
    Returns:
        User object if successful, None otherwise
    """
    try:
        from scoring_engine.supabase_client import get_supabase_client
        
        supabase = get_supabase_client()
        if not supabase:
            logger.error("Supabase not available")
            return None
        
        # Check if user already exists
        existing = supabase.table('users').select('email').eq('email', email).execute()
        if existing.data:
            logger.warning(f"User already exists: {email}")
            return None
        
        # Hash password
        password_hash = hash_password(password)
        
        # Create user record
        user_data = {
            'email': email,
            'password_hash': password_hash,
            'name': name or email.split('@')[0],
            'demographics': demographics or {},
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        result = supabase.table('users').insert(user_data).execute()
        
        if result.data:
            user = result.data[0]
            logger.info(f"User created successfully: {email}")
            # Don't return password_hash to client
            return {
                'id': user['id'],
                'email': user['email'],
                'name': user['name'],
                'demographics': user['demographics']
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error creating user: {e}", exc_info=True)
        return None


def authenticate_user(email: str, password: str) -> Optional[dict]:
    """
    Authenticate a user with email and password.
    
    Args:
        email: User's email address
        password: Plain text password
    
    Returns:
        User object with session token if successful, None otherwise
    """
    try:
        from scoring_engine.supabase_client import get_supabase_client
        
        supabase = get_supabase_client()
        if not supabase:
            logger.error("Supabase not available")
            return None
        
        # Fetch user
        result = supabase.table('users').select('*').eq('email', email).maybe_single().execute()
        
        if not result.data:
            logger.warning(f"User not found: {email}")
            return None
        
        user = result.data
        
        # Verify password
        if not verify_password(password, user['password_hash']):
            logger.warning(f"Invalid password for user: {email}")
            return None
        
        # Update last login
        supabase.table('users').update({
            'last_login_at': datetime.now(timezone.utc).isoformat()
        }).eq('email', email).execute()
        
        # Generate session token
        session_token = create_session_token()
        
        logger.info(f"User authenticated successfully: {email}")
        
        # Return user data (without password_hash) and session token
        return {
            'id': user['id'],
            'email': user['email'],
            'name': user['name'],
            'demographics': user['demographics'],
            'session_token': session_token
        }
        
    except Exception as e:
        logger.error(f"Error authenticating user: {e}", exc_info=True)
        return None


def get_user_by_email(email: str) -> Optional[dict]:
    """
    Get user information by email.
    
    Args:
        email: User's email address
    
    Returns:
        User object if found, None otherwise
    """
    try:
        from scoring_engine.supabase_client import get_supabase_client
        
        supabase = get_supabase_client()
        if not supabase:
            return None
        
        result = supabase.table('users').select('id, email, name, demographics, created_at').eq('email', email).maybe_single().execute()
        
        if result.data:
            return result.data
        
        return None
        
    except Exception as e:
        logger.error(f"Error fetching user: {e}")
        return None


def update_user_demographics(email: str, demographics: dict) -> bool:
    """
    Update user's demographic information.
    
    Args:
        email: User's email address
        demographics: New demographic data
    
    Returns:
        True if successful, False otherwise
    """
    try:
        from scoring_engine.supabase_client import get_supabase_client
        
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        result = supabase.table('users').update({
            'demographics': demographics
        }).eq('email', email).execute()
        
        return bool(result.data)
        
    except Exception as e:
        logger.error(f"Error updating user demographics: {e}")
        return False
