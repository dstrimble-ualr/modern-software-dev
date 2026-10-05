# END-TO-END TESTS
# Scope: a real Chromium browser talking to the real server over real HTTP.
# conftest.py starts `python -m app` for us. Playwright drives the page the way
# a user would: type, click, look. Nothing in the front end or back end is mocked.
import time

from playwright.sync_api import Page, expect


def test_shows_the_login_form_when_not_signed_in(page: Page, server):
    page.goto(f"{server}/")
    expect(page.get_by_placeholder("username")).to_be_visible()
    expect(page.get_by_placeholder("password")).to_be_visible()
    expect(page.get_by_role("button", name="Login")).to_be_visible()


def test_wrong_password_shows_login_failed_alert_and_stays_on_the_form(page: Page, server):
    alerts = []

    def on_dialog(dialog):
        alerts.append(dialog.message)
        dialog.dismiss()

    page.on("dialog", on_dialog)

    page.goto(f"{server}/")
    page.get_by_placeholder("username").fill("admin")
    page.get_by_placeholder("password").fill("wrong")
    page.get_by_role("button", name="Login").click()

    deadline = time.time() + 5
    while time.time() < deadline and not alerts:
        page.wait_for_timeout(50)
    assert alerts == ["login failed"]
    expect(page.get_by_placeholder("username")).to_be_visible()


def test_login_shows_the_widgets_and_logout_returns_to_the_form(page: Page, server):
    page.goto(f"{server}/")
    page.get_by_placeholder("username").fill("admin")
    page.get_by_placeholder("password").fill("password")
    page.get_by_role("button", name="Login").click()

    expect(page.get_by_role("heading", name="Widgets")).to_be_visible()
    expect(page.get_by_role("heading", name="Widget A")).to_be_visible()
    expect(page.get_by_text("$9.99")).to_be_visible()
    expect(page.get_by_role("heading", level=3)).to_have_count(3)

    page.get_by_role("button", name="Logout").click()
    expect(page.get_by_placeholder("username")).to_be_visible()
