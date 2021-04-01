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

'''

'''

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='/tmp/deep_log.log',
                    filemode='w')

built_function = {
    'datetime': datetime,  # datetime function
    'path': path,  # datetime function
    're': re
}


def gen_default_values(format_string):
    format_keys = [i[1] for i in Formatter().parse(format_string) if i[1] is not None]
    return {one: '' for one in format_keys if one}


class LogParser:
    def parse_file(self, file):
        pass

    def parse(self, lines):
        pass

    def parse_line(self, line):
        pass


class LogFilter:
    def filter(self, one_log_item):
        return True


class LogHandler:
    def handle(self, one_log_item):
        return one_log_item


class DefaultLogParser(LogParser):
    def __init__(self, *args, **kwargs):
        self.pattern = '' if 'pattern' not in kwargs else kwargs['pattern']
        self.log_items = []
        self.strategy = ''

    def parse_file(self, file):
        items = []
        current_item = {}

        while True:
            line = file.readline()
            if not line:
                # flush final results
                if current_item:
                    return [*items, current_item]
                else:
                    return [*items]

            result = self.parse_line(line)
            if result is None:
                # not matched, append to last item, if not found, ignore it
                if not current_item:
                    logging.warning("line %s ignored" % line)
                else:
                    # affinity to last item
                    current_item['raw'] = current_item['raw'] + line
                    current_item['content'] = current_item['content'] + line
                    # current_item.update(get_fileinfo(file.name))
            else:
                # matched pattern
                # flush current item first
                if current_item:
                    items.append(current_item)
                current_item = {'line_number': file.tell(), **result}
                current_item.update({'tags': set()})
                current_item.update(get_fileinfo(file.name))

    def parse_line(self, one_line):
        # {'raw': '', 'content': 'content'}
        # None if not matched
        result = None
        matched_result = re.match(self.pattern, one_line)

        if matched_result is None:
            result = None
        else:
            result = matched_result.groupdict()
            result['raw'] = one_line
            if 'content' not in result:
                result['content'] = one_line

        return result


class DefaultLogFilter(LogFilter):
    def filter(self, one_log_item):
        return True


class DefaultLogHandler(LogHandler):
    def handle(self, one_log_item):
        return one_log_item


class ModuleLogHandler(LogHandler):
    def handle(self, one_log_item):
        return one_log_item


class TypeLogHandler(LogHandler):
    def __init__(self, definitions):
        self.type_definitions = definitions

    def handle(self, one_log_item):
        for one_definition in self.type_definitions:
            type_name = one_definition['type']
            field_name = one_definition['field']
            default_value = None
            if default_value in one_definition:
                default_value = one_definition['default']
            if field_name in one_log_item:
                try:
                    if type_name == 'datetime':
                        time_format = one_definition['format']
                        converted_value = datetime.strptime(one_log_item[field_name], time_format)
                        one_log_item[field_name] = converted_value

                    if type_name == 'int':
                        original_value = one_log_item[field_name]
                        if original_value.isdigit():
                            one_log_item[field_name] = int(original_value)
                        else:
                            one_log_item[field_name] = default_value

                    if type_name == 'float':
                        original_value = one_log_item[field_name]
                        if original_value.isdigit():
                            one_log_item[field_name] = float(original_value)
                        else:
                            one_log_item[field_name] = default_value

                except Exception as e:
                    logging.error("error to transfer {} in {}, use default value {}".format(str(one_log_item),
                                                                                            str(one_definition),
                                                                                            str(default_value)))
                    one_log_item[field_name] = default_value
        return one_log_item


class StripLogHandler(LogHandler):
    def handle(self, one_log_item):
        return {key: (value.strip() if isinstance(value, str) else value) for key, value in one_log_item.items()}


class TransformLogHandler(LogHandler):
    def __init__(self, definitions):
        self.definitions = definitions

    def handle(self, one_log_item):
        new_one_log_item = copy(one_log_item)
        for one_definition in self.definitions:
            name = one_definition.get('name')
            value = one_definition.get('value')
            new_one_log_item[name] = eval(value, one_log_item)

        return new_one_log_item


