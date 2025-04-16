#!/usr/bin/env -S nix shell nixpkgs#uv nixpkgs#nushell --command nu

# TODO 環境変数, ただ上記のshebangなら不要かも, 環境変数知ってるbashから起動するので
# use ~/secret.nu

# const THINK = "deepseek/deepseek-reasoner"
const THINK = "deepseek/deepseek-chat"
const CODE = "deepseek/deepseek-coder"
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

const read_files = [
]
const edit_files = [
# ./exit.nu
./aider.nu
]
const user_prompt = ""
const user_prompts = []
const system_prompts = [
    "あなたはソフトウェアのエキスパートであり、",
    "特に指定がない限り回答は端的に日本語で行うこと。"
]

export-env {
    load-env {
        LD_LIBRARY_PATH: ([
            "/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib",
            "/nix/store/v2ny69wp81ch6k4bxmp4lnhh77r0n4h1-zlib-1.3.1/lib",
            # $env.LD_LIBRARY_PATH # TODO 既存の値がないから新規としている
        ] | str join ":")
    }
}

# let aider_test_command = $test_command

def aider_core [...args] {
    let read_options = ($read_files | each { |file| ["--read", $file] } | flatten)
    let edit_options = ($edit_files | each { |file| ["--file", $file] } | flatten)
    print "run aider"
    print $"THINK: ($THINK), CODE: ($CODE)"

    (
        uvx --from aider-chat aider
        ...$read_options
        ...$edit_options
        --model $THINK
        --editor-model $CODE
        --editor-edit-format diff
        --no-show-model-warnings
        --no-attribute-author
        --dark-mode
        ...$args
    )
}

export def main [
    --watch,
    --edit,
    --verbose,
    ...args
] {
    print $args
    if $watch {
        (
            aider_core
            "--watch-files"
            "--architect"
            # ...$args
       )
    } else if $edit {
        (
            # TODO https://aider.chat/docs/scripting.html
            # FILEパスを最後に入れると編集対象を指定可能
            # ->
            # aider --message "get_prompt($FILE)" $FILE
            aider_core
            "--message"
            $args.0
            $args.1
        )
    } else {
        (
            aider_core
            "--message"
            ($args | str join " ")
        )
    }

    if $verbose {
        print "Verbose mode enabled"
    }
}
