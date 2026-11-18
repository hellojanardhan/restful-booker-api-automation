import pytest
import subprocess
import shutil
from pathlib import Path

from playwright.sync_api import Playwright
from utils.rest_helper import RestHelper
from utils.booking_helper import BookingHelper
from utils.logger import get_logger

logger = get_logger("TestRunner")


@pytest.hookimpl(trylast=True)
def pytest_runtest_logstart(nodeid, location):
    print()
    logger.info("START | %s", nodeid.rsplit("::", 1)[-1])


@pytest.hookimpl(trylast=True)
def pytest_runtest_logreport(report):

    if report.passed and report.when == "call":
        print()
        logger.info("PASS | %s", report.nodeid.rsplit("::", 1)[-1])

    elif report.failed:
        print()
        logger.error(
            "FAIL | %s | %s",
            report.nodeid.rsplit("::", 1)[-1],
            report.when,
        )

    elif report.skipped:
        print()
        logger.warning(
            "SKIP | %s | %s",
            report.nodeid.rsplit("::", 1)[-1],
            report.when,
        )


# -------------------------------
# API Request Context Fixture
# -------------------------------


@pytest.fixture(scope="function")
def request_context(playwright: Playwright):
    request_context = playwright.request.new_context()

    yield request_context

    request_context.dispose()


# -------------------------------
# Allure Results Cleanup
# -------------------------------


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):
    allure_results = Path("reports/allure-results")

    if allure_results.exists():
        shutil.rmtree(allure_results)

    allure_results.mkdir(parents=True, exist_ok=True)


# -------------------------------
# Allure Report Generation
# -------------------------------


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    print("\nGenerating Allure report...")

    try:
        result = subprocess.run(
            [
                "cmd.exe",
                "/c",
                "allure.bat",
                "generate",
                "reports/allure-results",
                "-o",
                "reports/allure-report",
                "--clean",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            print("Allure report generated successfully!")
        else:
            print("Allure report generation failed!")
            print(result.stderr)

    except Exception as error:
        print(f"Allure reporting error: {error}")


# -------------------------------
# Rest Helper Fixture
# -------------------------------


@pytest.fixture(scope="function")
def rest_helper(request_context):
    return RestHelper(request_context)


# -------------------------------
# Booking Helper Fixture
# -------------------------------


@pytest.fixture(scope="function")
def booking_helper(rest_helper):
    return BookingHelper(rest_helper)
