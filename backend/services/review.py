from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc
from typing import Optional, List
from models.review import Review
from models.product import Product
from models.user import User
from schemas.review import ReviewCreate, ReviewUpdate, ReviewResponse
from lib.errors import APIException
from lib.utils.uuid_utils import uuid7
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import selectinload, load_only


class ReviewService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_review(self, review_data: ReviewCreate, user_id: UUID) -> Review:
        # Check if product exists
        product = await self.db.get(Product, review_data.product_id)
        if not product:
            raise APIException(status_code=404, message="Product not found")

        # Check if user has already reviewed this product
        existing_review = await self.db.execute(
            select(Review).filter_by(
                product_id=review_data.product_id, user_id=user_id)
        )
        if existing_review.scalars().first():
            raise APIException(
                status_code=400, detail="You have already reviewed this product")

        new_review = Review(
            id=uuid7(),
            user_id=user_id,
            **review_data.dict(exclude_unset=True)
        )
        self.db.add(new_review)
        await self.db.commit()
        await self.db.refresh(new_review)

        # Update product rating and review count
        await self._update_product_rating(review_data.product_id)

        return new_review

    async def get_reviews_for_product(self, product_id: UUID, page: int = 1, limit: int = 10, min_rating: Optional[int] = None, max_rating: Optional[int] = None, sort_by: Optional[str] = None) -> dict:
        offset = (page - 1) * limit
        query = select(Review).filter_by(product_id=product_id).options(
            selectinload(Review.user).load_only(
                User.id, User.firstname, User.lastname)
        )
        total_query = select(func.count()).select_from(
            Review).filter_by(product_id=product_id)

        if min_rating is not None:
            query = query.filter(Review.rating >= min_rating)
            total_query = total_query.filter(Review.rating >= min_rating)
        if max_rating is not None:
            query = query.filter(Review.rating <= max_rating)
            total_query = total_query.filter(Review.rating <= max_rating)

        if sort_by:
            sort_field, sort_order = sort_by.split('_')
            if sort_order == 'asc':
                query = query.order_by(getattr(Review, sort_field).asc())
            else:
                query = query.order_by(getattr(Review, sort_field).desc())
        else:
            query = query.order_by(desc(Review.created_at))

        total_reviews = (await self.db.execute(total_query)).scalar_one()
        reviews = (await self.db.execute(query.offset(offset).limit(limit))).scalars().all()

        return {
            "total": total_reviews,
            "page": page,
            "limit": limit,
            "data": [ReviewResponse.from_orm(r) for r in reviews]
        }

    async def get_review_by_id(self, review_id: UUID) -> Optional[Review]:
        result = await self.db.execute(select(Review).filter_by(id=review_id))
        return result.scalars().first()

    async def update_review(self, review_id: UUID, review_data: ReviewUpdate, user_id: UUID) -> Review:
        review = await self.get_review_by_id(review_id)
        if not review:
            raise APIException(status_code=404, message="Review not found")

        if review.user_id != user_id:
            raise APIException(
                status_code=403, message="Not authorized to update this review")

        for key, value in review_data.dict(exclude_unset=True).items():
            setattr(review, key, value)
        review.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(review)

        # Update product rating
        await self._update_product_rating(review.product_id)

        return review

    async def delete_review(self, review_id: UUID, user_id: UUID):
        review = await self.get_review_by_id(review_id)
        if not review:
            raise APIException(status_code=404, message="Review not found")

        if review.user_id != user_id:
            raise APIException(
                status_code=403, message="Not authorized to delete this review")

        await self.db.delete(review)
        await self.db.commit()

        # Update product rating
        await self._update_product_rating(review.product_id)

    async def _update_product_rating(self, product_id: UUID):
        # Calculate new average rating and count
        result = await self.db.execute(
            select(func.avg(Review.rating), func.count(Review.id))
            .filter_by(product_id=product_id)
        )
        avg_rating, review_count = result.first()

        product = await self.db.get(Product, product_id)
        if product:
            product.rating = avg_rating if avg_rating is not None else 0.0
            product.review_count = review_count if review_count is not None else 0
            product.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(product)