import copy
import pytest
from config.config import BOOKER_PASSWORD, BOOKER_USERNAME
from utils.logger import get_logger
from utils.data_generator import *
logger = get_logger(__name__)


@pytest.fixture(autouse=True)
def cleanup_created_bookings(booking_helper, monkeypatch):
    """Track and remove bookings created by each PUT test."""
    created_booking_ids = []
    create_booking = booking_helper.create_booking

    def track_create_booking(*args, **kwargs):
        response = create_booking(*args, **kwargs)
        if response.status == 200:
            booking_id = response.json().get("bookingid")
            if booking_id is not None and booking_id not in created_booking_ids:
                created_booking_ids.append(booking_id)
        return response

    monkeypatch.setattr(booking_helper, "create_booking", track_create_booking)
    yield

    if not created_booking_ids:
        return

    auth_response = booking_helper.create_auth_token(
        username=BOOKER_USERNAME,
        password=BOOKER_PASSWORD,
    )
    assert auth_response.status == 200
    token = auth_response.json()["token"]

    for booking_id in reversed(created_booking_ids):
        get_response = booking_helper.get_booking_by_id(booking_id)
        if get_response.status == 404:
            continue
        assert get_response.status == 200

        delete_response = booking_helper.delete_booking(
            bookingId=booking_id,
            token=token,
        )
        assert delete_response.status == 201
        logger.info("Cleaned up test booking ID=%s", booking_id)


@pytest.mark.order(1)
@pytest.mark.security
@pytest.mark.update_booking
@pytest.mark.authorization
def test_update_booking_with_valid_token_and_complete_payload(booking_helper):
    """
    Steps:
    1. Create a new booking
    2. Verify booking is created
    3. Create Auth token
    4. Update the booking with the valid token
    5. Verify the booking is updated
    """

    logger.info("STEP 1: Creating a new booking")

    payload = read_json("booking_data.json")
    create_response = booking_helper.create_booking(payload=payload)

    assert create_response.status == 200
    booking_id = create_response.json()["bookingid"]

    logger.info(f"Booking created successfully. Booking ID: {booking_id}")

    logger.info("STEP 2: Verifying the booking")

    get_response = booking_helper.get_booking_by_id(booking_id)

    assert get_response.status == 200
    logger.info("Booking verification successful")

    logger.info("STEP 3: Creating authentication token")

    auth_response = booking_helper.create_auth_token(username=BOOKER_USERNAME, password=BOOKER_PASSWORD)

    assert auth_response.status == 200
    token = auth_response.json()["token"]

    logger.info("Authentication token created successfully")

    logger.info("STEP 4: Updating the booking")

    updated_payload = payload.copy()
    updated_payload["firstname"] = "Updated"
    updated_payload["lastname"] = "Booking"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Cookie": f"token={token}",
    }

    update_response = booking_helper.update_booking(
        bookingId=booking_id, payload=updated_payload, headers=headers
    )

    assert update_response.status == 200
    logger.info(f"Booking ID {booking_id} updated successfully")

    logger.info("STEP 5: Verifying the updated booking")

    final_response = booking_helper.get_booking_by_id(booking_id)

    assert final_response.status == 200
    assert final_response.json() == updated_payload

    logger.info("Booking update verification successful")


@pytest.mark.order(2)
@pytest.mark.functional
@pytest.mark.update_booking
@pytest.mark.authorization
def test_update_booking_response_and_data_integrity(booking_helper):

    logger.info("STEP 1: Creating a new booking")

    payload = read_json("booking_data.json")
    create_response = booking_helper.create_booking(payload=payload)

    assert create_response.status == 200
    booking_id = create_response.json()["bookingid"]

    logger.info(f"Booking created successfully. ID: {booking_id}")

    logger.info("STEP 2: Creating authentication token")

    auth_response = booking_helper.create_auth_token(username=BOOKER_USERNAME, password=BOOKER_PASSWORD)
    assert auth_response.status == 200
    token = auth_response.json()["token"]

    logger.info("STEP 3: Preparing replacement payload")

    updated_payload = copy.deepcopy(payload)
    updated_payload["firstname"] = "Updated"
    updated_payload["lastname"] = "Booking"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Cookie": f"token={token}",
    }

    logger.info("STEP 4: Updating booking")

    update_response = booking_helper.update_booking(
        bookingId=booking_id, payload=updated_payload, headers=headers
    )

    assert update_response.status == 200

    logger.info("STEP 5: Verifying updated booking")

    get_response = booking_helper.get_booking_by_id(booking_id)

    assert get_response.status == 200
    assert get_response.json() == updated_payload

    logger.info("Booking updated and verified successfully")

