import shutil
import os
import json
import unittest
from datetime import datetime
from dxtrack import dxtrack
from dxtrack.dxtrack_impl import test_output_metric_file

context = 'test_metric_track'
stage = 'test'
run_id = 'test_run_id'
default_metadata = {'default': 'metadata'}


class TestErrorTrack(unittest.TestCase):

    def _setup(self, buffer_metrics=False):
        shutil.rmtree(test_output_metric_file, ignore_errors=True)

        dxtrack.configure(
            context=context,
            stage=stage,
            run_id=run_id,
            default_metadata=default_metadata,
            buffer_metrics=buffer_metrics
        )

    def tearDown(self):
        shutil.rmtree(os.path.dirname(test_output_metric_file))

    def test_metric_raw_output(self):
        self._setup()
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
        self.assertEqual(metric['metadata'], default_metadata)

    def test_metrics_buffering(self):
        self._setup(buffer_metrics=True)
        dxtrack.metric('test.metric', 1)
        self.assertFalse(os.path.exists(test_output_metric_file))
        dxtrack.metric('test.metric', 2)
        self.assertFalse(os.path.exists(test_output_metric_file))
        dxtrack.flush_metrics_buffer()
        self.assertTrue(os.path.exists(test_output_metric_file))
        with open(test_output_metric_file) as fh:
            metrics = [
                json.loads(line)
                for line in fh.readlines()
            ]
        self.assertEqual(len(metrics), 2)

    def test_metric_valid_values(self):
        self._setup(buffer_metrics=True)
        with self.assertRaises(ValueError) as e:
            dxtrack.metric('test.metric', 'abcd')
        self.assertIn('Unable to cast metric', str(e.exception))

    def test_metric_with_explicit_timestamp(self):
        self._setup()
        timestamp = datetime(year=1985, month=11, day=20)
        dxtrack.metric('test.metric', 1, timestamp=timestamp)
        with open(test_output_metric_file) as fh:
            metric = json.loads(fh.read())
        self.assertEqual(metric['timestamp'], '1985-11-20 00:00:00.000000')

        with self.assertRaises(ValueError) as e:
            dxtrack.metric('test.metric', 1, timestamp='2019-01-01')
        self.assertIn(
            'timestamp must be an instance of datetime.datetime',
            str(e.exception)
        )


if __name__ == '__main__':
    unittest.main()
