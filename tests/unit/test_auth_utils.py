# UNIT TESTS
# Scope: one module of pure functions, nothing else.
# No Flask, no HTTP, no database, no browser. These run in milliseconds.
from app.auth_utils import (
    AUTH_TOKEN,
    has_login_fields,
    has_valid_auth_token,
    normalize_credentials,
)


class TestHasValidAuthToken:
    def test_accepts_the_expected_token(self):
        assert has_valid_auth_token(AUTH_TOKEN) is True

    def test_rejects_anything_else(self):
        assert has_valid_auth_token("wrong-token") is False
        assert has_valid_auth_token("") is False
        assert has_valid_auth_token(None) is False


class TestNormalizeCredentials:
    def test_trims_username_and_leaves_password_untouched(self):
        assert normalize_credentials({"username": "  admin  ", "password": " pw "}) == {
            "username": "admin",
            "password": " pw ",
        }

    def test_turns_non_string_values_into_empty_strings(self):
        assert normalize_credentials({"username": 42, "password": ["x"]}) == {
            "username": "",
            "password": "",
        }

    def test_handles_missing_or_non_dict_body(self):
        assert normalize_credentials(None) == {"username": "", "password": ""}
        assert normalize_credentials(["not", "a", "dict"]) == {"username": "", "password": ""}


class TestHasLoginFields:
    def test_true_only_when_both_fields_are_non_empty(self):
        assert has_login_fields({"username": "admin", "password": "password"}) is True
        assert has_login_fields({"username": "   ", "password": "password"}) is False
        assert has_login_fields({"username": "admin", "password": ""}) is False
        assert has_login_fields({}) is False
        assert has_login_fields(None) is False
