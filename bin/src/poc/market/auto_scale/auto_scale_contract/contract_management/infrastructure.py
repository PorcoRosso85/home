"""Contract Management Infrastructure Layer

This module contains concrete implementations of repositories,
external service integrations, and infrastructure concerns.
"""

import json
import sqlite3
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import UUID

import kuzu

from .domain import (
    Contract, ContractId, ContractParty, ContractStatus,
    ContractTerm, Money, DateRange, PaymentTerms,
    ContractRepository
)


class InMemoryContractRepository(ContractRepository):
    """In-memory implementation of contract repository for testing"""
    
    def __init__(self):
        self._contracts: Dict[str, Contract] = {}
    
    def save(self, contract: Contract) -> None:
        """Save a contract to memory"""
        key = str(contract.contract_id)
        self._contracts[key] = contract
    
    def find_by_id(self, contract_id: ContractId) -> Optional[Contract]:
        """Find a contract by ID"""
        key = str(contract_id)
        return self._contracts.get(key)
    
    def find_active_contracts(self) -> List[Contract]:
        """Find all active contracts"""
        return [c for c in self._contracts.values() 
                if c.status == ContractStatus.ACTIVE]
    
    def find_by_client(self, client_id: str) -> List[Contract]:
        """Find contracts by client"""
        return [c for c in self._contracts.values() 
                if c.client.party_id == client_id]


