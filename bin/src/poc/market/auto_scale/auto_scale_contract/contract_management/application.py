"""Contract Management Application Layer

This module contains use cases, application services, and DTOs
that orchestrate the domain logic and handle application-specific concerns.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from .domain import (
    Contract, ContractId, ContractParty, ContractStatus,
    ContractTerm, Money, DateRange, PaymentTerms,
    ContractRepository, ContractSpecification,
    ActiveContractSpecification, HighValueContractSpecification
)


# Data Transfer Objects (DTOs)

@dataclass
class CreateContractRequest:
    """DTO for contract creation requests"""
    title: str
    description: str
    client_id: str
    client_name: str
    client_email: str
    vendor_id: str
    vendor_name: str
    vendor_email: str
    value_amount: Decimal
    currency: str
    start_date: datetime
    end_date: datetime
    payment_terms: str
    terms: List[Dict[str, Any]]


@dataclass
class ContractResponse:
    """DTO for contract responses"""
    contract_id: str
    title: str
    description: str
    client_name: str
    vendor_name: str
    value: str
    status: str
    start_date: str
    end_date: str
    payment_terms: str
    created_at: str
    updated_at: str


@dataclass
class ContractListResponse:
    """DTO for contract list responses"""
    contracts: List[ContractResponse]
    total_count: int


# Application Services

class ContractService:
    """Application service for contract management"""
    
    def __init__(self, repository: ContractRepository):
        self.repository = repository
    
    def create_contract(self, request: CreateContractRequest) -> ContractResponse:
        """Create a new contract"""
        # Create value objects
        contract_id = ContractId.generate()
        
        client = ContractParty(
            party_id=request.client_id,
            name=request.client_name,
            contact_email=request.client_email
        )
        
        vendor = ContractParty(
            party_id=request.vendor_id,
            name=request.vendor_name,
            contact_email=request.vendor_email
        )
        
        value = Money(
            amount=request.value_amount,
            currency=request.currency
        )
        
        validity_period = DateRange(
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        # Create terms
        terms = []
        for term_data in request.terms:
            term = ContractTerm(
                term_id=term_data['id'],
                title=term_data['title'],
                description=term_data['description'],
                is_mandatory=term_data.get('is_mandatory', True)
            )
            terms.append(term)
        
        # Create contract entity
        contract = Contract(
            contract_id=contract_id,
            title=request.title,
            description=request.description,
            client=client,
            vendor=vendor,
            value=value,
            validity_period=validity_period,
            payment_terms=PaymentTerms(request.payment_terms),
            status=ContractStatus.DRAFT,
            terms=terms,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Save to repository
        self.repository.save(contract)
        
        return self._to_response(contract)
    
    def activate_contract(self, contract_id: str) -> ContractResponse:
        """Activate a contract"""
        contract = self._get_contract(contract_id)
        contract.activate()
        self.repository.save(contract)
        return self._to_response(contract)
    
    def suspend_contract(self, contract_id: str) -> ContractResponse:
        """Suspend a contract"""
        contract = self._get_contract(contract_id)
        contract.suspend()
        self.repository.save(contract)
        return self._to_response(contract)
    
    def terminate_contract(self, contract_id: str) -> ContractResponse:
        """Terminate a contract"""
        contract = self._get_contract(contract_id)
        contract.terminate()
        self.repository.save(contract)
        return self._to_response(contract)
    
    def get_contract(self, contract_id: str) -> ContractResponse:
        """Get a contract by ID"""
        contract = self._get_contract(contract_id)
        return self._to_response(contract)
    
    def list_active_contracts(self) -> ContractListResponse:
        """List all active contracts"""
        contracts = self.repository.find_active_contracts()
        responses = [self._to_response(c) for c in contracts]
        return ContractListResponse(
            contracts=responses,
            total_count=len(responses)
        )
    
    def list_client_contracts(self, client_id: str) -> ContractListResponse:
        """List contracts for a specific client"""
        contracts = self.repository.find_by_client(client_id)
        responses = [self._to_response(c) for c in contracts]
        return ContractListResponse(
            contracts=responses,
            total_count=len(responses)
        )
    
    def find_high_value_contracts(self, threshold_amount: Decimal, 
                                  currency: str = "USD") -> ContractListResponse:
        """Find contracts above a certain value threshold"""
        threshold = Money(threshold_amount, currency)
        spec = HighValueContractSpecification(threshold)
        
        # This is a simplified implementation
        # In a real system, this would be pushed down to the repository
        all_contracts = self.repository.find_active_contracts()
        high_value_contracts = [c for c in all_contracts if spec.is_satisfied_by(c)]
        
        responses = [self._to_response(c) for c in high_value_contracts]
        return ContractListResponse(
            contracts=responses,
            total_count=len(responses)
        )
    
    def _get_contract(self, contract_id: str) -> Contract:
        """Get contract by ID with error handling"""
        contract_uuid = ContractId(UUID(contract_id))
        contract = self.repository.find_by_id(contract_uuid)
        if not contract:
            raise ContractNotFoundError(f"Contract {contract_id} not found")
        return contract
    
    def _to_response(self, contract: Contract) -> ContractResponse:
        """Convert domain entity to response DTO"""
        return ContractResponse(
            contract_id=str(contract.contract_id),
            title=contract.title,
            description=contract.description,
            client_name=contract.client.name,
            vendor_name=contract.vendor.name,
            value=f"{contract.value.amount} {contract.value.currency}",
            status=contract.status.value,
            start_date=contract.validity_period.start_date.isoformat(),
            end_date=contract.validity_period.end_date.isoformat(),
            payment_terms=contract.payment_terms.value,
            created_at=contract.created_at.isoformat(),
            updated_at=contract.updated_at.isoformat()
        )


# Use Cases

class ContractUseCase:
    """Base class for contract use cases"""
    
    def __init__(self, repository: ContractRepository):
        self.repository = repository


class CreateContractUseCase(ContractUseCase):
    """Use case for creating contracts"""
    
    def execute(self, request: CreateContractRequest) -> ContractResponse:
        """Execute the use case"""
        service = ContractService(self.repository)
        return service.create_contract(request)


class ActivateContractUseCase(ContractUseCase):
    """Use case for activating contracts"""
    
    def execute(self, contract_id: str) -> ContractResponse:
        """Execute the use case"""
        service = ContractService(self.repository)
        return service.activate_contract(contract_id)


class ListActiveContractsUseCase(ContractUseCase):
    """Use case for listing active contracts"""
    
    def execute(self) -> ContractListResponse:
        """Execute the use case"""
        service = ContractService(self.repository)
        return service.list_active_contracts()


# Application Exceptions

class ContractNotFoundError(Exception):
    """Exception raised when contract is not found"""
    pass


class InvalidContractStateError(Exception):
    """Exception raised when contract operation is invalid for current state"""
    pass


# Event Handlers (for event-driven architecture)

@dataclass
class ContractCreatedEvent:
    """Event emitted when a contract is created"""
    contract_id: str
    title: str
    client_id: str
    vendor_id: str
    value: str
    created_at: datetime


@dataclass
class ContractActivatedEvent:
    """Event emitted when a contract is activated"""
    contract_id: str
    activated_at: datetime


@dataclass
class ContractTerminatedEvent:
    """Event emitted when a contract is terminated"""
    contract_id: str
    terminated_at: datetime
    reason: Optional[str] = None


class ContractEventHandler:
    """Handler for contract-related events"""
    
    def handle_contract_created(self, event: ContractCreatedEvent) -> None:
        """Handle contract created event"""
        # Implementation would depend on specific requirements
        # e.g., send notifications, update analytics, etc.
        pass
    
    def handle_contract_activated(self, event: ContractActivatedEvent) -> None:
        """Handle contract activated event"""
        pass
    
    def handle_contract_terminated(self, event: ContractTerminatedEvent) -> None:
        """Handle contract terminated event"""
        pass