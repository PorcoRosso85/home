# Consumer Input Example
# Demonstrates input format that must comply with ConsumerInputContract

let chain = import "../../chain.ncl" in

{
  # Valid consumer input example (matches producer output format)
  valid_consumer_input = {
    data = [
      { id = "batch-001", value = 150, status = "processed" },
      { id = "batch-002", value = 200, status = "processed" },
      { id = "batch-003", value = 75, status = "processed" },
    ],
    metadata = {
      timestamp = "2024-01-15T14:45:30Z",
      version = "2.1.0",
      source = "batch-processor-service",
    },
    summary = {
      total_count = 3,
      success_count = 3,
      error_count = 0,
    },
  },

  # Invalid consumer input example (type mismatch)
  invalid_consumer_input = {
    data = [
      { id = 123, value = "not-a-number", status = true }, # wrong types
    ],
    metadata = {
      timestamp = 12345, # should be string
      version = 2.1, # should be string
      source = [], # should be string
    },
    summary = {
      total_count = "three", # should be number
      success_count = [], # should be number
      error_count = {}, # should be number
    },
  },

  # Test chain validation with different scenarios
  test_valid_chain = chain.validate_chain chain.example_producer_output valid_consumer_input,
  test_invalid_chain = chain.validate_chain chain.example_producer_output invalid_consumer_input,

  # Test consumer input against contract
  test_valid_input = valid_consumer_input & chain.ConsumerInputContract,
  
  # This will fail type checking:
  # test_invalid_input = invalid_consumer_input & chain.ConsumerInputContract,

  # Demonstrate that producer output can be directly used as consumer input
  producer_as_consumer_input = chain.example_producer_output & chain.ConsumerInputContract,
}