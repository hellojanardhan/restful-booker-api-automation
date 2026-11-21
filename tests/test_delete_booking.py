import uuid
import pytest

from utils.logger import get_logger
from utils.data_generator import *
from config.config import *

logger = get_logger(__name__)


def _create_unique_booking(booking_helper):
    """Create a booking with unique test data."""
    payload = read_json("booking_data.json")
    payload["firstname"] = f"{payload['firstname']}_{uuid.uuid4().hex[:8]}"

    response = booking_helper.create_booking(payload=payload)

    assert response.ok
    assert response.status == 200

    booking_id = response.json()["bookingid"]
    assert booking_id > 0

    return booking_id, payload


def _generate_auth_token(booking_helper):
    """Generate a valid authentication token."""
    response = booking_helper.create_auth_token(
        username=BOOKER_USERNAME, password=BOOKER_PASSWORD
    )

    assert response.ok
    assert response.status == 200

    token_response = response.json()
    assert "token" in token_response
    assert token_response["token"]

    return token_response["token"]


def _cleanup_booking(booking_helper, booking_id, token):
    """Delete a booking if it still exists."""
    response = booking_helper.get_booking_details(bookingId=booking_id)

    if response.status == 200:
        delete_response = booking_helper.delete_booking(
            bookingId=booking_id, token=token
        )
        assert delete_response.status == 201


@pytest.mark.order(1)
@pytest.mark.delete_booking
@pytest.mark.functional
@pytest.mark.regression
def test_delete_booking_with_valid_token(booking_helper):
    """
    Perform the following steps:
    1. Create a new booking.
    2. Verify that the booking is created successfully.
    3. Generate a new authentication token.
    4. Delete the created booking using the valid token.
    5. Verify that the booking is deleted successfully.
    """

    logger.info("STEP 1: Create a new booking")
    booking_id, payload = _create_unique_booking(booking_helper)

    logger.info("STEP 2: Verify that the booking is created successfully")
    response = booking_helper.get_booking_details(bookingId=booking_id)

    assert response.ok
    assert response.status == 200

    get_response = response.json()
    assert get_response["firstname"] == payload["firstname"]
    assert get_response["lastname"] == payload["lastname"]

    logger.info("STEP 3: Generate a new authentication token")
    token = _generate_auth_token(booking_helper)

    logger.info("STEP 4: Delete the created booking using the valid token")
    response = booking_helper.delete_booking(bookingId=booking_id, token=token)

    assert response.status == 201

    logger.info("STEP 5: Verify that the booking is deleted successfully")
    response = booking_helper.get_booking_details(bookingId=booking_id)

    assert response.status == 404


@pytest.mark.order(2)
@pytest.mark.delete_booking
@pytest.mark.functional
@pytest.mark.regression
def test_deleted_booking_absent_from_booking_list(booking_helper):
    """
    Perform the following steps:
    1. Create a new booking.
    2. Verify that the booking is created successfully.
    3. Generate a new authentication token.
    4. Delete the created booking using the valid token.
    5. Retrieve all booking IDs.
    6. Verify that the deleted booking ID is absent from the booking list.
    """

    logger.info("STEP 1: Create a new booking")
    booking_id, _ = _create_unique_booking(booking_helper)

    logger.info("STEP 2: Verify that the booking is created successfully")
    response = booking_helper.get_booking_details(bookingId=booking_id)

    assert response.status == 200

    logger.info("STEP 3: Generate a new authentication token")
    token = _generate_auth_token(booking_helper)

    logger.info("STEP 4: Delete the created booking")
    response = booking_helper.delete_booking(bookingId=booking_id, token=token)

    assert response.status == 201

    logger.info("STEP 5: Retrieve all booking IDs")
    response = booking_helper.get_all_booking_ids()

    assert response.status == 200
    booking_ids = [item["bookingid"] for item in response.json()]

    logger.info("STEP 6: Verify that the deleted booking ID is absent")
    assert booking_id not in booking_ids


@pytest.mark.order(3)
@pytest.mark.delete_booking
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.negative
def test_delete_booking_without_authentication(booking_helper):
    """
    Perform the following steps:
    1. Create a new booking.
    2. Verify that the booking is created successfully.
    3. Attempt to delete the booking without authentication.
    4. Verify that the deletion request is rejected.
    5. Verify that the booking still exists.
    """

    logger.info("STEP 1: Create a new booking")
    booking_id, _ = _create_unique_booking(booking_helper)

    try:
        logger.info("STEP 2: Verify that the booking is created successfully")
        response = booking_helper.get_booking_details(bookingId=booking_id)

        assert response.status == 200

        logger.info("STEP 3: Attempt to delete the booking without authentication")
        response = booking_helper.delete_booking(bookingId=booking_id)

        assert response.status == 403

        logger.info("STEP 4: Verify that the booking still exists")
        response = booking_helper.get_booking_details(bookingId=booking_id)

        assert response.status == 200

    finally:
        logger.info("CLEANUP: Delete the test booking")
        token = _generate_auth_token(booking_helper)
        _cleanup_booking(booking_helper, booking_id, token)


