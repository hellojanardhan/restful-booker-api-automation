"""Pytest fixtures and hooks for the Restful Booker test suite."""

import pytest
import os
import subprocess
import shutil
from pathlib import Path
from config.config import DELETE_BOOKING
from playwright.sync_api import Playwright
from utils.rest_helper import RestHelper
from utils.booking_helper import BookingHelper
from utils.logger import get_logger

logger = get_logger("TestRunner")


@pytest.hookimpl(trylast=True)
def pytest_runtest_logstart(nodeid, location):
    """Log the start of a test case."""
    print()
    logger.info("START | %s", nodeid.rsplit("::", 1)[-1])


@pytest.hookimpl(trylast=True)
def pytest_runtest_logreport(report):
    """Log pass, fail, and skip reports for test cases."""

    if report.passed and report.when == "call":
        print()
        logger.info("PASS | %s", report.nodeid.rsplit("::", 1)[-1])

    elif report.failed:
        print()
        logger.error(
            "FAIL | %s | %s | %s",
            report.nodeid.rsplit("::", 1)[-1],
            report.when,
            str(report.longrepr),
        )

    elif report.skipped:
        print()
        logger.warning(
            "SKIP | %s | %s",
            report.nodeid.rsplit("::", 1)[-1],
            report.when,
        )


@pytest.fixture(scope="function")
def request_context(playwright: Playwright):
    """Create and dispose a Playwright API request context per test."""
    request_context = None
    try:
        request_context = playwright.request.new_context()
    except Exception as error:
        logger.exception("Unable to create Playwright API request context")
        raise RuntimeError(f"Unable to create API request context: {error}") from error

    try:
        yield request_context
    finally:
        if request_context is not None:
            try:
                request_context.dispose()
            except Exception as error:
                logger.exception("Unable to dispose Playwright API request context")
                raise RuntimeError(
                    f"Unable to dispose API request context: {error}"
                ) from error


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):
    """Clean stale Allure results before the test session starts."""
    allure_results = Path("reports/allure-results")

    try:
        if allure_results.exists():
            shutil.rmtree(allure_results)

        allure_results.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        logger.exception("Unable to prepare Allure results directory")
        raise RuntimeError(
            f"Unable to prepare Allure results directory: {error}"
        ) from error


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    """Generate the Allure HTML report after the test session finishes."""

    print("\nGenerating Allure report...")

    try:
        allure_executable = shutil.which("allure") or shutil.which("allure.bat")

        if not allure_executable:
            logger.error("Allure CLI is not installed or not available in PATH")
            print("Allure CLI not found. Skipping report generation.")
            return

        command = [
            allure_executable,
            "generate",
            "reports/allure-results",
            "-o",
            "reports/allure-report",
            "--clean",
        ]

        # Windows requires cmd.exe to execute a .bat file.
        if os.name == "nt":
            command = ["cmd.exe", "/c"] + command

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )

        if result.returncode == 0:
            print("Allure report generated successfully!")
            logger.info("Allure report generated successfully")
        else:
            print("Allure report generation failed!")
            logger.error("Allure CLI error: %s", result.stderr)

    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as error:
        logger.exception("Allure report generation failed")
        print(f"Allure reporting error: {error}")

    except Exception as error:
        logger.exception("Unexpected Allure report generation error")
        print(f"Unexpected Allure reporting error: {error}")


@pytest.fixture(scope="function")
def rest_helper(request_context):
    """Provide a REST helper for a test."""
    return RestHelper(request_context)


@pytest.fixture(scope="function")
def booking_helper(rest_helper):
    """Provide a booking API helper for a test."""
    return BookingHelper(rest_helper)

@pytest.mark.fixture
def delete_booking(self, bookingId = None, token=None):
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
