# Invalid example: unknown output keys
{
  description = "Example with unknown output keys";
  goal = [ "demonstrate unknown output keys warning" ];
  nonGoal = [ "following the standard output schema" ];
  meta = {
    example = "invalid";
  };
  output = {
    packages = [ "invalid-example" ];
    unknownKey = [ "not-allowed" ];  # Unknown key - should cause warning
    anotherUnknown = "also-invalid";
  };
}