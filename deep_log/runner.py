import os
import time
from functools import partial
import multiprocessing as mp


class LogRunner:
    def __init__(self, log_miner, log_analyzer, log_writer, targets=None, modules=None, workers=None, name_only=False,
                 subscribe=False, limit=None, distinct=None):
        # rguments = ['subscribe', 'order_by', 'analyze', 'format', 'limit', 'full', 'reverse', 'name_only', 'workers']
        self.log_miner = log_miner  # mapper
        self.log_analyzer = log_analyzer  # reducer
        self.log_writer = log_writer
        self.targets = targets
        self.modules = modules
        self.name_only = name_only
        self.workers = workers
        self.subscribe = subscribe
        self.limit = limit
        self.distinct = distinct.split(',') if distinct else []

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

        need_reduce = self.log_analyzer.need_reduce()

        counter = 0
        existing_records = set()
        mapped_results = []
        for one in self.execute():
            if self.limit and counter >= self.limit:
                break

            if self.distinct:
                the_distinct_values = tuple([one.get(column) for column in self.distinct])
                if the_distinct_values in existing_records:
                    continue
                else:
                    existing_records.add(the_distinct_values)

            if not need_reduce:
                # print out directly
                self.log_writer.write(one)
            else:
                # for future reducer
                mapped_results.append(one)
            counter = counter + 1

        if need_reduce:
            analyzed_results = self.log_analyzer.analyze(mapped_results)
            self.log_writer.write(analyzed_results)
        #
        # self.log_writer(self.execute())
        # else:
        #     self.log_writer

    def execute(self):
        if self.subscribe:
            # stream mode
            for one in self.run_in_multi_streams():
                yield one

        else:
            for one in self.run_in_multi_batches():
                yield one

    def default_run(self):
        pass

    def run_in_multi_batches(self):
        with mp.Pool(processes=self.workers) as pool:
            for one in pool.imap_unordered(self.mine_files,
                                           self.log_miner.get_target_files(self.targets, self.modules)):
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
