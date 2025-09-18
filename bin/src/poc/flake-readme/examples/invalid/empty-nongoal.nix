# Invalid example: empty nonGoal array
{
  description = "Example with empty nonGoal array";
  goal = [ "demonstrate empty nonGoal error" ];
  nonGoal = [ ];  # Empty - should cause validation error
  meta = {
    example = "invalid";
  };
  output = {
    packages = [ "invalid-example" ];
  };
}