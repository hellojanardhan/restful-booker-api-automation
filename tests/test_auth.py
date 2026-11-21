"""Tests for authentication and authorized booking operations."""

import pytest
import base64
import json
from config.config import BOOKER_USERNAME, BOOKER_PASSWORD
from utils.data_generator import *
from utils.logger import get_logger
from pathlib import Path

logger = get_logger(__name__)


@pytest.mark.order(1)
@pytest.mark.authentication
@pytest.mark.authorization
@pytest.mark.regression
@pytest.mark.security
def test_create_auth_token(booking_helper):
    """Verify valid credentials create an authentication token.

    Test steps:
    1. Call the authentication endpoint with valid configured credentials.
    2. Verify the request returns HTTP 200.
    3. Parse the JSON response and verify it contains a non-empty token.
    """
    logger.info("START | test_create_auth_token")
    logger.info("Step 1: Request auth token with valid configured credentials")
    response = booking_helper.create_auth_token(username=BOOKER_USERNAME, password=BOOKER_PASSWORD)

    logger.info("Step 1 result: HTTP %s", response.status)
    logger.info("Step 2: Verify response status and token")
    assert response.ok
    assert response.status == 200

    response_body = response.json()

    assert "token" in response_body
    assert response_body["token"]
    logger.info("Step 2 result: Valid non-empty authentication token received")
    logger.info("END | test_create_auth_token")


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
@pytest.mark.order(2)
@pytest.mark.authentication
@pytest.mark.authorization
@pytest.mark.regression
@pytest.mark.negative
def test_create_auth_token_with_invalid_credentials(
    booking_helper, username, password, expected_reason
):
    """Verify invalid username and password combinations are rejected.

    Test steps:
    1. Call the authentication endpoint with an invalid credential combination.
    2. Verify the response status is 200.
    3. Parse the JSON response.
    4. Verify it contains the expected "Bad credentials" reason.
    """
    logger.info(
        "START | test_create_auth_token_with_invalid_credentials | username=%r",
        username,
    )
    logger.info("Step 1: Request auth token with invalid credentials")
    response = booking_helper.create_auth_token(username=username, password=password)

    logger.info("Step 1 result: HTTP %s", response.status)
    logger.info("Step 2: Verify Bad credentials response")
    assert response.ok
    assert response.status == 200

    response_body = response.json()

    assert "reason" in response_body
    assert response_body["reason"] == expected_reason
    logger.info("Step 2 result: Reason=%s", response_body["reason"])
    logger.info("END | test_create_auth_token_with_invalid_credentials")


@pytest.mark.parametrize(
    "username,password",
    [
        pytest.param("", BOOKER_PASSWORD, id="missing-username"),
        pytest.param(BOOKER_USERNAME, "", id="missing-password"),
        pytest.param("", "", id="missing-both-credentials"),
        pytest.param(" ", " ", id="whitespace-only-credentials"),
    ],
)
@pytest.mark.order(3)
@pytest.mark.authentication
@pytest.mark.authorization
@pytest.mark.regression
@pytest.mark.negative
def test_create_auth_token_with_missing_credentials(booking_helper, username, password):
    """Verify missing or whitespace credentials return a bad-credentials reason.

    Test steps:
    1. Call the authentication endpoint with missing or whitespace credentials.
    2. Verify the response status is 200.
    3. Parse the JSON response.
    4. Verify the response reason is "Bad credentials".
    """
    logger.info("START | test_create_auth_token_with_missing_credentials")
    logger.info("Step 1: Request auth token with missing or whitespace credentials")
    response = booking_helper.create_auth_token(username=username, password=password)

    logger.info("Step 1 result: HTTP %s", response.status)
    logger.info("Step 2: Verify Bad credentials response")
    assert response.ok
    assert response.status == 200
    response_body = response.json()

    logger.info("Auth rejection reason: %s", response_body.get("reason"))

    assert "reason" in response_body
    assert response_body["reason"] == "Bad credentials"
    logger.info("Step 2 result: Reason=%s", response_body["reason"])
    logger.info("END | test_create_auth_token_with_missing_credentials")


