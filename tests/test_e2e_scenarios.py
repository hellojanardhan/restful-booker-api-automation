import pytest
from concurrent.futures import ThreadPoolExecutor
from config.config import BOOKER_USERNAME, BOOKER_PASSWORD
from utils.logger import get_logger
from utils.data_generator import *

logger = get_logger(__name__)


def create_booking(booking_helper):
    payload = read_json("booking_data.json")
    payload["firstname"] = generate_firstname()
    payload["lastname"] = generate_lastname()
    payload["totalprice"] = generate_totalprice()
    payload["depositpaid"] = generate_depositpaid()
    payload["bookingdates"]["checkin"] = generate_checkin()

    response = booking_helper.create_booking(payload=payload)

    assert response.status == 200

    response_body = response.json()
    booking_id = response_body["bookingid"]

    assert booking_id > 0

    return booking_id, payload


def create_token(booking_helper):
    response = booking_helper.create_auth_token(
        username=BOOKER_USERNAME, password=BOOKER_PASSWORD
    )

    assert response.status == 200

    token = response.json()["token"]
    assert token

    return token


@pytest.mark.e2e
@pytest.mark.order(1)
def test_e2e_booking_creation_and_retrieval(booking_helper):
    """
    Perform the following steps:
    1. Create a new booking.
    2. Verify that the booking is created successfully.
    3. Retrieve and validate the booking details.
    4. Generate an authentication token.
    5. Delete the created booking.
    6. Verify that the booking is deleted successfully.
    """

    logger.info("STEP 1: Create a new booking")

    payload = read_json("booking_data.json")
    payload["firstname"] = generate_firstname()
    payload["lastname"] = generate_lastname()
    payload["totalprice"] = generate_totalprice()
    payload["depositpaid"] = generate_depositpaid()
    payload["bookingdates"]["checkin"] = generate_checkin()

    response = booking_helper.create_booking(payload=payload)

    assert response.ok
    assert response.status == 200

    response_body = response.json()
    booking_id = response_body["bookingid"]

    assert booking_id > 0
    assert response_body["booking"]["firstname"] == payload["firstname"]
    assert response_body["booking"]["lastname"] == payload["lastname"]
    assert response_body["booking"]["totalprice"] == payload["totalprice"]
    assert response_body["booking"]["depositpaid"] == payload["depositpaid"]
    assert response_body["booking"]["bookingdates"] == payload["bookingdates"]

    logger.info("Booking created successfully. Booking ID: %s", booking_id)

    logger.info("STEP 2: Retrieve and verify booking details")

    get_response = booking_helper.get_booking_details(bookingId=booking_id)

    assert get_response.status == 200

    get_response_body = get_response.json()

    assert get_response_body["firstname"] == payload["firstname"]
    assert get_response_body["lastname"] == payload["lastname"]
    assert get_response_body["totalprice"] == payload["totalprice"]
    assert get_response_body["depositpaid"] == payload["depositpaid"]
    assert get_response_body["bookingdates"] == payload["bookingdates"]

    logger.info("Booking details verified successfully")

    logger.info("STEP 3: Generate authentication token")

    token = create_token(booking_helper)

    logger.info("STEP 4: Delete the created booking")

    delete_response = booking_helper.delete_booking(bookingId=booking_id, token=token)

    assert delete_response.status == 201

    logger.info("STEP 5: Verify booking deletion")

    deleted_response = booking_helper.get_booking_details(bookingId=booking_id)

    assert deleted_response.status == 404

    logger.info("Booking deletion verified successfully")


