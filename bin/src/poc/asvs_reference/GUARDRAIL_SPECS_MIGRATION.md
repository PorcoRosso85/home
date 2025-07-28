# ASVS Reference Guardrail Specifications - Migration Guide

This document preserves the specifications from the removed guardrail functionality in the ASVS Reference POC. These specifications can be implemented in other POCs that require compliance enforcement.

## Overview

The ASVS Reference POC was refactored from an active guardrail system to a passive data provider. This document captures all removed specifications for potential implementation elsewhere.

## 1. Mandatory Reference Requirements

### Core Specifications

#### Category-Based Rules
```yaml
authentication:
  mandatory_standards: [ASVS, NIST]
  minimum_references: 2
  specific_sections:
    ASVS: ["V2", "V3"]
    NIST: ["800-63B"]

cryptography:
  mandatory_standards: [ASVS, NIST, FIPS]
  minimum_references: 3
  specific_sections:
    ASVS: ["V6"]
    NIST: ["800-57", "800-131A"]
    FIPS: ["140-2", "140-3"]

data_protection:
  mandatory_standards: [ASVS, GDPR]
  minimum_references: 2
  specific_sections:
    ASVS: ["V8", "V9"]
```

#### Override Patterns
- POC projects: `REQ-POC-*` - No reference requirements
- Legacy systems: `REQ-LEGACY-*` - Reduced requirements
- Critical infrastructure: `REQ-CRITICAL-*` - Enhanced requirements

#### Validation Rules
```python
def validate_references(requirement):
    category = requirement.get('category')
    references = requirement.get('references', [])
    
    if matches_override_pattern(requirement['id']):
        return apply_override_rules(requirement)
    
    config = get_mandatory_rules(category)
    if len(references) < config['minimum_references']:
        raise ValidationError(f"Requires {config['minimum_references']} references")
    
    for standard in config['mandatory_standards']:
        if not has_reference_from_standard(references, standard):
            raise ValidationError(f"Missing required {standard} reference")
```

### Test Cases to Preserve

1. **test_mandatory_standards_required**
   - Verify authentication requirements must have ASVS and NIST references
   - Verify cryptography requirements must have ASVS, NIST, and FIPS references

2. **test_minimum_reference_count**
   - Verify minimum 2 references for authentication
   - Verify minimum 3 references for cryptography

3. **test_override_patterns**
   - Verify POC requirements bypass reference checks
   - Verify legacy systems have reduced requirements

4. **test_coverage_reporting**
   - Calculate reference coverage percentage
   - Identify gaps in reference coverage

## 2. Enforced Workflow Specifications

### Core Business Rules

#### Requirement Creation
```python
def create_requirement(data):
    if not data.get('references') and not data.get('exception'):
        raise ValidationError("Requirement must have references or justified exception")
    
    if data.get('exception'):
        if len(data['exception']['justification']) < 50:
            raise ValidationError("Exception justification must be at least 50 characters")
    
    # Create audit trail
    audit_log.record({
        'action': 'create_requirement',
        'requirement_id': data['id'],
        'user': current_user,
        'timestamp': datetime.now(),
        'has_references': bool(data.get('references')),
        'has_exception': bool(data.get('exception'))
    })
```

#### State Transitions
```
draft → under_review → approved → implemented
         ↓               ↓
      rejected       deprecated
```

#### Workflow Rules
1. Cannot transition to approved with unresolved review comments
2. Deprecated references trigger migration notifications
3. Templates can predefine reference associations
4. Bulk operations maintain individual validation

### Test Cases to Preserve

1. **test_cannot_create_without_reference_or_exception**
   - Verify requirement creation fails without references or exception
   - Verify successful creation with valid references
   - Verify successful creation with justified exception

2. **test_state_transitions**
   - Verify valid state transitions
   - Verify invalid transitions are blocked
   - Verify transition audit logging

3. **test_gap_analysis**
   - Identify requirements without references
   - Calculate coverage statistics
   - Generate actionable recommendations

## 3. Exception Workflow Specifications

### Approval Hierarchy
```python
APPROVAL_LEVELS = {
    'not_applicable': ['team_lead'],
    'compensating_control': ['team_lead', 'security_architect'],
    'risk_accepted': ['security_architect', 'risk_management'],
    'temporary': ['team_lead', 'security_architect'],
    'custom_implementation': ['security_architect', 'technical_lead']
}
```

