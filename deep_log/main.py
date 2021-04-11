#!/usr/bin/env python
import argparse
import fnmatch
import functools
import json
import logging
import os
import re
import time
from collections import OrderedDict
import glob
# back pressure
# https://pyformat.info/
from copy import copy
from datetime import datetime
from os import path
from string import Formatter

from deep_log import utils, factory
from deep_log.miner import DeepLogMiner
from deep_log.file_filter import NameFileFilter, DslFileFilter
from deep_log.utils import built_function

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='/tmp/deep_log.log',
                    filemode='w')


def gen_default_values(format_string):
    format_keys = [i[1] for i in Formatter().parse(format_string) if i[1] is not None]
    return {one: '' for one in format_keys if one}





def get_settings(settings_file=None, variables=None, root_parser=None):
    # get settings file
    the_settings_file = None
    if settings_file is not None:
        the_settings_file = settings_file
    else:
        config_dir = path.expanduser("~/.deep_log")
        utils.make_directory(config_dir)  # ensure config file exists

        # settings.yaml first
        default_yaml_settings = os.path.join(config_dir, "settings.yaml")
        if os.path.exists(default_yaml_settings):
            the_settings_file = default_yaml_settings
        else:
            # settings.json secondly
            default_json_settings = os.path.join(config_dir, "settings.json")

            if os.path.exists(default_json_settings):
                the_settings_file = default_json_settings
            else:
                default_settings = {
                    "common": {},
                    "variables": {},
                    "root": {
                        "path": "/"
                    },
                    "loggers": []
                }
                with open(default_json_settings, "w") as f:
                    json.dump(default_settings, f)

                the_settings_file = default_json_settings

    # populate settings
    settings = None
    if the_settings_file.endswith('yaml'):
        import yaml
        with open(the_settings_file) as f:
            settings = yaml.safe_load(f)
    else:
        with open(the_settings_file) as f:
            settings = json.load(f)
    if variables:
        settings.get('variables').update(variables)

    # populate variables
    settings.get('variables').update(utils.evaluate_variables(variables, depth=5))

    # update root parser
    if root_parser:
        settings.get('root')['parser'] = {'name': 'DefaultLogParser', 'params': {'pattern': root_parser}}

    # update path
    settings.get("root")['path'] = settings.get("root").get('path').format(**settings.get('variables'))

    # update logger paths
    for one_logger in settings.get('loggers'):
        one_logger['path'] = one_logger.get('path').format(**settings.get('variables'))

    return settings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', help='config file')
    parser.add_argument('-l', '--filter', help='log filter')
    parser.add_argument('-p', '--parser', help='root parser')
    parser.add_argument('-t', '--file-filter', help='file filters')
    parser.add_argument('-n', '--file-name', help='file name filters')
    parser.add_argument('-u', '--layout', help='return layout ')
    parser.add_argument('-m', '--format', help='print format')
    parser.add_argument('-s', '--subscribe', action='store_true', help='subscribe mode')
    parser.add_argument('-o', '--order-by', help='field to order by')
    parser.add_argument('-r', '--reverse', action='store_true', help='reverse order, only work with order by')
    parser.add_argument('--limit', type=int, help='limit query count')
    parser.add_argument('--recent', help='query to recent time')
    parser.add_argument('-y', '--analyze', help='analyze')
    parser.add_argument('--tags', help='query by tags')
    parser.add_argument('--modules', help='query by tags')
    parser.add_argument('--full', action='store_true', help='display full')
    parser.add_argument('-D', action='append', dest='variables', help='definitions')
    parser.add_argument('dirs', metavar='N', nargs='*', help='log dirs to analyze')

    args = parser.parse_args()

    variables = {}
    if args.variables:
        variables = {one.split('=')[0]: one.split('=')[1] for one in args.variables}

    # log_miner = DeepLog(args.file, variables)
    log_miner = DeepLogMiner(get_settings(args.file, variables, args.parser))

    format = "{raw}" if not args.format else args.format
    default_value = gen_default_values(format)

    items = []

    count = 0

    # build file builders
    file_filters = []
    if args.file_name:
        file_filters.append(NameFileFilter(args.file_name))

    if args.file_filter:
        file_filters.append(DslFileFilter(args.file_filter))

    if args.recent:
        file_filters.append(factory.FileFilterFactory.create_recent_filter(args.recent))

    file_content_filters = []
    if args.filter:
        file_content_filters.append(factory.FilterFactory.create_dsl_filter(args.filter))

    if args.recent:
        file_content_filters.append(factory.FilterFactory.create_recent_dsl(args.recent))

    if args.tags:
        file_content_filters.append(factory.FilterFactory.create_tags_filter(args.tags))

    the_dirs = args.dirs
    if not the_dirs:
        modules = None
        if args.modules:
            modules = set(args.modules.split(','))
        the_dirs = log_miner.get_all_paths(modules)

    for item in log_miner.mining(the_dirs, file_filters=file_filters, pre_content_filters=[],
                                 root_parser=args.parser, subscribe=args.subscribe):

        for one_post_filters in file_content_filters:
            if not one_post_filters.filter({**built_function, **item}):
                # not passed
                break
        else:
            if not args.order_by and not args.analyze:
                # not order by mode, print out immediately
                if default_value:
                    print(format.format(**{**default_value, **item}))
                else:
                    print(format.format(str(item)))
            else:
                # only for order by
                items.append(item)

            count = count + 1
            if args.limit is not None and count >= args.limit:
                break

    if args.order_by:
        # order by mode, need shuffle in memory
        items.sort(key=lambda x: x.get(args.order_by), reverse=args.reverse)

        for one in items:
            if default_value:
                print(format.format(**{**default_value, **one}))
            else:
                print(format.format(str(one)))

    elif args.analyze:
        import pandas as pd
        data = pd.DataFrame(items)
        result = eval(args.analyze, {'data': data})
        if args.full:
            pd.set_option('display.max_colwidth', None)
            pd.set_option('display.max_rows', None)
        print(result)


if __name__ == '__main__':
    main()
