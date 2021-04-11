import fnmatch
import json
import os
from collections import OrderedDict
from os import path

# trie node
from deep_log import utils


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
        self.configs = self.load(config_file, variables)


    def load(self, settings_file=None, variables=None, root_parser=None):
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