@pytest.mark.order(4)
@pytest.mark.authentication
@pytest.mark.authorization
@pytest.mark.regression
@pytest.mark.negative
def test_create_auth_token_with_empty_json_body(booking_helper):
    """Verify an empty JSON object produces no authentication token.

    Test steps:
    1. Send an empty JSON object to the authentication endpoint.
    2. Verify the response status is 200.
    3. Parse the JSON response.
    4. Verify a reason is returned and no token is present.
    """
    logger.info("START | test_create_auth_token_with_empty_json_body")
    logger.info("Step 1: Request auth token with an empty JSON object")
    response = booking_helper.create_auth_token(payload={})
    logger.info("Step 1 result: HTTP %s", response.status)
    logger.info("Step 2: Verify no token is returned")
    assert response.status == 200
    response_body = response.json()
    assert "reason" in response_body
    assert "token" not in response_body
    logger.info("Step 2 result: No token; reason=%s", response_body["reason"])
    logger.info("END | test_create_auth_token_with_empty_json_body")


@pytest.mark.order(5)
@pytest.mark.authentication
@pytest.mark.authorization
@pytest.mark.regression
@pytest.mark.negative
def test_create_auth_token_with_empty_request_body(booking_helper):
    """Verify an empty request body is handled by the authentication endpoint.

    Test steps:
    1. Send an empty string as the authentication request body.
    2. Verify the endpoint returns HTTP 400.
    """

    logger.info("START | test_create_auth_token_with_empty_request_body")
    logger.info("Step 1: Request auth token with an empty request body")
    response = booking_helper.create_auth_token(payload="")

    logger.info("Step 1 result: HTTP %s", response.status)
    logger.info("Step 2: Verify malformed empty body is rejected")
    assert response.status == 400
    logger.info("Step 2 result: Empty body rejected")
    logger.info("END | test_create_auth_token_with_empty_request_body")


@pytest.mark.parametrize(
    "method",
    ["PUT", "PATCH", "DELETE"],
    ids=["authorized-put", "authorized-patch", "authorized-delete"],
)
@pytest.mark.order(6)
@pytest.mark.authentication
@pytest.mark.authorization
@pytest.mark.regression
@pytest.mark.security
def test_authorized_booking_operations(method, booking_helper):
    """Verify authorized booking operations return their expected status.

    Test steps:
    1. Generate a valid authentication token.
    2. Generate and create a booking with a random payload.
    3. Execute the parameterized PUT, PATCH, or DELETE operation with the token.
    4. Verify PUT and PATCH return 200 with updated names.
    5. Verify DELETE returns 201.
    """

    logger.info("START | test_authorized_booking_operations | method=%s", method)
    logger.info("Step 1: Generate authentication token")
    response = booking_helper.create_auth_token(username=BOOKER_USERNAME, password=BOOKER_PASSWORD)

    logger.info("Step 1 result: HTTP %s", response.status)
    assert response.status == 200

    response_body = response.json()
    assert "token" in response_body

    token = response_body["token"]

    logger.info("Step 2: Prepare and create booking")
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

    logger.info("Step 2 result: Booking create HTTP %s", response.status)
    assert response.status == 200

    booking_id = response.json()["bookingid"]
    assert booking_id > 0

    logger.info("Created booking | ID: %s", booking_id)

    logger.info("Step 3: Execute %s booking operation", method)
    response = booking_helper.perform_booking_operation(
        method=method,
        booking_id=booking_id,
        payload=payload if method != "DELETE" else None,
        token=token,
    )
    logger.info("Step 3 result: HTTP %s", response.status)
    if method in ["PUT", "PATCH"]:

        assert response.ok
        assert response.status == 200

        response_data = response.json()

        assert response_data["firstname"] == payload["firstname"]
        assert response_data["lastname"] == payload["lastname"]

    elif method == "DELETE":

        assert response.status == 201
    logger.info("END | test_authorized_booking_operations | method=%s", method)


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
@pytest.mark.order(7)
@pytest.mark.authentication
@pytest.mark.authorization
@pytest.mark.regression
@pytest.mark.negative
def test_create_auth_token_with_invalid_data_types(booking_helper, username, password):
    """Verify invalid credential data types are handled without server errors.

    Test steps:
    1. Send null, numeric, boolean, array, or object credential values.
    2. Parse the authentication response.
    3. Verify the response does not contain a token.
    """
    logger.info(
        "START | test_create_auth_token_with_invalid_data_types | username=%r password=%r",
        username,
        password,
    )
    logger.info("Step 1: Send authentication credentials with invalid data types")
    response = booking_helper.create_auth_token(username=username, password=password)
    logger.info("Step 1 result: HTTP %s", response.status)

    response_body = response.json()

    logger.info("Step 2: Verify response does not contain an auth token")
    assert "token" not in response_body
    logger.info("Step 2 result: No authentication token returned")
    logger.info("END | test_create_auth_token_with_invalid_data_types")


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
@pytest.mark.order(8)
@pytest.mark.authentication
@pytest.mark.authorization
@pytest.mark.regression
@pytest.mark.negative
def test_create_auth_token_with_malformed_json(booking_helper, payload):
    """Verify malformed JSON requests are rejected safely.

    Test steps:
    1. Send malformed JSON to the authentication endpoint.
    2. Verify the response is HTTP 400.
    3. Verify the response does not provide a token.
    """
    logger.info("START | test_create_auth_token_with_malformed_json")
    logger.info("Step 1: Send malformed JSON to authentication endpoint")
    response = booking_helper.create_auth_token(payload=payload)
    logger.info("Step 1 result: HTTP %s", response.status)
    assert response.status == 400

    logger.info("Step 2: Verify response body contains no token")
    assert response.status not in [200] or "token" not in response.json()
    logger.info("Step 2 result: Malformed JSON safely rejected")
    logger.info("END | test_create_auth_token_with_malformed_json")


