"""
Email Service Module — Resend Integration
Handles transactional emails: email confirmation and password reset.
"""

import os
import logging
from typing import Optional

import resend
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "BEST Galaxy <noreply@bestgalaxy.com>")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Initialise Resend
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY
    logger.info("Resend API key configured")
else:
    logger.warning("RESEND_API_KEY not set — emails will not be sent")


def _send(to: str, subject: str, html: str) -> Optional[dict]:
    """Low-level send wrapper. Returns the Resend response or None on failure."""
    if not RESEND_API_KEY:
        logger.error("Cannot send email — RESEND_API_KEY not configured")
        return None
    try:
        params: resend.Emails.SendParams = {
            "from": FROM_EMAIL,
            "to": [to],
            "subject": subject,
            "html": html,
        }
        result = resend.Emails.send(params)
        logger.info("Email sent to %s — subject: %s", to, subject)
        return result
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to, e, exc_info=True)
        return None


# ─── Email Confirmation ─────────────────────────────────────────────────────

def send_confirmation_email(to: str, name: str, token: str) -> Optional[dict]:
    """Send an email-confirmation link after signup."""
    confirm_url = f"{FRONTEND_URL}/confirm-email?token={token}"
    subject = "Confirm Your BEST Galaxy Account"
    html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 560px; margin: 0 auto; padding: 32px 24px;">
      <div style="text-align: center; margin-bottom: 32px;">
        <h1 style="font-size: 24px; color: #1e1b4b; margin: 0 0 8px;">Welcome to BEST Galaxy&trade;</h1>
        <p style="color: #6b7280; font-size: 14px; margin: 0;">Executive Function Assessment</p>
      </div>

      <div style="background: #f5f3ff; border-radius: 12px; padding: 24px; margin-bottom: 24px;">
        <p style="color: #374151; font-size: 15px; line-height: 1.6; margin: 0 0 16px;">
          Hi <strong>{name}</strong>,
        </p>
        <p style="color: #374151; font-size: 15px; line-height: 1.6; margin: 0 0 24px;">
          Thanks for creating your account! Please confirm your email address to get started.
        </p>
        <div style="text-align: center;">
          <a href="{confirm_url}"
             style="display: inline-block; background: linear-gradient(135deg, #4f46e5, #7c3aed);
                    color: #ffffff; font-weight: 700; font-size: 15px; text-decoration: none;
                    padding: 14px 32px; border-radius: 10px;">
            Confirm My Email
          </a>
        </div>
      </div>

      <p style="color: #9ca3af; font-size: 12px; line-height: 1.5;">
        If you didn&rsquo;t create this account, you can safely ignore this email.<br>
        This link expires in 24 hours.
      </p>
      <p style="color: #9ca3af; font-size: 12px; margin-top: 16px;">
        Or paste this URL into your browser:<br>
        <a href="{confirm_url}" style="color: #6366f1; word-break: break-all;">{confirm_url}</a>
      </p>
    </div>
    """
    return _send(to, subject, html)


# ─── Password Reset ─────────────────────────────────────────────────────────

def send_password_reset_email(to: str, name: str, token: str) -> Optional[dict]:
    """Send a password-reset link."""
    reset_url = f"{FRONTEND_URL}/reset-password?token={token}"
    subject = "Reset Your BEST Galaxy Password"
    html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 560px; margin: 0 auto; padding: 32px 24px;">
      <div style="text-align: center; margin-bottom: 32px;">
        <h1 style="font-size: 24px; color: #1e1b4b; margin: 0 0 8px;">Password Reset</h1>
        <p style="color: #6b7280; font-size: 14px; margin: 0;">BEST Galaxy&trade; Executive Function Assessment</p>
      </div>

      <div style="background: #fef2f2; border-radius: 12px; padding: 24px; margin-bottom: 24px;">
        <p style="color: #374151; font-size: 15px; line-height: 1.6; margin: 0 0 16px;">
          Hi <strong>{name}</strong>,
        </p>
        <p style="color: #374151; font-size: 15px; line-height: 1.6; margin: 0 0 24px;">
          We received a request to reset your password. Click the button below to choose a new one.
        </p>
        <div style="text-align: center;">
          <a href="{reset_url}"
             style="display: inline-block; background: linear-gradient(135deg, #dc2626, #b91c1c);
                    color: #ffffff; font-weight: 700; font-size: 15px; text-decoration: none;
                    padding: 14px 32px; border-radius: 10px;">
            Reset My Password
          </a>
        </div>
      </div>

      <p style="color: #9ca3af; font-size: 12px; line-height: 1.5;">
        If you didn&rsquo;t request this, you can safely ignore this email. Your password will not change.<br>
        This link expires in 1 hour.
      </p>
      <p style="color: #9ca3af; font-size: 12px; margin-top: 16px;">
        Or paste this URL into your browser:<br>
        <a href="{reset_url}" style="color: #6366f1; word-break: break-all;">{reset_url}</a>
      </p>
    </div>
    """
    return _send(to, subject, html)
