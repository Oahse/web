from fastapi import APIRouter, Depends, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from core.database import get_db
from core.utils.response import Response
from core.exceptions import APIException
from core.config import settings
from schemas.auth import UserCreate, UserLogin, Token, UserResponse, AuthResponse
from schemas.user import AddressCreate, AddressUpdate, AddressResponse
from schemas.response import APIResponse
from services.auth import AuthService
from services.user import UserService, AddressService
from models.user import User
from uuid import UUID

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_auth_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    return await AuthService.get_current_user(token, db)

@router.post("/register")
async def register(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user."""
    try:
        auth_service = AuthService(db)
        user = await auth_service.create_user(user_data, background_tasks)
        return Response(success=True, data=user, message="User registered successfully")
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=str(e)
        )

@router.post("/login")
async def login(
    background_tasks: BackgroundTasks,
    user_login: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Login user and return access token."""
    try:
        auth_service = AuthService(db)
        token = await auth_service.authenticate_user(user_login.email, user_login.password, background_tasks)
        print("Login successful, returning response.")
        return Response(success=True, data=token, message="Login successful")
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=f"Invalid credentials - {str(e)}"
        )

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_auth_user)
):
    """Logout user."""
    return Response(success=True, message="Logged out successfully")

@router.get("/profile")
async def get_profile(
    current_user: User = Depends(get_current_auth_user)
):
    """Get current user profile."""
    try:
        user_data = {
            "id": str(current_user.id),
            "email": current_user.email,
            "firstname": current_user.firstname,
            "lastname": current_user.lastname,
            "phone": current_user.phone,
            "role": current_user.role,
            "verified": current_user.verified,
            "active": current_user.active,
            "created_at": current_user.created_at.isoformat()
        }
        return Response(success=True, data=user_data)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get profile"
        )

@router.get("/addresses", response_model=List[AddressResponse])
async def get_addresses(
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all addresses for the current user."""
    try:
        address_service = AddressService(db)
        addresses = await address_service.get_user_addresses(current_user.id)
        return [AddressResponse.from_orm(address) for address in addresses]
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch addresses - {str(e)}"
        )

@router.post("/addresses", response_model=APIResponse[AddressResponse])
async def create_address(
    address_data: AddressCreate,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new address for the current user."""
    try:
        address_service = AddressService(db)
        address = await address_service.create_address(
            user_id=current_user.id,
            **address_data.dict()
        )
        return Response(success=True, data=address, message="Address created successfully")
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=f"Failed to create address - {str(e)}"
        )

@router.put("/addresses/{address_id}", response_model=APIResponse[AddressResponse])
async def update_address(
    address_id: UUID,
    address_data: AddressUpdate,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing address for the current user."""
    try:
        address_service = AddressService(db)
        address = await address_service.update_address(
            address_id=address_id,
            user_id=current_user.id, # Ensure user owns the address
            **address_data.dict(exclude_unset=True)
        )
        if not address:
            raise APIException(status_code=status.HTTP_404_NOT_FOUND, message="Address not found or not owned by user")
        return Response(success=True, data=address, message="Address updated successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=f"Failed to update address - {str(e)}"
        )

@router.delete("/addresses/{address_id}", response_model=APIResponse[dict])
async def delete_address(
    address_id: UUID,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an address for the current user."""
    try:
        address_service = AddressService(db)
        deleted = await address_service.delete_address(address_id, current_user.id) # Pass user_id for ownership check
        if not deleted:
            raise APIException(status_code=status.HTTP_404_NOT_FOUND, message="Address not found or not owned by user")
        return Response(success=True, message="Address deleted successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=f"Failed to delete address - {str(e)}"
        )

@router.get("/verify-email") # Changed to GET as it's typically a link click
async def verify_email(
    token: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Verify user email with token."""
    try:
        user_service = UserService(db)
        await user_service.verify_email(token, background_tasks)
        return Response(success=True, message="Email verified successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )

@router.post("/forgot-password")
async def forgot_password(
    email: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Send password reset email."""
    try:
        auth_service = AuthService(db)
        await auth_service.send_password_reset(email, background_tasks)
        return Response(success=True, message="Password reset email sent")
    except Exception as e:
        # Always return success for security
        return Response(success=True, message="If the email exists, a reset link has been sent")

@router.post("/reset-password")
async def reset_password(
    token: str,
    new_password: str,
    db: AsyncSession = Depends(get_db)
):
    """Reset password with token."""
    try:
        auth_service = AuthService(db)
        await auth_service.reset_password(token, new_password)
        return Response(success=True, message="Password reset successfully")
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

@router.put("/profile")
async def update_profile(
    user_data: dict,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user profile."""
    try:
        user_service = UserService(db)
        updated_user = await user_service.update_user(current_user.id, user_data)
        return Response(success=True, data=UserResponse.from_orm(updated_user), message="Profile updated successfully")
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=f"Failed to update profile - {str(e)}"
        )

@router.put("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password."""
    try:
        auth_service = AuthService(db)
        # Verify current password
        if not auth_service.verify_password(current_password, current_user.hashed_password):
            raise APIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Current password is incorrect"
            )
        
        # Update password
        user_service = UserService(db)
        hashed_password = auth_service.get_password_hash(new_password)
        await user_service.update_user(current_user.id, {"hashed_password": hashed_password})
        
        return Response(success=True, message="Password changed successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=f"Failed to change password - {str(e)}"
        )

@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token."""
    try:
        auth_service = AuthService(db)
        
        # Verify refresh token
        try:
            from jose import jwt, JWTError
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            email: str = payload.get("sub")
            token_type: str = payload.get("type")
            
            if email is None or token_type != "refresh":
                raise APIException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    message="Invalid refresh token"
                )
        except JWTError:
            raise APIException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid refresh token"
            )
        
        # Get user and create new tokens
        user = await auth_service.get_user_by_email(email)
        if not user:
            raise APIException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="User not found"
            )
        
        # Create new access token
        from datetime import timedelta
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth_service.create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        response_data = {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
        return Response(success=True, data=response_data, message="Token refreshed successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Failed to refresh token"
        )