@pytest.mark.parametrize(
    "username, password",
    [
        pytest.param("Admin", BOOKER_PASSWORD, id="username-title-case"),
        pytest.param("ADMIN", BOOKER_PASSWORD, id="username-uppercase"),
        pytest.param(BOOKER_USERNAME, "PASSWORD123", id="password-uppercase"),
        pytest.param(BOOKER_USERNAME, "Password123", id="password-title-case"),
    ],
)
@pytest.mark.order(9)
@pytest.mark.authentication
@pytest.mark.authorization
@pytest.mark.regression
@pytest.mark.security
def test_create_auth_token_with_case_sensitive_username_and_password(
    booking_helper, username, password
):
    """Verify authentication rejects differently cased credentials.

    Test steps:
    1. Send credentials with different username or password casing.
    2. Verify the response status is 200.
    3. Parse the JSON response.
    4. Verify "Bad credentials" is returned and no token is present.
    """
    logger.info(
        "START | test_create_auth_token_with_case_sensitive_username_and_password",
    )
    logger.info("Step 1: Send credentials with different casing")
    response = booking_helper.create_auth_token(username=username, password=password)
    logger.info("Step 1 result: HTTP %s", response.status)
    assert response.status == 200

    response_body = response.json()

    logger.info("Step 2: Verify Bad credentials and absence of token")
    logger.info("Auth rejection reason: %s", response_body.get("reason"))
    assert "reason" in response_body
    assert response_body["reason"] == "Bad credentials"
    assert "token" not in response_body
    logger.info("Step 2 result: Case-sensitive credentials rejected")
    logger.info("END | test_create_auth_token_with_case_sensitive_username_and_password")


