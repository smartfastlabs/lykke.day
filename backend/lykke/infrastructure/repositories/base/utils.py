"""Utility functions for repository operations."""

from dataclasses import fields, is_dataclass
from typing import Any, get_origin, get_type_hints

import pydantic


def filter_init_false_fields(data: dict[str, Any], entity_class: type[Any]) -> dict[str, Any]:
    """Filter out fields with init=False from a dictionary.
    
    When deserializing from the database, fields with init=False (like _domain_events)
    should not be passed to the entity constructor.
    
    Args:
        data: Dictionary containing data to filter
        entity_class: The entity class to check for init=False fields
        
    Returns:
        Filtered dictionary with init=False fields removed
    """
    if not is_dataclass(entity_class):
        return data
    
    init_false_fields = {f.name for f in fields(entity_class) if not f.init}
    return {k: v for k, v in data.items() if k not in init_false_fields}


def normalize_list_fields(data: dict[str, Any], model: type[Any]) -> dict[str, Any]:
    """Normalize None values to empty lists for list-typed fields.
    
    This function inspects a dataclass or Pydantic model's field annotations and converts
    None values to [] for fields that are typed as lists. This is necessary
    because databases may return None for JSONB array fields, but models
    expect list types (even with default_factory) to receive list values.
    
    Args:
        data: Dictionary containing row data from the database
        model: Dataclass or Pydantic model class to inspect for list-typed fields
        
    Returns:
        Dictionary with None values converted to [] for list-typed fields
    """
    normalized = data.copy()
    
    # Handle dataclasses
    if is_dataclass(model):
        type_hints = get_type_hints(model)
        for field in fields(model):
            # Skip if field not in data
            if field.name not in normalized:
                continue
                
            # Skip if value is not None
            if normalized[field.name] is not None:
                continue
                
            # Get the field annotation
            annotation = type_hints.get(field.name, field.type)
            
            # Check if the annotation is a list type
            origin = get_origin(annotation)
            if origin is list:
                # This is a list type, normalize None to []
                normalized[field.name] = []
        return normalized
    
    # Handle Pydantic models
    if isinstance(model, type) and issubclass(model, pydantic.BaseModel):
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

