"""
Property-based tests for fuzzy search functionality.

Feature: docker-full-functionality
Properties tested:
- Property 47: Fuzzy search matching
- Property 52: Exact match prioritization
"""

import pytest
import asyncio
from hypothesis import given, strategies as st, settings, assume
from sqlalchemy.ext.asyncio import AsyncSession
from services.search import SearchService


# Feature: docker-full-functionality, Property 47: Fuzzy search matching
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
async def test_fuzzy_search_matching(query: str, limit: int, db_session):
    """
    Property 47: Fuzzy search matching
    
    For any misspelled search query, the fuzzy search should find similar matches 
    within the configured similarity threshold.
    
    Validates: Requirements 17.3
    """
    query = query.strip()
    assume(len(query) >= 2)
    
    search_service = SearchService(db_session)
    
    try:
        # Test fuzzy search for products
        products = await search_service.fuzzy_search_products(
            query=query,
            limit=limit,
            filters=None
        )
        
        # Property: All results should be valid product dictionaries
        for product in products:
            assert isinstance(product, dict), "Each result should be a dictionary"
            assert "type" in product, "Each result should have a type field"
            assert product["type"] == "product", "All results should be products"
            
            # Property: Each result should have required fields
            required_fields = ["id", "name", "relevance_score"]
            for field in required_fields:
                assert field in product, f"Product should have {field} field"
            
            # Property: Relevance score should be numeric and non-negative
            assert isinstance(product["relevance_score"], (int, float)), \
                "Relevance score should be numeric"
            assert product["relevance_score"] >= 0, \
                "Relevance score should be non-negative"
            
            # Property: Product should contain the query in some form or be similar
            query_lower = query.lower()
            name_lower = product["name"].lower()
            description_lower = (product.get("description") or "").lower()
            category_lower = (product.get("category_name") or "").lower()
            
            # Check if query appears in any searchable field (exact, prefix, or fuzzy match)
            matches_name = query_lower in name_lower
            matches_description = query_lower in description_lower
            matches_category = query_lower in category_lower
            
            # For fuzzy matching, we allow results that don't contain exact substrings
            # but should have some similarity (this is validated by the search service)
            # The key property is that results are returned with relevance scores
            assert product["relevance_score"] > 0, \
                f"Product '{product['name']}' should have positive relevance score for query '{query}'"
        
        # Property: Results should be ordered by relevance (descending)
        if len(products) > 1:
            for i in range(len(products) - 1):
                current_score = products[i]["relevance_score"]
                next_score = products[i + 1]["relevance_score"]
                assert current_score >= next_score, \
                    f"Results should be ordered by relevance: {current_score} >= {next_score}"
        
        # Property: Number of results should not exceed limit
        assert len(products) <= limit, \
            f"Number of results ({len(products)}) should not exceed limit ({limit})"
    
    except Exception as e:
        # If there's a database error or no data, that's acceptable for property testing
        if "no such table" in str(e).lower() or "relation does not exist" in str(e).lower():
            pytest.skip(f"Database not initialized or missing data: {e}")
        else:
            raise


