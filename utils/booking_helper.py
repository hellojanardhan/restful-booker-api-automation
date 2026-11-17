import json
from config.config import (
    AUTH_TOKEN,
    GET_BOOKING,
    CREATE_BOOKING,
    DELETE_BOOKING,
    GET_ALL_BOOKING_IDS,
    PARTIAL_BOOKING,
    UPDATE_BOOKING,
)


class BookingHelper:

    def __init__(self, rest_helper):
        self.rest_helper = rest_helper

    def create_auth_token(self, username=None, password=None, payload=None, headers = None):

        if headers is None:
            headers = {"Content-Type": "application/json"}

        if payload is None:
            payload = {"username": username, "password": password}

        response = self.rest_helper.execute(
            method="POST", endpoint=AUTH_TOKEN, data=payload, headers=headers
        )

        return response

    def get_all_booking_ids(self):
        response = self.rest_helper.execute(method="get", endpoint=GET_ALL_BOOKING_IDS)

        return response

    def get_booking_by_id(self, bookingId):
        headers = {"Content-Type": "application/json"}
        response = self.rest_helper.execute(
            method="get", endpoint=GET_BOOKING.format(booking_id=bookingId)
        )

        return response

    def create_booking(self, payload):
        headers = {
            "Content-Type": "application/json",
        }

        response = self.rest_helper.execute(
            method="post", endpoint=CREATE_BOOKING, data=payload, headers=headers
        )

        return response


    def update_booking(self, token=None, bookingId=None, payload=None, headers=None):
        if headers is None:
            headers = {"Content-Type": "application/json"}

            if token is not None:
                headers["Cookie"] = f"token={token}"

        response = self.rest_helper.execute(
            method="PUT",
            endpoint=UPDATE_BOOKING.format(booking_id=bookingId),
            data=payload,
            headers=headers,
        )

        return response

    def partial_update_booking(self, bookingId, payload):
        headers = {"Content-Type": "application/json"}

        response = self.rest_helper.execute(
            method="patch",
            endpoint=PARTIAL_BOOKING.format(booking_id=bookingId),
            data=payload,
            headers=headers,
        )

        return response

    def delete_booking(self, bookingId):

        headers = {"Content-Type": "application/json"}

        response = self.rest_helper.execute(
            method="delete",
            endpoint=DELETE_BOOKING.format(booking_id=bookingId),
            headers=headers,
        )

        return response

    def perform_booking_operation(self, method, booking_id, payload=None, token=None):

        if token is not None:
            headers = {"Content-Type": "application/json", "Cookie": f"token={token}"}
        else:
            headers = {"Content-Type": "application/json"}

        endpoints = {
            "PUT": UPDATE_BOOKING,
            "PATCH": PARTIAL_BOOKING,
            "DELETE": DELETE_BOOKING,
        }

        endpoint = endpoints.get(method.upper())

        if endpoint is None:
            raise ValueError(f"Unsupported booking operation: {method}")

        response = self.rest_helper.execute(
            method=method,
            endpoint=endpoint.format(booking_id=booking_id),
            data=payload,
            headers=headers,
        )

        return response
