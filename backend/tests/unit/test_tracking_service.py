"""
Unit tests for variant tracking service
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from decimal import Decimal
from uuid import uuid4
from datetime import datetime, timedelta

from services.tracking import VariantTrackingService
from models.variant_tracking import (
    VariantTrackingEntry, VariantPriceHistory, 
    VariantAnalytics, VariantSubstitution
)
from core.errors import APIException


class TestVariantTrackingService:
    
    @pytest_asyncio.fixture
    async def tracking_service(self, db_session):
        return VariantTrackingService(db_session)
    
    @pytest.mark.asyncio
    async def test_track_variant_subscription_addition_success(
        self, tracking_service, test_product, test_subscription
    ):
        """Test successful variant tracking for subscription addition"""
        product, variant = test_product
        
        tracking_entry = await tracking_service.track_variant_subscription_addition(
            variant_id=variant.id,
            subscription_id=test_subscription.id,
            price_at_time=99.99,
            currency="USD",
            metadata={"source": "web", "campaign": "summer_sale"}
        )
        
        assert tracking_entry.variant_id == variant.id
        assert tracking_entry.subscription_id == test_subscription.id
        assert tracking_entry.price_at_time == Decimal("99.99")
        assert tracking_entry.currency == "USD"
        assert tracking_entry.metadata["source"] == "web"
        assert tracking_entry.created_at is not None
    
    @pytest.mark.asyncio
    async def test_track_variant_subscription_addition_invalid_variant(
        self, tracking_service, test_subscription
    ):
        """Test tracking with invalid variant ID"""
        invalid_variant_id = uuid4()
        
        with pytest.raises(APIException) as exc_info:
            await tracking_service.track_variant_subscription_addition(
                variant_id=invalid_variant_id,
                subscription_id=test_subscription.id,
                price_at_time=99.99
            )
        
        assert exc_info.value.status_code == 404
        assert "variant not found" in str(exc_info.value.message).lower()
    
    @pytest.mark.asyncio
    async def test_track_variant_subscription_addition_invalid_subscription(
        self, tracking_service, test_product
    ):
        """Test tracking with invalid subscription ID"""
        product, variant = test_product
        invalid_subscription_id = uuid4()
        
        with pytest.raises(APIException) as exc_info:
            await tracking_service.track_variant_subscription_addition(
                variant_id=variant.id,
                subscription_id=invalid_subscription_id,
                price_at_time=99.99
            )
        
        assert exc_info.value.status_code == 404
        assert "subscription not found" in str(exc_info.value.message).lower()
    
    @pytest.mark.asyncio
    async def test_track_price_change(self, tracking_service, test_product):
        """Test tracking variant price changes"""
        product, variant = test_product
        old_price = variant.price
        new_price = Decimal("149.99")
        
        price_history = await tracking_service.track_price_change(
            variant_id=variant.id,
            old_price=old_price,
            new_price=new_price,
            reason="market_adjustment",
            changed_by=uuid4()
        )
        
        assert price_history.variant_id == variant.id
        assert price_history.old_price == old_price
        assert price_history.new_price == new_price
        assert price_history.reason == "market_adjustment"
        assert price_history.changed_at is not None
    
    @pytest.mark.asyncio
    async def test_get_variant_analytics(self, tracking_service, test_product, test_subscription):
        """Test getting variant analytics"""
        product, variant = test_product
        
        # Create some tracking entries
        for i in range(5):
            await tracking_service.track_variant_subscription_addition(
                variant_id=variant.id,
                subscription_id=test_subscription.id,
                price_at_time=99.99 + i,
                currency="USD"
            )
        
        analytics = await tracking_service.get_variant_analytics(
            variant_id=variant.id,
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow()
        )
        
        assert analytics.variant_id == variant.id
        assert analytics.total_subscriptions >= 5
        assert analytics.average_price > 0
        assert analytics.total_revenue > 0
    
    @pytest.mark.asyncio
    async def test_get_price_history(self, tracking_service, test_product):
        """Test getting variant price history"""
        product, variant = test_product
        
        # Create price history entries
        prices = [Decimal("99.99"), Decimal("109.99"), Decimal("119.99")]
        for i, price in enumerate(prices[1:], 1):
            await tracking_service.track_price_change(
                variant_id=variant.id,
                old_price=prices[i-1],
                new_price=price,
                reason="price_increase",
                changed_by=uuid4()
            )
        
        price_history = await tracking_service.get_price_history(
            variant_id=variant.id,
            limit=10
        )
        
        assert len(price_history) >= 2
        assert all(ph.variant_id == variant.id for ph in price_history)
        # Should be ordered by date descending
        assert price_history[0].changed_at >= price_history[1].changed_at
    
    @pytest.mark.asyncio
    async def test_calculate_variant_performance(self, tracking_service, test_product, test_subscription):
        """Test calculating variant performance metrics"""
        product, variant = test_product
        
        # Create tracking data
        for i in range(10):
            await tracking_service.track_variant_subscription_addition(
                variant_id=variant.id,
                subscription_id=test_subscription.id,
                price_at_time=100.0 + (i * 5),  # Increasing prices
                currency="USD"
            )
        
        performance = await tracking_service.calculate_variant_performance(
            variant_id=variant.id,
            period_days=30
        )
        
        assert "subscription_count" in performance
        assert "revenue_total" in performance
        assert "average_price" in performance
        assert "price_trend" in performance
        assert performance["subscription_count"] == 10
        assert performance["revenue_total"] > 0
    
    @pytest.mark.asyncio
    async def test_find_variant_substitutions(self, tracking_service, test_product, db_session):
        """Test finding variant substitutions"""
        product, variant = test_product
        
        # Create a substitute variant
        substitute_variant = ProductVariant(
            id=uuid4(),
            product_id=product.id,
            name="Substitute Variant",
            price=Decimal("89.99"),
            cost=Decimal("45.00"),
            sku="SUB-001",
            is_active=True
        )
        db_session.add(substitute_variant)
        await db_session.commit()
        
        # Create substitution record
        substitution = VariantSubstitution(
            id=uuid4(),
            original_variant_id=variant.id,
            substitute_variant_id=substitute_variant.id,
            reason="out_of_stock",
            confidence_score=0.85,
            created_at=datetime.utcnow()
        )
        tracking_service.db.add(substitution)
        await tracking_service.db.commit()
        
        substitutions = await tracking_service.find_variant_substitutions(variant.id)
        
        assert len(substitutions) == 1
        assert substitutions[0].original_variant_id == variant.id
        assert substitutions[0].substitute_variant_id == substitute_variant.id
        assert substitutions[0].confidence_score == 0.85
    
    @pytest.mark.asyncio
    async def test_track_variant_view(self, tracking_service, test_product):
        """Test tracking variant views"""
        product, variant = test_product
        user_id = uuid4()
        
        view_entry = await tracking_service.track_variant_view(
            variant_id=variant.id,
            user_id=user_id,
            source="product_page",
            metadata={"referrer": "search", "device": "mobile"}
        )
        
        assert view_entry.variant_id == variant.id
        assert view_entry.user_id == user_id
        assert view_entry.source == "product_page"
        assert view_entry.metadata["referrer"] == "search"
    
    @pytest.mark.asyncio
    async def test_get_trending_variants(self, tracking_service, test_product, test_subscription):
        """Test getting trending variants"""
        product, variant = test_product
        
        # Create recent tracking entries to make variant trending
        for i in range(20):
            await tracking_service.track_variant_subscription_addition(
                variant_id=variant.id,
                subscription_id=test_subscription.id,
                price_at_time=99.99,
                currency="USD"
            )
        
        trending_variants = await tracking_service.get_trending_variants(
            limit=10,
            period_hours=24
        )
        
        assert len(trending_variants) >= 1
        assert any(tv["variant_id"] == variant.id for tv in trending_variants)
        assert all("trend_score" in tv for tv in trending_variants)
    
    @pytest.mark.asyncio
    async def test_calculate_conversion_rate(self, tracking_service, test_product):
        """Test calculating variant conversion rates"""
        product, variant = test_product
        user_id = uuid4()
        
        # Track views
        for i in range(10):
            await tracking_service.track_variant_view(
                variant_id=variant.id,
                user_id=user_id,
                source="product_page"
            )
        
        # Track conversions (subscriptions)
        for i in range(3):
            await tracking_service.track_variant_subscription_addition(
                variant_id=variant.id,
                subscription_id=uuid4(),
                price_at_time=99.99
            )
        
        conversion_rate = await tracking_service.calculate_conversion_rate(
            variant_id=variant.id,
            period_days=7
        )
        
        assert 0 <= conversion_rate <= 1
        # Should be around 0.3 (3 conversions / 10 views)
        assert abs(conversion_rate - 0.3) < 0.1
    
    @pytest.mark.asyncio
    async def test_get_variant_cohort_analysis(self, tracking_service, test_product, test_subscription):
        """Test variant cohort analysis"""
        product, variant = test_product
        
        # Create tracking entries over different time periods
        base_date = datetime.utcnow() - timedelta(days=30)
        for week in range(4):
            for day in range(7):
                date = base_date + timedelta(weeks=week, days=day)
                with patch('services.tracking.datetime') as mock_datetime:
                    mock_datetime.utcnow.return_value = date
                    await tracking_service.track_variant_subscription_addition(
                        variant_id=variant.id,
                        subscription_id=test_subscription.id,
                        price_at_time=99.99,
                        currency="USD"
                    )
        
        cohort_analysis = await tracking_service.get_variant_cohort_analysis(
            variant_id=variant.id,
            cohort_period="weekly"
        )
        
        assert "cohorts" in cohort_analysis
        assert len(cohort_analysis["cohorts"]) > 0
        assert all("period" in cohort for cohort in cohort_analysis["cohorts"])
        assert all("subscription_count" in cohort for cohort in cohort_analysis["cohorts"])
    
    @pytest.mark.asyncio
    async def test_export_tracking_data(self, tracking_service, test_product, test_subscription):
        """Test exporting tracking data"""
        product, variant = test_product
        
        # Create some tracking data
        for i in range(5):
            await tracking_service.track_variant_subscription_addition(
                variant_id=variant.id,
                subscription_id=test_subscription.id,
                price_at_time=99.99 + i,
                currency="USD"
            )
        
        export_data = await tracking_service.export_tracking_data(
            variant_id=variant.id,
            start_date=datetime.utcnow() - timedelta(days=7),
            end_date=datetime.utcnow(),
            format="json"
        )
        
        assert "tracking_entries" in export_data
        assert "price_history" in export_data
        assert "analytics_summary" in export_data
        assert len(export_data["tracking_entries"]) >= 5
    
    @pytest.mark.asyncio
    async def test_bulk_track_variants(self, tracking_service, test_product, test_subscription):
        """Test bulk tracking of multiple variants"""
        product, variant = test_product
        
        tracking_data = [
            {
                "variant_id": variant.id,
                "subscription_id": test_subscription.id,
                "price_at_time": 99.99,
                "currency": "USD"
            },
            {
                "variant_id": variant.id,
                "subscription_id": test_subscription.id,
                "price_at_time": 109.99,
                "currency": "USD"
            }
        ]
        
        tracking_entries = await tracking_service.bulk_track_variants(tracking_data)
        
        assert len(tracking_entries) == 2
        assert all(entry.variant_id == variant.id for entry in tracking_entries)
        assert tracking_entries[0].price_at_time == Decimal("99.99")
        assert tracking_entries[1].price_at_time == Decimal("109.99")
    
    @pytest.mark.asyncio
    async def test_get_variant_recommendations(self, tracking_service, test_product):
        """Test getting variant recommendations based on tracking data"""
        product, variant = test_product
        
        # Mock recommendation algorithm
        with patch.object(tracking_service, '_calculate_recommendations') as mock_calc:
            mock_calc.return_value = [
                {
                    "variant_id": variant.id,
                    "recommendation_type": "price_optimization",
                    "suggested_price": Decimal("119.99"),
                    "confidence": 0.85,
                    "reason": "High demand, low price sensitivity"
                }
            ]
            
            recommendations = await tracking_service.get_variant_recommendations(
                variant_id=variant.id
            )
            
            assert len(recommendations) == 1
            assert recommendations[0]["variant_id"] == variant.id
            assert recommendations[0]["recommendation_type"] == "price_optimization"
            assert recommendations[0]["confidence"] == 0.85