class KuzuGraphRepository(ContractRepository):
    """Kuzu GraphDB implementation of contract repository using in-memory database"""
    
    def __init__(self, db_path: str = ":memory:"):
        """Initialize KuzuDB with in-memory database by default"""
        self.db = kuzu.Database(db_path)
        self.conn = kuzu.Connection(self.db)
        self._init_schema()
    
    def _init_schema(self) -> None:
        """Initialize the graph database schema"""
        # Create node tables
        try:
            # Contract Node
            self.conn.execute("""
                CREATE NODE TABLE Contract(
                    id STRING PRIMARY KEY,
                    title STRING,
                    description STRING,
                    type STRING,
                    status STRING,
                    value_amount STRING,
                    value_currency STRING,
                    payment_terms STRING,
                    terms STRING,
                    created_at STRING,
                    expires_at STRING,
                    updated_at STRING
                )
            """)
        except Exception as e:
            # Table might already exist
            pass
        
        try:
            # Party Node
            self.conn.execute("""
                CREATE NODE TABLE Party(
                    id STRING PRIMARY KEY,
                    name STRING,
                    type STRING,
                    tax_id STRING,
                    created_at STRING
                )
            """)
        except Exception as e:
            # Table might already exist
            pass
        
        # Create relationship tables
        try:
            # ParentContract relationship
            self.conn.execute("""
                CREATE REL TABLE ParentContract(
                    FROM Contract TO Contract,
                    inheritance_type STRING,
                    inherited_terms STRING,
                    created_at STRING
                )
            """)
        except Exception as e:
            # Table might already exist
            pass
        
        try:
            # ContractParty relationship
            self.conn.execute("""
                CREATE REL TABLE ContractParty(
                    FROM Contract TO Party,
                    role STRING,
                    commission_rate DOUBLE,
                    special_terms STRING,
                    joined_at STRING
                )
            """)
        except Exception as e:
            # Table might already exist
            pass
        
        try:
            # ReferralChain relationship
            self.conn.execute("""
                CREATE REL TABLE ReferralChain(
                    FROM Party TO Party,
                    contract_id STRING,
                    referral_date STRING,
                    commission_rate DOUBLE
                )
            """)
        except Exception as e:
            # Table might already exist
            pass
    
    def save(self, contract: Contract) -> None:
        """Save a contract to the graph database"""
        # First, ensure parties exist
        self._ensure_party_exists(contract.client)
        self._ensure_party_exists(contract.vendor)
        
        # Prepare contract data
        contract_data = {
            'id': str(contract.contract_id),
            'title': contract.title,
            'description': contract.description or '',
            'type': self._determine_contract_type(contract),
            'status': contract.status.value,
            'value_amount': str(contract.value.amount),
            'value_currency': contract.value.currency,
            'payment_terms': contract.payment_terms.value,
            'terms': json.dumps([self._term_to_dict(t) for t in contract.terms]),
            'created_at': contract.created_at.isoformat(),
            'expires_at': contract.validity_period.end_date.isoformat(),
            'updated_at': contract.updated_at.isoformat()
        }
        
        # Create or update contract node
        # First check if contract exists
        result = self.conn.execute(
            "MATCH (c:Contract) WHERE c.id = $id RETURN c",
            {'id': str(contract.contract_id)}
        )
        
        if result.has_next():
            # Update existing contract
            self.conn.execute("""
                MATCH (c:Contract) WHERE c.id = $id
                SET c.title = $title,
                    c.description = $description,
                    c.type = $type,
                    c.status = $status,
                    c.value_amount = $value_amount,
                    c.value_currency = $value_currency,
                    c.payment_terms = $payment_terms,
                    c.terms = $terms,
                    c.created_at = $created_at,
                    c.expires_at = $expires_at,
                    c.updated_at = $updated_at
            """, contract_data)
        else:
            # Create new contract
            self.conn.execute("""
                CREATE (c:Contract {
                    id: $id,
                    title: $title,
                    description: $description,
                    type: $type,
                    status: $status,
                    value_amount: $value_amount,
                    value_currency: $value_currency,
                    payment_terms: $payment_terms,
                    terms: $terms,
                    created_at: $created_at,
                    expires_at: $expires_at,
                    updated_at: $updated_at
                })
            """, contract_data)
        
        # Create contract-party relationships
        self._create_contract_party_relationship(contract, contract.client, 'buyer')
        self._create_contract_party_relationship(contract, contract.vendor, 'seller')
    
    def find_by_id(self, contract_id: ContractId) -> Optional[Contract]:
        """Find a contract by ID"""
        result = self.conn.execute("""
            MATCH (c:Contract) WHERE c.id = $id
            OPTIONAL MATCH (c)-[cp:ContractParty]->(p:Party)
            RETURN c, collect({party: p, relationship: cp}) as parties
        """, {'id': str(contract_id)})
        
        row = result.get_next()
        if row:
            return self._row_to_contract(row)
        return None
    
    def find_active_contracts(self) -> List[Contract]:
        """Find all active contracts"""
        result = self.conn.execute("""
            MATCH (c:Contract) WHERE c.status = $status
            OPTIONAL MATCH (c)-[cp:ContractParty]->(p:Party)
            RETURN c, collect({party: p, relationship: cp}) as parties
        """, {'status': ContractStatus.ACTIVE.value})
        
        contracts = []
        while result.has_next():
            row = result.get_next()
            if contract := self._row_to_contract(row):
                contracts.append(contract)
        return contracts
    
    def find_by_client(self, client_id: str) -> List[Contract]:
        """Find contracts by client"""
        result = self.conn.execute("""
            MATCH (c:Contract)-[cp1:ContractParty]->(client:Party) 
            WHERE cp1.role = 'buyer' AND client.id = $client_id
            OPTIONAL MATCH (c)-[cp2:ContractParty]->(p:Party)
            RETURN c, collect({party: p, relationship: cp2}) as parties
        """, {'client_id': client_id})
        
        contracts = []
        while result.has_next():
            row = result.get_next()
            if contract := self._row_to_contract(row):
                contracts.append(contract)
        return contracts
    
    def _ensure_party_exists(self, party: ContractParty) -> None:
        """Ensure a party exists in the database"""
        # Check if party exists
        result = self.conn.execute(
            "MATCH (p:Party) WHERE p.id = $id RETURN p",
            {'id': party.party_id}
        )
        
        if result.has_next():
            # Update existing party
            self.conn.execute("""
                MATCH (p:Party) WHERE p.id = $id
                SET p.name = $name,
                    p.type = $type
            """, {
                'id': party.party_id,
                'name': party.name,
                'type': 'company'  # Default to company for now
            })
        else:
            # Create new party
            self.conn.execute("""
                CREATE (p:Party {
                    id: $id,
                    name: $name,
                    type: $type,
                    created_at: $created_at
                })
            """, {
                'id': party.party_id,
                'name': party.name,
                'type': 'company',  # Default to company for now
                'created_at': datetime.now().isoformat()
            })
    
    def _create_contract_party_relationship(self, contract: Contract, party: ContractParty, role: str) -> None:
        """Create relationship between contract and party"""
        # First check if relationship exists
        result = self.conn.execute("""
            MATCH (c:Contract)-[cp:ContractParty]->(p:Party)
            WHERE c.id = $contract_id AND p.id = $party_id AND cp.role = $role
            RETURN cp
        """, {
            'contract_id': str(contract.contract_id),
            'party_id': party.party_id,
            'role': role
        })
        
        if not result.has_next():
            # Create new relationship
            self.conn.execute("""
                MATCH (c:Contract) WHERE c.id = $contract_id
                MATCH (p:Party) WHERE p.id = $party_id
                CREATE (c)-[cp:ContractParty {
                    role: $role,
                    joined_at: $joined_at
                }]->(p)
            """, {
                'contract_id': str(contract.contract_id),
                'party_id': party.party_id,
                'role': role,
                'joined_at': datetime.now().isoformat()
            })
    
    def _determine_contract_type(self, contract: Contract) -> str:
        """Determine contract type based on contract details"""
        # Simple heuristic - could be enhanced based on actual business rules
        if hasattr(contract, 'contract_type'):
            return contract.contract_type
        return 'reseller'  # Default type
    
    def _term_to_dict(self, term: ContractTerm) -> Dict[str, Any]:
        """Convert term to dictionary"""
        return {
            'term_id': term.term_id,
            'title': term.title,
            'description': term.description,
            'is_mandatory': term.is_mandatory
        }
    
    def _row_to_contract(self, row: List[Any]) -> Optional[Contract]:
        """Convert database row to contract"""
        if not row or len(row) < 2:
            return None
        
        # Kuzu returns row as a list [contract_node, parties_collection]
        contract_node = row[0]
        parties_data = row[1]
        
        # Extract contract properties
        contract_id = contract_node['id']
        if not contract_id:
            return None
        
        # Find client and vendor from parties
        client = None
        vendor = None
        
        if parties_data and isinstance(parties_data, list):
            for party_info in parties_data:
                if party_info and isinstance(party_info, dict):
                    party_node = party_info.get('party')
                    relationship = party_info.get('relationship')
                    
                    if party_node and relationship:
                        role = relationship.get('role')
                        party = ContractParty(
                            party_id=party_node.get('id'),
                            name=party_node.get('name'),
                            contact_email=f"{party_node.get('id')}@example.com",  # Default email
                            contact_phone=None,
                            address=None
                        )
                        
                        if role == 'buyer':
                            client = party
                        elif role == 'seller':
                            vendor = party
        
        # If we don't have both client and vendor, return None
        if not client or not vendor:
            return None
        
        # Parse terms
        terms_json = contract_node.get('terms', '[]')
        if isinstance(terms_json, str):
            terms_data = json.loads(terms_json)
        else:
            terms_data = []
        
        terms = [
            ContractTerm(
                term_id=t['term_id'],
                title=t['title'],
                description=t['description'],
                is_mandatory=t.get('is_mandatory', True)
            )
            for t in terms_data
        ]
        
        # Parse dates
        created_at = datetime.fromisoformat(contract_node.get('created_at'))
        updated_at = datetime.fromisoformat(contract_node.get('updated_at', contract_node.get('created_at')))
        expires_at = datetime.fromisoformat(contract_node.get('expires_at'))
        
        # Create contract from stored data
        return Contract(
            contract_id=ContractId(UUID(contract_id)),
            title=contract_node.get('title', f"Contract {contract_id[:8]}"),
            description=contract_node.get('description', ''),
            client=client,
            vendor=vendor,
            value=Money(
                Decimal(contract_node.get('value_amount', '0')),
                contract_node.get('value_currency', 'USD')
            ),
            validity_period=DateRange(
                start_date=created_at,
                end_date=expires_at
            ),
            payment_terms=PaymentTerms(contract_node.get('payment_terms', PaymentTerms.NET_30.value)),
            status=ContractStatus(contract_node.get('status')),
            terms=terms,
            created_at=created_at,
            updated_at=updated_at
        )


