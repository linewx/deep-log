import os
import time
from functools import partial
import multiprocessing as mp


class LogRunner:
    def __init__(self, log_miner, log_analyzer, targets=None, modules=None, workers=8, name_only=False,
                 subscribe=False, limit=None, full=None, format=format, analyze=format, order_by=None, reverse=False):
        # rguments = ['subscribe', 'order_by', 'analyze', 'format', 'limit', 'full', 'reverse', 'name_only', 'workers']
        self.log_miner = log_miner  # mapper
        self.log_analyzer = log_analyzer  # reducer
        self.targets = targets
        self.modules = modules
        self.name_only = name_only
        self.workers = workers
        self.subscribe = subscribe
        self.order_by = order_by
        self.reverse = reverse

    def mine_files(self, files):
        if isinstance(files, str):
            files = [files]
        return list(self.log_miner.mine_files(files))

    def mining_files(self, files, queue):
        for one in self.log_miner.mining_files(files):
            queue.put(one)

    def run(self):
        if self.name_only:
            for one in self.log_miner.get_target_files():
                print(one)

        if self.subscribe:
            # stream mode
            for one in self.run_in_multi_streams():
                print(one)

        else:
            for one in self.run_in_multi_batches():
                print(one)

    def default_run(self):
        pass

    def run_in_multi_batches(self):
        with mp.Pool(processes=self.workers) as pool:
            for one in pool.imap_unordered(self.mine_files, self.log_miner.get_target_files(self.targets, self.modules)):
                try:
                    for item in one:
                        yield item
                except:
                    pass


    def run_in_multi_streams(self):
        file_groups = [[] for one in range(0, self.workers)]
        full_paths = self.log_miner.get_target_files(self.targets, self.modules)
        for one in range(len(full_paths)):
            the_index = one % self.workers
            file_groups[the_index].append(full_paths[one])

        queue = mp.Queue()
        for one_file_group in file_groups:
            p = mp.Process(target=self.mining_files, args=(one_file_group, queue))
            p.start()

        while True:
            yield (queue.get())
