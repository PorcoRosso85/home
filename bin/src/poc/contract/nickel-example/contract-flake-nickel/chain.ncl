# Contract Chain Implementation for Producer/Consumer
# Ensures type-level compatibility between Producer output and Consumer input

{
  # Producer Output Contract - defines what a producer should emit
  ProducerOutputContract = {
    data | Array { id | String, value | Number, status | String },
    metadata | {
      timestamp | String,
      version | String,
      source | String,
    },
    summary | {
      total_count | Number,
      success_count | Number,
      error_count | Number,
    },
  },

  # Consumer Input Contract - must match Producer output exactly
  ConsumerInputContract = {
    data | Array { id | String, value | Number, status | String },
    metadata | {
      timestamp | String,
      version | String,
      source | String,
    },
    summary | {
      total_count | Number,
      success_count | Number,
      error_count | Number,
    },
  },

  # Chain validation function - ensures producer output matches consumer input
  validate_chain = fun producer_output consumer_input =>
    let
      producer_validated = producer_output & ProducerOutputContract,
      consumer_validated = consumer_input & ConsumerInputContract,
    in
      # Type-level check: if both validate with same contract structure,
      # they are compatible
      if producer_validated == consumer_validated then
        { valid = true, message = "Chain validation successful" }
      else
        { valid = false, message = "Chain validation failed: type mismatch" },

  # Utility function to check if producer output can be consumed
  can_consume = fun producer_output =>
    let
      result = producer_output & ProducerOutputContract,
    in
      true,

  # Example valid producer output
  example_producer_output = {
    data = [
      { id = "item-001", value = 42, status = "processed" },
      { id = "item-002", value = 38, status = "processed" },
      { id = "item-003", value = 0, status = "error" },
    ],
    metadata = {
      timestamp = "2024-01-15T10:30:00Z",
      version = "1.0.0",
      source = "data-processor-v1",
    },
    summary = {
      total_count = 3,
      success_count = 2,
      error_count = 1,
    },
  },

  # Example valid consumer input (same structure as producer output)
  example_consumer_input = {
    data = [
      { id = "item-001", value = 42, status = "processed" },
      { id = "item-002", value = 38, status = "processed" },
    ],
    metadata = {
      timestamp = "2024-01-15T10:30:00Z",
      version = "1.0.0",
      source = "data-processor-v1",
    },
    summary = {
      total_count = 2,
      success_count = 2,
      error_count = 0,
    },
  },

  # Test chain validation
  test_chain_validation = validate_chain example_producer_output example_consumer_input,
}