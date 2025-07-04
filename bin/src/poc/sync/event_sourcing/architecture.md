# Template-based Event Sourcing Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                             Browser (KuzuDB WASM)                         │
├──────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────────────────┐ │
│  │   Cypher    │    │   Template   │    │      Local KuzuDB           │ │
│  │  Templates  ├───►│   Executor   ├───►│  ┌─────────┐ ┌──────────┐  │ │
│  │  (.cypher)  │    │              │    │  │  Nodes  │ │  Edges   │  │ │
│  └─────────────┘    └──────┬───────┘    │  └─────────┘ └──────────┘  │ │
│                            │             └─────────────────────────────┘ │
│                            ▼                                              │
│                     ┌──────────────┐                                     │
│                     │Template Event│                                     │
│                     │  Generator   │                                     │
│                     └──────┬───────┘                                     │
└────────────────────────────┼─────────────────────────────────────────────┘
                             │ Template Event
                             ▼ {template: "CREATE_USER", params: {...}}
┌──────────────────────────────────────────────────────────────────────────┐
│                          Server (Event Store Only)                        │
├──────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────────────────┐ │
│  │  Template   │    │   Event      │    │     Event Log (JSONL)       │ │
│  │ Validator   ├───►│   Store      ├───►│ evt_1|CREATE_USER|{...}|t1  │ │
│  │             │    │              │    │ evt_2|UPDATE_USER|{...}|t2  │ │
│  └─────────────┘    └──────┬───────┘    │ evt_3|FOLLOW_USER|{...}|t3  │ │
│                            │             └─────────────────────────────┘ │
│                            ▼                                              │
│                     ┌──────────────┐                                     │
│                     │  Broadcast   │                                     │
│                     │   to Other   │                                     │
│                     │   Browsers   │                                     │
│                     └──────────────┘                                     │
└──────────────────────────────────────────────────────────────────────────┘

## Key Points

1. **Browsers**: Have KuzuDB WASM, execute Cypher templates locally
2. **Server**: Pure event store, no graph database, validates and broadcasts
3. **Templates**: Prevent injection, ensure consistency across clients
4. **Events**: Immutable log of template executions with parameters