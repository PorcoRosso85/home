'use client';

import { useEffect, useState } from 'react';

export default function KuzuTest() {
  const [result, setResult] = useState<string>('Loading...');
  
  useEffect(() => {
    async function testKuzu() {
      try {
        const kuzu_wasm = (await import('kuzu-wasm')).default;
        const kuzu = await kuzu_wasm();
        const db = await kuzu.Database();
        const conn = await kuzu.Connection(db);
        
        await conn.execute(`CREATE NODE TABLE User(name STRING, PRIMARY KEY (name))`);
        await conn.execute(`CREATE (u:User {name: 'Alice'})`);
        const res = await conn.execute(`MATCH (u:User) RETURN u.name`);
        
        setResult(res.table.toString());
      } catch (error) {
        setResult(`Error: ${error}`);
      }
    }
    
    testKuzu();
  }, []);
  
  return (
    <div>
      <h1>Kuzu WASM Test</h1>
      <pre>{result}</pre>
    </div>
  );
}