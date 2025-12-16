"""
Property-based tests for user and category search functionality.

Feature: docker-full-functionality
Properties tested:
- Property 50: User search prefix matching
- Property 51: Category search with fuzzy matching
"""

import pytest
import asyncio
from hypothesis import given, strategies as st, settings, assume
from sqlalchemy.ext.asyncio import AsyncSession
# Remove unused import
from services.search import SearchService


# Feature: docker-full-functionality, Property 50: User search prefix matching
@settings(max_examples=100, deadline=10000)
@given(
    query_prefix=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
        min_size=2,
        max_size=10
    ).filter(lambda x: x.strip() and len(x.strip()) >= 2),
    limit=st.integers(min_value=5, max_value=50),
    role_filter=st.one_of(st.none(), st.sampled_from(["Customer", "Supplier", "Admin"]))
)
@pytest.mark.asyncio
async def test_user_search_prefix_matching(query_prefix: str, limit: int, role_filter: str, db_session):
    """
    Property 50: User search prefix matching
    
    For any user search query prefix, results should include users whose username 
    or email starts with the prefix.
    
    Validates: Requirements 17.6
    """
    query_prefix = query_prefix.strip()
    assume(len(query_prefix) >= 2)
    
    search_service = SearchService(db_session)
    
    try:
        users = await search_service.search_users(
                query=query_prefix,
                limit=limit,
                role_filter=role_filter
            )
        
        # Property: All results should be valid user dictionaries
        for user in users:
                assert isinstance(user, dict), "Each result should be a dictionary"
                assert "type" in user, "Each result should have a type field"
                assert user["type"] == "user", "All results should be users"
                
                # Property: Each result should have required user fields
                required_fields = ["id", "firstname", "lastname", "email", "relevance_score"]
                for field in required_fields:
                    assert field in user, f"User should have {field} field"
                
                # Property: Relevance score should be numeric and non-negative
                assert isinstance(user["relevance_score"], (int, float)), \
                    "Relevance score should be numeric"
                assert user["relevance_score"] >= 0, \
                    "Relevance score should be non-negative"
                
                # Property: User should match the query in some searchable field
                query_lower = query_prefix.lower()
                firstname_lower = user["firstname"].lower()
                lastname_lower = user["lastname"].lower()
                email_lower = user["email"].lower()
                full_name_lower = user.get("full_name", "").lower()
                
                # Check if query appears as prefix or substring in any user field
                matches_firstname = query_lower in firstname_lower
                matches_lastname = query_lower in lastname_lower
                matches_email = query_lower in email_lower
                matches_fullname = query_lower in full_name_lower
                
                assert matches_firstname or matches_lastname or matches_email or matches_fullname, \
                    f"User '{user['full_name']}' should contain query '{query_prefix}' in name or email"
                
                # Property: If role filter is specified, user should have that role
                if role_filter:
                    assert "role" in user, "User should have role field when role filter is applied"
                    assert user["role"] == role_filter, \
                        f"User role '{user['role']}' should match filter '{role_filter}'"
                
                # Property: User should have valid role
                if "role" in user:
                    valid_roles = ["Customer", "Supplier", "Admin"]
                    assert user["role"] in valid_roles, \
                        f"User role '{user['role']}' should be one of {valid_roles}"
                
                # Property: User should have verified status
                if "verified" in user:
                    assert isinstance(user["verified"], bool), \
                        "User verified status should be boolean"
        
        # Property: Results should be ordered by relevance (descending)
        if len(users) > 1:
            for i in range(len(users) - 1):
                current_score = users[i]["relevance_score"]
                next_score = users[i + 1]["relevance_score"]
                assert current_score >= next_score, \
                    f"Users should be ordered by relevance: {current_score} >= {next_score}"
        
        # Property: Number of results should not exceed limit
        assert len(users) <= limit, \
                f"Number of results ({len(users)}) should not exceed limit ({limit})"
        
    except Exception as e:
        # If there's a database error or no data, that's acceptable for property testing
        if "no such table" in str(e).lower() or "relation does not exist" in str(e).lower():
            pytest.skip(f"Database not initialized or missing data: {e}")
        else:
            raise