@pytest.mark.parametrize(
    "missing_field",
    [
        pytest.param("firstname", id="missing_firstname"),
        pytest.param("lastname", id="missing_lastname"),
        pytest.param("totalprice", id="missing_totalprice"),
        pytest.param("depositpaid", id="missing_depositpaid"),
        pytest.param("bookingdates", id="missing_bookingdates"),
        pytest.param("additionalneeds", id="missing_additionalneeds"),
    ],
)
@pytest.mark.order(3)
@pytest.mark.negative
@pytest.mark.update_booking
@pytest.mark.authorization
def test_update_booking_with_missing_fields(booking_helper, missing_field):

    logger.info(f"STEP 1: Testing missing field: {missing_field}")

    payload = read_json("booking_data.json")
    create_response = booking_helper.create_booking(payload=payload)

    assert create_response.status == 200
    booking_id = create_response.json()["bookingid"]

    logger.info(f"Booking created. ID: {booking_id}")

    auth_response = booking_helper.create_auth_token(username=BOOKER_USERNAME, password=BOOKER_PASSWORD)
    assert auth_response.status == 200
    token = auth_response.json()["token"]

    updated_payload = copy.deepcopy(payload)
    updated_payload.pop(missing_field, None)

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Cookie": f"token={token}",
    }

    logger.info(f"STEP 2: Updating booking without {missing_field}")

    response = booking_helper.update_booking(
        bookingId=booking_id, payload=updated_payload, headers=headers
    )

    logger.info(f"Update response status: {response.status}")

    logger.info("STEP 3: Verifying booking using GET")

    get_response = booking_helper.get_booking_by_id(booking_id)

    assert get_response.status == 200

    logger.info(f"Booking state after missing {missing_field}: {get_response.json()}")


@pytest.mark.order(4)
@pytest.mark.security
@pytest.mark.update_booking
@pytest.mark.authorization
def test_update_booking_without_authentication(booking_helper):

    logger.info("STEP 1: Creating booking")

    payload = read_json("booking_data.json")
    create_response = booking_helper.create_booking(payload=payload)

    assert create_response.status == 200
    booking_id = create_response.json()["bookingid"]

    original_booking = booking_helper.get_booking_by_id(booking_id).json()

    logger.info("STEP 2: Updating without authentication")

    updated_payload = copy.deepcopy(payload)
    updated_payload["firstname"] = "Unauthorized"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    response = booking_helper.update_booking(
        bookingId=booking_id,
        payload=updated_payload,
        headers=headers
    )

    assert response.status == 403

    logger.info("STEP 3: Verifying booking remains unchanged")

    get_response = booking_helper.get_booking_by_id(booking_id)

    assert get_response.json() == original_booking

    logger.info("Unauthenticated update rejected successfully")


