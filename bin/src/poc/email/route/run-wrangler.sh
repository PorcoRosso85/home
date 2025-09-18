#!/usr/bin/env bash

echo "Starting wrangler in development mode..."
echo "Server will be available at http://localhost:8787"
echo ""
echo "Test endpoints:"
echo "  curl http://localhost:8787/__health"
echo "  curl -X POST http://localhost:8787/__email -H 'Content-Type: application/json' -d '{\"from\":\"test@example.com\",\"to\":\"archive@test.com\",\"body\":\"Test email\"}'"
echo ""

exec nix shell nixpkgs#wrangler --command wrangler dev --local --port 8787