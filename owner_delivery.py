"""One bounded delivery attempt; never logs Telegram credentials or response text."""
import json
from urllib.error import HTTPError
from owner_notifications import claim_delivery, mark_delivered, release_delivery, format_delivery


def deliver_one(connect, send, admin):
    with connect() as conn:
        item = claim_delivery(conn)
    if item is None:
        return False
    try:
        result = send(admin, format_delivery(item))
        if not isinstance(result, dict) or not isinstance(result.get("message_id"), int):
            raise ValueError("missing Telegram receipt")
    except Exception as exc:
        code = None
        retry_after = None
        if isinstance(exc, HTTPError):
            code = exc.code
            try:
                payload = json.loads(exc.read(65536))
                retry_after = payload.get("parameters", {}).get("retry_after")
                if not isinstance(retry_after, (int, float)):
                    retry_after = None
            except (ValueError, OSError):
                pass
        with connect() as conn:
            release_delivery(conn, item[0], error=("HTTP_" + str(code)) if code else type(exc).__name__,
                             retry_after=retry_after, permanent=code in (400, 401, 403, 404))
        return False
    with connect() as conn:
        mark_delivered(conn, item[0], message_id=result["message_id"])
    return True