class TagLogHandler(LogHandler):
    def __init__(self, definitions):
        # {
        #   'name': 'tag_name',
        #   'condition': 'tag_name
        # }
        self.tag_definitions = definitions

    def handle(self, one_log_item):
        tags = one_log_item.get('tags') if 'tags' in one_log_item else set()
        for one_definition in self.tag_definitions:
            name = one_definition.get('name')
            condition = one_definition.get('condition')
            if name in tags:
                # already tagged
                continue
            else:
                try:
                    if eval(condition, {**one_log_item, **built_function}):
                        tags.add(name)
                except Exception as e:
                    logging.error("can not evaluate condition {} on {}".format(condition, str(one_log_item)))

        one_log_item['tags'] = tags
        return one_log_item


class FileNameFilter:
    def __init__(self, filters):
        if filters:
            self.filters = filters.split(',')
        else:
            self.filters = None

    def filter(self, file_name):
        if self.filters:
            for one in self.filters:
                if fnmatch.fnmatch(file_name.lower(), one):
                    return True
            return False
        else:
            return True


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


class FileInfoFilter:
    def __init__(self, file_filter):
        self.file_filter = file_filter

    def get_fileinfo(self, filename):
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

    def filter(self, filename):
        if self.file_filter:
            return eval(self.file_filter, {**self.get_fileinfo(filename), **built_function})
        else:
            return True


class LogHandler:
    pass


class TrieNode:
    def __init__(self, name, children=None, value=None):
        self.name = name
        self.children = children if children else OrderedDict()
        self.value = value

    def is_children(self, name):
        pass

    def upsert_child(self, name):
        if name in self.children:
            return self.children.get(name)
        else:
            new_node = TrieNode(name)
            self.children[name] = new_node
            return new_node

    def get_child(self, name, fuzzy=True):
        if not fuzzy:
            return self.children.get(name)
        else:
            for one in self.children.keys():
                if fnmatch.fnmatch(name, one):
                    return self.children.get(one)

    def set_value(self, value):
        self.value = value

    def get_value(self):
        return self.value


class Trie:
    def __init__(self, root=None):
        self.root = root if root else TrieNode('/')

    def insert(self, name, value):
        current_node = self.root
        path = name.split("/")
        for path_node in path:
            if path_node is None or not path_node.strip():
                continue
            current_node = current_node.upsert_child(path_node)

        current_node.set_value(value)

    def find(self, name, accept=None):
        current_node = self.root
        current_value = current_node.get_value()
        path = name.split("/")
        for path_node in path:
            if path_node is None or not path_node.strip():
                continue
            current_node = current_node.get_child(path_node)
            if current_node is None:
                break
            else:
                node_value = current_node.get_value()
                if node_value is not None:
                    if accept is None:
                        current_value = node_value
                    elif accept(node_value):
                        current_value = node_value
                    else:
                        pass

        return current_value


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


def get_settings(settings_file=None, variables=None, root_parser=None):
    # get settings file
    the_settings_file = None
    if settings_file is not None:
        the_settings_file = settings_file
    else:
        config_dir = path.expanduser("~/.deep_log")
        make_directory(config_dir)  # ensure config file exists

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
    settings.get('variables').update(evaluate_variables(variables, depth=5))

    # update root parser
    if root_parser:
        settings.get('root')['parser'] = {'name': 'DefaultLogParser', 'params': {'pattern': root_parser}}

    # update path
    settings.get("root")['path'] = settings.get("root").get('path').format(**settings.get('variables'))

    # update logger paths
    for one_logger in settings.get('loggers'):
        one_logger['path'] = one_logger.get('path').format(**settings.get('variables'))

    return settings


