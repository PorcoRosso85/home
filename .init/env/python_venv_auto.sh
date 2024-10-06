cd() {

  builtin cd "$@"

  function activate_venv() {
          if [[ $(ls -a -U1 .venv/ |wc -l) < 1 ]]; then #.venvディレクトリ下に仮想環境なし
                echo "There is no virtual env"
          elif [[ $(ls -a -U1 .venv/ |wc -l) > 1 ]]; then #.venv直下に仮想環境が複数ある
                echo "There are over 2 venv dirs"
                echo "Please activate venv manually"
          else #.venvディレクトリが１つある時
                 source .venv/$(ls .venv/)/bin/activate
          fi
  }


  if [ -z "$VIRTUAL_ENV" ]; then
          if [ -d .venv ]; then
                activate_venv
          fi

  elif [[ $(pwd) != $(dirname $(dirname "$VIRTUAL_ENV"))/* ]] ; then
          deactivate

          if [ -d .venv ]; then
                activate_venv
          fi
  fi

}
