#!/usr/bin/env -S nix shell nixpkgs#nushell --command nu

# const THINK = "openrouter/anthropic/claude-3.7-sonnet:thinking"
# const THINK = "openrouter/qwen/qwq-32b:free"
# const THINK = "openrouter/qwen/qwen-plus"
# const THINK = "openrouter/qwen/qwen2.5-32b-instruct"
# const THINK = "deepseek/deepseek-reasoner"
# const THINK = "deepseek/deepseek-chat"
# const THINK = "openrouter/perplexity/r1-1776"
# const THINK = "openrouter/google/gemini-2.0-pro-exp-02-05:free"
# const THINK = "gemini/gemini-2.0-pro-exp-02-05"
# const THINK = "gemini/gemini-2.0-flash-thinking-exp-01-21"
# const THINK = "openrouter/openai/o3-mini-high"
# const CODE = "openrouter/google/gemini-2.0-flash-001"
# const CODE = "openrouter/google/gemini-2.0-pro-exp-02-05:free"
# const CODE = "gemini/gemini-2.0-pro-exp-02-05"
# const CODE = "openrouter/openai/gpt-4o-mini"
# const THINK = "gemini/gemini-2.0-pro-exp-02-05"
# const CODE = "gemini/gemini-2.0-pro-exp-02-05"
# const CODE = "deepseek/deepseek-coder"

# const provider = ["google", "gemini-2.0-pro-exp-02-05"]
# const provider = ["gemini", "gemini-2.0-flash-thinking-exp-01-21"]
# const provider = ["github", "deepSeek-r1"]
# const provider = ["openrouter", "google/gemini-2.0-pro-exp-02-05:free"]
# const provider = ["openrouter", "google/gemini-2.0-flash-thinking-exp:free"]
# const provider = ["openrouter", "google/gemini-2.0-flash-lite-preview-02-05:free"]
# const provider = ["openrouter", "deepseek/deepseek-r1:free"]
const provider = ["openrouter", "deepseek/deepseek-chat-v3-0324"]
# const provider = ["openrouter", "openai/o3-mini-high"]
# const provider = ["openrouter", "qwen/qwen-plus"]
# const provider = ["openrouter", "qwen/qwen2.5-32b-instruct"]
# const provider = ["openrouter", "openai/gpt-4o-mini"]
# const provider = ["openrouter", "openai/gpt-4o-mini-search-preview"]
# const provider = ["openrouter", ""]
# const provider = ["openrouter", "qwen/qwq-32b"]
# const provider = ["openrouter", "google/gemma-3-27b-it:free"]
# const provider = ["openai", "o3-mini-high"]
# const provider = ["qwen", "qwen-plus"]

const PROVIDER = $provider.0
const MODEL = $provider.1

const read_files = [
]
const edit_files = [
]
const user_prompt = ""
const user_prompts = []
const system_prompts = [
    "あなたはソフトウェアのエキスパートであり、",
    "特に指定がない限り回答は端的に日本語で行うこと。"
]

def goose_core [
    # --system: string,
    --tools: string,
    ...args
] {
    (
        GOOSE_PROVIDER=$PROVIDER
        GOOSE_MODEL=$MODEL
        RUST_BACKTRACE=1
        goose run
        ...$args
        --with-builtin developer 
        # --with-extension "BRAVE_API_KEY=BSAcvwSt2uAfq9eG9zm4ElbgwPrLlO- pnpx @modelcontextprotocol/server-brave-search"
 
        # goose session --with-builtin "developer,computercontroller"
        # goose session --with-extension "uvx mcp-server-fetch"
        # goose session --with-extension "GITHUB_PERSONAL_ACCESS_TOKEN=<YOUR_TOKEN> npx -y @modelcontextprotocol/server-github"
        # goose configure
   )
}

export def main [
    --act: string,
    --chat,
    --verbose,
    --once,
    ...args
] {
    if $once {
        let text = ($args | str join " ")
        (
            GOOSE_PROVIDER=$PROVIDER
            GOOSE_MODEL=$MODEL
            RUST_BACKTRACE=1
            goose run -t
            $text
        )
    } else if not ($act | is-empty) {
        (
            goose_core 
            # "--no-confirm"
            # "--non-interactive"
            # --system あなたには以下にしたがってコマンドを実行する権限が与えられています (
            #     cat $act | str trim   
            # )
            ...$args
        )
    } else if not ($chat| is-empty) {
        (
            GOOSE_PROVIDER=$PROVIDER
            GOOSE_MODEL=$MODEL
            RUST_BACKTRACE=1
            goose session
            --with-builtin developer
            # --with-extension "BRAVE_API_KEY=BSAcvwSt2uAfq9eG9zm4ElbgwPrLlO- pnpx @modelcontextprotocol/server-brave-search"
            ...$args
        )
    } else {
        let input = (open -r /dev/stdin)
        # print $input
        (
            goose_core 
            "--text"
            $input
        )
    }

    if $verbose {
        print "Verbose mode enabled"
    }
}