### Approval Workflow
```python
def submit_exception_for_approval(exception):
    exception['status'] = 'pending_approval'
    exception['required_approvals'] = APPROVAL_LEVELS[exception['type']]
    exception['current_approval_level'] = 0
    exception['approvals'] = []
    
    if exception['type'] == 'temporary':
        if not exception.get('expiration_date'):
            raise ValidationError("Temporary exceptions require expiration date")
    
    notify_next_approver(exception)
    return exception
```

### Audit Trail Requirements
```python
def record_approval_action(exception_id, action, approver, comments=None):
    audit_record = {
        'exception_id': exception_id,
        'action': action,  # approve, reject, conditional_approve
        'approver': approver,
        'timestamp': datetime.now(),
        'comments': comments,
        'hash': calculate_hash(previous_record)  # Blockchain-style
    }
    
    audit_log.append(audit_record)
    
    if action == 'approve':
        check_and_advance_workflow(exception_id)
```

### Test Cases to Preserve

1. **test_approval_hierarchy**
   - Verify correct approvers for each exception type
   - Verify sequential approval requirements
   - Verify approval delegation

2. **test_temporary_exceptions**
   - Verify expiration date requirement
   - Verify automatic expiration handling
   - Verify renewal process

3. **test_audit_immutability**
   - Verify audit records cannot be modified
   - Verify hash chain integrity
   - Verify audit export functionality

## 4. Implementation Examples

### For Requirement Management POC
```python
from asvs_api import create_asvs_provider

class RequirementWithGuardrails:
    def __init__(self):
        self.asvs_provider = create_asvs_provider()
        self.mandatory_rules = load_mandatory_rules()
    
    def create_requirement(self, data):
        # Apply mandatory reference validation
        self._validate_references(data)
        
        # Create requirement
        requirement = self._create_base_requirement(data)
        
        # Audit logging
        self._audit_log('create', requirement)
        
        return requirement
```

### For Compliance Dashboard POC
```python
class ComplianceAnalyzer:
    def analyze_reference_coverage(self, requirements):
        results = {
            'total': len(requirements),
            'with_references': 0,
            'with_exceptions': 0,
            'gaps': []
        }
        
        for req in requirements:
            if req.get('references'):
                results['with_references'] += 1
            elif req.get('exception'):
                results['with_exceptions'] += 1
            else:
                results['gaps'].append(req['id'])
        
        results['coverage_percentage'] = (
            results['with_references'] / results['total'] * 100
        )
        
        return results
```

## 5. Migration Checklist

When implementing these specifications in another POC:

- [ ] Review category-based mandatory rules
- [ ] Implement reference validation logic
- [ ] Set up exception workflow with approval levels
- [ ] Create audit trail mechanism
- [ ] Implement state machine for workflows
- [ ] Add coverage analysis capabilities
- [ ] Create notification system for approvals
- [ ] Set up periodic review reminders
- [ ] Implement template system for common patterns
- [ ] Add bulk operation support with validation

## 6. Data Structures to Preserve

### Mandatory Reference Configuration
```python
MandatoryReferenceRule = TypedDict('MandatoryReferenceRule', {
    'category': str,
    'mandatory_standards': List[str],
    'minimum_references': int,
    'specific_sections': Dict[str, List[str]],
    'coverage_threshold': float
})
```

### Exception Structure
```python
Exception = TypedDict('Exception', {
    'id': str,
    'requirement_id': str,
    'type': Literal['not_applicable', 'compensating_control', 'risk_accepted', 'temporary', 'custom_implementation'],
    'justification': str,
    'compensating_controls': Optional[List[str]],
    'expiration_date': Optional[datetime],
    'approvals': List[Approval],
    'status': Literal['draft', 'pending_approval', 'approved', 'rejected', 'expired']
})
```

### Workflow State
```python
WorkflowState = TypedDict('WorkflowState', {
    'requirement_id': str,
    'current_state': Literal['draft', 'under_review', 'approved', 'implemented', 'deprecated', 'rejected'],
    'previous_state': Optional[str],
    'transition_date': datetime,
    'transitioned_by': str,
    'comments': Optional[str]
})
```

## 7. Integration Points

These specifications can be integrated with:

1. **Requirement Graph POC** - For requirement-reference relationships
2. **Compliance Dashboard POC** - For visualization and reporting
3. **Audit Trail POC** - For immutable record keeping
4. **Notification POC** - For approval workflows
5. **Template Engine POC** - For predefined patterns

## Conclusion

This document preserves all guardrail specifications removed from the ASVS Reference POC. These can be selectively implemented in other POCs based on their specific compliance and workflow needs. The ASVS Reference POC remains available as a clean data provider for accessing ASVS security requirements.