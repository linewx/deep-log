#!/usr/bin/env bash

# https://stackoverflow.com/questions/2087148/can-i-use-pip-instead-of-easy-install-for-python-setup-py-install-dependen
#rm -fr ./build

pip uninstall -y deep-log

pip install .