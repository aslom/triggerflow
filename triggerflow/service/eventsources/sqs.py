import json
import logging
import boto3
from multiprocessing import Queue

from .model import EventSourceHook

logging.getLogger('botocore').setLevel(logging.INFO)


class SQSEventSource(EventSourceHook):
    def __init__(self,
                 event_queue: Queue,
                 region: str,
                 account: str,
                 topic: str,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.event_queue = event_queue
        self.region = region
        self.account = account
        self.topic = topic or self.name

        self.queue_url = 'https://sqs.{}.amazonaws.com/{}/{}'.format(region, account, topic)
        self.client = None

    def run(self):
        sqs = boto3.resource('sqs')  # Consumer expects queue to be publicly accessible
        queue = sqs.Queue(self.queue_url)

        while True:
            for message in queue.receive_messages(WaitTimeSeconds=10):
                termination_event = json.loads(message.body)
                payload_body = termination_event['responsePayload']['body']
                subject = payload_body.get('subject') if type(payload_body) == dict else json.loads(payload_body).get(
                    'subject')
                termination_cloudevent = {'specversion': '1.0',
                                          'id': termination_event['requestContext']['requestId'],
                                          'source': termination_event['requestContext']['functionArn'],
                                          'type': 'termination.event.{}'.format(
                                              termination_event['requestContext']['condition'].lower()),
                                          'time': termination_event['timestamp'],
                                          'subject': subject,
                                          'datacontenttype': 'application/json',
                                          'data': termination_event['responsePayload']['body']}
                self.event_queue.put(termination_cloudevent)
                # message.delete()

    def commit(self, records):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()
