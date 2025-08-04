#!/usr/bin/env nix-instantiate --eval
# Example showing how to use kuzu-migrate library in practice

let
  # Get the parent flake
  kuzu-migrate = builtins.getFlake (toString ../../..);
  
  # Mock pkgs for demonstration
  pkgs = {
    system = "x86_64-linux";
    writeShellScript = name: text: "/nix/store/mock-${name}";
  };
  
  # Use the library function with custom DDL path
  myMigrationApps = kuzu-migrate.lib.mkKuzuMigration {
    inherit pkgs;
    ddlPath = "./my-project/migrations";
  };
  
  # You can also create multiple sets for different databases
  mainDbApps = kuzu-migrate.lib.mkKuzuMigration {
    inherit pkgs;
    ddlPath = "./databases/main/ddl";
  };
  
  testDbApps = kuzu-migrate.lib.mkKuzuMigration {
    inherit pkgs;
    ddlPath = "./databases/test/ddl";
  };
in
{
  # Show what's available
  example1 = "Single database configuration:";
  myApps = builtins.attrNames myMigrationApps;
  
  example2 = "Multiple database configuration:";
  mainDb = builtins.attrNames mainDbApps;
  testDb = builtins.attrNames testDbApps;
  
  # Show the structure of an app
  appStructure = {
    type = myMigrationApps.init.type;
    hasProgram = myMigrationApps.init ? program;
  };
  
  # Demonstrate that ddlPath is properly passed
  paths = {
    myProject = builtins.match ".*--ddl (./my-project/migrations).*" (toString myMigrationApps.init.program) != null;
    mainDb = builtins.match ".*--ddl (./databases/main/ddl).*" (toString mainDbApps.init.program) != null;
    testDb = builtins.match ".*--ddl (./databases/test/ddl).*" (toString testDbApps.init.program) != null;
  };
}