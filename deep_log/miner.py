import glob
import os
import time
from os import path

from deep_log import utils


class DeepLogMiner:
    def __init__(self, config):
        self.config = config

    def _parse_file(self, fp):
        parser = self.config.get_parser(fp.name)
        return parser.parse_file(fp)

    def _handle_file(self, fp, parsed_results):
        handlers = self.config.get_handlers(fp.name)

        for one_handler in handlers:
            parsed_results = [one_handler.handle(one) for one in parsed_results]

        return parsed_results

    def _filter_file(self, fp, parsed_results):
        filters = self.config.get_filters(fp.name)
        for one_node_filters in filters:
            parsed_results = [one for one in parsed_results if one_node_filters.filter(one)]
        return parsed_results

    def _is_qualified_item(self, log_item):
        filters = self.config.get_global_filters()
        for one_filter in filters:
            if not one_filter.filter(log_item):
                return False
        return True

    def mine_file(self, fp):
        parsed_results = self._parse_file(fp)
        parsed_results = self._handle_file(fp, parsed_results)
        parsed_results = self._filter_file(fp, parsed_results)
        return parsed_results

    def mine_files(self, fps):
        for fp in fps:
            file_name = fp.name
            results = self.mine_file(fp)
            if results:
                for one in results:
                    yield {'file_name': file_name, **one}

    def mining_files(self, filename_list):
        fps = []
        for one in filename_list:
            try:
                fp = open(one)
                fps.append(fp)
            except:
                pass

        for fp in fps:
            fp.seek(0, 2)

        while True:
            for one in self.mine_files(fps):
                yield one
            time.sleep(0.1)

    def _filter_meta(self, file_name_list):
        if not file_name_list:
            return file_name_list

        filtered_list = []
        for file_name in file_name_list:
            meta_filters = self.config.get_meta_filters(file_name)
            for one_filter in meta_filters:
                if not one_filter.filter_meta(file_name):
                    break
            else:
                filtered_list.append(file_name)

        return filtered_list

    def normalize_path(self, dir):
        dir = path.expanduser(dir)
        dir = path.expandvars(dir)
        dir = path.abspath(dir)
        return glob.glob(dir)

    def mine(self, target_dirs=None, modules=None, subscribe=False):
        if not target_dirs:
            target_dirs = self.config.get_default_paths(modules)

        full_paths = []

        dirs = []
        for one_target_dir in target_dirs:
            dirs.extend(self.normalize_path(one_target_dir))

        for folder in dirs:

            if path.isfile(folder):
                full_paths.append(folder)
                continue

            for root, dirs, files in os.walk(folder):
                for file in files:
                    full_paths.append(os.path.join(root, file))
        #
        # if file_filters:
        #     for one_file_filter in file_filters:
        #         full_paths = [one for one in full_paths if one_file_filter.filter(one)]

        # for internal file filter
        full_paths = self._filter_meta(full_paths)

        if subscribe:
            for one in self.mining_files(full_paths):
                yield one
        else:
            opened_file_list = []
            for one in full_paths:
                try:
                    fp = open(one)
                    opened_file_list.append(fp)
                except:
                    pass

            for one in self.mine_files(opened_file_list):
                yield one
