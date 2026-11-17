import pytest

from config.config import USERNAME, PASSWORD
from utils import data_generator


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
            data_generator.generate_password(),
            "Bad credentials",
            id="correct-username-wrong-password",
        ),
        pytest.param(
            data_generator.generate_username(),
            PASSWORD,
            "Bad credentials",
            id="wrong-username-correct-password",
        ),
        pytest.param(
            data_generator.generate_username(),
            data_generator.generate_password(),
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


