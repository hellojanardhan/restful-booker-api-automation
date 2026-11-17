from faker import Faker
from pathlib import Path
import json
import random
import string

faker = Faker()


def read_json(file_name):

    file_path = Path(__file__).resolve().parent.parent / "test_data" / file_name

    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def generate_username():
    length = random.randint(8, 10)

    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def generate_password():
    length = random.randint(8, 10)

    characters = string.ascii_letters + string.digits + string.punctuation

    return "".join(random.choices(characters, k=length))


def generate_firstname():
    return faker.first_name()


def generate_lastname():
    return faker.last_name()


def generate_totalprice():
    return random.randint(100, 10000)


def generate_depositpaid():
    return random.choice([True, False])


def generate_checkin():
    return faker.date_between(start_date="today", end_date="+30d").isoformat()


def generate_checkout(checkin):
    from datetime import datetime, timedelta

    checkin_date = datetime.strptime(checkin, "%Y-%m-%d")

    checkout_date = checkin_date + timedelta(days=random.randint(1, 10))

    return checkout_date.strftime("%Y-%m-%d")


def generate_additionalneeds():
    return random.choice(["Breakfast", "Lunch", "Dinner", "None"])
