"""Small application contract plus an explicit REST-Gateway boundary model."""
import json


class ContractError(ValueError):
    pass


def request_body(value):
    if not isinstance(value, dict) or set(value) != {"quantity"}:
        raise ContractError("quantity required, no extra fields")
    if type(value["quantity"]) is not int or not 1 <= value["quantity"] <= 10:
        raise ContractError("quantity must be an integer from 1 to 10")


def response_body(value):
    if not isinstance(value, dict) or set(value) != {"total_cents"}:
        raise ContractError("total_cents required, no extra fields")
    if type(value["total_cents"]) is not int or value["total_cents"] < 0:
        raise ContractError("total_cents must be a nonnegative integer")


def edge_request(body, content_type, query, default_model=False):
    """Only the documented teaching subset; not an AWS emulator or JSON Schema engine."""
    if not query.get("limit"):
        return 400
    if content_type == "application/json" or default_model:
        try:
            request_body(json.loads(body))
        except (ValueError, TypeError):
            return 400
    return None


def envelope(status, body):
    return {"statusCode": status, "headers": {"Content-Type": "application/json"}, "body": json.dumps(body)}


def application(body, content_type, query, provider):
    if content_type != "application/json":
        return envelope(415, {"error": "unsupported_media_type"})
    try:
        value = json.loads(body)
        request_body(value)
        limit = query.get("limit", "")
        if not limit.isascii() or not limit.isdigit() or not 1 <= int(limit) <= 100:
            raise ContractError("limit must be integer from 1 to 100")
    except (ValueError, TypeError, AttributeError):
        return envelope(400, {"error": "invalid_request"})
    result = provider(value["quantity"])
    try:
        response_body(result)
    except ContractError:
        # Do not leak the malformed provider payload as an apparent success.
        return envelope(502, {"error": "invalid_provider_response"})
    return envelope(200, result)


def proxy_passthrough(result):
    """Envelope subset only; body schema is deliberately NOT checked here."""
    if not isinstance(result, dict) or type(result.get("statusCode")) is not int or not isinstance(result.get("body"), str):
        return 502, {"error": "invalid_integration_envelope"}
    return result["statusCode"], json.loads(result["body"])
