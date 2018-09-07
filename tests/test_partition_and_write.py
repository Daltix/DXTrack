import os
import glob
import shutil
import unittest
from deployment import partition_and_write


output_dir = './tests/output/'


class TestPartitionWritePromos(unittest.TestCase):

    def tearDown(self):
        shutil.rmtree(output_dir, ignore_errors=True)

    def setUp(self):
        shutil.rmtree(output_dir, ignore_errors=True)

    def test_write_partitioned(self):
        partition_and_write(
            input_files=['tests/fixtures/error.jsonl'],
            output_prefix=output_dir
        )
        partitions = os.listdir(output_dir)
        self.assertEqual(
            {'context=test_error_track', 'context=test_another_track'},
            set(partitions)
        )
        self.assertEqual(
            os.listdir(output_dir + 'context=test_another_track/'),
            ['date=2018-09-08']
        )
        self.assertEqual(
            os.listdir(output_dir + 'context=test_error_track/'),
            ['date=2018-09-07']
        )


if __name__ == '__main__':
    unittest.main()
