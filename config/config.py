"""Environment-backed configuration and API endpoint constants."""

import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
BOOKER_USERNAME = os.getenv("BOOKER_USERNAME")
BOOKER_PASSWORD = os.getenv("BOOKER_PASSWORD")

missing_environment = [
    name
    for name, value in (
        ("BASE_URL", BASE_URL),
        ("BOOKER_USERNAME", BOOKER_USERNAME),
        ("BOOKER_PASSWORD", BOOKER_PASSWORD),
    )
    if not value
]
if missing_environment:
    raise EnvironmentError(
        "Missing required environment variables: "
        + ", ".join(missing_environment)
    )

# Health Check
PING_CHECK = f"{BASE_URL}/ping"

# Authentication
AUTH_TOKEN = f"{BASE_URL}/auth"

# Booking Endpoints
GET_ALL_BOOKING_IDS = f"{BASE_URL}/booking"
CREATE_BOOKING = f"{BASE_URL}/booking"

GET_BOOKING = f"{BASE_URL}/booking/{{booking_id}}"
UPDATE_BOOKING = f"{BASE_URL}/booking/{{booking_id}}"
PARTIAL_BOOKING = f"{BASE_URL}/booking/{{booking_id}}"
DELETE_BOOKING = f"{BASE_URL}/booking/{{booking_id}}"

CHECK_PING = f"{BASE_URL}/ping"

PERF_P95_MS = 2000
PERF_MAX_MS = 5000
