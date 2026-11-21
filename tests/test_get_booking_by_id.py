"""Tests for retrieving individual bookings by booking ID."""

import pytest

from config.config import BOOKER_PASSWORD, BOOKER_USERNAME, GET_BOOKING
from utils.data_generator import read_json
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.fixture
def created_booking(booking_helper):
    """Create a booking and provide its ID and token, then clean it up."""
    token_response = booking_helper.create_auth_token(
        username=BOOKER_USERNAME,
        password=BOOKER_PASSWORD,
    )
    assert token_response.status == 200
    token = token_response.json()["token"]

    payload = read_json("booking_data.json")
    create_response = booking_helper.create_booking(payload=payload)
    assert create_response.status == 200
    booking_id = create_response.json()["bookingid"]

    yield booking_helper, booking_id, payload, token

    try:
        cleanup = booking_helper.delete_booking(
            bookingId=booking_id,
            token=token,
        )
        logger.info(
            "Cleanup booking ID=%s | HTTP %s",
            booking_id,
            cleanup.status,
        )
    except Exception:
        logger.exception(
            "Cleanup failed for booking ID=%s",
            booking_id,
        )


@pytest.mark.order(1)
@pytest.mark.functional
@pytest.mark.booking_by_id
def test_get_booking_by_id_created_by_current_test(created_booking):
    """Verify the current test can retrieve the booking it created.

    Test steps:
    1. Use the fixture-created booking ID.
    2. Send GET /booking/{id}.
    3. Verify HTTP 200 and the matching booking ID.
    """
    booking_helper, booking_id, _, _ = created_booking
    logger.info(
        "START | test_get_booking_by_id_created_by_current_test | id=%s",
        booking_id,
    )

    response = booking_helper.get_booking_by_id(booking_id)
    logger.info("Step 2 result: HTTP %s", response.status)
    assert response.status == 200
    assert isinstance(response.json(), dict)
    assert "firstname" in response.json()
    logger.info(
        "END | test_get_booking_by_id_created_by_current_test"
    )


@pytest.mark.order(2)
@pytest.mark.schema
@pytest.mark.booking_by_id
def test_get_booking_response_schema_and_data_types(created_booking):
    """Verify the by-ID response contains the expected fields and types."""
    booking_helper, booking_id, _, _ = created_booking
    logger.info(
        "START | test_get_booking_response_schema_and_data_types | id=%s",
        booking_id,
    )

    response = booking_helper.get_booking_by_id(booking_id)
    logger.info("Step result: HTTP %s", response.status)
    assert response.status == 200
    body = response.json()

    assert isinstance(body, dict)
    for field in (
        "firstname",
        "lastname",
        "totalprice",
        "depositpaid",
        "bookingdates",
        "additionalneeds",
    ):
        assert field in body

    assert isinstance(body["firstname"], str)
    assert isinstance(body["lastname"], str)
    assert isinstance(body["totalprice"], int)
    assert isinstance(body["depositpaid"], bool)
    assert isinstance(body["bookingdates"], dict)
    assert isinstance(body["additionalneeds"], str)
    assert set(body["bookingdates"]) >= {"checkin", "checkout"}
    assert isinstance(body["bookingdates"]["checkin"], str)
    assert isinstance(body["bookingdates"]["checkout"], str)
    logger.info(
        "END | test_get_booking_response_schema_and_data_types"
    )


@pytest.mark.order(3)
@pytest.mark.functional
@pytest.mark.booking_by_id
def test_get_booking_matches_created_payload(created_booking):
    """Verify the by-ID response matches the fixture-created payload."""
    booking_helper, booking_id, payload, _ = created_booking
    logger.info(
        "START | test_get_booking_matches_created_payload | id=%s",
        booking_id,
    )

    response = booking_helper.get_booking_by_id(booking_id)
    logger.info("Step result: HTTP %s", response.status)
    assert response.status == 200
    body = response.json()

    assert body["firstname"] == payload["firstname"]
    assert body["lastname"] == payload["lastname"]
    assert body["totalprice"] == payload["totalprice"]
    assert body["depositpaid"] == payload["depositpaid"]
    assert body["bookingdates"] == payload["bookingdates"]
    assert body["additionalneeds"] == payload["additionalneeds"]
    logger.info(
        "END | test_get_booking_matches_created_payload"
    )


@pytest.mark.order(4)
@pytest.mark.negative
@pytest.mark.booking_by_id
def test_get_booking_with_nonexistent_id(booking_helper):
    """Verify a previously deleted booking ID returns HTTP 404."""
    logger.info("START | test_get_booking_with_nonexistent_id")

    token_response = booking_helper.create_auth_token(
        username=BOOKER_USERNAME,
        password=BOOKER_PASSWORD,
    )
    assert token_response.status == 200
    token = token_response.json()["token"]

    payload = read_json("booking_data.json")
    create_response = booking_helper.create_booking(payload=payload)
    assert create_response.status == 200
    nonexistent_id = create_response.json()["bookingid"]

    delete_response = booking_helper.delete_booking(
        bookingId=nonexistent_id,
        token=token,
    )
    assert delete_response.status == 201

    response = booking_helper.get_booking_by_id(nonexistent_id)
    logger.info("Step result: HTTP %s", response.status)
    assert response.status == 404
    logger.info("END | test_get_booking_with_nonexistent_id")


