# chmod() {
#   local extension_path=$HOME"/.extension"
# #   chmod +x extension_path/.
# #   chmod +x $(find $extension_path -maxdepth 2 | grep .sh)
#   chmod $extension_path/*
#  }
#  chmod

# [alias]
alias ls='ls -la'

alias sobash="source ~/.bashrc"
#[ -f ~/.fzf.bash ] && source ~/.fzf.bash
#
alias g='git'
alias dots='/usr/bin/git --git-dir=/root/.dotfiles/ --work-tree=/root'

#alias cdf='cd $(find . -maxdepth 3 -type d | fzf)'
alias cdfm='cd $(find /mnt/c/Users/admin.DESKTOP-1PF4AT3/ -maxdepth 3 -type d | grep "Documents\|Downloads\|wsl" | fzf)'
alias catf='cat $(find . -maxdepth 4 | fzf)'
#alias catff='cat $(find . -maxdepth 4 | fzf)'
#

alias pip='python3.11 -m pip'


# [alias/nvim]
#alias nvim='nvim'
#alias nvim_markdown='nvim -u ~/.config/nvim/lua_markdown.lua'

# [alias/docker]
alias dcir='docker image rm'
alias dccl='docker container ls -a'
alias dccr='docker container rm'
alias dcsp='docker system purge'
alias dce='docker exec'

alias dockerdrawio='docker run -it --rm --name="draw" -p 8080:8080 -p 8443:8443 jgraph/drawio'
alias dockeransible="docker run -ti --rm -v ~/.ssh:/root/.ssh -v ~/.aws:/root/.aws -v $(pwd):/apps -w /apps alpine/ansible ansible"

# [function]
glp() {
  preview="git diff $@ --color=always -- {-1}"
  git diff $@ --name-only | fzf -m --ansi --preview $preview
}

# [Fzf]
export FZF_DEFAULT_COMMAND="find . -printf '%Tm/%Td %TH:%TM %p\n'"
export FZF_DEFAULT_OPTS="--layout=reverse --height 40%"
FZF_CTRL_T_COMMAND="find . -maxdepth 3"
FZF_CTRL_R_OPTS="--reverse --height 25%"

fgf() { 
  find $1 | grep $2 | fzf
}

fw() {
 find . -type f | grep $1 | xargs grep -n -E -w "$2" | fzf
}

mkcd() {
  if ! [ -d $1 ]; then
    mkdir $1
    echo "made dir" $1
  fi
  cd $1
}

plewcm() {
  cat $1 | fzf
  g cm -
}

jqjc() {
  # https://richrose.dev/posts/linux/jq/jq-json2csv/
  jq -r '.stock[] | [.id, .item, .description] | @csv' $1
}

jqjm() {
  # https://gist.github.com/mrVanboy/4472ead613102b382691b3b28ae03ae4
  jq -r '. | sort_by((.location.path | explode | map(-.)), .location.lines.begin) | .[] | @text "| [\(.location.path):\(.location.lines.begin)](../blob/BRANCH-NAME/\(.location.path)#L\(.location.lines.begin)) | \(.description)"' gl-code-quality-report.json
}

jqcj() {
  # https://qiita.com/mj69/items/80a3a18210a4fa28ff44
  # https://rafaelleru.github.io/blog/json-magic-vim/
  jq -R -s -f $1 $2 |jq 'del(.[][] | nulls)'\
  |head -n -2 | sed -e 1d -e 's/},/}/g' | jq . -c|\
  sed "s/^/{ \"index\" :{} }\n/g" > $3
  #echo $(jq '.' $3) > $3
  # $1:mapping file, $2:target csv
}

gloj() {
  # https://scrapbox.io/nwtgck/git%E6%A8%99%E6%BA%96%E3%81%A0%E3%81%91%E3%81%A7%E3%80%81log%E3%81%AE%E6%83%85%E5%A0%B1%E3%82%92JSON%E3%81%AB%E3%81%97%E3%81%A6%E5%8F%96%E5%BE%97%E3%81%99%E3%82%8B%E6%96%B9%E6%B3%95
   git log --pretty=format:'{%n  "commit": "%H",%n  "abbreviated_commit": "%h",%n  "tree": "%T",%n  "abbreviated_tree": "%t",%n  "parent": "%P",%n  "abbreviated_parent": "%p",%n  "refs": "%D",%n  "encoding": "%e",%n  "subject": "%s",%n  "sanitized_subject_line": "%f",%n  "body": "%b",%n  "commit_notes": "%N",%n  "verification_flag": "%G?",%n  "signer": "%GS",%n  "signer_key": "%GK",%n  "author": {%n    "name": "%aN",%n    "email": "%aE",%n    "date": "%aD"%n  },%n  "commiter": {%n    "name": "%cN",%n    "email": "%cE",%n    "date": "%cD"%n  }%n},'
  # https://gist.github.com/varemenos/e95c2e098e657c7688fd
}

# [path]
#export PATH=$PATH:~/.rustup/toolchains/stable-x86_64-unknown-linux-gnu/bin:~/.bashrcs

# [apps]
export EDITOR=nvim

# [theme]
# call ohmybash
# ./.bashrcs/ohmybash.sh
#

# [external]
#while read -r f;
#do
#  chmod +x $f
#  external_bashrcs=$f
#done < <(find ~/.bashrcs -mindepth 1 -maxdepth 1)
#
#for bashrc in ${external_bashrcs[@]}
#do
#  if [ -f "$bashrc" ]
#  then
#    source "$bashrc"
#    echo "Loaded external_bashrcs"
#  else
#    echo "File not found...in: $bashrc"
#  fi
#done
