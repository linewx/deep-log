from string import Formatter
import pandas as pd
import types

class OutputFormat:
    def format(self, content):
        pass


class DefaultOutputFormat(OutputFormat):
    def format(self, content):
        return str(content)


class TextOutputFormat(OutputFormat):
    def __init__(self, format_string=None):
        self.log_format = '{_record}' if format_string is None else format_string

        self.full_mode = True if format_string == '{}' else False

        self.default_values = TextOutputFormat.build_default_values(self.log_format)

    @staticmethod
    def build_default_values(format_string):
        format_keys = [i[1] for i in Formatter().parse(format_string) if i[1] is not None]
        return {one: '' for one in format_keys if one}

    def format(self, content):
        # not order by mode, print out immediately
        if self.full_mode:
            return str(content)
        else:
            return self.log_format.format(**{**self.default_values, **content})


class DataFrameOutputFormat(OutputFormat):
    def __init__(self, show_all=True):
        self.show_all = True

    def format(self, content):
        if self.show_all:
            import pandas as pd
            pd.set_option('display.max_colwidth', None)
            pd.set_option('display.max_rows', None)
        return content


class RecordWriter:
    def __init__(self):
        self.formatters = {}

    def register(self, name, formatter):
        self.formatters[name] = formatter

    def get_formatter(self, record):
        return self.formatters.get(type(record).__name__, DefaultOutputFormat())

    def write(self, record):
        if isinstance(record, types.GeneratorType) or isinstance(record, list):
            # iterable object
            for one in record:
                self.write(one)
        else:
            formatter = self.get_formatter(record)
            print(formatter.format(record))


class LogRecordWriterFactory:
    @staticmethod
    def create(format, pd_full_mode):
        record_writer = RecordWriter()
        record_writer.register('dict', TextOutputFormat(format))
        record_writer.register('DataFrame', DataFrameOutputFormat(pd_full_mode))
        return record_writer


def test():
    for i in range(100):
        yield i

if __name__ == '__main__':
    print(type(test()))