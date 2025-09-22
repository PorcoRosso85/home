# Release Plan v2.0.0 - Ignore-Only Policy Implementation

## Executive Summary

This document outlines the comprehensive release plan for flake-readme v2.0.0, which implements the fact-policy separation with an ignore-only system. This represents a **breaking change** from v1.x behavior, requiring careful migration planning and user communication.

## Breaking Change Summary

### Core Policy Change
- **v1.x Behavior**: Mixed fact/policy system allowing both explicit inclusion and exclusion patterns
- **v2.0.0 Behavior**: Pure ignore-only system - all files tracked by Git are included unless explicitly ignored
- **Impact**: Existing configurations using inclusion patterns (`include.*`) will be deprecated and non-functional

### User-Facing Changes
1. **Configuration Schema**: Extension fields (`usage`, `features`, `techStack`) remain as warnings in v2.0 for backward compatibility
2. **Flake Output Behavior**: Removed `docs-json`, `docs-report`, and `default` packages - functionality consolidated to `lib.docs.index`
3. **Git Integration**: Enhanced boundary enforcement - respects `.gitignore` and Git tracking status more strictly

## Version Timeline

### Phase 1: Release Candidate (Target: Current + 2 weeks)
- **v2.0.0-rc.1**: Initial release candidate
  - Complete ignore-only implementation
  - Comprehensive test suite validation
  - Documentation update completion
  - Migration guide finalization

### Phase 2: Stable Release (Target: RC + 3 weeks)
- **v2.0.0**: Stable release
  - All critical issues from RC phase resolved
  - Community feedback incorporation
  - Production-ready documentation
  - Announcement and communication rollout

### Phase 3: Support Transition (Target: Stable + 6 months)
- **v1.x EOL Planning**: Deprecation notices and migration support
- **v2.1.x**: First maintenance releases with bug fixes and minor enhancements

## Current Version Status Analysis

```
Current State: No semantic versioning tags found
Recent Commits:
- fd6b02b8: feat: implement fact-policy separation with ignore-only system
- 6729daa2: fix: complete notation consistency for external user experience
- f98b4f8a: feat: unify OpenCode client notation

Version Strategy: Starting from v2.0.0 (skipping v1.x to emphasize breaking change)
```

## Deprecation Schedule

### v1.x Support Duration
- **Immediate (v2.0.0 Release)**: v1.x enters maintenance mode
- **6 months post-v2.0.0**: Security fixes only for v1.x
- **12 months post-v2.0.0**: Complete v1.x end-of-life

### Extension Field Transition
- **v2.0.0**: Extension fields generate warnings (backward compatibility)
- **v2.1.0**: Extension fields trigger deprecation notices
- **v3.0.0**: Extension fields become errors (full enforcement)

## Testing Requirements Before Release

### Automated Test Coverage
- [x] Invalid example detection (validates error/warning generation)
- [x] v1 extension field warning system
- [x] Documentation structure validation
- [ ] Migration path testing (v1.x → v2.0.0 conversion)
- [ ] Performance regression testing
- [ ] Cross-platform compatibility (Linux, macOS, Darwin)

### Manual Testing Checklist
- [ ] Real-world flake integration testing
- [ ] Git boundary enforcement validation
- [ ] Error message clarity and actionability
- [ ] Documentation accuracy and completeness
- [ ] App functionality (`readme-init`, `readme-check`)

### Integration Testing
- [ ] flake-parts module compatibility
- [ ] Complex project structure handling
- [ ] Edge case validation (submodules, symlinks, large repos)
- [ ] Concurrent usage testing

## Risk Assessment and Mitigation

### High-Risk Areas
1. **Breaking Change Impact**
   - *Risk*: Existing users experience sudden configuration failures
   - *Mitigation*: Comprehensive migration guide, grace period with warnings, automated migration tools

2. **Git Integration Complexity**
   - *Risk*: Boundary enforcement may be too restrictive or inconsistent
   - *Mitigation*: Extensive testing with diverse repository structures, clear documentation of Git assumptions

3. **Performance Implications**
   - *Risk*: Ignore-only system may process more files than necessary
   - *Mitigation*: Performance benchmarks, optimization strategies, early performance regression detection

### Medium-Risk Areas
1. **Documentation Gap**
   - *Risk*: Users lack clear guidance for migration
   - *Mitigation*: Multi-format documentation (README, examples, migration scripts)

2. **Community Adoption**
   - *Risk*: Resistance to breaking changes
   - *Mitigation*: Clear value proposition communication, community engagement, responsive support

## Announcement Channels and Communication Plan

### Pre-Release Communication (RC Phase)
- [ ] GitHub Issues: Breaking change announcement
- [ ] Documentation: Migration guide publication
- [ ] Community: Advance notice to known users
- [ ] Internal: Development team alignment

### Release Communication
- [ ] GitHub Release: Comprehensive changelog with migration notes
- [ ] Documentation Site: Updated integration examples
- [ ] Social Media: Feature highlights and migration resources
- [ ] Nix Community: NixOS Discourse post with technical details

### Post-Release Support
- [ ] Issue Triage: Prioritize migration-related problems
- [ ] Documentation Updates: Address common migration questions
- [ ] Community Feedback: Collect and incorporate user experience reports

## Version Preparation Checklist

### Code Readiness
- [x] Core ignore-only implementation complete
- [x] Test suite comprehensive and passing
- [ ] Performance optimization review
- [ ] Code review and quality assessment
- [ ] Security review completion

### Documentation Readiness
- [ ] API documentation updated for v2.0.0 schema
- [ ] Migration guide written and tested
- [ ] Integration examples updated
- [ ] Troubleshooting guide enhanced
- [ ] CHANGELOG.md preparation

### Release Infrastructure
- [ ] Semantic versioning tag strategy confirmed
- [ ] CI/CD pipeline validation for release workflow
- [ ] Package distribution mechanism verification
- [ ] Rollback procedure documentation

### Community Readiness
- [ ] Beta testing with select community members
- [ ] Feedback incorporation and iteration
- [ ] Support channel preparation
- [ ] Known issues documentation

## Success Metrics

### Release Success Indicators
- Zero critical bugs in first 2 weeks post-release
- Migration guide effectiveness (< 50% support requests about migration)
- Community adoption rate (usage metrics if available)
- Performance parity or improvement vs v1.x

### Long-term Success Metrics
- User satisfaction with ignore-only approach
- Reduced configuration complexity
- Improved Git integration reliability
- Community contribution growth

## Timeline Summary

| Milestone | Target Date | Key Deliverables |
|-----------|-------------|------------------|
| RC Preparation | Current + 1 week | Complete testing, finalize documentation |
| v2.0.0-rc.1 | Current + 2 weeks | Release candidate with full feature set |
| Stable Release | RC + 3 weeks | v2.0.0 with community feedback incorporated |
| v1.x EOL Notice | Stable + immediate | Begin deprecation communication |
| Full v1.x EOL | Stable + 12 months | Complete transition to v2.x |

---

*Generated: 2025-09-23*
*Last Updated: Initial version*
*Next Review: Pre-RC milestone*