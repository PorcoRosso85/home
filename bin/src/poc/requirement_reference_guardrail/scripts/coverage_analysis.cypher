// Coverage Analysis Queries for Requirement Reference Guardrails
// This file contains Cypher queries to analyze the coverage of security standards

// Query 1: Count requirements by security category
MATCH (req:RequirementEntity)
WHERE req.security_category IS NOT NULL
RETURN req.security_category AS category, count(req) AS requirement_count
ORDER BY requirement_count DESC;

// Query 2: Find requirements without references
MATCH (req:RequirementEntity)
WHERE req.security_category IS NOT NULL
AND NOT EXISTS((req)-[:IMPLEMENTS]->(:ReferenceEntity))
RETURN req.id AS requirement_id, 
       req.description AS description,
       req.security_category AS category
ORDER BY req.security_category, req.id;

// Query 3: Reference usage statistics
MATCH (ref:ReferenceEntity)<-[:IMPLEMENTS]-(req:RequirementEntity)
RETURN ref.standard AS standard,
       ref.section AS section,
       count(req) AS usage_count
ORDER BY usage_count DESC, ref.standard, ref.section
LIMIT 20;

// Query 4: Coverage by ASVS section
MATCH (ref:ReferenceEntity)
WHERE ref.standard = 'ASVS'
OPTIONAL MATCH (ref)<-[:IMPLEMENTS]-(req:RequirementEntity)
WITH ref.section AS section, 
     ref.level AS level,
     count(req) AS implementation_count
RETURN section, level, implementation_count
ORDER BY section, level;

// Query 5: Requirements with multiple references (good practice)
MATCH (req:RequirementEntity)-[:IMPLEMENTS]->(ref:ReferenceEntity)
WITH req, count(ref) AS ref_count
WHERE ref_count > 1
MATCH (req)-[:IMPLEMENTS]->(ref:ReferenceEntity)
RETURN req.id AS requirement_id,
       req.description AS description,
       collect(ref.id) AS reference_ids,
       ref_count
ORDER BY ref_count DESC;

// Query 6: Exception requests analysis
MATCH (exc:ExceptionRequest)<-[:HAS_EXCEPTION]-(req:RequirementEntity)
RETURN exc.status AS exception_status,
       count(exc) AS count,
       collect(DISTINCT req.security_category) AS categories
ORDER BY count DESC;

// Query 7: Gap analysis - Missing ASVS coverage
WITH ['V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'V7', 'V8', 'V9', 'V10', 'V11', 'V12', 'V13', 'V14'] AS all_sections
UNWIND all_sections AS section
OPTIONAL MATCH (ref:ReferenceEntity)<-[:IMPLEMENTS]-(req:RequirementEntity)
WHERE ref.standard = 'ASVS' AND ref.section = section
WITH section, count(req) AS coverage_count
RETURN section AS asvs_section,
       coverage_count,
       CASE 
         WHEN coverage_count = 0 THEN 'No Coverage'
         WHEN coverage_count < 5 THEN 'Low Coverage'
         WHEN coverage_count < 20 THEN 'Medium Coverage'
         ELSE 'High Coverage'
       END AS coverage_level
ORDER BY section;

// Query 8: Security category to reference pattern compliance
MATCH (req:RequirementEntity)-[:IMPLEMENTS]->(ref:ReferenceEntity)
WHERE req.security_category IS NOT NULL
WITH req.security_category AS category,
     CASE 
       WHEN ref.id STARTS WITH 'ASVS-V2' THEN 'ASVS-V2'
       WHEN ref.id STARTS WITH 'ASVS-V3' THEN 'ASVS-V3'
       WHEN ref.id STARTS WITH 'ASVS-V4' THEN 'ASVS-V4'
       WHEN ref.id STARTS WITH 'ASVS-V5' THEN 'ASVS-V5'
       WHEN ref.id STARTS WITH 'ASVS-V6' THEN 'ASVS-V6'
       WHEN ref.id STARTS WITH 'NIST-' THEN substring(ref.id, 0, 7)
       ELSE 'Other'
     END AS reference_pattern
RETURN category, reference_pattern, count(*) AS count
ORDER BY category, reference_pattern;

// Query 9: Orphaned references (not used by any requirement)
MATCH (ref:ReferenceEntity)
WHERE NOT EXISTS((ref)<-[:IMPLEMENTS]-(:RequirementEntity))
RETURN ref.id AS reference_id,
       ref.standard AS standard,
       ref.section AS section,
       ref.title AS title
ORDER BY ref.standard, ref.section
LIMIT 50;

// Query 10: Overall guardrail effectiveness
MATCH (req:RequirementEntity)
WITH count(req) AS total_requirements
MATCH (req:RequirementEntity)
WHERE req.security_category IS NOT NULL
WITH total_requirements, count(req) AS security_requirements
MATCH (req:RequirementEntity)-[:IMPLEMENTS]->(:ReferenceEntity)
WHERE req.security_category IS NOT NULL
WITH total_requirements, security_requirements, count(DISTINCT req) AS compliant_requirements
MATCH (exc:ExceptionRequest)<-[:HAS_EXCEPTION]-(req:RequirementEntity)
WITH total_requirements, security_requirements, compliant_requirements, count(DISTINCT req) AS exception_requirements
RETURN total_requirements,
       security_requirements,
       compliant_requirements,
       exception_requirements,
       round(100.0 * security_requirements / total_requirements, 2) AS security_percentage,
       round(100.0 * compliant_requirements / security_requirements, 2) AS compliance_percentage,
       round(100.0 * exception_requirements / security_requirements, 2) AS exception_percentage;