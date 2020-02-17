import dill
import inspect
from base64 import b64encode
from enum import Enum


class ConditionActionModel:
    pass


class DefaultConditions(ConditionActionModel, Enum):
    TRUE = {'name': 'TRUE'}
    FUNCTION_JOIN = {'name': 'FUNCTION_JOIN'}
    COUNTER_THRESHOLD = {'name': 'COUNTER_THRESHOLD'}


class DefaultActions(ConditionActionModel, Enum):
    PASS = {'name': 'PASS'}
    TERMINATE = {'name': 'TERMINATE'}
    IBM_CF_INVOKE_KAFKA = {'name': 'IBM_CF_INVOKE_KAFKA'}
    IBM_CF_INVOKE_RABBITMQ = {'name': 'IBM_CF_INVOKE_RABBITMQ'}
    AWS_LAMBDA_INVOKE = {'name': 'AWS_LAMBDA_INVOKE'}


class DockerImage(ConditionActionModel):
    def __init__(self, image: str, class_name: str):
        self.value = {'name': 'DOCKER_IMAGE',
                      'image': image,
                      'class_name': class_name}


class PythonCallable(ConditionActionModel):
    def __init__(self, function: callable):

        try:
            assert inspect.isfunction(function)
            assert set(inspect.signature(function).parameters.keys()).issubset({'context', 'event'})
        except AssertionError:
            raise Exception('Function must be a callable and fulfil signature (context, event)')

        pickled_callable = dill.dumps(function)
        encoded_callable = b64encode(pickled_callable).decode('utf-8')

        self.value = {'name': 'PYTHON_CALLABLE',
                      'callable': encoded_callable}
