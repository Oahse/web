from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc, text
from sqlalchemy.orm import selectinload, joinedload
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal
import statistics
import json
import asyncio

from models.inventory import Inventory, WarehouseLocation, StockAdjustment
from models.product import ProductVariant, Product
from models.subscription import Subscription
from models.variant_tracking import VariantTrackingEntry, VariantAnalytics, VariantSubstitution
from services.inventory import InventoryService
from services.variant_tracking import VariantTrackingService
# from services.notification import NotificationService  # Commented out to avoid circular imports
from core.exceptions import APIException
from core.utils.logging import structured_logger


class EnhancedInventoryIntegrationService:
    """
    Enhanced inventory management integration with advanced demand prediction,
    automated reorder suggestions, and supplier system integration.
    
    Requirements: 14.2, 14.5, 14.6, 14.7
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.inventory_service = InventoryService(db)
        self.variant_tracking_service = VariantTrackingService(db)
        # self.notification_service = NotificationService(db)  # Commented out to avoid circular imports

    # ============================================================================
    # DEMAND PREDICTION BASED ON REAL SUBSCRIPTION PATTERNS
    # ============================================================================

    async def predict_demand_based_on_subscription_patterns(
        self,
        variant_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        forecast_days: int = 30,
        confidence_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Predict demand based on real subscription patterns using advanced analytics.
        
        Requirements: 14.2
        
        Args:
            variant_id: Specific variant to analyze (None for all variants)
            location_id: Specific location to analyze (None for all locations)
            forecast_days: Number of days to forecast ahead
            confidence_threshold: Minimum confidence level for predictions
            
        Returns:
            Dict with demand predictions and analytics
        """
        try:
            # Get historical subscription data for analysis
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=180)  # Use 6 months of history
            
            # Build query for variant tracking entries
            tracking_query = select(VariantTrackingEntry).options(
                joinedload(VariantTrackingEntry.variant).joinedload(ProductVariant.product),
                joinedload(VariantTrackingEntry.subscription)
            ).where(
                and_(
                    VariantTrackingEntry.tracking_timestamp >= start_date,
                    VariantTrackingEntry.tracking_timestamp <= end_date
                )
            )
            
            if variant_id:
                tracking_query = tracking_query.where(VariantTrackingEntry.variant_id == variant_id)
            
            tracking_result = await self.db.execute(tracking_query)
            tracking_entries = tracking_result.scalars().all()
            
            # Get active subscriptions for current demand baseline
            active_subscriptions_query = select(Subscription).where(
                Subscription.status.in_(["active", "trialing"])
            )
            
            if variant_id:
                active_subscriptions_query = active_subscriptions_query.where(
                    Subscription.variant_ids.contains([str(variant_id)])
                )
            
            active_subscriptions_result = await self.db.execute(active_subscriptions_query)
            active_subscriptions = active_subscriptions_result.scalars().all()
            
            # Analyze subscription patterns by variant
            variant_predictions = {}
            
            # Group tracking entries by variant
            entries_by_variant = {}
            for entry in tracking_entries:
                v_id = str(entry.variant_id)
                if v_id not in entries_by_variant:
                    entries_by_variant[v_id] = []
                entries_by_variant[v_id].append(entry)
            
            # Analyze each variant
            for v_id, entries in entries_by_variant.items():
                variant_prediction = await self._analyze_variant_demand_pattern(
                    UUID(v_id), entries, active_subscriptions, forecast_days
                )
                
                # Only include predictions with sufficient confidence
                if variant_prediction["confidence_level"] >= confidence_threshold:
                    variant_predictions[v_id] = variant_prediction
            
            # Calculate aggregate predictions
            total_predicted_demand = sum(
                pred["predicted_demand"] for pred in variant_predictions.values()
            )
            
            average_confidence = (
                sum(pred["confidence_level"] for pred in variant_predictions.values()) / 
                len(variant_predictions) if variant_predictions else 0.0
            )
            
            # Get current inventory levels for comparison
            inventory_levels = await self._get_current_inventory_levels(
                variant_ids=[UUID(v_id) for v_id in variant_predictions.keys()],
                location_id=location_id
            )
            
            # Generate recommendations
            recommendations = await self._generate_demand_based_recommendations(
                variant_predictions, inventory_levels, forecast_days
            )
            
            structured_logger.info(
                message="Demand prediction completed",
                metadata={
                    "variants_analyzed": len(variant_predictions),
                    "forecast_days": forecast_days,
                    "total_predicted_demand": total_predicted_demand,
                    "average_confidence": round(average_confidence, 3)
                }
            )
            
            return {
                "analysis_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "forecast_days": forecast_days,
                    "confidence_threshold": confidence_threshold
                },
                "summary": {
                    "variants_analyzed": len(variant_predictions),
                    "total_predicted_demand": total_predicted_demand,
                    "average_confidence_level": round(average_confidence, 3),
                    "high_confidence_predictions": len([
                        p for p in variant_predictions.values() 
                        if p["confidence_level"] >= 0.8
                    ])
                },
                "variant_predictions": variant_predictions,
                "inventory_comparison": inventory_levels,
                "recommendations": recommendations,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            structured_logger.error(
                message="Failed to predict demand based on subscription patterns",
                metadata={
                    "variant_id": str(variant_id) if variant_id else None,
                    "location_id": str(location_id) if location_id else None,
                    "forecast_days": forecast_days
                },
                exception=e
            )
            raise APIException(
                status_code=500,
                message="Failed to generate demand predictions"
            )

    async def _analyze_variant_demand_pattern(
        self,
        variant_id: UUID,
        tracking_entries: List[VariantTrackingEntry],
        active_subscriptions: List[Subscription],
        forecast_days: int
    ) -> Dict[str, Any]:
        """Analyze demand pattern for a specific variant"""
        
        # Separate additions and removals by time period
        additions_by_week = {}
        removals_by_week = {}
        price_changes = []
        
        for entry in tracking_entries:
            week_key = entry.tracking_timestamp.strftime("%Y-W%U")
            
            if entry.action_type == "added":
                additions_by_week[week_key] = additions_by_week.get(week_key, 0) + 1
            elif entry.action_type == "removed":
                removals_by_week[week_key] = removals_by_week.get(week_key, 0) + 1
            elif entry.action_type == "price_changed":
                price_changes.append({
                    "date": entry.tracking_timestamp,
                    "price": entry.price_at_time
                })
        
        # Calculate weekly net demand
        all_weeks = sorted(set(additions_by_week.keys()) | set(removals_by_week.keys()))
        weekly_net_demands = []
        
        for week in all_weeks:
            additions = additions_by_week.get(week, 0)
            removals = removals_by_week.get(week, 0)
            net_demand = additions - removals
            weekly_net_demands.append(net_demand)
        
        # Calculate trend and seasonality
        if len(weekly_net_demands) >= 4:
            # Simple linear trend calculation
            weeks_numeric = list(range(len(weekly_net_demands)))
            trend_slope = self._calculate_linear_trend(weeks_numeric, weekly_net_demands)
            
            # Calculate seasonal patterns (if enough data)
            seasonal_factor = self._calculate_seasonal_factor(weekly_net_demands)
        else:
            trend_slope = 0
            seasonal_factor = 1.0
        
        # Calculate base demand from current active subscriptions
        current_active_count = len([
            sub for sub in active_subscriptions 
            if str(variant_id) in (sub.variant_ids or [])
        ])
        
        # Calculate average weekly demand
        avg_weekly_demand = sum(weekly_net_demands) / len(weekly_net_demands) if weekly_net_demands else 0
        
        # Project future demand
        forecast_weeks = forecast_days / 7
        
        # Apply trend and seasonal adjustments
        base_forecast = avg_weekly_demand * forecast_weeks
        trend_adjustment = trend_slope * forecast_weeks * (forecast_weeks / 2)  # Compound trend
        seasonal_adjustment = base_forecast * (seasonal_factor - 1.0)
        
        predicted_demand = max(0, int(base_forecast + trend_adjustment + seasonal_adjustment))
        
        # Calculate confidence level
        confidence_level = self._calculate_prediction_confidence(
            weekly_net_demands, len(tracking_entries), current_active_count
        )
        
        # Get variant details
        variant_query = select(ProductVariant).options(
            joinedload(ProductVariant.product)
        ).where(ProductVariant.id == variant_id)
        variant_result = await self.db.execute(variant_query)
        variant = variant_result.scalar_one_or_none()
        
        return {
            "variant_id": str(variant_id),
            "variant_name": variant.name if variant else None,
            "product_name": variant.product.name if variant and variant.product else None,
            "historical_analysis": {
                "weeks_analyzed": len(all_weeks),
                "total_additions": sum(additions_by_week.values()),
                "total_removals": sum(removals_by_week.values()),
                "avg_weekly_net_demand": round(avg_weekly_demand, 2),
                "trend_slope": round(trend_slope, 4),
                "seasonal_factor": round(seasonal_factor, 3)
            },
            "current_state": {
                "active_subscriptions": current_active_count,
                "recent_price_changes": len(price_changes)
            },
            "prediction": {
                "predicted_demand": predicted_demand,
                "forecast_period_days": forecast_days,
                "base_forecast": round(base_forecast, 2),
                "trend_adjustment": round(trend_adjustment, 2),
                "seasonal_adjustment": round(seasonal_adjustment, 2),
                "confidence_level": round(confidence_level, 3)
            }
        }

    def _calculate_linear_trend(self, x_values: List[int], y_values: List[float]) -> float:
        """Calculate linear trend slope using least squares method"""
        if len(x_values) < 2:
            return 0.0
        
        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x_squared = sum(x * x for x in x_values)
        
        denominator = n * sum_x_squared - sum_x * sum_x
        if denominator == 0:
            return 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        return slope

    def _calculate_seasonal_factor(self, weekly_demands: List[float]) -> float:
        """Calculate seasonal adjustment factor"""
        if len(weekly_demands) < 8:  # Need at least 8 weeks for seasonal analysis
            return 1.0
        
        # Simple seasonal calculation - compare recent weeks to historical average
        recent_weeks = weekly_demands[-4:]  # Last 4 weeks
        historical_avg = sum(weekly_demands[:-4]) / len(weekly_demands[:-4]) if len(weekly_demands) > 4 else 0
        recent_avg = sum(recent_weeks) / len(recent_weeks)
        
        if historical_avg == 0:
            return 1.0
        
        seasonal_factor = recent_avg / historical_avg
        # Cap seasonal factor to reasonable bounds
        return max(0.5, min(2.0, seasonal_factor))

    def _calculate_prediction_confidence(
        self,
        weekly_demands: List[float],
        total_data_points: int,
        current_active_count: int
    ) -> float:
        """Calculate confidence level for demand prediction"""
        
        # Base confidence on data availability
        data_confidence = min(1.0, total_data_points / 50)  # Full confidence at 50+ data points
        
        # Confidence based on data consistency
        if len(weekly_demands) > 1:
            demand_std = statistics.stdev(weekly_demands)
            demand_mean = statistics.mean(weekly_demands)
            
            if demand_mean != 0:
                coefficient_of_variation = demand_std / abs(demand_mean)
                consistency_confidence = max(0.1, 1.0 - min(1.0, coefficient_of_variation))
            else:
                consistency_confidence = 0.5
        else:
            consistency_confidence = 0.3
        
        # Confidence based on current activity
        activity_confidence = min(1.0, current_active_count / 10)  # Full confidence at 10+ active subscriptions
        
        # Weighted average of confidence factors
        overall_confidence = (
            data_confidence * 0.4 +
            consistency_confidence * 0.4 +
            activity_confidence * 0.2
        )
        
        return max(0.1, min(1.0, overall_confidence))

    # ============================================================================
    # REORDER SUGGESTIONS BASED ON ACTUAL CONSUMPTION RATES
    # ============================================================================

    async def generate_reorder_suggestions_based_on_consumption(
        self,
        location_id: Optional[UUID] = None,
        days_ahead: int = 30,
        include_seasonal_adjustments: bool = True,
        min_confidence_level: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        Generate reorder suggestions based on actual consumption rates and demand predictions.
        
        Requirements: 14.5
        
        Args:
            location_id: Specific warehouse location (None for all locations)
            days_ahead: Forecast period for reorder calculations
            include_seasonal_adjustments: Whether to apply seasonal demand adjustments
            min_confidence_level: Minimum confidence level for recommendations
            
        Returns:
            List of reorder suggestions with detailed analytics
        """
        try:
            # Get all inventory items that might need analysis
            inventory_query = select(Inventory).options(
                joinedload(Inventory.variant).joinedload(ProductVariant.product),
                joinedload(Inventory.location)
            )
            
            if location_id:
                inventory_query = inventory_query.where(Inventory.location_id == location_id)
            
            inventory_result = await self.db.execute(inventory_query)
            inventory_items = inventory_result.scalars().all()
            
            reorder_suggestions = []
            
            # Analyze each inventory item
            for item in inventory_items:
                try:
                    suggestion = await self._generate_variant_reorder_suggestion(
                        item, days_ahead, include_seasonal_adjustments, min_confidence_level
                    )
                    
                    if suggestion and suggestion.get("needs_reorder", False):
                        reorder_suggestions.append(suggestion)
                        
                except Exception as e:
                    structured_logger.warning(
                        message="Failed to generate reorder suggestion for variant",
                        metadata={
                            "variant_id": str(item.variant_id),
                            "inventory_id": str(item.id)
                        },
                        exception=e
                    )
                    continue
            
            # Sort suggestions by priority
            reorder_suggestions.sort(key=lambda x: (
                self._get_urgency_score(x["urgency"]),
                x.get("days_until_stockout", 999),
                -x.get("predicted_revenue_impact", 0)
            ))
            
            # Calculate summary statistics
            total_suggested_investment = sum(
                s.get("suggested_order_value", 0) for s in reorder_suggestions
            )
            
            high_urgency_count = len([s for s in reorder_suggestions if s.get("urgency") == "high"])
            
            structured_logger.info(
                message="Reorder suggestions generated",
                metadata={
                    "total_suggestions": len(reorder_suggestions),
                    "high_urgency_count": high_urgency_count,
                    "total_suggested_investment": total_suggested_investment,
                    "location_id": str(location_id) if location_id else "all_locations"
                }
            )
            
            return reorder_suggestions
            
        except Exception as e:
            structured_logger.error(
                message="Failed to generate reorder suggestions",
                metadata={
                    "location_id": str(location_id) if location_id else None,
                    "days_ahead": days_ahead
                },
                exception=e
            )
            raise APIException(
                status_code=500,
                message="Failed to generate reorder suggestions"
            )

    async def _generate_variant_reorder_suggestion(
        self,
        inventory_item: Inventory,
        days_ahead: int,
        include_seasonal_adjustments: bool,
        min_confidence_level: float
    ) -> Optional[Dict[str, Any]]:
        """Generate reorder suggestion for a specific variant"""
        
        # Get demand prediction for this variant
        demand_prediction = await self.predict_demand_based_on_subscription_patterns(
            variant_id=inventory_item.variant_id,
            forecast_days=days_ahead,
            confidence_threshold=min_confidence_level
        )
        
        variant_prediction = demand_prediction["variant_predictions"].get(
            str(inventory_item.variant_id)
        )
        
        if not variant_prediction:
            return None
        
        # Get consumption rate from stock adjustments
        consumption_analysis = await self._analyze_consumption_rate(
            inventory_item.id, days_ahead
        )
        
        # Calculate reorder parameters
        current_stock = inventory_item.quantity
        low_stock_threshold = inventory_item.low_stock_threshold
        
        # Predicted demand from subscription patterns
        predicted_subscription_demand = variant_prediction["prediction"]["predicted_demand"]
        
        # Historical consumption rate
        daily_consumption_rate = consumption_analysis["daily_consumption_rate"]
        predicted_consumption_demand = daily_consumption_rate * days_ahead
        
        # Use the higher of the two predictions for safety
        total_predicted_demand = max(predicted_subscription_demand, predicted_consumption_demand)
        
        # Apply seasonal adjustments if requested
        if include_seasonal_adjustments:
            seasonal_factor = variant_prediction["historical_analysis"]["seasonal_factor"]
            total_predicted_demand = int(total_predicted_demand * seasonal_factor)
        
        # Calculate reorder point and quantity
        lead_time_days = 7  # Default lead time (could be configurable per supplier)
        safety_stock = max(low_stock_threshold, int(daily_consumption_rate * lead_time_days))
        
        reorder_point = int((daily_consumption_rate * lead_time_days) + safety_stock)
        
        # Determine if reorder is needed
        needs_reorder = current_stock <= reorder_point or current_stock < total_predicted_demand
        
        if not needs_reorder:
            return None
        
        # Calculate suggested order quantity using Economic Order Quantity (EOQ) principles
        suggested_quantity = max(
            int(total_predicted_demand + safety_stock - current_stock),
            low_stock_threshold * 2,  # Minimum order
            int(daily_consumption_rate * 14)  # At least 2 weeks supply
        )
        
        # Determine urgency
        days_until_stockout = (
            int(current_stock / daily_consumption_rate) 
            if daily_consumption_rate > 0 else 999
        )
        
        if current_stock <= 0:
            urgency = "critical"
        elif days_until_stockout <= 3:
            urgency = "high"
        elif days_until_stockout <= 7:
            urgency = "medium"
        else:
            urgency = "low"
        
        # Calculate financial impact
        variant_price = inventory_item.variant.current_price if inventory_item.variant else 0
        suggested_order_value = suggested_quantity * variant_price
        
        # Estimate revenue impact of stockout
        avg_subscription_value = variant_prediction.get("historical_analysis", {}).get("avg_weekly_net_demand", 0) * variant_price
        potential_revenue_loss = avg_subscription_value * max(0, days_until_stockout - lead_time_days)
        
        return {
            "variant_id": str(inventory_item.variant_id),
            "variant_name": inventory_item.variant.name if inventory_item.variant else None,
            "product_name": inventory_item.variant.product.name if inventory_item.variant and inventory_item.variant.product else None,
            "location_id": str(inventory_item.location_id),
            "location_name": inventory_item.location.name if inventory_item.location else None,
            
            # Current state
            "current_stock": current_stock,
            "low_stock_threshold": low_stock_threshold,
            "reorder_point": reorder_point,
            
            # Demand analysis
            "predicted_demand": {
                "subscription_based": predicted_subscription_demand,
                "consumption_based": int(predicted_consumption_demand),
                "total_predicted": total_predicted_demand,
                "confidence_level": variant_prediction["prediction"]["confidence_level"]
            },
            
            # Consumption analysis
            "consumption_analysis": consumption_analysis,
            
            # Reorder recommendation
            "needs_reorder": needs_reorder,
            "suggested_quantity": suggested_quantity,
            "urgency": urgency,
            "days_until_stockout": days_until_stockout,
            
            # Financial impact
            "financial_analysis": {
                "unit_cost": variant_price,
                "suggested_order_value": suggested_order_value,
                "potential_revenue_loss": potential_revenue_loss,
                "predicted_revenue_impact": avg_subscription_value * days_ahead
            },
            
            # Timing
            "lead_time_days": lead_time_days,
            "safety_stock": safety_stock,
            "forecast_period_days": days_ahead,
            
            # Metadata
            "generated_at": datetime.utcnow().isoformat(),
            "seasonal_adjustment_applied": include_seasonal_adjustments
        }

    async def _analyze_consumption_rate(
        self,
        inventory_id: UUID,
        analysis_days: int = 30
    ) -> Dict[str, Any]:
        """Analyze historical consumption rate for an inventory item"""
        
        start_date = datetime.utcnow() - timedelta(days=analysis_days)
        
        # Get stock adjustments (outgoing stock only)
        adjustments_query = select(StockAdjustment).where(
            and_(
                StockAdjustment.inventory_id == inventory_id,
                StockAdjustment.quantity_change < 0,  # Only outgoing stock
                StockAdjustment.created_at >= start_date
            )
        ).order_by(StockAdjustment.created_at)
        
        adjustments_result = await self.db.execute(adjustments_query)
        adjustments = adjustments_result.scalars().all()
        
        # Calculate consumption metrics
        total_consumed = sum(abs(adj.quantity_change) for adj in adjustments)
        daily_consumption_rate = total_consumed / analysis_days if analysis_days > 0 else 0
        
        # Analyze consumption pattern consistency
        daily_consumption = {}
        for adj in adjustments:
            date_key = adj.created_at.date()
            daily_consumption[date_key] = daily_consumption.get(date_key, 0) + abs(adj.quantity_change)
        
        consumption_values = list(daily_consumption.values())
        consumption_consistency = 0.0
        
        if len(consumption_values) > 1:
            consumption_std = statistics.stdev(consumption_values)
            consumption_mean = statistics.mean(consumption_values)
            
            if consumption_mean > 0:
                coefficient_of_variation = consumption_std / consumption_mean
                consumption_consistency = max(0.0, 1.0 - min(1.0, coefficient_of_variation))
        
        return {
            "analysis_period_days": analysis_days,
            "total_consumed": total_consumed,
            "daily_consumption_rate": round(daily_consumption_rate, 2),
            "consumption_events": len(adjustments),
            "consumption_consistency": round(consumption_consistency, 3),
            "consumption_pattern": {
                "days_with_consumption": len(daily_consumption),
                "max_daily_consumption": max(consumption_values) if consumption_values else 0,
                "avg_daily_consumption": round(sum(consumption_values) / len(consumption_values), 2) if consumption_values else 0
            }
        }

    def _get_urgency_score(self, urgency: str) -> int:
        """Convert urgency level to numeric score for sorting"""
        urgency_scores = {
            "critical": 0,
            "high": 1,
            "medium": 2,
            "low": 3
        }
        return urgency_scores.get(urgency, 4)

    # ============================================================================
    # BATCH OPERATIONS FOR INVENTORY UPDATES USING REAL WAREHOUSE DATA
    # ============================================================================

    async def batch_update_inventory_from_warehouse_data(
        self,
        warehouse_data: List[Dict[str, Any]],
        source_system: str = "warehouse_management_system",
        validate_data: bool = True,
        create_audit_trail: bool = True
    ) -> Dict[str, Any]:
        """
        Batch update inventory from real warehouse data with comprehensive validation and audit trail.
        
        Requirements: 14.6
        
        Args:
            warehouse_data: List of inventory updates from warehouse system
            source_system: Name of the source system providing the data
            validate_data: Whether to validate data before processing
            create_audit_trail: Whether to create detailed audit trail
            
        Returns:
            Dict with batch update results and statistics
        """
        try:
            batch_start_time = datetime.utcnow()
            
            # Validate input data if requested
            if validate_data:
                validation_result = await self._validate_warehouse_data(warehouse_data)
                if not validation_result["is_valid"]:
                    raise APIException(
                        status_code=400,
                        message=f"Warehouse data validation failed: {validation_result['errors']}"
                    )
            
            # Process updates in batches for better performance
            batch_size = 100
            total_items = len(warehouse_data)
            processed_items = []
            failed_items = []
            
            for i in range(0, total_items, batch_size):
                batch = warehouse_data[i:i + batch_size]
                batch_result = await self._process_warehouse_data_batch(
                    batch, source_system, create_audit_trail
                )
                
                processed_items.extend(batch_result["processed"])
                failed_items.extend(batch_result["failed"])
            
            # Generate alerts for significant changes
            alerts_generated = await self._generate_batch_update_alerts(processed_items)
            
            # Create summary audit record
            if create_audit_trail:
                await self._create_batch_update_audit_record(
                    source_system, batch_start_time, processed_items, failed_items
                )
            
            # Calculate statistics
            total_processed = len(processed_items)
            total_failed = len(failed_items)
            success_rate = (total_processed / total_items) * 100 if total_items > 0 else 0
            
            # Analyze impact of updates
            impact_analysis = await self._analyze_batch_update_impact(processed_items)
            
            structured_logger.info(
                message="Batch inventory update completed",
                metadata={
                    "source_system": source_system,
                    "total_items": total_items,
                    "processed_items": total_processed,
                    "failed_items": total_failed,
                    "success_rate": round(success_rate, 2),
                    "alerts_generated": len(alerts_generated),
                    "processing_time_seconds": (datetime.utcnow() - batch_start_time).total_seconds()
                }
            )
            
            return {
                "batch_summary": {
                    "source_system": source_system,
                    "batch_start_time": batch_start_time.isoformat(),
                    "batch_end_time": datetime.utcnow().isoformat(),
                    "total_items": total_items,
                    "processed_successfully": total_processed,
                    "failed_items": total_failed,
                    "success_rate_percent": round(success_rate, 2)
                },
                "processed_items": processed_items,
                "failed_items": failed_items,
                "alerts_generated": alerts_generated,
                "impact_analysis": impact_analysis,
                "recommendations": await self._generate_post_batch_recommendations(impact_analysis)
            }
            
        except Exception as e:
            structured_logger.error(
                message="Failed to process batch inventory update",
                metadata={
                    "source_system": source_system,
                    "total_items": len(warehouse_data) if warehouse_data else 0
                },
                exception=e
            )
            raise APIException(
                status_code=500,
                message="Failed to process batch inventory update"
            )

    async def _validate_warehouse_data(
        self,
        warehouse_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate warehouse data before processing"""
        
        errors = []
        warnings = []
        
        required_fields = ["variant_id", "quantity"]
        optional_fields = ["location_id", "batch_number", "expiry_date", "cost_per_unit"]
        
        for i, item in enumerate(warehouse_data):
            item_errors = []
            
            # Check required fields
            for field in required_fields:
                if field not in item or item[field] is None:
                    item_errors.append(f"Missing required field: {field}")
            
            # Validate data types and values
            if "variant_id" in item:
                try:
                    UUID(str(item["variant_id"]))
                except ValueError:
                    item_errors.append("Invalid variant_id format")
            
            if "quantity" in item:
                try:
                    quantity = int(item["quantity"])
                    if quantity < 0:
                        warnings.append(f"Item {i}: Negative quantity ({quantity})")
                except (ValueError, TypeError):
                    item_errors.append("Invalid quantity format")
            
            if "location_id" in item and item["location_id"]:
                try:
                    UUID(str(item["location_id"]))
                except ValueError:
                    item_errors.append("Invalid location_id format")
            
            if item_errors:
                errors.append(f"Item {i}: {', '.join(item_errors)}")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "items_validated": len(warehouse_data)
        }

    async def _process_warehouse_data_batch(
        self,
        batch_data: List[Dict[str, Any]],
        source_system: str,
        create_audit_trail: bool
    ) -> Dict[str, Any]:
        """Process a batch of warehouse data updates"""
        
        processed = []
        failed = []
        
        for item_data in batch_data:
            try:
                # Extract item information
                variant_id = UUID(str(item_data["variant_id"]))
                new_quantity = int(item_data["quantity"])
                location_id = UUID(str(item_data["location_id"])) if item_data.get("location_id") else None
                
                # Find inventory item
                inventory_query = select(Inventory).where(Inventory.variant_id == variant_id)
                if location_id:
                    inventory_query = inventory_query.where(Inventory.location_id == location_id)
                
                inventory_result = await self.db.execute(inventory_query)
                inventory = inventory_result.scalar_one_or_none()
                
                if not inventory:
                    # Create new inventory item if it doesn't exist
                    if location_id:
                        inventory = Inventory(
                            variant_id=variant_id,
                            location_id=location_id,
                            quantity=new_quantity,
                            low_stock_threshold=10  # Default threshold
                        )
                        self.db.add(inventory)
                        await self.db.flush()  # Get the ID
                        
                        quantity_change = new_quantity
                        old_quantity = 0
                    else:
                        failed.append({
                            "variant_id": str(variant_id),
                            "error": "Inventory item not found and no location_id provided for creation"
                        })
                        continue
                else:
                    # Update existing inventory
                    old_quantity = inventory.quantity
                    quantity_change = new_quantity - old_quantity
                    inventory.quantity = new_quantity
                    inventory.updated_at = datetime.utcnow()
                
                # Create stock adjustment record
                adjustment = StockAdjustment(
                    inventory_id=inventory.id,
                    quantity_change=quantity_change,
                    reason=f"warehouse_sync_{source_system}",
                    notes=f"Batch update from {source_system}. Old: {old_quantity}, New: {new_quantity}"
                )
                
                # Add additional metadata if provided
                if item_data.get("batch_number"):
                    adjustment.notes += f", Batch: {item_data['batch_number']}"
                
                self.db.add(adjustment)
                
                processed_item = {
                    "variant_id": str(variant_id),
                    "location_id": str(inventory.location_id),
                    "old_quantity": old_quantity,
                    "new_quantity": new_quantity,
                    "quantity_change": quantity_change,
                    "adjustment_id": None,  # Will be set after commit
                    "processed_at": datetime.utcnow().isoformat(),
                    "metadata": {
                        "batch_number": item_data.get("batch_number"),
                        "cost_per_unit": item_data.get("cost_per_unit"),
                        "expiry_date": item_data.get("expiry_date")
                    }
                }
                
                processed.append(processed_item)
                
            except Exception as e:
                failed.append({
                    "variant_id": item_data.get("variant_id", "unknown"),
                    "error": str(e),
                    "item_data": item_data
                })
        
        # Commit the batch
        try:
            await self.db.commit()
            
            # Update adjustment IDs in processed items
            for item in processed:
                # This is a simplified approach - in production you'd want to track the actual adjustment IDs
                item["adjustment_id"] = "committed"
                
        except Exception as e:
            await self.db.rollback()
            # Move all processed items to failed
            for item in processed:
                failed.append({
                    "variant_id": item["variant_id"],
                    "error": f"Batch commit failed: {str(e)}",
                    "item_data": item
                })
            processed = []
        
        return {
            "processed": processed,
            "failed": failed
        }

    async def _generate_batch_update_alerts(
        self,
        processed_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate alerts for significant inventory changes"""
        
        alerts = []
        
        for item in processed_items:
            variant_id = UUID(item["variant_id"])
            old_quantity = item["old_quantity"]
            new_quantity = item["new_quantity"]
            quantity_change = item["quantity_change"]
            
            # Alert for significant quantity changes
            if old_quantity > 0:
                change_percentage = abs(quantity_change) / old_quantity
                if change_percentage > 0.5:  # More than 50% change
                    alerts.append({
                        "type": "significant_quantity_change",
                        "variant_id": str(variant_id),
                        "old_quantity": old_quantity,
                        "new_quantity": new_quantity,
                        "change_percentage": round(change_percentage * 100, 2),
                        "severity": "high" if change_percentage > 0.8 else "medium"
                    })
            
            # Alert for stockouts
            if new_quantity <= 0 and old_quantity > 0:
                alerts.append({
                    "type": "stockout",
                    "variant_id": str(variant_id),
                    "previous_quantity": old_quantity,
                    "severity": "critical"
                })
            
            # Alert for sudden stock increases (potential data errors)
            if quantity_change > old_quantity * 2 and old_quantity > 0:
                alerts.append({
                    "type": "unusual_stock_increase",
                    "variant_id": str(variant_id),
                    "old_quantity": old_quantity,
                    "new_quantity": new_quantity,
                    "severity": "medium"
                })
        
        return alerts

    # ============================================================================
    # SUPPLIER SYSTEM INTEGRATION FOR AUTOMATED PURCHASE ORDERS
    # ============================================================================

    async def integrate_with_supplier_systems_for_automated_orders(
        self,
        reorder_suggestions: Optional[List[Dict[str, Any]]] = None,
        auto_approve_threshold: float = 1000.0,
        supplier_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Integrate with supplier systems for automated purchase order generation.
        
        Requirements: 14.7
        
        Args:
            reorder_suggestions: List of reorder suggestions (if None, will generate new ones)
            auto_approve_threshold: Maximum order value for automatic approval
            supplier_preferences: Supplier-specific preferences and configurations
            
        Returns:
            Dict with purchase order results and supplier integration status
        """
        try:
            # Generate reorder suggestions if not provided
            if reorder_suggestions is None:
                reorder_suggestions = await self.generate_reorder_suggestions_based_on_consumption(
                    days_ahead=30,
                    min_confidence_level=0.7
                )
            
            # Group suggestions by supplier
            orders_by_supplier = await self._group_reorder_suggestions_by_supplier(
                reorder_suggestions, supplier_preferences or {}
            )
            
            purchase_orders = []
            integration_results = []
            
            # Process orders for each supplier
            for supplier_id, supplier_orders in orders_by_supplier.items():
                try:
                    po_result = await self._create_supplier_purchase_order(
                        supplier_id, supplier_orders, auto_approve_threshold
                    )
                    
                    purchase_orders.append(po_result)
                    
                    # Attempt to send order to supplier system
                    integration_result = await self._send_purchase_order_to_supplier(
                        supplier_id, po_result
                    )
                    
                    integration_results.append(integration_result)
                    
                except Exception as e:
                    structured_logger.error(
                        message="Failed to process supplier order",
                        metadata={
                            "supplier_id": supplier_id,
                            "order_count": len(supplier_orders)
                        },
                        exception=e
                    )
                    
                    integration_results.append({
                        "supplier_id": supplier_id,
                        "status": "failed",
                        "error": str(e),
                        "order_count": len(supplier_orders)
                    })
            
            # Calculate summary statistics
            total_orders = len(purchase_orders)
            total_value = sum(po.get("total_value", 0) for po in purchase_orders)
            auto_approved_orders = len([po for po in purchase_orders if po.get("auto_approved", False)])
            successful_integrations = len([ir for ir in integration_results if ir.get("status") == "success"])
            
            structured_logger.info(
                message="Supplier integration completed",
                metadata={
                    "total_purchase_orders": total_orders,
                    "total_order_value": total_value,
                    "auto_approved_orders": auto_approved_orders,
                    "successful_integrations": successful_integrations,
                    "suppliers_contacted": len(orders_by_supplier)
                }
            )
            
            return {
                "integration_summary": {
                    "total_purchase_orders": total_orders,
                    "total_order_value": total_value,
                    "auto_approved_orders": auto_approved_orders,
                    "manual_approval_required": total_orders - auto_approved_orders,
                    "successful_integrations": successful_integrations,
                    "failed_integrations": len(integration_results) - successful_integrations,
                    "suppliers_contacted": len(orders_by_supplier)
                },
                "purchase_orders": purchase_orders,
                "integration_results": integration_results,
                "reorder_suggestions_processed": len(reorder_suggestions),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            structured_logger.error(
                message="Failed to integrate with supplier systems",
                metadata={
                    "reorder_suggestions_count": len(reorder_suggestions) if reorder_suggestions else 0,
                    "auto_approve_threshold": auto_approve_threshold
                },
                exception=e
            )
            raise APIException(
                status_code=500,
                message="Failed to integrate with supplier systems"
            )

    async def _group_reorder_suggestions_by_supplier(
        self,
        reorder_suggestions: List[Dict[str, Any]],
        supplier_preferences: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group reorder suggestions by supplier"""
        
        orders_by_supplier = {}
        
        for suggestion in reorder_suggestions:
            variant_id = UUID(suggestion["variant_id"])
            
            # Get variant details to determine supplier
            variant_query = select(ProductVariant).options(
                joinedload(ProductVariant.product)
            ).where(ProductVariant.id == variant_id)
            variant_result = await self.db.execute(variant_query)
            variant = variant_result.scalar_one_or_none()
            
            if not variant:
                continue
            
            # Determine supplier (this would typically come from product/variant data)
            # For now, we'll use a simplified approach based on product category or default supplier
            supplier_id = self._determine_supplier_for_variant(variant, supplier_preferences)
            
            if supplier_id not in orders_by_supplier:
                orders_by_supplier[supplier_id] = []
            
            # Enhance suggestion with supplier-specific information
            enhanced_suggestion = {
                **suggestion,
                "supplier_id": supplier_id,
                "supplier_part_number": self._get_supplier_part_number(variant, supplier_id),
                "supplier_unit_cost": self._get_supplier_unit_cost(variant, supplier_id),
                "lead_time_days": self._get_supplier_lead_time(supplier_id, supplier_preferences)
            }
            
            orders_by_supplier[supplier_id].append(enhanced_suggestion)
        
        return orders_by_supplier

    def _determine_supplier_for_variant(
        self,
        variant: ProductVariant,
        supplier_preferences: Dict[str, Any]
    ) -> str:
        """Determine the best supplier for a variant"""
        
        # This is a simplified implementation
        # In a real system, this would involve complex supplier selection logic
        
        # Check if there's a preferred supplier for this product category
        if variant.product and variant.product.category:
            category_supplier = supplier_preferences.get("category_suppliers", {}).get(
                variant.product.category
            )
            if category_supplier:
                return category_supplier
        
        # Check for default supplier
        default_supplier = supplier_preferences.get("default_supplier")
        if default_supplier:
            return default_supplier
        
        # Fallback to a generic supplier ID
        return "default_supplier_001"

    def _get_supplier_part_number(self, variant: ProductVariant, supplier_id: str) -> str:
        """Get supplier-specific part number for variant"""
        # This would typically come from a supplier catalog or mapping table
        return f"{supplier_id}_{variant.sku}" if variant.sku else f"{supplier_id}_{variant.id}"

    def _get_supplier_unit_cost(self, variant: ProductVariant, supplier_id: str) -> float:
        """Get supplier-specific unit cost for variant"""
        # This would typically come from supplier pricing data
        # For now, use a percentage of the current price as cost
        base_price = variant.current_price or 0
        return base_price * 0.6  # Assume 60% of retail price as cost

    def _get_supplier_lead_time(self, supplier_id: str, supplier_preferences: Dict[str, Any]) -> int:
        """Get lead time for supplier"""
        supplier_lead_times = supplier_preferences.get("lead_times", {})
        return supplier_lead_times.get(supplier_id, 7)  # Default 7 days

    async def _create_supplier_purchase_order(
        self,
        supplier_id: str,
        supplier_orders: List[Dict[str, Any]],
        auto_approve_threshold: float
    ) -> Dict[str, Any]:
        """Create a purchase order for a supplier"""
        
        po_number = f"PO-{datetime.utcnow().strftime('%Y%m%d')}-{supplier_id[-4:]}"
        
        # Calculate order totals
        line_items = []
        total_quantity = 0
        total_value = 0.0
        
        for order in supplier_orders:
            quantity = order["suggested_quantity"]
            unit_cost = order["supplier_unit_cost"]
            line_total = quantity * unit_cost
            
            line_items.append({
                "variant_id": order["variant_id"],
                "variant_name": order["variant_name"],
                "supplier_part_number": order["supplier_part_number"],
                "quantity": quantity,
                "unit_cost": unit_cost,
                "line_total": line_total,
                "urgency": order["urgency"],
                "days_until_stockout": order.get("days_until_stockout")
            })
            
            total_quantity += quantity
            total_value += line_total
        
        # Determine if auto-approval is possible
        auto_approved = total_value <= auto_approve_threshold
        
        purchase_order = {
            "po_number": po_number,
            "supplier_id": supplier_id,
            "order_date": datetime.utcnow().isoformat(),
            "status": "approved" if auto_approved else "pending_approval",
            "auto_approved": auto_approved,
            "total_quantity": total_quantity,
            "total_value": total_value,
            "line_items": line_items,
            "delivery_requirements": {
                "requested_delivery_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "delivery_location": "primary_warehouse",  # This would be configurable
                "special_instructions": "Standard delivery terms"
            },
            "approval_threshold": auto_approve_threshold,
            "created_at": datetime.utcnow().isoformat()
        }
        
        return purchase_order

    async def _send_purchase_order_to_supplier(
        self,
        supplier_id: str,
        purchase_order: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send purchase order to supplier system"""
        
        try:
            # This is where you would integrate with actual supplier APIs
            # For now, we'll simulate the integration
            
            # Simulate API call delay
            await asyncio.sleep(0.1)
            
            # Simulate different response scenarios
            if supplier_id == "test_supplier_fail":
                raise Exception("Supplier API unavailable")
            
            # Simulate successful integration
            supplier_response = {
                "supplier_order_id": f"SUP-{purchase_order['po_number']}",
                "acknowledgment_date": datetime.utcnow().isoformat(),
                "estimated_delivery_date": (datetime.utcnow() + timedelta(days=10)).isoformat(),
                "order_status": "accepted",
                "total_confirmed": purchase_order["total_value"]
            }
            
            return {
                "supplier_id": supplier_id,
                "po_number": purchase_order["po_number"],
                "status": "success",
                "supplier_response": supplier_response,
                "integration_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "supplier_id": supplier_id,
                "po_number": purchase_order["po_number"],
                "status": "failed",
                "error": str(e),
                "integration_timestamp": datetime.utcnow().isoformat()
            }

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    async def _get_current_inventory_levels(
        self,
        variant_ids: List[UUID],
        location_id: Optional[UUID] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Get current inventory levels for specified variants"""
        
        query = select(Inventory).options(
            joinedload(Inventory.variant),
            joinedload(Inventory.location)
        ).where(Inventory.variant_id.in_(variant_ids))
        
        if location_id:
            query = query.where(Inventory.location_id == location_id)
        
        result = await self.db.execute(query)
        inventory_items = result.scalars().all()
        
        inventory_levels = {}
        for item in inventory_items:
            variant_id_str = str(item.variant_id)
            inventory_levels[variant_id_str] = {
                "current_stock": item.quantity,
                "low_stock_threshold": item.low_stock_threshold,
                "location_id": str(item.location_id),
                "location_name": item.location.name if item.location else None,
                "is_low_stock": item.quantity <= item.low_stock_threshold,
                "is_out_of_stock": item.quantity <= 0
            }
        
        return inventory_levels

    async def _generate_demand_based_recommendations(
        self,
        variant_predictions: Dict[str, Dict[str, Any]],
        inventory_levels: Dict[str, Dict[str, Any]],
        forecast_days: int
    ) -> List[Dict[str, Any]]:
        """Generate recommendations based on demand predictions and inventory levels"""
        
        recommendations = []
        
        for variant_id, prediction in variant_predictions.items():
            inventory = inventory_levels.get(variant_id, {})
            current_stock = inventory.get("current_stock", 0)
            predicted_demand = prediction["prediction"]["predicted_demand"]
            confidence_level = prediction["prediction"]["confidence_level"]
            
            # Generate recommendation based on stock vs demand
            if current_stock < predicted_demand:
                shortage = predicted_demand - current_stock
                recommendations.append({
                    "type": "reorder_needed",
                    "variant_id": variant_id,
                    "variant_name": prediction["variant_name"],
                    "current_stock": current_stock,
                    "predicted_demand": predicted_demand,
                    "shortage": shortage,
                    "confidence_level": confidence_level,
                    "priority": "high" if confidence_level > 0.8 else "medium",
                    "recommendation": f"Reorder {shortage} units to meet predicted demand"
                })
            elif current_stock > predicted_demand * 2:
                excess = current_stock - (predicted_demand * 1.5)  # Keep 50% buffer
                recommendations.append({
                    "type": "excess_inventory",
                    "variant_id": variant_id,
                    "variant_name": prediction["variant_name"],
                    "current_stock": current_stock,
                    "predicted_demand": predicted_demand,
                    "excess": int(excess),
                    "confidence_level": confidence_level,
                    "priority": "low",
                    "recommendation": f"Consider reducing inventory by {int(excess)} units"
                })
        
        return recommendations

    async def _analyze_batch_update_impact(
        self,
        processed_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze the impact of batch inventory updates"""
        
        total_items = len(processed_items)
        total_quantity_change = sum(item["quantity_change"] for item in processed_items)
        
        # Categorize changes
        increases = [item for item in processed_items if item["quantity_change"] > 0]
        decreases = [item for item in processed_items if item["quantity_change"] < 0]
        no_change = [item for item in processed_items if item["quantity_change"] == 0]
        
        # Calculate value impact (simplified)
        total_increase_quantity = sum(item["quantity_change"] for item in increases)
        total_decrease_quantity = sum(abs(item["quantity_change"]) for item in decreases)
        
        return {
            "total_items_updated": total_items,
            "net_quantity_change": total_quantity_change,
            "changes_breakdown": {
                "increases": len(increases),
                "decreases": len(decreases),
                "no_change": len(no_change)
            },
            "quantity_impact": {
                "total_increase": total_increase_quantity,
                "total_decrease": total_decrease_quantity,
                "net_change": total_quantity_change
            },
            "significant_changes": len([
                item for item in processed_items 
                if abs(item["quantity_change"]) > item["old_quantity"] * 0.5
            ])
        }

    async def _generate_post_batch_recommendations(
        self,
        impact_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations after batch update"""
        
        recommendations = []
        
        if impact_analysis["significant_changes"] > 0:
            recommendations.append(
                f"Review {impact_analysis['significant_changes']} items with significant quantity changes"
            )
        
        if impact_analysis["quantity_impact"]["net_change"] < 0:
            recommendations.append(
                "Net inventory decrease detected - consider reviewing consumption patterns"
            )
        
        if impact_analysis["changes_breakdown"]["no_change"] > impact_analysis["total_items_updated"] * 0.3:
            recommendations.append(
                "High number of no-change items - review data source for efficiency"
            )
        
        return recommendations

    async def _create_batch_update_audit_record(
        self,
        source_system: str,
        batch_start_time: datetime,
        processed_items: List[Dict[str, Any]],
        failed_items: List[Dict[str, Any]]
    ):
        """Create audit record for batch update"""
        
        # This would typically create a record in an audit table
        # For now, we'll just log the audit information
        
        audit_record = {
            "audit_type": "batch_inventory_update",
            "source_system": source_system,
            "batch_start_time": batch_start_time.isoformat(),
            "batch_end_time": datetime.utcnow().isoformat(),
            "processed_count": len(processed_items),
            "failed_count": len(failed_items),
            "total_quantity_change": sum(item["quantity_change"] for item in processed_items),
            "variants_affected": len(set(item["variant_id"] for item in processed_items))
        }
        
        structured_logger.info(
            message="Batch update audit record created",
            metadata=audit_record
        )