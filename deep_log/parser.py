import logging
import re

from deep_log.utils import get_fileinfo


class LogParser:
    def parse_file(self, file):
        pass

    def parse(self, lines):
        pass

    def parse_line(self, line):
        pass


class DefaultLogParser(LogParser):
    def __init__(self, *args, **kwargs):
        self.pattern = '' if 'pattern' not in kwargs else kwargs['pattern']
        self.log_items = []
        self.strategy = ''

    def parse_file(self, file):
        items = []
        current_item = {}

        while True:
            line = file.readline()
            if not line:
                # flush final results
                if current_item:
                    return [*items, current_item]
                else:
                    return [*items]

            result = self.parse_line(line)
            if result is None:
                # not matched, append to last item, if not found, ignore it
                if not current_item:
                    logging.warning("line %s ignored" % line)
                else:
                    # affinity to last item
                    current_item['raw'] = current_item['raw'] + line
                    current_item['content'] = current_item['content'] + line
                    # current_item.update(get_fileinfo(file.name))
            else:
                # matched pattern
                # flush current item first
                if current_item:
                    items.append(current_item)
                current_item = {'line_number': file.tell(), **result}
                current_item.update({'tags': set()})
                current_item.update(get_fileinfo(file.name))

    def parse_line(self, one_line):
        # {'raw': '', 'content': 'content'}
        # None if not matched
        result = None
        matched_result = re.match(self.pattern, one_line)

        if matched_result is None:
            result = None
        else:
            result = matched_result.groupdict()
            result['raw'] = one_line
            if 'content' not in result:
                result['content'] = one_line

        return result


