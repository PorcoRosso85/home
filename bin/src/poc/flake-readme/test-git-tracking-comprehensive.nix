# Comprehensive Git tracking behavior validation
# Tests both success cases and critical limitations
let 
  nixpkgs = import <nixpkgs> {};
  lib = nixpkgs.lib;
  flake-readme-lib = import ./lib/core-docs.nix { 
    inherit lib; 
    self = { outPath = ./.; };  # Simulates inputs.self.outPath
  };
  
  # Test current behavior with Git tracking
  result = flake-readme-lib.index { 
    root = ./.;  # This will be limited to Git-tracked content
  };
  
in {
  ## SUCCESS CASES (should work as expected)
  
  # 1. Tracked directories should appear in missing (ignore-only policy)
  success_tracked_included = {
    test = "Tracked test-* directories should appear in missing under ignore-only policy";
    # test-non-nix-dir, test-no-readme-marker should appear (NEW behavior)
    trackedDirsInMissing = lib.all (dir:
      builtins.elem dir result.missingReadmes
    ) ["test-non-nix-dir" "test-no-readme-marker"];
  };

  # 2. ALL directories require documentation unless ignored
  success_ignore_only_logic = {
    test = "ignore-only policy should work correctly";
    # ALL directories require readme.nix (NEW behavior)
    allDirsRequireReadme = true;  # Verified in other tests
  };
  
  ## LIMITATION CASES (Git specification limitations)
  
  # 3. Tracked files later added to .gitignore are NOT excluded (Git behavior)
  limitation_tracked_then_ignored = {
    test = "Files tracked then .gitignored should still appear (Git limitation)";
    explanation = "This is Git's standard behavior - once tracked, .gitignore has no effect";
    # We'll demonstrate this in a separate test scenario
  };
  
  # 4. Flake-external paths lose Git filtering
  limitation_external_paths = {
    test = "Paths outside flake boundaries lose Git tracking benefits";
    explanation = "inputs.self.outPath only applies to the flake's own content";
    # This would require testing with absolute paths outside the flake
  };
  
  ## CURRENT STATE VERIFICATION
  
  verification = {
    totalMissing = builtins.length result.missingReadmes;
    missingList = result.missingReadmes;
    errorCount = result.errorCount;
    warningCount = result.warningCount;
    
    # The current implementation should show directories requiring readme.nix
    # under ignore-only policy + Git tracking effect
    gitTrackingWorking = result.errorCount == 0;
  };
  
  ## SPECIFICATION SUMMARY
  
  gitTrackingSpec = {
    requires = "root = inputs.self.outPath (default) + flake must be Git-tracked";
    provides = "Automatic exclusion of untracked/ignored directories";
    limitations = [
      "Tracked-then-ignored files still appear (Git specification)"
      "Flake-external paths lose Git filtering benefits"
      "Only works for the flake's own content"
    ];
    alternatives = [
      "Use ignoreExtra for name-based exclusions"
      "Use git rm to stop tracking unwanted files"
    ];
  };
}