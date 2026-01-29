from fastapi import APIRouter, Depends, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional, List
from core.utils.response import Response
from core.errors import APIException
from core.db import get_db
from core.logging import get_logger
from services.user import UserService, AddressService
from services.search import SearchService
# Import AddressResponse
from schemas.user import UserCreate, UserUpdate, AddressResponse
from schemas.user import AddressCreate, AddressUpdate
# Import AuthService and oauth2_scheme
from services.auth import AuthService
from core.dependencies import get_current_auth_user
from models.user import User  # Import User model

logger = get_logger(__name__)
router = APIRouter(prefix="/users", tags=["Users & Addresses"])


# ==========================================================
# USER ENDPOINTS
# ==========================================================

@router.get("/me")
async def get_current_user_me(
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user profile (alias for /profile)"""
    try:
        from schemas.user import UserResponse
        
        user_data = {
            "id": current_user.id,
            "email": current_user.email,
            "firstname": current_user.firstname,
            "lastname": current_user.lastname,
            "full_name": f"{current_user.firstname} {current_user.lastname}",
            "phone": current_user.phone,
            "role": current_user.role,
            "verified": current_user.verified,
            "is_active": current_user.is_active,
            "age": current_user.age,
            "gender": current_user.gender,
            "country": current_user.country,
            "language": current_user.language,
            "timezone": current_user.timezone,
            "created_at": current_user.created_at,
            "updated_at": current_user.updated_at
        }
        
        user_response = UserResponse.model_validate(user_data)
        return Response.success(data=user_response)
    except APIException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        raise APIException(status_code=500, message="Internal server error")


@router.get("/profile")
async def get_user_profile(
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's profile"""
    try:
        from schemas.user import UserResponse
        
        # Convert User model to UserResponse
        user_data = {
            "id": current_user.id,
            "email": current_user.email,
            "firstname": current_user.firstname,
            "lastname": current_user.lastname,
            "full_name": f"{current_user.firstname} {current_user.lastname}",
            "phone": current_user.phone,
            "role": current_user.role,
            "verified": current_user.verified,
            "is_active": current_user.is_active,
            "age": current_user.age,
            "gender": current_user.gender,
            "country": current_user.country,
            "language": current_user.language,
            "timezone": current_user.timezone,
            "created_at": current_user.created_at,
            "updated_at": current_user.updated_at
        }
        
        user_response = UserResponse.model_validate(user_data)
        return Response.success(data=user_response)
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch user profile: {str(e)}"
        )


@router.put("/profile")
async def update_user_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's profile"""
    try:
        from schemas.user import UserResponse
        service = UserService(db)
        updated_user = await service.update_user(current_user.id, payload)
        if not updated_user:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND, 
                message="User profile not found"
            )
        
        # Convert User model to UserResponse
        user_data = {
            "id": updated_user.id,
            "email": updated_user.email,
            "firstname": updated_user.firstname,
            "lastname": updated_user.lastname,
            "full_name": f"{updated_user.firstname} {updated_user.lastname}",
            "phone": updated_user.phone,
            "role": updated_user.role,
            "verified": updated_user.verified,
            "is_active": updated_user.is_active,
            "age": updated_user.age,
            "gender": updated_user.gender,
            "country": updated_user.country,
            "language": updated_user.language,
            "timezone": updated_user.timezone,
            "created_at": updated_user.created_at,
            "updated_at": updated_user.updated_at
        }
        
        user_response = UserResponse.model_validate(user_data)
        return Response.success(data=user_response, message="Profile updated successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to update user profile: {str(e)}"
        )


@router.get("/search")
async def search_users(
    q: str = Query(..., min_length=2, description="Search query (minimum 2 characters)"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    role: Optional[str] = Query(None, regex="^(Customer|Supplier|Admin)$", description="Filter by user role"),
    db: AsyncSession = Depends(get_db)
):
    """
    Advanced search for users with prefix matching on name and email.
    """
    try:
        user_service = UserService(db)
        
        users = await user_service.search_users(
            query=q,
            limit=limit,
            role_filter=role
        )
        
        return Response.success(
            data={
                "query": q,
                "role_filter": role,
                "users": users,
                "count": len(users)
            }
        )
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to search users: {str(e)}"
        )


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
@router.get("/me/addresses")
async def list_my_addresses(
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    service = AddressService(db)
    addresses = await service.get_user_addresses(current_user.id)
    # Convert SQLAlchemy models to Pydantic models
    return Response.success(data=[AddressResponse.from_orm(address) for address in addresses])


@router.get("/{user_id}/addresses")
async def list_addresses(user_id: UUID, db: AsyncSession = Depends(get_db)):
    service = AddressService(db)
    addresses = await service.get_user_addresses(user_id)
    return Response.success(data=addresses)


@router.get("/addresses/{address_id}")
async def get_address(
    address_id: UUID,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific address (must be owned by current user)"""
    try:
        service = AddressService(db)
        address = await service.get_address_by_id(address_id)
        if not address or address.user_id != current_user.id:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Address not found"
            )
        return Response.success(data=address)
    except APIException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving address {address_id}: {e}")
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to retrieve address"
        )


@router.post("/addresses")
async def create_user_address(
    payload: AddressCreate, 
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Create address for current user (requires authentication)"""
    try:
        service = AddressService(db)
        address = await service.create_address(user_id=current_user.id, **payload.model_dump())
        return Response.success(
            data=address,
            message="Address created successfully",
            status_code=status.HTTP_201_CREATED
        )
    except Exception as e:
        logger.error(f"Error creating address for user {current_user.id}: {e}")
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to create address"
        )


@router.put("/addresses/{address_id}")
async def update_user_address(
    address_id: UUID, 
    payload: AddressUpdate, 
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Update address for current user (requires authentication)"""
    try:
        service = AddressService(db)
        updated = await service.update_address(address_id, current_user.id, **payload.model_dump(exclude_unset=True))
        if not updated:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Address not found"
            )
        return Response.success(data=updated, message="Address updated successfully")
    except APIException:
        raise
    except Exception as e:
        logger.error(f"Error updating address {address_id} for user {current_user.id}: {e}")
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to update address"
        )


@router.delete("/addresses/{address_id}")
async def delete_user_address(
    address_id: UUID,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete address for current user (requires authentication)"""
    try:
        service = AddressService(db)
        # Verify the address belongs to current user
        address = await service.get_address_by_id(address_id)
        if not address or address.user_id != current_user.id:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Address not found"
            )
        deleted = await service.delete_address(address_id)
        if not deleted:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Address not found"
            )
        return Response.success(message="Address deleted successfully")
    except APIException:
        raise
    except Exception as e:
        logger.error(f"Error deleting address {address_id}: {e}")
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to delete address"
        )

