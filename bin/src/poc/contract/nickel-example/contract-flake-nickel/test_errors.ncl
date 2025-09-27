# Error Case Testing for Enhanced Diagnostics
# Tests various error scenarios to verify clear error messages

let diagnostics = import "error_diagnostics.ncl" in
{
  # Test 1: Valid data (should pass)
  test_valid_data = 
    diagnostics.valid_producer_data & diagnostics.ProducerContractWithDiagnostics,

  # Test 2: Negative processed value
  test_negative_processed = 
    diagnostics.invalid_data_examples.negative_processed & diagnostics.ProducerContractWithDiagnostics,

  # Test 3: Negative failed value  
  test_negative_failed =
    diagnostics.invalid_data_examples.negative_failed & diagnostics.ProducerContractWithDiagnostics,

  # Test 4: Empty output array
  test_empty_output =
    diagnostics.invalid_data_examples.empty_output & diagnostics.ProducerContractWithDiagnostics,

  # Test 5: Wrong type for processed field
  test_type_mismatch =
    diagnostics.invalid_data_examples.wrong_type_processed & diagnostics.ProducerContractWithDiagnostics,

  # Test 6: Missing required field
  test_missing_field = 
    diagnostics.invalid_data_examples.missing_field & diagnostics.ProducerContractWithDiagnostics,

  # Test 7: Enhanced validation function tests
  enhanced_validation_tests = {
    # Valid case
    valid = diagnostics.validate_with_diagnostics diagnostics.valid_producer_data,
    
    # Error cases - these will trigger detailed error messages
    negative_processed_error = diagnostics.validate_with_diagnostics diagnostics.invalid_data_examples.negative_processed,
    negative_failed_error = diagnostics.validate_with_diagnostics diagnostics.invalid_data_examples.negative_failed,
    empty_output_error = diagnostics.validate_with_diagnostics diagnostics.invalid_data_examples.empty_output,
    type_mismatch_error = diagnostics.validate_with_diagnostics diagnostics.invalid_data_examples.wrong_type_processed,
  },

  # Test 8: Command contract error testing
  command_error_tests = {
    # Valid command
    valid_command = {
      command = "build",
      version = "1.0.0", 
      capabilities = ["compile", "test"],
    } & diagnostics.CommandContractWithDiagnostics,
    
    # Invalid version format
    invalid_version = {
      command = "build",
      version = "1.0",  # Wrong format - should trigger INVALID_FORMAT error
      capabilities = ["compile"],
    } & diagnostics.CommandContractWithDiagnostics,
    
    # Empty command
    empty_command = {
      command = "",  # Should trigger EMPTY_ARRAY error
      version = "1.0.0",
      capabilities = ["compile"],  
    } & diagnostics.CommandContractWithDiagnostics,
    
    # Empty capabilities
    empty_capabilities = {
      command = "build",
      version = "1.0.0",
      capabilities = [],  # Should trigger EMPTY_ARRAY error
    } & diagnostics.CommandContractWithDiagnostics,
  },

  # Summary of error types being tested
  error_test_summary = {
    total_error_types = 5,
    error_types = [
      diagnostics.ErrorLabels.NEGATIVE_VALUE,
      diagnostics.ErrorLabels.TYPE_MISMATCH,
      diagnostics.ErrorLabels.MISSING_FIELD, 
      diagnostics.ErrorLabels.EMPTY_ARRAY,
      diagnostics.ErrorLabels.INVALID_FORMAT,
    ],
    description = "Tests cover negative values, type mismatches, missing fields, empty arrays, and invalid format violations",
  },
}