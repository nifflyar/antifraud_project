import base64
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import os
import secrets

from jose import jwt

from app.application.interfaces.auth import AuthService
from app.infrastructure.config import Config

_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SALT_SIZE = 16
_KEY_LENGTH = 64


class AuthServiceImpl(AuthService):
    def __init__(self, config: Config) -> None:
        self.config = config

    def hash_password(self, password: str) -> str:
        salt = os.urandom(_SALT_SIZE)
        derived_key = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=_SCRYPT_N,
            r=_SCRYPT_R,
            p=_SCRYPT_P,
            dklen=_KEY_LENGTH,
        )
        encoded_salt = base64.b64encode(salt).decode("ascii")
        encoded_key = base64.b64encode(derived_key).decode("ascii")
        return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${encoded_salt}${encoded_key}"

    def verify_password(self, password: str, password_hash: str) -> bool:
        try:
            algorithm, n_value, r_value, p_value, encoded_salt, encoded_key = (
                password_hash.split("$", maxsplit=5)
            )
        except ValueError:
            return False

        if algorithm != "scrypt":
            return False

        salt = base64.b64decode(encoded_salt.encode("ascii"))
        expected_key = base64.b64decode(encoded_key.encode("ascii"))
        derived_key = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=int(n_value),
            r=int(r_value),
            p=int(p_value),
            dklen=len(expected_key),
        )
        return hmac.compare_digest(derived_key, expected_key)

    def create_access_token(self, user_id: int, is_admin: bool) -> str:
        payload = {
            "sub": str(user_id),
            "is_admin": is_admin,
            "exp": datetime.now(UTC) + timedelta(
                minutes=self.config.auth.access_token_expire_minutes
            ),
        }
        token = jwt.encode(
            payload,
            self.config.auth.secret_key.get_secret_value(),
            algorithm=self.config.auth.algorithm,
        )
        return token

    def create_refresh_token(self) -> str:
        return secrets.token_urlsafe(32)

    def hash_refresh_token(self, refresh_token: str) -> str:
        return hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()
