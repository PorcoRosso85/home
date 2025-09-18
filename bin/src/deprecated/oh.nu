#!/usr/bin/env -S nix shell nixpkgs#nushell --command nu


# # shell例
# shell例
# oh() {
#   prompt=$1
#   sudo docker run -it \
#     --pull=always \
#     -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.27-nikolaik \
#     -e SANDBOX_USER_ID=$(id -u) \
#     -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
#     -e LLM_API_KEY=$LLM_API_KEY \
#     -e LLM_MODEL=$LLM_MODEL \
#     -e LOG_ALL_EVENTS=true \
#     -v $WORKSPACE_BASE:/opt/workspace_base \
#     -v /var/run/docker.sock:/var/run/docker.sock \
#     -v ~/.openhands-state:/.openhands-state \
#     --add-host host.docker.internal:host-gateway \
#     --name openhands-app-$(date +%Y%m%d%H%M%S) \
#     docker.all-hands.dev/all-hands-ai/openhands:0.27 \
#     python -m openhands.core.main -t "$prompt"
# }
# */


export def main [...args] {
  print "この処理を実行するにはユーザーがdockerのsudo権限を保持している必要があります。"
  # print $args
  let prompt = if ($args | length) > 0 {
    $args.0
  } else {
    $in
  }

  if ($prompt | is-empty) {
    print "Usage: oh.nu <prompt>"
    exit 1
  }

  let workspaceBase = ($env.PWD | path expand)
  let llmApiKey = $env.LLM_API_KEY
  let llmModel = "openrouter/google/gemini-2.0-flash-thinking-exp-01-21:free"

  if ($workspaceBase == "" or $llmApiKey == "" or $llmModel == "") {
    print "環境変数 WORKSPACE_BASE, LLM_API_KEY, LLM_MODEL が設定されている必要があります。デフォルト値を使用します。"
    exit 1
  }

  let containerName = $"openhands-app-(date now | format date '%Y%m%d%H%M%S')"
  # print "workspaceBase: " $workspaceBase
  # print $containerName

  (
    docker run
      --rm
      -it
      --pull=always
      "-e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.27-nikolaik"
      -e WORKSPACE_MOUNT_PATH=$workspaceBase
      -e SANDBOX_USER_ID=$(id -u) # TODO, 外すとrootになり壊れる
      -e LLM_API_KEY=$llmApiKey
      -e LLM_MODEL=$llmModel
      -e LOG_ALL_EVENTS=true
      -v $"($workspaceBase):/opt/workspace_base"
      -v /var/run/docker.sock:/var/run/docker.sock
      -v /home/nixos/.openhands-state:/.openhands-state
      --add-host host.docker.internal:host-gateway
      --name $containerName
      docker.all-hands.dev/all-hands-ai/openhands:0.27
      python -m openhands.core.main -t $prompt
  )
}
