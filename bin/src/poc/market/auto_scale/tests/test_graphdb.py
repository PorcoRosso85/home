"""
Test suite for KuzuGraphRepository implementation

This module tests the graph database functionality for the auto-scale contract management system,
including in-memory database initialization, schema application, and hierarchical contract relationships.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from auto_scale_contract.contract_management.domain import (
    Contract, ContractId, ContractParty, ContractStatus,
    ContractTerm, Money, DateRange, PaymentTerms,
    ContractRepository
)


# Mock KuzuGraphRepository for testing
# In production, this would be imported from infrastructure module
class KuzuGraphRepository(ContractRepository):
    """Graph database implementation of contract repository using KuzuDB"""
    
    def __init__(self, db_path: str = ":memory:"):
        """
        Initialize KuzuGraphRepository
        
        Args:
            db_path: Path to database file or ":memory:" for in-memory database
        """
        try:
            import kuzu
        except ImportError:
            pytest.skip("kuzu module not available - run tests in nix environment")
        
        self.db_path = db_path
        self.db = kuzu.Database(db_path)
        self.conn = kuzu.Connection(self.db)
        self._init_schema()
    
    def _init_schema(self) -> None:
        """Initialize the graph database schema"""
        # Create node tables
        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS Contract (
                contract_id STRING PRIMARY KEY,
                title STRING,
                description STRING,
                client_id STRING,
                client_name STRING,
                client_email STRING,
                vendor_id STRING,
                vendor_name STRING,
                vendor_email STRING,
                value_amount STRING,
                value_currency STRING,
                start_date STRING,
                end_date STRING,
                payment_terms STRING,
                status STRING,
                created_at STRING,
                updated_at STRING
            )
        """)
        
        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS ContractTerm (
                term_id STRING PRIMARY KEY,
                title STRING,
                description STRING,
                is_mandatory BOOLEAN
            )
        """)
        
        # Create relationship tables
        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS HAS_TERM (
                FROM Contract TO ContractTerm
            )
        """)
        
        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS PARENT_OF (
                FROM Contract TO Contract,
                relationship_type STRING
            )
        """)
    
    def save(self, contract: Contract) -> None:
        """Save a contract to the graph database"""
        # Convert contract to node data
        contract_data = {
            "contract_id": str(contract.contract_id),
            "title": contract.title,
            "description": contract.description or "",
            "client_id": contract.client.party_id,
            "client_name": contract.client.name,
            "client_email": contract.client.contact_email,
            "vendor_id": contract.vendor.party_id,
            "vendor_name": contract.vendor.name,
            "vendor_email": contract.vendor.contact_email,
            "value_amount": str(contract.value.amount),
            "value_currency": contract.value.currency,
            "start_date": contract.validity_period.start_date.isoformat(),
            "end_date": contract.validity_period.end_date.isoformat(),
            "payment_terms": contract.payment_terms.value,
            "status": contract.status.value,
            "created_at": contract.created_at.isoformat(),
            "updated_at": contract.updated_at.isoformat()
        }
        
        # Upsert contract node
        self.conn.execute("""
            MERGE (c:Contract {contract_id: $contract_id})
            SET c.title = $title,
                c.description = $description,
                c.client_id = $client_id,
                c.client_name = $client_name,
                c.client_email = $client_email,
                c.vendor_id = $vendor_id,
                c.vendor_name = $vendor_name,
                c.vendor_email = $vendor_email,
                c.value_amount = $value_amount,
                c.value_currency = $value_currency,
                c.start_date = $start_date,
                c.end_date = $end_date,
                c.payment_terms = $payment_terms,
                c.status = $status,
                c.created_at = $created_at,
                c.updated_at = $updated_at
        """, contract_data)
        
        # Save terms and relationships
        for term in contract.terms:
            term_data = {
                "term_id": term.term_id,
                "title": term.title,
                "description": term.description,
                "is_mandatory": term.is_mandatory
            }
            
            self.conn.execute("""
                MERGE (t:ContractTerm {term_id: $term_id})
                SET t.title = $title,
                    t.description = $description,
                    t.is_mandatory = $is_mandatory
            """, term_data)
            
            # Create relationship
            self.conn.execute("""
                MATCH (c:Contract {contract_id: $contract_id})
                MATCH (t:ContractTerm {term_id: $term_id})
                MERGE (c)-[:HAS_TERM]->(t)
            """, {"contract_id": str(contract.contract_id), "term_id": term.term_id})
    
    def find_by_id(self, contract_id: ContractId) -> Optional[Contract]:
        """Find a contract by ID"""
        result = self.conn.execute("""
            MATCH (c:Contract {contract_id: $contract_id})
            OPTIONAL MATCH (c)-[:HAS_TERM]->(t:ContractTerm)
            RETURN c, collect(t) as terms
        """, {"contract_id": str(contract_id)})
        
        if result.has_next():
            row = result.get_next()
            contract_node = row[0]
            term_nodes = row[1]
            
            return self._node_to_contract(contract_node, term_nodes)
        
        return None
    
    def find_active_contracts(self) -> List[Contract]:
        """Find all active contracts"""
        result = self.conn.execute("""
            MATCH (c:Contract {status: $status})
            OPTIONAL MATCH (c)-[:HAS_TERM]->(t:ContractTerm)
            RETURN c, collect(t) as terms
        """, {"status": ContractStatus.ACTIVE.value})
        
        contracts = []
        while result.has_next():
            row = result.get_next()
            contract_node = row[0]
            term_nodes = row[1]
            contracts.append(self._node_to_contract(contract_node, term_nodes))
        
        return contracts
    
    def find_by_client(self, client_id: str) -> List[Contract]:
        """Find contracts by client"""
        result = self.conn.execute("""
            MATCH (c:Contract {client_id: $client_id})
            OPTIONAL MATCH (c)-[:HAS_TERM]->(t:ContractTerm)
            RETURN c, collect(t) as terms
        """, {"client_id": client_id})
        
        contracts = []
        while result.has_next():
            row = result.get_next()
            contract_node = row[0]
            term_nodes = row[1]
            contracts.append(self._node_to_contract(contract_node, term_nodes))
        
        return contracts
    
    def add_parent_child_relationship(self, parent_id: ContractId, child_id: ContractId, 
                                      relationship_type: str = "SUBCONTRACT") -> None:
        """Add a parent-child relationship between contracts"""
        self.conn.execute("""
            MATCH (p:Contract {contract_id: $parent_id})
            MATCH (c:Contract {contract_id: $child_id})
            MERGE (p)-[:PARENT_OF {relationship_type: $rel_type}]->(c)
        """, {
            "parent_id": str(parent_id),
            "child_id": str(child_id),
            "rel_type": relationship_type
        })
    
    def find_child_contracts(self, parent_id: ContractId) -> List[Contract]:
        """Find all child contracts of a parent contract"""
        result = self.conn.execute("""
            MATCH (p:Contract {contract_id: $parent_id})-[:PARENT_OF]->(c:Contract)
            OPTIONAL MATCH (c)-[:HAS_TERM]->(t:ContractTerm)
            RETURN c, collect(t) as terms
        """, {"parent_id": str(parent_id)})
        
        contracts = []
        while result.has_next():
            row = result.get_next()
            contract_node = row[0]
            term_nodes = row[1]
            contracts.append(self._node_to_contract(contract_node, term_nodes))
        
        return contracts
    
    def find_parent_contract(self, child_id: ContractId) -> Optional[Contract]:
        """Find the parent contract of a child contract"""
        result = self.conn.execute("""
            MATCH (p:Contract)-[:PARENT_OF]->(c:Contract {contract_id: $child_id})
            OPTIONAL MATCH (p)-[:HAS_TERM]->(t:ContractTerm)
            RETURN p, collect(t) as terms
        """, {"child_id": str(child_id)})
        
        if result.has_next():
            row = result.get_next()
            contract_node = row[0]
            term_nodes = row[1]
            return self._node_to_contract(contract_node, term_nodes)
        
        return None
    
    def _node_to_contract(self, contract_node: Dict[str, Any], term_nodes: List[Dict[str, Any]]) -> Contract:
        """Convert graph node to Contract domain object"""
        # Reconstruct ContractParty objects
        client = ContractParty(
            party_id=contract_node["client_id"],
            name=contract_node["client_name"],
            contact_email=contract_node["client_email"],
            contact_phone=None,
            address=None
        )
        
        vendor = ContractParty(
            party_id=contract_node["vendor_id"],
            name=contract_node["vendor_name"],
            contact_email=contract_node["vendor_email"],
            contact_phone=None,
            address=None
        )
        
        # Reconstruct ContractTerm objects
        terms = []
        if term_nodes is not None:  # Handle case where collect() returns None
            for term_node in term_nodes:
                if term_node:  # Check if term_node is not None
                    terms.append(ContractTerm(
                        term_id=term_node["term_id"],
                        title=term_node["title"],
                        description=term_node["description"],
                        is_mandatory=term_node["is_mandatory"]
                    ))
        
        # Reconstruct Contract object
        return Contract(
            contract_id=ContractId(UUID(contract_node["contract_id"])),
            title=contract_node["title"],
            description=contract_node["description"] if contract_node["description"] else "",
            client=client,
            vendor=vendor,
            value=Money(Decimal(contract_node["value_amount"]), contract_node["value_currency"]),
            validity_period=DateRange(
                start_date=datetime.fromisoformat(contract_node["start_date"]),
                end_date=datetime.fromisoformat(contract_node["end_date"])
            ),
            payment_terms=PaymentTerms(contract_node["payment_terms"]),
            status=ContractStatus(contract_node["status"]),
            terms=terms,
            created_at=datetime.fromisoformat(contract_node["created_at"]),
            updated_at=datetime.fromisoformat(contract_node["updated_at"])
        )


# Fixtures

@pytest.fixture
def in_memory_db():
    """Provide an in-memory KuzuDB instance for testing"""
    repo = KuzuGraphRepository(":memory:")
    yield repo
    # Cleanup is automatic for in-memory databases


@pytest.fixture
def sample_contract():
    """Provide a sample contract for testing"""
    now = datetime.now()
    return Contract(
        contract_id=ContractId(uuid4()),
        title="Software Development Agreement",
        description="Agreement for custom software development",
        client=ContractParty(
            party_id="client-001",
            name="Acme Corporation",
            contact_email="contact@acme.com",
            contact_phone="+1-555-1234",
            address="123 Main St, City"
        ),
        vendor=ContractParty(
            party_id="vendor-001",
            name="TechSolutions Inc",
            contact_email="sales@techsolutions.com",
            contact_phone="+1-555-5678",
            address="456 Tech Ave, City"
        ),
        value=Money(Decimal("50000.00"), "USD"),
        validity_period=DateRange(
            start_date=now,
            end_date=now + timedelta(days=365)
        ),
        payment_terms=PaymentTerms.NET_30,
        status=ContractStatus.ACTIVE,
        terms=[
            ContractTerm(
                term_id="term-001",
                title="Delivery Timeline",
                description="Software must be delivered within 6 months",
                is_mandatory=True
            ),
            ContractTerm(
                term_id="term-002",
                title="Support Period",
                description="12 months of support included",
                is_mandatory=True
            )
        ],
        created_at=now,
        updated_at=now
    )


@pytest.fixture
def multiple_contracts():
    """Provide multiple contracts for testing"""
    base_date = datetime.now()
    
    contracts = []
    for i in range(3):
        contracts.append(Contract(
            contract_id=ContractId(uuid4()),
            title=f"Contract {i+1}",
            description=f"Test contract number {i+1}",
            client=ContractParty(
                party_id=f"client-{i+1:03d}",
                name=f"Client {i+1}",
                contact_email=f"client{i+1}@example.com"
            ),
            vendor=ContractParty(
                party_id="vendor-001",
                name="TechSolutions Inc",
                contact_email="sales@techsolutions.com"
            ),
            value=Money(Decimal(f"{10000 * (i+1)}.00"), "USD"),
            validity_period=DateRange(
                start_date=base_date,
                end_date=base_date + timedelta(days=90 * (i+1))
            ),
            payment_terms=PaymentTerms.NET_30,
            status=ContractStatus.ACTIVE if i < 2 else ContractStatus.DRAFT,
            terms=[
                ContractTerm(
                    term_id=f"term-{i+1}-1",
                    title=f"Term 1 for Contract {i+1}",
                    description="Standard term",
                    is_mandatory=True
                )
            ],
            created_at=base_date,
            updated_at=base_date
        ))
    
    return contracts


# Tests

class TestKuzuGraphRepositoryInitialization:
    """Test KuzuGraphRepository initialization and schema setup"""
    
    def test_in_memory_initialization(self):
        """Test that repository can be initialized with in-memory database"""
        repo = KuzuGraphRepository(":memory:")
        assert repo.db_path == ":memory:"
        assert repo.db is not None
        assert repo.conn is not None
    
    def test_schema_creation(self, in_memory_db):
        """Test that schema is properly created on initialization"""
        # Verify Contract table exists
        result = in_memory_db.conn.execute("CALL table_info('Contract') RETURN *")
        assert result.has_next()
        
        # Verify ContractTerm table exists
        result = in_memory_db.conn.execute("CALL table_info('ContractTerm') RETURN *")
        assert result.has_next()
        
        # Note: KuzuDB doesn't have a direct way to check relationship tables
        # We'll test their functionality in the relationship tests


class TestContractCRUD:
    """Test basic CRUD operations for contracts"""
    
    def test_save_and_retrieve_contract(self, in_memory_db, sample_contract):
        """Test saving and retrieving a single contract"""
        # Save contract
        in_memory_db.save(sample_contract)
        
        # Retrieve contract
        retrieved = in_memory_db.find_by_id(sample_contract.contract_id)
        
        assert retrieved is not None
        assert retrieved.contract_id == sample_contract.contract_id
        assert retrieved.title == sample_contract.title
        assert retrieved.description == sample_contract.description
        assert retrieved.client.party_id == sample_contract.client.party_id
        assert retrieved.vendor.party_id == sample_contract.vendor.party_id
        assert retrieved.value.amount == sample_contract.value.amount
        assert retrieved.value.currency == sample_contract.value.currency
        assert len(retrieved.terms) == len(sample_contract.terms)
    
    def test_find_nonexistent_contract(self, in_memory_db):
        """Test finding a contract that doesn't exist"""
        non_existent_id = ContractId(uuid4())
        result = in_memory_db.find_by_id(non_existent_id)
        assert result is None
    
    def test_find_active_contracts(self, in_memory_db, multiple_contracts):
        """Test finding all active contracts"""
        # Save all contracts
        for contract in multiple_contracts:
            in_memory_db.save(contract)
        
        # Find active contracts
        active_contracts = in_memory_db.find_active_contracts()
        
        # Should find 2 active contracts (first two in the fixture)
        assert len(active_contracts) == 2
        assert all(c.status == ContractStatus.ACTIVE for c in active_contracts)
    
    def test_find_by_client(self, in_memory_db, multiple_contracts):
        """Test finding contracts by client ID"""
        # Save all contracts
        for contract in multiple_contracts:
            in_memory_db.save(contract)
        
        # Find contracts for client-001
        client_contracts = in_memory_db.find_by_client("client-001")
        
        assert len(client_contracts) == 1
        assert client_contracts[0].client.party_id == "client-001"
    
    def test_update_contract(self, in_memory_db, sample_contract):
        """Test updating an existing contract"""
        # Save initial contract
        in_memory_db.save(sample_contract)
        
        # Modify and save again
        sample_contract.status = ContractStatus.TERMINATED
        sample_contract.updated_at = datetime.now()
        in_memory_db.save(sample_contract)
        
        # Retrieve and verify update
        retrieved = in_memory_db.find_by_id(sample_contract.contract_id)
        assert retrieved.status == ContractStatus.TERMINATED


