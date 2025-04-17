#!/usr/bin/env -S nix shell nixpkgs#uv nixpkgs#nushell --command nu

# const THINK = "openrouter/anthropic/claude-3.7-sonnet:thinking"
# const THINK = "openrouter/qwen/qwq-32b:free"
# const THINK = "openrouter/qwen/qwen-plus"
# const THINK = "openrouter/qwen/qwen2.5-32b-instruct"
# const THINK = "deepseek/deepseek-reasoner"
# const THINK = "deepseek/deepseek-chat"
# const THINK = "openrouter/perplexity/r1-1776"
# const THINK = "openrouter/google/gemini-2.0-pro-exp-02-05:free"
# const THINK = "gemini/gemini-2.0-pro-exp-02-05"
const THINK = "gemini/gemini-2.0-flash-thinking-exp-01-21"
# const THINK = "openrouter/openai/o3-mini-high"
# const CODE = "openrouter/google/gemini-2.0-flash-001"
# const CODE = "openrouter/google/gemini-2.0-pro-exp-02-05:free"
# const CODE = "gemini/gemini-2.0-pro-exp-02-05"
# const CODE = "openrouter/openai/gpt-4o-mini"
# const THINK = "gemini/gemini-2.0-pro-exp-02-05"
# const CODE = "gemini/gemini-2.0-pro-exp-02-05"
const CODE = "deepseek/deepseek-coder"

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

def gptme_core [
    # --system: string,
    --tools: string,
    ...args
] {
    (
        uvx gptme
            --model $THINK
            # --system $system
            ...$args
    )
}

export def main [
    --eg: string,
    --test: string,
    --plan,
    --act: string,
    --upsert: string,
    --verbose,
    ...args
] {
    # let input = (open -r /dev/stdin)
    # print $input
    if not ($eg | is-empty) {
        echo $"eg用の引数: ($eg)"
#         let fixed_prompt = "
# 'read <url>' '-' 'create a branch' '-' 'look up relevant files' '-' 'make changes' '-' 'typecheck it' '-' 'test it' '-' 'create a pull request'   
# "
        gptme_core ...$args


    } else if not ($test | is-empty) {
        let fixed_prompt = "
./src/infrastructure/logger.py の
テストを追加で作成すること
どんなテストを追加するかは自ら判断すること
テストを追加したのちpytestでテストを実行すること
テストがすべて通るまで変更を繰り返すこと
一度作成したテストは変更しないこと
テストは実装ファイル内に作成すること
別のテストファイルを作成することはしないこと
ファイルへの書き込みエラーが発生してもリトライすること
"
        (
            gptme_core ...[$fixed_prompt, ...$args]
        )
    } else if $plan {
        (
            gptme_core 
            # --system あなたには以下にしたがってファイルを作成する権限が与えられています (
            #     cat /home/nixos/scripts/tasks/init.md | str trim   
            # )
            ...$args
        )
    } else if not ($act | is-empty) {
        (
            gptme_core 
            # "--no-confirm"
            # "--non-interactive"
            # --system あなたには以下にしたがってコマンドを実行する権限が与えられています (
            #     cat $act | str trim   
            # )
            ...$args
        )
    } else if not ($upsert | is-empty) {
        print $upsert
        (
            gptme_core 
            # "--no-confirm"
            "--non-interactive"
            ...$args
        )
    } else {
        # TODO 文字列として扱いたい
        # let prefix = $input
        (
            gptme_core 
            # ...[$prefix, ...$args]
            ...$args
        )
    }

    if $verbose {
        print "Verbose mode enabled"
    }
}
