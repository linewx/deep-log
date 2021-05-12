from datetime import datetime

from deep_log import meta_filter

from deep_log import filter


class FilterFactory:
    @staticmethod
    def create_dsl_filter(dsl, pass_on_exception=False):
        return {
            'name': 'DslFilter',
            'params': {
                'filter': dsl,
                'pass_on_exception': pass_on_exception
            }
        }
        # return filter.DslFilter(dsl, pass_on_exception)

    @staticmethod
    def create_recent_dsl(recent):
        filter_dsl_template = 'time.timestamp() - {} > 0'
        if not recent:
            return 'True'

        recent_seconds = 0
        if recent.isdigit():
            # seconds by default
            recent_seconds = int(recent)
        elif recent.lower().endswith('s'):
            recent_seconds = int(recent[:-1])
        elif recent.lower().endswith('m'):
            recent_seconds = int(recent[:-1]) * 60
        elif recent.lower().endswith('h'):
            recent_seconds = int(recent[:-1]) * 60 * 60
        elif recent.lower().endswith('d'):
            recent_seconds = int(recent[:-1]) * 60 * 60 * 24
        else:
            raise Exception("unsupported recent format {}".format(recent))

        start_time = datetime.now().timestamp() - recent_seconds

        return {
            'name': 'DslFilter',
            'params': {
                'filter': filter_dsl_template.format(start_time)
            }
        }

        # return filter.DslFilter(filter_dsl_template.format(start_time))

    @staticmethod
    def create_tags_filter(tags):
        target_tags = set(tags.split(','))
        return {
            'name': 'DslFilter',
            'params': {
                'filter': 'tags & {}'.format(str(target_tags))
            }
        }
        # return filter.DslFilter('tags & {}'.format(str(target_tags)))


class MetaFilterFactory:
    @staticmethod
    def create_recent_filter(recent):
        meta_filter_template = 'mtime.timestamp() - {} > 0'
        if recent is None:
            # no fitler
            return meta_filter.DslMetaFilter(None)

        recent_seconds = 0
        if recent.isdigit():
            # seconds by default
            recent_seconds = int(recent)
        elif recent.lower().endswith('s'):
            recent_seconds = int(recent[:-1])
        elif recent.lower().endswith('m'):
            recent_seconds = int(recent[:-1]) * 60
        elif recent.lower().endswith('h'):
            recent_seconds = int(recent[:-1]) * 60 * 60
        elif recent.lower().endswith('d'):
            recent_seconds = int(recent[:-1]) * 60 * 60 * 24
        else:
            raise Exception("unsupported recent format {}".format(recent))

        start_time = datetime.now().timestamp() - recent_seconds
        return {
            'name': 'DslMetaFilter',
            'params': {
                'filter': meta_filter_template.format(start_time)
            }
        }
        # return meta_filter.DslMetaFilter(meta_filter_template.format(start_time))

    @staticmethod
    def create_name_filter(patterns='', exclude_patterns=''):
        # lazy initilze, for code object can't serialized between process
        return {
            'name': 'NameFilter',
            'params': {
                'patterns': patterns,
                'exclude_patterns': exclude_patterns
            }
        }
        # return meta_filter.NameFilter(pattern)

    @staticmethod
    def create_dsl_filter(dsl):
        return {
            'Name': 'DslMetaFilter',
            'params': {
                'filter': dsl
            }
        }
        # return meta_filter.DslMetaFilter(dsl)