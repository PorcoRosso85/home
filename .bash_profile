#!/bin/bash

bashrc() {
  BASHRC=$HOME/.bashrc
  if [ -e $BASHRC ]
    then source $BASHRC
  fi
}
bashrc

common_profile() {
  COMMON_PROFILE=$HOME/.common_profile
  if [ -e $COMMON_PROFILE ]
    then source $COMMON_PROFILE
  fi
}
common_profile

export DVM_DIR="/root/.dvm"
export PATH="$DVM_DIR/bin:$PATH"