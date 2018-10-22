import os
import sys
import traceback
import copy
from datetime import datetime
import json
import hashlib
import boto3
from .papertrail import setup_papertrail

DT_FORMAT = '%Y-%m-%d %H:%M:%S.%f'
valid_stages = {'test', 'dev', 'prod'}
test_output_err_file = './.dxtrack_output/error.jsonl'
test_output_metric_file = './.dxtrack_output/metric.jsonl'

err_fhose_name = 'dxtrack-error-input-{}'
metric_fhose_name = 'dxtrack-metric-input-{}'


def _hash_str(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


class DXTrack:

    context = None
    stage = None
    run_id = None
    default_metadata = None
    _is_configured = False
    _err_fhose_name = None
    _metric_fhose_name = None
    _kinesis_client = None
    _session = None
    _err_buffer = []
    _metric_buffer = []
    # whether or not to send metrics immediately or keep them in a buffer
    # until flush_metrics_buffer()
    _buffer_metrics = None
    _papertrail_logger = None

    def configure(self, context, stage, run_id, default_metadata=None,
                  profile_name=None, aws_access_key_id=None,
                  aws_secret_access_key=None, buffer_metrics=False,
                  papertrail_hostport=None):
        if aws_access_key_id and aws_secret_access_key:
            self._session = boto3.Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key)
        else:
            # if profile is not specified, boto will try to use the
            # 'default' profile
            self._session = boto3.Session(profile_name=profile_name)

        self._kinesis_client = self._session.client(
            'firehose',
            region_name='eu-west-1',
        )
        self.context = context
        self.stage = stage
        self.run_id = run_id
        self.default_metadata = default_metadata or {}
        self._validate_setup()
        # self._configure_sys_excepthook()
        self._err_fhose_name = err_fhose_name.format(self.stage)
        self._metric_fhose_name = metric_fhose_name.format(self.stage)
        self._setup_output()
        self._is_configured = True
        self._buffer_metrics = buffer_metrics
        if papertrail_hostport:
            self._papertrail_logger = setup_papertrail(papertrail_hostport)

    def error(self, metadata=None):
        if not self._is_configured:
            print('dxtrack is not configured')
            return
        try:
            self._error(metadata)
            self._send_errs()
        except Exception as e:
            # normally would never catch Exception but this is a special case
            # because we should never, in any case, halt execution if this
            # function is not working
            print('Error calling dxtrack.error {}'.format(e))

    def errors(self, errors, metadata=None):
        self._validate_metadata(metadata)
        for error in errors:
            self._buffer_err(type(error), error, None, metadata=metadata)
        self._send_errs()

    def _error(self, metadata):
        self._validate_metadata(metadata)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        self._buffer_err(exc_type, exc_value, exc_traceback, metadata)

    def metric(self, metric_name, value, metadata=None):
        if not self._is_configured:
            print('dxtrack is not configured')
            return
        try:
            self._metric(metric_name, value, metadata)
        except Exception as e:
            # normally would never catch Exception but this is a special case
            # because we should never, in any case, halt execution if this
            # function is not working
            print('Error calling dxtrack.metric {}'.format(e))

    def flush_metrics_buffer(self):
        self._send_metrics()

    def _metric(self, metric_name, value, metadata):
        self._validate_metadata(metadata)
        md = copy.deepcopy(self.default_metadata)
        md.update(metadata or {})
        metric_dict = self._base_raw_output(md)
        metric_dict['metric_name'] = metric_name
        metric_dict['value'] = value
        metric_dict['id'] = _hash_str(json.dumps(metric_dict))
        self._metric_buffer.append(metric_dict)
        if not self._buffer_metrics:
            self._send_metrics()
        if self._papertrail_logger:
            self._papertrail_logger.info('{}-{}-{}'.format(
                metric_name, value, str(metadata)))

    def _buffer_err(self, exc_type, exc_value, exc_traceback, metadata=None):
        err_dict = self._create_err_dict(
            exc_type, exc_value, exc_traceback, metadata)
        if self._papertrail_logger:
            exc_part = err_dict['exception']
            self._papertrail_logger.error('{} {}\n{}\n{}'.format(
                exc_part['type'], exc_part.get('value'), exc_part['traceback'],
                str(metadata)))
        self._err_buffer.append(err_dict)

    def _send_errs(self):
        self._write_out(
            self._err_buffer, test_output_err_file, self._err_fhose_name
        )
        self._err_buffer = []

    def _send_metrics(self):
        self._write_out(
            self._metric_buffer, test_output_metric_file,
            self._metric_fhose_name
        )
        self._metric_buffer = []

    def _write_out(self, arr_of_dict, fname, fhose_name):
        entries = [json.dumps(entry) for entry in arr_of_dict]
        if self.stage == 'test':
            with open(fname, 'w') as fh:
                fh.write('\n'.join(entries))
        else:
            self._kinesis_client.put_record_batch(
                DeliveryStreamName=fhose_name,
                Records=[
                    {'Data': entry + '\n'}
                    for entry in entries
                ]
            )

    def _create_err_dict(
            self, exc_type, exc_value, exc_traceback, metadata=None):
        obj = self._base_raw_output(metadata)
        if exc_traceback:
            exc_traceback = '\n'.join(traceback.format_tb(exc_traceback))
        exception_dict = {
            'type': str(exc_type.__name__),
            'value': str(exc_value),
            'traceback': exc_traceback
        }
        obj.update({
            'exception': exception_dict
        })
        obj['id'] = _hash_str(json.dumps(obj))
        return obj

    def _base_raw_output(self, metadata=None):
        merged_metadata = copy.deepcopy(self.default_metadata)
        if metadata:
            merged_metadata.update(metadata)
        return {
            'context': self.context,
            'stage': self.stage,
            'run_id': self.run_id,
            'metadata': merged_metadata,
            'timestamp': datetime.utcnow().strftime(DT_FORMAT)
        }

    # This is scary stuff, let's just not do this for now
    #
    # def _configure_sys_excepthook(self):
    #     old_excepthook = sys.excepthook
    #
    #     def _excepthook(exc_type, exc_value, exc_traceback):
    #         self._buffer_err(exc_type, exc_value, exc_traceback)
    #         self._cleanup()
    #         if old_excepthook:
    #             old_excepthook(exc_type, exc_value, exc_traceback)
    #
    #     sys.excepthook = _excepthook

    def _setup_output(self):
        if self.stage == 'test':
            os.makedirs(os.path.dirname(test_output_err_file), exist_ok=True)
            os.makedirs(
                os.path.dirname(test_output_metric_file), exist_ok=True)

    def _validate_setup(self):
        if self.stage not in valid_stages:
            raise ValueError(
                'stage expected to be one of {}, given {} instead'.format(
                    valid_stages, self.stage)
            )

        if not isinstance(self.context, str):
            raise ValueError('context is required to be a string')
        if not isinstance(self.stage, str):
            raise ValueError('stage is required to be a string')
        if not isinstance(self.run_id, str):
            raise ValueError('run_id is required to be a string')
        self._validate_metadata(self.default_metadata)

    def _validate_metadata(self, metadata):
        if metadata is not None and not isinstance(metadata, dict):
            raise ValueError('default_metadata is required to be a dict')
