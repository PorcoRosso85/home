"""Contract Management Domain Layer

This module contains the core business logic, entities, and value objects
for contract management following Domain-Driven Design principles.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4


class ContractStatus(Enum):
    """Contract lifecycle states"""
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    EXPIRED = "expired"


class PaymentTerms(Enum):
    """Payment terms options"""
    NET_30 = "net_30"
    NET_60 = "net_60"
    NET_90 = "net_90"
    IMMEDIATE = "immediate"
    ON_DELIVERY = "on_delivery"


@dataclass(frozen=True)
class ContractId:
    """Value object for contract identification"""
    value: UUID
    
    @classmethod
    def generate(cls) -> 'ContractId':
        """Generate a new contract ID"""
        return cls(value=uuid4())
    
    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class Money:
    """Value object for monetary amounts"""
    amount: Decimal
    currency: str = "USD"
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Money amount cannot be negative")
        if not self.currency:
            raise ValueError("Currency code is required")
    
    def add(self, other: 'Money') -> 'Money':
        """Add two money values"""
        if self.currency != other.currency:
            raise ValueError(f"Cannot add different currencies: {self.currency} and {other.currency}")
        return Money(self.amount + other.amount, self.currency)


@dataclass(frozen=True)
class DateRange:
    """Value object for date ranges"""
    start_date: datetime
    end_date: datetime
    
    def __post_init__(self):
        if self.end_date <= self.start_date:
            raise ValueError("End date must be after start date")
    
    def contains(self, date: datetime) -> bool:
        """Check if a date is within the range"""
        return self.start_date <= date <= self.end_date
    
    @property
    def duration_days(self) -> int:
        """Get duration in days"""
        return (self.end_date - self.start_date).days


@dataclass
class ContractParty:
    """Entity representing a party in a contract"""
    party_id: str
    name: str
    contact_email: str
    contact_phone: Optional[str] = None
    address: Optional[str] = None


@dataclass
class ContractTerm:
    """Value object for contract terms and conditions"""
    term_id: str
    title: str
    description: str
    is_mandatory: bool = True


@dataclass
class Contract:
    """Aggregate root for contract management"""
    contract_id: ContractId
    title: str
    description: str
    client: ContractParty
    vendor: ContractParty
    value: Money
    validity_period: DateRange
    payment_terms: PaymentTerms
    status: ContractStatus
    terms: List[ContractTerm]
    created_at: datetime
    updated_at: datetime
    
    def activate(self) -> None:
        """Activate the contract"""
        if self.status != ContractStatus.DRAFT:
            raise ValueError(f"Cannot activate contract in {self.status} status")
        if datetime.now() < self.validity_period.start_date:
            raise ValueError("Cannot activate contract before start date")
        self.status = ContractStatus.ACTIVE
        self.updated_at = datetime.now()
    
    def suspend(self) -> None:
        """Suspend the contract"""
        if self.status != ContractStatus.ACTIVE:
            raise ValueError(f"Cannot suspend contract in {self.status} status")
        self.status = ContractStatus.SUSPENDED
        self.updated_at = datetime.now()
    
    def terminate(self) -> None:
        """Terminate the contract"""
        if self.status in [ContractStatus.TERMINATED, ContractStatus.EXPIRED]:
            raise ValueError(f"Contract is already {self.status}")
        self.status = ContractStatus.TERMINATED
        self.updated_at = datetime.now()
    
    def is_valid_on(self, date: datetime) -> bool:
        """Check if contract is valid on a specific date"""
        return (self.status == ContractStatus.ACTIVE and 
                self.validity_period.contains(date))
    
    def add_term(self, term: ContractTerm) -> None:
        """Add a term to the contract"""
        if self.status != ContractStatus.DRAFT:
            raise ValueError("Cannot modify terms of non-draft contract")
        self.terms.append(term)
        self.updated_at = datetime.now()


class ContractRepository:
    """Repository interface for contract persistence"""
    
    def save(self, contract: Contract) -> None:
        """Save a contract"""
        raise NotImplementedError
    
    def find_by_id(self, contract_id: ContractId) -> Optional[Contract]:
        """Find a contract by ID"""
        raise NotImplementedError
    
    def find_active_contracts(self) -> List[Contract]:
        """Find all active contracts"""
        raise NotImplementedError
    
    def find_by_client(self, client_id: str) -> List[Contract]:
        """Find contracts by client"""
        raise NotImplementedError


class ContractSpecification:
    """Specification pattern for contract queries"""
    
    def is_satisfied_by(self, contract: Contract) -> bool:
        """Check if contract satisfies the specification"""
        raise NotImplementedError


class ActiveContractSpecification(ContractSpecification):
    """Specification for active contracts"""
    
    def is_satisfied_by(self, contract: Contract) -> bool:
        return contract.status == ContractStatus.ACTIVE


class HighValueContractSpecification(ContractSpecification):
    """Specification for high-value contracts"""
    
    def __init__(self, threshold: Money):
        self.threshold = threshold
    
    def is_satisfied_by(self, contract: Contract) -> bool:
        return (contract.value.amount >= self.threshold.amount and 
                contract.value.currency == self.threshold.currency)