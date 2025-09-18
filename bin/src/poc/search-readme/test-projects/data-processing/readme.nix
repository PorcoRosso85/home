{
  description = "Data processing utilities for ETL workflows";
  goal = [
    "Transform CSV files into structured data"
    "Validate data schemas during processing"
    "Handle large datasets efficiently"
  ];
  nonGoal = [
    "Real-time streaming processing"
    "Machine learning model training"
  ];
  meta = {
    owner = [ "@data-team" ];
    lifecycle = "stable";
  };
  output = {
    packages = [ "csv-transformer" "schema-validator" ];
    apps = [ "data-pipeline" ];
  };
}