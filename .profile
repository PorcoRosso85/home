# TODO このファイルはnixにより生成させるべき。ただし'home.file'機能の文字列として同様の記述が不可能な個所をエスケープなど解決したい
# .profile の役割
# - ログイン起動時のみ
# - システム全体のシェル環境を設定
# - PATH、環境変数、その他システム全体の設定をします
# ==================================================
source $HOME/_.profile # home-managerを読み込み

# if running bash
if [ -n "$BASH_VERSION" ]; then
    # include .bashrc if it exists
    if [ -f "$HOME/.bashrc" ]; then
	. "$HOME/.bashrc"
    fi
fi

# set PATH so it includes user's private bin if it exists
if [ -d "$HOME/bin" ] ; then
    PATH="$HOME/bin:$PATH"
fi

# set PATH so it includes user's private bin if it exists
if [ -d "$HOME/.local/bin" ] ; then
    PATH="$HOME/.local/bin:$PATH"
fi