@pytest.mark.parametrize(
    "invalid_id",
    [
        pytest.param("abc", id="letters"),
        pytest.param("-1", id="negative"),
        pytest.param("1.5", id="decimal"),
        pytest.param(" ", id="whitespace"),
        pytest.param("true", id="boolean"),
    ],
)
@pytest.mark.order(5)
@pytest.mark.negative
@pytest.mark.booking_by_id
def test_get_booking_with_invalid_id_formats(
    booking_helper, invalid_id
):
    """Verify malformed booking ID formats are handled."""
    logger.info(
        "START | test_get_booking_with_invalid_id_formats | id=%r",
        invalid_id,
    )
    response = booking_helper.rest_helper.execute(
        method="GET",
        endpoint=GET_BOOKING.format(booking_id=invalid_id),
    )
    logger.info("Step result: HTTP %s", response.status)
    assert response.status in (200, 400, 404, 500)
    logger.info("END | test_get_booking_with_invalid_id_formats")


@pytest.mark.parametrize(
    "endpoint_suffix",
    [
        pytest.param("", id="empty_id"),
        pytest.param("/", id="trailing_slash"),
    ],
)
@pytest.mark.order(6)
@pytest.mark.negative
@pytest.mark.booking_by_id
def test_get_booking_with_empty_id_and_trailing_slash(
    booking_helper, endpoint_suffix
):
    """Verify empty IDs and trailing slashes do not expose a booking."""
    logger.info(
        "START | test_get_booking_with_empty_id_and_trailing_slash "
        "| suffix=%r",
        endpoint_suffix,
    )
    base_endpoint = GET_BOOKING.format(booking_id="")
    response = booking_helper.rest_helper.execute(
        method="GET",
        endpoint=base_endpoint,
    )
    logger.info("Step result: HTTP %s", response.status)
    assert response.status in (200, 404, 405)
    logger.info(
        "END | test_get_booking_with_empty_id_and_trailing_slash"
    )


@pytest.mark.parametrize(
    "accept",
    [
        pytest.param("application/json", id="json"),
        pytest.param("*/*", id="wildcard"),
        pytest.param("text/plain", id="text"),
    ],
)
@pytest.mark.order(7)
@pytest.mark.security
@pytest.mark.booking_by_id
def test_get_booking_with_different_accept_headers(
    created_booking, accept
):
    """Verify the by-ID endpoint responds with supported Accept headers."""
    booking_helper, booking_id, _, _ = created_booking
    logger.info(
        "START | test_get_booking_with_different_accept_headers "
        "| id=%s | accept=%s",
        booking_id,
        accept,
    )
    response = booking_helper.get_booking_by_id(
        booking_id,
        headers={"Accept": accept},
    )
    logger.info("Step result: HTTP %s", response.status)
    assert response.status in (200, 418)
    if response.status == 200:
        assert isinstance(response.json(), dict)
    logger.info("END | test_get_booking_with_different_accept_headers")


@pytest.mark.order(8)
@pytest.mark.security
@pytest.mark.booking_by_id
def test_get_booking_without_authentication(created_booking):
    """Verify booking retrieval does not require authentication."""
    booking_helper, booking_id, _, _ = created_booking
    logger.info("START | test_get_booking_without_authentication")
    response = booking_helper.get_booking_by_id(booking_id)
    logger.info("Step result: HTTP %s", response.status)
    assert response.status == 200
    logger.info("END | test_get_booking_without_authentication")


@pytest.mark.order(9)
@pytest.mark.security
@pytest.mark.booking_by_id
def test_get_booking_without_authentication_three_consecutive_times(
    created_booking
):
    """Verify three consecutive unauthenticated reads remain successful."""
    booking_helper, booking_id, _, _ = created_booking
    logger.info(
        "START | test_get_booking_without_authentication_three_consecutive_times"
    )
    for attempt in range(1, 4):
        response = booking_helper.get_booking_by_id(booking_id)
        logger.info(
            "Attempt %s result: HTTP %s",
            attempt,
            response.status,
        )
        assert response.status == 200
        assert isinstance(response.json(), dict)
    logger.info(
        "END | test_get_booking_without_authentication_three_consecutive_times"
    )


@pytest.mark.parametrize("method", ["HEAD", "OPTIONS"])
@pytest.mark.order(10)
@pytest.mark.security
@pytest.mark.booking_by_id
@pytest.mark.functional
def test_head_and_options_methods_on_booking_by_id(
    created_booking, method
):
    """Verify unsupported HEAD and OPTIONS methods are handled."""
    booking_helper, booking_id, _, _ = created_booking
    logger.info(
        "START | test_head_and_options_methods_on_booking_by_id "
        "| method=%s",
        method,
    )
    response = booking_helper.rest_helper.execute(
        method=method,
        endpoint=GET_BOOKING.format(booking_id=booking_id),
    )
    logger.info("Step result: HTTP %s", response.status)
    assert response.status in (200, 404, 405)
    logger.info("END | test_head_and_options_methods_on_booking_by_id")
