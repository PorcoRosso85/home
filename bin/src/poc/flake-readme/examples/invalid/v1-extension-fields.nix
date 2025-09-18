# v1 Schema with Extension Fields - Educational Example
#
# This example demonstrates what happens when you add fields to a v1 schema document
# that are not part of the official v1 specification.
#
# LEARNING OBJECTIVE:
# Understand the v1 extension field warning system and how to handle unknown fields
#
# WHAT THIS EXAMPLE TEACHES:
# 1. v1 schema supports exactly: description, goal, nonGoal, meta, output, source
# 2. Additional fields generate warnings but don't cause validation failure
# 3. Extension fields are preserved for inspection (in 'extra' field)
# 4. This allows gradual migration and experimentation with future schema versions
#
# EXPECTED BEHAVIOR:
# - ✅ Document validates successfully (not an error)
# - ⚠️  Warnings generated for unknown fields: usage, features, techStack
# - 📋 Warning message: "Unknown keys found at .: [usage, features, techStack]"
# - 📊 warningCount > 0 in validation output
# - 💾 Extension fields stored in result.extra for inspection

{
  # ============================================================================
  # VALID v1 SCHEMA FIELDS
  # These are the official v1 schema fields that will validate without warnings
  # ============================================================================
  
  description = "Example v1 document with extension fields that should warn";
  
  goal = [ 
    "demonstrate v1 extension field warning behavior"
    "show how validation preserves unknown fields"
    "provide clear learning example for developers"
  ];
  
  nonGoal = [ 
    "being a valid v1 document without warnings"
    "replacing the official v1 schema specification"
  ];
  
  meta = {
    # Meta field allows arbitrary structured data
    example = "v1-with-extensions";
    purpose = "education";
    warningLevel = "expected";
  };
  
  output = {
    # Output field describes what this project produces
    packages = [ "test-package" ];
    # Note: you can add any keys here as this is a structured field
  };
  
  # ============================================================================
  # EXTENSION FIELDS - THESE TRIGGER WARNINGS IN v1 DOCUMENTS
  # The fields below are NOT part of the v1 schema specification
  # ============================================================================
  
  # ⚠️  EXTENSION FIELD: 'usage' is not in v1 schema
  # This field might be useful for documentation but triggers a warning
  usage = "This should trigger a warning - not part of v1 schema";
  
  # ⚠️  EXTENSION FIELD: 'features' is not in v1 schema  
  # Arrays are supported but the field name itself is unknown to v1
  features = [ 
    "warning-generation"
    "field-preservation" 
    "educational-example"
  ];
  
  # ⚠️  EXTENSION FIELD: 'techStack' is not in v1 schema
  # Structured data works but the top-level field name triggers warnings
  techStack = {
    language = "nix";
    framework = "flake-parts";
    purpose = "demonstration";
  };
  
  # ============================================================================
  # DEVELOPER GUIDANCE
  # ============================================================================
  
  # If you see warnings for these fields, you have several options:
  #
  # 1. IGNORE WARNINGS (if experimenting):
  #    - Warnings don't prevent validation success
  #    - Extension fields are preserved in output.extra
  #    - Good for testing future schema ideas
  #
  # 2. MOVE TO META FIELD (recommended):
  #    meta = {
  #      usage = "...";
  #      features = [ ... ];
  #      techStack = { ... };
  #    }
  #
  # 3. REMOVE UNKNOWN FIELDS (cleanest):
  #    - Keep only: description, goal, nonGoal, meta, output, source
  #    - Follow pure v1 schema specification
  #
  # 4. MIGRATE TO FUTURE SCHEMA (when available):
  #    - Future schemas may officially support these fields
  #    - Extension fields help inform schema evolution
}