"""Run explicitly against a disposable bucket; this uploads a small billable object."""
import os
import urllib.request
import boto3


def main():
    bucket = os.environ['LAB_UPLOAD_BUCKET']
    client = boto3.client('s3', region_name='us-east-1')
    payload = b'Learning direct uploads.\n'
    url = client.generate_presigned_url('put_object', Params={
        'Bucket': bucket, 'Key': 'learning/demo.txt', 'ContentType': 'text/plain',
    }, ExpiresIn=60)
    request = urllib.request.Request(url, data=payload, method='PUT', headers={'Content-Type':'text/plain'})
    with urllib.request.urlopen(request, timeout=20) as response:
        assert response.status == 200
    obj = client.get_object(Bucket=bucket, Key='learning/demo.txt')
    with obj['Body'] as body:
        assert body.read() == payload
    print('Uploaded and verified learning/demo.txt; follow the cleanup steps.')


if __name__ == '__main__':
    main()
