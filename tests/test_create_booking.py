"""Tests for creating bookings through the Restful Booker API."""

import pytest

from config.config import BOOKER_PASSWORD, BOOKER_USERNAME
from utils.data_generator import read_json
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.fixture
def created_bookings(booking_helper):
    """Track successfully created bookings and delete them after each test."""
    booking_ids = set()
    yield booking_ids

    if not booking_ids:
        return

    token_response = booking_helper.create_auth_token(
        username=BOOKER_USERNAME,
        password=BOOKER_PASSWORD,
    )
    if token_response.status != 200:
        logger.error(
            "Cleanup token generation failed | HTTP %s",
            token_response.status,
        )
        return

    token = token_response.json().get("token")
    for booking_id in sorted(booking_ids):
        try:
            response = booking_helper.perform_booking_operation(
                method="DELETE",
                booking_id=booking_id,
                token=token,
            )
            logger.info(
                "Cleanup booking ID=%s | HTTP %s",
                booking_id,
                response.status,
            )
        except Exception as error:
            logger.exception(
                "Cleanup failed for booking ID=%s",
                booking_id,
            )
            pytest.fail(
                f"Failed to clean up booking {booking_id}: {error}",
                pytrace=False,
            )


def _log_start(test_name, **details):
    detail_text = " | ".join(f"{key}={value}" for key, value in details.items())
    suffix = f" | {detail_text}" if detail_text else ""
    logger.info("START | %s%s", test_name, suffix)


def _get_created_booking(response, created_bookings):
    """Validate a successful create response and register its booking ID."""
    if response.status != 200:
        logger.error(
            "Create booking failed unexpectedly | HTTP %s",
            response.status,
        )
        pytest.fail(
            f"Create-booking expected HTTP 200, received {response.status}",
            pytrace=False,
        )

    try:
        response_body = response.json()
        booking_id = response_body["bookingid"]
    except (KeyError, TypeError, ValueError) as error:
        logger.exception("Create-booking response did not contain a valid booking ID")
        pytest.fail(
            f"Invalid create-booking response: {error}",
            pytrace=False,
        )

    if not isinstance(booking_id, int) or booking_id <= 0:
        logger.error(
            "Invalid booking ID in create response: %r",
            booking_id,
        )
        pytest.fail(
            f"Invalid booking ID returned: {booking_id}",
            pytrace=False,
        )

    created_bookings.add(booking_id)
    return booking_id, response_body


@pytest.mark.order(1)
@pytest.mark.create_booking
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.functional
def test_create_booking_with_valid_payload(
    booking_helper, created_bookings
):
    """Verify a valid booking payload creates a booking.

    Test steps:
    1. Load valid booking data.
    2. Send a create-booking request.
    3. Verify the status and returned booking values.
    """
    _log_start("test_create_booking_with_valid_payload")
    logger.info("Step 1: Load valid booking payload")
    payload = read_json("booking_data.json")

    logger.info("Step 2: Send create-booking request")
    response = booking_helper.create_booking(payload=payload)
    logger.info("Step 2 result: HTTP %s", response.status)

    assert response.ok
    assert response.status == 200

    logger.info("Step 3: Verify booking values")
    booking_id, response_body = _get_created_booking(
        response,
        created_bookings,
    )
    assert response_body["booking"]["firstname"] == payload["firstname"]
    assert response_body["booking"]["lastname"] == payload["lastname"]
    logger.info("Step 3 result: Booking ID=%s", booking_id)
    logger.info("END | test_create_booking_with_valid_payload")


