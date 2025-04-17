#!/usr/bin/env -S nix run nixpkgs#nodejs_22
const kuzu = require("kuzu");

(async () => {
  // Create an empty on-disk database and connect to it
  const db = new kuzu.Database("");
  const conn = new kuzu.Connection(db);

  const queryResult = await conn.query("RETURN 1;");

  // Get all rows from the query result
  const rows = await queryResult.getAll();

  // Print the rows
  for (const row of rows) {
    console.log(row);
  }
})();
