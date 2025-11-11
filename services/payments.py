# services/payments.py
from __future__ import annotations
import os, json, hmac, hashlib
from typing import Dict, Tuple
from enum import Enum
import requests

class PaymentStatus(str, Enum):
    SUCCESS = "success"
    PENDING = "pending"
    FAILED = "failed"

# services/payments.py  (only the mapping changed; rest same)
def payment_links_config() -> Dict[str, str]:
    return {
        # DOCX
        "RESUME": os.getenv("RAZORPAY_LINK_RESUME", "#"),
        "SOP": os.getenv("RAZORPAY_LINK_SOP", "#"),
        "COVER_LETTER": os.getenv("RAZORPAY_LINK_COVER_LETTER", "#"),
        "VISA_COVER_LETTER": os.getenv("RAZORPAY_LINK_VISA_COVER_LETTER", "#"),
        # LaTeX / PDF
        "RESUME_LATEX": os.getenv("RAZORPAY_LINK_RESUME_LATEX", "#"),
        "SOP_LATEX": os.getenv("RAZORPAY_LINK_SOP_LATEX", "#"),
        "COVER_LETTER_LATEX": os.getenv("RAZORPAY_LINK_COVER_LETTER_LATEX", "#"),
        "VISA_COVER_LETTER_LATEX": os.getenv("RAZORPAY_LINK_VISA_COVER_LETTER_LATEX", "#"),
        # (reserved)
        "VISA_ITINERARY": os.getenv("RAZORPAY_LINK_VISA_ITINERARY", "#"),
        "VISA_SPONSOR": os.getenv("RAZORPAY_LINK_VISA_SPONSOR", "#"),
    }


def _basic_auth() -> Tuple[str, str]:
    kid = os.getenv("RAZORPAY_KEY_ID")
    ksec = os.getenv("RAZORPAY_KEY_SECRET")
    if not kid or not ksec:
        raise RuntimeError("Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in .env")
    return kid, ksec

def verify_razorpay_payment(payment_id: str) -> tuple[PaymentStatus, str]:
    kid, ksec = _basic_auth()
    url = f"https://api.razorpay.com/v1/payments/{payment_id}"
    try:
        resp = requests.get(url, auth=(kid, ksec), timeout=15)
    except Exception as e:
        return PaymentStatus.FAILED, json.dumps({"error": str(e)})
    if resp.status_code != 200:
        return PaymentStatus.FAILED, resp.text
    data = resp.json()
    status = data.get("status")
    if status == "captured":
        return PaymentStatus.SUCCESS, json.dumps(data, indent=2)
    elif status in {"created", "authorized", "pending"}:
        return PaymentStatus.PENDING, json.dumps(data, indent=2)
    else:
        return PaymentStatus.FAILED, json.dumps(data, indent=2)

# Optional webhook verification (if you add a backend)
def verify_webhook_signature(payload_body: bytes, razorpay_signature: str, webhook_secret: str) -> bool:
    digest = hmac.new(webhook_secret.encode("utf-8"), payload_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, razorpay_signature)
