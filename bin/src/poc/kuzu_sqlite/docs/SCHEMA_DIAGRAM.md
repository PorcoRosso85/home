# SQLite Schema → KuzuDB Graph Structure

## SQLite Relational Schema (Source)

```
┌─────────────────────────┐
│        users            │
├─────────────────────────┤
│ id      INTEGER PK      │
│ name    TEXT            │
│ age     INTEGER         │
│ city    TEXT            │
└─────────────────────────┘
           │
           │ 1:N
           ├──────────────┐
           │              │
           ▼              ▼
┌─────────────────────────┐  ┌─────────────────────────┐
│       follows           │  │        posts            │
├─────────────────────────┤  ├─────────────────────────┤
│ follower_id INTEGER FK  │  │ id         INTEGER PK   │
│ followee_id INTEGER FK  │  │ user_id    INTEGER FK   │
│ since       DATE        │  │ content    TEXT         │
├─────────────────────────┤  │ created_at TIMESTAMP    │
│ PK(follower_id,         │  └─────────────────────────┘
│    followee_id)         │             │
└─────────────────────────┘             │ 1:N
                                        │
                                        ▼
                          ┌─────────────────────────┐
                          │        likes            │
                          ├─────────────────────────┤
                          │ user_id    INTEGER FK   │
                          │ post_id    INTEGER FK   │
                          │ liked_at   TIMESTAMP    │
                          ├─────────────────────────┤
                          │ PK(user_id, post_id)    │
                          └─────────────────────────┘
```

## Relationships in SQLite

```
users.id ──────┬──→ follows.follower_id
               ├──→ follows.followee_id
               ├──→ posts.user_id
               └──→ likes.user_id

posts.id ──────────→ likes.post_id
```

## KuzuDB Graph Structure (Target)

```
                    ┌──────────────┐
                    │     User     │
                    │   (NODE)     │
                    ├──────────────┤
                    │ id: INT64    │
                    │ name: STRING │
                    │ age: INT64   │
                    │ city: STRING │
                    └──────────────┘
                      │    ▲    │
                      │    │    │
         ┌────────────┤    │    ├────────────┐
         │            │    │    │            │
         │         FOLLOWS │    │            │
         │          (REL)  │    │            │
         │      ┌──────────┴────┤            │
         │      │               │            │
         │      │  since: DATE  │            │
         │      └───────────────┘            │
         │                                   │
         │                                   │
    POSTED (REL)                        LIKES (REL)
         │                                   │
         │                                   │
         ▼                                   ▼
    ┌──────────────┐                   ┌──────────────┐
    │     Post     │◄──────────────────│              │
    │   (NODE)     │      LIKES        │              │
    ├──────────────┤    liked_at:      │              │
    │ id: INT64    │    TIMESTAMP      │              │
    │ content:     │                   └──────────────┘
    │   STRING     │
    │ created_at:  │
    │   STRING     │
    └──────────────┘
```

## Data Transformation Mapping

```
SQLite Table          →    KuzuDB Structure
─────────────────────────────────────────────
users                 →    User (NODE)
posts                 →    Post (NODE)
follows               →    FOLLOWS (REL: User→User)
posts.user_id         →    POSTED (REL: User→Post)
likes                 →    LIKES (REL: User→Post)
```

## Example Graph Pattern

```
Alice ─FOLLOWS→ Bob ─FOLLOWS→ Dan
  │               │              │
  │               └──POSTED──→ Post2
  │                              ▲
  └─────────LIKES────────────────┘

Carol ─FOLLOWS→ Eve ─FOLLOWS→ Frank
  │               │
  └──FOLLOWS──→ Alice
```

## Query Pattern Examples

### 1. Mutual Follow (相互フォロー)
```
(User1) ─FOLLOWS→ (User2)
   ▲                 │
   └────FOLLOWS──────┘
```

### 2. Friend of Friend (2-hop)
```
(Alice) ─FOLLOWS→ (Friend) ─FOLLOWS→ (FriendOfFriend)
```

### 3. Triangle Relationship
```
    (A)
   ╱   ╲
  ↓     ↓
(B) ──→ (C)
```

### 4. Post Engagement
```
(Author) ─POSTED→ (Post) ←LIKES─ (User1)
                     ▲
                     │
                  LIKES
                     │
                  (User2)
```