@pytest.mark.parametrize(
    "depositpaid",
    [
        pytest.param(True, id="depositpaid_true"),
        pytest.param(False, id="depositpaid_false"),
    ],
)
@pytest.mark.order(2)
@pytest.mark.create_booking
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.functional
def test_create_booking_with_depositpaid_values(
    booking_helper, created_bookings, depositpaid
):
    """Verify both boolean deposit-paid values are persisted.

    Test steps:
    1. Load valid booking data.
    2. Set depositpaid to the parameterized value.
    3. Create the booking.
    4. Verify the returned value.
    """
    _log_start(
        "test_create_booking_with_depositpaid_values",
        depositpaid=depositpaid,
    )
    payload = read_json("booking_data.json")
    payload["depositpaid"] = depositpaid

    logger.info("Step 1-2: Set depositpaid=%s", depositpaid)
    logger.info("Step 3: Send create-booking request")
    response = booking_helper.create_booking(payload=payload)
    logger.info("Step 3 result: HTTP %s", response.status)

    assert response.ok
    assert response.status == 200
    booking_id, response_body = _get_created_booking(
        response,
        created_bookings,
    )

    logger.info("Step 4: Verify depositpaid response")
    assert response_body["booking"]["depositpaid"] == depositpaid
    logger.info(
        "Step 4 result: Booking ID=%s, depositpaid=%s",
        booking_id,
        depositpaid,
    )
    logger.info("END | test_create_booking_with_depositpaid_values")


@pytest.mark.order(3)
@pytest.mark.create_booking
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.functional
def test_create_booking_without_optional_additionalneeds(
    booking_helper, created_bookings
):
    """Verify additionalneeds is optional.

    Test steps:
    1. Load valid booking data.
    2. Remove additionalneeds.
    3. Create the booking.
    4. Verify the API returns a positive booking ID.
    """
    _log_start("test_create_booking_without_optional_additionalneeds")
    payload = read_json("booking_data.json")
    payload.pop("additionalneeds", None)

    logger.info("Step 1-2: Remove optional additionalneeds")
    response = booking_helper.create_booking(payload=payload)
    logger.info("Step 3 result: HTTP %s", response.status)

    assert response.status == 200
    booking_id, response_body = _get_created_booking(
        response,
        created_bookings,
    )
    assert response_body["booking"]["firstname"] == payload["firstname"]
    logger.info("Step 4 result: Booking ID=%s", booking_id)
    logger.info("END | test_create_booking_without_optional_additionalneeds")


@pytest.mark.parametrize(
    "required_field",
    [
        pytest.param("firstname", id="missing_firstname"),
        pytest.param("lastname", id="missing_lastname"),
        pytest.param("totalprice", id="missing_totalprice"),
        pytest.param("depositpaid", id="missing_depositpaid"),
        pytest.param("bookingdates", id="missing_bookingdates"),
    ],
)
@pytest.mark.order(4)
@pytest.mark.create_booking
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.negative
def test_create_booking_with_missing_required_fields(
    booking_helper, required_field
):
    """Verify required fields are not silently accepted.

    Test steps:
    1. Load valid data.
    2. Remove one required field.
    3. Create the booking.
    4. Verify the server rejects it with HTTP 500.
    """
    _log_start(
        "test_create_booking_with_missing_required_fields",
        required_field=required_field,
    )
    payload = read_json("booking_data.json")
    payload.pop(required_field, None)

    logger.info("Step 1-2: Remove required field %s", required_field)
    response = booking_helper.create_booking(payload=payload)
    logger.info("Step 3-4 result: HTTP %s", response.status)

    assert response.status == 500
    logger.info("END | test_create_booking_with_missing_required_fields")


@pytest.mark.parametrize(
    "bookingdates",
    [
        pytest.param(None, id="bookingdates_null"),
        pytest.param({}, id="bookingdates_empty"),
        pytest.param({"checkin": "2026-12-01"}, id="missing_checkout"),
        pytest.param({"checkout": "2026-12-05"}, id="missing_checkin"),
    ],
)
@pytest.mark.order(5)
@pytest.mark.create_booking
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.negative
def test_create_booking_with_invalid_bookingdates(
    booking_helper, bookingdates
):
    """Verify malformed bookingdates are handled safely.

    Test steps:
    1. Load valid data.
    2. Replace bookingdates with invalid data.
    3. Create the booking.
    4. Verify a 200 or 500 response is returned.
    """
    _log_start("test_create_booking_with_invalid_bookingdates")
    payload = read_json("booking_data.json")
    payload["bookingdates"] = bookingdates

    response = booking_helper.create_booking(payload=payload)
    logger.info("Step 3-4 result: HTTP %s", response.status)
    assert response.status in (200, 500)
    logger.info("END | test_create_booking_with_invalid_bookingdates")


