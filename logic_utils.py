"""Pure game logic for the guessing game.

Nothing in this module imports Streamlit. Every function takes plain values
and returns plain values so it can be unit-tested with pytest without a UI.
"""

# FIX: Refactored all four logic functions out of app.py into this module
# using Cursor agent mode, so they can be imported by both app.py and the
# tests. Reviewed the diff function-by-function before accepting.

WIN = "Win"
TOO_HIGH = "Too High"
TOO_LOW = "Too Low"


def get_range_for_difficulty(difficulty: str):
    """Return (low, high) inclusive range for a given difficulty."""
    if difficulty == "Easy":
        return 1, 20
    if difficulty == "Normal":
        return 1, 100
    if difficulty == "Hard":
        return 1, 50
    return 1, 100


def parse_guess(raw, low: int = 1, high: int = 100):
    """
    Parse user input into an int guess and validate it against [low, high].

    Returns: (ok: bool, guess_int: int | None, error_message: str | None)
    """
    if raw is None or str(raw).strip() == "":
        return False, None, "Enter a guess."

    text = str(raw).strip()

    try:
        # Accept "42" and "42.0" but reject "abc", "4 2", "", etc.
        value = int(float(text)) if "." in text else int(text)
    except (ValueError, TypeError):
        return False, None, "That is not a number."

    # FIX (Bug 3): Added range validation. The original only checked "is it a
    # number", so 1000000 and -1 were accepted as valid guesses even though the
    # UI promises a 1 to 100 range. Verified with pytest (test_parse_guess_*)
    # and in the live app: out-of-range input now shows an error and does not
    # consume an attempt.
    if value < low or value > high:
        return False, None, f"Enter a number between {low} and {high}."

    return True, value, None


def check_guess(guess: int, secret: int) -> str:
    """
    Compare guess to secret and return an outcome string.

    Returns one of: "Win", "Too High", "Too Low".
    """
    # FIX: Removed the original try/except TypeError fallback that compared
    # str(guess) to str(secret) lexicographically ("60" > "7" is False). That
    # fallback only existed because app.py converted the secret to a string on
    # even-numbered attempts. Both the hack and the fallback are gone, so this
    # is now a plain integer comparison. Verified with the three starter tests
    # plus test_check_guess_integer_comparison_not_string.
    if guess == secret:
        return WIN
    if guess > secret:
        return TOO_HIGH
    return TOO_LOW


def hint_message(outcome: str) -> str:
    """Return the user-facing hint for a check_guess outcome."""
    # FIX: The original messages were backwards ("Too High" told the player to
    # "Go HIGHER!"). Split the message out of check_guess so the starter tests
    # can assert on the plain outcome string, and corrected the direction.
    if outcome == WIN:
        return "🎉 Correct!"
    if outcome == TOO_HIGH:
        return "📉 Too high. Go LOWER!"
    if outcome == TOO_LOW:
        return "📈 Too low. Go HIGHER!"
    return ""


def update_score(current_score: int, outcome: str, attempt_number: int) -> int:
    """Update score based on outcome and attempt number.

    Moved verbatim from app.py. Behavior intentionally unchanged in this pass.
    """
    if outcome == WIN:
        points = 100 - 10 * (attempt_number + 1)
        if points < 10:
            points = 10
        return current_score + points

    if outcome == TOO_HIGH:
        # FIXME (not fixed in this pass): awarding +5 for a wrong guess on
        # even-numbered attempts looks like a bug, but it is out of scope for
        # the two bugs targeted here. Left as-is so the diff stays reviewable.
        if attempt_number % 2 == 0:
            return current_score + 5
        return current_score - 5

    if outcome == TOO_LOW:
        return current_score - 5

    return current_score
