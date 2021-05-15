import multiprocessing as mp
import os
import sys


class LogEngine:
    def __init__(self, log_miner, log_analyzer, log_writer, targets=None, modules=None, workers=None, name_only=False,
                 subscribe=False, limit=None, distinct=None, window=None, time_window=None, include_history=None):
        # rguments = ['subscribe', 'order_by', 'analyze', 'format', 'limit', 'full', 'reverse', 'name_only', 'workers']
        self.log_miner = log_miner  # mapper
        self.log_analyzer = log_analyzer  # reducer
        self.log_writer = log_writer
        self.targets = targets
        self.modules = modules if not modules else modules.split(',')
        self.name_only = name_only
        self.workers = workers if workers else os.cpu_count()
        self.subscribe = subscribe
        self.limit = limit
        self.distinct = distinct.split(',') if distinct else []
        self.include_history = include_history

        if window is not None:
            self.window = window
        else:
            if self.log_analyzer.need_reduce():
                # max windows size
                self.window = sys.maxsize
            else:
                self.window = 1

        # for future usage
        self.time_window = time_window if not time_window else 0

    def mine_files(self, files):
        if isinstance(files, str):
            files = [files]
        return list(self.log_miner.mine_files(files))

    def mining_files(self, files, queue):
        for one in self.log_miner.mining_files(files, self.include_history):
            queue.put(one)

    def run(self):
        if self.name_only:
            for one in self.log_miner.get_target_files(self.targets, self.modules):
                print(one)

            return

        total_counter = 0
        batch_counter = 0
        existing_records = set()
        batch_results = []

        for one in self.execute():
            if self.limit and total_counter >= self.limit:
                break

            if self.distinct:
                the_distinct_values = tuple([one.get(column) for column in self.distinct])
                if the_distinct_values in existing_records:
                    continue
                else:
                    existing_records.add(the_distinct_values)

            # accumulate records
            total_counter = total_counter + 1
            batch_counter = batch_counter + 1
            batch_results.append(one)

            if batch_counter == self.window:
                # hit window size then flush windows

                self.log_writer.write(self.log_analyzer.analyze(batch_results))
                # reset
                batch_counter = 0
                batch_results.clear()

        else:
            # flush content
            self.log_writer.write(self.log_analyzer.analyze(batch_results))

    def execute(self):
        if self.workers == 1:
            for one in self.execute1():
                yield one

        if self.subscribe:
            # stream mode
            for one in self.run_in_multi_streams():
                yield one

        else:
            for one in self.run_in_multi_batches():
                yield one

    def execute1(self):
        if self.subscribe:
            return self.log_miner.mining_files(self.log_miner.get_target_files(self.targets, self.modules))
        else:
            return self.log_miner.mine_files(self.log_miner.get_target_files(self.targets, self.modules))

    def run_in_multi_batches(self):
        with mp.Pool(processes=self.workers) as pool:
            for one in pool.imap_unordered(self.mine_files,
                                           self.log_miner.get_target_files(self.targets, self.modules)):
                try:
                    for item in one:
                        yield item
                except Exception as error:
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
            yield queue.get()
