# Final Implementation Plan: ignore-only Policy Transition

## ✅ Critical Implementation Details (Your Essential Refinements)

### 1. examples/ Default Ignore Consistency Fix
**Problem Identified:** Policy mismatch causes post-transition issues
```nix
# lib/core-docs.nix:63-66 (HAS examples ignore)
defaultIgnore = name: type: builtins.elem name [
  ".git" ".direnv" "node_modules" "result" "dist" "target" ".cache"
] || (name == "examples" && type == "directory");

# lib/flake-module.nix:54-57 (MISSING examples ignore)
defaultIgnore = name: type: builtins.elem name ([
  ".git" ".direnv" "node_modules" "result" "dist" "target" ".cache"
] ++ cfg.ignoreExtra);  # ← NO examples!
```

**Required Fix:** Add "examples" to lib/flake-module.nix defaultIgnore list
**Impact:** Prevents examples/ missing readme.nix explosion after ignore-only transition

### 2. Comprehensive Replacement Target List
**ALL files requiring .nix-only → ignore-only updates:**

**Documentation Files:**
- README.md
- docs/integration.md
- MIGRATION_GUIDE.md
- IMPLEMENTATION_SUMMARY.md
- GIT_TRACKING_SPECIFICATION.md
- FACT_POLICY_SEPARATION_SPEC.md
- readme.nix (description field)

**Test Files (.nix-only in names/expectations):**
- test-documentable-nix-only.nix
- test-nix-only-validation.nix
- test-nix-only-comprehensive.nix
- test-nix-only-RED.nix
- test-integration-comprehensive.nix
- test-git-tracking-comprehensive.nix
- test-git-boundary-constraints.nix
- test-simplified-final.nix
- test-simplified-version.nix

**Code Comments:**
- flake.nix ("only for documentable dirs" comment)

### 3. Enhanced Definition of Done (DoD)

**Core Behavior Verification:**
- ✅ Root "." included in missing detection when no readme.nix present
- ✅ module-side ignoreExtra properly extends ignore-only behavior
- ✅ examples/ consistent ignore between core-docs and flake-module
- ✅ v.isDocumentable removed from missing detection (lib/core-docs.nix:160)
- ✅ isDocumentable preserved as "fact only" with clarifying comment

**Representative Test Cases (5 scenarios):**
1. **non-.nix directory** → now appears in missing (new behavior)
2. **has-.nix directory** → appears in missing (unchanged behavior)
3. **ignored directory** → excluded from missing (unchanged behavior)
4. **root "." directory** → appears in missing if no readme.nix (explicit verification)
5. **examples/ directory** → excluded from missing (consistent across modules)

---

## 🎯 4-Step Implementation (50 minutes total)

### Step 1: Repository-Wide Reference Updates (15 min)
**Scope:** ALL .nix-only references across 15+ files
**Method:** Keyword-based search and replace (stable, not line-dependent)
**Critical Fix:** Add "examples" to lib/flake-module.nix defaultIgnore

### Step 2: Core Logic Simplification (10 min)
**Change:** Single line modification
```nix
# Before
if v.isDocumentable && (!v.hasReadme) && (!shouldIgnore) then p else null

# After
if (!v.hasReadme) && (!shouldIgnore) then p else null
```
**Comment Addition:** Mark isDocumentable role as "fact collection only"

### Step 3: Integration Guide Enhancement (10 min)
**Add:** examples/ policy documentation
**Add:** Root "." requirement explicit coverage
**Ensure:** DRY principle compliance guidance

### Step 4: Test Infrastructure Complete Update (15 min)
**Update:** 10+ test files with ignore-only expectations
**Verify:** All 5 representative cases pass

---

## 🏗️ Architecture Achievement

### SRP Separation Success:
```nix
# FACT COLLECTION (preserved for future extensibility)
isDocumentable = lib.any (n: lib.hasSuffix ".nix" n) names;

# POLICY APPLICATION (simplified to ignore-only)
if (!v.hasReadme) && (!shouldIgnore) then p else null
```

### Future Roadmap Notes:
- **DRY Enhancement:** Unify core-docs and flake-module ignore sources (post-KISS phase)
- **API Stability:** isDocumentable meaning preserved for external dependencies
- **Extension Ready:** Fact collection logic ready for future policy variations

## ✅ Production Readiness Achieved

With your refinements integrated:
- **Zero missing edge cases** in replacement scope
- **Policy consistency** across all modules
- **Explicit verification** of critical behaviors
- **Future-proof architecture** with clear separation of concerns

Ready for systematic execution of this comprehensive, production-ready plan.