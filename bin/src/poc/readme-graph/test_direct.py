#!/usr/bin/env nix-shell
#!nix-shell -i python3 -p python312Packages.kuzu

import kuzu
from pathlib import Path

db_path = "./test.db"

if Path(db_path).exists():
    import shutil
    shutil.rmtree(db_path)

db = kuzu.Database(db_path)
conn = kuzu.Connection(db)

conn.execute("""
    CREATE NODE TABLE Module(
        path STRING PRIMARY KEY,
        purpose STRING,
        type STRING
    )
""")

conn.execute("""
    CREATE REL TABLE DEPENDS_ON(FROM Module TO Module)
""")

conn.execute("""
    CREATE (m:Module {
        path: '/test/module',
        purpose: 'Test module',
        type: 'service'
    })
""")

result = conn.execute("MATCH (m:Module) RETURN m.path, m.purpose, m.type")
while result.has_next():
    row = result.get_next()
    print(f"Module: path={row[0]}, purpose={row[1]}, type={row[2]}")

print("✅ Test successful!")