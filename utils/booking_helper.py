"""High-level helper methods for Restful Booker API operations."""

import json
from config.config import (
    AUTH_TOKEN,
    GET_BOOKING,
    CREATE_BOOKING,
    DELETE_BOOKING,
    GET_ALL_BOOKING_IDS,
    PARTIAL_BOOKING,
    UPDATE_BOOKING,
    PING_CHECK
)


class BookingHelper:
    """Build and execute booking API requests through a REST helper."""

    def __init__(self, rest_helper):
        """Initialize the helper with a REST request context."""
        self.rest_helper = rest_helper

    def create_auth_token(self, username=None, password=None, payload=None, headers = None):
        """Create an authentication token."""

        if headers is None:
            headers = {"Content-Type": "application/json"}

        if payload is None:
            payload = {"username": username, "password": password}

        response = self.rest_helper.execute(
            method="POST", endpoint=AUTH_TOKEN, data=payload, headers=headers
        )

        return response

    def get_all_bookings(self, headers = None , params = None):
        """Retrieve all booking identifiers."""
        if headers is None:
            headers = {"Content-Type": "application/json"}
        response = self.rest_helper.execute(
            method="GET",
            endpoint=GET_ALL_BOOKING_IDS,
            headers=headers,
            params=params,
        )

        return response

    def get_all_booking_ids(self, headers=None, params=None):
        """Retrieve all booking identifiers using the collection helper name."""
        return self.get_all_bookings(headers=headers, params=params)

    def get_booking_by_id(self, bookingId, headers=None):
        """Retrieve a single booking by its booking identifier."""
        if bookingId is None:
            raise ValueError("bookingId is required")
        if headers is None:
            headers = {"Content-Type": "application/json"}

        return self.rest_helper.execute(
            method="GET",
            endpoint=GET_BOOKING.format(booking_id=bookingId),
            headers=headers,
        )

    def get_booking_details(self, bookingId = None, headers=None , params = None):
        """Retrieve a booking by its identifier."""
        if headers is None:
            headers = {"Content-Type": "application/json"}
        if params is None:
            response = self.rest_helper.execute(
                method="GET", endpoint=GET_BOOKING.format(booking_id=bookingId), headers=headers
            )
        else:
            response = self.rest_helper.execute(
                method="GET",
                endpoint=GET_ALL_BOOKING_IDS,
                headers=headers,
                params=params,
                )
        return response


    def create_booking(self, payload=None, params=None, token=None, headers=None):
        """Create a booking from the supplied payload."""

        if payload is None:
            raise ValueError("Booking payload is required")

        response = self.rest_helper.execute(
            method="POST",
            endpoint=CREATE_BOOKING,
            data=payload,
            params=params,
            headers=headers,
        )

        return response

    def update_booking(
        self, token=None, bookingId=None, payload=None, headers=None, params=None
    ):
        """Replace a booking and optionally authenticate with a token."""
        if bookingId is None:
            raise ValueError("bookingId is required")
        if payload is None:
            raise ValueError("Booking payload is required")

        if headers is None:
            headers = {"Content-Type": "application/json"}

        if token is not None:
            headers["Cookie"] = f"token={token}"

        response = self.rest_helper.execute(
            method="PUT",
            endpoint=UPDATE_BOOKING.format(booking_id=bookingId),
            data=payload,
            headers=headers,
            params=params,
        )

        return response

    def partial_update_booking(self, bookingId, payload, token=None, headers=None):
        """Apply a partial update to a booking."""
        if bookingId is None:
            raise ValueError("bookingId is required")
        if payload is None:
            raise ValueError("Booking payload is required")
        if headers is None:
            headers = {"Content-Type": "application/json"}
        else:
            headers = headers.copy()
            headers.setdefault("Content-Type", "application/json")
        if token is not None:
            headers["Cookie"] = f"token={token}"

        response = self.rest_helper.execute(
            method="patch",
            endpoint=PARTIAL_BOOKING.format(booking_id=bookingId),
            data=payload,
            headers=headers,
        )

        return response

    def delete_booking(self, bookingId, token=None):
        """Delete a booking by identifier."""
        if bookingId is None:
            raise ValueError("bookingId is required")

        headers = {"Content-Type": "application/json"}
        if token is not None:
            headers["Cookie"] = f"token={token}"

        response = self.rest_helper.execute(
            method="delete",
            endpoint=DELETE_BOOKING.format(booking_id=bookingId),
            headers=headers,
        )

        return response

    def perform_booking_operation(self, method, booking_id, payload=None, token=None):
        """Perform a supported booking operation."""

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

    def check_ping(self, method=None, token=None, headers=None):
        """Execute a health-check request, using GET by default."""
        if headers is None:
            headers = {"Content-Type": "application/json"}

        if token is not None:
            headers["Cookie"] = f"token={token}"

        if method is None:
            method = "GET"

        response = self.rest_helper.execute(
            method=method,
            endpoint=PING_CHECK,
            headers=headers,
        )
        return response
