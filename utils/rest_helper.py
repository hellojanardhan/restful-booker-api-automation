import json

from utils.logger import get_logger


def _serialize(value):
    if value is None:
        return "None"
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return value
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, separators=(",", ":"), default=str)
    return str(value)


def _url_for_log(endpoint, params):
    if not params:
        return endpoint

    pairs = params.items() if isinstance(params, dict) else params
    raw_query = "&".join(
        f"{key}={item}"
        for key, value in pairs
        for item in (value if isinstance(value, (list, tuple)) else [value])
    )
    separator = "&" if "?" in endpoint else "?"
    return f"{endpoint}{separator}{raw_query}"


class RestHelper:

    def __init__(self, request_context):
        self.request_context = request_context
        self.logger = get_logger(self.__class__.__name__)

    def execute(self, method, endpoint, **kwargs):

        method = method.upper().strip()
        params = kwargs.get("params")
        url = _url_for_log(endpoint, params)
        payload = kwargs.get("data")
        if payload is None:
            payload = kwargs.get("form", kwargs.get("multipart"))
        self.logger.info("%s : %s", method, url)
        self.logger.info("Request  : %s", _serialize(payload))

        try:
            if method == "GET":
                response = self.request_context.get(endpoint, **kwargs)
            elif method == "POST":
                response = self.request_context.post(endpoint, **kwargs)
            elif method == "PUT":
                response = self.request_context.put(endpoint, **kwargs)
            elif method == "PATCH":
                response = self.request_context.patch(endpoint, **kwargs)
            elif method == "DELETE":
                response = self.request_context.delete(endpoint, **kwargs)
            else:
                raise ValueError(f"Unsupported HTTP Method: {method}")

            response_body = response.body()
            try:
                response_body = json.loads(response_body)
            except (json.JSONDecodeError, UnicodeDecodeError):
                response_body = response_body.decode("utf-8", errors="replace")

            self.logger.info(
                "Response : %s\n%s\n",
                response.status,
                _serialize(response_body),
            )
            return response
        except Exception:
            self.logger.exception("%s request to %s failed", method, url)
            raise