class DeepLog:
    def __init__(self, settings):
        self.tree = None
        self.settings = settings

        loggers = self.settings.get('loggers')

        # root_node = TrieNode("/", value=None)
        root_node = TrieNode("/", value=self.settings.get('root'))

        self.tree = Trie(root_node)

        for one_logger in loggers:
            if one_logger is None or 'path' not in one_logger:
                logging.warning("config %(key)s ignore, because no path defined" % locals())
            else:
                the_path = one_logger.get('path')
                the_path = the_path.format(**self.settings.get('variables'))
                the_node = TrieNode(the_path, one_logger)
                self.tree.insert(the_path, one_logger)

    def get_all_paths(self, modules=None):
        paths = []
        loggers = self.settings.get('loggers')
        for one_logger in loggers:
            if one_logger is not None and 'path' in one_logger:
                the_path = one_logger.get('path')
                the_path = the_path.format(**self.settings.get('variables'))
                the_modules = set() if one_logger.get('modules') is None else set(one_logger.get('modules'))
                if not modules:
                    # no modules limit
                    paths.append(the_path)
                else:
                    if set(modules) & the_modules:
                        paths.append(the_path)

        return paths

    def get_settings_file(self, custom_settings=None):
        config_dir = path.expanduser("~/.deep_log")
        if custom_settings is None:
            make_directory(config_dir)

            # settings.yaml first
            default_yaml_settings = os.path.join(config_dir, "settings.yaml")
            if os.path.exists(default_yaml_settings):
                return default_yaml_settings

            # settings.json secondly
            default_json_settings = os.path.join(config_dir, "settings.json")

            if os.path.exists(default_json_settings):
                return default_json_settings

            default_settings = {
                "common": {

                },
                "loggers": {
                    "root": {}
                }
            }
            with open(default_json_settings, "w") as f:
                json.dump(default_settings, f)

            return default_json_settings
        else:
            return custom_settings

    def _parse_file(self, fp):
        file_name = fp.name
        node = self.tree.find(file_name, accept=lambda x: 'parser' in x)
        if node is not None and node.get('parser'):
            node_parser = node.get('parser')
            parser_name = node_parser.get('name')
            parser_params = node_parser.get('params') if node_parser.get('params') else {}
            parser = globals()[parser_name](**parser_params)
            return parser.parse_file(fp)
        else:
            return DefaultLogParser().parse_file(fp)

    def _handle_file(self, fp, parsed_results):
        file_name = fp.name
        node = self.tree.find(file_name, accept=lambda x: 'handlers' in x)

        if node is not None and node.get('handlers'):
            node_handlers = node.get('handlers')
            for one_node_handler in node_handlers:
                handler_name = one_node_handler.get('name')
                handler_params = one_node_handler.get('params') if one_node_handler.get('params') else {}
                handler = globals()[handler_name](**handler_params)
                parsed_results = [handler.handle(one) for one in parsed_results]

        return parsed_results

    def _filter_file(self, fp, parsed_results):
        file_name = fp.name
        node = self.tree.find(file_name, accept=lambda x: 'filters' in x)
        if node is not None and node.get('filters'):
            node_filters = node.get('filters')
            for one_node_filters in node_filters:
                filter_name = one_node_filters.get('name')
                filter_params = one_node_filters.get('params') if one_node_filters.get('params') else {}
                filter = globals()[filter_name](**filter_params)
                parsed_results = [one for one in parsed_results if filter.filter(one)]

            return parsed_results
        else:
            return parsed_results

    def mine_file(self, fp):
        parsed_results = self._parse_file(fp)
        parsed_results = self._filter_file(fp, parsed_results)
        parsed_results = self._handle_file(fp, parsed_results)
        return parsed_results

    def mine_files(self, fps):
        for fp in fps:
            file_name = fp.name
            results = self.mine_file(fp)
            if results:
                for one in results:
                    yield {'file_name': file_name, **one}

    def mining_files(self, filename_list):
        fps = []
        for one in filename_list:
            try:
                fp = open(one)
                fps.append(fp)
            except:
                pass

        for fp in fps:
            fp.seek(0, 2)

        while True:
            for one in self.mine_files(fps):
                yield one
            time.sleep(0.1)

    def _filter_one_file(self, file_name):
        node = self.tree.find(file_name, accept=lambda x: 'file_filters' in x)
        if node is None:
            # no filter found
            return True

        node_file_filters = node.get('file_filters')

        if node_file_filters is None:
            return True

        for one_node_file_filter in node_file_filters:
            file_filter_name = one_node_file_filter.get('name')
            file_filter_params = one_node_file_filter.get('params')
            filter = globals()[file_filter_name](**file_filter_params)
            if not filter(file_name):
                return False

        return True

    def normalize_path(self, dir):
        dir = path.expanduser(dir)
        dir = path.expandvars(dir)
        dir = path.abspath(dir)
        return glob.glob(dir)

    def mining(self, target_dirs, file_filters=None, pre_content_filters=None, root_parser=None, subscribe=False):
        full_paths = []

        dirs = []
        for one_target_dir in target_dirs:
            dirs.extend(self.normalize_path(one_target_dir))

        for folder in dirs:

            if path.isfile(folder):
                full_paths.append(folder)
                continue

            for root, dirs, files in os.walk(folder):
                for file in files:
                    full_paths.append(os.path.join(root, file))

        if file_filters:
            for one_file_filter in file_filters:
                full_paths = [one for one in full_paths if one_file_filter.filter(one)]

        # for internal file filter
        full_paths = [one for one in full_paths if self._filter_one_file(one)]

        if subscribe:
            for one in self.mining_files(full_paths):
                yield one
        else:
            opened_file_list = []
            for one in full_paths:
                try:
                    fp = open(one)
                    opened_file_list.append(fp)
                except:
                    pass

            for one in self.mine_files(opened_file_list):
                yield one