class SQLiteContractRepository(ContractRepository):
    """SQLite implementation of contract repository"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_schema()
    
    def _init_schema(self) -> None:
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS contracts (
                    contract_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    client_data TEXT NOT NULL,
                    vendor_data TEXT NOT NULL,
                    value_amount TEXT NOT NULL,
                    value_currency TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    payment_terms TEXT NOT NULL,
                    status TEXT NOT NULL,
                    terms_data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_contracts_status 
                ON contracts(status)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_contracts_client 
                ON contracts(client_data)
            """)
    
    def save(self, contract: Contract) -> None:
        """Save a contract to SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO contracts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(contract.contract_id),
                contract.title,
                contract.description,
                json.dumps(self._party_to_dict(contract.client)),
                json.dumps(self._party_to_dict(contract.vendor)),
                str(contract.value.amount),
                contract.value.currency,
                contract.validity_period.start_date.isoformat(),
                contract.validity_period.end_date.isoformat(),
                contract.payment_terms.value,
                contract.status.value,
                json.dumps([self._term_to_dict(t) for t in contract.terms]),
                contract.created_at.isoformat(),
                contract.updated_at.isoformat()
            ))
    
    def find_by_id(self, contract_id: ContractId) -> Optional[Contract]:
        """Find a contract by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM contracts WHERE contract_id = ?",
                (str(contract_id),)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_contract(row)
            return None
    
    def find_active_contracts(self) -> List[Contract]:
        """Find all active contracts"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM contracts WHERE status = ?",
                (ContractStatus.ACTIVE.value,)
            )
            return [self._row_to_contract(row) for row in cursor.fetchall()]
    
    def find_by_client(self, client_id: str) -> List[Contract]:
        """Find contracts by client"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM contracts")
            contracts = []
            for row in cursor.fetchall():
                contract = self._row_to_contract(row)
                if contract.client.party_id == client_id:
                    contracts.append(contract)
            return contracts
    
    def _party_to_dict(self, party: ContractParty) -> Dict[str, Any]:
        """Convert party to dictionary"""
        return {
            'party_id': party.party_id,
            'name': party.name,
            'contact_email': party.contact_email,
            'contact_phone': party.contact_phone,
            'address': party.address
        }
    
    def _dict_to_party(self, data: Dict[str, Any]) -> ContractParty:
        """Convert dictionary to party"""
        return ContractParty(
            party_id=data['party_id'],
            name=data['name'],
            contact_email=data['contact_email'],
            contact_phone=data.get('contact_phone'),
            address=data.get('address')
        )
    
    def _term_to_dict(self, term: ContractTerm) -> Dict[str, Any]:
        """Convert term to dictionary"""
        return {
            'term_id': term.term_id,
            'title': term.title,
            'description': term.description,
            'is_mandatory': term.is_mandatory
        }
    
    def _dict_to_term(self, data: Dict[str, Any]) -> ContractTerm:
        """Convert dictionary to term"""
        return ContractTerm(
            term_id=data['term_id'],
            title=data['title'],
            description=data['description'],
            is_mandatory=data.get('is_mandatory', True)
        )
    
    def _row_to_contract(self, row: sqlite3.Row) -> Contract:
        """Convert database row to contract"""
        return Contract(
            contract_id=ContractId(UUID(row['contract_id'])),
            title=row['title'],
            description=row['description'],
            client=self._dict_to_party(json.loads(row['client_data'])),
            vendor=self._dict_to_party(json.loads(row['vendor_data'])),
            value=Money(Decimal(row['value_amount']), row['value_currency']),
            validity_period=DateRange(
                start_date=datetime.fromisoformat(row['start_date']),
                end_date=datetime.fromisoformat(row['end_date'])
            ),
            payment_terms=PaymentTerms(row['payment_terms']),
            status=ContractStatus(row['status']),
            terms=[self._dict_to_term(t) for t in json.loads(row['terms_data'])],
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )


