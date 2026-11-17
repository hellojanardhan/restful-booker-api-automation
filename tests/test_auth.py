import pytest
import base64
import json
from config.config import USERNAME, PASSWORD
from utils.data_generator import *
from pathlib import Path


def test_create_auth_token(booking_helper):
    response = booking_helper.create_auth_token(username=USERNAME, password=PASSWORD)

    assert response.ok
    assert response.status == 200

    response_body = response.json()

    assert "token" in response_body
    assert response_body["token"]


@pytest.mark.parametrize(
    "username, password, expected_reason",
    [
        pytest.param(
            USERNAME,
            generate_password(),
            "Bad credentials",
            id="correct-username-wrong-password",
        ),
        pytest.param(
            generate_username(),
            PASSWORD,
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
    response = booking_helper.create_auth_token(username=username, password=password)

    assert response.ok
    assert response.status == 200

    response_body = response.json()

    assert "reason" in response_body
    assert response_body["reason"] == expected_reason


@pytest.mark.parametrize(
    "username,password",
    [
        pytest.param("", PASSWORD, id="missing-username"),
        pytest.param(USERNAME, "", id="missing-password"),
        pytest.param("", "", id="missing-both-credentials"),
        pytest.param(" ", " ", id="whitespace-only-credentials"),
    ],
)
def test_create_auth_token_with_missing_credentials(booking_helper, username, password):
    response = booking_helper.create_auth_token(username=username, password=password)

    assert response.ok
    assert response.status == 200
    response_body = response.json()

    print(f"response body : {response_body}")

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
    response = booking_helper.create_auth_token(username=USERNAME, password=PASSWORD)

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

    print(f"Booking ID: {booking_id}")

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
        pytest.param(None, PASSWORD, id="username-null"),
        pytest.param(123, PASSWORD, id="username-number"),
        pytest.param(True, PASSWORD, id="username-boolean"),
        pytest.param([], PASSWORD, id="username-array"),
        pytest.param({}, PASSWORD, id="username-object"),
        pytest.param(USERNAME, None, id="password-null"),
        pytest.param(USERNAME, 123, id="password-number"),
        pytest.param(USERNAME, True, id="password-boolean"),
        pytest.param(USERNAME, [], id="password-array"),
        pytest.param(USERNAME, {}, id="password-object"),
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
    print("Status:", response.status)
    print("Response:", response.text())

    assert response.status not in [200] or "token" not in response.json()


@pytest.mark.parametrize(
    "username, password",
    [
        pytest.param("Admin", PASSWORD, id="username-title-case"),
        pytest.param("ADMIN", PASSWORD, id="username-uppercase"),
        pytest.param(USERNAME, "PASSWORD123", id="password-uppercase"),
        pytest.param(USERNAME, "Password123", id="password-title-case"),
    ],
)
def test_create_auth_token_with_case_sensitive_username_and_password(
    booking_helper, username, password
):
    response = booking_helper.create_auth_token(username=username, password=password)
    assert response.status == 200

    response_body = response.json()

    print(response_body)

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
    print(f"First Booking Response is {booking_a_response_data}")
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
    response = booking_helper.create_auth_token(username=USERNAME, password=PASSWORD)

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
    credentials = f"{USERNAME}:{PASSWORD}"

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
