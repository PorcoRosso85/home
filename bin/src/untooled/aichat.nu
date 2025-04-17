#!/usr/bin/env -S nix shell nixpkgs#aichat nixpkgs#nushell --command nu

# const provider = ["gemini", "gemini-2.0-pro-exp-02-05"]
const provider = ["gemini", "gemini-2.0-flash"]
# const provider = ["gemini", "gemini-2.0-flash-thinking-exp-01-21"]
# const provider = ["github", "deepSeek-r1"]
# const provider = ["openrouter", "google/gemini-2.0-pro-exp-02-05:free"]
# const provider = ["openrouter", "google/gemini-2.0-flash-thinking-exp:free"]
# const provider = ["openrouter", "google/gemini-2.0-flash-lite-preview-02-05:free"]
# const provider = ["openrouter", "deepseek/deepseek-r1:free"]
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
const MODEL = $"($provider.0):($provider.1)"


# editable
# TODO もしパイプされていたらパイプによるstdinをaichatに渡す
# eg 'echo stdin | ./src/aichat.nu arg1 arg2'

const read_files = [
# ../mitchell/
]
const edit_files = []
const user_prompt = ""
const user_prompts = []
const system_prompts = [
"あなたはソフトウェアのエキスパートであり、",
"特に指定がない限り回答は端的に日本語で行うこと。"
]

def aichat_core [...args] {
    let read_options = ($read_files | each { |file| ["--file", $file] } | flatten)
    let edit_options = ($edit_files | each { |file| ["--file", $file] } | flatten)
    let model_option = ["--model", $MODEL]
    let system_prompt = ["--prompt", ($system_prompts | str join " ")]
    (
        AICHAT_PLATFORM=$PROVIDER aichat
        ...$model_option
        ...$system_prompt
        ...$read_options
        ...$edit_options
        ...$args
    )
}

export def main [
    --rag
    --repl
    --verbose
    ...args
] {
    if $rag {
        (
            aichat_core
            "--rag"
            ...$args
        )
    } else if $repl {
        let model_option = ["--model", $MODEL]
        (
            AICHAT_PLATFORM=$PROVIDER aichat
            ...$model_option
        )
    } else {
        (
            aichat_core
            ...$args
        )
    }

    if $verbose {
        print "Verbose mode enabled"
    }
}
