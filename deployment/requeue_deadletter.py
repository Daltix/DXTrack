import boto3
import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    '-s', '--stage', help='The stage', type=str, required=True
)
parser.add_argument(
    '-n', '--n_messages', help='Max number to requeue', type=int, default=1
)


def requeue(stage, n_messages):
    sqs = boto3.resource('sqs')
    q_name = 'dxtrack-jsonl-file-queue-{}'.format(stage)
    dlq_name = 'dxtrack-deadletter-jsonl-file-queue-{}'.format(stage)
    q = sqs.get_queue_by_name(QueueName=q_name)
    dlq = sqs.get_queue_by_name(QueueName=dlq_name)
    count = 0
    stop = False

    while True:
        failed_messages = dlq.receive_messages()
        if not failed_messages or stop:
            break
        for failed_message in failed_messages:
            count += 1
            q.send_message(MessageBody=failed_message.body)
            failed_message.delete()
            if count == n_messages:
                stop = True
                break
    print('requeued {} messages'.format(count))


if __name__ == '__main__':
    args = parser.parse_args()
    requeue(args.stage, args.n_messages)
