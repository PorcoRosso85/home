-- Purpose: Propagate changes from parent contract to all child contracts
-- Description: When a parent contract is updated, this query finds all
--              descendant contracts and applies inherited changes
-- Parameters:
--   $parent_contract_id: STRING - ID of the parent contract that changed
--   $inheritable_fields: MAP - Fields that should be propagated to children
-- Returns:
--   child_id: STRING - ID of the child contract
--   depth: INT64 - Depth in the hierarchy
--   inherited_terms: STRING - JSON of inherited terms
--   update_status: STRING - Result of the update operation

-- Find all descendants in the contract hierarchy
MATCH path = (parent:Contract {id: $parent_contract_id})-[:ParentContract*]->(child:Contract)
WHERE child.status IN ['active', 'draft']
WITH parent, child, length(path) as depth, 
     relationships(path) as parent_rels
-- Extract inheritance rules from relationships
WITH parent, child, depth,
     [r IN parent_rels | r.inheritance_type] as inheritance_types,
     [r IN parent_rels | r.inherited_terms] as inherited_terms_list
-- Apply inheritance based on rules
WITH parent, child, depth,
     CASE 
       WHEN 'full' IN inheritance_types THEN $inheritable_fields
       WHEN 'partial' IN inheritance_types THEN 
         -- Merge only specific terms marked for inheritance
         {payment_terms: $inheritable_fields.payment_terms,
          value_currency: $inheritable_fields.value_currency}
       ELSE {}
     END as fields_to_inherit
-- Return update information
RETURN 
  child.id as child_id,
  depth,
  toString(fields_to_inherit) as inherited_terms,
  CASE 
    WHEN size(keys(fields_to_inherit)) > 0 THEN 'pending_update'
    ELSE 'no_inheritance'
  END as update_status
ORDER BY depth ASC