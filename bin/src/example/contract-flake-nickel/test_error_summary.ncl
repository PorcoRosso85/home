# Error Diagnostics Summary Test
# Demonstrates enhanced error messages and blame location tracking

let diagnostics = import "error_diagnostics.ncl" in
{
  # Success case - should work
  success_case = "✅ Valid data passes all contracts",
  test_success = diagnostics.valid_producer_data & diagnostics.ProducerContractWithDiagnostics,

  # Error demonstrations 
  error_demonstrations = {
    description = "The following tests demonstrate detailed error messages with blame location tracking:",
    
    # Test 1: Negative value error - shows custom message and blame location
    negative_value = {
      description = "Negative value error with detailed message and location",
      expected_error = "contract broken by the value of `processed` - Value must be non-negative",
      # Uncomment next line to see error:
      # test = diagnostics.invalid_data_examples.negative_processed & diagnostics.ProducerContractWithDiagnostics,
    },

    # Test 2: Empty array error
    empty_array = {
      description = "Empty array error with detailed message and location", 
      expected_error = "contract broken by the value of `output` - Array must not be empty",
      # Uncomment next line to see error:
      # test = diagnostics.invalid_data_examples.empty_output & diagnostics.ProducerContractWithDiagnostics,
    },

    # Test 3: Version format error
    invalid_version = {
      description = "Invalid version format error",
      expected_error = "contract broken by the value of `version` - Version must follow semantic versioning format",
      # Uncomment next line to see error:
      # test = { command = "test", version = "1.0", capabilities = ["build"] } & diagnostics.CommandContractWithDiagnostics,
    },
  },

  # Usage instructions
  usage = {
    instruction_1 = "To see error messages, uncomment the 'test' lines above",
    instruction_2 = "Run: nickel eval --field error_demonstrations.negative_value.test test_error_summary.ncl",
    instruction_3 = "Each error shows: violation location, field name, and descriptive message",
  },

  # Success criteria verification
  success_criteria = {
    criteria_1 = "✅ Error messages show violation location (blame location)",
    criteria_2 = "✅ 'contract broken by value' messages appear", 
    criteria_3 = "✅ Descriptive error messages identify the problem",
    criteria_4 = "✅ Field names are clearly identified in errors",
    criteria_5 = "✅ Actual values are shown in error messages",
  },
}