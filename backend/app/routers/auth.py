"""
Authentication Router
"""
from typing import Optional
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status, Header
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.schemas.user import UserCreate, UserLogin, UserOut, Token
from backend.app.services.auth_service import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def get_current_user(
    authorization: Optional[str] = Header(None),
    cityfix_session: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Extract current user from Bearer token if provided."""
    token = None
    if authorization and authorization.startswith("Bearer "):
        parts = authorization.split(" ", 1)
        if len(parts) == 2:
            token = parts[1].strip()
    elif cityfix_session:
        token = cityfix_session
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    email = payload.get("sub")
    if not email:
        return None
    return db.query(User).filter(User.email == email).first()


def require_user(user: Optional[User] = Depends(get_current_user)) -> User:
    """Enforce that user is authenticated."""
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, response: Response, db: Session = Depends(get_db)):
    """Register a new citizen or city authority user."""
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists"
        )
    
    hashed_pwd = get_password_hash(user_in.password)
    new_user = User(
        full_name=user_in.full_name,
        email=user_in.email,
        hashed_password=hashed_pwd,
        role="citizen",
        department=user_in.department,
        phone=user_in.phone
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": new_user.email, "role": new_user.role})
    response.set_cookie("cityfix_session", token, httponly=True, samesite="lax", max_age=86400)
    return Token(access_token=token, token_type="bearer", user=UserOut.model_validate(new_user))


@router.post("/login", response_model=Token)
def login(creds: UserLogin, response: Response, db: Session = Depends(get_db)):
    """Log in with email and password."""
    user = db.query(User).filter(User.email == creds.email).first()
    if not user or not verify_password(creds.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    token = create_access_token({"sub": user.email, "role": user.role})
    response.set_cookie("cityfix_session", token, httponly=True, samesite="lax", max_age=86400)
    return Token(access_token=token, token_type="bearer", user=UserOut.model_validate(user))


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("cityfix_session")
    return {"success": True}


@router.get("/me", response_model=UserOut)
def get_profile(user: User = Depends(require_user)):
    """Return current authenticated user profile."""
    return user
