#!/bin/bash
# Install python 3.12.2
# We don't activate after installing since this is not required by default
# python 3.12.3 will be installed in $HOME/.pyenv/versions/3.12.2/bin
curl https://pyenv.run | bash
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
pyenv install 3.12.2
pyenv doctor