@pytest.mark.parametrize(
    "token_type",
    [
        pytest.param("empty", id="empty_token"),
        pytest.param("altered", id="altered_token"),
        pytest.param("random", id="random_token"),
    ],
)
@pytest.mark.order(5)
@pytest.mark.negative
@pytest.mark.update_booking
@pytest.mark.authorization
def test_update_booking_with_invalid_auth_tokens(booking_helper, token_type):

    logger.info(f"STEP 1: Testing token type: {token_type}")

    payload = read_json("booking_data.json")
    create_response = booking_helper.create_booking(payload=payload)

    assert create_response.status == 200
    booking_id = create_response.json()["bookingid"]

    original_booking = booking_helper.get_booking_by_id(booking_id).json()

    auth_response = booking_helper.create_auth_token(username=BOOKER_USERNAME, password=BOOKER_PASSWORD)
    assert auth_response.status == 200
    valid_token = auth_response.json()["token"]

    if token_type == "empty":
        token = ""
    elif token_type == "altered":
        token = valid_token[:-1] + ("0" if valid_token[-1] != "0" else "1")
    else:
        token = "invalid_random_token_123"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Cookie": f"token={token}",
    }

    updated_payload = copy.deepcopy(payload)
    updated_payload["firstname"] = "Unauthorized"

    logger.info("STEP 2: Sending PUT with invalid token")

    response = booking_helper.update_booking(
        bookingId=booking_id, payload=updated_payload, headers=headers
    )

    assert response.status == 403

    logger.info("STEP 3: Verifying original booking")

    get_response = booking_helper.get_booking_by_id(booking_id)

    assert get_response.json() == original_booking

    logger.info("Invalid token rejected successfully")


@pytest.mark.order(6)
@pytest.mark.negative
@pytest.mark.update_booking
@pytest.mark.authorization
def test_update_booking_with_nonexistent_booking_id(booking_helper):

    logger.info("STEP 1: Creating authentication token")

    auth_response = booking_helper.create_auth_token(username=BOOKER_USERNAME, password=BOOKER_PASSWORD)
    assert auth_response.status == 200
    token = auth_response.json()["token"]

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Cookie": f"token={token}",
    }

    payload = read_json("booking_data.json")

    logger.info("STEP 2: Updating nonexistent booking")

    bad_id = 999999999

    response = booking_helper.update_booking(
        bookingId=bad_id, payload=payload, headers=headers
    )

    assert response.status == 405

    logger.info("STEP 3: Verifying nonexistent booking")

    get_response = booking_helper.get_booking_by_id(bad_id)

    assert get_response.status == 404


@pytest.mark.parametrize(
    "accept",
    [
        pytest.param(None, id="missing_accept"),
        pytest.param(
            "text/plain",
            id="text_plain",
            marks=pytest.mark.xfail(
                strict=True,
                reason="The hosted API returns 418 but still applies the PUT update.",
            ),
        ),
        pytest.param(
            "invalid",
            id="invalid_accept",
            marks=pytest.mark.xfail(
                strict=True,
                reason="The hosted API returns 418 but still applies the PUT update.",
            ),
        ),
    ],
)
@pytest.mark.order(7)
@pytest.mark.functional
@pytest.mark.update_booking
@pytest.mark.authorization
def test_update_booking_with_missing_or_unsupported_accept_header(
    booking_helper, accept
):
    """Verify missing and unsupported Accept headers do not hide PUT outcomes."""
    logger.info("STEP 1: Testing Accept header: %s", accept)

    payload = read_json("booking_data.json")
    create_response = booking_helper.create_booking(payload=payload)

    assert create_response.status == 200
    booking_id = create_response.json()["bookingid"]

    original_booking = booking_helper.get_booking_by_id(booking_id).json()

    auth_response = booking_helper.create_auth_token(
        username=BOOKER_USERNAME,
        password=BOOKER_PASSWORD,
    )
    assert auth_response.status == 200
    token = auth_response.json()["token"]

    headers = {"Content-Type": "application/json", "Cookie": f"token={token}"}

    if accept is not None:
        headers["Accept"] = accept

    updated_payload = copy.deepcopy(payload)
    updated_payload["firstname"] = "AcceptTest"

    logger.info("STEP 2: Sending PUT request")

    response = booking_helper.update_booking(
        bookingId=booking_id, payload=updated_payload, headers=headers
    )

    logger.info("Response status: %s", response.status)
    expected_status = 200 if accept is None else 418
    assert response.status == expected_status

    logger.info("STEP 3: Verifying booking state")

    get_response = booking_helper.get_booking_by_id(booking_id)
    assert get_response.status == 200
    expected_booking = updated_payload if accept is None else original_booking
    assert get_response.json() == expected_booking


