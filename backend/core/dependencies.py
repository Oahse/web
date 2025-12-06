from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from models.user import User
from services.auth import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_auth_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    """Get current authenticated user with proper error handling"""
    try:
        user = await AuthService.get_current_user(token, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    """Get current authenticated user"""
    try:
        user = await AuthService.get_current_user(token, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Require admin role"""
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def verify_user_or_admin_access(current_user: User = Depends(get_current_active_user)) -> User:
    """Verify user has access (user or admin)"""
    if not current_user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active"
        )
    return current_user


async def require_supplier(current_user: User = Depends(get_current_active_user)) -> User:
    """Require supplier role"""
    if current_user.role not in ["Supplier", "Admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
    return current_user


async def require_admin_or_supplier(current_user: User = Depends(get_current_active_user)) -> User:
    """Require Admin or Supplier role"""
    if current_user.role not in ["Admin", "Supplier"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or Supplier access required"
        )
    return current_user
