import copy

from deep_log import utils


class LogFilter:
    def filter(self, one_log_item):
        return True


class DefaultLogFilter(LogFilter):
    def filter(self, one_log_item):
        return True


class DslFilter(LogFilter):
    def __init__(self, filter, pass_on_exception=False):

        self.dsl = filter
        self.pass_on_exception = pass_on_exception
        if self.dsl:
            self.dsl = compile(self.dsl, '', 'eval')

    def filter(self, one_log_item):
        try:
            if self.dsl:
                clone_item = copy.deepcopy(one_log_item)
                return eval(self.dsl, {**clone_item, **utils.built_function})
            else:
                return True
        except Exception as error:
            print(error)
            return self.pass_on_exception