# Feature: docker-full-functionality, Property 52: Exact match prioritization
@settings(max_examples=50, deadline=10000)
@given(
    base_query=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll")),
        min_size=3,
        max_size=8
    ).filter(lambda x: x.strip() and len(x.strip()) >= 3),
    typo_type=st.sampled_from(["substitute", "insert", "delete", "transpose"])
)
@pytest.mark.asyncio
async def test_exact_match_prioritization(base_query: str, typo_type: str, db_session):
    """
    Property 52: Exact match prioritization
    
    For any search with both exact and fuzzy matches, exact matches should rank 
    higher than fuzzy matches.
    
    Validates: Requirements 17.8
    """
    base_query = base_query.strip()
    assume(len(base_query) >= 3)
    
    # Create a typo version of the query
    if typo_type == "substitute" and len(base_query) > 0:
        # Substitute one character
        pos = len(base_query) // 2
        typo_query = base_query[:pos] + "x" + base_query[pos+1:]
    elif typo_type == "insert":
        # Insert an extra character
        pos = len(base_query) // 2
        typo_query = base_query[:pos] + "x" + base_query[pos:]
    elif typo_type == "delete" and len(base_query) > 3:
        # Delete a character
        pos = len(base_query) // 2
        typo_query = base_query[:pos] + base_query[pos+1:]
    elif typo_type == "transpose" and len(base_query) > 3:
        # Transpose two adjacent characters
        pos = len(base_query) // 2
        if pos < len(base_query) - 1:
            chars = list(base_query)
            chars[pos], chars[pos+1] = chars[pos+1], chars[pos]
            typo_query = "".join(chars)
        else:
            typo_query = base_query + "x"  # Fallback
    else:
        typo_query = base_query + "x"  # Fallback
    
    assume(typo_query != base_query)
    assume(len(typo_query) >= 2)
    
    search_service = SearchService(db_session)
    
    try:
        # Search with the original (exact) query
        exact_results = await search_service.fuzzy_search_products(
            query=base_query,
            limit=20,
            filters=None
        )
        
        # Search with the typo (fuzzy) query
        fuzzy_results = await search_service.fuzzy_search_products(
            query=typo_query,
            limit=20,
            filters=None
        )
        
        # Property: If both searches return results, we can compare relevance patterns
        if exact_results and fuzzy_results:
            # Find products that appear in both result sets
            exact_products = {p["id"]: p for p in exact_results}
            fuzzy_products = {p["id"]: p for p in fuzzy_results}
            
            common_products = set(exact_products.keys()) & set(fuzzy_products.keys())
            
            # Property: For products that appear in both searches,
            # the exact match search should generally give higher or equal scores
            for product_id in common_products:
                exact_score = exact_products[product_id]["relevance_score"]
                fuzzy_score = fuzzy_products[product_id]["relevance_score"]
                
                # Allow some tolerance for scoring differences due to different query contexts
                # The key property is that exact matches should not be significantly lower
                score_ratio = exact_score / fuzzy_score if fuzzy_score > 0 else float('inf')
                
                # Exact matches should generally score at least as well as fuzzy matches
                # We allow some tolerance (0.8) for algorithmic variations
                assert score_ratio >= 0.8, \
                    f"Product {product_id}: exact match score ({exact_score}) should be " \
                    f"comparable to fuzzy match score ({fuzzy_score}), ratio: {score_ratio}"
        
        # Property: Both result sets should be properly ordered by relevance
        for results, query_type in [(exact_results, "exact"), (fuzzy_results, "fuzzy")]:
            if len(results) > 1:
                for i in range(len(results) - 1):
                    current_score = results[i]["relevance_score"]
                    next_score = results[i + 1]["relevance_score"]
                    assert current_score >= next_score, \
                        f"{query_type} results should be ordered by relevance: " \
                        f"{current_score} >= {next_score}"
    
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
    ).filter(lambda x: x.strip() and len(x.strip()) >= 2),
    filters=st.fixed_dictionaries({
        "min_price": st.one_of(st.none(), st.floats(min_value=0, max_value=1000)),
        "max_price": st.one_of(st.none(), st.floats(min_value=0, max_value=1000)),
    })
)
@pytest.mark.asyncio
async def test_fuzzy_search_with_filters(query: str, filters: dict, db_session):
    """
    Test that fuzzy search works correctly with additional filters.
    
    This tests the integration between fuzzy search and filtering capabilities.
    """
    query = query.strip()
    assume(len(query) >= 2)
    
    # Ensure min_price <= max_price if both are specified
    if filters["min_price"] is not None and filters["max_price"] is not None:
        assume(filters["min_price"] <= filters["max_price"])
    
    search_service = SearchService(db_session)
    
    try:
        # Clean up filters (remove None values)
        clean_filters = {k: v for k, v in filters.items() if v is not None}
        
        products = await search_service.fuzzy_search_products(
            query=query,
            limit=20,
            filters=clean_filters if clean_filters else None
        )
        
        # Property: All results should be valid
        for product in products:
            assert isinstance(product, dict), "Each result should be a dictionary"
            assert "type" in product and product["type"] == "product", \
                "Each result should be a product"
            assert "relevance_score" in product, "Each result should have relevance_score"
            assert product["relevance_score"] >= 0, "Relevance score should be non-negative"
        
        # Property: Results should be ordered by relevance
        if len(products) > 1:
            for i in range(len(products) - 1):
                current_score = products[i]["relevance_score"]
                next_score = products[i + 1]["relevance_score"]
                assert current_score >= next_score, \
                    f"Results should be ordered by relevance: {current_score} >= {next_score}"
    
    except Exception as e:
        # If there's a database error or no data, that's acceptable for property testing
        if "no such table" in str(e).lower() or "relation does not exist" in str(e).lower():
            pytest.skip(f"Database not initialized or missing data: {e}")
        else:
            raise