@pytest.mark.order(10)
@pytest.mark.authentication
@pytest.mark.authorization
@pytest.mark.regression
@pytest.mark.security
def test_reuse_valid_auth_token_across_multiple_bookings(booking_helper):
    """Verify one valid token can authorize multiple booking updates.

    Test steps:
    1. Create two separate bookings and verify their identifiers.
    2. Generate one valid authentication token.
    3. Update the first booking with the token and verify HTTP 200.
    4. Attempt to update the second booking with the malformed payload and verify HTTP 400.
    """
    logger.info("START | test_reuse_valid_auth_token_across_multiple_bookings")
    logger.info("Step 1: Create first booking")
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
    logger.info("Step 1 result: First booking ID=%s", booking_id_a)

    logger.info("Step 2: Create second booking")
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
    logger.info("Step 2 result: Second booking ID=%s", booking_id_b)

    logger.info("Step 3: Generate authentication token")
    response = booking_helper.create_auth_token(username=BOOKER_USERNAME, password=BOOKER_PASSWORD)

    logger.info("Step 3 result: HTTP %s", response.status)
    assert response.status == 200

    response_body = response.json()
    assert "token" in response_body

    token = response_body["token"]

    logger.info("Step 4: Update first booking with token")
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
    logger.info("Step 4 result: HTTP %s", booking_a_response.status)

    logger.info("Step 5: Update second booking with token")
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
    logger.info("Step 5 result: HTTP %s", booking_b_response.status)
    logger.info("END | test_reuse_valid_auth_token_across_multiple_bookings")


@pytest.mark.order(11)
@pytest.mark.authentication
@pytest.mark.authorization
@pytest.mark.regression
@pytest.mark.security
def test_authorized_put_with_http_basic_auth(booking_helper):
    """Verify HTTP Basic Authorization is rejected for booking updates.

    Test steps:
    1. Encode the configured username and password using HTTP Basic credentials.
    2. Create a booking.
    3. Send an update request with the Basic Authorization header.
    4. Verify the update response status.
    5. Fetch the booking and verify the updated names.
    """

    logger.info("START | test_authorized_put_with_http_basic_auth")
    logger.info("Step 1: Prepare HTTP Basic Authorization credentials")
    credentials = f"{BOOKER_USERNAME}:{BOOKER_PASSWORD}"

    encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {encoded_credentials}",
    }

    # Prepare booking payload
    payload = read_json("booking_data.json")

    logger.info("Step 2: Create booking")
    response = booking_helper.create_booking(payload=payload)

    logger.info("Step 2 result: HTTP %s", response.status)
    assert response.status == 200

    booking_id = response.json()["bookingid"]
    assert booking_id > 0

    # Prepare updated payload
    updated_payload = payload.copy()

    updated_payload["firstname"] = generate_firstname()
    updated_payload["lastname"] = generate_lastname()

    logger.info("Step 3: Update booking using Basic Authorization")
    response = booking_helper.update_booking(
        bookingId=booking_id, payload=updated_payload, headers=headers
    )

    logger.info("Step 3 result: HTTP %s", response.status)
    assert response.status == 200

    logger.info("Step 4: Fetch booking and verify updated fields")
    response = booking_helper.get_booking_by_id(booking_id)

    assert response.status == 200

    updated_response = response.json()

    assert updated_response["firstname"] == updated_payload["firstname"]
    assert updated_response["lastname"] == updated_payload["lastname"]
    logger.info("Step 4 result: Updated fields verified")
    logger.info("END | test_authorized_put_with_http_basic_auth")


@pytest.mark.order(12)
@pytest.mark.authentication
@pytest.mark.authorization
@pytest.mark.regression
@pytest.mark.security
def test_token_in_authorization_header_is_rejected(booking_helper):
    """Verify a token is not accepted in an Authorization header.

    Test steps:
    1. Generate a valid authentication token.
    2. Create a booking.
    3. Send an update request with the token in a Bearer Authorization header.
    4. Verify the update is rejected with HTTP 403.
    """

    logger.info("START | test_token_in_authorization_header_is_rejected")
    logger.info("Step 1: Generate authentication token")
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
    logger.info("Step 1 result: Token generated")

    token = response_body['token']

    logger.info("Step 2: Create booking")
    payload = read_json("booking_data.json")
    response = booking_helper.create_booking(payload)
    assert response.ok
    assert response.status == 200
    response_body = response.json()
    assert response_body["bookingid"] > 0
    bookingId = response_body["bookingid"]
    logger.info("Step 2 result: Booking ID=%s", bookingId)

    headers = {
        "Content-Type" : "application/json",
        "Authorization" : f"Bearer {token}"
    }

    logger.info("Step 3: Update with token in Bearer Authorization header")
    update_response = booking_helper.update_booking(
        bookingId=bookingId, payload=payload, headers=headers
    )

    logger.info("Step 3 result: HTTP %s", update_response.status)
    assert update_response.status == 403
    logger.info("END | test_token_in_authorization_header_is_rejected")

