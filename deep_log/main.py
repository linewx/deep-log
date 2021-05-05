#!/usr/bin/env python
import argparse
import logging

from deep_log import factory
from deep_log.analyzer import LogAnalyzer
from deep_log.config import LogConfig
from deep_log.miner import DeepLogMiner

# back pressure
# https://pyformat.info/
from deep_log.record_writer import LogRecordWriterFactory
from deep_log.engine import LogEngine

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='/tmp/deep_log.log',
                    filemode='w')


class CmdHelper:
    @staticmethod
    def build_filters(args):
        filters = []
        if not args:
            return filters

        if args.pattern:
            filters.append(
                factory.FilterFactory.create_dsl_filter('\'{}\' in _record'.format(args.pattern), args.pass_on_exception))

        if args.filter:
            filters.append(factory.FilterFactory.create_dsl_filter(args.filter, args.pass_on_exception))

        if args.recent:
            filters.append(factory.FilterFactory.create_recent_dsl(args.recent))

        if args.tags:
            filters.append(factory.FilterFactory.create_tags_filter(args.tags))

        return filters

    @staticmethod
    def build_meta_filters(args):
        # build meta filter
        meta_filters = []

        if not args:
            return meta_filters

        if args.file_name:
            meta_filters.append(factory.MetaFilterFactory.create_name_filter(args.file_name))

        if args.file_filter:
            meta_filters.append(factory.MetaFilterFactory.create_dsl_filter(args.file_filter))

        if args.recent:
            meta_filters.append(factory.MetaFilterFactory.create_recent_filter(args.recent))

        return meta_filters

    @staticmethod
    def build_variables(args):
        variables = {}
        if args.variables:
            variables = {one.split('=')[0]: one.split('=')[1] for one in args.variables}

        return variables

    @staticmethod
    def get_argument(args, config, variable):
        value = getattr(args, variable)
        if value is None:
            return config.get_variable(variable)
        else:
            return value

    @staticmethod
    def build_args_parser():
        parser = argparse.ArgumentParser()
        parser.add_argument('-f', '--file', help='config file')
        parser.add_argument('-l', '--filter', help='log filter')
        parser.add_argument('-p', '--parser', help='root parser')
        parser.add_argument('-t', '--file-filter', help='file filters')
        parser.add_argument('-n', '--file-name', help='file name filters')
        parser.add_argument('-u', '--layout', help='return layout')
        parser.add_argument('-m', '--format', help='print format')
        parser.add_argument('-s', '--subscribe', action='store_true', help='subscribe mode')
        parser.add_argument('-o', '--order-by', help='field to order by')
        parser.add_argument('-r', '--reverse', action='store_true', help='reverse order, only work with order by')
        parser.add_argument('--limit', type=int, help='limit query count')
        parser.add_argument('--window', type=int, help='processing window size')
        parser.add_argument('--workers', type=int, help='workers count')
        parser.add_argument('--recent', help='query to recent time')
        parser.add_argument('-y', '--analyze', help='analyze')
        parser.add_argument('--tags', help='query by tags')
        parser.add_argument('--modules', help='query by modules')
        parser.add_argument('--template', help='logger template')
        parser.add_argument('--distinct', help='distinct column')
        parser.add_argument('--template_dir', help='logger template dir')
        parser.add_argument('--name-only', action='store_true', help='show only file name')
        parser.add_argument('--full', action='store_true', help='display full')
        parser.add_argument('--include-history', action='store_true', help='subscribe history or nor')
        parser.add_argument('--pass-on-exception', action='store_true', help='default value if met exception')
        parser.add_argument('-D', action='append', dest='variables', help='definitions')
        parser.add_argument('--target', metavar='N', nargs='*', help='log dirs to analyze')
        parser.add_argument('pattern', nargs='?', help='default pattern to analyze')

        return parser.parse_args()

    @staticmethod
    def build_modules(args):
        if args.modules:
            return args.modules.split(',')
        return []


def main():
    args = CmdHelper.build_args_parser()
    log_config = LogConfig(args.file, CmdHelper.build_variables(args), custom_template_name=args.template,
                           custom_template_dir=args.template_dir)
    log_config.add_filters(CmdHelper.build_filters(args), scope='global')
    log_config.add_meta_filters(CmdHelper.build_meta_filters(args), scope='global')
    # log_config.set_template(args.template, scope='global')
    log_miner = DeepLogMiner(log_config) # mapper

    log_analyzer = LogAnalyzer(args.order_by, args.analyze, args.reverse) #reducer

    log_record_writer = LogRecordWriterFactory.create(args.format, args.full)

    arguments = ['subscribe',  'limit',  'name_only', 'workers', 'modules', 'distinct', 'include_history', 'window']

    # log_analyzer.analyze(dirs=args.target, modules=CmdHelper.build_modules(args),
    #                      **{one: CmdHelper.get_argument(args, log_config, one) for one in arguments})
    #
    runner = LogEngine(log_miner, log_analyzer, log_record_writer, targets=args.target,
                       **{one: CmdHelper.get_argument(args, log_config, one) for one in arguments})
    runner.run()


if __name__ == '__main__':
    main()
