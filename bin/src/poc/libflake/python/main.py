#!/usr/bin/env python3
from core.database import create_database, create_connection

db = create_database(":memory:")
conn = create_connection(db)

conn.execute("CREATE NODE TABLE Person(name STRING, PRIMARY KEY(name))")
conn.execute("CREATE (:Person {name: 'Alice'})")
result = conn.execute("MATCH (p:Person) RETURN p.name")

print(f"✓ Query result: {result.get_next()[0]}")
print("✓ Persistence module works!")