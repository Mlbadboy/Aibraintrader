import logging

logger = logging.getLogger(__name__)

class InvestorMatcher:
    """
    Evaluates if a specific Mutual Fund is suitable for a given investor profile.
    Profiles: 'Conservative', 'Moderate', 'Aggressive'
    """
    def __init__(self):
        # Define maximum tolerable risk scores (0-100) for each profile
        self.risk_tolerances = {
            "Conservative": 35,
            "Moderate": 65,
            "Aggressive": 100
        }

    def match_profile(self, user_profile: str, risk_score: int, volatility_class: str) -> dict:
        """
        Returns a dictionary containing suitability and any mismatch warnings.
        """
        user_profile = user_profile.capitalize()
        if user_profile not in self.risk_tolerances:
            user_profile = "Moderate" # Default
            
        max_tolerable = self.risk_tolerances[user_profile]
        
        is_suitable = True
        warnings = []
        
        # 1. Check absolute risk score
        if risk_score > max_tolerable:
            is_suitable = False
            warnings.append(f"Fund Risk Score ({risk_score}) exceeds your {user_profile} tolerance ({max_tolerable}).")
            
        # 2. Check qualitative volatility
        if user_profile == "Conservative" and volatility_class in ["Moderate", "High"]:
            is_suitable = False
            warnings.append(f"A {volatility_class} volatility fund is not recommended for Conservative investors.")
            
        if user_profile == "Moderate" and volatility_class == "High":
            warnings.append("This fund has high volatility. Ensure it forms a smaller satellite portion of your portfolio.")
            
        # Calculate a 0-100 Suitability Score (100 being perfect match)
        # E.g., Conservative investor in a 20 risk fund is a great match. 
        # Aggressive investor in a 90 risk fund is a match, but aggressive in a 20 risk fund is also fine (just maybe suboptimal for growth).
        diff = max_tolerable - risk_score
        
        if diff < 0:
            suitability_score = max(0, 100 + diff * 2) # Penalize heavily for exceeding risk
        else:
            if user_profile == "Aggressive" and diff > 50:
                 # Aggressive investor in super safe fund
                 suitability_score = 70 
                 warnings.append("This fund may be too conservative to meet your aggressive growth targets.")
            else:
                 suitability_score = 100 - (diff * 0.5) # Slight penalty for being "too" safe
                 
        return {
            "user_profile": user_profile,
            "is_suitable": is_suitable,
            "suitability_score_100": min(100, max(0, round(suitability_score))),
            "warnings": warnings,
            "recommendation": "Strong Match" if is_suitable and not warnings else "Proceed with Caution" if is_suitable else "Not Recommended"
        }
