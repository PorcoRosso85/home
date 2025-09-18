# Producer Output Example
# Demonstrates output format that must comply with ProducerOutputContract

let chain = import "../../chain.ncl" in

{
  # Valid producer output example
  valid_producer_output = {
    data = [
      { id = "batch-001", value = 150, status = "processed" },
      { id = "batch-002", value = 200, status = "processed" },
      { id = "batch-003", value = 75, status = "processed" },
      { id = "batch-004", value = 0, status = "error" },
    ],
    metadata = {
      timestamp = "2024-01-15T14:45:30Z",
      version = "2.1.0",
      source = "batch-processor-service",
    },
    summary = {
      total_count = 4,
      success_count = 3,
      error_count = 1,
    },
  },

  # Invalid producer output example (missing required fields)
  invalid_producer_output = {
    data = [
      { id = "item-001", value = 42 }, # missing status field
    ],
    metadata = {
      timestamp = "2024-01-15T14:45:30Z",
      # missing version and source
    },
    # missing summary completely
  },

  # Validate the producer output
  validation_result = chain.validate_chain valid_producer_output chain.example_consumer_input,
  
  # Check if output can be consumed
  can_be_consumed = chain.can_consume valid_producer_output,
  invalid_can_be_consumed = chain.can_consume invalid_producer_output,

  # Test producer output against contract
  test_valid = valid_producer_output & chain.ProducerOutputContract,
}