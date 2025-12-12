import json
import os
import logging
import boto3
import datetime
import urllib.parse
import urllib.request

from botocore.awsrequest import AWSRequest
from botocore.auth import SigV4Auth

logger = logging.getLogger()
logger.setLevel(logging.INFO)

rekognition = boto3.client('rekognition')
s3 = boto3.client('s3')

ES_ENDPOINT = os.environ['ES_ENDPOINT'].rstrip('/')
ES_INDEX = os.environ.get('ES_INDEX', 'photos')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
ES_SERVICE = 'es'   # OpenSearch service ID


# --------------------------
# SIGN HTTP REQUEST TO OPENSEARCH
# --------------------------
def sign_and_send_es(method, path, body_dict):
    body = json.dumps(body_dict).encode('utf-8')
    url = ES_ENDPOINT + path

    session = boto3.Session()
    credentials = session.get_credentials().get_frozen_credentials()

    request = AWSRequest(
        method=method,
        url=url,
        data=body,
        headers={'Content-Type': 'application/json'}
    )

    SigV4Auth(credentials, ES_SERVICE, AWS_REGION).add_auth(request)

    signed_headers = dict(request.headers.items())
    req = urllib.request.Request(
        url,
        data=body,
        headers=signed_headers,
        method=method
    )

    with urllib.request.urlopen(req) as resp:
        resp_body = resp.read()
        logger.info("ES status: %s", resp.status)
        logger.info("ES response: %s", resp_body.decode('utf-8'))


# --------------------------
# GET LABELS FROM REKOGNITION
# --------------------------
def get_labels_from_rekognition(bucket, key):
    try:
        response = rekognition.detect_labels(
            Image={'S3Object': {'Bucket': bucket, 'Name': key}},
            MaxLabels=10,
            MinConfidence=75
        )
        labels = [lbl['Name'].lower() for lbl in response.get('Labels', [])]
        return labels
    except Exception as e:
        logger.error("Rekognition error: %s", e, exc_info=True)
        return []


# --------------------------
# GET CUSTOM LABELS FROM S3 OBJECT METADATA
# --------------------------
def get_custom_labels(bucket, key):
    try:
        head = s3.head_object(Bucket=bucket, Key=key)
        metadata = head.get('Metadata', {})
        raw = metadata.get('customlabels')   # header: x-amz-meta-customlabels
        if not raw:
            return []
        return [
            label.strip().lower()
            for label in raw.split(',')
            if label.strip()
        ]
    except Exception as e:
        logger.error("Metadata read error: %s", e, exc_info=True)
        return []


# --------------------------
# MAIN LAMBDA HANDLER
# --------------------------
def handler(event, context):
    logger.info("Incoming Event: %s", json.dumps(event))

    for record in event.get('Records', []):
        bucket = record['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(record['s3']['object']['key'])

        # 1. Rekognition labels
        auto_labels = get_labels_from_rekognition(bucket, key)

        # 2. Custom labels
        custom_labels = get_custom_labels(bucket, key)

        # Combine labels
        all_labels = sorted(set(auto_labels + custom_labels))

        # Assignment-required JSON document:
        doc = {
            "objectKey": key,
            "bucket": bucket,
            "createdTimestamp": datetime.datetime.utcnow().isoformat(),
            "labels": all_labels
        }

        logger.info("Document to index: %s", json.dumps(doc))

        # Use URL-encoded S3 key as ID
        doc_id = urllib.parse.quote(key, safe="")
        path = f"/{ES_INDEX}/_doc/{doc_id}"

        try:
            sign_and_send_es("PUT", path, doc)
        except Exception as e:
            logger.error("Error indexing doc: %s", e, exc_info=True)

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "OK"})
    }