@pytest.mark.e2e
@pytest.mark.order(2)
def test_e2e_complete_booking_lifecycle(booking_helper):
    """
    Perform the following steps:
    1. Create a new booking.
    2. Verify booking creation.
    3. Retrieve and validate booking details.
    4. Generate an authentication token.
    5. Update complete booking details using PUT.
    6. Verify the PUT update.
    7. Partially update booking details using PATCH.
    8. Verify changed and unchanged fields.
    9. Delete the booking.
    10. Verify booking deletion.
    """

    logger.info("STEP 1: Create a new booking")

    booking_id, payload = create_booking(booking_helper)

    get_response = booking_helper.get_booking_details(bookingId=booking_id)

    assert get_response.status == 200

    get_body = get_response.json()

    assert get_body["firstname"] == payload["firstname"]
    assert get_body["lastname"] == payload["lastname"]
    assert get_body["totalprice"] == payload["totalprice"]
    assert get_body["depositpaid"] == payload["depositpaid"]
    assert get_body["bookingdates"] == payload["bookingdates"]

    logger.info("STEP 2: Generate authentication token")

    token = create_token(booking_helper)

    logger.info("STEP 3: Update complete booking using PUT")

    updated_payload = {
        "firstname": generate_firstname(),
        "lastname": generate_lastname(),
        "totalprice": generate_totalprice(),
        "depositpaid": generate_depositpaid(),
        "bookingdates": {
            "checkin": generate_checkin(),
            "checkout": payload["bookingdates"]["checkout"],
        },
        "additionalneeds": generate_additionalneeds(),
    }

    update_response = booking_helper.update_booking(
        bookingId=booking_id, payload=updated_payload, token=token
    )

    assert update_response.status == 200

    update_body = update_response.json()

    assert update_body["firstname"] == updated_payload["firstname"]
    assert update_body["lastname"] == updated_payload["lastname"]
    assert update_body["totalprice"] == updated_payload["totalprice"]
    assert update_body["depositpaid"] == updated_payload["depositpaid"]
    assert update_body["bookingdates"] == updated_payload["bookingdates"]
    assert update_body["additionalneeds"] == updated_payload["additionalneeds"]

    logger.info("STEP 4: Partially update booking using PATCH")

    partial_payload = {
        "firstname": generate_firstname(),
        "totalprice": generate_totalprice(),
    }

    patch_response = booking_helper.partial_update_booking(
        bookingId=booking_id, payload=partial_payload, token=token
    )

    assert patch_response.status == 200

    patch_body = patch_response.json()

    assert patch_body["firstname"] == partial_payload["firstname"]
    assert patch_body["totalprice"] == partial_payload["totalprice"]
    assert patch_body["lastname"] == updated_payload["lastname"]
    assert patch_body["depositpaid"] == updated_payload["depositpaid"]
    assert patch_body["bookingdates"] == updated_payload["bookingdates"]
    assert patch_body["additionalneeds"] == updated_payload["additionalneeds"]

    logger.info("STEP 5: Delete booking")

    delete_response = booking_helper.delete_booking(bookingId=booking_id, token=token)

    assert delete_response.status == 201

    logger.info("STEP 6: Verify booking deletion")

    deleted_response = booking_helper.get_booking_details(bookingId=booking_id)

    assert deleted_response.status == 404

    logger.info("Complete booking lifecycle verified successfully")


@pytest.mark.e2e
@pytest.mark.order(3)
def test_e2e_update_and_delete_booking_data_integrity(booking_helper):
    """
    Perform the following steps:
    1. Create two bookings.
    2. Generate authentication token.
    3. Update the first booking.
    4. Verify the updated booking.
    5. Delete the first booking.
    6. Verify the first booking is deleted.
    7. Verify the second booking remains unchanged.
    8. Delete the second booking.
    """

    logger.info("STEP 1: Create two bookings")

    booking_id_1, payload_1 = create_booking(booking_helper)
    booking_id_2, payload_2 = create_booking(booking_helper)

    logger.info("STEP 2: Generate authentication token")

    token = create_token(booking_helper)

    logger.info("STEP 3: Update first booking")

    updated_payload = {
        "firstname": generate_firstname(),
        "lastname": generate_lastname(),
        "totalprice": generate_totalprice(),
        "depositpaid": generate_depositpaid(),
        "bookingdates": payload_1["bookingdates"],
        "additionalneeds": generate_additionalneeds(),
    }

    update_response = booking_helper.update_booking(
        bookingId=booking_id_1, payload=updated_payload, token=token
    )

    assert update_response.status == 200

    logger.info("STEP 4: Verify first booking update")

    update_body = update_response.json()

    assert update_body["firstname"] == updated_payload["firstname"]
    assert update_body["lastname"] == updated_payload["lastname"]

    logger.info("STEP 5: Delete first booking")

    delete_response = booking_helper.delete_booking(bookingId=booking_id_1, token=token)

    assert delete_response.status == 201

    assert booking_helper.get_booking_details(bookingId=booking_id_1).status == 404

    logger.info("STEP 6: Verify second booking remains unchanged")

    second_response = booking_helper.get_booking_details(bookingId=booking_id_2)

    assert second_response.status == 200

    second_body = second_response.json()

    assert second_body["firstname"] == payload_2["firstname"]
    assert second_body["lastname"] == payload_2["lastname"]
    assert second_body["totalprice"] == payload_2["totalprice"]

    logger.info("STEP 7: Delete second booking")

    second_delete = booking_helper.delete_booking(bookingId=booking_id_2, token=token)

    assert second_delete.status == 201


