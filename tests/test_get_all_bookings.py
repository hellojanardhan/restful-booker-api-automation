"""Tests for retrieving and deleting booking records."""

import pytest

from config.config import BOOKER_PASSWORD, BOOKER_USERNAME
from utils.data_generator import read_json
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.order(1)
@pytest.mark.booking_collection
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.functional
def test_get_all_bookings_without_filters(booking_helper):
    """Verify the booking collection is returned without filters."""
    logger.info("START | test_get_all_bookings_without_filters")
    response = booking_helper.get_all_booking_ids()
    logger.info("Step 1 result: HTTP %s", response.status)

    assert response.ok
    assert response.status == 200
    logger.info("END | test_get_all_bookings_without_filters")


@pytest.mark.order(2)
@pytest.mark.booking_collection
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.functional
def test_get_booking_id_present_after_create_and_absent_after_delete(booking_helper):
    """Verify a created booking is present, then absent after deletion.

    Test steps:
    1. Create an authentication token.
    2. Create a booking and capture its ID.
    3. Verify the ID appears in the booking collection.
    4. Verify direct booking lookup succeeds.
    5. Delete the booking with the authentication token.
    6. Verify the ID is absent from the collection and direct lookup returns 404.
    """
    logger.info(
        "START | test_get_booking_id_present_after_create_and_absent_after_delete"
    )

    logger.info("Step 1: Create authentication token")
    token_response = booking_helper.create_auth_token(
        username=BOOKER_USERNAME,
        password=BOOKER_PASSWORD,
    )
    assert token_response.status == 200
    token_body = token_response.json()
    assert token_body.get("token")
    token = token_body["token"]
    logger.info("Step 1 result: Authentication token created")

    logger.info("Step 2: Create booking")
    payload = read_json("booking_data.json")
    response = booking_helper.create_booking(payload=payload)
    logger.info("Step 2 result: HTTP %s", response.status)

    assert response.ok
    assert response.status == 200
    response_body = response.json()
    assert response_body["bookingid"] > 0
    booking_id = response_body["bookingid"]
    logger.info("Step 2 result: Booking ID=%s", booking_id)

    try:
        logger.info("Step 3: Verify booking ID is present in collection")
        collection_response = booking_helper.get_all_booking_ids()
        logger.info("Step 3 result: HTTP %s", collection_response.status)
        assert collection_response.status == 200
        booking_ids = [
            item["bookingid"]
            for item in collection_response.json()
        ]
        assert booking_id in booking_ids
        logger.info("Step 3 result: Booking ID=%s found", booking_id)

        logger.info("Step 4: Verify direct booking lookup succeeds")
        get_response = booking_helper.get_booking_by_id(bookingId=booking_id)
        logger.info("Step 4 result: HTTP %s", get_response.status)
        assert get_response.ok
        assert get_response.status == 200
        assert get_response.json()["firstname"] == payload["firstname"]
        assert get_response.json()["lastname"] == payload["lastname"]
        logger.info("Step 4 result: Booking ID=%s details verified", booking_id)

        logger.info("Step 5: Delete booking")
        delete_response = booking_helper.delete_booking(
            bookingId=booking_id,
            token=token,
        )
        logger.info("Step 5 result: HTTP %s", delete_response.status)
        assert delete_response.status == 201

        logger.info("Step 6: Verify booking ID is absent")
        collection_response = booking_helper.get_all_booking_ids()
        assert collection_response.status == 200
        booking_ids = [
            item["bookingid"]
            for item in collection_response.json()
        ]
        assert booking_id not in booking_ids

        final_get_response = booking_helper.get_booking_by_id(
            bookingId=booking_id
        )
        logger.info(
            "Step 6 result: Collection absence verified; final GET HTTP %s",
            final_get_response.status,
        )
        assert final_get_response.status == 404
        logger.info("END | test_get_booking_id_present_after_create_and_absent_after_delete")
    except Exception:
        logger.exception(
            "Test failed for booking ID=%s; attempting cleanup",
            booking_id,
        )
        try:
            cleanup_response = booking_helper.delete_booking(
                bookingId=booking_id,
                token=token,
            )
            logger.warning(
                "Cleanup attempted for booking ID=%s | HTTP %s",
                booking_id,
                cleanup_response.status,
            )
        except Exception:
            logger.exception(
                "Cleanup failed for booking ID=%s",
                booking_id,
            )
        raise


