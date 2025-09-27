# Test file for value constraints

let constraints = import "constraints.ncl" in

{
  # Test 1: Valid data should pass
  test_valid_data = {
    test_name = "Valid data test",
    expected = "success",
    result = constraints.validate_producer_with_constraints constraints.valid_data,
  },
  
  # Test 2: Show negative processed will produce blame function (contract broken)
  test_negative_processed = {
    test_name = "Negative processed test",
    expected = "contract_broken", 
    # This evaluation will show blame function for processed field
    result = constraints.validate_producer_with_constraints constraints.invalid_negative_processed,
  },
    
  # Test 3: Show negative failed will produce blame function (contract broken)
  test_negative_failed = {
    test_name = "Negative failed test",
    expected = "contract_broken",
    # This evaluation will show blame function for failed field
    result = constraints.validate_producer_with_constraints constraints.invalid_negative_failed,
  },
    
  # Test 4: Show empty output will produce blame function (contract broken)
  test_empty_output = {
    test_name = "Empty output test", 
    expected = "contract_broken",
    # This evaluation will show blame function for output field
    result = constraints.validate_producer_with_constraints constraints.invalid_empty_output,
  },
}