@pytest.mark.order(13)
@pytest.mark.authentication
@pytest.mark.authorization
@pytest.mark.regression
@pytest.mark.security
def test_token_in_query_parameter_is_rejected(booking_helper):
    """Verify a token query parameter does not authorize a booking update.

    Test steps:
    1. Generate a valid authentication token.
    2. Create a booking.
    3. Send an update request with the token as a query parameter.
    4. Verify the update is rejected with HTTP 403.
    """
    logger.info("START | test_token_in_query_parameter_is_rejected")
    logger.info("Step 1: Generate authentication token")
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
    logger.info("Step 1 result: Token generated")

    token = response_body['token']

    logger.info("Step 2: Create booking")
    payload = read_json("booking_data.json")
    response = booking_helper.create_booking(payload)
    assert response.ok
    assert response.status == 200
    response_body = response.json()
    assert response_body["bookingid"] > 0
    bookingId = response_body["bookingid"]
    logger.info("Step 2 result: Booking ID=%s", bookingId)

    params = {
        "token" : f"{token}"
    }
    logger.info("Step 3: Update with token in query parameter")
    update_response = booking_helper.update_booking(
        bookingId=bookingId, payload=payload, params = params
    )

    logger.info("Step 3 result: HTTP %s", update_response.status)
    assert update_response.status == 403
    logger.info("END | test_token_in_query_parameter_is_rejected")


@pytest.mark.order(14)
@pytest.mark.authentication
@pytest.mark.authorization
@pytest.mark.regression
@pytest.mark.security
def test_token_in_json_body_is_rejected(booking_helper):
    """Verify a token in a JSON body does not authorize a booking update.

    Test steps:
    1. Generate a valid authentication token.
    2. Create a booking.
    3. Add the token to the booking JSON request body.
    4. Send the update request without a cookie.
    5. Verify the update is rejected with HTTP 403.
    """
    logger.info("START | test_token_in_json_body_is_rejected")
    logger.info("Step 1: Generate authentication token")
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
    logger.info("Step 1 result: Token generated")

    token = response_body['token']

    logger.info("Step 2: Create booking")
    payload = read_json("booking_data.json")
    response = booking_helper.create_booking(payload)
    assert response.ok
    assert response.status == 200
    response_body = response.json()
    assert response_body["bookingid"] > 0
    bookingId = response_body["bookingid"]
    logger.info("Step 2 result: Booking ID=%s", bookingId)

    logger.info("Step 3: Add token to JSON body and send update")
    payload["token"] = token
    update_response = booking_helper.update_booking(
        bookingId=bookingId, payload=payload
    )

    logger.info("Step 3 result: HTTP %s", update_response.status)
    assert update_response.status == 403
    logger.info("END | test_token_in_json_body_is_rejected")


