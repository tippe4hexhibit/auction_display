from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.orm import Session
import os

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

security = HTTPBearer()

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = pwd_context.hash("admin123")  # Default password: admin123

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return user info."""
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
    except JWTError:
        raise credentials_exception

def authenticate_user(username: str, password: str, db: Session = None) -> bool:
    """Authenticate user credentials."""
    if username == ADMIN_USERNAME and verify_password(password, ADMIN_PASSWORD_HASH):
        return True
    
    if db:
        from database import User
        user = db.query(User).filter(User.username == username).first()
        if user and verify_password(password, user.password_hash):
            return True
    
    return False

def create_user(username: str, password: str, db: Session) -> bool:
    """Create a new admin user."""
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
    """Change password for an existing user."""
    from database import User
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    
    user.password_hash = get_password_hash(new_password)
    db.commit()
    return True

def get_all_users(db: Session):
    """Get all users."""
    from database import User
    return db.query(User).all()

def delete_user(username: str, db: Session) -> bool:
    """Delete a user."""
    from database import User
    
    if username == ADMIN_USERNAME:
        return False
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    
    db.delete(user)
    db.commit()
    return True

def require_auth(user_info: dict = Depends(verify_token)):
    """Dependency to require authentication for protected routes."""
    return user_info
