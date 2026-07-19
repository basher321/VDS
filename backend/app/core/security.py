"""Password hashing + lightweight signed bearer tokens (local deployment)."""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from itsdangerous import BadSignature, URLSafeTimedSerializer
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .config import get_settings
from .database import get_db

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
_serializer = URLSafeTimedSerializer(get_settings().secret_key, salt="vds-auth")
oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

TOKEN_MAX_AGE = 60 * 60 * 12  # 12 hours


def hash_password(raw: str) -> str:
    return pwd.hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
    try:
        return pwd.verify(raw, hashed)
    except Exception:
        return False


def make_token(username: str) -> str:
    return _serializer.dumps({"u": username})


def get_current_user(token: str | None = Depends(oauth2), db: Session = Depends(get_db)):
    from ..models.organization import User  # local import avoids cycles
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    try:
        data = _serializer.loads(token, max_age=TOKEN_MAX_AGE)
    except BadSignature:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    user = db.query(User).filter(User.username == data.get("u")).first()
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")
    return user