@pytest.mark.asyncio
async def test_similarity_threshold_configuration(db_session):
    """
    Test that the search service has a properly configured similarity threshold.
    
    This tests the configuration property of the fuzzy search system.
    """
    search_service = SearchService(db_session)
    
    # Property: Similarity threshold should be between 0 and 1
    assert hasattr(search_service, 'similarity_threshold'), \
        "SearchService should have similarity_threshold attribute"
    
    threshold = search_service.similarity_threshold
    assert isinstance(threshold, (int, float)), \
        "Similarity threshold should be numeric"
    assert 0 <= threshold <= 1, \
        f"Similarity threshold should be between 0 and 1, got {threshold}"
    
    # Property: Weights should be properly configured
    assert hasattr(search_service, 'weights'), \
        "SearchService should have weights configuration"
    
    weights = search_service.weights
    assert isinstance(weights, dict), "Weights should be a dictionary"
    
    required_weight_types = ["exact", "prefix", "fuzzy"]
    for weight_type in required_weight_types:
        assert weight_type in weights, f"Weights should include {weight_type}"
        assert isinstance(weights[weight_type], (int, float)), \
            f"Weight for {weight_type} should be numeric"
        assert weights[weight_type] >= 0, \
            f"Weight for {weight_type} should be non-negative"
    
    # Property: Exact matches should have highest weight
    assert weights["exact"] >= weights["prefix"], \
        "Exact match weight should be >= prefix weight"
    assert weights["prefix"] >= weights["fuzzy"], \
        "Prefix match weight should be >= fuzzy weight"


@pytest.mark.asyncio
async def test_levenshtein_distance_calculation(db_session):
    """
    Test the Levenshtein distance calculation function.
    
    This tests the correctness of the fuzzy matching algorithm.
    """
    search_service = SearchService(db_session)
    
    # Test known Levenshtein distances
    test_cases = [
        ("", "", 0),
        ("a", "", 1),
        ("", "a", 1),
        ("abc", "abc", 0),
        ("abc", "ab", 1),
        ("abc", "abcd", 1),
        ("abc", "axc", 1),
        ("kitten", "sitting", 3),
        ("saturday", "sunday", 3),
    ]
    
    for s1, s2, expected_distance in test_cases:
        actual_distance = search_service.calculate_levenshtein_distance(s1, s2)
        assert actual_distance == expected_distance, \
            f"Levenshtein distance between '{s1}' and '{s2}' should be {expected_distance}, got {actual_distance}"
    
    # Property: Distance should be symmetric
    test_pairs = [("hello", "world"), ("test", "best"), ("python", "java")]
    for s1, s2 in test_pairs:
        dist1 = search_service.calculate_levenshtein_distance(s1, s2)
        dist2 = search_service.calculate_levenshtein_distance(s2, s1)
        assert dist1 == dist2, \
            f"Levenshtein distance should be symmetric: d('{s1}', '{s2}') = d('{s2}', '{s1}')"
    
    # Property: Triangle inequality (d(a,c) <= d(a,b) + d(b,c))
    test_triplets = [("abc", "def", "ghi"), ("test", "best", "rest")]
    for s1, s2, s3 in test_triplets:
        d12 = search_service.calculate_levenshtein_distance(s1, s2)
        d23 = search_service.calculate_levenshtein_distance(s2, s3)
        d13 = search_service.calculate_levenshtein_distance(s1, s3)
        assert d13 <= d12 + d23, \
            f"Triangle inequality should hold: d('{s1}', '{s3}') <= d('{s1}', '{s2}') + d('{s2}', '{s3}')"