# bin/src

このディレクトリは開発環境に必要なすべてのツールを用意します

## Flakeの責務

このflakeは、src配下の各ディレクトリの責務分離を監視する役割を持つ。各サブディレクトリが単一責務原則に従い、明確に分離された機能を維持していることを保証する。

## Dir

```log
.
├── doc
│   ├── content
│   ├── public
│   ├── ref
│   ├── sass
│   ├── static
│   └── templates
├── google
├── src
│   ├── aichat_extension
│   ├── deprecated
│   ├── go_cozo
│   ├── lean
│   ├── python_cozo
│   ├── verso
│   └── zig
└── tasks

```

## Argc

このディレクトリで `argc build` が可能になっています（Argcfile）。
このコマンドにより ./toolsおよび ./tools.txtに従ってMCPに呼び出されるツールがビルドされます。

### 1. Clone the repository

```sh
git clone https://github.com/sigoden/llm-functions
cd llm-functions
```

### 2. Build tools and agents

#### I. Create a `./tools.txt` file with each tool filename on a new line.

```
get_current_weather.sh
execute_command.sh
#execute_py_code.py
``` 

<details>
<summary>Where is the web_search tool?</summary>
<br>

The `web_search` tool itself doesn't exist directly, Instead, you can choose from a variety of web search tools.

To use one as the `web_search` tool, follow these steps:

1. **Choose a Tool:** Available tools include:
    * `web_search_cohere.sh`
    * `web_search_perplexity.sh`
    * `web_search_tavily.sh`
    * `web_search_vertexai.sh`

2. **Link Your Choice:** Use the `argc` command to link your chosen tool as `web_search`. For example, to use `web_search_perplexity.sh`:

    ```sh
    $ argc link-web-search web_search_perplexity.sh
    ```

    This command creates a symbolic link, making `web_search.sh` point to your selected `web_search_perplexity.sh` tool. 

Now there is a `web_search.sh` ready to be added to your `./tools.txt`.

</details>

#### II. Create a `./agents.txt` file with each agent name on a new line.

```
coder
todo
```

#### III. Build `bin` and `functions.json`

```sh
argc build
```

#### IV. Ensure that everything is ready (environment variables, Node/Python dependencies, mcp-bridge server)

```sh
argc check
```

### 3. Link LLM-functions and AIChat

AIChat expects LLM-functions to be placed in AIChat's **functions_dir** so that AIChat can use the tools and agents that LLM-functions provides.

You can symlink this repository directory to AIChat's **functions_dir** with:

```sh
ln -s "$(pwd)" "$(aichat --info | sed -n 's/^functions_dir\s\+//p')"
# OR
argc link-to-aichat
```

Alternatively, you can tell AIChat where the LLM-functions directory is by using an environment variable:

```sh
export AICHAT_FUNCTIONS_DIR="$(pwd)"
```

### 4. Start using the functions

Done! Now you can use the tools and agents with AIChat.

```sh
aichat --role %functions% what is the weather in Paris?
aichat --agent todo list all my todos
```
