import fnmatch
import glob
import json
import logging
import os
import time
from collections import OrderedDict
from os import path

from deep_log import utils
from deep_log.config import Logger, Loggers
from deep_log.parser import DefaultLogParser


class DeepLogMiner:
    def __init__(self, settings):
        self.tree = None
        self.settings = settings

        loggers = self.settings.get('loggers')

        # root_node = TrieNode("/", value=None)
        root_node = Logger("/", value=self.settings.get('root'))

        self.tree = Loggers(root_node)

        for one_logger in loggers:
            if one_logger is None or 'path' not in one_logger:
                logging.warning("config %(key)s ignore, because no path defined" % locals())
            else:
                the_path = one_logger.get('path')
                the_path = the_path.format(**self.settings.get('variables'))
                the_node = Logger(the_path, one_logger)
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
            utils.make_directory(config_dir)

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