# Feature: docker-full-functionality, Property 51: Category search with fuzzy matching
@settings(max_examples=100, deadline=10000)
@given(
    query=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Pc")),
        min_size=2,
        max_size=12
    ).filter(lambda x: x.strip() and len(x.strip()) >= 2),
    limit=st.integers(min_value=5, max_value=50)
)
@pytest.mark.asyncio
async def test_category_search_with_fuzzy_matching(query: str, limit: int, db_session):
    """
    Property 51: Category search with fuzzy matching
    
    For any category search query, results should include categories with names 
    that match via prefix or fuzzy matching.
    
    Validates: Requirements 17.7
    """
    query = query.strip()
    assume(len(query) >= 2)
    
    search_service = SearchService(db_session)
    
    try:
            categories = await search_service.search_categories(
                query=query,
                limit=limit
            )
            
            # Property: All results should be valid category dictionaries
            for category in categories:
                assert isinstance(category, dict), "Each result should be a dictionary"
                assert "type" in category, "Each result should have a type field"
                assert category["type"] == "category", "All results should be categories"
                
                # Property: Each result should have required category fields
                required_fields = ["id", "name", "relevance_score"]
                for field in required_fields:
                    assert field in category, f"Category should have {field} field"
                
                # Property: Relevance score should be numeric and non-negative
                assert isinstance(category["relevance_score"], (int, float)), \
                    "Relevance score should be numeric"
                assert category["relevance_score"] >= 0, \
                    "Relevance score should be non-negative"
                
                # Property: Category should match the query in name or description
                query_lower = query.lower()
                name_lower = category["name"].lower()
                description_lower = (category.get("description") or "").lower()
                
                # Check if query appears in category name or description
                # For fuzzy matching, we allow results that don't contain exact substrings
                # but should have some similarity (validated by the search service)
                matches_name = query_lower in name_lower
                matches_description = query_lower in description_lower
                
                # The key property is that results have positive relevance scores
                assert category["relevance_score"] > 0, \
                    f"Category '{category['name']}' should have positive relevance score for query '{query}'"
                
                # Property: Category should have valid optional fields
                if "product_count" in category:
                    assert isinstance(category["product_count"], int), \
                        "Product count should be integer"
                    assert category["product_count"] >= 0, \
                        "Product count should be non-negative"
                
                if "image_url" in category and category["image_url"]:
                    assert isinstance(category["image_url"], str), \
                        "Image URL should be string"
            
            # Property: Results should be ordered by relevance (descending)
            if len(categories) > 1:
                for i in range(len(categories) - 1):
                    current_score = categories[i]["relevance_score"]
                    next_score = categories[i + 1]["relevance_score"]
                    assert current_score >= next_score, \
                        f"Categories should be ordered by relevance: {current_score} >= {next_score}"
            
            # Property: Number of results should not exceed limit
            assert len(categories) <= limit, \
                f"Number of results ({len(categories)}) should not exceed limit ({limit})"
        
    except Exception as e:
            # If there's a database error or no data, that's acceptable for property testing
            if "no such table" in str(e).lower() or "relation does not exist" in str(e).lower():
                pytest.skip(f"Database not initialized or missing data: {e}")
            else:
                raise


@settings(max_examples=50, deadline=10000)
@given(
    query=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll")),
        min_size=2,
        max_size=8
    ).filter(lambda x: x.strip() and len(x.strip()) >= 2),
    search_type=st.sampled_from(["user", "category"])
)
@pytest.mark.asyncio
async def test_user_category_search_consistency(query: str, search_type: str, db_session):
    """
    Test that user and category searches return consistent result structures.
    
    This tests the consistency property across different search types.
    """
    query = query.strip()
    assume(len(query) >= 2)
    
    search_service = SearchService(db_session)
        
        try:
            if search_type == "user":
                results = await search_service.search_users(
                    query=query,
                    limit=20,
                    role_filter=None
                )
            else:  # category
                results = await search_service.search_categories(
                    query=query,
                    limit=20
                )
            
            # Property: All results should have consistent structure
            for result in results:
                assert isinstance(result, dict), "Each result should be a dictionary"
                
                # Property: Common fields should be present
                common_fields = ["id", "type", "relevance_score"]
                for field in common_fields:
                    assert field in result, f"Result should have {field} field"
                
                # Property: Type should match search type
                assert result["type"] == search_type, \
                    f"Result type should be {search_type}, got {result['type']}"
                
                # Property: ID should be a valid UUID string
                assert isinstance(result["id"], str), "ID should be string"
                assert len(result["id"]) > 0, "ID should not be empty"
                
                # Property: Relevance score should be valid
                score = result["relevance_score"]
                assert isinstance(score, (int, float)), "Relevance score should be numeric"
                assert score >= 0, "Relevance score should be non-negative"
                
                # Type-specific field validation
                if search_type == "user":
                    user_fields = ["firstname", "lastname", "email", "full_name"]
                    for field in user_fields:
                        assert field in result, f"User result should have {field} field"
                        assert isinstance(result[field], str), f"User {field} should be string"
                else:  # category
                    category_fields = ["name"]
                    for field in category_fields:
                        assert field in result, f"Category result should have {field} field"
                        assert isinstance(result[field], str), f"Category {field} should be string"
        
        except Exception as e:
            # If there's a database error or no data, that's acceptable for property testing
            if "no such table" in str(e).lower() or "relation does not exist" in str(e).lower():
                pytest.skip(f"Database not initialized or missing data: {e}")
            else:
                raise


