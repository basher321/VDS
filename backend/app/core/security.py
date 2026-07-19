"""Password hashing + lightweight signed bearer tokens (local deployment)."""
from fastapi import Depends, HTTPException, Request, status
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


def _user_from_token(token: str, db: Session):
    from ..models.organization import User  # local import avoids cycles
    try:
        data = _serializer.loads(token, max_age=TOKEN_MAX_AGE)
    except BadSignature:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    user = db.query(User).filter(User.username == data.get("u")).first()
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")
    return user


def get_current_user(token: str | None = Depends(oauth2), db: Session = Depends(get_db)):
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    return _user_from_token(token, db)


def get_current_user_flexible(request: Request, token: str | None = Depends(oauth2),
                              db: Session = Depends(get_db)):
    """Like get_current_user, but also accepts ?token=... in the query string.

    Browsers can't attach an Authorization header to plain navigation, <a href>,
    <object data=...>, or window.open() -- so links/embeds that open a PDF directly
    (as opposed to going through fetch()) have no way to send the bearer token except
    in the URL itself."""
    tok = token or request.query_params.get("token")
    if not tok:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    return _user_from_token(tok, db)
