#!/usr/bin/env -S nix run nixpkgs#deno -- run --allow-all --allow-scripts=npm:kuzu@0.9.0

/**
❯ LD_LIBRARY_PATH=/nix/store/2y8c3b7ydkl68liz336035llfhmm6r95-gfortran-14-20241116-lib/lib/:$LD_LIBRARY_PATH ./init.ts
*/

import * as kuzu from "kuzu";

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