@pytest.mark.parametrize(
    "firstname, lastname",
    [
        pytest.param("Janardhan", "QA", id="filter_by_janardhan_qa"),
        pytest.param("John", "Smith", id="filter_by_john_smith"),
        pytest.param("David", "Miller", id="filter_by_david_miller"),
    ],
)
@pytest.mark.order(3)
@pytest.mark.booking_collection
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.functional
def test_get_bookings_with_firstname_and_lastname_filters(booking_helper,firstname, lastname):
    """Verify combined firstname and lastname filters return matching bookings.

    Test steps:
    1. Create an authentication token.
    2. Create a booking with the parameterized names.
    3. Request the booking collection with both name filters.
    4. Verify HTTP 200 and the created booking ID in the response.
    5. Delete the created booking during cleanup.
    """
    logger.info(
        "START | test_get_bookings_with_firstname_and_lastname_filters "
        "| firstname=%s | lastname=%s",
        firstname,
        lastname,
    )

    logger.info("Step 1: Create authentication token")
    token_response = booking_helper.create_auth_token(
        username=BOOKER_USERNAME,
        password=BOOKER_PASSWORD,
    )
    assert token_response.status == 200
    token = token_response.json().get("token")
    assert token
    logger.info("Step 1 result: Authentication token created")

    payload = read_json("booking_data.json")
    payload["firstname"] = firstname
    payload["lastname"] = lastname

    logger.info("Step 2: Create filtered-name booking")
    create_response = booking_helper.create_booking(payload=payload)
    logger.info("Step 2 result: HTTP %s", create_response.status)
    assert create_response.status == 200
    create_body = create_response.json()
    booking_id = create_body["bookingid"]
    assert booking_id > 0

    try:
        params = {
            "firstname": firstname,
            "lastname": lastname,
        }
        logger.info("Step 3: Request collection with both name filters")
        response = booking_helper.get_booking_details(params=params)
        logger.info("Step 3 result: HTTP %s", response.status)

        logger.info("Step 4: Verify matching booking ID")
        assert response.ok
        assert response.status == 200
        response_body = response.json()
        assert isinstance(response_body, list)
        matching_ids = [
            item["bookingid"]
            for item in response_body
            if item.get("bookingid") is not None
        ]
        assert booking_id in matching_ids
        logger.info(
            "Step 4 result: Booking ID=%s found with firstname=%s, lastname=%s",
            booking_id,
            firstname,
            lastname,
        )
        logger.info(
            "END | test_get_bookings_with_firstname_and_lastname_filters"
        )
    except Exception:
        logger.exception(
            "Test failed for filtered booking ID=%s",
            booking_id,
        )
        raise
    finally:
        logger.info("Step 5: Clean up created booking")
        cleanup_response = booking_helper.delete_booking(
            bookingId=booking_id,
            token=token,
        )
        logger.info(
            "Step 5 result: HTTP %s",
            cleanup_response.status,
        )


