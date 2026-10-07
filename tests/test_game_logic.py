import pytest

from logic_utils import check_guess, hint_message, parse_guess


# ---------------------------------------------------------------------------
# Starter tests (unchanged). These define the contract: check_guess returns a
# plain outcome string, not a tuple.
# ---------------------------------------------------------------------------

def test_winning_guess():
    # If the secret is 50 and guess is 50, it should be a win
    result = check_guess(50, 50)
    assert result == "Win"

def test_guess_too_high():
    # If secret is 50 and guess is 60, hint should be "Too High"
    result = check_guess(60, 50)
    assert result == "Too High"

def test_guess_too_low():
    # If secret is 50 and guess is 40, hint should be "Too Low"
    result = check_guess(40, 50)
    assert result == "Too Low"


# ---------------------------------------------------------------------------
# Regression test for the string-comparison glitch.
# The original app.py converted the secret to a string on even-numbered
# attempts, which made check_guess fall into a lexicographic comparison
# ("60" > "7" is False). This case is the exact pair that exposed it.
# ---------------------------------------------------------------------------

def test_check_guess_integer_comparison_not_string():
    # Lexicographically "60" < "7", but numerically 60 > 7.
    assert check_guess(60, 7) == "Too High"
    assert check_guess(7, 60) == "Too Low"


# ---------------------------------------------------------------------------
# Hint direction. The original messages were inverted: a "Too High" outcome
# told the player to go HIGHER.
# ---------------------------------------------------------------------------

def test_hint_message_direction():
    assert "LOWER" in hint_message("Too High")
    assert "HIGHER" in hint_message("Too Low")
    assert "Correct" in hint_message("Win")


# ---------------------------------------------------------------------------
# Bug 3: range validation. parse_guess used to accept any integer at all.
# ---------------------------------------------------------------------------

def test_parse_guess_accepts_in_range_value():
    ok, value, err = parse_guess("42", low=1, high=100)
    assert ok is True
    assert value == 42
    assert err is None


@pytest.mark.parametrize("raw", ["1000000", "101", "-1", "0"])
def test_parse_guess_rejects_out_of_range(raw):
    # These were all accepted by the original code despite the 1-100 UI text.
    ok, value, err = parse_guess(raw, low=1, high=100)
    assert ok is False
    assert value is None
    assert err == "Enter a number between 1 and 100."


def test_parse_guess_respects_difficulty_range():
    # Easy mode is 1-20, so 50 is a valid Normal guess but invalid on Easy.
    assert parse_guess("50", low=1, high=100)[0] is True
    assert parse_guess("50", low=1, high=20)[0] is False


def test_parse_guess_accepts_boundaries():
    assert parse_guess("1", low=1, high=100) == (True, 1, None)
    assert parse_guess("100", low=1, high=100) == (True, 100, None)


@pytest.mark.parametrize("raw", ["", "   ", None])
def test_parse_guess_rejects_empty(raw):
    ok, value, err = parse_guess(raw)
    assert ok is False
    assert err == "Enter a guess."


@pytest.mark.parametrize("raw", ["abc", "4 2", "1e3x"])
def test_parse_guess_rejects_non_numeric(raw):
    ok, value, err = parse_guess(raw)
    assert ok is False
    assert err == "That is not a number."


def test_parse_guess_truncates_decimal_input():
    # Original behavior preserved: "42.9" becomes 42.
    assert parse_guess("42.9") == (True, 42, None)
