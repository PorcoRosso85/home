"""Contract Management Module - Public API

This module exports the public API for contract management,
following Domain-Driven Design principles with a lightweight approach.
"""

# Domain Layer - Core business logic and entities
from .domain import (
    # Enums
    ContractStatus,
    PaymentTerms,
    
    # Value Objects
    ContractId,
    Money,
    DateRange,
    
    # Entities
    ContractParty,
    ContractTerm,
    Contract,
    
    # Repository Interface
    ContractRepository,
    
    # Specifications
    ContractSpecification,
    ActiveContractSpecification,
    HighValueContractSpecification,
)

# Application Layer - Use cases and DTOs
from .application import (
    # DTOs
    CreateContractRequest,
    ContractResponse,
    ContractListResponse,
    NetworkMetricsResponse,
    GrowthPredictionResponse,
    CommunityDiscountResponse,
    ReferralRewardResponse,
    
    # Services
    ContractService,
    ContractAnalyticsService,
    
    # Use Cases
    ContractUseCase,
    CreateContractUseCase,
    ActivateContractUseCase,
    ListActiveContractsUseCase,
    
    # Events
    ContractCreatedEvent,
    ContractActivatedEvent,
    ContractTerminatedEvent,
    ContractEventHandler,
    
    # Exceptions
    ContractNotFoundError,
    InvalidContractStateError,
)

# Infrastructure Layer - Concrete implementations
# Note: Infrastructure implementations are not yet available
# Infrastructure Layer - Concrete implementations
# Import from repositories module (renamed from infrastructure.py)
from .repositories import KuzuGraphRepository

__all__ = [
    # Domain Layer
    "ContractStatus",
    "PaymentTerms",
    "ContractId",
    "Money",
    "DateRange",
    "ContractParty",
    "ContractTerm",
    "Contract",
    "ContractRepository",
    "ContractSpecification",
    "ActiveContractSpecification",
    "HighValueContractSpecification",
    
    # Application Layer
    "CreateContractRequest",
    "ContractResponse",
    "ContractListResponse",
    "NetworkMetricsResponse",
    "GrowthPredictionResponse",
    "CommunityDiscountResponse",
    "ReferralRewardResponse",
    "ContractService",
    "ContractAnalyticsService",
    "ContractUseCase",
    "CreateContractUseCase",
    "ActivateContractUseCase",
    "ListActiveContractsUseCase",
    "ContractCreatedEvent",
    "ContractActivatedEvent",
    "ContractTerminatedEvent",
    "ContractEventHandler",
    "ContractNotFoundError",
    "InvalidContractStateError",
    
    # Infrastructure Layer
    # Note: Infrastructure implementations are not yet available
    # "InMemoryContractRepository",
    "KuzuGraphRepository",
    # "SQLiteContractRepository",
    # "FileSystemContractRepository",
    # "EmailNotificationService",
    # "ContractDocumentGenerator",
    # "ContractAuditLogger",
]