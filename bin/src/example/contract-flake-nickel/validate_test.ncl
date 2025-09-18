# Validate test data against contract
let contracts = import "contracts.ncl" in
let test_data = import "test_producer.ncl" in
contracts.validate_producer test_data