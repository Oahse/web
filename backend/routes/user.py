from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional, List
from core.utils.response import Response
from core.exceptions import APIException
from core.database import get_db
from services.user import UserService,AddressService
from schemas.user import UserCreate, UserUpdate, AddressResponse # Import AddressResponse
from schemas.user import AddressCreate, AddressUpdate
from services.auth import AuthService, oauth2_scheme # Import AuthService and oauth2_scheme
from models.user import User # Import User model

router = APIRouter(prefix="/api/v1/users", tags=["Users & Addresses"])

# Dependency to get current authenticated user
async def get_current_authenticated_user(db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    return await AuthService.get_current_user(token, db)

# ==========================================================
# USER ENDPOINTS
# ==========================================================

@router.get("/")
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    service = UserService(db)
    users = await service.get_users(page=page, limit=limit)
    return Response.success(data=users)


@router.get("/{user_id}")
async def get_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    user = await service.get_user(user_id)
    if not user:
        raise APIException(status_code=status.HTTP_404_NOT_FOUND, message="User not found")
    return Response.success(data=user)


@router.post("/")
async def create_user(payload: UserCreate, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    user = await service.create_user(payload, background_tasks)
    return Response.success(data=user, code=status.HTTP_201_CREATED)


@router.put("/{user_id}")
async def update_user(user_id: UUID, payload: UserUpdate, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    updated_user = await service.update_user(user_id, payload)
    if not updated_user:
        raise APIException(status_code=status.HTTP_404_NOT_FOUND, message="User not found")
    return Response.success(data=updated_user)


@router.delete("/{user_id}")
async def delete_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    deleted = await service.delete_user(user_id)
    if not deleted:
        raise APIException(status_code=status.HTTP_404_NOT_FOUND, message="User not found")
    return Response.success(message="User deleted successfully")


# ==========================================================
# ADDRESS ENDPOINTS
# ==========================================================

@router.get("/me/addresses", response_model=List[AddressResponse]) # Add response_model
async def list_my_addresses(
    current_user: User = Depends(get_current_authenticated_user),
    db: AsyncSession = Depends(get_db)
):
    service = AddressService(db)
    addresses = await service.get_user_addresses(current_user.id)
    # Convert SQLAlchemy models to Pydantic models
    return [AddressResponse.from_orm(address) for address in addresses]

@router.get("/{user_id}/addresses")
async def list_addresses(user_id: UUID, db: AsyncSession = Depends(get_db)):
    service = AddressService(db)
    addresses = await service.get_user_addresses(user_id)
    return Response.success(data=addresses)


@router.get("/addresses/{address_id}")
async def get_address(address_id: UUID, db: AsyncSession = Depends(get_db)):
    service = AddressService(db)
    address = await service.get_address(address_id)
    if not address:
        raise APIException(status_code=status.HTTP_404_NOT_FOUND, message="Address not found")
    return Response.success(data=address)


@router.post("/{user_id}/addresses")
async def create_address(user_id: UUID, payload: AddressCreate, db: AsyncSession = Depends(get_db)):
    service = AddressService(db)
    address = await service.create_address(user_id=user_id, **payload.model_dump())
    return Response.success(data=address, code=status.HTTP_201_CREATED)


@router.put("/addresses/{address_id}")
async def update_address(address_id: UUID, payload: AddressUpdate, db: AsyncSession = Depends(get_db)):
    service = AddressService(db)
    updated = await service.update_address(address_id, **payload.model_dump(exclude_unset=True))
    if not updated:
        raise APIException(status_code=status.HTTP_404_NOT_FOUND, message="Address not found")
    return Response.success(data=updated)


@router.post("/addresses")
async def create_user_address(payload: AddressCreate, db: AsyncSession = Depends(get_db)):
    """Create address for current user (requires authentication)"""
    # This would need authentication to get current user ID
    # For now, we'll use a placeholder
    service = AddressService(db)
    # This endpoint would need proper authentication
    raise APIException(status_code=status.HTTP_501_NOT_IMPLEMENTED, message="Endpoint requires authentication")

@router.put("/addresses/{address_id}")
async def update_user_address(address_id: UUID, payload: AddressUpdate, db: AsyncSession = Depends(get_db)):
    """Update address for current user (requires authentication)"""
    service = AddressService(db)
    # This would need authentication to get current user ID
    updated = await service.update_address(address_id, None, **payload.model_dump(exclude_unset=True))
    if not updated:
        raise APIException(status_code=status.HTTP_404_NOT_FOUND, message="Address not found")
    return Response.success(data=updated)

@router.delete("/addresses/{address_id}")
async def delete_user_address(address_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete address for current user (requires authentication)"""
    service = AddressService(db)
    # This would need authentication to get current user ID
    deleted = await service.delete_address(address_id)
    if not deleted:
        raise APIException(status_code=status.HTTP_404_NOT_FOUND, message="Address not found")
    return Response.success(message="Address deleted successfully")