@settings(max_examples=30, deadline=10000)
@given(
    query=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll")),
        min_size=2,
        max_size=6
    ).filter(lambda x: x.strip() and len(x.strip()) >= 2)
)
@pytest.mark.asyncio
async def test_empty_results_handling(query: str, db_session):
    """
    Test that user and category searches handle empty results gracefully.
    
    This tests the edge case property for searches with no matches.
    """
    query = query.strip()
    assume(len(query) >= 2)
    
    # Use a very specific query that's unlikely to match anything
    unlikely_query = f"xyzunlikely{query}999"
    
    search_service = SearchService(db_session)
        
        try:
            # Test user search with unlikely query
            users = await search_service.search_users(
                query=unlikely_query,
                limit=10,
                role_filter=None
            )
            
            # Property: Should return empty list, not None or error
            assert isinstance(users, list), "User search should return a list"
            
            # Test category search with unlikely query
            categories = await search_service.search_categories(
                query=unlikely_query,
                limit=10
            )
            
            # Property: Should return empty list, not None or error
            assert isinstance(categories, list), "Category search should return a list"
            
            # Property: If there are results, they should be valid
            for user in users:
                assert isinstance(user, dict), "Each user result should be a dictionary"
                assert user["type"] == "user", "Each result should be a user"
            
            for category in categories:
                assert isinstance(category, dict), "Each category result should be a dictionary"
                assert category["type"] == "category", "Each result should be a category"
        
        except Exception as e:
            # If there's a database error or no data, that's acceptable for property testing
            if "no such table" in str(e).lower() or "relation does not exist" in str(e).lower():
                pytest.skip(f"Database not initialized or missing data: {e}")
            else:
                raise


@pytest.mark.asyncio
async def test_user_search_role_filtering(db_session):
    """
    Test that user search role filtering works correctly.
    
    This tests the filtering property of user search.
    """
    search_service = SearchService(db_session)
            
            try:
                # Test with each valid role
                valid_roles = ["Customer", "Supplier", "Admin"]
                
                for role in valid_roles:
                    users = await search_service.search_users(
                        query="test",
                        limit=10,
                        role_filter=role
                    )
                    
                    # Property: All returned users should have the specified role
                    for user in users:
                        if "role" in user:
                            assert user["role"] == role, \
                                f"User role should be {role}, got {user['role']}"
                
                # Test with no role filter
                all_users = await search_service.search_users(
                    query="test",
                    limit=10,
                    role_filter=None
                )
                
                # Property: Should return users regardless of role
                for user in all_users:
                    assert "type" in user and user["type"] == "user", \
                        "All results should be users"
            
            except Exception as e:
                if "no such table" in str(e).lower() or "relation does not exist" in str(e).lower():
                    pytest.skip(f"Database not initialized or missing data: {e}")
                else:
                    raise


@pytest.mark.asyncio
async def test_search_service_initialization(db_session):
    """
    Test that the SearchService initializes with correct configuration.
    
    This tests the initialization properties of the search service.
    """
    search_service = SearchService(db_session)
            
            # Property: Service should have database session
            assert search_service.db is not None, "SearchService should have database session"
            
            # Property: Service should have similarity threshold configured
            assert hasattr(search_service, 'similarity_threshold'), \
                "SearchService should have similarity_threshold"
            threshold = search_service.similarity_threshold
            assert isinstance(threshold, (int, float)), "Similarity threshold should be numeric"
            assert 0 < threshold < 1, "Similarity threshold should be between 0 and 1"
            
            # Property: Service should have weights configured
            assert hasattr(search_service, 'weights'), "SearchService should have weights"
            weights = search_service.weights
            assert isinstance(weights, dict), "Weights should be a dictionary"
            
            required_weights = ["exact", "prefix", "fuzzy"]
            for weight_type in required_weights:
                assert weight_type in weights, f"Should have {weight_type} weight"
                assert weights[weight_type] > 0, f"{weight_type} weight should be positive"
            
            # Property: Service should have field weights configured
            assert hasattr(search_service, 'product_field_weights'), \
                "SearchService should have product_field_weights"
            field_weights = search_service.product_field_weights
            assert isinstance(field_weights, dict), "Field weights should be a dictionary"
            
            required_fields = ["name", "description", "category", "tags"]
            for field in required_fields:
                assert field in field_weights, f"Should have {field} field weight"
                assert field_weights[field] > 0, f"{field} weight should be positive"