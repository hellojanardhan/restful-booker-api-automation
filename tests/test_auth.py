import pytest
import base64
import json
from config.config import BOOKER_USERNAME, BOOKER_PASSWORD
from utils.data_generator import *
from utils.logger import get_logger
from pathlib import Path

logger = get_logger(__name__)


def test_create_auth_token(booking_helper):
    logger.info("Creating an auth token with valid credentials")
    response = booking_helper.create_auth_token(username=BOOKER_USERNAME, password=BOOKER_PASSWORD)

    assert response.ok
    assert response.status == 200

    response_body = response.json()

    assert "token" in response_body
    assert response_body["token"]


@pytest.mark.parametrize(
    "username, password, expected_reason",
    [
        pytest.param(
            BOOKER_USERNAME,
            generate_password(),
            "Bad credentials",
            id="correct-username-wrong-password",
        ),
        pytest.param(
            generate_username(),
            BOOKER_PASSWORD,
            "Bad credentials",
            id="wrong-username-correct-password",
        ),
        pytest.param(
            generate_username(),
            generate_password(),
            "Bad credentials",
            id="wrong-username-wrong-password",
        ),
    ],
)
def test_create_auth_token_with_invalid_credentials(
    booking_helper, username, password, expected_reason
):
    logger.info("Checking auth rejection for invalid credentials")
    response = booking_helper.create_auth_token(username=username, password=password)

    assert response.ok
    assert response.status == 200

    response_body = response.json()

    assert "reason" in response_body
    assert response_body["reason"] == expected_reason


@pytest.mark.parametrize(
    "username,password",
    [
        pytest.param("", BOOKER_PASSWORD, id="missing-username"),
        pytest.param(BOOKER_USERNAME, "", id="missing-password"),
        pytest.param("", "", id="missing-both-credentials"),
        pytest.param(" ", " ", id="whitespace-only-credentials"),
    ],
)
def test_create_auth_token_with_missing_credentials(booking_helper, username, password):
    logger.info("Checking auth rejection for missing credentials")
    response = booking_helper.create_auth_token(username=username, password=password)

    assert response.ok
    assert response.status == 200
    response_body = response.json()

    logger.info("Auth rejection reason: %s", response_body.get("reason"))

    assert "reason" in response_body
    assert response_body["reason"] == "Bad credentials"


def test_create_auth_token_with_empty_json_body(booking_helper):
    response = booking_helper.create_auth_token(payload={})
    assert response.status == 200
    response_body = response.json()
    assert "reason" in response_body
    assert "token" not in response_body


def test_create_auth_token_with_empty_request_body(booking_helper):

    response = booking_helper.create_auth_token(payload="")

    assert response.status == 400


@pytest.mark.parametrize(
    "method",
    ["PUT", "PATCH", "DELETE"],
    ids=["authorized-put", "authorized-patch", "authorized-delete"],
)
def test_authorized_booking_operations(method, booking_helper):

    # Generate authentication token
    response = booking_helper.create_auth_token(username=BOOKER_USERNAME, password=BOOKER_PASSWORD)

    assert response.status == 200

    response_body = response.json()
    assert "token" in response_body

    token = response_body["token"]

    # Prepare booking payload
    payload = read_json("booking_data.json")
    checkin = generate_checkin()

    payload["firstname"] = generate_firstname()
    payload["lastname"] = generate_lastname()
    payload["totalprice"] = generate_totalprice()
    payload["depositpaid"] = generate_depositpaid()
    payload["bookingdates"]["checkin"] = checkin
    payload["additionalneeds"] = generate_additionalneeds()

    # Create a new booking
    response = booking_helper.create_booking(payload=payload)

    assert response.status == 200

    booking_id = response.json()["bookingid"]
    assert booking_id > 0

    logger.info("Created booking | ID: %s", booking_id)

    # Execute PUT / PATCH / DELETE
    response = booking_helper.perform_booking_operation(
        method=method,
        booking_id=booking_id,
        payload=payload if method != "DELETE" else None,
        token=token,
    )
    if method in ["PUT", "PATCH"]:

        assert response.ok
        assert response.status == 200

        response_data = response.json()

        assert response_data["firstname"] == payload["firstname"]
        assert response_data["lastname"] == payload["lastname"]

    elif method == "DELETE":

        assert response.status == 201


