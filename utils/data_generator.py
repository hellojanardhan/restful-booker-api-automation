"""Data generation and test-data file loading utilities."""

from faker import Faker
from pathlib import Path
import json
import random
import string

faker = Faker()


def read_json(file_name):
    """Load and return a JSON test-data file."""

    file_path = Path(__file__).resolve().parent.parent / "test_data" / file_name

    try:
        with file_path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError as error:
        raise FileNotFoundError(
            f"Test-data file not found: {file_path}"
        ) from error
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid JSON in test-data file: {file_path}"
        ) from error
    except OSError as error:
        raise OSError(
            f"Unable to read test-data file: {file_path}"
        ) from error


def generate_username():
    """Generate a random lowercase username."""
    length = random.randint(8, 10)

    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def generate_password():
    """Generate a random password containing letters, digits, and punctuation."""
    length = random.randint(8, 10)

    characters = string.ascii_letters + string.digits + string.punctuation

    return "".join(random.choices(characters, k=length))


def generate_firstname():
    """Generate a random first name."""
    return faker.first_name()


def generate_lastname():
    """Generate a random last name."""
    return faker.last_name()


def generate_totalprice():
    """Generate a random booking total price."""
    return random.randint(100, 10000)


def generate_depositpaid():
    """Generate a random deposit-paid status."""
    return random.choice([True, False])


def generate_checkin():
    """Generate a random check-in date within the next 30 days."""
    return faker.date_between(start_date="today", end_date="+30d").isoformat()


def generate_checkout(checkin):
    """Generate a valid checkout date 1 to 10 days after check-in."""
    from datetime import datetime, timedelta

    checkin_date = datetime.strptime(checkin, "%Y-%m-%d")

    checkout_date = checkin_date + timedelta(days=random.randint(1, 10))

    return checkout_date.strftime("%Y-%m-%d")


def generate_additionalneeds():
    """Generate a random additional-needs value."""
    return random.choice(["Breakfast", "Lunch", "Dinner", "None"])
