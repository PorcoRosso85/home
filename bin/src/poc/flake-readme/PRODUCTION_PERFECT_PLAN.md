# Production-Perfect Implementation Plan: ignore-only Policy Transition

## ✅ **Final Critical Refinements - "Practically Perfect" Checklist**

### 1. **Comprehensive Test Target Identification (No Exceptions)**
**Beyond test-nix-only-*.nix:** ALL tests assuming nix-only/isDocumentable behavior

**Complete Test Update Target List:**
```bash
# nix-only explicit tests
test-nix-only-validation.nix
test-nix-only-comprehensive.nix
test-nix-only-RED.nix
test-documentable-nix-only.nix

# Integration tests with isDocumentable assumptions
test-integration-comprehensive.nix
test-git-tracking-comprehensive.nix
test-git-boundary-constraints.nix
test-simplified-final.nix
test-simplified-version.nix

# Any other test with documentable/nix-only logic
```

### 2. **Breaking Change Documentation (Step 1.5 Mandatory)**
**Required File Updates:**
- CHANGELOG.md (breaking change entry)
- MIGRATION_GUIDE.md (ignoreExtra + git rm --cached procedures)
- FEATURE_REMOVAL_ANALYSIS.md (impact assessment)
- IMPLEMENTATION_SUMMARY.md (architectural change documentation)

### 3. **examples/ Policy Consistency (DoD Verification)**
**Implementation Fix:**
```nix
# lib/flake-module.nix defaultIgnore (ADD "examples")
defaultIgnore = name: type: builtins.elem name ([
  ".git" ".direnv" "node_modules" "result" "dist" "target" ".cache" "examples"  # ← ADD THIS
] ++ cfg.ignoreExtra);
```

**DoD Verification:** Both core-docs and flake-module have "examples" in defaultIgnore

### 4. **Repository-wide Reference Cleanup (grep-based DoD)**
**Zero Tolerance Verification:**
```bash
# DoD: These greps must return ZERO unintended matches
grep -r "\.nix-only" . --exclude-dir=.git
grep -r "isDocumentable.*policy\|policy.*isDocumentable" . --exclude-dir=.git
grep -r "documentable.*detection\|detection.*documentable" . --exclude-dir=.git

# Exception: Intentional references in MIGRATION_GUIDE.md/CHANGELOG.md are OK
```

### 5. **CLI Output Text Consistency (User-Facing Messages)**
**Target Updates:**
- flake.nix comments ("only for documentable dirs")
- CLI help text/error messages
- User-facing output containing "documentable" terminology
- Any echo/printf statements with old terminology

### 6. **Root "." Requirement Verification (Explicit DoD)**
**DoD Item:** "root . appears in missing when no readme.nix present"
**Test Verification:** Create test case specifically validating root directory behavior

---

## 🎯 **Production-Perfect 4-Step Plan (50 minutes)**

### **Step 1: Repository-Wide Updates + examples/ Fix (15 min)**
**Complete Scope:**
- **15+ Documentation files** (.nix-only → ignore-only)
- **10+ Test files** (ALL with isDocumentable assumptions)
- **Code comments + CLI output** (user-facing text consistency)
- **examples/ fix** (lib/flake-module.nix defaultIgnore addition)
- **Step 1.5 MANDATORY:** Breaking change documentation

### **Step 2: Core Logic Simplification (10 min)**
```nix
# Single line change + clarifying comment
if (!v.hasReadme) && (!shouldIgnore) then p else null
# Comment: "isDocumentable preserved as fact collection only"
```

### **Step 3: Integration Guide Enhancement (10 min)**
- examples/ policy documentation
- Root "." requirement explicit coverage
- DRY principle compliance guidance

### **Step 4: Test Infrastructure Complete Overhaul (15 min)**
- **ALL** tests with isDocumentable assumptions
- 5 representative cases verification
- ignoreExtra behavior validation

---

## 📋 **Production-Perfect Definition of Done**

### **Core Architecture:**
- ✅ v.isDocumentable removed from missing detection (lib/core-docs.nix:160)
- ✅ isDocumentable preserved as "fact collection only" with comment
- ✅ ignore-only policy unified across system

### **Policy Consistency:**
- ✅ examples/ ignored in BOTH core-docs AND flake-module
- ✅ Root "." included in missing detection when no readme.nix
- ✅ ignoreExtra properly extends ignore-only behavior

### **Reference Cleanup (Zero Tolerance):**
- ✅ grep verification: zero unintended .nix-only/documentable references
- ✅ CLI output text consistency (user-facing messages)
- ✅ Test expectations flipped to ignore-only assumptions

### **Breaking Change Documentation:**
- ✅ CHANGELOG.md breaking change entry
- ✅ MIGRATION_GUIDE.md with ignoreExtra + git rm --cached procedures
- ✅ Impact assessment and migration paths documented

### **Test Verification (No Exceptions):**
- ✅ ALL tests with isDocumentable assumptions updated
- ✅ 5 representative cases (non-.nix/has-.nix/ignore/root/examples)
- ✅ Root "." behavior explicitly tested

---

## 🏆 **Production Excellence Achieved**

**Before (Architecture Problem):**
```nix
# Mixed concerns blocking extensibility
if v.isDocumentable && (!v.hasReadme) && (!shouldIgnore)
```

**After (SRP Separation):**
```nix
# Facts and policy cleanly separated
isDocumentable = hasNixFiles;  # FACT (future-ready)
if (!v.hasReadme) && (!shouldIgnore)  # POLICY (ignore-only)
```

**Result:** Clean architecture + comprehensive transition + zero edge cases

This plan now represents **production-level excellence** with exhaustive attention to implementation details that ensure real-world success.