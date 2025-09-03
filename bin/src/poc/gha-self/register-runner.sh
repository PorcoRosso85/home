#!/usr/bin/env bash
set -euo pipefail

echo "Getting registration token..."
TOKEN=$(gh api \
  --method POST \
  -H "Accept: application/vnd.github+json" \
  /repos/$(gh repo view --json nameWithOwner -q .nameWithOwner)/actions/runners/registration-token \
  -q .token)

echo "Configuring runner..."
github-runner configure \
  --url "https://github.com/$(gh repo view --json nameWithOwner -q .nameWithOwner)" \
  --token "$TOKEN" \
  --name "nix-runner-$(hostname)" \
  --labels "self-hosted,nix,flake-gha-self" \
  --work "_work" \
  --unattended \
  --replace

echo "Runner registered successfully!"
echo "Run ./run-runner.sh to start the runner"