@pytest.mark.parametrize(
    "username, password",
    [
        pytest.param(None, BOOKER_PASSWORD, id="username-null"),
        pytest.param(123, BOOKER_PASSWORD, id="username-number"),
        pytest.param(True, BOOKER_PASSWORD, id="username-boolean"),
        pytest.param([], BOOKER_PASSWORD, id="username-array"),
        pytest.param({}, BOOKER_PASSWORD, id="username-object"),
        pytest.param(BOOKER_USERNAME, None, id="password-null"),
        pytest.param(BOOKER_USERNAME, 123, id="password-number"),
        pytest.param(BOOKER_USERNAME, True, id="password-boolean"),
        pytest.param(BOOKER_USERNAME, [], id="password-array"),
        pytest.param(BOOKER_USERNAME, {}, id="password-object"),
    ],
)
def test_create_auth_token_with_invalid_data_types(booking_helper, username, password):
    response = booking_helper.create_auth_token(username=username, password=password)

    response_body = response.json()

    assert "token" not in response_body


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param('{"username": "admin"', id="truncated-json"),
        pytest.param(
            '{"username": "admin", "password": "password123",}', id="trailing-comma"
        ),
        pytest.param(
            "{'username': 'admin', 'password': 'password123'}", id="single-quotes"
        ),
    ],
)
def test_create_auth_token_with_malformed_json(booking_helper, payload):
    response = booking_helper.create_auth_token(payload=payload)
    assert response.status == 400
    logger.info("Malformed JSON request returned HTTP %s", response.status)

    assert response.status not in [200] or "token" not in response.json()


@pytest.mark.parametrize(
    "username, password",
    [
        pytest.param("Admin", BOOKER_PASSWORD, id="username-title-case"),
        pytest.param("ADMIN", BOOKER_PASSWORD, id="username-uppercase"),
        pytest.param(BOOKER_USERNAME, "PASSWORD123", id="password-uppercase"),
        pytest.param(BOOKER_USERNAME, "Password123", id="password-title-case"),
    ],
)
def test_create_auth_token_with_case_sensitive_username_and_password(
    booking_helper, username, password
):
    response = booking_helper.create_auth_token(username=username, password=password)
    assert response.status == 200

    response_body = response.json()

    logger.info("Auth rejection reason: %s", response_body.get("reason"))

    assert "reason" in response_body
    assert response_body["reason"] == "Bad credentials"
    assert "token" not in response_body


def test_reuse_valid_auth_token_across_multiple_bookings(booking_helper):
    # Creating Booking A
    payload_a = read_json("booking_data.json")
    response_a = booking_helper.create_booking(payload_a)
    assert response_a.ok
    assert response_a.status == 200
    booking_a_response_data = response_a.json()
    assert booking_a_response_data["bookingid"] > 0
    booking_id_a = booking_a_response_data["bookingid"]
    booking_a = booking_a_response_data["booking"]
    logger.info("Created first booking with ID %s", booking_id_a)
    assert booking_a["firstname"] == payload_a["firstname"]
    assert booking_a["lastname"] == payload_a["lastname"]

    # Creating Booking B
    payload_b = {
        "firstname": "Rahul",
        "lastname": "Sharma",
        "totalprice": 850,
        "depositpaid": False,
        "bookingdates": {"checkin": "2026-12-10", "checkout": "2026-12-15"},
        "additionalneeds": "Breakfast",
    }
    response_b = booking_helper.create_booking(payload_b)
    assert response_b.ok
    assert response_b.status == 200
    booking_b = response_b.json()
    booking_id_b = booking_b["bookingid"]
    assert booking_b["bookingid"] > 0
    assert booking_b["booking"]["firstname"] == payload_b["firstname"]
    assert booking_b["booking"]["lastname"] == payload_b["lastname"]

    # Create Auth token
    response = booking_helper.create_auth_token(username=BOOKER_USERNAME, password=BOOKER_PASSWORD)

    assert response.status == 200

    response_body = response.json()
    assert "token" in response_body

    token = response_body["token"]

    # Update Booking A
    checkin = generate_checkin()

    booking_a["firstname"] = generate_firstname()
    booking_a["lastname"] = generate_lastname()
    booking_a["totalprice"] = generate_totalprice()
    booking_a["depositpaid"] = generate_depositpaid()
    booking_a["additionalneeds"] = generate_additionalneeds()
    booking_a["bookingdates"]["checkin"] = checkin
    booking_a_response = booking_helper.update_booking(
        token=token, bookingId=booking_id_a, payload=booking_a
    )

    assert booking_a_response.status == 200

    # Update Booking A
    checkin = generate_checkin()

    booking_b["firstname"] = generate_firstname()
    booking_b["lastname"] = generate_lastname()
    booking_b["totalprice"] = generate_totalprice()
    booking_b["depositpaid"] = generate_depositpaid()
    booking_b["additionalneeds"] = generate_additionalneeds()
    booking_b_response = booking_helper.update_booking(
        token=token, bookingId=booking_id_b, payload=booking_b
    )

    assert booking_b_response.status == 400


