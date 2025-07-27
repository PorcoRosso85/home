"""User Defined Functions (UDF) Registry for KuzuDB

This module manages the registration and execution of Python functions
as User Defined Functions within KuzuDB. It provides a clean interface
for registering custom business logic that can be executed directly
within the graph database.
"""

from typing import Dict, Any, Callable, Optional, Union, List
from decimal import Decimal
from datetime import datetime
import kuzu
from pathlib import Path


class UDFRegistrationResult:
    """Result type for UDF registration operations"""
    
    def __init__(self, success: bool, function_name: str, error_message: Optional[str] = None):
        self.ok = success
        self.function_name = function_name
        self.error = error_message if not success else None


class UDFRegistry:
    """Registry for managing User Defined Functions in KuzuDB
    
    This class provides methods to register Python functions as UDFs
    that can be called directly from Cypher queries, moving business
    logic closer to the data layer.
    """
    
    def __init__(self, connection: kuzu.Connection):
        """Initialize UDF Registry with a KuzuDB connection
        
        Args:
            connection: Active KuzuDB connection instance
        """
        self.connection = connection
        self._registered_functions: Dict[str, Callable] = {}
    
    def register_function(
        self, 
        name: str, 
        func: Callable,
        input_types: List[str],
        output_type: str
    ) -> UDFRegistrationResult:
        """Register a Python function as a KuzuDB UDF
        
        Args:
            name: Name to register the function as in KuzuDB
            func: Python function to register
            input_types: List of input parameter types (e.g., ['DOUBLE', 'STRING'])
            output_type: Return type of the function (e.g., 'DOUBLE')
            
        Returns:
            UDFRegistrationResult indicating success or failure
        """
        try:
            # Validate function signature
            if not callable(func):
                return UDFRegistrationResult(
                    success=False,
                    function_name=name,
                    error_message=f"Provided object '{name}' is not callable"
                )
            
            # Store function reference for later use
            self._registered_functions[name] = func
            
            # In actual implementation, this would register with KuzuDB
            # For now, we prepare the registration but KuzuDB Python API
            # doesn't yet support UDF registration directly
            
            return UDFRegistrationResult(
                success=True,
                function_name=name
            )
            
        except Exception as e:
            return UDFRegistrationResult(
                success=False,
                function_name=name,
                error_message=str(e)
            )
    
    def unregister_function(self, name: str) -> UDFRegistrationResult:
        """Unregister a UDF from KuzuDB
        
        Args:
            name: Name of the function to unregister
            
        Returns:
            UDFRegistrationResult indicating success or failure
        """
        if name not in self._registered_functions:
            return UDFRegistrationResult(
                success=False,
                function_name=name,
                error_message=f"Function '{name}' is not registered"
            )
        
        try:
            # Remove from internal registry
            del self._registered_functions[name]
            
            # In actual implementation, this would unregister from KuzuDB
            
            return UDFRegistrationResult(
                success=True,
                function_name=name
            )
            
        except Exception as e:
            return UDFRegistrationResult(
                success=False,
                function_name=name,
                error_message=str(e)
            )
    
    def list_registered_functions(self) -> List[str]:
        """Get list of all registered UDF names
        
        Returns:
            List of registered function names
        """
        return list(self._registered_functions.keys())
    
    def is_registered(self, name: str) -> bool:
        """Check if a function is registered
        
        Args:
            name: Function name to check
            
        Returns:
            True if function is registered, False otherwise
        """
        return name in self._registered_functions


