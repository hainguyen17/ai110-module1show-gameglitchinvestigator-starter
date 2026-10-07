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


def test_parse_guess_accepts_whole_number_decimals():
    # "42.0" is a whole number written with a decimal point. Accept it.
    assert parse_guess("42.0") == (True, 42, None)
    assert parse_guess("50.") == (True, 50, None)


# ---------------------------------------------------------------------------
# Challenge 1: advanced edge cases. Each of these broke the game after the
# Phase 2 fixes were in place.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw", ["1.0e999", "1.5e400", "-1.0e999"])
def test_edge_case_1_huge_float_does_not_crash(raw):
    # float("1.0e999") is inf, and int(inf) raises OverflowError. The original
    # except clause caught only ValueError/TypeError, so this crashed the app
    # with a traceback. Must now be a clean rejection.
    ok, value, err = parse_guess(raw, low=1, high=100)
    assert ok is False
    assert value is None
    assert err == "That is not a number."


@pytest.mark.parametrize("raw", ["nan", "inf", "-inf", "infinity"])
def test_edge_case_1_non_finite_words_are_rejected(raw):
    # float() accepts these spellings, so they must not slip through either.
    ok, value, err = parse_guess(raw, low=1, high=100)
    assert ok is False
    assert err == "That is not a number."


@pytest.mark.parametrize("raw", ["42.9", "42.1", "0.5", "99.999"])
def test_edge_case_2_fractional_input_is_rejected(raw):
    # The original truncated 42.9 to 42 silently. A whole-number game should
    # tell the player instead of guessing what they meant.
    ok, value, err = parse_guess(raw, low=1, high=100)
    assert ok is False
    assert value is None
    assert err == "Enter a whole number."


def test_edge_case_2_truncation_cannot_bypass_range_check():
    # 100.7 used to truncate to 100 and pass the 1-100 range check even though
    # 100.7 > 100. Now rejected before the range check is reached.
    ok, value, err = parse_guess("100.7", low=1, high=100)
    assert ok is False
    assert value is None


@pytest.mark.parametrize("raw,expected", [
    ("+50", 50),      # explicit plus sign
    (" 50 ", 50),     # surrounding whitespace
    ("1_0", 10),      # Python accepts underscores in int()
    ("４２", 42),      # full-width digits are valid Unicode decimals
])
def test_parse_guess_tolerates_unusual_but_valid_integers(raw, expected):
    # Documenting current behavior: these parse because int() accepts them.
    assert parse_guess(raw, low=1, high=100) == (True, expected, None)


def test_parse_guess_rejects_extremely_long_digit_string():
    # Python 3.11+ caps int(str) at 4300 digits and raises ValueError.
    # Either outcome (ValueError -> "not a number", or huge int -> out of
    # range) must be a clean rejection, never a crash.
    ok, value, err = parse_guess("1" * 5000, low=1, high=100)
    assert ok is False
    assert value is None
