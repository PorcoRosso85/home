# Nickel Contract Definitions for Flakes

{
  ProducerContract = {
    processed | Number
      | doc "Number of items processed",
    failed | Number
      | doc "Number of failed items",
    output | Array String
      | doc "Array of processed item IDs",
  },

  ConsumerContract = {
    summary | String
      | doc "Summary of processing results",
    details | { _ : _ }
      | doc "Detailed processing information",
  },

  CommandContract = {
    command | String
      | doc "Command name to execute",
    version | String
      | std.string.is_match "^[0-9]+\\.[0-9]+\\.[0-9]+$"
      | doc "Semantic version",
    capabilities | Array String
      | doc "List of capabilities",
  },
  
  # Example validation function
  validate_producer = fun data =>
    data & {
      processed | Number,
      failed | Number,
      output | Array String,
    },
    
  # Example data that conforms to contract
  example_producer = {
    processed = 10,
    failed = 2,
    output = ["item-1", "item-2", "item-3"],
  },
}