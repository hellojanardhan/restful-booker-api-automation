"""Low-level HTTP execution and response logging helpers."""

import json
from typing import Any

from utils.logger import get_logger
from playwright.sync_api import Error as PlaywrightError


def _serialize(value):
    """Serialize a value into a readable log-safe representation."""
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
    """Append request parameters to an endpoint for diagnostic logging."""
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
    """Execute HTTP requests and log request and response details."""

    def __init__(self, request_context):
        """Initialize the helper with a Playwright request context."""
        self.request_context = request_context
        self.logger = get_logger(self.__class__.__name__)

    def execute(self, method, endpoint, **kwargs):
        """Execute an HTTP method and return the Playwright response."""

        if not isinstance(method, str) or not method.strip():
            raise ValueError("HTTP method must be a non-empty string")
        if not isinstance(endpoint, str) or not endpoint.strip():
            raise ValueError("API endpoint must be a non-empty string")

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
            elif method == "HEAD":
                response = self.request_context.head(endpoint, **kwargs)
            elif method == "OPTIONS":
                response = self.request_context.fetch(
                    endpoint,
                    method="OPTIONS",
                    **kwargs,
                )
            else:
                raise ValueError(f"Unsupported HTTP Method: {method}")

            try:
                response_body = response.body()
                response_body = json.loads(response_body)
            except (json.JSONDecodeError, UnicodeDecodeError):
                if isinstance(response_body, bytes):
                    response_body = response_body.decode("utf-8", errors="replace")
                else:
                    response_body = str(response_body)

            self.logger.info(
                "Response : %s\n%s\n",
                response.status,
                _serialize(response_body),
            )
            return response
        except ValueError:
            self.logger.exception("Invalid request configuration for %s %s", method, url)
            raise
        except PlaywrightError as error:
            self.logger.exception(
                "Playwright API request failed: %s %s",
                method,
                url,
            )
            raise RuntimeError(
                f"API request failed ({method} {url}): {error}"
            ) from error
        except (TimeoutError, ConnectionError, OSError) as error:
            self.logger.exception("Network error for %s %s", method, url)
            raise RuntimeError(
                f"Network error while calling {method} {url}: {error}"
            ) from error
        except Exception as error:
            self.logger.exception("%s request to %s failed", method, url)
            raise RuntimeError(
                f"Unexpected error while calling {method} {url}: {error}"
            ) from error


def parse_response_json(response: Any) -> dict:
    """Parse a Playwright response as JSON and provide a meaningful error."""
    logger = get_logger("ResponseParser")
    try:
        body = response.json()
        if not isinstance(body, dict):
            raise ValueError("Expected a JSON object")
        return body
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as error:
        logger.error(
            "Unable to parse JSON response | HTTP %s | error=%s",
            getattr(response, "status", "unknown"),
            error,
        )
        raise ValueError(
            f"API response is not valid JSON (HTTP {getattr(response, 'status', 'unknown')})"
        ) from error
