import fnmatch

from deep_log import utils


class MetaFilter:
    def filter_meta(self, file_name):
        return True


class NameFilter(MetaFilter):
    def __init__(self, patterns='', exclude_patterns=''):
        self.patterns = patterns.split(',') if patterns else []
        self.exclude_patterns = exclude_patterns.split(',') if exclude_patterns else []

    def filter_meta(self, file_name):
        for one_pattern in self.patterns:
            if fnmatch.fnmatch(file_name.lower(), one_pattern):
                break
        else:
            return False

        for one_exclude_pattern in self.exclude_patterns:
            if fnmatch.fnmatch(file_name.lower(), one_exclude_pattern):
                return False

        return True


class DslMetaFilter(MetaFilter):
    def __init__(self, file_filter):
        self.file_filter = file_filter
        self.code = compile(self.file_filter, '', 'eval')

    def filter_meta(self, filename):
        if self.file_filter:
            return eval(self.code, {**utils.get_fileinfo(filename), **utils.built_function})
        else:
            return True
