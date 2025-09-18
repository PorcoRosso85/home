{
  description = "Complex flake with multiple dependencies";

  inputs = {
    # Direct dependencies
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    
    # Local dependency
    local-flake.url = "path:./local-flake";
    
    # Git dependency
    my-repo.url = "git+ssh://git@github.com/user/repo";
    
    # Follows example
    utils-follow.follows = "nixpkgs/flake-utils";
    
    # Complex follows
    nested-follow.follows = "local-flake/nixpkgs";
  };

  outputs = { self, nixpkgs, flake-utils, local-flake, my-repo, ... }:
    {
      # outputs implementation
    };
}