class TestContractRelationships:
    """Test parent-child contract relationships"""
    
    def test_add_parent_child_relationship(self, in_memory_db):
        """Test creating a parent-child relationship between contracts"""
        # Create parent and child contracts
        now = datetime.now()
        parent = Contract(
            contract_id=ContractId(uuid4()),
            title="Master Service Agreement",
            description="Parent contract",
            client=ContractParty("client-001", "Big Corp", "contact@bigcorp.com"),
            vendor=ContractParty("vendor-001", "Service Provider", "sales@provider.com"),
            value=Money(Decimal("100000.00"), "USD"),
            validity_period=DateRange(now, now + timedelta(days=730)),
            payment_terms=PaymentTerms.NET_30,
            status=ContractStatus.ACTIVE,
            terms=[],
            created_at=now,
            updated_at=now
        )
        
        child = Contract(
            contract_id=ContractId(uuid4()),
            title="Project A Contract",
            description="Child contract under MSA",
            client=ContractParty("client-001", "Big Corp", "contact@bigcorp.com"),
            vendor=ContractParty("vendor-001", "Service Provider", "sales@provider.com"),
            value=Money(Decimal("25000.00"), "USD"),
            validity_period=DateRange(now, now + timedelta(days=90)),
            payment_terms=PaymentTerms.NET_30,
            status=ContractStatus.ACTIVE,
            terms=[],
            created_at=now,
            updated_at=now
        )
        
        # Save both contracts
        in_memory_db.save(parent)
        in_memory_db.save(child)
        
        # Create relationship
        in_memory_db.add_parent_child_relationship(parent.contract_id, child.contract_id)
        
        # Verify relationship from parent side
        children = in_memory_db.find_child_contracts(parent.contract_id)
        assert len(children) == 1
        assert children[0].contract_id == child.contract_id
        
        # Verify relationship from child side
        found_parent = in_memory_db.find_parent_contract(child.contract_id)
        assert found_parent is not None
        assert found_parent.contract_id == parent.contract_id
    
    def test_multiple_child_contracts(self, in_memory_db):
        """Test a parent contract with multiple children"""
        # Create parent contract
        now = datetime.now()
        parent = Contract(
            contract_id=ContractId(uuid4()),
            title="Framework Agreement",
            description="Parent framework",
            client=ContractParty("client-001", "Enterprise Co", "contact@enterprise.com"),
            vendor=ContractParty("vendor-001", "Solutions Ltd", "sales@solutions.com"),
            value=Money(Decimal("500000.00"), "USD"),
            validity_period=DateRange(now, now + timedelta(days=1095)),
            payment_terms=PaymentTerms.NET_60,
            status=ContractStatus.ACTIVE,
            terms=[],
            created_at=now,
            updated_at=now
        )
        
        in_memory_db.save(parent)
        
        # Create and link multiple child contracts
        child_ids = []
        for i in range(3):
            child = Contract(
                contract_id=ContractId(uuid4()),
                title=f"Work Order {i+1}",
                description=f"Child contract {i+1}",
                client=ContractParty("client-001", "Enterprise Co", "contact@enterprise.com"),
                vendor=ContractParty("vendor-001", "Solutions Ltd", "sales@solutions.com"),
                value=Money(Decimal(f"{50000 * (i+1)}.00"), "USD"),
                validity_period=DateRange(now, now + timedelta(days=30 * (i+1))),
                payment_terms=PaymentTerms.NET_30,
                status=ContractStatus.ACTIVE,
                terms=[],
                created_at=now,
                updated_at=now
            )
            
            in_memory_db.save(child)
            in_memory_db.add_parent_child_relationship(parent.contract_id, child.contract_id)
            child_ids.append(child.contract_id)
        
        # Verify all children are linked
        children = in_memory_db.find_child_contracts(parent.contract_id)
        assert len(children) == 3
        retrieved_child_ids = {c.contract_id for c in children}
        assert retrieved_child_ids == set(child_ids)
    
    def test_no_parent_contract(self, in_memory_db, sample_contract):
        """Test finding parent of a contract that has no parent"""
        in_memory_db.save(sample_contract)
        
        parent = in_memory_db.find_parent_contract(sample_contract.contract_id)
        assert parent is None
    
    def test_no_child_contracts(self, in_memory_db, sample_contract):
        """Test finding children of a contract that has no children"""
        in_memory_db.save(sample_contract)
        
        children = in_memory_db.find_child_contracts(sample_contract.contract_id)
        assert len(children) == 0


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_contract_with_no_terms(self, in_memory_db):
        """Test saving and retrieving a contract with no terms"""
        now = datetime.now()
        contract = Contract(
            contract_id=ContractId(uuid4()),
            title="Simple Contract",
            description="Simple contract without additional terms",
            client=ContractParty("client-001", "Client", "client@example.com"),
            vendor=ContractParty("vendor-001", "Vendor", "vendor@example.com"),
            value=Money(Decimal("1000.00"), "USD"),
            validity_period=DateRange(now, now + timedelta(days=30)),
            payment_terms=PaymentTerms.IMMEDIATE,
            status=ContractStatus.DRAFT,
            terms=[],  # No terms
            created_at=now,
            updated_at=now
        )
        
        in_memory_db.save(contract)
        retrieved = in_memory_db.find_by_id(contract.contract_id)
        
        assert retrieved is not None
        assert len(retrieved.terms) == 0
    
    def test_contract_with_empty_description(self, in_memory_db):
        """Test handling contracts with empty description"""
        now = datetime.now()
        contract = Contract(
            contract_id=ContractId(uuid4()),
            title="Contract without description",
            description="",  # Empty description
            client=ContractParty("client-001", "Client", "client@example.com"),
            vendor=ContractParty("vendor-001", "Vendor", "vendor@example.com"),
            value=Money(Decimal("5000.00"), "EUR"),
            validity_period=DateRange(now, now + timedelta(days=60)),
            payment_terms=PaymentTerms.NET_30,
            status=ContractStatus.ACTIVE,
            terms=[],
            created_at=now,
            updated_at=now
        )
        
        in_memory_db.save(contract)
        retrieved = in_memory_db.find_by_id(contract.contract_id)
        
        assert retrieved is not None
        assert retrieved.description == ""
    
    def test_large_decimal_values(self, in_memory_db):
        """Test handling large decimal monetary values"""
        now = datetime.now()
        large_value = Decimal("999999999.99")
        contract = Contract(
            contract_id=ContractId(uuid4()),
            title="High Value Contract",
            description="Contract with large monetary value",
            client=ContractParty("client-001", "Big Client", "client@example.com"),
            vendor=ContractParty("vendor-001", "Vendor", "vendor@example.com"),
            value=Money(large_value, "JPY"),
            validity_period=DateRange(now, now + timedelta(days=365)),
            payment_terms=PaymentTerms.NET_60,
            status=ContractStatus.ACTIVE,
            terms=[],
            created_at=now,
            updated_at=now
        )
        
        in_memory_db.save(contract)
        retrieved = in_memory_db.find_by_id(contract.contract_id)
        
        assert retrieved is not None
        assert retrieved.value.amount == large_value