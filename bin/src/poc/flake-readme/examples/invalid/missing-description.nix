# Invalid example: missing description
{
  goal = [ "demonstrate missing description error" ];
  nonGoal = [ "being a valid readme.nix" ];
  meta = {
    example = "invalid";
  };
  output = {
    packages = [ "invalid-example" ];
  };
}