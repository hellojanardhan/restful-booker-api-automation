"""Tests for the ping health-check endpoint."""

import time

import pytest

from config.config import PERF_P95_MS, PERF_MAX_MS
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.order(1)
@pytest.mark.ping
@pytest.mark.smoke
@pytest.mark.functional
@pytest.mark.security
def test_get_ping_without_authentication(booking_helper):
    """Verify that an unauthenticated GET to ping succeeds.

    Test steps:
    1. Send a GET request to the ping endpoint without authentication.
    2. Check that the response is successful.
    3. Verify that the HTTP status is 201.
    """
    logger.info("START | test_get_ping_without_authentication")
    logger.info("Step 1: Send unauthenticated GET request to ping endpoint")
    response = booking_helper.check_ping()

    logger.info("Step 1 result: HTTP %s, successful=%s", response.status, response.ok)
    logger.info("Step 2: Verify response status is 201")
    assert response.ok
    assert response.status == 201
    logger.info("Step 2 result: Ping responded successfully")
    logger.info("END | test_get_ping_without_authentication")


@pytest.mark.order(2)
@pytest.mark.ping
@pytest.mark.smoke
@pytest.mark.functional
@pytest.mark.functional
def test_get_ping_five_consecutive_requests(booking_helper):
    """Verify ping remains successful across five consecutive requests.

    Test steps:
    1. Send five separate unauthenticated GET requests to the ping endpoint.
    2. Check each response for success.
    3. Verify every response has HTTP status 201.
    """
    logger.info("START | test_get_ping_five_consecutive_requests")
    for request_number in range(1, 6):
        logger.info("Step %s: Send consecutive ping GET request", request_number)
        response = booking_helper.check_ping()

        logger.info(
            "Step %s result: HTTP %s, successful=%s",
            request_number,
            response.status,
            response.ok,
        )
        assert response.ok
        assert response.status == 201
    logger.info("END | test_get_ping_five_consecutive_requests")


@pytest.mark.order(3)
@pytest.mark.ping
@pytest.mark.smoke
@pytest.mark.functional
@pytest.mark.functional
def test_get_ping_response_time_within_threshold(booking_helper):
    """Verify ping response P95 and maximum times meet performance limits.

    Test steps:
    1. Send ten unauthenticated GET requests to the ping endpoint.
    2. Measure elapsed time for each response in milliseconds.
    3. Calculate P95 and maximum response times.
    4. Verify P95 and maximum values are within configured thresholds.
    """
    logger.info("START | test_get_ping_response_time_within_threshold")
    response_times = []
    for request_number in range(1, 11):
        logger.info("Step 1.%s: Send timed ping GET request", request_number)
        start_time = time.perf_counter()
        response = booking_helper.check_ping()
        end_time = time.perf_counter()
        response_time = (end_time - start_time) * 1000
        response_times.append(response_time)
        logger.info(
            "Step 1.%s result: HTTP %s, response time %.2f ms",
            request_number,
            response.status,
            response_time,
        )

    logger.info("Step 2: Calculate P95 and maximum response times")
    p95 = sorted(response_times)[int(0.95 * (len(response_times) - 1))]
    max_time = max(response_times)
    logger.info("Ping response times: %s", response_times)
    logger.info("Ping P95 response time: %.2f ms", p95)
    logger.info("Ping maximum response time: %.2f ms", max_time)

    logger.info("Step 3: Verify P95 and maximum thresholds")
    assert p95 <= PERF_P95_MS, f"P95 exceeded threshold: {p95:.2f} ms"
    assert max_time <= PERF_MAX_MS, (
        f"Maximum response time exceeded threshold: {max_time:.2f} ms"
    )
    logger.info("Step 3 result: P95 and maximum response times are within thresholds")
    logger.info("END | test_get_ping_response_time_within_threshold")


@pytest.mark.parametrize(
    "method", ["POST", "PUT", "DELETE"]
)
@pytest.mark.order(4)
@pytest.mark.ping
@pytest.mark.smoke
@pytest.mark.functional
@pytest.mark.negative
def test_unsupported_methods_on_ping_endpoint(booking_helper, method):
    """Verify unsupported HTTP methods are rejected by the ping endpoint.

    Test steps:
    1. Send a POST, PUT, or DELETE request to the ping endpoint.
    2. Record the HTTP response status.
    3. Verify that the endpoint returns HTTP 404.
    """
    logger.info("START | test_unsupported_methods_on_ping_endpoint | method=%s", method)
    logger.info("Step 1: Send unsupported %s request to ping endpoint", method)
    response = booking_helper.check_ping(method=method)

    logger.info("Step 1 result: HTTP %s", response.status)
    logger.info("Step 2: Verify endpoint returns HTTP 404")
    assert response.status == 404
    logger.info("Step 2 result: Unsupported method was rejected")
    logger.info("END | test_unsupported_methods_on_ping_endpoint | method=%s", method)