@pytest.mark.parametrize(
    "body, content_type",
    [
        pytest.param("{", "application/json", id="malformed_json"),
        pytest.param("", "application/json", id="empty_body"),
        pytest.param("[]", "application/json", id="array_body"),
        pytest.param('{"firstname":"Test"}', "text/plain", id="wrong_content_type"),
    ],
)
@pytest.mark.order(8)
@pytest.mark.negative
@pytest.mark.update_booking
@pytest.mark.authorization
def test_update_booking_with_invalid_request_bodies(booking_helper, body, content_type):

    logger.info("STEP 1: Creating booking")

    payload = read_json("booking_data.json")
    create_response = booking_helper.create_booking(payload=payload)

    assert create_response.status == 200
    booking_id = create_response.json()["bookingid"]

    original_booking = booking_helper.get_booking_by_id(booking_id).json()

    auth_response = booking_helper.create_auth_token(username=BOOKER_USERNAME, password=BOOKER_PASSWORD)
    assert auth_response.status == 200
    token = auth_response.json()["token"]

    headers = {
        "Content-Type": content_type,
        "Accept": "application/json",
        "Cookie": f"token={token}",
    }

    logger.info(f"STEP 2: Sending invalid body: {body}")

    response = booking_helper.update_booking(
        bookingId=booking_id, payload=body, headers=headers
    )

    logger.info(f"Response status: {response.status}")

    logger.info("STEP 3: Verifying booking state")

    get_response = booking_helper.get_booking_by_id(booking_id)
    assert get_response.json() == original_booking


@pytest.mark.parametrize(
    "missing_field",
    [
        pytest.param("firstname", id="missing_firstname"),
        pytest.param("lastname", id="missing_lastname"),
        pytest.param("totalprice", id="missing_totalprice"),
        pytest.param("depositpaid", id="missing_depositpaid"),
        pytest.param("bookingdates", id="missing_bookingdates"),
    ],
)
@pytest.mark.order(9)
@pytest.mark.negative
@pytest.mark.update_booking
@pytest.mark.authorization
def test_update_booking_with_missing_required_fields(booking_helper, missing_field):

    logger.info(f"STEP 1: Testing missing field: {missing_field}")

    payload = read_json("booking_data.json")
    create_response = booking_helper.create_booking(payload=payload)

    assert create_response.status == 200
    booking_id = create_response.json()["bookingid"]

    auth_response = booking_helper.create_auth_token(username=BOOKER_USERNAME, password=BOOKER_PASSWORD)
    assert auth_response.status == 200
    token = auth_response.json()["token"]

    original_payload = copy.deepcopy(payload)
    payload.pop(missing_field, None)

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Cookie": f"token={token}",
    }

    logger.info("STEP 2: Updating with missing required field")

    response = booking_helper.update_booking(
        bookingId=booking_id, payload=payload, headers=headers
    )

    logger.info(f"Response status: {response.status}")

    logger.info("STEP 3: Retrieving updated booking")

    get_response = booking_helper.get_booking_by_id(booking_id)

    assert get_response.status == 200

    logger.info(f"Original payload: {original_payload}")
    logger.info(f"Resulting payload: {get_response.json()}")