@pytest.mark.parametrize(
    "totalprice, expected_status",
    [
        pytest.param("abc", 200, id="string_value"),
        pytest.param("150", 200, id="numeric_string"),
        pytest.param(True, 200, id="boolean_true"),
        pytest.param(None, 500, id="null_value"),
        pytest.param([], 200, id="empty_list"),
        pytest.param({}, 200, id="empty_dict"),
    ],
)
@pytest.mark.order(6)
@pytest.mark.create_booking
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.negative
def test_create_booking_with_invalid_totalprice_types(
    booking_helper, created_bookings, totalprice, expected_status
):
    """Verify observed API behavior for invalid totalprice types.

    Test steps:
    1. Load valid data.
    2. Replace totalprice with an invalid type.
    3. Create the booking.
    4. Verify the report-observed HTTP status.
    """
    _log_start("test_create_booking_with_invalid_totalprice_types")
    payload = read_json("booking_data.json")
    payload["totalprice"] = totalprice

    response = booking_helper.create_booking(payload=payload)
    logger.info("Step 3-4 result: HTTP %s", response.status)
    assert response.status == expected_status
    if response.status == 200:
        _get_created_booking(response, created_bookings)
    logger.info("END | test_create_booking_with_invalid_totalprice_types")


@pytest.mark.parametrize(
    "depositpaid, expected_status",
    [
        pytest.param("true", 200, id="string_true"),
        pytest.param("yes", 200, id="string_yes"),
        pytest.param(1, 200, id="integer_one"),
        pytest.param(0, 200, id="integer_zero"),
        pytest.param(None, 500, id="null_value"),
        pytest.param([], 200, id="empty_list"),
        pytest.param({}, 200, id="empty_dict"),
    ],
)
@pytest.mark.order(7)
@pytest.mark.create_booking
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.negative
def test_create_booking_with_invalid_depositpaid_types(
    booking_helper, created_bookings, depositpaid, expected_status
):
    """Verify observed API behavior for invalid depositpaid types.

    Test steps:
    1. Load valid data.
    2. Replace depositpaid with an invalid type.
    3. Create the booking.
    4. Verify the report-observed HTTP status.
    """
    _log_start("test_create_booking_with_invalid_depositpaid_types")
    payload = read_json("booking_data.json")
    payload["depositpaid"] = depositpaid

    response = booking_helper.create_booking(payload=payload)
    logger.info("Step 3-4 result: HTTP %s", response.status)
    assert response.status == expected_status
    if response.status == 200:
        _get_created_booking(response, created_bookings)
    logger.info("END | test_create_booking_with_invalid_depositpaid_types")


