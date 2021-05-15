import logging
import re
# back pressure
# https://pyformat.info/
from copy import copy
from datetime import datetime
from os import path

from deep_log import utils
from deep_log.utils import built_function


class LogHandler:
    def handle(self, one_log_item):
        return one_log_item


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
    def __init__(self, fields=None):
        self.fields = fields

    def handle(self, one_log_item):
        if self.fields is None:
            return {key: (value.strip() if isinstance(value, str) else value) for key, value in one_log_item.items()}
        else:
            return {key: (value.strip() if key in self.fields and isinstance(value, str) else value) for key, value in
                    one_log_item.items()}


class TransformLogHandler(LogHandler):
    def __init__(self, definitions):
        self.definitions = definitions

    def handle(self, one_log_item):
        new_one_log_item = copy(one_log_item)
        for one_definition in self.definitions:
            name = one_definition.get('name')
            value = one_definition.get('value')
            new_one_log_item[name] = eval(value, {**one_log_item, **utils.built_function})

        return new_one_log_item


class RegLogHandler(LogHandler):
    def __init__(self, pattern, field=None):
        self.pattern = pattern
        self.field = field if field else '_record'
        self.compiled_pattern = re.compile(self.pattern)

    def handle(self, one_log_item):
        new_one_log_item = copy(one_log_item)
        if self.pattern:
            matched_result = self.compiled_pattern.search(new_one_log_item.get(self.field))
            if matched_result:
                new_one_log_item.update(matched_result.groupdict())
        return new_one_log_item


class TagLogHandler(LogHandler):
    def __init__(self, definitions):
        # {
        #   'name': 'tag_name',
        #   'condition': 'tag_name
        # }
        self.tag_definitions = definitions
        self._precess_condition()

    def _precess_condition(self):
        self.tag_definitions = [{"name": one.get("name"), "condition": compile(one.get('condition'), '', 'eval')} for
                                one in self.tag_definitions]

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
