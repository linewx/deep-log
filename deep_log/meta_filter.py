import fnmatch

from deep_log import utils


class MetaFilter:
    def filter_file(self, file_name):
        return True


class NameFilter(MetaFilter):
    def __init__(self, filters):
        if filters:
            self.filters = filters.split(',')
        else:
            self.filters = None

    def filter_file(self, file_name):
        if self.filters:
            for one in self.filters:
                if fnmatch.fnmatch(file_name.lower(), one):
                    return True
            return False
        else:
            return True


class DslMetaFilter(MetaFilter):
    def __init__(self, file_filter):
        self.file_filter = file_filter
        self.code = compile(self.file_filter, '', 'eval')

    def filter_file(self, filename):
        if self.file_filter:
            return eval(self.code, {**utils.get_fileinfo(filename), **utils.built_function})
        else:
            return True
