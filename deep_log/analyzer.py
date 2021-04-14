from string import Formatter


class LogFormatter:
    def __init__(self, format_string=None):
        self.log_format = '{raw}' if format_string is None else format_string

        self.full_mode = True if format_string == '{}' else False

        self.default_values = LogFormatter.build_default_values(self.log_format)

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

    def print(self, content):
        print(self.format(content))


class LogAnalyzer:
    def __init__(self, miner):
        self.miner = miner

    def _build_formatter(self, format_string=None):
        return LogFormatter(format_string)

    def analyze(self, dirs=None, modules=(), subscribe=None, order_by=None, analyze=None, log_format=None, limit=None,
                full=False,
                reverse=False, name_only=False, workers=1):
        if name_only:
            log_format = '{}'

        formmater = self._build_formatter(log_format)

        items = []
        count = 0

        streaming_mode = True

        if order_by or analyze:
            streaming_mode = False
        if workers and workers > 1:
            for item in self.miner.mine_x(dirs, modules=modules, subscribe=subscribe, name_only=name_only, subscribe_handler=formmater.print, workers=workers):
                if streaming_mode:
                    print(formmater.format(item))
                else:
                    items.append(item)

                count = count + 1
                if limit is not None and count >= limit:
                    break
        else:
            for item in self.miner.mine(dirs, modules=modules, subscribe=subscribe, name_only=name_only):
                if streaming_mode:
                    print(formmater.format(item))
                else:
                    items.append(item)

                count = count + 1
                if limit is not None and count >= limit:
                    break
        if order_by:
            # order by mode, need shuffle in memory
            items.sort(key=lambda x: x.get(order_by), reverse=reverse)

            for item in items:
                print(formmater.format(item))

        elif analyze:
            import pandas as pd
            data = pd.DataFrame(items)
            result = eval(analyze, {'data': data})
            if full:
                pd.set_option('display.max_colwidth', None)
                pd.set_option('display.max_rows', None)
            print(result)