@pytest.mark.parametrize(
    "field, value, expected_status",
    [
        pytest.param("firstname", 123, 500, id="firstname_integer"),
        pytest.param("firstname", True, 500, id="firstname_boolean"),
        pytest.param("firstname", None, 500, id="firstname_null"),
        pytest.param("firstname", [], 500, id="firstname_list"),
        pytest.param("firstname", {}, 500, id="firstname_dict"),
        pytest.param("lastname", 123, 500, id="lastname_integer"),
        pytest.param("lastname", True, 500, id="lastname_boolean"),
        pytest.param("lastname", None, 500, id="lastname_null"),
        pytest.param("lastname", [], 500, id="lastname_list"),
        pytest.param("lastname", {}, 500, id="lastname_dict"),
        pytest.param("additionalneeds", 123, 200, id="additionalneeds_integer"),
        pytest.param("additionalneeds", True, 200, id="additionalneeds_boolean"),
        pytest.param("additionalneeds", None, 200, id="additionalneeds_null"),
        pytest.param("additionalneeds", [], 200, id="additionalneeds_list"),
        pytest.param("additionalneeds", {}, 200, id="additionalneeds_dict"),
    ],
)
@pytest.mark.order(8)
@pytest.mark.create_booking
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.negative
def test_create_booking_with_invalid_name_and_additionalneeds_types(
    booking_helper,
    created_bookings,
    field,
    value,
    expected_status,
):
    """Verify field-type handling for names and additionalneeds.

    Test steps:
    1. Load valid data.
    2. Replace the target field with an invalid type.
    3. Create the booking.
    4. Verify the field-specific status.
    """
    _log_start(
        "test_create_booking_with_invalid_name_and_additionalneeds_types",
        field=field,
        value=value,
    )
    payload = read_json("booking_data.json")
    payload[field] = value

    response = booking_helper.create_booking(payload=payload)
    logger.info("Step 3-4 result: HTTP %s", response.status)
    assert response.status == expected_status
    if response.status == 200:
        _get_created_booking(response, created_bookings)
    logger.info("END | test_create_booking_with_invalid_name_and_additionalneeds_types")


@pytest.mark.parametrize(
    "date_value",
    [
        pytest.param("2026-02-30", id="invalid_calendar_date"),
        pytest.param("2026-13-01", id="invalid_month"),
        pytest.param("01/12/2026", id="different_date_format"),
        pytest.param("20261201", id="compact_date_format"),
        pytest.param("", id="empty_date"),
        pytest.param(None, id="null_date"),
        pytest.param("2026-12-01T10:00:00Z", id="datetime_format"),
    ],
)
@pytest.mark.order(9)
@pytest.mark.create_booking
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.negative
def test_create_booking_with_invalid_date_formats(
    booking_helper, date_value
):
    """Verify invalid date formats fail safely.

    Test steps:
    1. Load valid data.
    2. Replace bookingdates with invalid date data.
    3. Create the booking.
    4. Verify HTTP 500.
    """
    _log_start("test_create_booking_with_invalid_date_formats")
    payload = read_json("booking_data.json")
    payload["bookingdates"] = date_value

    response = booking_helper.create_booking(payload=payload)
    logger.info("Step 3-4 result: HTTP %s", response.status)
    assert response.status == 500
    logger.info("END | test_create_booking_with_invalid_date_formats")


@pytest.mark.order(10)
@pytest.mark.create_booking
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.functional
def test_create_booking_with_checkout_before_checkin(
    booking_helper, created_bookings
):
    """Verify the API's current handling of reversed booking dates.

    Test steps:
    1. Set check-in after checkout.
    2. Create the booking.
    3. Verify a positive ID and record it for cleanup.
    """
    _log_start("test_create_booking_with_checkout_before_checkin")
    payload = read_json("booking_data.json")
    payload["bookingdates"] = {
        "checkin": "2026-12-10",
        "checkout": "2026-12-01",
    }

    response = booking_helper.create_booking(payload=payload)
    logger.info("Step 2 result: HTTP %s", response.status)
    assert response.status == 200
    booking_id, _ = _get_created_booking(response, created_bookings)
    logger.info("Step 3 result: Booking ID=%s", booking_id)
    logger.info("END | test_create_booking_with_checkout_before_checkin")


