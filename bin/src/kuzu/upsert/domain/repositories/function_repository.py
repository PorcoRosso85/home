"""
¢pêÝ¸ÈênÉá¤óâ¸åüë

Snâ¸åüëgo¢p‹¨óÆ£Æ£nêÝ¸Èê¤ó¿üÕ§ü¹hÉá¤óí¸Ã¯’Ð›W~Y
"""

from typing import Dict, Any, List, Optional, Union, Protocol, Callable

from upsert.domain.types import (
    FunctionTypeData,
    FunctionTypeError,
    FunctionTypeResult
)


class FunctionRepositoryProtocol(Protocol):
    """¢p‹êÝ¸Èên×íÈ³ëš©"""
    def save(self, function_data: Dict[str, Any]) -> FunctionTypeResult: ...
    def find_by_title(self, title: str) -> FunctionTypeResult: ...
    def get_all(self) -> Union[List[Dict[str, Any]], FunctionTypeError]: ...


def create_function_repository(
    save_impl: Callable[[Dict[str, Any]], FunctionTypeResult],
    find_by_title_impl: Callable[[str], FunctionTypeResult],
    get_all_impl: Callable[[], Union[List[Dict[str, Any]], FunctionTypeError]]
) -> FunctionRepositoryProtocol:
    """¢p‹êÝ¸Èê’\Y‹
    
    Args:
        save_impl: ÝXŸÅ
        find_by_title_impl: ¿¤Èëgn"ŸÅ
        get_all_impl: höÖ—ŸÅ
    
    Returns:
        FunctionRepositoryProtocol: ¢p‹êÝ¸Èê
    """
    
    def save(function_data: Dict[str, Any]) -> FunctionTypeResult:
        """¢p‹Çü¿’ÝXY‹
        
        Args:
            function_data: ÝXY‹¢p‹Çü¿
        
        Returns:
            FunctionTypeResult: ŸBo¢p‹Çü¿1WBo¨éüÅ1
        """
        # Éá¤óí¸Ã¯kˆ‹ÐêÇü·çó
        validation_result = validate_function_data(function_data)
        if "code" in validation_result:
            return validation_result
        
        # ŸÅ’|súY
        return save_impl(function_data)
    
    def find_by_title(title: str) -> FunctionTypeResult:
        """¿¤Èëg¢p‹’"Y‹
        
        Args:
            title: "Y‹¢p‹n¿¤Èë
        
        Returns:
            FunctionTypeResult: ŸBo¢p‹Çü¿1WBo¨éüÅ1
        """
        if not title:
            return {
                "code": "INVALID_TITLE",
                "message": "¿¤ÈëLšUŒfD~[“"
            }
        
        # ŸÅ’|súY
        return find_by_title_impl(title)
    
    def get_all() -> Union[List[Dict[str, Any]], FunctionTypeError]:
        """Yyfn¢p‹’Ö—Y‹
        
        Returns:
            Union[List[Dict[str, Any]], FunctionTypeError]: ŸBo¢p‹ê¹È1WBo¨éüÅ1
        """
        # ŸÅ’|súY
        return get_all_impl()
    
    # êÝ¸ÈêªÖ¸§¯È’ÔY
    return type("FunctionRepository", (), {
        "save": save,
        "find_by_title": find_by_title,
        "get_all": get_all
    })()


def validate_function_data(function_data: Dict[str, Any]) -> FunctionTypeResult:
    """¢p‹Çü¿’<Y‹
    
    Args:
        function_data: <Y‹¢p‹Çü¿
    
    Returns:
        FunctionTypeResult: ŸBoe›Çü¿1WBo¨éüÅ1
    """
    # ÅÕ£üëÉn<
    required_fields = ["title", "type"]
    for field in required_fields:
        if field not in function_data:
            return {
                "code": "MISSING_FIELD",
                "message": f"ÅÕ£üëÉLBŠ~[“: {field}"
            }
    
    # ¿¤Èën<
    title = function_data.get("title", "")
    if not title or not isinstance(title, str):
        return {
            "code": "INVALID_TITLE",
            "message": "¿¤ÈëozgjD‡WgB‹ÅLBŠ~Y"
        }
    
    # ‹n<
    type_value = function_data.get("type", "")
    if not type_value or not isinstance(type_value, str):
        return {
            "code": "INVALID_TYPE",
            "message": "‹ozgjD‡WgB‹ÅLBŠ~Y"
        }
    
    # Ñéáü¿n<‚WX(YŒp	
    if "parameters" in function_data:
        params = function_data["parameters"]
        
        # propertiesLX(Y‹K
        if not isinstance(params, dict) or "properties" not in params:
            return {
                "code": "INVALID_PARAMETERS",
                "message": "parametersoproperties’+€ªÖ¸§¯ÈgB‹ÅLBŠ~Y"
            }
        
        # requiredLX(Y‹4ê¹ÈgB‹Sh’º
        if "required" in params and not isinstance(params["required"], list):
            return {
                "code": "INVALID_REQUIRED",
                "message": "requiredoê¹ÈgB‹ÅLBŠ~Y"
            }
        
        # Ñéáü¿×íÑÆ£n<
        properties = params["properties"]
        if not isinstance(properties, dict):
            return {
                "code": "INVALID_PROPERTIES",
                "message": "propertiesoªÖ¸§¯ÈgB‹ÅLBŠ~Y"
            }
        
        for param_name, param_info in properties.items():
            if not isinstance(param_info, dict):
                return {
                    "code": "INVALID_PARAMETER_INFO",
                    "message": f"Ñéáü¿ '{param_name}' nÅ1oªÖ¸§¯ÈgB‹ÅLBŠ~Y"
                }
            
            # typeÕ£üëÉLB‹Kº
            if "type" not in param_info:
                return {
                    "code": "MISSING_PARAMETER_TYPE",
                    "message": f"Ñéáü¿ '{param_name}' n‹LšUŒfD~[“"
                }
    
    # ;Š$n<‚WX(YŒp	
    if "returnType" in function_data:
        return_type = function_data["returnType"]
        
        if not isinstance(return_type, dict):
            return {
                "code": "INVALID_RETURN_TYPE",
                "message": "returnTypeoªÖ¸§¯ÈgB‹ÅLBŠ~Y"
            }
        
        # typeÕ£üëÉLB‹Kº
        if "type" not in return_type:
            return {
                "code": "MISSING_RETURN_TYPE",
                "message": ";Š$n‹LšUŒfD~[“"
            }
    
    # Yyfn<’Ñ¹W_4
    return function_data


