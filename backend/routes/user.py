from fastapi import APIRouter, Depends, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional, List
from core.utils.response import Response
from core.exceptions import APIException
from core.database import get_db
from services.user import UserService, AddressService
from services.search import SearchService
# Import AddressResponse
from schemas.user import UserCreate, UserUpdate, AddressResponse
from schemas.user import AddressCreate, AddressUpdate
# Import AuthService and oauth2_scheme
from services.auth import AuthService, oauth2_scheme
from models.user import User  # Import User model

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
    role: Optional[str] = Query(None, description="Filter by user role"),
    q: Optional[str] = Query(None, description="Search query for user name or email"),
    search_mode: Optional[str] = Query("basic", regex="^(basic|advanced)$", description="Search mode: basic or advanced"),
    db: AsyncSession = Depends(get_db)
):
    """List users with optional search functionality."""
    try:
        # If there's a search query and advanced search is requested, use the search service
        if q and len(q.strip()) >= 2 and search_mode == "advanced":
            search_service = SearchService(db)
            
            # Use advanced search
            search_results = await search_service.search_users(
                query=q.strip(),
                limit=limit,
                role_filter=role
            )
            
            # Convert search results to match the expected format
            return Response.success(data={
                "data": search_results,
                "total": len(search_results),
                "page": page,
                "per_page": limit,
                "total_pages": 1,
                "search_mode": "advanced"
            })
        else:
            # Use basic user service for regular queries
            service = UserService(db)
            users = await service.get_users(page=page, limit=limit, role=role)
            if isinstance(users, dict):
                users["search_mode"] = "basic"
            return Response.success(data=users)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch users: {str(e)}"
        )


@router.get("/{user_id}")
async def get_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    user = await service.get_user(user_id)
    if not user:
        raise APIException(
            status_code=status.HTTP_404_NOT_FOUND, message="User not found")
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
        raise APIException(
            status_code=status.HTTP_404_NOT_FOUND, message="User not found")
    return Response.success(data=updated_user)


@router.delete("/{user_id}")
async def delete_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    deleted = await service.delete_user(user_id)
    if not deleted:
        raise APIException(
            status_code=status.HTTP_404_NOT_FOUND, message="User not found")
    return Response.success(message="User deleted successfully")


# ==========================================================
# ADDRESS ENDPOINTS
# ==========================================================

# Add response_model
@router.get("/me/addresses", response_model=List[AddressResponse])
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
        raise APIException(status_code=status.HTTP_404_NOT_FOUND,
                           message="Address not found")
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
        raise APIException(status_code=status.HTTP_404_NOT_FOUND,
                           message="Address not found")
    return Response.success(data=updated)


@router.post("/addresses")
async def create_user_address(payload: AddressCreate, db: AsyncSession = Depends(get_db)):
    """Create address for current user (requires authentication)"""
    # This would need authentication to get current user ID
    # For now, we'll use a placeholder
    service = AddressService(db)
    # This endpoint would need proper authentication
    raise APIException(status_code=status.HTTP_501_NOT_IMPLEMENTED,
                       message="Endpoint requires authentication")


@router.put("/addresses/{address_id}")
async def update_user_address(address_id: UUID, payload: AddressUpdate, db: AsyncSession = Depends(get_db)):
    """Update address for current user (requires authentication)"""
    service = AddressService(db)
    # This would need authentication to get current user ID
    updated = await service.update_address(address_id, None, **payload.model_dump(exclude_unset=True))
    if not updated:
        raise APIException(status_code=status.HTTP_404_NOT_FOUND,
                           message="Address not found")
    return Response.success(data=updated)


@router.delete("/addresses/{address_id}")
async def delete_user_address(address_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete address for current user (requires authentication)"""
    service = AddressService(db)
    # This would need authentication to get current user ID
    deleted = await service.delete_address(address_id)
    if not deleted:
        raise APIException(status_code=status.HTTP_404_NOT_FOUND,
                           message="Address not found")
    return Response.success(message="Address deleted successfully")