def make_directory(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)


def build_recent_file_filter(recent):
    file_filter_template = 'mtime.timestamp() - {} > 0'
    if recent is None:
        # no fitler
        return FileInfoFilter(None)

    recent_seconds = 0
    if recent.isdigit():
        # seconds by default
        recent_seconds = int(recent)
    elif recent.lower().endswith('s'):
        recent_seconds = int(recent[:-1])
    elif recent.lower().endswith('m'):
        recent_seconds = int(recent[:-1]) * 60
    elif recent.lower().endswith('h'):
        recent_seconds = int(recent[:-1]) * 60 * 60
    elif recent.lower().endswith('d'):
        recent_seconds = int(recent[:-1]) * 60 * 60 * 24
    else:
        raise Exception("unsupported recent format {}".format(recent))

    start_time = datetime.now().timestamp() - recent_seconds
    return FileInfoFilter(file_filter_template.format(start_time))


def build_recent_filter(recent):
    file_filter_template = 'time.timestamp() - {} > 0'
    if recent is None:
        # no fitler
        return FileInfoFilter(None)

    recent_seconds = 0
    if recent.isdigit():
        # seconds by default
        recent_seconds = int(recent)
    elif recent.lower().endswith('s'):
        recent_seconds = int(recent[:-1])
    elif recent.lower().endswith('m'):
        recent_seconds = int(recent[:-1]) * 60
    elif recent.lower().endswith('h'):
        recent_seconds = int(recent[:-1]) * 60 * 60
    elif recent.lower().endswith('d'):
        recent_seconds = int(recent[:-1]) * 60 * 60 * 24
    else:
        raise Exception("unsupported recent format {}".format(recent))

    start_time = datetime.now().timestamp() - recent_seconds
    return file_filter_template.format(start_time)


def build_tags_filter(tags):
    target_tags = set(tags.split(','))
    return 'tags & {}'.format(str(target_tags))


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
    parser.add_argument('-D', action='append', dest='variables', help='definitions')
    parser.add_argument('dirs', metavar='N', nargs='*', help='log dirs to analyze')

    args = parser.parse_args()

    variables = {}
    if args.variables:
        variables = {one.split('=')[0]: one.split('=')[1] for one in args.variables}

    # log_miner = DeepLog(args.file, variables)
    log_miner = DeepLog(get_settings(args.file, variables, args.parser))
    format = "{raw}" if not args.format else args.format
    default_value = gen_default_values(format)

    items = []

    count = 0

    # build file builders
    file_filters = []
    if args.file_name:
        file_filters.append(FileNameFilter(args.file_name))

    if args.file_filter:
        file_filters.append(FileInfoFilter(args.file_filter))

    if args.recent:
        file_filters.append(build_recent_file_filter(args.recent))

    post_filters = []
    if args.filter:
        post_filters.append(args.filter)

    if args.recent:
        post_filters.append(build_recent_filter(args.recent))

    if args.tags:
        post_filters.append(build_tags_filter(args.tags))

    the_dirs = args.dirs
    if not the_dirs:
        modules = None
        if args.modules:
            modules = set(args.modules.split(','))
        the_dirs = log_miner.get_all_paths(modules)

    for item in log_miner.mining(the_dirs, file_filters=file_filters, pre_content_filters=[],
                                 root_parser=args.parser, subscribe=args.subscribe):

        for one_post_filters in post_filters:
            if not eval(one_post_filters, {**built_function, **item}):
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
        print(result)


if __name__ == '__main__':
    main()