@pytest.mark.order(4)
@pytest.mark.delete_booking
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.negative
@pytest.mark.parametrize(
    "token",
    ["", "invalid_token", "123456789", "random_invalid_token"],
    ids=["empty_token", "invalid_token", "numeric_token", "random_token"],
)
def test_delete_booking_with_invalid_auth_tokens(booking_helper, token):
    """
    Perform the following steps:
    1. Create a new booking.
    2. Verify that the booking is created successfully.
    3. Attempt to delete the booking using an invalid authentication token.
    4. Verify that the deletion request is rejected.
    5. Verify that the booking still exists.
    """

    logger.info("STEP 1: Create a new booking")
    booking_id, _ = _create_unique_booking(booking_helper)

    try:
        logger.info("STEP 2: Verify that the booking is created successfully")
        response = booking_helper.get_booking_details(bookingId=booking_id)

        assert response.status == 200

        logger.info("STEP 3: Attempt to delete the booking using an invalid token")
        response = booking_helper.delete_booking(bookingId=booking_id, token=token)

        assert response.status == 403

        logger.info("STEP 4: Verify that the booking still exists")
        response = booking_helper.get_booking_details(bookingId=booking_id)

        assert response.status == 200

    finally:
        logger.info("CLEANUP: Delete the test booking")
        valid_token = _generate_auth_token(booking_helper)
        _cleanup_booking(booking_helper, booking_id, valid_token)


@pytest.mark.order(5)
@pytest.mark.delete_booking
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.negative
def test_delete_booking_with_nonexistent_booking_id(booking_helper):
    """
    Perform the following steps:
    1. Generate a new authentication token.
    2. Use a nonexistent booking ID.
    3. Verify that the booking ID does not exist.
    4. Attempt to delete the nonexistent booking using the valid token.
    5. Verify that the deletion request is unsuccessful.
    """

    logger.info("STEP 1: Generate a new authentication token")
    token = _generate_auth_token(booking_helper)

    logger.info("STEP 2: Use a nonexistent booking ID")
    booking_id = 999999999

    logger.info("STEP 3: Verify that the booking ID does not exist")
    response = booking_helper.get_booking_details(bookingId=booking_id)

    assert response.status == 404

    logger.info("STEP 4: Attempt to delete the nonexistent booking")
    response = booking_helper.delete_booking(bookingId=booking_id, token=token)

    logger.info("STEP 5: Verify that the deletion request is unsuccessful")
    assert response.status != 201
    assert response.status < 500


@pytest.mark.order(6)
@pytest.mark.delete_booking
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.negative
def test_delete_same_booking_twice(booking_helper):
    """
    Perform the following steps:
    1. Create a new booking.
    2. Generate a new authentication token.
    3. Delete the created booking using the valid token.
    4. Attempt to delete the same booking again.
    5. Verify that the second deletion request is unsuccessful.
    6. Verify that the booking remains deleted.
    """

    logger.info("STEP 1: Create a new booking")
    booking_id, _ = _create_unique_booking(booking_helper)

    logger.info("STEP 2: Generate a new authentication token")
    token = _generate_auth_token(booking_helper)

    logger.info("STEP 3: Delete the created booking")
    response = booking_helper.delete_booking(bookingId=booking_id, token=token)

    assert response.status == 201

    logger.info("STEP 4: Attempt to delete the same booking again")
    response = booking_helper.delete_booking(bookingId=booking_id, token=token)

    assert response.status != 201
    assert response.status < 500

    logger.info("STEP 5: Verify that the booking remains deleted")
    response = booking_helper.get_booking_details(bookingId=booking_id)

    assert response.status == 404