class FileSystemContractRepository(ContractRepository):
    """File system based implementation of contract repository"""
    
    def __init__(self, storage_path: Path):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def save(self, contract: Contract) -> None:
        """Save a contract to file system"""
        file_path = self._get_file_path(contract.contract_id)
        contract_data = self._contract_to_dict(contract)
        
        with open(file_path, 'w') as f:
            json.dump(contract_data, f, indent=2, default=str)
    
    def find_by_id(self, contract_id: ContractId) -> Optional[Contract]:
        """Find a contract by ID"""
        file_path = self._get_file_path(contract_id)
        
        if not file_path.exists():
            return None
        
        with open(file_path, 'r') as f:
            data = json.load(f)
            return self._dict_to_contract(data)
    
    def find_active_contracts(self) -> List[Contract]:
        """Find all active contracts"""
        contracts = []
        for file_path in self.storage_path.glob("*.json"):
            with open(file_path, 'r') as f:
                data = json.load(f)
                if data['status'] == ContractStatus.ACTIVE.value:
                    contracts.append(self._dict_to_contract(data))
        return contracts
    
    def find_by_client(self, client_id: str) -> List[Contract]:
        """Find contracts by client"""
        contracts = []
        for file_path in self.storage_path.glob("*.json"):
            with open(file_path, 'r') as f:
                data = json.load(f)
                if data['client']['party_id'] == client_id:
                    contracts.append(self._dict_to_contract(data))
        return contracts
    
    def _get_file_path(self, contract_id: ContractId) -> Path:
        """Get file path for a contract"""
        return self.storage_path / f"{contract_id}.json"
    
    def _contract_to_dict(self, contract: Contract) -> Dict[str, Any]:
        """Convert contract to dictionary"""
        return {
            'contract_id': str(contract.contract_id),
            'title': contract.title,
            'description': contract.description,
            'client': self._party_to_dict(contract.client),
            'vendor': self._party_to_dict(contract.vendor),
            'value': {
                'amount': str(contract.value.amount),
                'currency': contract.value.currency
            },
            'validity_period': {
                'start_date': contract.validity_period.start_date.isoformat(),
                'end_date': contract.validity_period.end_date.isoformat()
            },
            'payment_terms': contract.payment_terms.value,
            'status': contract.status.value,
            'terms': [self._term_to_dict(t) for t in contract.terms],
            'created_at': contract.created_at.isoformat(),
            'updated_at': contract.updated_at.isoformat()
        }
    
    def _dict_to_contract(self, data: Dict[str, Any]) -> Contract:
        """Convert dictionary to contract"""
        return Contract(
            contract_id=ContractId(UUID(data['contract_id'])),
            title=data['title'],
            description=data['description'],
            client=self._dict_to_party(data['client']),
            vendor=self._dict_to_party(data['vendor']),
            value=Money(
                Decimal(data['value']['amount']),
                data['value']['currency']
            ),
            validity_period=DateRange(
                start_date=datetime.fromisoformat(data['validity_period']['start_date']),
                end_date=datetime.fromisoformat(data['validity_period']['end_date'])
            ),
            payment_terms=PaymentTerms(data['payment_terms']),
            status=ContractStatus(data['status']),
            terms=[self._dict_to_term(t) for t in data['terms']],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at'])
        )
    
    def _party_to_dict(self, party: ContractParty) -> Dict[str, Any]:
        """Convert party to dictionary"""
        return {
            'party_id': party.party_id,
            'name': party.name,
            'contact_email': party.contact_email,
            'contact_phone': party.contact_phone,
            'address': party.address
        }
    
    def _dict_to_party(self, data: Dict[str, Any]) -> ContractParty:
        """Convert dictionary to party"""
        return ContractParty(
            party_id=data['party_id'],
            name=data['name'],
            contact_email=data['contact_email'],
            contact_phone=data.get('contact_phone'),
            address=data.get('address')
        )
    
    def _term_to_dict(self, term: ContractTerm) -> Dict[str, Any]:
        """Convert term to dictionary"""
        return {
            'term_id': term.term_id,
            'title': term.title,
            'description': term.description,
            'is_mandatory': term.is_mandatory
        }
    
    def _dict_to_term(self, data: Dict[str, Any]) -> ContractTerm:
        """Convert dictionary to term"""
        return ContractTerm(
            term_id=data['term_id'],
            title=data['title'],
            description=data['description'],
            is_mandatory=data.get('is_mandatory', True)
        )


