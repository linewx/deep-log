import fnmatch
import json
import logging
import os
from collections import OrderedDict
from os import path

# trie node
from deep_log import utils

from deep_log import parser
from deep_log import handler

from deep_log import filter
from deep_log import meta_filter


class Logger:
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
            new_node = Logger(name)
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


# Trie Tree
class Loggers:
    def __init__(self, root=None):
        self.root = root if root else Logger('/')

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


class LogConfig:
    def __init__(self, config_file=None, variables=None, filters=None, handlers=None, parsers=None):
        self.settings = self._parse_config(config_file, variables)

        self.loggers = self._build_loggers(self.settings)

        self.global_settings = {
            'parsers': [],
            'filters': [],
            'handlers': [],
            'meta_filters': []
        }

    def _parse_config(self, settings_file=None, variables=None, root_parser=None):
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

    def _build_loggers(self, settings):
        loggers_section = settings.get('loggers')

        # root_node = TrieNode("/", value=None)
        root_node = Logger("/", value=settings.get('root'))

        loggers = Loggers(root_node)

        for one_logger in loggers_section:
            if one_logger is None or 'path' not in one_logger:
                logging.warning("config %(key)s ignore, because no path defined" % locals())
            else:
                the_path = one_logger.get('path')
                the_path = the_path.format(**settings.get('variables'))
                the_node = Logger(the_path, one_logger)
                loggers.insert(the_path, one_logger)

        return loggers

    def get_default_paths(self, modules=None):
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

    def get_parser(self, file_name):
        node = self.loggers.find(file_name, accept=lambda x: 'parser' in x)
        if node is not None and node.get('parser'):
            node_parser = node.get('parser')
            parser_name = node_parser.get('name')
            parser_params = node_parser.get('params') if node_parser.get('params') else {}
            deep_parser = getattr(parser, parser_name)(**parser_params)
            return deep_parser
        else:
            return parser.DefaultLogParser()

    def get_handlers(self, file_name, scope=('node', 'global')):
        handlers = []

        if 'node' in scope:
            node = self.loggers.find(file_name, accept=lambda x: 'handlers' in x)

            if node is not None and node.get('handlers'):
                node_handlers = node.get('handlers')
                for one_node_handler in node_handlers:
                    handler_name = one_node_handler.get('name')
                    handler_params = one_node_handler.get('params') if one_node_handler.get('params') else {}
                    deep_handler = getattr(handler, handler_name)(**handler_params)
                    handlers.append(deep_handler)
        if 'global' in scope:
            for one_node_handler in self.global_settings['handlers']:
                handler_name = one_node_handler.get('name')
                handler_params = one_node_handler.get('params') if one_node_handler.get('params') else {}
                deep_handler = getattr(handler, handler_name)(**handler_params)
                handlers.append(deep_handler)

        return handlers

    def get_filters(self, file_name, scope=('node', 'global')):
        filters = []

        if 'node' in scope:
            node = self.loggers.find(file_name, accept=lambda x: 'filters' in x)
            if node is not None and node.get('filters'):
                node_filters = node.get('filters')
                for one_node_filters in node_filters:
                    filter_name = one_node_filters.get('name')
                    filter_params = one_node_filters.get('params') if one_node_filters.get('params') else {}
                    deep_filter = getattr(filter, filter_name)(**filter_params)
                    filters.append(deep_filter)

        if 'global' in scope:
            for one_node_filters in self.global_settings['filters']:
                filter_name = one_node_filters.get('name')
                filter_params = one_node_filters.get('params') if one_node_filters.get('params') else {}
                deep_filter = getattr(filter, filter_name)(**filter_params)
                filters.append(deep_filter)

        return filters

    def get_meta_filters(self, file_name, scope=('node', 'global')):
        meta_filters = []
        if 'node' in scope:
            node = self.loggers.find(file_name, accept=lambda x: 'meta_filters' in x)
            if node is not None and node.get('meta_filters'):
                node_filters = node.get('meta_filters')
                for one_node_filters in node_filters:
                    filter_name = one_node_filters.get('name')
                    filter_params = one_node_filters.get('params') if one_node_filters.get('params') else {}
                    deep_filter = getattr(meta_filter, filter_name)(**filter_params)
                    meta_filters.append(deep_filter)

        if 'global' in scope:
            for one_global_filters in self.global_settings['meta_filters']:
                filter_name = one_global_filters.get('name')
                filter_params = one_global_filters.get('params') if one_global_filters.get('params') else {}
                deep_filter = getattr(meta_filter, filter_name)(**filter_params)
                meta_filters.append(deep_filter)

        return meta_filters

    def add_filters(self, filters, scope='global'):
        if scope == 'global' and filters:
            self.global_settings['filters'].extend(filters)

    def add_handlers(self, handlers, scope='global'):
        if scope == 'global' and handlers:
            self.global_settings['filters'].extend(handlers)

    def add_parsers(self, parsers, scope='global'):
        if scope == 'global' and parsers:
            self.global_settings['filters'].extend(parsers)

    def add_meta_filters(self, filters, scope='global'):
        if scope == 'global' and filters:
            self.global_settings['meta_filters'].extend(filters)

    def get_variable(self, variable):
        return self.settings.get('variables').get(variable)