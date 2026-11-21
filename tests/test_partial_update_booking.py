"""Tests for partially updating existing bookings."""

import pytest

from config.config import BOOKER_PASSWORD, BOOKER_USERNAME
from utils.data_generator import read_json
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.fixture
def authenticated_booking(booking_helper):
    """Create a token and booking, then clean up the booking."""
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

    cleanup = booking_helper.delete_booking(
        bookingId=booking_id,
        token=token,
    )
    logger.info(
        "Cleanup booking ID=%s | HTTP %s",
        booking_id,
        cleanup.status,
    )


@pytest.mark.order(1)
@pytest.mark.partial_update
@pytest.mark.functional
@pytest.mark.authorization
@pytest.mark.regression
def test_partial_update_one_field_at_a_time(authenticated_booking):
    """Verify each supported field can be patched independently."""
    booking_helper, booking_id, _, token = authenticated_booking
    logger.info("START | test_partial_update_one_field_at_a_time")

    updates = {
        "firstname": "PatchedFirstname",
        "lastname": "PatchedLastname",
        "totalprice": 222,
        "depositpaid": False,
    }
    for field, value in updates.items():
        logger.info("PATCH field=%s value=%r", field, value)
        response = booking_helper.partial_update_booking(
            bookingId=booking_id,
            payload={field: value},
            token=token,
        )
        logger.info("PATCH field=%s | HTTP %s", field, response.status)
        assert response.status == 200
        assert response.json()[field] == value

    logger.info("END | test_partial_update_one_field_at_a_time")


@pytest.mark.order(2)
@pytest.mark.partial_update
@pytest.mark.functional
@pytest.mark.authorization
@pytest.mark.regression
def test_partial_update_multiple_fields(authenticated_booking):
    """Verify multiple fields can be patched in one request."""
    booking_helper, booking_id, _, token = authenticated_booking
    logger.info("START | test_partial_update_multiple_fields")

    patch_payload = {
        "firstname": "Multiple",
        "lastname": "Fields",
        "totalprice": 333,
    }
    response = booking_helper.partial_update_booking(
        bookingId=booking_id,
        payload=patch_payload,
        token=token,
    )
    logger.info("PATCH multiple fields | HTTP %s", response.status)
    assert response.status == 200
    for field, value in patch_payload.items():
        assert response.json()[field] == value

    logger.info("END | test_partial_update_multiple_fields")


@pytest.mark.order(3)
@pytest.mark.partial_update
@pytest.mark.negative
@pytest.mark.security
@pytest.mark.authorization
@pytest.mark.regression
def test_partial_update_without_authentication(authenticated_booking):
    """Verify partial update is rejected without a valid token."""
    booking_helper, booking_id, _, _ = authenticated_booking
    logger.info("START | test_partial_update_without_authentication")

    response = booking_helper.partial_update_booking(
        bookingId=booking_id,
        payload={"firstname": "Unauthorized"},
    )
    logger.info("PATCH without authentication | HTTP %s", response.status)
    assert response.status == 403

    logger.info("END | test_partial_update_without_authentication")


@pytest.mark.order(4)
@pytest.mark.partial_update
@pytest.mark.negative
@pytest.mark.authorization
@pytest.mark.regression
def test_partial_update_nonexistent_booking(booking_helper):
    """Verify a nonexistent booking ID is rejected."""
    logger.info("START | test_partial_update_nonexistent_booking")
    response = booking_helper.partial_update_booking(
        bookingId=2147483647,
        payload={"firstname": "Missing"},
        token="invalid-token",
    )
    logger.info("PATCH nonexistent booking | HTTP %s", response.status)
    assert response.status in (403, 404, 405)
    logger.info("END | test_partial_update_nonexistent_booking")


@pytest.mark.order(5)
@pytest.mark.partial_update
@pytest.mark.negative
@pytest.mark.parametrize(
    "field,value",
    [
        pytest.param("firstname", None, id="firstname_null"),
        pytest.param("lastname", [], id="lastname_list"),
        pytest.param("totalprice", "invalid", id="totalprice_string"),
        pytest.param("depositpaid", "yes", id="depositpaid_string"),
        pytest.param("unknown_field", "value", id="unknown_field"),
    ],
)
@pytest.mark.authorization
@pytest.mark.regression
def test_partial_update_with_invalid_fields(
    authenticated_booking, field, value
):
    """Verify invalid or unsupported patch fields are handled."""
    booking_helper, booking_id, _, token = authenticated_booking
    logger.info(
        "START | test_partial_update_with_invalid_fields | %s=%r",
        field,
        value,
    )

    response = booking_helper.partial_update_booking(
        bookingId=booking_id,
        payload={field: value},
        token=token,
    )
    logger.info("PATCH invalid field | HTTP %s", response.status)
    assert response.status in (200, 400, 405, 500)

    logger.info("END | test_partial_update_with_invalid_fields")


@pytest.mark.order(6)
@pytest.mark.partial_update
@pytest.mark.negative
@pytest.mark.authorization
@pytest.mark.regression
def test_partial_update_empty_payload(authenticated_booking):
    """Verify an empty patch payload is handled safely."""
    booking_helper, booking_id, _, token = authenticated_booking
    logger.info("START | test_partial_update_empty_payload")

    response = booking_helper.partial_update_booking(
        bookingId=booking_id,
        payload={},
        token=token,
    )
    logger.info("PATCH empty payload | HTTP %s", response.status)
    assert response.status in (200, 400)

    logger.info("END | test_partial_update_empty_payload")


