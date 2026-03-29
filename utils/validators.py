"""
Validation utilities for product data
"""
import re
from typing import Dict, List, Any
from urllib.parse import urlparse




def validate_product_data(product: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate product data structure and required fields


    Args:
        product: Product data dictionary


    Returns:
        Tuple of (is_valid, list of validation errors)
    """
    errors = []
    required_fields = ['product_id', 'title', 'description', 'price', 'category']


    # Check required fields
    for field in required_fields:
        if field not in product or not product[field]:
            errors.append(f"Missing required field: {field}")


    # Validate product_id format
    if 'product_id' in product:
        if not isinstance(product['product_id'], str) or len(product['product_id']) == 0:
            errors.append("product_id must be a non-empty string")


    # Validate title
    if 'title' in product:
        if not isinstance(product['title'], str):
            errors.append("title must be a string")
        elif len(product['title']) < 3:
            errors.append("title must be at least 3 characters long")
        elif len(product['title']) > 200:
            errors.append("title must not exceed 200 characters")


    # Validate description
    if 'description' in product:
        if not isinstance(product['description'], str):
            errors.append("description must be a string")
        elif len(product['description']) < 10:
            errors.append("description must be at least 10 characters long")


    # Validate price
    if 'price' in product:
        price_valid, price_errors = validate_price(product['price'])
        if not price_valid:
            errors.extend(price_errors)


    # Validate images if present
    if 'images' in product:
        if not isinstance(product['images'], list):
            errors.append("images must be a list")
        else:
            for idx, img_url in enumerate(product['images']):
                if not validate_url(img_url):
                    errors.append(f"Invalid image URL at index {idx}: {img_url}")


    return len(errors) == 0, errors




def validate_price(price: Any) -> tuple[bool, List[str]]:
    """
    Validate product price


    Args:
        price: Price value to validate


    Returns:
        Tuple of (is_valid, list of validation errors)
    """
    errors = []


    # Check if price is numeric
    if not isinstance(price, (int, float)):
        errors.append(f"Price must be a number, got {type(price).__name__}")
        return False, errors


    # Check if price is positive
    if price <= 0:
        errors.append(f"Price must be positive, got {price}")


    # Check for reasonable price range (e.g., not more than $1,000,000)
    if price > 1_000_000:
        errors.append(f"Price seems unreasonably high: ${price:,.2f}")


    # Check for unreasonably low prices
    if price < 0.01:
        errors.append(f"Price seems unreasonably low: ${price:.2f}")


    return len(errors) == 0, errors




def validate_url(url: str) -> bool:
    """
    Validate URL format


    Args:
        url: URL string to validate


    Returns:
        True if valid, False otherwise
    """
    if not isinstance(url, str):
        return False


    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False




def validate_category(category: str, valid_categories: List[str]) -> tuple[bool, str]:
    """
    Validate product category


    Args:
        category: Category to validate
        valid_categories: List of valid categories


    Returns:
        Tuple of (is_valid, error_message)
    """
    if not category:
        return False, "Category cannot be empty"


    if category not in valid_categories:
        return False, f"Invalid category '{category}'. Must be one of: {', '.join(valid_categories)}"


    return True, ""




def validate_specifications(specs: Dict[str, str]) -> tuple[bool, List[str]]:
    """
    Validate product specifications


    Args:
        specs: Specifications dictionary


    Returns:
        Tuple of (is_valid, list of validation errors)
    """
    errors = []


    if not isinstance(specs, dict):
        errors.append("Specifications must be a dictionary")
        return False, errors


    if len(specs) == 0:
        errors.append("Specifications cannot be empty")


    for key, value in specs.items():
        if not isinstance(key, str) or not isinstance(value, str):
            errors.append(f"Specification key and value must be strings: {key}={value}")


        if not key.strip():
            errors.append("Specification keys cannot be empty")


    return len(errors) == 0, errors



