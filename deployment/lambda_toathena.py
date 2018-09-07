import os
import botocore
import boto3
from deployment.partition_and_write import partition_and_write

STAGE = os.environ.get('STAGE', 'dev')
ERROR_TABLE_NAME = os.environ['ERROR_TABLE_NAME']
METRIC_TABLE_NAME = os.environ['METRIC_TABLE_NAME']
DB_NAME = os.environ['DB_NAME']
BUCKET_NAME = os.environ['BUCKET_NAME']

athena = boto3.client('athena')
sqs = boto3.resource('sqs')
s3 = boto3.client('s3')
bucket = boto3.resource('s3').Bucket(BUCKET_NAME)


def _read_queue_messages(event):
    s3_input_locations = []
    for record in event['Records']:
        s3_input_locations.append(record['body'])

    return s3_input_locations


def _load_new_partitions(table_name):
    # need to run this in case files were written that introduce new
    # partition values
    athena.start_query_execution(
        QueryString='MSCK REPAIR TABLE {}.{}'.format(DB_NAME, table_name),
        ResultConfiguration={
            'OutputLocation': 's3://{}/athena-output'.format(BUCKET_NAME),
            'EncryptionConfiguration': {
                'EncryptionOption': 'SSE_S3'
            }
        }
    )


def _try_delete(key):
    print('deleting {}'.format(key))
    try:
        s3.delete_object(
            Bucket=BUCKET_NAME,
            Key=key.replace('s3://{}/'.format(BUCKET_NAME), '')
        )
    except botocore.exceptions.ClientError:
        print('could not delete {} because not found'.format(key))


def main(event, *_):
    s3_input_locations = _read_queue_messages(event)
    for s3_input_location in s3_input_locations:
        if 'error' in s3_input_location:
            table_name = ERROR_TABLE_NAME
        elif 'metric' in s3_input_location:
            table_name = METRIC_TABLE_NAME
        else:
            raise ValueError(
                'dont know where to send {}'.format(s3_input_location)
            )
        partition_and_write(
            input_files=[s3_input_location],
            output_prefix='s3://{}/{}'.format(BUCKET_NAME, table_name)
        )
        _load_new_partitions(table_name)
    for key in s3_input_locations:
        _try_delete(key)
