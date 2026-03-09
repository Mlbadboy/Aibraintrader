import logging
import hashlib
import os
import json
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SecureCoreGuard:
    """
    Security Gatekeeper for Agentic AI Trading Brain.
    Implements mandatory abstraction and 'encryption' of the core model workflow
    to prevent reverse engineering of proprietary logic.
    """
    
    _INTERNAL_ALIAS_SALT = os.getenv("CORE_ALIAS_SALT", "secure_trading_brain_2026")
    _PUBLIC_ACCESS_MODE = os.getenv("APP_PUBLIC_ACCESS", "TRUE").upper() == "TRUE"

    @classmethod
    def obfuscate_agent_name(cls, real_name: str) -> str:
        """Creates a deterministic hash alias for internal agent names."""
        raw = f"{real_name}{cls._INTERNAL_ALIAS_SALT}"
        return f"core_proc_{hashlib.sha256(raw.encode()).hexdigest()[:12]}"

    @classmethod
    def encrypt_payload_metadata(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Masks internal agent names and technical metadata keys in the response
        payload so core workflow details aren't exposed in standard API results.
        """
        if not payload:
            return payload

        # Mapping of internal technical keys to obfuscated public keys
        key_map = {
            "regime": cls.obfuscate_agent_name("RegimeAgent"),
            "selected_strategy": cls.obfuscate_agent_name("StrategyAgent"),
            "ml_predictions": cls.obfuscate_agent_name("EnsembleModel"),
            "sentiment": cls.obfuscate_agent_name("SentimentEngine"),
            "trading_decision": cls.obfuscate_agent_name("DebateAgent"),
            "risk_assessment": cls.obfuscate_agent_name("RiskGuardian"),
            "latest_indicators": cls.obfuscate_agent_name("FeatureEngineer"),
            "classification": cls.obfuscate_agent_name("ClassificationAgent"),
            "options_strategy": cls.obfuscate_agent_name("OptionsAgent")
        }

        secure_payload = payload.copy()
        
        # We replace the keys so the 'workflow' looks like a sequence of hashed IDs
        # rather than a list of known AI agents.
        for internal_key, public_alias in key_map.items():
            if internal_key in secure_payload:
                secure_payload[public_alias] = secure_payload.pop(internal_key)
        
        # We also hide details inside ML predictions
        if "ml_predictions" in payload:
            ml_data = payload["ml_predictions"]
            # Mask model specific names if they exist
            if "model_weights_used" in ml_data:
                del ml_data["model_weights_used"]
        
        return secure_payload

    @classmethod
    def is_public_access_allowed(cls) -> bool:
        """Checks if the 'Give Access to All' mode is active."""
        return cls._PUBLIC_ACCESS_MODE

    @classmethod
    def wrap_orchestration(cls, func):
        """
        Decorator to wrap the full pipeline orchestration.
        Acts as the primary 'encryption' gate for the model workflow.
        """
        def wrapper(*args, **kwargs):
            try:
                # 1. Execute proprietary logic
                result = func(*args, **kwargs)
                
                # 2. Apply security transformations before exposing to outside world
                return cls.encrypt_payload_metadata(result)
            except Exception as e:
                logger.error(f"Security Gatekeeper failure: {e}")
                # Return generic error to hide stack trace details
                return {"error": "Secure execution failure", "timestamp": datetime.utcnow().isoformat()}
        
        return wrapper

# Guarded implementation of the core loader
def load_encrypted_model_asset(path: str):
    """
    Placeholder for loading encrypted model weights.
    In production, this would use a library like Cryptography or PyArmor
    to decrypt weights into memory only during instantiation.
    """
    logger.info(f"Loading core model weights from protected storage: {path}")
    # Simulate decryption logic
    with open(path, 'rb') as f:
        data = f.read()
    return data # In reality, return decrypted object
