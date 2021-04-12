class LogFilter:
    def filter(self, one_log_item):
        return True


class DefaultLogFilter(LogFilter):
    def filter(self, one_log_item):
        return True


class DslFilter(LogFilter):
    def __init__(self, dsl, pass_on_exception=False):

        self.dsl = dsl
        self.pass_on_exception = pass_on_exception
        if self.dsl:
            self.dsl = compile(self.dsl, '', 'eval')

    def filter(self, one_log_item):
        try:
            if self.dsl:
                return eval(self.dsl, one_log_item)
            else:
                return True
        except:
            return self.pass_on_exception