@pytest.mark.order(15)
@pytest.mark.authentication
@pytest.mark.authorization
@pytest.mark.regression
@pytest.mark.security
def test_token_cookie_name_case_variation_is_rejected(booking_helper):
    """Verify cookie names are case-sensitive for authentication.

    Test steps:
    1. Generate a valid authentication token.
    2. Create a booking.
    3. Send an update with the same value under the incorrectly cased "Token" cookie name.
    4. Verify the update is rejected with HTTP 403.
    """
    logger.info("START | test_token_cookie_name_case_variation_is_rejected")
    logger.info("Step 1: Generate authentication token")
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
    logger.info("Step 1 result: Token generated")

    token = response_body["token"]

    logger.info("Step 2: Create booking")
    payload = read_json("booking_data.json")
    response = booking_helper.create_booking(payload)
    assert response.ok
    assert response.status == 200
    response_body = response.json()
    assert response_body["bookingid"] > 0
    bookingId = response_body["bookingid"]
    logger.info("Step 2 result: Booking ID=%s", bookingId)

    headers = {
        "Content-Type" : "application/json",
        "Cookie" : f"Token={token}"
    }
    logger.info("Step 3: Send update with incorrectly cased Token cookie")
    update_response = booking_helper.update_booking(
        bookingId=bookingId, payload=payload, headers=headers
    )

    logger.info("Step 3 result: HTTP %s", update_response.status)
    assert update_response.status == 403
    logger.info("END | test_token_cookie_name_case_variation_is_rejected")


@pytest.mark.order(16)
@pytest.mark.authentication
@pytest.mark.authorization
@pytest.mark.regression
@pytest.mark.security
def test_token_cookie_with_extra_unrelated_cookies(booking_helper):
    """Verify valid tokens work alongside unrelated cookies.

    Test steps:
    1. Generate a valid authentication token.
    2. Create a booking.
    3. Send the valid token and an unrelated session cookie.
    4. Verify the update succeeds with HTTP 200.
    """
    logger.info("START | test_token_cookie_with_extra_unrelated_cookies")
    logger.info("Step 1: Generate authentication token")
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
    logger.info("Step 1 result: Token generated")

    token = response_body["token"]

    logger.info("Step 2: Create booking")
    payload = read_json("booking_data.json")
    response = booking_helper.create_booking(payload)
    assert response.ok
    assert response.status == 200
    response_body = response.json()
    assert response_body["bookingid"] > 0
    bookingId = response_body["bookingid"]
    logger.info("Step 2 result: Booking ID=%s", bookingId)

    headers = {
        "Content-Type" : "application/json",
        "Cookie" : f"token={token};session_id=abc123"
    }
    logger.info("Step 3: Update with valid token and unrelated session cookie")
    update_response = booking_helper.update_booking(
        bookingId=bookingId, payload=payload,
        headers = headers
    )

    logger.info("Step 3 result: HTTP %s", update_response.status)
    assert update_response.status == 200
    logger.info("END | test_token_cookie_with_extra_unrelated_cookies")


@pytest.mark.order(17)
@pytest.mark.authentication
@pytest.mark.authorization
@pytest.mark.regression
@pytest.mark.security
def test_duplicate_token_cookie_with_same_value_is_accepted(booking_helper):
    """Verify duplicate cookies with the same token value are accepted.

    Test steps:
    1. Generate a valid authentication token.
    2. Create a booking.
    3. Send two "token" cookies containing the same value.
    4. Verify the update succeeds with HTTP 200.
    """
    logger.info("START | test_duplicate_token_cookie_with_same_value_is_accepted")
    logger.info("Step 1: Generate authentication token")
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
    logger.info("Step 1 result: Token generated")

    token = response_body["token"]

    logger.info("Step 2: Create booking")
    payload = read_json("booking_data.json")
    response = booking_helper.create_booking(payload)
    assert response.ok
    assert response.status == 200
    response_body = response.json()
    assert response_body["bookingid"] > 0
    bookingId = response_body["bookingid"]
    logger.info("Step 2 result: Booking ID=%s", bookingId)

    headers = {
        "Content-Type": "application/json",
        "Cookie": f"token={token};token={token}",
    }
    logger.info("Step 3: Update with duplicate same-value token cookies")
    update_response = booking_helper.update_booking(
        bookingId=bookingId, payload=payload, headers=headers
    )

    logger.info("Step 3 result: HTTP %s", update_response.status)
    assert update_response.status == 200
    logger.info("END | test_duplicate_token_cookie_with_same_value_is_accepted")


