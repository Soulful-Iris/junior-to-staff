"""SQS worker: the effect is ONE conditional DynamoDB result item, no external side effect."""
import hashlib
import json
import os
import re


class Conflict(Exception):
    pass


def parse_job(body):
    job = json.loads(body)
    if not isinstance(job, dict) or set(job) != {'operation_id', 'numbers'}:
        raise ValueError('expected operation_id and numbers only')
    key, numbers = job['operation_id'], job['numbers']
    if not isinstance(key, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', key):
        raise ValueError('invalid operation id')
    if not isinstance(numbers, list) or len(numbers) > 1000 or any(type(n) is not int or abs(n) > 10**9 for n in numbers):
        raise ValueError('numbers must be <=1000 bounded integers')
    canonical = json.dumps(numbers, separators=(',', ':'))
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    return key, digest, sum(numbers)


class DynamoStore:
    def __init__(self, client, table):
        self.client, self.table = client, table

    def save(self, key, digest, result):
        try:
            self.client.put_item(
                TableName=self.table,
                Item={'operation_id': {'S': key}, 'digest': {'S': digest}, 'result': {'N': str(result)}},
                ConditionExpression='attribute_not_exists(operation_id)',
            )
            return 'created'
        except Exception as error:
            code = getattr(error, 'response', {}).get('Error', {}).get('Code')
            if code != 'ConditionalCheckFailedException':
                raise
        existing = self.client.get_item(
            TableName=self.table, Key={'operation_id': {'S': key}}, ConsistentRead=True,
        ).get('Item')
        if not existing or existing.get('digest', {}).get('S') != digest:
            raise Conflict('operation id reused with different payload or missing result')
        return 'duplicate'


def process_batch(event, store):
    failures = []
    for record in event['Records']:
        try:
            key, digest, result = parse_job(record['body'])
            store.save(key, digest, result)
        except Exception as error:
            # Do not log payloads. The batch item id is useful for diagnosis.
            print(json.dumps({'messageId': record['messageId'], 'errorType': type(error).__name__}))
            failures.append({'itemIdentifier': record['messageId']})
    return {'batchItemFailures': failures}


def handler(event, context):
    import boto3
    return process_batch(event, DynamoStore(boto3.client('dynamodb'), os.environ['RESULT_TABLE']))
