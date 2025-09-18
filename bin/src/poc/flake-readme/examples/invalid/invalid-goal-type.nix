# Invalid Goal Type - Schema Type Error  
#
# LEARNING OBJECTIVE:
# Understand that `goal` and `nonGoal` must be arrays of strings, not single strings
#
# WHAT THIS TEACHES:
# - Field type validation is strict in the v1 schema
# - `goal` and `nonGoal` expect arrays even for single values
# - Type errors are distinct from empty field errors
# - The schema enforces consistency for automated processing
#
# EXPECTED BEHAVIOR:  
# - ❌ Validation fails with type error about goal field
# - 📋 Error message indicates expected array but received string
# - 🚫 Hard error that prevents processing (unlike warnings)

{
  description = "Example with invalid goal type - demonstrates type validation";
  
  # ❌ TYPE ERROR: goal must be an array, not a string
  # Even single goals must be wrapped in arrays for consistency
  # This enables uniform processing of documentation across projects
  goal = "should be an array but is a string";  # Wrong type - validation will fail
  
  nonGoal = [ 
    "having inconsistent data types"
    "making automated processing difficult" 
  ];
  
  meta = {
    example = "type-error";
    errorType = "wrong-field-type";
  };
  
  output = {
    packages = [ "invalid-example" ];
  };
  
  # ============================================================================
  # HOW TO FIX THIS ERROR
  # ============================================================================
  # Wrap the string value in an array:
  #
  # goal = [ "should be an array but is a string" ];
  #
  # For multiple goals:
  # goal = [
  #   "first goal statement"
  #   "second goal statement" 
  #   "third goal statement"
  # ];
  #
  # The same rule applies to nonGoal - always use arrays of strings
}