@pytest.mark.parametrize(
    "field, value",
    [
        pytest.param("totalprice", "abc", id="totalprice_string"),
        pytest.param("totalprice", None, id="totalprice_null"),
        pytest.param("depositpaid", "true", id="depositpaid_string"),
        pytest.param("depositpaid", 1, id="depositpaid_integer"),
        pytest.param("firstname", 123, id="firstname_integer"),
        pytest.param("lastname", [], id="lastname_list"),
    ],
)
@pytest.mark.order(10)
@pytest.mark.negative
@pytest.mark.update_booking
@pytest.mark.authorization
def test_update_booking_with_invalid_data_types_and_dates(booking_helper, field, value):

    logger.info(f"STEP 1: Testing {field} with value {value}")

    payload = read_json("booking_data.json")
    create_response = booking_helper.create_booking(payload=payload)

    assert create_response.status == 200
    booking_id = create_response.json()["bookingid"]

    auth_response = booking_helper.create_auth_token(username=BOOKER_USERNAME, password=BOOKER_PASSWORD)
    assert auth_response.status == 200
    token = auth_response.json()["token"]

    updated_payload = copy.deepcopy(payload)

    if field in ("checkin", "checkout"):
        updated_payload["bookingdates"][field] = value
    else:
        updated_payload[field] = value

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Cookie": f"token={token}",
    }

    logger.info("STEP 2: Sending PUT request with invalid value")

    response = booking_helper.update_booking(
        bookingId=booking_id, payload=updated_payload, headers=headers
    )

    logger.info(f"Response status: {response.status}")

    logger.info("STEP 3: Checking stored booking")

    get_response = booking_helper.get_booking_by_id(booking_id)

    assert get_response.status == 200
    logger.info(f"Stored booking: {get_response.json()}")


@pytest.mark.parametrize(
    "field, value",
    [
        pytest.param("totalprice", 0, id="zero_price"),
        pytest.param("totalprice", 1, id="minimum_price"),
        pytest.param("totalprice", -1, id="negative_price"),
        pytest.param("totalprice", 2147483647, id="max_integer"),
        pytest.param("firstname", "A" * 255, id="firstname_255"),
        pytest.param("firstname", "A" * 256, id="firstname_256"),
        pytest.param("firstname", "Janardhan😊", id="unicode_name"),
    ],
)
@pytest.mark.order(11)
@pytest.mark.functional
@pytest.mark.update_booking
@pytest.mark.authorization
def test_update_booking_with_boundary_values(booking_helper, field, value):

    logger.info(f"STEP 1: Testing boundary value for {field}")

    payload = read_json("booking_data.json")
    create_response = booking_helper.create_booking(payload=payload)

    assert create_response.status == 200
    booking_id = create_response.json()["bookingid"]

    auth_response = booking_helper.create_auth_token(username=BOOKER_USERNAME, password=BOOKER_PASSWORD)
    assert auth_response.status == 200
    token = auth_response.json()["token"]

    updated_payload = copy.deepcopy(payload)
    updated_payload[field] = value

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Cookie": f"token={token}",
    }

    logger.info("STEP 2: Updating with boundary value")

    response = booking_helper.update_booking(
        bookingId=booking_id, payload=updated_payload, headers=headers
    )

    assert response.status < 500

    logger.info("STEP 3: Verifying stored value")

    get_response = booking_helper.get_booking_by_id(booking_id)
    assert get_response.status == 200

    if response.status == 200:
        assert get_response.json()[field] == value


@pytest.mark.order(12)
@pytest.mark.functional
@pytest.mark.update_booking
@pytest.mark.authorization
def test_update_booking_with_identical_payload_twice(booking_helper):

    logger.info("STEP 1: Creating booking")

    payload = read_json("booking_data.json")
    create_response = booking_helper.create_booking(payload=payload)

    assert create_response.status == 200
    booking_id = create_response.json()["bookingid"]

    auth_response = booking_helper.create_auth_token(username=BOOKER_USERNAME, password=BOOKER_PASSWORD)
    assert auth_response.status == 200
    token = auth_response.json()["token"]

    updated_payload = copy.deepcopy(payload)
    updated_payload["firstname"] = "IdempotencyTest"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Cookie": f"token={token}",
    }

    logger.info("STEP 2: Sending first PUT request")

    first_response = booking_helper.update_booking(
        bookingId=booking_id, payload=updated_payload, headers=headers
    )

    logger.info("STEP 3: Sending identical PUT request")

    second_response = booking_helper.update_booking(
        bookingId=booking_id, payload=updated_payload, headers=headers
    )

    assert first_response.status == second_response.status
    assert first_response.json() == second_response.json()

    logger.info("STEP 4: Verifying final booking state")

    get_response = booking_helper.get_booking_by_id(booking_id)

    assert get_response.json() == updated_payload

    logger.info("PUT idempotency verified")


