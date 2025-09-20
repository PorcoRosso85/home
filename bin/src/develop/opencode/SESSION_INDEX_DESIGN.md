# Session Index Design - Operational Value Documentation

## Purpose

Enhance OpenCode session management operability through bidirectional SID↔dir mapping while maintaining strict adherence to 5 principles (SRP/YAGNI/KISS/DRY/SOLID) and "code for purpose only" convergence.

## Core Values

### 1. Operational Diagnostics & Cleanup
- **Value**: SID→dir reverse lookup enables immediate session identification
- **Use Case**: `ses_abc123...` → `/path/to/project` resolution for troubleshooting
- **Benefit**: Rapid problem identification during session management operations

### 2. Server API Transparency
- **Value**: Zero server-side modifications required
- **Principle**: Non-destructive enhancement to existing systems
- **Advantage**: Independent client-server evolution paths

### 3. Backward Compatibility Guarantee
- **Value**: Existing dir→SID file structure preserved
- **Location**: `${XDG_STATE_HOME}/opencode/sessions/$hostport/$project.session`
- **Policy**: Additive functionality only, no existing behavior changes

### 4. Privacy & Portability Considerations
- **Risk Awareness**: Index with raw paths may expose confidential directory structures
- **Future Options**:
  - `OPENCODE_INDEX=0` disable mode (YAGNI - implement when needed)
  - `dirHash-only` mode without raw paths (YAGNI - implement when needed)
- **Current Approach**: Full functionality with documented privacy implications

## Implementation Strategy: Tier-Based Progression

### Tier 0: Minimal Implementation (Current Scope)
- **Approach**: append-only index.jsonl
- **Benefits**: Simple, crash-resistant, rebuild-capable
- **Constraints**: Single process, basic corruption handling
- **Scalability**: Suitable for thousands to tens of thousands of sessions

### Tier 1: Production Hardening (Future)
- **Enhancements**: tmp→fsync→rename, monthly rotation, light locking
- **Trigger**: Multi-process requirements or larger session volumes

### Tier 2: High-Availability (Future)
- **Enhancements**: Explicit file locking, memory LRU cache, full corruption recovery
- **Trigger**: High-concurrency environments or critical uptime requirements

### Tier 3: Database Migration (Future)
- **Approach**: SQLite indexing for complex queries
- **Trigger**: Hundreds of thousands of sessions or complex search requirements

## 5 Principles Compliance

### Single Responsibility Principle (SRP)
- **Index Functions**: Dedicated `oc_session_index_*` namespace
- **Separation**: Session management ≠ Index management
- **Clarity**: Each function has single, well-defined purpose

### You Aren't Gonna Need It (YAGNI)
- **Start Simple**: Tier 0 implementation only
- **Progressive Enhancement**: Add complexity only when requirements proven
- **Feature Gating**: Optional components await actual usage demands

### Keep It Simple, Stupid (KISS)
- **No Database**: Text-based JSONL format
- **Append-Only**: Minimal file operations
- **Human Readable**: Debuggable with standard tools (cat, grep, jq)

### Don't Repeat Yourself (DRY)
- **Unified API**: Consistent `oc_session_index_*` naming
- **Centralized Normalization**: Single point for path/hostport processing
- **Error Contract Unity**: stdout=data, stderr=log, non-zero=failure

### SOLID Principles
- **Open/Closed**: Extensible (Tier 0→1→2) without modifying existing code
- **Liskov Substitution**: Index functions replaceable between tiers
- **Interface Segregation**: Focused function interfaces
- **Dependency Inversion**: Abstract away storage implementation details

## Expected Outcomes

### Immediate Benefits
1. **SID→dir reverse lookup**: Instant session origin identification
2. **dir→multiple SID listing**: Historical session tracking per project
3. **Operation transparency**: No hidden server-side dependencies
4. **Backward compatibility**: Existing workflows unaffected

### Operational Improvements
1. **Debugging**: Quick session-to-project mapping
2. **Cleanup**: Bulk session management by project
3. **Migration**: Project relocation with session preservation
4. **Monitoring**: Session usage patterns analysis

### Future Extensibility
1. **Staged Hardening**: Tier 0→1→2 progression as needed
2. **Privacy Options**: Configurable path exposure levels
3. **Performance Scaling**: Database migration when justified
4. **Integration Ready**: API contracts support advanced tooling

## Risk Mitigation

### Privacy
- **Documentation**: Clear explanation of index content
- **Future Safeguards**: Planned disable/hash-only modes
- **User Control**: Transparent operation with clear data location

### Reliability
- **Corruption Handling**: Built-in broken line skipping
- **Recovery Mechanism**: bydir scan → index rebuild capability
- **Graceful Degradation**: System continues without index if needed

### Performance
- **Bounded Growth**: Tier progression prevents resource exhaustion
- **Efficient Access**: JSONL format enables line-by-line processing
- **Memory Management**: Process-scoped duplicate prevention

## Conclusion

This session index design delivers immediate operational value while maintaining strict adherence to software engineering principles. The tier-based approach ensures sustainable growth without premature optimization, and the privacy-conscious design provides clear upgrade paths for various deployment scenarios.

The implementation prioritizes user value (operation diagnostics), system integrity (backward compatibility), and engineering excellence (5 principles compliance) in a balanced, pragmatic approach.