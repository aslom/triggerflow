import uuid
import boto3

from jsonpath_ng import parse, jsonpath
from datetime import datetime


def action_aws_asf_pass(context, event):
    if 'Result' in context['State'] and 'ResultPath' in context['State']:
        exp = parse(context['State']['ResultPath'])
        if not exp.find(context['global_context']):
            raise Exception('Result path not found in global context')
        else:
            exp.update(context['global_context'], context['State']['Result'])

    termination_cloudevent = {'specversion': '1.0',
                              'id': uuid.uuid4().hex,
                              'source': '/'.join(['local', context['namespace'], context['trigger_id']]),
                              'type': 'termination.event.success',
                              'time': str(datetime.utcnow().isoformat()),
                              'subject': context['subject']}

    context['local_event_queue'].put(termination_cloudevent)


def action_aws_asf_task(context, event):
    if 'lambda' not in context['State']['Resource']:
        raise NotImplementedError()

    # TODO ensure lambda funct has a sqs topic destination configured
    boto3_client = boto3.client('lambda',
                                aws_access_key_id=context['global_context']['aws']['access_key_id'],
                                aws_secret_access_key=context['global_context']['aws']['secret_access_key'])

    invoke_args = {}
    for parameter_key in context['State']['Parameters']:
        if parameter_key.endswith('.$'):
            key = parameter_key[:-2]
            exp = parse(context['State']['Parameters'][parameter_key])
            match = exp.find(context['global_context'])
            if len(match) == 1:
                invoke_args[key] = match.pop().value
            elif len(match) > 1:
                invoke_args[key] = [m.value for m in match]
            else:
                invoke_args[key] = None

    boto3_client.invoke_async(FunctionName=context['State']['Resource'], InvokeArgs=invoke_args)


def action_aws_asf_map(context, event):
    exp = parse(context['State']['InputPath'])
    match = exp.find(context['global_context'])
    iterator = match.pop().value

    for element in iterator:
        termination_cloudevent = {'specversion': '1.0',
                                  'id': uuid.uuid4().hex,
                                  'source': '/'.join(['local', context['namespace'], context['trigger_id']]),
                                  'type': 'termination.event.success',
                                  'time': str(datetime.utcnow().isoformat()),
                                  'subject': context['subject'],
                                  'datacontenttype': 'application/json',
                                  'data': element}

        context['local_event_queue'].put(termination_cloudevent)

    join_sm = context['join_state_machine']
    context['triggers'][join_sm]['context']['join_multiple'] = len(iterator)


def action_aws_asf_end_statemachine(context, event):
    termination_cloudevent = {'specversion': '1.0',
                              'id': uuid.uuid4().hex,
                              'source': '/'.join(['local', context['namespace'], context['trigger_id']]),
                              'type': 'termination.event.success',
                              'time': str(datetime.utcnow().isoformat()),
                              'subject': context['subject']}

    context['local_event_queue'].put(termination_cloudevent)
