import functools
import glob
import os
import re
import datetime
from os import path
from string import Formatter

built_function = {
    'datetime': datetime,  # datetime function
    'path': path,  # datetime function
    're': re
}


def evaluate_variable(variable, variables, depth=5):
    result = variable
    for index in range(depth):
        if '{' in result and '}' in result:
            result = result.format(**variables)

    return result


def evaluate_variables(variables, depth=5):
    results = {}
    for key, value in variables.items():
        results[key] = evaluate_variable(key, variables, depth)

    return results


def make_directory(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)


def normalize_path(dir, with_wildcard=False):
    dir = path.expanduser(dir)
    dir = path.expandvars(dir)
    dir = path.abspath(dir)

    if with_wildcard:
        return glob.glob(dir)
    else:
        return dir


@functools.lru_cache(maxsize=256, typed=True)
def get_fileinfo(filename):
    if os.path.exists(filename):
        return {
            '_name': filename,
            '_writable': os.access(filename, os.W_OK),
            '_readable': os.access(filename, os.R_OK),
            '_executable': os.access(filename, os.X_OK),
            '_ctime': datetime.datetime.fromtimestamp(path.getctime(filename)),
            '_mtime': datetime.datetime.fromtimestamp(path.getmtime(filename)),
            '_actime': datetime.datetime.fromtimestamp(path.getatime(filename)),
            '_size': path.getsize(filename),
            '_basename': path.basename(filename),
            '_isdir': path.isdir(filename),
            '_isfile': path.isfile(filename),
            '_exists': True,
        }

    else:
        return {
            '_name': filename,
            '_exists': False
        }