@pytest.mark.order(11)
@pytest.mark.create_booking
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.functional
def test_create_booking_with_same_checkin_checkout_date(
    booking_helper, created_bookings
):
    """Verify a booking with identical check-in and checkout dates.

    Test steps:
    1. Set both dates to the same value.
    2. Create the booking.
    3. Verify the response and returned dates.
    """
    _log_start("test_create_booking_with_same_checkin_checkout_date")
    payload = read_json("booking_data.json")
    payload["bookingdates"]["checkin"] = "2026-12-10"
    payload["bookingdates"]["checkout"] = "2026-12-10"

    response = booking_helper.create_booking(payload=payload)
    logger.info("Step 2 result: HTTP %s", response.status)
    assert response.status == 200
    booking_id, response_body = _get_created_booking(
        response,
        created_bookings,
    )
    assert (
        response_body["booking"]["bookingdates"]["checkin"]
        == "2026-12-10"
    )
    assert (
        response_body["booking"]["bookingdates"]["checkout"]
        == "2026-12-10"
    )
    logger.info("Step 3 result: Booking ID=%s", booking_id)
    logger.info("END | test_create_booking_with_same_checkin_checkout_date")


@pytest.mark.parametrize(
    "totalprice",
    [
        pytest.param(-1, id="negative"),
        pytest.param(0, id="zero"),
        pytest.param(2147483647, id="maximum_integer"),
    ],
)
@pytest.mark.order(12)
@pytest.mark.create_booking
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.functional
def test_create_booking_with_totalprice_boundary_values(
    booking_helper, created_bookings, totalprice
):
    """Verify totalprice boundary values are handled.

    Test steps:
    1. Set the parameterized totalprice.
    2. Create the booking.
    3. Verify the API response and cleanup the booking.
    """
    _log_start(
        "test_create_booking_with_totalprice_boundary_values",
        totalprice=totalprice,
    )
    payload = read_json("booking_data.json")
    payload["totalprice"] = totalprice

    response = booking_helper.create_booking(payload=payload)
    logger.info("Step 2 result: HTTP %s", response.status)
    assert response.status == 200
    booking_id, response_body = _get_created_booking(
        response,
        created_bookings,
    )
    assert response_body["booking"]["totalprice"] == totalprice
    logger.info("Step 3 result: Booking ID=%s", booking_id)
    logger.info("END | test_create_booking_with_totalprice_boundary_values")


@pytest.mark.parametrize(
    "name",
    [
        pytest.param("", id="empty"),
        pytest.param("A", id="single_character"),
        pytest.param("A" * 255, id="255_characters"),
    ],
)
@pytest.mark.order(13)
@pytest.mark.create_booking
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.functional
def test_create_booking_with_name_length_boundary_values(
    booking_helper, created_bookings, name
):
    """Verify name-length boundary values are handled.

    Test steps:
    1. Set firstname and lastname to the parameterized length.
    2. Create the booking.
    3. Verify the response and cleanup.
    """
    _log_start(
        "test_create_booking_with_name_length_boundary_values",
        name_length=len(name),
    )
    payload = read_json("booking_data.json")
    payload["firstname"] = name
    payload["lastname"] = name

    response = booking_helper.create_booking(payload=payload)
    logger.info("Step 2 result: HTTP %s", response.status)
    assert response.status == 200
    booking_id, response_body = _get_created_booking(
        response,
        created_bookings,
    )
    assert response_body["booking"]["firstname"] == name
    assert response_body["booking"]["lastname"] == name
    logger.info("Step 3 result: Booking ID=%s", booking_id)
    logger.info("END | test_create_booking_with_name_length_boundary_values")