def test_authorized_put_with_http_basic_auth(booking_helper):

    # Generate Basic Authentication credentials
    credentials = f"{BOOKER_USERNAME}:{BOOKER_PASSWORD}"

    encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {encoded_credentials}",
    }

    # Prepare booking payload
    payload = read_json("booking_data.json")

    # Create booking
    response = booking_helper.create_booking(payload=payload)

    assert response.status == 200

    booking_id = response.json()["bookingid"]
    assert booking_id > 0

    # Prepare updated payload
    updated_payload = payload.copy()

    updated_payload["firstname"] = generate_firstname()
    updated_payload["lastname"] = generate_lastname()

    # Update booking using Basic Authentication
    response = booking_helper.update_booking(
        bookingId=booking_id, payload=updated_payload, headers=headers
    )

    assert response.status == 200

    # Verify booking using GET
    response = booking_helper.get_booking_by_id(booking_id)

    assert response.status == 200

    updated_response = response.json()

    assert updated_response["firstname"] == updated_payload["firstname"]
    assert updated_response["lastname"] == updated_payload["lastname"]


def test_token_in_authorization_header_is_rejected(booking_helper):

    # Creating access token
    response = booking_helper.create_auth_token(username=BOOKER_USERNAME, password=BOOKER_PASSWORD)

    assert response.ok
    assert response.status == 200

    response_body = response.json()
    logger.info(
        "Auth response status %s; token present: %s",
        response.status,
        bool(response_body.get("token")),
    )
    assert "token" in response_body
    assert response_body["token"]

    token = response_body['token']

    payload = read_json("booking_data.json")
    response = booking_helper.create_booking(payload)
    assert response.ok
    assert response.status == 200
    response_body = response.json()
    assert response_body["bookingid"] > 0
    bookingId = response_body["bookingid"]

    headers = {
        "Content-Type" : "application/json",
        "Authorization" : f"Bearer {token}"
    }

    update_response = booking_helper.update_booking(
        bookingId=bookingId, payload=payload, headers=headers
    )

    assert update_response.status == 403

def test_token_in_query_parameter_is_rejected(booking_helper):
    # Creating access token
    response = booking_helper.create_auth_token(username=BOOKER_USERNAME, password=BOOKER_PASSWORD)

    assert response.ok
    assert response.status == 200

    response_body = response.json()
    logger.info(
        "Auth response status %s; token present: %s",
        response.status,
        bool(response_body.get("token")),
    )
    assert "token" in response_body
    assert response_body["token"]

    token = response_body['token']

    payload = read_json("booking_data.json")
    response = booking_helper.create_booking(payload)
    assert response.ok
    assert response.status == 200
    response_body = response.json()
    assert response_body["bookingid"] > 0
    bookingId = response_body["bookingid"]

    params = {
        "token" : f"{token}"
    }
    update_response = booking_helper.update_booking(
        bookingId=bookingId, payload=payload, params = params
    )

    assert update_response.status == 403


def test_token_in_json_body_is_rejected(booking_helper):
    # Creating access token
    response = booking_helper.create_auth_token(username=BOOKER_USERNAME, password=BOOKER_PASSWORD)

    assert response.ok
    assert response.status == 200

    response_body = response.json()
    logger.info(
        "Auth response status %s; token present: %s",
        response.status,
        bool(response_body.get("token")),
    )
    assert "token" in response_body
    assert response_body["token"]

    token = response_body['token']

    payload = read_json("booking_data.json")
    response = booking_helper.create_booking(payload)
    assert response.ok
    assert response.status == 200
    response_body = response.json()
    assert response_body["bookingid"] > 0
    bookingId = response_body["bookingid"]

    payload["token"] = token
    update_response = booking_helper.update_booking(
        bookingId=bookingId, payload=payload
    )

    assert update_response.status == 403


def test_token_cookie_name_case_variation_is_rejected(booking_helper):
    # Creating access token
    response = booking_helper.create_auth_token(
        username=BOOKER_USERNAME, password=BOOKER_PASSWORD
    )

    assert response.ok
    assert response.status == 200

    response_body = response.json()
    logger.info(
        "Auth response status %s; token present: %s",
        response.status,
        bool(response_body.get("token")),
    )
    assert "token" in response_body
    assert response_body["token"]

    token = response_body["token"]

    payload = read_json("booking_data.json")
    response = booking_helper.create_booking(payload)
    assert response.ok
    assert response.status == 200
    response_body = response.json()
    assert response_body["bookingid"] > 0
    bookingId = response_body["bookingid"]

    headers = {
        "Content-Type" : "application/json",
        "Cookie" : f"Token={token}"
    }
    update_response = booking_helper.update_booking(
        bookingId=bookingId, payload=payload, headers=headers
    )

    assert update_response.status == 403


