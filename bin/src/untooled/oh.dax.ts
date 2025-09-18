#!/usr/bin/env -S nix shell nixpkgs#deno --command deno run --allow-all

import $ from "jsr:@david/dax";

/**
shell例
oh() {
  prompt=$1
  sudo docker run -it \
    --pull=always \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.27-nikolaik \
    -e SANDBOX_USER_ID=$(id -u) \
    -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
    -e LLM_API_KEY=$LLM_API_KEY \
    -e LLM_MODEL=$LLM_MODEL \
    -e LOG_ALL_EVENTS=true \
    -v $WORKSPACE_BASE:/opt/workspace_base \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v ~/.openhands-state:/.openhands-state \
    --add-host host.docker.internal:host-gateway \
    --name openhands-app-$(date +%Y%m%d%H%M%S) \
    docker.all-hands.dev/all-hands-ai/openhands:0.27 \
    python -m openhands.core.main -t "$prompt"
}
*/
async function main(prompt: string) {
  const workspaceBase = Deno.env.get("WORKSPACE_BASE") ?? ".";
  const llmApiKey = Deno.env.get("LLM_API_KEY") ?? "";
  const llmModel = Deno.env.get("LLM_MODEL") ?? "openrouter/google/gemini-2.0-flash-thinking-exp-01-21:free";

  if (!workspaceBase || !llmApiKey || !llmModel) {
    console.error("環境変数 WORKSPACE_BASE, LLM_API_KEY, LLM_MODEL が設定されている必要があります。デフォルト値を使用します。");
    // Deno.exit(1);
  }

  const containerName = `openhands-app-${new Date().toISOString().replace(/[-:T.Z]/g, "")}`;
  const home = Deno.env.get("HOME") ?? "";
  if (!home) {
    console.error("環境変数 HOME が設定されている必要があります。");
  }

  const userIdProc = Deno.run({
    cmd: ["id", "-u"],
    stdout: "piped",
    stderr: "null",
  });
  const userIdOutput = new TextDecoder().decode(await userIdProc.output());
  userIdProc.close();
  const userId = userIdOutput.trim();

  const result = await $`docker run
    -it
    --rm
    --pull=always
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.27-nikolaik
    -e SANDBOX_USER_ID=${userId}
    -e WORKSPACE_MOUNT_PATH=${workspaceBase}
    -e LLM_API_KEY=${llmApiKey}
    -e LLM_MODEL=${llmModel}
    -e LOG_ALL_EVENTS=true
    -v ${workspaceBase}:/opt/workspace_base
    -v /var/run/docker.sock:/var/run/docker.sock
    -v ${home}/.openhands-state:/.openhands-state
    --add-host host.docker.internal:host-gateway
    --name ${containerName}
    docker.all-hands.dev/all-hands-ai/openhands:0.27
    python -m openhands.core.main -t ${prompt}
    `
    .text();
    // .stdout("piped")
    // .stderr("piped");

  console.log(result)
}

if (import.meta.main) {
  if (Deno.args.length < 1) {
    console.error("Usage: oh.dax.ts <prompt>");
    Deno.exit(1);
  }
  const prompt = Deno.args[0];
  await main(prompt);
}