@pytest.mark.parametrize(
    "firstname",
    [
        pytest.param("José Nguyễn", id="unicode"),
        pytest.param("Jim<script>alert(1)</script>", id="special_characters"),
    ],
)
@pytest.mark.order(14)
@pytest.mark.create_booking
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.functional
def test_create_booking_with_unicode_and_special_characters(
    booking_helper, created_bookings, firstname
):
    """Verify Unicode and special characters are returned safely.

    Test steps:
    1. Set a Unicode or special-character firstname.
    2. Create the booking.
    3. Verify the response value and cleanup.
    """
    _log_start(
        "test_create_booking_with_unicode_and_special_characters",
        firstname=firstname,
    )
    payload = read_json("booking_data.json")
    payload["firstname"] = firstname

    response = booking_helper.create_booking(payload=payload)
    logger.info("Step 2 result: HTTP %s", response.status)
    assert response.status == 200
    booking_id, response_body = _get_created_booking(
        response,
        created_bookings,
    )
    assert response_body["booking"]["firstname"] == firstname
    logger.info("Step 3 result: Booking ID=%s", booking_id)
    logger.info("END | test_create_booking_with_unicode_and_special_characters")


@pytest.mark.order(15)
@pytest.mark.create_booking
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.negative
def test_create_booking_with_hostile_input_strings(
    booking_helper, created_bookings
):
    """Verify hostile-looking strings are handled as data.

    Test steps:
    1. Set SQL-like and script-like input values.
    2. Create the booking.
    3. Verify HTTP 200 and cleanup.
    """
    _log_start("test_create_booking_with_hostile_input_strings")
    payload = read_json("booking_data.json")
    payload["firstname"] = "' OR 1=1 --"
    payload["lastname"] = "<img src=x onerror=alert(1)>"
    payload["additionalneeds"] = "\"; DROP TABLE booking; --"

    response = booking_helper.create_booking(payload=payload)
    logger.info("Step 2 result: HTTP %s", response.status)
    assert response.status == 200
    booking_id, _ = _get_created_booking(response, created_bookings)
    logger.info("Step 3 result: Booking ID=%s", booking_id)
    logger.info("END | test_create_booking_with_hostile_input_strings")


@pytest.mark.order(16)
@pytest.mark.create_booking
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.functional
def test_create_booking_with_unknown_payload_fields(
    booking_helper, created_bookings
):
    """Verify unknown JSON fields do not prevent booking creation.

    Test steps:
    1. Add an unknown field to valid data.
    2. Create the booking.
    3. Verify HTTP 200 and cleanup.
    """
    _log_start("test_create_booking_with_unknown_payload_fields")
    payload = read_json("booking_data.json")
    payload["unexpected_field"] = "ignored"

    response = booking_helper.create_booking(payload=payload)
    logger.info("Step 2 result: HTTP %s", response.status)
    assert response.status == 200
    booking_id, _ = _get_created_booking(response, created_bookings)
    logger.info("Step 3 result: Booking ID=%s", booking_id)
    logger.info("END | test_create_booking_with_unknown_payload_fields")


@pytest.mark.order(17)
@pytest.mark.create_booking
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.functional
def test_create_booking_with_existing_bookingid(
    booking_helper, created_bookings
):
    """Verify a client-supplied bookingid is not trusted.

    Test steps:
    1. Add bookingid=1 to valid payload data.
    2. Create the booking.
    3. Verify the server returns a separate positive ID.
    """
    _log_start("test_create_booking_with_existing_bookingid")
    payload = read_json("booking_data.json")
    payload["bookingid"] = 1

    response = booking_helper.create_booking(payload=payload)
    logger.info("Step 2 result: HTTP %s", response.status)
    assert response.status == 200
    booking_id, _ = _get_created_booking(response, created_bookings)
    assert booking_id != 1
    logger.info("Step 3 result: New Booking ID=%s", booking_id)
    logger.info("END | test_create_booking_with_existing_bookingid")


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param("", id="empty_string"),
        pytest.param("{}", id="empty_json_string"),
        pytest.param("{invalid", id="malformed_json"),
    ],
)
@pytest.mark.order(18)
@pytest.mark.create_booking
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.negative
def test_create_booking_with_invalid_request_bodies(
    booking_helper, payload
):
    """Verify malformed or empty request bodies return an error.

    Test steps:
    1. Send each invalid request body.
    2. Verify the response is not a successful booking creation.
    """
    _log_start("test_create_booking_with_invalid_request_bodies")
    response = booking_helper.create_booking(payload=payload)
    logger.info("Step 1 result: HTTP %s", response.status)

    assert response.status in (400, 500)
    logger.info("Step 2 result: Invalid body rejected")
    logger.info("END | test_create_booking_with_invalid_request_bodies")


