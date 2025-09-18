# Collaborative Text Editing without CRDTs or OT

Author: Matthew Weidner  
Date: May 21st, 2025  
Source: https://mattweidner.com/2025/05/21/text-without-crdts.html

## Summary

This article proposes a simple alternative to Conflict-free Replicated Data Types (CRDTs) and Operational Transformation (OT) for collaborative text editing.

## Core Approach

The key idea is to:
1. Label each text character with a unique global ID
2. Have clients send "insert after" operations that reference specific character IDs
3. Let the server process operations literally by inserting text after the specified IDs

## Main Advantages

- **Conceptually simpler** than existing CRDT/OT approaches
- **More flexible** for implementing custom collaborative editing features
- **Supports optimistic local updates** through server reconciliation
- **Naturally handles concurrent operations** without complex conflict resolution

## Technical Implementation

### Text State Representation
```typescript
Array<{ id: ID; char?: string; isDeleted: boolean }>
```

### Key Properties
- Concurrent insertions are processed in reverse order of server receipt
- Supports rich text and flexible operation types
- Can be adapted for both centralized and decentralized collaboration

## Relationship to Existing CRDTs

The author notes that this method is technically equivalent to some existing CRDTs like RGA/Causal Trees, but with a more straightforward implementation that's easier to understand and customize.

## Helper Library: Articulated

The article introduces "Articulated", a helper library designed to optimize ID list management for this approach, making it more practical for production use.

## Practical Applications

This approach is particularly suitable for:
- Real-time collaborative text editors
- Applications requiring custom collaborative features
- Systems where simplicity and flexibility are prioritized over pure theoretical elegance