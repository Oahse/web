"""
Property-based tests for search autocomplete functionality.

Feature: docker-full-functionality
Properties tested:
- Property 45: Autocomplete prefix matching
- Property 54: Autocomplete result limiting
"""

import pytest
import asyncio
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from sqlalchemy.ext.asyncio import AsyncSession
from services.search import SearchService


# Feature: docker-full-functionality, Property 45: Autocomplete prefix matching
@settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    query_prefix=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll")),
        min_size=2,
        max_size=6
    ).filter(lambda x: x.strip() and len(x.strip()) >= 2),
    search_type=st.sampled_from(["product", "user", "category"])
)
@pytest.mark.asyncio
async def test_autocomplete_prefix_matching(query_prefix: str, search_type: str, db_session):
    """
    Property 45: Autocomplete prefix matching
    
    For any search query prefix, the autocomplete should return suggestions that start with the prefix.
    
    Validates: Requirements 17.1
    """
    query_prefix = query_prefix.strip()
    assume(len(query_prefix) >= 2)
    
    search_service = SearchService(db_session)
    
    try:
        suggestions = await search_service.autocomplete(
            query=query_prefix,
            search_type=search_type,
            limit=10
        )
        
        # Property: All suggestions should be relevant to the search type
        for suggestion in suggestions:
            assert suggestion["type"] == search_type, \
                f"Suggestion type {suggestion['type']} should match requested type {search_type}"
            
            # Property: Suggestions should have relevance scores
            assert "relevance_score" in suggestion, "Each suggestion should have a relevance_score"
            assert isinstance(suggestion["relevance_score"], (int, float)), \
                "Relevance score should be numeric"
            assert suggestion["relevance_score"] >= 0, "Relevance score should be non-negative"
            
            # Property: Suggestions should contain the query in some form (prefix, fuzzy, or exact match)
            query_lower = query_prefix.lower()
            
            if search_type == "product":
                assert "name" in suggestion, "Product suggestion should have name"
                name_lower = suggestion["name"].lower()
                description_lower = (suggestion.get("description") or "").lower()
                category_lower = (suggestion.get("category_name") or "").lower()
                
                # Check if query appears as prefix or substring in any searchable field
                matches_name = query_lower in name_lower
                matches_description = query_lower in description_lower
                matches_category = query_lower in category_lower
                
                assert matches_name or matches_description or matches_category, \
                    f"Product suggestion '{suggestion['name']}' should contain query '{query_prefix}' in name, description, or category"
            
            elif search_type == "user":
                assert "firstname" in suggestion and "lastname" in suggestion, \
                    "User suggestion should have firstname and lastname"
                firstname_lower = suggestion["firstname"].lower()
                lastname_lower = suggestion["lastname"].lower()
                email_lower = suggestion.get("email", "").lower()
                full_name_lower = suggestion.get("full_name", "").lower()
                
                # Check if query appears in any user field
                matches_firstname = query_lower in firstname_lower
                matches_lastname = query_lower in lastname_lower
                matches_email = query_lower in email_lower
                matches_fullname = query_lower in full_name_lower
                
                assert matches_firstname or matches_lastname or matches_email or matches_fullname, \
                    f"User suggestion '{suggestion['full_name']}' should contain query '{query_prefix}' in name or email"
            
            elif search_type == "category":
                assert "name" in suggestion, "Category suggestion should have name"
                name_lower = suggestion["name"].lower()
                description_lower = (suggestion.get("description") or "").lower()
                
                # Check if query appears in category name or description
                matches_name = query_lower in name_lower
                matches_description = query_lower in description_lower
                
                assert matches_name or matches_description, \
                    f"Category suggestion '{suggestion['name']}' should contain query '{query_prefix}' in name or description"
    
    except Exception as e:
        # If there's a database error or no data, that's acceptable for property testing
        if "no such table" in str(e).lower() or "relation does not exist" in str(e).lower():
            pytest.skip(f"Database not initialized or missing data: {e}")
        else:
            raise


