# Value Constraints for Contract Validation

{
  # Producer data validation with value constraints
  validate_producer_with_constraints = fun data =>
    let validate_non_negative = fun field =>
      if field >= 0 then field 
      else std.contract.blame_with_message "Value must be non-negative" in
    let validate_non_empty_array = fun arr =>
      if std.array.length arr > 0 then arr
      else std.contract.blame_with_message "Array must not be empty" in
    {
      processed = validate_non_negative data.processed,
      failed = validate_non_negative data.failed, 
      output = validate_non_empty_array data.output,
    },
    
  # Valid test data
  valid_data = {
    processed = 10,
    failed = 2,
    output = ["item-1", "item-2", "item-3"],
  },
  
  # Invalid test data - negative values
  invalid_negative_processed = {
    processed = -5,  # Should trigger constraint error
    failed = 2,
    output = ["item-1"],
  },
  
  invalid_negative_failed = {
    processed = 10,
    failed = -1,  # Should trigger constraint error
    output = ["item-1"],
  },
  
  # Invalid test data - empty array
  invalid_empty_output = {
    processed = 10,
    failed = 2,
    output = [],  # Should trigger constraint error
  },
  
  # Test valid data
  test_valid = validate_producer_with_constraints valid_data,
}