import os
import time
from datetime import datetime
import json
from collections import  defaultdict
from smart_open import smart_open


TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S.%f'
DAY_FORMAT = '%Y-%m-%d'


def partition_and_write(input_files: list, output_prefix: str):
    PartitionAndWrite(
        input_files=input_files, output_prefix=output_prefix
    ).partition_and_write()


def _partition_entries(entries: list, prefix: str, output_fname: str):
    # this will write out compressed files because of the .gz at the end
    # of the filepath - smart_open magic!
    partitioned_entries = defaultdict(list)
    for entry in entries:
        date = entry['timestamp'].split(' ')[0]
        string_entry = json.dumps(entry)
        partitioned_entries[
            '{prefix}/context={context}/date={date}/{output_fname}.gz'.format(
                prefix=prefix, context=entry['context'], date=date,
                output_fname=output_fname
            )
        ].append(string_entry)
    return partitioned_entries


class PartitionAndWrite:

    def __init__(self, input_files, output_prefix=None):
        self._input_files = input_files
        self._lines_to_partition = []
        self._entry_count = 0
        self._buffer_size = 1000
        self._output_prefix = output_prefix
        self._fout = None
        self._output_fname = datetime.utcnow().strftime('%Y-%m-%d_%H%M%S%f')

    def _partition_and_write(self):

        partitioned_entries = _partition_entries(
            self._lines_to_partition, self._output_prefix, self._output_fname)

        for fname, entries in partitioned_entries.items():
            entries_str = '\n'.join(entries)
            if fname not in self._fout:
                if not fname.startswith('s3://'):
                    os.makedirs(os.path.dirname(fname), exist_ok=True)
                self._fout[fname] = smart_open(fname, 'w')
                fout = smart_open(fname)
            self._fout[fname].write(entries_str)

    def _stream_and_partition(self, file_to_stream):
        with smart_open(file_to_stream) as fin:
            for line in fin:
                line = json.loads(line)
                self._lines_to_partition.append(line)
                self._entry_count += 1
                if len(self._lines_to_partition) >= self._buffer_size:
                    self._partition_and_write()
            self._partition_and_write()

    def _close_fout(self):
        for fh in self._fout.values():
            fh.close()

    def _partition_and_write_files(self):
        self._fout = dict()
        for file_to_stream in self._input_files:
            self._stream_and_partition(file_to_stream)
        self._close_fout()

    def partition_and_write(self):
        start = time.time()
        self._partition_and_write_files()
        print('total time: {} for {} entries'.format(
            time.time() - start, self._entry_count
        ))