@pytest.mark.order(13)
@pytest.mark.negative
@pytest.mark.update_booking
@pytest.mark.authorization
@pytest.mark.xfail(
    strict=True,
    reason=(
        "The hosted API returns 405 but mutates the other booking and removes "
        "the target booking when bookingid is included in the PUT body."
    ),
)
def test_update_booking_with_different_bookingid_in_payload(booking_helper):

    logger.info("STEP 1: Creating booking A and booking B")

    payload_a = read_json("booking_data.json")
    payload_b = read_json("booking_data.json")

    payload_b["firstname"] = "BookingB"

    response_a = booking_helper.create_booking(payload=payload_a)
    response_b = booking_helper.create_booking(payload=payload_b)

    assert response_a.status == 200
    assert response_b.status == 200

    booking_a = response_a.json()["bookingid"]
    booking_b = response_b.json()["bookingid"]

    original_b = booking_helper.get_booking_by_id(booking_b).json()
    original_a = booking_helper.get_booking_by_id(booking_a).json()

    auth_response = booking_helper.create_auth_token(username=BOOKER_USERNAME, password=BOOKER_PASSWORD)
    assert auth_response.status == 200
    token = auth_response.json()["token"]

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Cookie": f"token={token}",
    }

    logger.info("STEP 2: Adding booking B ID to booking A payload")

    updated_payload = copy.deepcopy(payload_a)
    updated_payload["firstname"] = "UpdatedA"
    updated_payload["bookingid"] = booking_b

    try:
        response = booking_helper.update_booking(
            bookingId=booking_a, payload=updated_payload, headers=headers
        )
        assert response.status == 405

        logger.info("STEP 3: Verifying both bookings")

        get_a = booking_helper.get_booking_by_id(booking_a)
        get_b = booking_helper.get_booking_by_id(booking_b)

        assert get_a.status == 200
        assert get_a.json() == original_a
        assert get_b.json() == original_b
    finally:
        for booking_id in (booking_a, booking_b):
            current = booking_helper.get_booking_by_id(booking_id)
            if current.status == 200:
                cleanup = booking_helper.delete_booking(
                    bookingId=booking_id,
                    token=token,
                )
                assert cleanup.status == 201


@pytest.mark.order(14)
@pytest.mark.functional
@pytest.mark.update_booking
@pytest.mark.authorization
def test_update_booking_does_not_modify_other_bookings(booking_helper):

    logger.info("STEP 1: Creating booking A")

    payload_a = read_json("booking_data.json")
    response_a = booking_helper.create_booking(payload=payload_a)

    assert response_a.status == 200
    booking_a = response_a.json()["bookingid"]

    logger.info("STEP 2: Creating booking B")

    payload_b = read_json("booking_data.json")
    payload_b["firstname"] = "UntouchedBooking"

    response_b = booking_helper.create_booking(payload=payload_b)

    assert response_b.status == 200
    booking_b = response_b.json()["bookingid"]

    original_b = booking_helper.get_booking_by_id(booking_b).json()

    auth_response = booking_helper.create_auth_token(username=BOOKER_USERNAME, password=BOOKER_PASSWORD)
    assert auth_response.status == 200
    token = auth_response.json()["token"]

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Cookie": f"token={token}",
    }

    logger.info("STEP 3: Updating booking A")

    updated_payload = copy.deepcopy(payload_a)
    updated_payload["firstname"] = "UpdatedBookingA"

    update_response = booking_helper.update_booking(
        bookingId=booking_a, payload=updated_payload, headers=headers
    )

    assert update_response.status == 200

    logger.info("STEP 4: Verifying booking B remains unchanged")

    get_b = booking_helper.get_booking_by_id(booking_b)

    assert get_b.status == 200
    assert get_b.json() == original_b

    logger.info("Booking B remains unchanged")
