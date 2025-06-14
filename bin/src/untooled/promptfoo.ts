#!/usr/bin/env -S nix shell nixpkgs#deno --command deno run --allow-all
import promptfoo from "npm:promptfoo";
const results = await promptfoo.evaluate("", "");