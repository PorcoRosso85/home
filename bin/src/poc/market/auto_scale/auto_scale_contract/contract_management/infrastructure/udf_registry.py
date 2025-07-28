"""User Defined Functions (UDF) Registry for KuzuDB

RESPONSIBILITY: Bridge between Python auto-scale functions and future GraphDB UDFs.
AUTO-SCALE CONTRIBUTION: Prepares the system for moving all viral growth logic
into the database layer, enabling true scalability without application bottlenecks.

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


# Note: CommissionCalculator removed - use functions from infrastructure/functions/ instead


def create_default_registry(connection: kuzu.Connection) -> UDFRegistry:
    """Create a UDF registry for auto-scale functions
    
    AUTO-SCALE: Registers all viral growth functions that will eventually
    run as UDFs within KuzuDB, enabling database-level auto-scaling logic.
    
    Args:
        connection: Active KuzuDB connection
        
    Returns:
        UDFRegistry instance ready for auto-scale function registration
    """
    registry = UDFRegistry(connection)
    
    # Import auto-scale functions
    from .functions.commission.calculate import CommissionCalculator
    from .functions.growth import metrics
    from .functions.referral import traverse
    
    # Register commission functions for multi-tier rewards
    commission_calc = CommissionCalculator()
    registry.register_function(
        name="calculate_commission",
        func=commission_calc.calculate,
        input_types=["DOUBLE", "DOUBLE"],
        output_type="DOUBLE"
    )
    
    registry.register_function(
        name="distribute_referral_commission",
        func=commission_calc.distribute_referral_commission,
        input_types=["DOUBLE", "LIST"],
        output_type="MAP"
    )
    
    # Register growth metrics for viral coefficient tracking
    registry.register_function(
        name="calculate_k_factor",
        func=metrics.calculate_k_factor,
        input_types=["INT64", "DOUBLE", "MAP"],
        output_type="STRUCT"
    )
    
    registry.register_function(
        name="calculate_network_value",
        func=metrics.calculate_network_value,
        input_types=["INT64", "DOUBLE", "MAP"],
        output_type="STRUCT"
    )
    
    # Register referral traversal for commission distribution
    registry.register_function(
        name="traverse_referral_upward",
        func=traverse.traverse_upward,
        input_types=["STRING", "INT64"],
        output_type="STRUCT"
    )
    
    return registry