import fnmatch
import json
import logging
import os
from collections import OrderedDict
from os import path

# trie node
import pkg_resources

from deep_log import utils

from deep_log import parser
from deep_log import handler

from deep_log import filter
from deep_log import meta_filter
import yaml


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


class TemplateRepo:
    def __init__(self, template_dir=None):
        self.template_repo = {}

        if not os.path.exists(template_dir):
            return

        for one in os.listdir(template_dir):
            if not one.endswith('yaml'):
                continue

            template_file = os.path.join(template_dir, one)
            with open(template_file) as f:
                try:
                    one_template = yaml.safe_load(f)
                    if 'name' in one_template:
                        self.template_repo[one_template.get('name')] = one_template
                except Exception as e:
                    logging.error(e)

    def get_template(self, template_name):
        return self.template_repo.get(template_name)


class LogConfig:
    def __init__(self, config_root=None, custom_variables=None, custom_template_name=None, custom_template_dir=None):
        self.config_root = config_root if config_root else utils.normalize_path('~/.deep_log')
        self.global_settings = {
            'parsers': [],
            'filters': [],
            'handlers': [],
            'meta_filters': []
        }

        # load settings
        settings = self._load_config(config_root)
        self.populate_default_values(settings)
        self.populate_vars(settings, custom_variables)
        self.populate_paths(settings)

        template_repo = TemplateRepo(os.path.join(self.config_root, 'templates'))
        self.populate_templates(settings, template_repo, custom_template_name, custom_template_dir)
        # populate variable

        # populate template
        # self.settings = self._parse_config(config_file, variables)

        self.loggers = self._build_loggers(settings)

        self.settings = settings
        #
        # def _get_logger_template(self, logger_template, variables=None):
        #     templates = self.settings.get('templates')
        #
        #     if 'name' in logger_template:
        #         for one in templates:
        #             if one.get('name') == logger_template.get('name'):
        #                 return one
        #     elif 'location' in logger_template:
        #         # populate location
        #         config_dir = os.path.dirname(utils.normalize_path(self._get_config_file()))
        #         template_file = utils.normalize_path(os.path.join(config_dir, logger_template.get('location')))
        #         with open(template_file) as f:
        #             return yaml.safe_loa_get_logger_templated(f)

        # return {}

    def _merge_loggers(self, logger1, logger2):
        if logger1 is None and logger2 is None:
            return {}
        if logger1 is None:
            return logger2
        if logger2 is None:
            return logger1
        return {
            "parser": self._merge_object(logger1.get('parser'), logger2.get('parser')),
            "filters": self._merge_array(logger1.get('filters'), logger2.get('filters')),
            "meta_filters": self._merge_array(logger1.get('meta_filters'), logger2.get('meta_filters')),
            "handlers": self._merge_array(logger1.get('handlers'), logger2.get('handlers')),
        }

    def _merge_array(self, array1, array2):
        if array1 is None and array2 is None:
            return []
        if array1 is None:
            return array2
        if array2 is None:
            return array1
        return [*array1, *array2]

    def _merge_object(self, obj1, obj2):
        if obj1 is None and obj2 is None:
            return []
        if obj1 is None:
            return obj2
        if obj2 is None:
            return obj1

        return obj2

    def _load_config(self, settings_file=None, variables=None, root_parser=None):
        if not os.path.exists(self._get_config_file()):
            raise Exception('config file not found')

        with open(self._get_config_file()) as f:
            return yaml.safe_load(f)

    def populate_default_values(self, settings):
        if 'variables' not in settings or settings.get('variables') is None:
            settings['variables'] = {}

        if 'loggers' not in settings or settings.get('loggers') is None:
            settings['loggers'] = []

    def populate_vars(self, settings, variables):
        if settings.get('variables') is None:
            settings['variables'] = {}

        if variables:
            settings.get('variables').update(variables)

        # populate variables
        settings.get('variables').update(utils.evaluate_variables(variables, depth=5))

    def populate_paths(self, settings):
        # populate loggers paths
        for one_logger in settings.get('loggers'):
            one_logger['path'] = one_logger.get('path').format(**settings.get('variables'))
        return settings

    def populate_templates(self, settings, template_repo=None, custom_template=None, custom_template_dir=None):
        # populate root template
        root_logger = settings.get('root')
        if custom_template:
            # use custom template to populate
            merged_logger = self._merge_loggers(template_repo.get_template(custom_template), root_logger)
            root_logger.update(merged_logger)

        elif custom_template_dir:
            # use custom template dir to populate
            template_content = {}
            with open(utils.normalize_path(custom_template_dir)) as f:
                template_content = yaml.safe_load(f)
            merged_logger = self._merge_loggers(template_content, root_logger)
            root_logger.update(merged_logger)

        elif 'template' in root_logger:
            logger_template_name = root_logger.get('template')
            merged_logger = self._merge_loggers(template_repo.get_template(logger_template_name), root_logger)
            root_logger.update(merged_logger)
        elif 'template_dir' in root_logger:
            logger_template_dir = os.path.join(self.config_root, root_logger.get('template_dir'))
            template_content = {}
            with open(logger_template_dir) as f:
                template_content = yaml.safe_load(f)
            merged_logger = self._merge_loggers(template_content, root_logger)
            root_logger.update(merged_logger)

        # populate logger template
        for one_logger in settings.get('loggers'):
            merged_logger = {}
            if custom_template:
                # use custom template to populate
                merged_logger = self._merge_loggers(template_repo.get_template(custom_template), one_logger)
                one_logger.update(merged_logger)

            if custom_template_dir:
                # use custom template dir to populate
                template_content = {}
                with open(utils.normalize_path(custom_template_dir)) as f:
                    template_content = yaml.safe_load(f)
                merged_logger = self._merge_loggers(template_content, one_logger)
                one_logger.update(merged_logger)

            elif 'template' in one_logger:
                logger_template_name = one_logger.get('template')
                merged_logger = self._merge_loggers(template_repo.get_template(logger_template_name), one_logger)
                one_logger.update(merged_logger)
            elif 'template_dir' in one_logger:
                logger_template_dir = os.path.join(self.config_root, one_logger.get('template_dir'))
                template_content = {}
                with open(logger_template_dir) as f:
                    template_content = yaml.safe_load(f)
                merged_logger = self._merge_loggers(template_content, one_logger)
                one_logger.update(merged_logger)
        return settings

    def _get_config_file(self):
        if os.path.exists(self.config_root):
            return utils.normalize_path(os.path.join(self.config_root, 'config.yaml'))
        elif os.path.exists(utils.normalize_path('~/.deep_log/config.yaml')):
            return utils.normalize_path('~/.deep_log/config.yaml')
        else:
            return pkg_resources.resource_filename('deep_log', 'config.yaml')

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
                loggers.insert(the_path, one_logger)

        return loggers

    # def _build_one_logger(self, one_logger):
    #     if not one_logger:
    #         return one_logger
    #
    #     merged_logger = None
    #
    #     if self.global_settings['template']:
    #         # use global template instead specified by user
    #         # don't use any definitions in config file
    #         return self._get_logger_template(self.global_settings['template'])
    #
    #     if 'template' in one_logger:
    #         logger_template_name = one_logger.get('template')
    #         merged_logger = self._merge_loggers(merged_logger, self._get_logger_template(logger_template_name))
    #
    #     return self._merge_loggers(merged_logger, one_logger)

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
                    # if set(modules) & the_modules:
                    if set(modules) <= the_modules:
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

    def set_template(self, template, scope='global'):
        if scope == 'global' and template:
            self.global_settings['template'] = template
