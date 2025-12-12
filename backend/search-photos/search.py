import json
import os
import logging
import boto3
import urllib.parse
import urllib.request

from botocore.awsrequest import AWSRequest
from botocore.auth import SigV4Auth

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# --------------------------
# ENVIRONMENT VARIABLES
# --------------------------
ES_ENDPOINT = os.environ["ES_ENDPOINT"].rstrip("/")
ES_INDEX = os.environ.get("ES_INDEX", "photos")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
ES_SERVICE = "es"

# LEX V2 CONFIGURATION
BOT_ID = os.environ["BOT_ID"]
BOT_ALIAS_ID = os.environ["BOT_ALIAS_ID"]
LOCALE_ID = "en_US"

lex = boto3.client("lexv2-runtime")


# --------------------------
# SIGN OPENSEARCH REQUEST
# --------------------------
def sign_and_send_es(method, path, body_dict):
    body = json.dumps(body_dict).encode("utf-8")
    url = ES_ENDPOINT + path

    session = boto3.Session()
    credentials = session.get_credentials().get_frozen_credentials()

    request = AWSRequest(
        method=method,
        url=url,
        data=body,
        headers={"Content-Type": "application/json"}
    )
    SigV4Auth(credentials, ES_SERVICE, AWS_REGION).add_auth(request)
    signed_headers = dict(request.headers.items())

    req = urllib.request.Request(url, data=body, headers=signed_headers, method=method)

    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


# --------------------------
# EXTRACT LABELS USING LEX V2 (FIXED VERSION)
# --------------------------
def extract_labels_from_lex(query):
    query_lc = query.lower()

    try:
        response = lex.recognize_text(
            botId=BOT_ID,
            botAliasId=BOT_ALIAS_ID,
            localeId=LOCALE_ID,
            sessionId="user123",
            text=query
        )

        interpreted = response.get("interpretations", [])
        labels = []

        for interp in interpreted:
            slots = interp.get("intent", {}).get("slots", {})
            for slot_name, slot_val in slots.items():
                if slot_val and "value" in slot_val:
                    labels.append(slot_val["value"]["interpretedValue"].lower())

        # ⭐ FIXED: FALLBACK WHEN LEX RETURNS NO LABELS
        if not labels:
            tokens = query_lc.split()
            stop = {"show", "me", "photos", "with", "and", "in"}
            labels = [t for t in tokens if t not in stop]

        return list(dict.fromkeys(labels))

    except Exception as e:
        logger.error("Lex error: %s", e)

        # Fallback if Lex API call fails entirely
        tokens = query_lc.split()
        stop = {"show", "me", "photos", "with", "and", "in"}
        return [t for t in tokens if t not in stop]


# --------------------------
# MAIN LAMBDA HANDLER
# --------------------------
def lambda_handler(event, context):
    logger.info("EVENT: %s", json.dumps(event))

    q = None
    if "q" in event:
        q = event["q"]
    elif event.get("queryStringParameters"):
        q = event["queryStringParameters"].get("q")

    if not q:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing query parameter q"}),
            "headers": {"Access-Control-Allow-Origin": "*"}
        }

    labels = extract_labels_from_lex(q)
    logger.info("Extracted labels: %s", labels)

    if not labels:
        return {
            "statusCode": 200,
            "body": json.dumps({"results": []}),
            "headers": {"Access-Control-Allow-Origin": "*"}
        }

    # --------------------------
    # DEBUG LOG TO CONFIRM NEW CODE IS RUNNING
    # --------------------------
    logger.info("USING KEYWORD QUERY")

    # --------------------------
    # CORRECTED OPENSEARCH QUERY
    # --------------------------
    query_body = {
        "query": {
            "terms": {
                "labels.keyword": labels
            }
        }
    }

    es_path = f"/{ES_INDEX}/_search"

    try:
        es_response = sign_and_send_es("POST", es_path, query_body)
        hits = es_response.get("hits", {}).get("hits", [])

        results = []
        for hit in hits:
            src = hit["_source"]
            bucket = src["bucket"]
            object_key = src["objectKey"]
            url = f"https://{bucket}.s3.amazonaws.com/{urllib.parse.quote(object_key)}"

            results.append({
                "objectKey": object_key,
                "bucket": bucket,
                "labels": src["labels"],
                "url": url
            })

        return {
            "statusCode": 200,
            "body": json.dumps({"results": results}),
            "headers": {"Access-Control-Allow-Origin": "*"}
        }

    except Exception as e:
        logger.error("Search error: %s", e)
        return {
            "statusCode": 500,
            "body": json.dumps({"results": []}),
            "headers": {"Access-Control-Allow-Origin": "*"}
        }

