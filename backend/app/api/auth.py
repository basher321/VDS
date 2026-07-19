"""Login: verify credentials, return a signed bearer token."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.security import verify_password, make_token, get_current_user
from ..models.organization import User
from ..schemas.organization import LoginIn, TokenOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not user.is_active or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")
    return TokenOut(access_token=make_token(user.username), full_name=user.full_name)


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"username": user.username, "full_name": user.full_name, "role": user.role}
