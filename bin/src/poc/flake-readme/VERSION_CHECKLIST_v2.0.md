# Version Preparation Checklist v2.0.0

## Pre-Release Candidate (Current → RC-1 week)

### Core Implementation Review
- [x] **Ignore-only policy**: Complete fact-policy separation implemented
- [x] **Git boundary enforcement**: Working and tested
- [x] **Schema validation**: Comprehensive error/warning system
- [x] **Test suite**: All checks passing (docs-lint, invalid-examples, v1-extension-warnings)
- [ ] **Performance optimization**: Benchmark against v1.x baseline
- [ ] **Memory usage analysis**: Ensure ignore-only approach is efficient
- [ ] **Cross-platform testing**: Verify Linux, macOS, Darwin compatibility

### Documentation Completeness
- [x] **RELEASE_PLAN_v2.0.md**: Comprehensive release planning
- [x] **MIGRATION.md**: User migration guide (existing)
- [x] **Breaking changes**: Clearly documented policy change
- [ ] **API documentation**: Update for v2.0.0 schema changes
- [ ] **Integration examples**: Update flake-parts usage examples
- [ ] **Troubleshooting guide**: Common migration issues and solutions
- [ ] **CHANGELOG.md**: Prepare comprehensive changelog

### Quality Assurance
- [x] **Automated testing**: Full test suite passing
- [x] **Error handling**: Comprehensive validation system
- [x] **Syntax validation**: Working for readme.nix files
- [ ] **Code review**: Final security and quality assessment
- [ ] **Static analysis**: Run additional code quality tools
- [ ] **Edge case testing**: Symlinks, submodules, complex Git histories

## Release Candidate Phase (RC-1 → RC+2 weeks)

### v2.0.0-rc.1 Preparation
- [ ] **Version tagging strategy**: Confirm semantic versioning approach
- [ ] **Release notes**: Draft comprehensive RC notes
- [ ] **Beta tester list**: Identify and contact beta testers
- [ ] **Feedback collection**: Set up issue tracking for RC feedback
- [ ] **Communication plan**: Announce RC to community

### Community Testing
- [ ] **Beta testing**: Engage 3-5 experienced users
- [ ] **Migration testing**: Test with real-world v1.x configurations
- [ ] **Integration testing**: Test with popular flake setups
- [ ] **Performance testing**: Real-world performance validation
- [ ] **Feedback incorporation**: Address critical RC feedback

### Infrastructure Preparation
- [ ] **CI/CD pipeline**: Automate release process
- [ ] **Package distribution**: Verify flake outputs work correctly
- [ ] **Rollback procedures**: Document emergency rollback steps
- [ ] **Monitoring setup**: Track adoption and issues post-release

## Stable Release Phase (RC+2 → RC+3 weeks)

### v2.0.0 Final Preparation
- [ ] **Critical bug fixes**: Address all RC-identified issues
- [ ] **Documentation polish**: Final review and updates
- [ ] **Release notes**: Complete changelog with migration notes
- [ ] **Support materials**: FAQ, troubleshooting guides ready
- [ ] **Communication materials**: Announcement posts, social media

### Release Execution
- [ ] **Final testing**: Complete test suite validation
- [ ] **Version tag**: Create v2.0.0 tag with proper metadata
- [ ] **GitHub release**: Publish with comprehensive notes
- [ ] **Documentation deployment**: Update integration guides
- [ ] **Community announcement**: Post to relevant channels

### Post-Release Activities
- [ ] **Issue triage**: Monitor and prioritize v2.0.0 issues
- [ ] **Migration support**: Provide active migration assistance
- [ ] **Performance monitoring**: Track real-world performance
- [ ] **Feedback collection**: Gather user experience reports
- [ ] **Documentation updates**: Address common questions

## Version Metadata Preparation

### Semantic Versioning
```
Strategy: Start at v2.0.0 (skipping v1.x to emphasize breaking change)
Current: No existing tags (clean slate)
RC Format: v2.0.0-rc.1, v2.0.0-rc.2, etc.
Stable: v2.0.0
```

### Git Tag Strategy
```bash
# RC Release
git tag -a v2.0.0-rc.1 -m "Release Candidate 1: Ignore-only policy implementation"

# Stable Release
git tag -a v2.0.0 -m "v2.0.0: Ignore-only policy with fact-policy separation"
```

### Flake Metadata
- Update flake description to reflect v2.0.0 features
- Ensure lib.docs.index API is stable and documented
- Verify app outputs (readme-init, readme-check) are production-ready

## Success Criteria

### Technical Criteria
- [ ] Zero critical bugs in RC testing
- [ ] Performance parity or improvement vs baseline
- [ ] All automated tests passing consistently
- [ ] Documentation accuracy verified by beta testers

### Community Criteria
- [ ] Positive feedback from beta testing (>75% satisfaction)
- [ ] Migration guide effectiveness (<50% migration support requests)
- [ ] Clear value proposition communication
- [ ] Active community engagement and support

### Release Criteria
- [ ] All checklist items completed
- [ ] Community feedback incorporated
- [ ] Support infrastructure ready
- [ ] Communication plan executed

## Timeline Summary

| Phase | Duration | Key Milestones |
|-------|----------|----------------|
| Pre-RC | 1 week | Complete implementation review, docs update |
| RC Phase | 2 weeks | Community testing, feedback incorporation |
| Stable | 1 week | Final polish, release execution |
| **Total** | **4 weeks** | **v2.0.0 stable release** |

## Emergency Procedures

### Rollback Plan
If critical issues are discovered post-release:
1. **Immediate**: Revert Git tag and GitHub release
2. **Communication**: Notify community of discovered issues
3. **Fix**: Address critical issues in hot-fix branch
4. **Re-release**: Create new version (v2.0.1) with fixes

### Support Escalation
- Critical bugs: 24-48 hour response time
- Migration issues: 2-3 day response time
- General questions: 1 week response time

---

**Checklist Status**: Ready for RC preparation phase
**Next Review**: Pre-RC completion milestone
**Owner**: Development team
**Updated**: 2025-09-23