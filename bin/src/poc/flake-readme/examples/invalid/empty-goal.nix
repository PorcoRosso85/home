# Empty Goal Array - Schema Validation Error
#
# LEARNING OBJECTIVE:
# Understand why the `goal` field must contain at least one meaningful entry
#
# WHAT THIS TEACHES:
# - The `goal` field is required and must be a non-empty array
# - Empty arrays fail validation because goals define project purpose
# - Each goal should be a concrete, actionable statement
#
# EXPECTED BEHAVIOR:
# - ❌ Validation fails with error about empty goal array
# - 📋 Error message indicates that goals are required for documentation
# - 🚫 This is a hard error, not a warning (unlike extension fields)

{
  description = "Example with empty goal array - demonstrates validation error";
  
  # ❌ VALIDATION ERROR: Empty goal array
  # The goal field must contain at least one meaningful entry
  # Goals define what the project aims to achieve
  goal = [ ];  # This empty array will cause validation to fail
  
  nonGoal = [ 
    "having unclear project purpose"
    "leaving developers guessing about intentions"
  ];
  
  meta = {
    example = "validation-error";
    errorType = "empty-required-field";
  };
  
  output = {
    packages = [ "invalid-example" ];
  };
  
  # ============================================================================
  # HOW TO FIX THIS ERROR
  # ============================================================================
  # Replace the empty array with concrete goals:
  #
  # goal = [
  #   "provide clear project documentation"
  #   "demonstrate schema validation requirements"
  #   "help developers understand the goal field purpose"
  # ];
  #
  # Each goal should answer "What does this project accomplish?"
}