# External Service Integrations

class EmailNotificationService:
    """Service for sending email notifications"""
    
    def send_contract_created_notification(self, contract: Contract) -> None:
        """Send notification when contract is created"""
        # In a real implementation, this would integrate with an email service
        print(f"Email sent: Contract '{contract.title}' created")
    
    def send_contract_activated_notification(self, contract: Contract) -> None:
        """Send notification when contract is activated"""
        print(f"Email sent: Contract '{contract.title}' is now active")
    
    def send_contract_expiry_reminder(self, contract: Contract, days_until_expiry: int) -> None:
        """Send reminder about contract expiry"""
        print(f"Email sent: Contract '{contract.title}' expires in {days_until_expiry} days")


class ContractDocumentGenerator:
    """Service for generating contract documents"""
    
    def generate_pdf(self, contract: Contract) -> bytes:
        """Generate PDF document for contract"""
        # In a real implementation, this would use a PDF generation library
        # For now, return a placeholder
        pdf_content = f"Contract: {contract.title}\n"
        pdf_content += f"Client: {contract.client.name}\n"
        pdf_content += f"Vendor: {contract.vendor.name}\n"
        pdf_content += f"Value: {contract.value.amount} {contract.value.currency}\n"
        return pdf_content.encode('utf-8')
    
    def generate_docx(self, contract: Contract) -> bytes:
        """Generate DOCX document for contract"""
        # Placeholder implementation
        return self.generate_pdf(contract)


class ContractAuditLogger:
    """Service for audit logging of contract operations"""
    
    def __init__(self, log_file: Path):
        self.log_file = log_file
    
    def log_contract_created(self, contract: Contract, user_id: str) -> None:
        """Log contract creation"""
        self._write_log({
            'timestamp': datetime.now().isoformat(),
            'event': 'contract_created',
            'contract_id': str(contract.contract_id),
            'user_id': user_id,
            'details': {
                'title': contract.title,
                'client': contract.client.name,
                'vendor': contract.vendor.name,
                'value': f"{contract.value.amount} {contract.value.currency}"
            }
        })
    
    def log_contract_status_change(self, contract: Contract, old_status: ContractStatus, 
                                   new_status: ContractStatus, user_id: str) -> None:
        """Log contract status change"""
        self._write_log({
            'timestamp': datetime.now().isoformat(),
            'event': 'contract_status_changed',
            'contract_id': str(contract.contract_id),
            'user_id': user_id,
            'details': {
                'old_status': old_status.value,
                'new_status': new_status.value
            }
        })
    
    def _write_log(self, log_entry: Dict[str, Any]) -> None:
        """Write log entry to file"""
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')