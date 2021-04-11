class LogFilter:
    def filter(self, one_log_item):
        return True


class DefaultLogFilter(LogFilter):
    def filter(self, one_log_item):
        return True


class DslFilter(LogFilter):
    def __init__(self, dsl):
        self.dsl = dsl
        if self.dsl:
            self.dsl = compile(self.dsl)

    def filter(self, one_log_item):
        if self.dsl:
            return eval(self.dsl, one_log_item)
        else:
            return True