@pytest.mark.order(4)
@pytest.mark.booking_collection
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.functional
def test_get_bookings_with_firstname_filter_only(booking_helper):
    """Verify firstname-only collection filtering.

    Test steps:
    1. Create a uniquely named booking.
    2. Filter the collection by firstname.
    3. Verify HTTP 200 and that the booking ID is returned.
    4. Delete the created booking during cleanup.
    """
    firstname = "FirstnameOnlyFilter"
    logger.info(
        "START | test_get_bookings_with_firstname_filter_only | firstname=%s",
        firstname,
    )
    token_response = booking_helper.create_auth_token(
        username=BOOKER_USERNAME,
        password=BOOKER_PASSWORD,
    )
    assert token_response.status == 200
    token = token_response.json()["token"]
    payload = read_json("booking_data.json")
    payload["firstname"] = firstname

    booking_id = None
    try:
        create_response = booking_helper.create_booking(payload=payload)
        assert create_response.status == 200
        booking_id = create_response.json()["bookingid"]

        response = booking_helper.get_booking_details(
            params={"firstname": firstname}
        )
        assert response.status == 200
        booking_ids = [item["bookingid"] for item in response.json()]
        assert booking_id in booking_ids
        logger.info(
            "END | test_get_bookings_with_firstname_filter_only "
            "| Booking ID=%s found",
            booking_id,
        )
    finally:
        if booking_id is not None:
            cleanup = booking_helper.delete_booking(
                bookingId=booking_id,
                token=token,
            )
            logger.info(
                "Cleanup booking ID=%s | HTTP %s",
                booking_id,
                cleanup.status,
            )


@pytest.mark.order(5)
@pytest.mark.booking_collection
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.functional
def test_get_bookings_with_lastname_filter_only(booking_helper):
    """Verify lastname-only collection filtering.

    Test steps:
    1. Create a uniquely named booking.
    2. Filter the collection by lastname.
    3. Verify HTTP 200 and that the booking ID is returned.
    """
    lastname = "LastnameOnlyFilter"
    logger.info(
        "START | test_get_bookings_with_lastname_filter_only | lastname=%s",
        lastname,
    )
    token_response = booking_helper.create_auth_token(
        username=BOOKER_USERNAME,
        password=BOOKER_PASSWORD,
    )
    assert token_response.status == 200
    token = token_response.json()["token"]
    payload = read_json("booking_data.json")
    payload["lastname"] = lastname

    booking_id = None
    try:
        create_response = booking_helper.create_booking(payload=payload)
        assert create_response.status == 200
        booking_id = create_response.json()["bookingid"]

        response = booking_helper.get_booking_details(
            params={"lastname": lastname}
        )
        assert response.status == 200
        booking_ids = [item["bookingid"] for item in response.json()]
        assert booking_id in booking_ids
        logger.info(
            "END | test_get_bookings_with_lastname_filter_only "
            "| Booking ID=%s found",
            booking_id,
        )
    finally:
        if booking_id is not None:
            cleanup = booking_helper.delete_booking(
                bookingId=booking_id,
                token=token,
            )
            logger.info(
                "Cleanup booking ID=%s | HTTP %s",
                booking_id,
                cleanup.status,
            )


@pytest.mark.order(6)
@pytest.mark.booking_collection
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.functional
def test_get_bookings_with_checkin_date_filter(booking_helper):
    """Verify checkin date filtering."""
    logger.info("START | test_get_bookings_with_checkin_date_filter")
    response = booking_helper.get_booking_details(params={"checkin": "2030-01-10"})
    logger.info("Step result: HTTP %s", response.status)
    assert response.status == 200
    assert isinstance(response.json(), list)
    logger.info("END | test_get_bookings_with_checkin_date_filter")


@pytest.mark.order(7)
@pytest.mark.booking_collection
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.functional
def test_get_bookings_with_checkout_date_filter(booking_helper):
    """Verify checkout date filtering."""
    logger.info("START | test_get_bookings_with_checkout_date_filter")
    response = booking_helper.get_booking_details(params={"checkout": "2030-01-12"})
    logger.info("Step result: HTTP %s", response.status)
    assert response.status == 200
    assert isinstance(response.json(), list)
    logger.info("END | test_get_bookings_with_checkout_date_filter")


@pytest.mark.order(8)
@pytest.mark.booking_collection
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.functional
def test_get_bookings_with_combined_name_and_date_filters(booking_helper):
    """Verify combined name and date filters."""
    logger.info("START | test_get_bookings_with_combined_name_and_date_filters")
    response = booking_helper.get_booking_details(params={
        "firstname": "John",
        "lastname": "Smith",
        "checkin": "2030-01-10",
        "checkout": "2030-01-12",
    })
    logger.info("Step result: HTTP %s", response.status)
    assert response.status == 200
    assert isinstance(response.json(), list)
    logger.info("END | test_get_bookings_with_combined_name_and_date_filters")