@pytest.mark.order(7)
@pytest.mark.partial_update
@pytest.mark.negative
@pytest.mark.authorization
@pytest.mark.regression
def test_partial_update_with_unknown_property(authenticated_booking):
    """Verify an unknown JSON property is handled safely.

    Test steps:
    1. Send a partial update containing one unknown property.
    2. Verify the API response is handled successfully or rejects the payload.
    3. Verify the known booking fields remain readable.
    """
    booking_helper, booking_id, _, token = authenticated_booking
    logger.info("START | test_partial_update_with_unknown_property")

    response = booking_helper.partial_update_booking(
        bookingId=booking_id,
        payload={"unknown_property": "ignored"},
        token=token,
    )
    logger.info("PATCH unknown property | HTTP %s", response.status)
    assert response.status in (200, 400, 500)

    get_response = booking_helper.get_booking_by_id(booking_id)
    assert get_response.status == 200
    assert "unknown_property" not in get_response.json()
    logger.info("END | test_partial_update_with_unknown_property")


@pytest.mark.order(8)
@pytest.mark.partial_update
@pytest.mark.negative
@pytest.mark.authorization
@pytest.mark.regression
@pytest.mark.parametrize(
    "field,value",
    [
        pytest.param("firstname", None, id="firstname_null"),
        pytest.param("firstname", "", id="firstname_empty"),
        pytest.param("lastname", None, id="lastname_null"),
        pytest.param("lastname", "", id="lastname_empty"),
    ],
)
def test_partial_update_with_null_and_empty_string(
    authenticated_booking, field, value
):
    """Verify null and empty-string values are handled consistently."""
    booking_helper, booking_id, _, token = authenticated_booking
    logger.info(
        "START | test_partial_update_with_null_and_empty_string | %s=%r",
        field,
        value,
    )

    response = booking_helper.partial_update_booking(
        bookingId=booking_id,
        payload={field: value},
        token=token,
    )
    logger.info("PATCH null or empty value | HTTP %s", response.status)
    assert response.status in (200, 400, 500)

    get_response = booking_helper.get_booking_by_id(booking_id)
    assert get_response.status == 200
    logger.info("END | test_partial_update_with_null_and_empty_string")


@pytest.mark.order(9)
@pytest.mark.partial_update
@pytest.mark.functional
@pytest.mark.authorization
@pytest.mark.regression
def test_partial_update_with_identical_payload_twice(
    authenticated_booking
):
    """Verify identical partial updates remain stable."""
    booking_helper, booking_id, _, token = authenticated_booking
    logger.info("START | test_partial_update_with_identical_payload_twice")

    patch_payload = {"firstname": "IdempotentPatch", "totalprice": 444}

    first_response = booking_helper.partial_update_booking(
        bookingId=booking_id,
        payload=patch_payload,
        token=token,
    )
    second_response = booking_helper.partial_update_booking(
        bookingId=booking_id,
        payload=patch_payload,
        token=token,
    )
    logger.info(
        "First HTTP %s | Second HTTP %s",
        first_response.status,
        second_response.status,
    )
    assert first_response.status == 200
    assert second_response.status == 200
    assert first_response.json() == second_response.json()

    get_response = booking_helper.get_booking_by_id(booking_id)
    assert get_response.status == 200
    assert get_response.json()["firstname"] == "IdempotentPatch"
    assert get_response.json()["totalprice"] == 444
    logger.info("END | test_partial_update_with_identical_payload_twice")


@pytest.mark.order(10)
@pytest.mark.partial_update
@pytest.mark.negative
@pytest.mark.authorization
@pytest.mark.regression
def test_partial_update_with_bookingid_in_payload(
    authenticated_booking
):
    """Verify a bookingid in the payload cannot replace the URL booking ID."""
    booking_helper, booking_id, _, token = authenticated_booking
    logger.info("START | test_partial_update_with_bookingid_in_payload")

    response = booking_helper.partial_update_booking(
        bookingId=booking_id,
        payload={
            "firstname": "BookingIdPatch",
            "bookingid": 2147483647,
        },
        token=token,
    )
    logger.info("PATCH with bookingid payload | HTTP %s", response.status)
    assert response.status in (200, 400, 405, 500)

    get_response = booking_helper.get_booking_by_id(booking_id)
    assert get_response.status in (200, 404)
    if response.status == 200:
        assert get_response.json()["firstname"] == "BookingIdPatch"
    logger.info("END | test_partial_update_with_bookingid_in_payload")


@pytest.mark.order(11)
@pytest.mark.partial_update
@pytest.mark.negative
@pytest.mark.security
@pytest.mark.authorization
@pytest.mark.regression
@pytest.mark.parametrize(
    "accept",
    [
        pytest.param(None, id="missing_accept"),
        pytest.param("application/json", id="json_accept"),
        pytest.param("text/plain", id="text_plain"),
        pytest.param("invalid", id="invalid_accept"),
    ],
)
def test_partial_update_with_missing_or_unsupported_accept_header(
    authenticated_booking, accept
):
    """Verify missing and unsupported Accept headers are handled."""
    booking_helper, booking_id, _, token = authenticated_booking
    logger.info(
        "START | test_partial_update_with_missing_or_unsupported_accept_header "
        "| accept=%r",
        accept,
    )

    headers = {"Content-Type": "application/json"}
    if accept is not None:
        headers["Accept"] = accept

    response = booking_helper.partial_update_booking(
        bookingId=booking_id,
        payload={"firstname": "AcceptHeaderPatch"},
        token=token,
        headers=headers,
    )
    logger.info("PATCH with Accept header | HTTP %s", response.status)
    assert response.status in (200, 406, 418, 500)

    get_response = booking_helper.get_booking_by_id(booking_id)
    assert get_response.status == 200
    logger.info(
        "END | test_partial_update_with_missing_or_unsupported_accept_header"
    )
