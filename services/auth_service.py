"""Authentication service."""
from datetime import datetime, timedelta
from typing import Optional
import uuid
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from models.models import User
from core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and verify JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate a user."""
    user = db.query(User).filter_by(email=email).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_user(db: Session, email: str, username: str, password: str, full_name: str = None) -> User:
    """Create a new user."""
    hashed_password = get_password_hash(password)
    user = User(
        id=uuid.uuid4(),
        email=email,
        username=username,
        hashed_password=hashed_password,
        full_name=full_name,
        is_active=True,
        is_admin=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    return db.query(User).filter_by(email=email).first()


def get_user_by_id(db: Session, user_id: uuid.UUID) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter_by(id=user_id).first()