class CommissionCalculator:
    """Business logic for commission calculations as UDFs
    
    This class contains static methods that can be registered as UDFs
    for calculating commissions within the graph database.
    """
    
    @staticmethod
    def calculate_base_commission(
        contract_value: float,
        commission_rate: float
    ) -> Dict[str, Union[bool, float, str]]:
        """Calculate base commission for a contract
        
        Args:
            contract_value: Total contract value
            commission_rate: Commission percentage (0.0 to 1.0)
            
        Returns:
            Result dict with commission amount or error
        """
        try:
            if contract_value < 0:
                return {
                    "ok": False,
                    "error": "Contract value cannot be negative"
                }
            
            if not 0 <= commission_rate <= 1:
                return {
                    "ok": False,
                    "error": "Commission rate must be between 0 and 1"
                }
            
            commission = contract_value * commission_rate
            
            return {
                "ok": True,
                "value": round(commission, 2)
            }
            
        except Exception as e:
            return {
                "ok": False,
                "error": str(e)
            }
    
    @staticmethod
    def calculate_tiered_commission(
        contract_value: float,
        tier_thresholds: List[float],
        tier_rates: List[float]
    ) -> Dict[str, Union[bool, float, str]]:
        """Calculate commission based on tiered rates
        
        Args:
            contract_value: Total contract value
            tier_thresholds: List of value thresholds for each tier
            tier_rates: List of commission rates for each tier
            
        Returns:
            Result dict with commission amount or error
        """
        try:
            if contract_value < 0:
                return {
                    "ok": False,
                    "error": "Contract value cannot be negative"
                }
            
            if len(tier_thresholds) != len(tier_rates):
                return {
                    "ok": False,
                    "error": "Tier thresholds and rates must have same length"
                }
            
            # Find applicable tier
            applicable_rate = 0.0
            for i, threshold in enumerate(tier_thresholds):
                if contract_value >= threshold:
                    applicable_rate = tier_rates[i]
                else:
                    break
            
            commission = contract_value * applicable_rate
            
            return {
                "ok": True,
                "value": round(commission, 2)
            }
            
        except Exception as e:
            return {
                "ok": False,
                "error": str(e)
            }
    
    @staticmethod
    def calculate_referral_chain_commission(
        base_commission: float,
        chain_level: int,
        decay_factor: float = 0.5
    ) -> Dict[str, Union[bool, float, str]]:
        """Calculate commission for referral chain members
        
        Args:
            base_commission: Original commission amount
            chain_level: Level in the referral chain (0 = direct, 1 = first referrer, etc.)
            decay_factor: Factor by which commission decreases per level
            
        Returns:
            Result dict with commission amount or error
        """
        try:
            if base_commission < 0:
                return {
                    "ok": False,
                    "error": "Base commission cannot be negative"
                }
            
            if chain_level < 0:
                return {
                    "ok": False,
                    "error": "Chain level cannot be negative"
                }
            
            if not 0 < decay_factor < 1:
                return {
                    "ok": False,
                    "error": "Decay factor must be between 0 and 1"
                }
            
            # Calculate commission with exponential decay
            commission = base_commission * (decay_factor ** chain_level)
            
            return {
                "ok": True,
                "value": round(commission, 2)
            }
            
        except Exception as e:
            return {
                "ok": False,
                "error": str(e)
            }


def create_default_registry(connection: kuzu.Connection) -> UDFRegistry:
    """Create a UDF registry with default business functions registered
    
    Args:
        connection: Active KuzuDB connection
        
    Returns:
        UDFRegistry instance with common functions pre-registered
    """
    registry = UDFRegistry(connection)
    
    # Register commission calculation functions
    registry.register_function(
        name="calculate_base_commission",
        func=CommissionCalculator.calculate_base_commission,
        input_types=["DOUBLE", "DOUBLE"],
        output_type="STRUCT"
    )
    
    registry.register_function(
        name="calculate_tiered_commission",
        func=CommissionCalculator.calculate_tiered_commission,
        input_types=["DOUBLE", "LIST", "LIST"],
        output_type="STRUCT"
    )
    
    registry.register_function(
        name="calculate_referral_chain_commission",
        func=CommissionCalculator.calculate_referral_chain_commission,
        input_types=["DOUBLE", "INT64", "DOUBLE"],
        output_type="STRUCT"
    )
    
    return registry