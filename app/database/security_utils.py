from sqlalchemy.orm import Session
from app.database.models import AuditLog
import json
import logging
from cryptography.fernet import Fernet
import os

logger = logging.getLogger(__name__)

# Encryption Key (Should be in env in prod)
ENCRYPTION_KEY = os.getenv("AUDIT_ENCRYPTION_KEY", Fernet.generate_key().decode())
cipher_suite = Fernet(ENCRYPTION_KEY.encode())

class SecurityUtils:
    @staticmethod
    def log_audit(db: Session, user_id, action_type, module, payload: dict, severity="info"):
        """Logs an encrypted action to the audit_logs table."""
        try:
            # Encrypt sensitive payload data if necessary
            payload_str = json.dumps(payload)
            encrypted_payload = cipher_suite.encrypt(payload_str.encode()).decode()
            
            new_log = AuditLog(
                user_id=user_id,
                action_type=action_type,
                module=module,
                payload={"encrypted_data": encrypted_payload},
                severity=severity
            )
            db.add(new_log)
            db.commit()
            logger.info(f"Audit Log Created: {action_type} in {module}")
        except Exception as e:
            logger.error(f"Audit Logging Failed: {e}")

    @staticmethod
    def decrypt_payload(encrypted_payload_dict):
        """Decrypts a previously logged audit payload."""
        try:
            encrypted_data = encrypted_payload_dict.get("encrypted_data")
            if not encrypted_data: return {}
            decrypted_text = cipher_suite.decrypt(encrypted_data.encode()).decode()
            return json.loads(decrypted_text)
        except Exception:
            return {"error": "Decryption failed"}
