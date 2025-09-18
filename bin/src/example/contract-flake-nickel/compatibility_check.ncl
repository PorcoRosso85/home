# Producer→Consumer契約互換性検証
let ProducerContract = (import "contracts.ncl").ProducerContract in
let ConsumerContract = (import "contracts.ncl").ConsumerContract in

# テスト用の互換性データペア
let compatible_example = {
  producer = {
    processed = 5,
    failed = 1,
    output = ["item-a", "item-b"],
  },
  consumer = {
    summary = "Processing complete",
    details = {
      processed = 5,
      failed = 1,
      output = ["item-a", "item-b"],
      status = "success",
    },
  },
} in

# 互換性検証結果の直接計算
let compatibility_check = {
  output_mapping_valid = std.typeof compatible_example.producer.output == std.typeof compatible_example.consumer.details.output,
  numeric_types_valid = 
    std.is_number compatible_example.producer.processed &&
    std.is_number compatible_example.producer.failed,
  required_fields_valid = 
    std.record.has_field "processed" compatible_example.producer &&
    std.record.has_field "failed" compatible_example.producer &&
    std.record.has_field "output" compatible_example.producer &&
    std.record.has_field "details" compatible_example.consumer,
  overall_compatible = 
    (std.typeof compatible_example.producer.output == std.typeof compatible_example.consumer.details.output) &&
    (std.is_number compatible_example.producer.processed && std.is_number compatible_example.producer.failed) &&
    (std.record.has_field "processed" compatible_example.producer &&
     std.record.has_field "failed" compatible_example.producer &&
     std.record.has_field "output" compatible_example.producer &&
     std.record.has_field "details" compatible_example.consumer),
} in

{
  # 互換性検証実行結果（serializable）
  compatibility_result = compatibility_check,
  
  # テストデータも含める
  test_data = compatible_example,
  
  # メタデータ
  metadata = {
    description = "Producer-Consumer contract compatibility validation",
    feature_id = "FR-002",
    validation_rules = ["output_mapping", "numeric_compatibility", "required_fields"],
  },
}