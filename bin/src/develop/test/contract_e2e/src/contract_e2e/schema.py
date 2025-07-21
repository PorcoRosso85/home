"""Schema validation functions"""

from typing import Dict, Any, Optional
import jsonschema
from .types import ValidationError


def validate_schemas(
    data: Dict[str, Any],
    schema: Dict[str, Any]
) -> Optional[ValidationError]:
    """Validate data against JSON Schema
    
    Returns None if valid, ValidationError if invalid
    """
    try:
        jsonschema.validate(data, schema)
        return None
    except jsonschema.ValidationError as e:
        return ValidationError(
            type="validation_error",
            schema_path=str(e.absolute_schema_path) if hasattr(e, 'absolute_schema_path') else "",
            instance_path=str(e.absolute_path) if hasattr(e, 'absolute_path') else "",
            message=str(e.message)
        )