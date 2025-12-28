"""Utility functions for repository operations."""

from typing import Any, get_args, get_origin

import pydantic


def normalize_list_fields(data: dict[str, Any], model: type[pydantic.BaseModel]) -> dict[str, Any]:
    """Normalize None values to empty lists for list-typed fields.
    
    This function inspects a Pydantic model's field annotations and converts
    None values to [] for fields that are typed as lists. This is necessary
    because databases may return None for JSONB array fields, but Pydantic
    expects list types (even with default_factory) to receive list values.
    
    Args:
        data: Dictionary containing row data from the database
        model: Pydantic model class to inspect for list-typed fields
        
    Returns:
        Dictionary with None values converted to [] for list-typed fields
    """
    normalized = data.copy()
    
    # Get the model's field annotations
    for field_name, field_info in model.model_fields.items():
        # Skip if field not in data
        if field_name not in normalized:
            continue
            
        # Skip if value is not None
        if normalized[field_name] is not None:
            continue
            
        # Get the field annotation
        annotation = field_info.annotation
        
        # Check if the annotation is a list type
        origin = get_origin(annotation)
        if origin is list:
            # This is a list type, normalize None to []
            normalized[field_name] = []
    
    return normalized

