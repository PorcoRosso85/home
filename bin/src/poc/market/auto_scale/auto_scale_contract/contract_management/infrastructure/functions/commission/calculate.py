"""Commission calculation implementation for auto-scale mechanism.

RESPONSIBILITY: Enable viral growth through multi-tier referral rewards.
AUTO-SCALE CONTRIBUTION: Incentivizes customers to refer others by providing
diminishing but meaningful rewards across multiple referral levels (15% → 7.5% → 3.75%).

Following error handling conventions: return results, no exceptions.
"""

from decimal import Decimal
from typing import Dict, List, Any, Optional


class CommissionCalculator:
    """Calculate commissions for auto-scale referral system.
    
    Core responsibility: Distribute rewards across referral chains to create
    self-reinforcing customer acquisition loops.
    """
    
    def calculate(self, amount: Decimal, rate: Decimal) -> Decimal:
        """Calculate basic commission.
        
        Used as the foundation for all commission calculations in the
        referral reward system.
        """
        return amount * rate
    
    def calculate_tiered(self, amount: Decimal, tiers: List[Dict[str, Any]]) -> Decimal:
        """Calculate commission based on tiered rates.
        
        AUTO-SCALE: Rewards high-value referrals with better rates,
        encouraging quality over quantity in customer acquisition.
        """
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
        """Distribute commission across referral chain.
        
        AUTO-SCALE: Core mechanism that rewards multiple levels of referrers,
        creating network effects where each customer has incentive to grow
        the network further. Implements diminishing returns to maintain
        profitability while encouraging viral growth.
        """
        distribution = {}
        
        for agent in referral_chain:
            agent_id = agent["agent_id"]
            percentage = agent["percentage"]
            distribution[agent_id] = base_commission * percentage
        
        return distribution