@pytest.mark.e2e
@pytest.mark.order(4)
def test_e2e_unauthorized_and_authorized_booking_operations(booking_helper):
    """
    Perform the following steps:
    1. Create a booking.
    2. Attempt PUT without authentication.
    3. Verify unauthorized PUT is rejected.
    4. Attempt PATCH with an invalid token.
    5. Verify unauthorized PATCH is rejected.
    6. Attempt DELETE without authentication.
    7. Verify unauthorized DELETE is rejected.
    8. Generate a valid token.
    9. Update the booking with valid authentication.
    10. Delete the booking with valid authentication.
    11. Verify booking deletion.
    """

    logger.info("STEP 1: Create booking")

    booking_id, payload = create_booking(booking_helper)

    updated_payload = {
        "firstname": generate_firstname(),
        "lastname": payload["lastname"],
        "totalprice": generate_totalprice(),
        "depositpaid": payload["depositpaid"],
        "bookingdates": payload["bookingdates"],
        "additionalneeds": generate_additionalneeds(),
    }

    logger.info("STEP 2: Attempt PUT without authentication")

    put_response = booking_helper.update_booking(
        bookingId=booking_id, payload=updated_payload, token=""
    )

    assert put_response.status == 403

    logger.info("STEP 3: Verify booking remains unchanged")

    get_response = booking_helper.get_booking_details(bookingId=booking_id)

    assert get_response.status == 200
    assert get_response.json()["firstname"] == payload["firstname"]

    logger.info("STEP 4: Attempt PATCH with invalid token")

    patch_response = booking_helper.partial_update_booking(
        bookingId=booking_id,
        payload={"firstname": generate_firstname()},
        token="invalid_token",
    )

    assert patch_response.status == 403

    logger.info("STEP 5: Attempt DELETE without authentication")

    delete_response = booking_helper.delete_booking(bookingId=booking_id, token="")

    assert delete_response.status == 403

    logger.info("STEP 6: Generate valid token")

    token = create_token(booking_helper)

    logger.info("STEP 7: Perform authorized PUT")

    authorized_response = booking_helper.update_booking(
        bookingId=booking_id, payload=updated_payload, token=token
    )

    assert authorized_response.status == 200

    logger.info("STEP 8: Delete booking with valid token")

    authorized_delete = booking_helper.delete_booking(bookingId=booking_id, token=token)

    assert authorized_delete.status == 201

    logger.info("STEP 9: Verify booking deletion")

    assert booking_helper.get_booking_details(bookingId=booking_id).status == 404


@pytest.mark.e2e
@pytest.mark.order(5)
def test_e2e_reuse_authentication_token_across_multiple_bookings(booking_helper):
    """
    Perform the following steps:
    1. Generate one authentication token.
    2. Create two bookings.
    3. Update both bookings using the same token.
    4. Verify both booking updates.
    5. Delete both bookings using the same token.
    6. Verify both bookings are deleted.
    """

    logger.info("STEP 1: Generate authentication token")

    token = create_token(booking_helper)

    logger.info("STEP 2: Create two bookings")

    booking_id_1, payload_1 = create_booking(booking_helper)
    booking_id_2, payload_2 = create_booking(booking_helper)

    updated_payload_1 = {
        "firstname": generate_firstname(),
        "lastname": payload_1["lastname"],
        "totalprice": generate_totalprice(),
        "depositpaid": payload_1["depositpaid"],
        "bookingdates": payload_1["bookingdates"],
        "additionalneeds": generate_additionalneeds(),
    }

    updated_payload_2 = {
        "firstname": generate_firstname(),
        "lastname": payload_2["lastname"],
        "totalprice": generate_totalprice(),
        "depositpaid": payload_2["depositpaid"],
        "bookingdates": payload_2["bookingdates"],
        "additionalneeds": generate_additionalneeds(),
    }

    logger.info("STEP 3: Update first booking")

    response_1 = booking_helper.update_booking(
        bookingId=booking_id_1, payload=updated_payload_1, token=token
    )

    assert response_1.status == 200

    logger.info("STEP 4: Update second booking using same token")

    response_2 = booking_helper.update_booking(
        bookingId=booking_id_2, payload=updated_payload_2, token=token
    )

    assert response_2.status == 200

    logger.info("STEP 5: Verify both updates")

    assert (
        booking_helper.get_booking_details(bookingId=booking_id_1).json()["firstname"]
        == updated_payload_1["firstname"]
    )

    assert (
        booking_helper.get_booking_details(bookingId=booking_id_2).json()["firstname"]
        == updated_payload_2["firstname"]
    )

    logger.info("STEP 6: Delete both bookings")

    delete_1 = booking_helper.delete_booking(bookingId=booking_id_1, token=token)

    delete_2 = booking_helper.delete_booking(bookingId=booking_id_2, token=token)

    assert delete_1.status == 201
    assert delete_2.status == 201

    logger.info("STEP 7: Verify both deletions")

    assert booking_helper.get_booking_details(bookingId=booking_id_1).status == 404

    assert booking_helper.get_booking_details(bookingId=booking_id_2).status == 404
