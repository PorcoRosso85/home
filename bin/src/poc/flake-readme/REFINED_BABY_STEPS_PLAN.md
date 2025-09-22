# Refined Baby Steps Plan: Fact-Policy Separation Implementation

## Pre-Analysis: Understanding the Value

**Application Essence**: flake-readme is a documentation requirement enforcement system that should clearly separate what it observes (facts) from what it requires (policies).

**Current Problem**: Documentation conflates technical capabilities with policy decisions, creating user confusion about what's configurable vs. hardcoded.

**Target Value**: Clear separation enables users to understand system capabilities independently from current policy settings.

---

## Step 1: Policy Documentation Clarification (Reference-Stable)

### 1.1: Value Clarification (WHY)
- **Core Value**: Users need to distinguish between system facts and policy choices
- **Business Impact**: Reduces confusion, improves maintainability, enables policy evolution
- **User Benefit**: Clear understanding of what can be configured vs. what is system behavior

### 1.2: Specification Definition (WHAT) [RED]
- **Target**: Keyword-based documentation updates (stable references)
- **Search Keywords**: ".nix-only", "documentable", ".nix-only Documentable Detection", "nix-only"
- **Scope**: README.md, docs/integration.md, comprehensive search for related content
- **Outcome**: ".nix-only" policy descriptions replaced with "ignore-only" approach

### 1.3: Implementation (HOW) [GREEN]
- **Primary**: README.md keyword-based replacement
- **Secondary**: docs/integration.md consistency updates
- **Method**: Search-and-replace with context validation

### 1.4: Verification (CHECK)
- **Test**: All ".nix-only" references removed from documentation
- **Consistency**: Policy language clearly distinguished from fact descriptions
- **Integration**: docs/integration.md examples reflect new approach

### 1.5: Breaking Change Documentation (CHANGELOG/MIGRATION) [NEW]
- **CHANGELOG**: Document breaking change with clear impact assessment
- **MIGRATION**: ignoreExtra usage examples and git rm --cached workflows
- **User Guide**: Practical transition steps for existing users

---

## Step 2: Missing Detection Logic Simplification (Minimal Diff)

### 2.1: Value Clarification (WHY)
- **SRP Principle**: Separate fact recording (isDocumentable) from policy judgment (missing detection)
- **Maintainability**: Policy can evolve without changing fact collection
- **Clarity**: Users understand what system observes vs. what it requires

### 2.2: Specification Definition (WHAT) [RED]
- **Target**: lib/core-docs.nix:160 condition modification
- **Change**: Remove `v.isDocumentable` from missing detection condition
- **Result**: All directories (including root ".") checked for readme.nix regardless of content
- **Test Cases**: 4 representative scenarios (non-.nix/has-.nix/ignore/root)

### 2.3: Implementation (HOW) [GREEN]
- **Code Change**: lib/core-docs.nix:160 condition update
- **Comment Addition**: Clarify isDocumentable role as "fact only"
- **Future Note**: Mark isDocumentable for potential removal if unused

### 2.4: Verification (CHECK)
- **Root Coverage**: Verify "." directory included in missing detection
- **Ignore Respect**: Confirm ignore patterns still exclude properly
- **Test Updates**: Update test expectations for new behavior
- **Representative Cases**: All 4 cases working correctly

---

## Step 3: Test Infrastructure Updates (Existing Test Alignment)

### 3.1: Test Impact Analysis (WHY)
- **Regression Prevention**: Ensure behavior changes are intentional
- **Specification Alignment**: Tests reflect new policy-fact separation
- **Coverage Verification**: Representative cases properly tested

### 3.2: Test Case Updates (WHAT) [RED]
- **Candidates**: test-documentable-nix-only.nix, test-non-nix-dir
- **New Expectations**: Non-.nix directories now generate missing warnings
- **Representative Cases**: 4 core scenarios explicitly tested

### 3.3: Implementation (HOW) [GREEN]
- **Update Test Expectations**: Align with new missing detection logic
- **Add Missing Cases**: Ensure representative scenarios covered
- **Maintain Regression Coverage**: Existing valid behavior preserved

### 3.4: Verification (CHECK)
- **Test Suite**: All tests pass with new logic
- **Coverage**: 4 representative cases explicitly verified
- **Regression**: No unintended behavior changes

---

## Step 4: Documentation Ecosystem Updates (Comprehensive Consistency)

### 4.1: Integration Guide Enhancement (WHY)
- **DRY Principle**: Avoid README duplication while ensuring completeness
- **Practical Value**: Users get actionable guidance in context
- **Operational Excellence**: Git workflows properly documented

### 4.2: Content Updates (WHAT) [RED]
- **docs/integration.md**: "Missing readme.nix" section updates
- **Ignore Recommendations**: Practical examples without README duplication
- **Git Operations**: git rm --cached workflows in integration context

### 4.3: Implementation (HOW) [GREEN]
- **Integration Guide**: Update missing detection examples
- **Operational Guidance**: Add practical ignore/git workflows
- **Cross-Reference**: Maintain coherent documentation ecosystem

### 4.4: Verification (CHECK)
- **Consistency**: All documentation reflects new fact-policy separation
- **Completeness**: Users can successfully implement ignore strategies
- **DRY Compliance**: No excessive duplication between documents

---

## Final Definition of Done (DoD)

### Core Behavior Changes:
- **Missing Detection**: `ignore`に一致しない全ディレクトリ（`.` 含む）で readme.nix が無ければ missingReadmes に出る
- **Code Location**: lib/core-docs.nix:160 の条件から `v.isDocumentable` が取り除かれている
- **Collection Boundary**: flake 境界と readme.nix 収集の挙動は不変

### Documentation Updates:
- **README**: ".nix-only" 記述が撤回され、"ignore-only" 方針が明記
- **Integration Guide**: Missing 例・ガイドが新方針準拠
- **Breaking Changes**: CHANGELOG と MIGRATION に破壊的変更と移行手順が追記

### Technical Verification:
- **Tests**: 代表ケース4種（非.nix/有.nix/ignore/ルート）を満たし、既存テストの期待が新方針と整合
- **Comments**: isDocumentable の役割が「事実」である旨と、現状は欠落判定に使わない旨をコードで明記

### Risk Mitigation:
- **Breaking Change Impact**: 事前にドキュメント/CHANGELOG で周知、ignoreExtra の活用例を提示
- **KISS/YAGNI Adherence**: ベース名のみの ignore 判定の限界は現段階で据え置き、将来の拡張余地として注記

This plan incorporates all your excellent feedback while maintaining the Baby Steps structure for systematic implementation.