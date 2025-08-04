{
  description = "Claude launcher";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }: {
    # Empty for now - using direct shell scripts instead
  };
}