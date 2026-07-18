"""
firestore_store.py — Firestore-backed persistence for CampusMind AI.

Saves conversation history + remembered facts to Firestore so they survive
app restarts and redeploys (unlike a local JSON file on Streamlit Community
Cloud's ephemeral filesystem). Data is encrypted at rest and in transit by
Firestore automatically.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

logger = logging.getLogger(__name__)

COLLECTION = "campusmind_users"


@st.cache_resource
def _get_firestore_client():
    """
    Initialize the Firebase Admin app once per server process (cached across
    reruns and sessions) and return a Firestore client.

    Expects a `[firebase]` table in st.secrets containing the full service
    account JSON key fields (see README for setup).
    """
    if not firebase_admin._apps:
        cred_dict = dict(st.secrets["firebase"])
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    return firestore.client()


class FirestoreStore:
    """Reads/writes one user's memory + chat history as a single Firestore document."""

    def __init__(self, user_id: str):
        if not user_id:
            raise ValueError("FirestoreStore requires a non-empty user_id.")
        self.user_id = user_id
        try:
            self.db = _get_firestore_client()
            self.doc_ref = self.db.collection(COLLECTION).document(user_id)
            self.available = True
        except Exception as e:
            logger.error("Firestore init failed, falling back to session-only memory: %s", e)
            self.doc_ref = None
            self.available = False

    def load(self) -> dict:
        """Return {'memory': {...}, 'messages': [...]}. Empty values if no doc yet or unavailable."""
        if not self.available:
            return {"memory": {}, "messages": []}
        try:
            snap = self.doc_ref.get()
            if snap.exists:
                data = snap.to_dict()
                return {
                    "memory": data.get("memory", {}),
                    "messages": data.get("messages", []),
                }
        except Exception as e:
            logger.error("Firestore load failed: %s", e)
        return {"memory": {}, "messages": []}

    def save(self, memory: dict, messages: list):
        """Overwrite this user's stored memory + history."""
        if not self.available:
            return
        try:
            self.doc_ref.set({
                "memory": memory,
                "messages": messages,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            })
        except Exception as e:
            logger.error("Firestore save failed: %s", e)

    def clear(self):
        if not self.available:
            return
        try:
            self.doc_ref.delete()
        except Exception as e:
            logger.error("Firestore delete failed: %s", e)