@pytest.mark.order(18)
@pytest.mark.authentication
@pytest.mark.authorization
@pytest.mark.regression
@pytest.mark.security
def test_token_cookie_with_surrounding_whitespace_is_accepted(booking_helper):
    """Verify accepted token cookies handle surrounding whitespace.

    Test steps:
    1. Generate a valid authentication token.
    2. Create a booking and capture its original state.
    3. Send an update using a token cookie with surrounding whitespace.
    4. Verify the update succeeds with HTTP 200.
    5. Fetch the booking and verify it remains unchanged.
    """
    logger.info("START | test_token_cookie_with_surrounding_whitespace_is_accepted")
    logger.info("Step 1: Generate authentication token")
    response = booking_helper.create_auth_token(
        username=BOOKER_USERNAME, password=BOOKER_PASSWORD
    )
    assert response.status == 200
    token = response.json()["token"]
    logger.info("Step 1 result: Token generated")

    logger.info("Step 2: Create booking and capture original state")
    payload = read_json("booking_data.json")
    response = booking_helper.create_booking(payload)

    assert response.status == 200
    bookingId = response.json()["bookingid"]
    original_booking = booking_helper.get_booking_by_id(bookingId).json()
    logger.info("Step 2 result: Booking ID=%s", bookingId)

    headers = {
    "Content-Type": "application/json",
    "Cookie": f"token=   {token}   ",
}

    logger.info("Step 3: Send update with surrounding token whitespace")
    update_response = booking_helper.update_booking(
        bookingId=bookingId,
        payload=payload,
        headers=headers
    )

    logger.info("Step 3 result: HTTP %s", update_response.status)
    assert update_response.status == 200

    logger.info("Step 4: Fetch final booking state")
    final_booking = booking_helper.get_booking_by_id(bookingId).json()

    logger.info("Step 4 result: Final state equals original=%s", final_booking == original_booking)
    assert final_booking == original_booking
    logger.info("END | test_token_cookie_with_surrounding_whitespace_is_accepted")

@pytest.mark.order(19)
@pytest.mark.authentication
@pytest.mark.authorization
@pytest.mark.regression
@pytest.mark.security
def test_old_and_new_tokens_validity_after_generating_second_token(booking_helper):
    """Verify generating a second token does not invalidate the first token.

    Test steps:
    1. Generate the first authentication token.
    2. Generate a second authentication token.
    3. Create a booking.
    4. Update the booking using the first token and verify HTTP 200.
    5. Update the booking using the second token and verify HTTP 200.
    """

    logger.info("START | test_old_and_new_tokens_validity_after_generating_second_token")
    logger.info("Step 1: Generate first authentication token")
    response1 = booking_helper.create_auth_token(
        username=BOOKER_USERNAME,
        password=BOOKER_PASSWORD
    )

    assert response1.status == 200
    token1 = response1.json()["token"]

    logger.info("Step 1 result: First token generated")

    logger.info("Step 2: Generate second authentication token")
    response2 = booking_helper.create_auth_token(
        username=BOOKER_USERNAME,
        password=BOOKER_PASSWORD
    )

    assert response2.status == 200
    token2 = response2.json()["token"]

    logger.info("Step 2 result: Second token generated")

    logger.info("Step 3: Create booking")
    payload = read_json("booking_data.json")

    create_response = booking_helper.create_booking(payload)

    assert create_response.status == 200

    booking_id = create_response.json()["bookingid"]

    logger.info("Step 3 result: Booking ID=%s", booking_id)

    logger.info("Step 4: Update booking using first token")
    old_token_response = booking_helper.update_booking(
        bookingId=booking_id,
        payload=payload,
        token=token1
    )

    logger.info("Step 4 result: HTTP %s", old_token_response.status)

    logger.info("Step 5: Update booking using second token")
    new_token_response = booking_helper.update_booking(
        bookingId=booking_id,
        payload=payload,
        token=token2
    )

    logger.info("Step 5 result: HTTP %s", new_token_response.status)

    assert old_token_response.status == 200
    assert new_token_response.status == 200
    logger.info("END | test_old_and_new_tokens_validity_after_generating_second_token")
