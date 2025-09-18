# Enhanced Error Diagnostics for Contract Validation
# Provides detailed error messages and violation location tracking

{
  # Custom error labels for clear violation reporting
  ErrorLabels = {
    NEGATIVE_VALUE = "NEGATIVE_VALUE_ERROR",
    TYPE_MISMATCH = "TYPE_MISMATCH_ERROR", 
    MISSING_FIELD = "MISSING_FIELD_ERROR",
    EMPTY_ARRAY = "EMPTY_ARRAY_ERROR",
    INVALID_FORMAT = "INVALID_FORMAT_ERROR",
  },

  # Enhanced contracts using proper Nickel contract constructors
  NonNegativeNumber = std.contract.from_validator (fun x =>
    if x >= 0 then 'Ok
    else 'Error { message = "Value must be non-negative, got: %{std.serialize 'Json x}" }),

  NonEmptyArray = std.contract.from_validator (fun arr =>
    if std.array.length arr > 0 then 'Ok
    else 'Error { message = "Array must not be empty, got: %{std.serialize 'Json arr}" }),

  NonEmptyString = std.contract.from_validator (fun s =>
    if std.string.length s > 0 then 'Ok  
    else 'Error { message = "String must not be empty, got: %{std.serialize 'Json s}" }),

  # Enhanced contract with detailed error messages
  ProducerContractWithDiagnostics = {
    processed 
      | Number
      | NonNegativeNumber
      | doc "Number of items processed (must be >= 0)",
      
    failed
      | Number  
      | NonNegativeNumber
      | doc "Number of failed items (must be >= 0)",
      
    output
      | Array String
      | NonEmptyArray
      | doc "Array of processed item IDs (must not be empty)",
  },

  # Validation function with enhanced error reporting
  validate_with_diagnostics = fun data =>
    let check_non_negative = fun field_name value =>
      if value < 0 then
        std.contract.blame_with_message
          "%{ErrorLabels.NEGATIVE_VALUE}: Field '%{field_name}' must be non-negative. Got: %{std.serialize 'Json value}"
      else value in
    let check_non_empty_array = fun field_name arr =>
      if std.array.length arr == 0 then
        std.contract.blame_with_message
          "%{ErrorLabels.EMPTY_ARRAY}: Field '%{field_name}' must be a non-empty array. Got empty array"
      else arr in
    {
      processed = check_non_negative "processed" data.processed,
      failed = check_non_negative "failed" data.failed,
      output = check_non_empty_array "output" data.output,
    },

  # Version validation with detailed error messages  
  VersionContract = std.contract.from_validator (fun s => 
    if std.string.is_match "^[0-9]+\\.[0-9]+\\.[0-9]+$" s then 'Ok
    else 'Error { message = "Version must follow semantic versioning format (e.g., '1.0.0'), got: %{std.serialize 'Json s}" }),

  # Command contract with comprehensive diagnostics
  CommandContractWithDiagnostics = {
    command
      | String
      | NonEmptyString
      | doc "Command name to execute (must not be empty)",
      
    version
      | String
      | VersionContract
      | doc "Semantic version (e.g., '1.0.0')",
      
    capabilities
      | Array String
      | NonEmptyArray
      | doc "List of capabilities (must not be empty)",
  },

  # Test data examples
  valid_producer_data = {
    processed = 10,
    failed = 2,
    output = ["item-1", "item-2", "item-3"],
  },

  # Invalid data for error testing
  invalid_data_examples = {
    negative_processed = {
      processed = -5,  # Triggers NEGATIVE_VALUE error
      failed = 2,
      output = ["item-1"],
    },
    
    negative_failed = {
      processed = 10,
      failed = -1,  # Triggers NEGATIVE_VALUE error  
      output = ["item-1"],
    },
    
    empty_output = {
      processed = 10,
      failed = 2,
      output = [],  # Triggers EMPTY_ARRAY error
    },
    
    wrong_type_processed = {
      processed = "not a number",  # Triggers TYPE_MISMATCH error
      failed = 2,
      output = ["item-1"],
    },
    
    missing_field = {
      # processed field missing - Triggers MISSING_FIELD error
      failed = 2,
      output = ["item-1"],
    },
  },
}