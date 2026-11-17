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

    def create_auth_token(self, username, password):

        headers = {"Content-Type": "application/json"}

        payload = {
            "username": username,
            "password": password
        }

        response = self.rest_helper.execute(
            method="post",
            endpoint=AUTH_TOKEN,
            data=payload,
            headers=headers
        )

        return response

    def get_all_booking_ids(self):
        response = self.rest_helper.execute(method="get", endpoint=GET_ALL_BOOKING_IDS)

        return response

    def get_booking_by_id(self,bookingId):
        headers = {
            "Content-Type" : "application/json"
        }
        response = self.rest_helper.execute(
            method = "get",
            endpoint = f"{GET_BOOKING}/{bookingId}"
            
        )

        return response

    def create_booking(self,payload):
        headers = {
            "Content-Type" : "application/json"
        }

        response = self.rest_helper.execute(
            method = "post",
            endpoint = CREATE_BOOKING,
            data = payload,
            headers = headers
        )

        return response

    def update_booking(self,payload,bookingId):
        headers = {
            "Content-Type" : "application/json"
        }

        response = self.rest_helper.execute(
            method = "post",
            endpoint = f"{UPDATE_BOOKING}/{bookingId}",
            data = payload,
            headers = headers
        )

        return response

    def partial_update_booking(self,bookingId, payload):
        headers = {"Content-Type": "application/json"}

        response = self.rest_helper.execute(
            method="post", endpoint=f"{PARTIAL_BOOKING}/{bookingId}", data=payload, headers=headers
        )

        return response

    def delete_booking(self, bookingId):

        headers = {"Content-Type": "application/json"}

        response = self.rest_helper.execute(
            method="post", endpoint=f"{DELETE_BOOKING}/{bookingId}",headers=headers
        )

        return response
