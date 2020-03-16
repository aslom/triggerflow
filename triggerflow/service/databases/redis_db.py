import redis
import time
import json


class RedisDatabase:
    max_retries = 15

    def __init__(self, host: str, port: int, password: str=None):
        self.client = redis.StrictRedis(host=host, port=port, password=password,
                                        charset="utf-8", decode_responses=True)

    def get_conn(self):
        return self.client

    def put(self, workspace: str, document_id: str, data: dict):
        redis_key = '{}-{}'.format(workspace, document_id)
        formated_data = {}
        for key in data:
            formated_data[key] = json.dumps(data[key])
        if formated_data:
            self.client.hmset(redis_key, formated_data)

    def get(self, workspace: str, document_id: str):
        redis_key = '{}-{}'.format(workspace, document_id)
        formated_data = self.client.hgetall(redis_key)
        data = {}
        for key in formated_data:
            data[key] = json.loads(formated_data[key])
        return data

    def delete(self, workspace: str, document_id: str):
        redis_key = '{}-{}'.format(workspace, document_id)
        self.client.delete(redis_key)

    def get_auth(self, username: str):
        redis_key = '$auth$'
        return self.client.hget(redis_key, username)

    def create_workspace(self, workspace):
        redis_key = '$workspaces$'
        self.client.hset(redis_key, workspace, time.time())

    def workspace_exists(self, workspace):
        redis_key = '$workspaces$'
        return self.client.hexists(redis_key, workspace)

    def delete_workspace(self, workspace):
        redis_key = '$workspaces$'

        wk = self.client.keys('{}-*'.format(workspace))
        for k in wk:
            self.client.delete(k)

        self.client.hdel(redis_key, workspace)

    def document_exists(self, workspace, document_id):
        redis_key = '{}-{}'.format(workspace, document_id)
        return self.client.exists(redis_key)

    def key_exists(self, workspace, document_id, key):
        redis_key = '{}-{}'.format(workspace, document_id)
        return self.client.hexists(redis_key, key)

    def set_key(self, workspace, document_id, key, value):
        redis_key = '{}-{}'.format(workspace, document_id)
        self.client.hset(redis_key, key, json.dumps(value))

    def get_key(self, workspace, document_id, key):
        redis_key = '{}-{}'.format(workspace, document_id)
        return json.loads(self.client.hget(redis_key, key))

    def delete_key(self, workspace, document_id, key):
        redis_key = '{}-{}'.format(workspace, document_id)
        self.client.hdel(redis_key, key)