@pytest.mark.order(7)
@pytest.mark.delete_booking
@pytest.mark.functional
@pytest.mark.regression
def test_delete_booking_does_not_affect_other_bookings(booking_helper):
    """
    Perform the following steps:
    1. Create two different bookings.
    2. Verify that both bookings are created successfully.
    3. Generate a new authentication token.
    4. Delete the first booking using the valid token.
    5. Verify that the first booking is deleted.
    6. Verify that the second booking remains unchanged.
    """

    logger.info("STEP 1: Create two different bookings")
    booking_id1, _ = _create_unique_booking(booking_helper)
    booking_id2, _ = _create_unique_booking(booking_helper)

    token = _generate_auth_token(booking_helper)

    try:
        logger.info("STEP 2: Verify that both bookings are created successfully")

        response = booking_helper.get_booking_details(bookingId=booking_id1)
        assert response.status == 200

        response = booking_helper.get_booking_details(bookingId=booking_id2)
        assert response.status == 200

        second_booking_before_delete = response.json()

        logger.info("STEP 3: Delete the first booking")
        response = booking_helper.delete_booking(bookingId=booking_id1, token=token)

        assert response.status == 201

        logger.info("STEP 4: Verify that the first booking is deleted")
        response = booking_helper.get_booking_details(bookingId=booking_id1)

        assert response.status == 404

        logger.info("STEP 5: Verify that the second booking remains unchanged")
        response = booking_helper.get_booking_details(bookingId=booking_id2)

        assert response.status == 200
        assert response.json() == second_booking_before_delete

    finally:
        logger.info("CLEANUP: Delete remaining test bookings")
        _cleanup_booking(booking_helper, booking_id1, token)
        _cleanup_booking(booking_helper, booking_id2, token)


@pytest.mark.order(8)
@pytest.mark.delete_booking
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.negative
@pytest.mark.parametrize(
    "booking_id",
    [0, -1, "invalid", "1.5", "';--"],
    ids=["zero_id", "negative_id", "alphabetic_id", "decimal_id", "sql_injection_id"],
)
def test_delete_booking_with_invalid_id_formats(booking_helper, booking_id):
    """
    Perform the following steps:
    1. Generate a new authentication token.
    2. Use an invalid booking ID.
    3. Attempt to delete the booking using the valid token.
    4. Verify that the request does not result in a server error.
    5. Verify that the request does not successfully delete a booking.
    """

    logger.info("STEP 1: Generate a new authentication token")
    token = _generate_auth_token(booking_helper)

    logger.info("STEP 2: Create a sentinel booking and use an invalid ID")
    sentinel_id, _ = _create_unique_booking(booking_helper)

    logger.info("STEP 3: Attempt to delete using the invalid booking ID")
    response = booking_helper.delete_booking(bookingId=booking_id, token=token)

    logger.info("STEP 4: Verify that the request does not result in a server error")
    assert response.status < 500

    logger.info("STEP 5: Verify the sentinel booking was not deleted")
    sentinel_response = booking_helper.get_booking_details(
        bookingId=sentinel_id
    )
    assert sentinel_response.status == 200
    _cleanup_booking(booking_helper, sentinel_id, token)


@pytest.mark.order(9)
@pytest.mark.delete_booking
@pytest.mark.functional
@pytest.mark.regression
@pytest.mark.negative
def test_put_and_patch_do_not_resurrect_deleted_booking(booking_helper):
    """
    Perform the following steps:
    1. Create a new booking.
    2. Generate a new authentication token.
    3. Delete the created booking.
    4. Verify that the booking is deleted successfully.
    5. Attempt to update the deleted booking using PUT.
    6. Verify that PUT does not recreate the booking.
    7. Attempt to partially update the deleted booking using PATCH.
    8. Verify that PATCH does not recreate the booking.
    """

    logger.info("STEP 1: Create a new booking")
    booking_id, payload = _create_unique_booking(booking_helper)

    logger.info("STEP 2: Generate a new authentication token")
    token = _generate_auth_token(booking_helper)

    logger.info("STEP 3: Delete the created booking")
    response = booking_helper.delete_booking(bookingId=booking_id, token=token)

    assert response.status == 201

    logger.info("STEP 4: Verify that the booking is deleted successfully")
    response = booking_helper.get_booking_details(bookingId=booking_id)

    assert response.status == 404

    logger.info("STEP 5: Attempt to update the deleted booking using PUT")
    put_response = booking_helper.update_booking(
        bookingId=booking_id, payload=payload, token=token
    )

    assert put_response.status != 200

    logger.info("STEP 6: Verify that PUT does not recreate the booking")
    response = booking_helper.get_booking_details(bookingId=booking_id)

    assert response.status == 404

    logger.info("STEP 7: Attempt to partially update the deleted booking using PATCH")
    patch_response = booking_helper.partial_update_booking(
        bookingId=booking_id, payload={"firstname": "UpdatedName"}, token=token
    )

    assert patch_response.status != 200

    logger.info("STEP 8: Verify that PATCH does not recreate the booking")
    response = booking_helper.get_booking_details(bookingId=booking_id)

    assert response.status == 404
