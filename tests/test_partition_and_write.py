import os
import glob
import shutil
import unittest
from deployment import partition_and_write


output_dir = './tests/output/'


class TestParseWritePromos(unittest.TestCase):

    def tearDown(self):
        shutil.rmtree(output_dir, ignore_errors=True)

    def setUp(self):
        shutil.rmtree(output_dir, ignore_errors=True)

    def test_write_single_file(self):
        output_file = '{}/output.csv'.format(output_dir)
        parse_write_promos(
            input_files=['tests/resources/brico.jsonl'],
            output_file=output_file
        )
        self.assertTrue(os.path.exists(output_file))
        promos_df = pd.read_csv(
            output_file, names=COLUMNS, sep=';')
        self.assertEqual(promos_df.shape, (28, 34))
        self.assertEqual(promos_df.product_id.nunique(), 26)

    def _test_write_partitioned(self):
        parse_write_promos(
            input_files=['tests/resources/brico.jsonl'],
            output_prefix=output_dir
        )
        partitions = os.listdir(output_dir)
        self.assertEqual(
            {'downloaded_on_date=2018-06-16', 'downloaded_on_date=2018-09-01'},
            set(partitions)
        )
        output_files = glob.glob('{}/**/**.csv'.format(output_dir))
        df1 = pd.read_csv(output_files[0], names=COLUMNS, sep=';')
        df2 = pd.read_csv(output_files[1], names=COLUMNS, sep=';')

        self.assertEqual(df1.shape[0] + df2.shape[0], 28)
        self.assertEqual(
            df1.product_id.nunique() + df2.product_id.nunique(),
            26
        )


if __name__ == '__main__':
    unittest.main()