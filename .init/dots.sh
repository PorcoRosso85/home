#!/bin/bash

set -e

DOTS=".dots"
DOTS_DIR="$HOME/$DOTS"
GIT_EXECUTABLE="/usr/bin/git"
RC_PATH="$HOME/.bashrc"
REMOTE_REPO_URL="https://github.com/PorcoRosso85/dots.git"

dots_alias() {
  $GIT_EXECUTABLE --git-dir=$DOTS_DIR --work-tree=$HOME "$@"
}

add_alias_to_rc() {
  # Remove if alias exists using dots_alias config
  dots_alias config --unset alias.dots 2>/dev/null || true
  # Add the new alias
  dots_alias config alias.dots 'dots_alias'
}

OVERRIDE_DIRS=("$HOME/.config" "$HOME/.init")
FORCE_OVERRIDE=true

handle_files_before_checkout() {
  FILES_TO_CHECKOUT=$(dots_alias ls-tree -r HEAD --name-only)
  for file in $FILES_TO_CHECKOUT; do
    if [[ -e "$HOME/$file" && ( " ${OVERRIDE_DIRS[@]} " =~ " $HOME/$file " || "$FORCE_OVERRIDE" == true ) ]]; then
      rm -rf "$HOME/$file"
    fi
  done
}

handle_checkout_errors() {
  CHECKOUT_ERROR=$(dots_alias checkout 2>&1 || true)
  if [[ $CHECKOUT_ERROR == *"would be overwritten by checkout"* ]]; then
    echo "$CHECKOUT_ERROR" | grep "would be overwritten by checkout:" -A1000 | tail -n +2 | grep -v "Aborting" | while read -r conflicted_file; do
      conflicted_file=$(echo "$conflicted_file" | sed 's/^[ \t]*//;s/:$//')
      if [[ " ${OVERRIDE_DIRS[@]} " =~ " $HOME/$conflicted_file " || "$FORCE_OVERRIDE" == true ]]; then
        echo "Overriding $HOME/$conflicted_file"
        rm -rf "$HOME/$conflicted_file"
      else
        echo "Cannot handle conflict for $HOME/$conflicted_file automatically. Please address this manually."
      fi
    done
    dots_alias checkout
  fi
}

push_new() {
  if [[ -d "$DOTS_DIR" ]]; then
    echo "$DOTS directory already exists. Skipping setup."
    return 1
  fi

  trap rollback ERR

  echo "Setting up $DOTS directory..."
  $GIT_EXECUTABLE init --bare "$DOTS_DIR"
  add_alias_to_rc
  dots_alias config --local status.showUntrackedFiles no
  echo "$DOTS directory has been set up."
  echo "Please restart your terminal or run 'source $RC_PATH' to use the 'dots' alias."

  dots_alias add .vimrc
  dots_alias commit -m "Add vimrc"
  dots_alias add .bashrc
  dots_alias commit -m "Add bashrc"
  dots_alias remote add origin "$REMOTE_REPO_URL"
  # Fetch to determine the default branch
  dots_alias fetch
  DEFAULT_BRANCH=$(dots_alias branch -r | sed -n '/\* /s///p')
  dots_alias push -u origin "$DEFAULT_BRANCH"

  trap - ERR
}

pull_existed() {
  if [[ -d "$DOTS_DIR" ]]; then
    echo "$DOTS directory already exists. Removing it..."
    rm -rf "$DOTS_DIR"
  fi

  echo "Cloning $DOTS directory..."
  $GIT_EXECUTABLE clone --bare "$REMOTE_REPO_URL" "$DOTS_DIR"
  echo "$DOTS" >> "$HOME/.gitignore"
  add_alias_to_rc

  handle_files_before_checkout

  # handle_checkout_errors関数を呼び出す
  handle_checkout_errors
  
  source "$RC_PATH"
  echo "$DOTS directory has been cloned and set up."
}

push_updated() {
  if [[ ! -d "$DOTS_DIR" ]]; then
    echo "$DOTS directory does not exist. Please set it up first."
    return 1
  fi

  echo "Updating $DOTS directory..."
  echo $dots_alias
  dots_alias add -A
  echo "Enter a commit message: "
  dots_alias commit -m "Update dotfiles"
  # Fetch to determine the default branch
  echo "Pushing changes to remote..."
  dots_alias fetch
  DEFAULT_BRANCH=$(dots_alias branch -r | sed -n '/\* /s///p')
  dots_alias push origin "$DEFAULT_BRANCH"
  echo "$DOTS directory has been updated."
}

main() {
  while true; do
    echo "WARNING: Before running this script, ensure you trust its source."
    echo "Choose an action:"
    echo "1. Set up a new $DOTS directory (push_new)"
    echo "2. Clone an existing $DOTS directory (pull_dots)"
    echo "3. Update an existing $DOTS directory (push_updated)"
    echo "Enter the number corresponding to your choice: "
    read choice

    case "$choice" in
      1)
        push_new
        break
        ;;
      2)
        pull_dots
        break
        ;;
      3)
        push_updated
        break
        ;;
      *)
        echo "Invalid choice. Please try again..."
        ;;
    esac
  done
}

main
