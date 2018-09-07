import os
import boto3

sqs = boto3.resource('sqs')

queue = sqs.get_queue_by_name(QueueName=os.environ['QUEUE_NAME'])


def _main(event):
    for record in event['Records']:
        queue.send_message(
            MessageBody='s3://{}/{}'.format(
                record['s3']['bucket']['name'],
                record['s3']['object']['key']
            )
        )


def main(event, _):
    _main(event)
