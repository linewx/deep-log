#!/usr/bin/env python
import argparse
import logging

from deep_log import factory
from deep_log.analyzer import LogAnalyzer
from deep_log.config import LogConfig
from deep_log.miner import DeepLogMiner

# back pressure
# https://pyformat.info/

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

        if args.filter:
            filters.append(factory.FilterFactory.create_dsl_filter(args.filter))

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

    @staticmethod
    def build_variables(args):
        variables = {}
        if args.variables:
            variables = {one.split('=')[0]: one.split('=')[1] for one in args.variables}

        return variables

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
        parser.add_argument('--recent', help='query to recent time')
        parser.add_argument('-y', '--analyze', help='analyze')
        parser.add_argument('--tags', help='query by tags')
        parser.add_argument('--modules', help='query by tags')
        parser.add_argument('--full', action='store_true', help='display full')
        parser.add_argument('-D', action='append', dest='variables', help='definitions')
        parser.add_argument('dirs', metavar='N', nargs='*', help='log dirs to analyze')

        return parser.parse_args()


def main():
    args = CmdHelper.build_args_parser()
    log_config = LogConfig(args.file, CmdHelper.build_variables(args))
    log_config.add_filters(CmdHelper.build_filters(args), scope='global')
    log_miner = DeepLogMiner(log_config)
    log_analyzer = LogAnalyzer(log_miner)

    log_analyzer.analyze(dirs=args.dirs, modules=args.modules, subscribe=args.subscribe, order_by=args.order_by,
                         analyze=args.analyze,
                         log_format=args.format, limit=args.limit, full=args.full, reverse=args.reverse)


if __name__ == '__main__':
    main()
