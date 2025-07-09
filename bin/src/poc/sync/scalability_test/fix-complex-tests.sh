#!/usr/bin/env bash
# Fix memory issues in complex scenarios test

sed -i 's/await disconnect(client);/\/\/ クリーンアップはafterEachで実行/g' complex-scenarios.test.ts

# Add client tracking for each test
sed -i '/const client = await createCausalSyncClient({$/,/});$/{
  /});$/a\    allClients.push(client);
}' complex-scenarios.test.ts

echo "Fixed complex scenarios test file"