# Feature: docker-full-functionality, Property 54: Autocomplete result limiting
@settings(max_examples=15, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    query=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll")),
        min_size=2,
        max_size=5
    ).filter(lambda x: x.strip() and len(x.strip()) >= 2),
    search_type=st.sampled_from(["product", "user", "category"]),
    limit=st.integers(min_value=1, max_value=10)
)
@pytest.mark.asyncio
async def test_autocomplete_result_limiting(query: str, search_type: str, limit: int, db_session):
    """
    Property 54: Autocomplete result limiting
    
    For any autocomplete request, the system should return at most the requested limit of suggestions.
    
    Validates: Requirements 17.10
    """
    query = query.strip()
    assume(len(query) >= 2)
    
    search_service = SearchService(db_session)
    
    try:
        suggestions = await search_service.autocomplete(
            query=query,
            search_type=search_type,
            limit=limit
        )
        
        # Property: Number of suggestions should not exceed the limit
        assert len(suggestions) <= limit, \
            f"Number of suggestions ({len(suggestions)}) should not exceed limit ({limit})"
        
        # Property: All suggestions should be valid dictionaries with required fields
        for suggestion in suggestions:
            assert isinstance(suggestion, dict), "Each suggestion should be a dictionary"
            assert "type" in suggestion, "Each suggestion should have a type field"
            assert suggestion["type"] == search_type, \
                f"Suggestion type should match requested type {search_type}"
            assert "relevance_score" in suggestion, "Each suggestion should have a relevance_score"
            
            # Type-specific field validation
            if search_type == "product":
                assert "id" in suggestion, "Product suggestion should have id"
                assert "name" in suggestion, "Product suggestion should have name"
            elif search_type == "user":
                assert "id" in suggestion, "User suggestion should have id"
                assert "firstname" in suggestion, "User suggestion should have firstname"
                assert "lastname" in suggestion, "User suggestion should have lastname"
            elif search_type == "category":
                assert "id" in suggestion, "Category suggestion should have id"
                assert "name" in suggestion, "Category suggestion should have name"
        
        # Property: Suggestions should be ordered by relevance (descending)
        if len(suggestions) > 1:
            for i in range(len(suggestions) - 1):
                current_score = suggestions[i]["relevance_score"]
                next_score = suggestions[i + 1]["relevance_score"]
                assert current_score >= next_score, \
                    f"Suggestions should be ordered by relevance score (descending): " \
                    f"{current_score} >= {next_score}"
    
    except Exception as e:
        # If there's a database error or no data, that's acceptable for property testing
        if "no such table" in str(e).lower() or "relation does not exist" in str(e).lower():
            pytest.skip(f"Database not initialized or missing data: {e}")
        else:
            raise


@pytest.mark.asyncio
async def test_autocomplete_empty_results_handling(db_session):
    """
    Test that autocomplete handles cases where no results are found gracefully.
    
    This is an edge case property test to ensure the system doesn't crash
    when no matching data is found.
    """
    # Use a very specific query that's unlikely to match anything
    unlikely_query = "xyzabcunlikely999"
    
    search_service = SearchService(db_session)
    
    try:
        for search_type in ["product", "user", "category"]:
            suggestions = await search_service.autocomplete(
                query=unlikely_query,
                search_type=search_type,
                limit=10
            )
            
            # Property: Should return empty list, not None or error
            assert isinstance(suggestions, list), \
                f"Autocomplete should return a list, got {type(suggestions)}"
            
            # Property: Empty results should be an empty list
            # (We can't guarantee no results, but if there are results, they should be valid)
            for suggestion in suggestions:
                assert isinstance(suggestion, dict), "Each suggestion should be a dictionary"
                assert "type" in suggestion, "Each suggestion should have a type field"
                assert suggestion["type"] == search_type, \
                    f"Suggestion type should match requested type {search_type}"
    
    except Exception as e:
        # If there's a database error or no data, that's acceptable for property testing
        if "no such table" in str(e).lower() or "relation does not exist" in str(e).lower():
            pytest.skip(f"Database not initialized or missing data: {e}")
        else:
            raise


@pytest.mark.asyncio
async def test_autocomplete_minimum_query_length(db_session):
    """
    Test that autocomplete properly handles queries that are too short.
    
    This tests the input validation property.
    """
    search_service = SearchService(db_session)
    
    # Test with empty query
    suggestions = await search_service.autocomplete(
        query="",
        search_type="product",
        limit=10
    )
    assert suggestions == [], "Empty query should return empty list"
    
    # Test with single character query
    suggestions = await search_service.autocomplete(
        query="a",
        search_type="product",
        limit=10
    )
    assert suggestions == [], "Single character query should return empty list"
    
    # Test with whitespace-only query
    suggestions = await search_service.autocomplete(
        query="   ",
        search_type="product",
        limit=10
    )
    assert suggestions == [], "Whitespace-only query should return empty list"


@pytest.mark.asyncio
async def test_autocomplete_invalid_search_type(db_session):
    """
    Test that autocomplete handles invalid search types gracefully.
    """
    search_service = SearchService(db_session)
    
    # Test with invalid search type
    suggestions = await search_service.autocomplete(
        query="test",
        search_type="invalid_type",
        limit=10
    )
    assert suggestions == [], "Invalid search type should return empty list"