import re
import json
from typing import Tuple, Dict
from cryptography.fernet import Fernet

class LocalPrivacyProxy:
    def __init__(self) -> None:
        # Generate or use a standard repeatable Fernet key
        self.key = Fernet.generate_key()
        self.cipher = Fernet(self.key)
        
        # Target patterns for proprietary assets
        self.patterns = {
            "DB_NAME": r"\b\w+(?:DB|Database|Repository)\b",
            "API_ENDPOINT": r"\b\w+(?:API|Endpoint|Service)\b",
            "IP_ADDRESS": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            "TEAM_EMAIL": r"\b[a-zA-Z0-9._%+-]+@\w+\.(?:com|in|org|net)\b",
            "ACCOUNT_NO": r"\b\d{9,18}\b"
        }

    def mask(self, text: str) -> Tuple[str, str]:
        """
        Mask sensitive entities in the text. Returns (masked_text, encrypted_map_string).
        """
        mapping: Dict[str, str] = {}
        masked_text = text
        token_counter = 1
        
        for category, regex in self.patterns.items():
            matches = re.findall(regex, masked_text)
            for match in set(matches):
                if match not in mapping.values():
                    token = f"<SYSTEM_{category}_{token_counter}>"
                    mapping[token] = match
                    masked_text = masked_text.replace(match, token)
                    token_counter += 1
                    
        # Symmetrically encrypt the mapping dict
        serialized_map = json.dumps(mapping).encode("utf-8")
        encrypted_map = self.cipher.encrypt(serialized_map).decode("utf-8")
        
        return masked_text, encrypted_map

    def unmask(self, masked_text: str, encrypted_map_str: str) -> str:
        """
        Symmetrically decrypt and restore original values to the masked text.
        """
        if not encrypted_map_str:
            return masked_text
            
        try:
            decrypted_bytes = self.cipher.decrypt(encrypted_map_str.encode("utf-8"))
            mapping: Dict[str, str] = json.loads(decrypted_bytes.decode("utf-8"))
            
            restored_text = masked_text
            for token, real_value in mapping.items():
                restored_text = restored_text.replace(token, real_value)
            return restored_text
        except Exception:
            # Fallback to returning original string in case of decryption issues
            return masked_text