def test_token_cookie_with_extra_unrelated_cookies(booking_helper):
    # Creating access token
    response = booking_helper.create_auth_token(
        username=BOOKER_USERNAME, password=BOOKER_PASSWORD
    )

    assert response.ok
    assert response.status == 200

    response_body = response.json()
    logger.info(
        "Auth response status %s; token present: %s",
        response.status,
        bool(response_body.get("token")),
    )
    assert "token" in response_body
    assert response_body["token"]

    token = response_body["token"]

    payload = read_json("booking_data.json")
    response = booking_helper.create_booking(payload)
    assert response.ok
    assert response.status == 200
    response_body = response.json()
    assert response_body["bookingid"] > 0
    bookingId = response_body["bookingid"]

    headers = {
        "Content-Type" : "application/json",
        "Cookie" : f"token={token};session_id=abc123"
    }
    update_response = booking_helper.update_booking(
        bookingId=bookingId, payload=payload,
        headers = headers
    )

    assert update_response.status == 200


def test_duplicate_token_cookie_with_same_value_is_accepted(booking_helper):
    # Creating access token
    response = booking_helper.create_auth_token(
        username=BOOKER_USERNAME, password=BOOKER_PASSWORD
    )

    assert response.ok
    assert response.status == 200

    response_body = response.json()
    logger.info(
        "Auth response status %s; token present: %s",
        response.status,
        bool(response_body.get("token")),
    )
    assert "token" in response_body
    assert response_body["token"]

    token = response_body["token"]

    payload = read_json("booking_data.json")
    response = booking_helper.create_booking(payload)
    assert response.ok
    assert response.status == 200
    response_body = response.json()
    assert response_body["bookingid"] > 0
    bookingId = response_body["bookingid"]

    headers = {
        "Content-Type": "application/json",
        "Cookie": f"token={token};token={token}",
    }
    update_response = booking_helper.update_booking(
        bookingId=bookingId, payload=payload, headers=headers
    )

    assert update_response.status == 200


def test_token_cookie_with_surrounding_whitespace_is_accepted(booking_helper):
    # Create token
    response = booking_helper.create_auth_token(
        username=BOOKER_USERNAME, password=BOOKER_PASSWORD
    )
    assert response.status == 200
    token = response.json()["token"]

    # Create booking
    payload = read_json("booking_data.json")
    response = booking_helper.create_booking(payload)

    assert response.status == 200
    bookingId = response.json()["bookingid"]

    headers = {
    "Content-Type": "application/json",
    "Cookie": f"token=   {token}   ",
}

    # Before the security attempt
    original_booking = booking_helper.get_booking_by_id(bookingId).json()

    # Send token with whitespace
    update_response = booking_helper.update_booking(
        bookingId=bookingId,
        payload=payload,
        headers=headers
    )

    assert update_response.status == 200

    # Verify booking remains unchanged
    final_booking = booking_helper.get_booking_by_id(bookingId).json()

    assert final_booking == original_booking

def test_old_and_new_tokens_validity_after_generating_second_token(booking_helper):

    # Generate first token
    response1 = booking_helper.create_auth_token(
        username=BOOKER_USERNAME,
        password=BOOKER_PASSWORD
    )

    assert response1.status == 200
    token1 = response1.json()["token"]

    logger.info("First token generated successfully")

    # Generate second token
    response2 = booking_helper.create_auth_token(
        username=BOOKER_USERNAME,
        password=BOOKER_PASSWORD
    )

    assert response2.status == 200
    token2 = response2.json()["token"]

    logger.info("Second token generated successfully")

    # Create booking
    payload = read_json("booking_data.json")

    create_response = booking_helper.create_booking(payload)

    assert create_response.status == 200

    booking_id = create_response.json()["bookingid"]

    logger.info("Created booking | ID: %s", booking_id)

    # Test first/old token
    old_token_response = booking_helper.update_booking(
        bookingId=booking_id,
        payload=payload,
        token=token1
    )

    logger.info(
        "Old token | HTTP %s",
        old_token_response.status
    )

    # Test second/new token
    new_token_response = booking_helper.update_booking(
        bookingId=booking_id,
        payload=payload,
        token=token2
    )

    logger.info(
        "New token | HTTP %s",
        new_token_response.status
    )

    assert old_token_response.status == 200
    assert new_token_response.status == 200
