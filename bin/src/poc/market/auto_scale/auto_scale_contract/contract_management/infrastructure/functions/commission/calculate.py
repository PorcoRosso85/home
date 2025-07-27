"""Commission calculation implementation.

Following error handling conventions: return results, no exceptions.
"""

from decimal import Decimal
from typing import Dict, List, Any, Optional


class CommissionCalculator:
    """Calculate commissions for various scenarios."""
    
    def calculate(self, amount: Decimal, rate: Decimal) -> Decimal:
        """Calculate basic commission."""
        return amount * rate
    
    def calculate_tiered(self, amount: Decimal, tiers: List[Dict[str, Any]]) -> Decimal:
        """Calculate commission based on tiered rates."""
        for tier in tiers:
            min_amount = tier["min_amount"]
            max_amount = tier["max_amount"]
            
            if max_amount is None:
                if amount >= min_amount:
                    return amount * tier["rate"]
            elif min_amount <= amount < max_amount:
                return amount * tier["rate"]
        
        return Decimal("0")
    
    def distribute_referral_commission(
        self,
        base_commission: Decimal,
        referral_chain: List[Dict[str, Any]]
    ) -> Dict[str, Decimal]:
        """Distribute commission across referral chain."""
        distribution = {}
        
        for agent in referral_chain:
            agent_id = agent["agent_id"]
            percentage = agent["percentage"]
            distribution[agent_id] = base_commission * percentage
        
        return distribution
    
    def calculate_with_caps(
        self,
        amount: Decimal,
        rules: Dict[str, Any]
    ) -> Decimal:
        """Calculate commission with minimum and maximum caps."""
        rate = rules["rate"]
        minimum = rules["minimum"]
        maximum = rules["maximum"]
        
        commission = amount * rate
        
        if commission < minimum:
            return minimum
        elif commission > maximum:
            return maximum
        
        return commission
    
    def calculate_bundle_commission(
        self,
        bundle_items: List[Dict[str, Any]]
    ) -> Decimal:
        """Calculate total commission for bundled products."""
        total_commission = Decimal("0")
        
        for item in bundle_items:
            item_commission = item["amount"] * item["rate"]
            total_commission += item_commission
        
        return total_commission