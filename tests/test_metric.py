import shutil
import os
import json
import unittest
from dxtrack import dxtrack
from dxtrack.dxtrack_impl import test_output_metric_file

context = 'test_metric_track'
stage = 'test'
run_id = 'test_run_id'
default_metadata = {'default': 'metadata'}


class TestErrorTrack(unittest.TestCase):

    def setUp(self):
        shutil.rmtree(test_output_metric_file, ignore_errors=True)

        dxtrack.configure(
            context=context,
            stage=stage,
            run_id=run_id,
            default_metadata=default_metadata
        )

    # def tearDown(self):
    #     shutil.rmtree(os.path.dirname(test_output_metric_file))

    def test_metric_raw_output(self):
        dxtrack.metric('test.metric', 1)
        with open(test_output_metric_file) as fh:
            metric = json.loads(fh.read())
        self.assertTrue(os.path.exists(test_output_metric_file))
        self.assertEqual(
            {
                'context',
                'metric_name',
                'stage',
                'run_id',
                'timestamp',
                'metadata',
                'id',
                'value'
             },
            set(metric.keys())
        )
        self.assertEqual(metric['context'], context)
        self.assertEqual(metric['metric_name'], 'test.metric')
        self.assertEqual(metric['run_id'], run_id)
        self.assertEqual(metric['stage'], stage)
        self.assertEqual(metric['value'], 1)


if __name__ == '__main__':
    unittest.main()