@pytest.mark.order(9)
@pytest.mark.booking_collection
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.negative
def test_get_bookings_with_nonexistent_name_filter(booking_helper):
    """Verify a nonexistent name filter returns a valid collection."""
    logger.info("START | test_get_bookings_with_nonexistent_name_filter")
    response = booking_helper.get_booking_details(
        params={"firstname": "NoSuchFirstName987654"}
    )
    logger.info("Step result: HTTP %s", response.status)
    assert response.status == 200
    assert isinstance(response.json(), list)
    logger.info("END | test_get_bookings_with_nonexistent_name_filter")


@pytest.mark.order(10)
@pytest.mark.booking_collection
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.functional
def test_get_bookings_with_case_partial_and_special_character_filters(booking_helper):
    """Verify edge-case name filters are handled without crashing."""
    logger.info("START | test_get_bookings_with_case_partial_and_special_character_filters")
    for firstname in ("john", "Jo", "O'Miller"):
        response = booking_helper.get_booking_details(params={"firstname": firstname})
        logger.info("Filter %s | HTTP %s", firstname, response.status)
        assert response.status == 200
        assert isinstance(response.json(), list)
    logger.info("END | test_get_bookings_with_case_partial_and_special_character_filters")


@pytest.mark.order(11)
@pytest.mark.booking_collection
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.negative
def test_get_bookings_with_invalid_date_filters(booking_helper):
    """Verify invalid date filters produce a handled response."""
    logger.info("START | test_get_bookings_with_invalid_date_filters")
    for date_value in ("2026-02-30", "2026-13-01", "invalid-date"):
        response = booking_helper.get_booking_details(
            params={"checkin": date_value}
        )
        logger.info("Filter %s | HTTP %s", date_value, response.status)
        assert response.status in (200, 400, 500)
    logger.info("END | test_get_bookings_with_invalid_date_filters")


@pytest.mark.order(12)
@pytest.mark.booking_collection
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.negative
def test_get_bookings_with_unknown_and_repeated_query_parameters(booking_helper):
    """Verify unknown and repeated-style query parameters are handled."""
    logger.info("START | test_get_bookings_with_unknown_and_repeated_query_parameters")
    response = booking_helper.get_booking_details(params={
        "unknown_filter": "value",
        "firstname": "John",
    })
    logger.info("Step result: HTTP %s", response.status)
    assert response.status == 200
    assert isinstance(response.json(), list)
    logger.info("END | test_get_bookings_with_unknown_and_repeated_query_parameters")


@pytest.mark.order(13)
@pytest.mark.booking_collection
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.functional
def test_get_bookings_with_sql_injection_and_xss_filter_values(booking_helper):
    """Verify hostile filter values are treated as normal string input."""
    logger.info("START | test_get_bookings_with_sql_injection_and_xss_filter_values")
    for filter_value in ("' OR 1=1 --", "<script>alert(1)</script>"):
        response = booking_helper.get_booking_details(
            params={"firstname": filter_value}
        )
        logger.info("Filter %s | HTTP %s", filter_value, response.status)
        assert response.status == 200
        assert isinstance(response.json(), list)
    logger.info("END | test_get_bookings_with_sql_injection_and_xss_filter_values")


@pytest.mark.order(14)
@pytest.mark.booking_collection
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.negative
def test_unsupported_methods_on_booking_collection(booking_helper):
    """Verify unsupported collection methods are rejected."""
    logger.info("START | test_unsupported_methods_on_booking_collection")
    from config.config import GET_ALL_BOOKING_IDS

    for method in ("PUT", "PATCH", "DELETE"):
        response = booking_helper.rest_helper.execute(
            method=method,
            endpoint=GET_ALL_BOOKING_IDS,
        )
        logger.info("Method %s | HTTP %s", method, response.status)
        assert response.status in (400, 404, 405)
    logger.info("END | test_unsupported_methods_on_booking_collection")