@pytest.mark.parametrize(
    "headers",
    [
        pytest.param(
            {"Content-Type": "application/json", "Accept": "application/json"},
            id="json_headers",
        ),
        pytest.param(
            {"Content-Type": "application/json", "Accept": "*/*"},
            id="wildcard_accept",
        ),
    ],
)
@pytest.mark.order(19)
@pytest.mark.create_booking
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.security
def test_create_booking_with_content_type_and_accept_headers(
    booking_helper, created_bookings, headers
):
    """Verify supported content type and accept headers.

    Test steps:
    1. Load valid data.
    2. Create a booking with parameterized headers.
    3. Verify HTTP 200 and cleanup.
    """
    _log_start("test_create_booking_with_content_type_and_accept_headers")
    payload = read_json("booking_data.json")

    response = booking_helper.create_booking(
        payload=payload,
        headers=headers,
    )
    logger.info("Step 2 result: HTTP %s", response.status)
    assert response.status == 200
    booking_id, _ = _get_created_booking(response, created_bookings)
    logger.info("Step 3 result: Booking ID=%s", booking_id)
    logger.info("END | test_create_booking_with_content_type_and_accept_headers")


@pytest.mark.order(20)
@pytest.mark.create_booking
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.functional
def test_create_duplicate_bookings_with_identical_payload(
    booking_helper, created_bookings
):
    """Verify identical payloads create separate bookings.

    Test steps:
    1. Send the same valid payload twice.
    2. Verify both responses return HTTP 200.
    3. Verify the booking IDs are different.
    """
    _log_start("test_create_duplicate_bookings_with_identical_payload")
    payload = read_json("booking_data.json")

    response_a = booking_helper.create_booking(payload=payload)
    logger.info("Step 1 first response: HTTP %s", response_a.status)
    assert response_a.status == 200
    booking_id_a, _ = _get_created_booking(
        response_a,
        created_bookings,
    )

    response_b = booking_helper.create_booking(payload=payload)
    logger.info("Step 1 second response: HTTP %s", response_b.status)
    assert response_b.status == 200
    booking_id_b, _ = _get_created_booking(
        response_b,
        created_bookings,
    )

    assert booking_id_a != booking_id_b
    logger.info(
        "Step 3 result: Booking IDs %s and %s are unique",
        booking_id_a,
        booking_id_b,
    )
    logger.info("END | test_create_duplicate_bookings_with_identical_payload")


@pytest.mark.parametrize(
    "headers",
    [
        pytest.param({}, id="without_authentication"),
        pytest.param(
            {
                "Content-Type": "application/json",
                "Authorization": "Bearer invalid-token",
            },
            id="with_invalid_bearer_token",
        ),
    ],
)
@pytest.mark.order(21)
@pytest.mark.create_booking
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.security
def test_create_booking_with_and_without_authentication(
    booking_helper, created_bookings, headers
):
    """Verify booking creation does not require valid authentication.

    Test steps:
    1. Create a booking without auth or with an invalid bearer token.
    2. Verify HTTP 200.
    3. Verify a positive booking ID and cleanup.
    """
    _log_start("test_create_booking_with_and_without_authentication")
    payload = read_json("booking_data.json")

    response = booking_helper.create_booking(
        payload=payload,
        headers=headers,
    )
    logger.info("Step 1 result: HTTP %s", response.status)
    assert response.status == 200
    booking_id, _ = _get_created_booking(response, created_bookings)
    logger.info("Step 3 result: Booking ID=%s", booking_id)
    logger.info("END | test_create_booking_with_and_without_authentication")
