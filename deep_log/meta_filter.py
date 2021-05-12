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
        match_included = False
        if not self.patterns:
            match_included = True
        for one_pattern in self.patterns:
            if fnmatch.fnmatch(file_name, one_pattern):
                match_included = True
        if not match_included:
            return False

        for one_exclude_pattern in self.exclude_patterns:
            if fnmatch.fnmatch(file_name, one_exclude_pattern):
                return False

        return True


class DslMetaFilter(MetaFilter):
    def __init__(self, filter):
        self.file_filter = filter
        self.code = compile(self.file_filter, '', 'eval')

    def filter_meta(self, filename):
        if self.file_filter:
            return eval(self.code, {**utils.get_fileinfo(filename), **utils.built_function})
        else:
            return True
