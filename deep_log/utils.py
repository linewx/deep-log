import functools
import os
import re
from datetime import datetime
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


@functools.lru_cache(maxsize=256, typed=True)
def get_fileinfo(filename):
    if os.path.exists(filename):
        return {
            'name': filename,
            'writable': os.access(filename, os.W_OK),
            'readable': os.access(filename, os.R_OK),
            'executable': os.access(filename, os.X_OK),
            'ctime': datetime.fromtimestamp(path.getctime(filename)),
            'mtime': datetime.fromtimestamp(path.getmtime(filename)),
            'actime': datetime.fromtimestamp(path.getatime(filename)),
            'size': path.getsize(filename),
            'basename': path.basename(filename),
            'isdir': path.isdir(filename),
            'isfile': path.isfile(filename),
            'exists': True,
        }

    else:
        return {
            'name': filename,
            'exists': False
        }