# Æ¹È¢p
def test_function_repository_logic() -> None:
    """¢p‹êÝ¸Èêí¸Ã¯nÆ¹È"""
    # âÃ¯ŸÅ
    def mock_save(data: Dict[str, Any]) -> FunctionTypeResult:
        return {
            "title": data["title"],
            "description": data.get("description", ""),
            "type": data["type"],
            "message": f"¢p‹ '{data['title']}' ’ÝXW~W_"
        }
    
    def mock_find_by_title(title: str) -> FunctionTypeResult:
        if title == "ExistingFunction":
            return {
                "title": "ExistingFunction",
                "description": "Existing function description",
                "type": "function",
                "parameters": {
                    "properties": {
                        "param1": {
                            "type": "string",
                            "description": "Parameter 1"
                        }
                    },
                    "required": ["param1"]
                },
                "returnType": {
                    "type": "string",
                    "description": "Return value"
                }
            }
        else:
            return {
                "code": "NOT_FOUND",
                "message": f"¢p‹ '{title}' L‹dKŠ~[“"
            }
    
    def mock_get_all() -> List[Dict[str, Any]]:
        return [
            {
                "title": "Function1",
                "description": "Description 1",
                "type": "function"
            },
            {
                "title": "Function2",
                "description": "Description 2",
                "type": "function"
            }
        ]
    
    # êÝ¸Èên\
    repo = create_function_repository(mock_save, mock_find_by_title, mock_get_all)
    
    # <: ÐêÇü·çóÆ¹È - ÅÕ£üëÉn =
    invalid_data = {"description": "Missing title and type"}
    result = repo.save(invalid_data)
    assert "code" in result
    assert result["code"] == "MISSING_FIELD"
    
    # <: ÐêÇü·çóÆ¹È - !¹j¿¤Èë
    invalid_title_data = {"title": "", "type": "function"}
    result = repo.save(invalid_title_data)
    assert "code" in result
    assert result["code"] == "INVALID_TITLE"
    
    # <: ÐêÇü·çóÆ¹È - !¹jÑéáü¿
    invalid_params_data = {
        "title": "TestFunction",
        "type": "function",
        "parameters": "not an object"
    }
    result = repo.save(invalid_params_data)
    assert "code" in result
    assert result["code"] == "INVALID_PARAMETERS"
    
    # <: 	¹jÇü¿nÝX
    valid_data = {
        "title": "TestFunction",
        "description": "Test function",
        "type": "function",
        "parameters": {
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "Parameter 1"
                }
            },
            "required": ["param1"]
        },
        "returnType": {
            "type": "string",
            "description": "Return value"
        }
    }
    result = repo.save(valid_data)
    assert "code" not in result
    assert result["title"] == "TestFunction"
    
    # <: ¿¤Èëgn" - X(Y‹¢p
    find_result = repo.find_by_title("ExistingFunction")
    assert "code" not in find_result
    assert find_result["title"] == "ExistingFunction"
    
    # <: ¿¤Èëgn" - X(WjD¢p
    find_result = repo.find_by_title("NonExistingFunction")
    assert "code" in find_result
    assert find_result["code"] == "NOT_FOUND"
    
    # <: Yyfn¢pnÖ—
    all_result = repo.get_all()
    assert isinstance(all_result, list)
    assert len(all_result) == 2
    assert all_result[0]["title"] == "Function1"
    assert all_result[1]["title"] == "Function2"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
