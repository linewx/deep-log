#!/usr/bin/env python
import argparse
import fnmatch
import json
import logging
import os
import re
import time
from collections import OrderedDict
# back pressure
# https://pyformat.info/
from datetime import datetime
from os import path
from string import Formatter

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='/tmp/deep_log.log',
                    filemode='w')

built_function = {
    'datetime': datetime,  # datetime function
    'path': path,  # datetime function
}


def gen_default_values(format_string):
    format_keys = [i[1] for i in Formatter().parse(format_string) if i[1] is not None]
    return {one: '' for one in format_keys}


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
            else:
                # matched pattern
                # flush current item first
                if current_item:
                    items.append(current_item)
                current_item = {'line_number': file.tell(), **result}

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
                        original_value = one_definition[field_name]
                        if original_value.isdigit():
                            one_log_item[field_name] = int(original_value)
                        else:
                            one_log_item[field_name] = default_value

                    if type_name == 'float':
                        original_value = one_definition[field_name]
                        if original_value.isdigit():
                            one_log_item[field_name] = float(original_value)
                        else:
                            one_log_item[field_name] = default_value

                    return one_log_item
                except Exception as e:
                    logging.error("error to transfer {} in {}, use default value {}".format(str(one_log_item),
                                                                                            str(one_definition),
                                                                                            str(default_value)))
                    one_log_item[field_name] = default_value
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


class LogMiner:
    def __init__(self, setting_file):
        self.tree = None

        with open(setting_file) as f:
            settings = json.load(f)
            loggers = settings.get('loggers')
            root_node = TrieNode("/", value=None)
            if 'root' in loggers:
                root_node = TrieNode("/", value=loggers.get('root'))

            self.tree = Trie(root_node)

            for key, value in loggers.items():
                if key == 'root':
                    # root node should be already added
                    continue
                if value is None or 'path' not in value:
                    logging.warning("config %(key)s ignore, because no path defined" % locals())
                else:
                    the_path = value.get('path')
                    the_node = TrieNode(the_path, value)
                    self.tree.insert(the_path, value)

    def _parse_file(self, fp):
        file_name = fp.name
        node = self.tree.find(file_name, accept=lambda x: 'parser' in x)
        if node is not None and node.get('parser'):
            node_parser = node.get('parser')
            parser_name = node_parser.get('name')
            parser_params = node_parser.get('params')
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
                handler_params = one_node_handler.get('params')
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
                filter_params = one_node_filters.get('params')
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

    def mining(self, dirs, file_filters=None, pre_content_filters=None, subscribe=False):
        full_paths = []
        for folder in dirs:
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


def get_settings_file(custom_settings=None):
    config_dir = path.expanduser("~/.deep_log")
    if custom_settings is None:
        make_directory(config_dir)

        default_settings_json = os.path.join(config_dir, "settings.json")
        if not os.path.exists(default_settings_json):
            default_settings = {
                "common": {

                },
                "loggers": {
                    "root": {}
                }
            }
            with open(default_settings_json, "w") as f:
                json.dump(default_settings, f)
        return os.path.join(config_dir, "settings.json")
    return custom_settings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', help='config file')
    parser.add_argument('-l', '--filter', help='log filter')
    parser.add_argument('-t', '--file-filter', help='file filters')
    parser.add_argument('-n', '--file-name', help='file name filters')
    parser.add_argument('-u', '--layout', help='return layout ')
    parser.add_argument('-m', '--format', help='print format ')
    parser.add_argument('-s', '--subscribe', action='store_true', help='subscribe mode')
    parser.add_argument('-o', '--order-by', help='field to order by')
    parser.add_argument('-r', '--reverse', action='store_true', help='reverse order, only work with order by')
    parser.add_argument('--limit', type=int, help='limit query count')
    parser.add_argument('dirs', metavar='N', nargs='+', help='log dirs to analyze')

    args = parser.parse_args()

    log_miner = LogMiner(get_settings_file(args.file))
    format = "{raw}" if not args.format else args.format
    default_value = gen_default_values(format)

    items = []

    count = 0
    for item in log_miner.mining(args.dirs, [FileNameFilter(args.file_name), FileInfoFilter(args.file_filter)], [],
                                 args.subscribe):
        if args.filter:
            if not eval(args.filter, {**built_function, **item}):
                continue
        if args.subscribe or not args.order_by:
            # not subscribe mode or not order by mode, print out immediately
            print(format.format(**{**default_value, **item}))
        else:
            # only for order by
            items.append(item)

        count = count + 1
        if args.limit is not None and count >= args.limit:
            break

    items.sort(key=lambda x: x.get(args.order_by), reverse=args.reverse)

    for one in items:
        print(format.format(**{**default_value, **one}))


if __name__ == '__main__':
    main()
