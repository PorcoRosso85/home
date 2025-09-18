#!/usr/bin/env -S nix shell nixpkgs#deno --command deno run --allow-all
import { z } from "npm:zod";
console.log(z.string().parse("hello"));