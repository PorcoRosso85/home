# Producer implementation
let contracts = import "contracts.ncl" in
{
  processed = 3,
  failed = 0,
  output = ["item1", "item2", "item3"],
} & contracts.ProducerContract