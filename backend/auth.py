from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import bcrypt as _bcrypt
import jwt
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session
import os

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )

def get_password_hash(password: str) -> str:
    return _bcrypt.hashpw(
        password.encode("utf-8"),
        _bcrypt.gensalt(),
    ).decode("utf-8")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return {"username": username}
    except InvalidTokenError:
        raise credentials_exception

def authenticate_user(username: str, password: str, db: Session) -> bool:
    from database import User
    user = db.query(User).filter(User.username == username).first()
    return bool(user and verify_password(password, user.password_hash))

def create_user(username: str, password: str, db: Session) -> bool:
    from database import User

    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        return False

    password_hash = get_password_hash(password)
    user = User(username=username, password_hash=password_hash, is_admin=True)
    db.add(user)
    db.commit()
    return True

def change_user_password(username: str, new_password: str, db: Session) -> bool:
    from database import User

    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False

    user.password_hash = get_password_hash(new_password)
    db.commit()
    return True

def get_all_users(db: Session):
    from database import User
    return db.query(User).all()

def delete_user(username: str, db: Session) -> bool:
    from database import User

    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False

    # Never delete the last remaining account — that would lock everyone out.
    if db.query(User).count() <= 1:
        return False

    db.delete(user)
    db.commit()
    return True

def require_auth(user_info: dict = Depends(verify_token)):
    return user_info
