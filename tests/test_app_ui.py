"""
End-to-end checks against the real app.py using Streamlit's AppTest harness.

These simulate the exact click sequences that reproduced Bug 1 and Bug 3 in the
browser, so the fixes are verified at the UI layer and not only in logic_utils.
"""

from streamlit.testing.v1 import AppTest


def _start_app():
    at = AppTest.from_file("app.py", default_timeout=10)
    at.run()
    return at


def _submit(at, text):
    at.text_input[0].set_value(text)
    at.button[0].click()  # "Submit Guess"
    at.run()


def _click_new_game(at):
    at.button[1].click()  # "New Game"
    at.run()


def test_bug1_new_game_works_after_winning():
    at = _start_app()
    secret = at.session_state["secret"]

    # Win the round.
    _submit(at, str(secret))
    assert at.session_state["status"] == "won"
    assert any("You won" in s.value for s in at.success)

    # Before the fix, this click did nothing and status stayed "won".
    _click_new_game(at)
    assert at.session_state["status"] == "playing"
    assert at.session_state["attempts"] == 0
    assert at.session_state["score"] == 0
    assert at.session_state["history"] == []
    assert not any("already won" in s.value for s in at.success)

    # And the game is actually playable again: a wrong guess produces a hint.
    new_secret = at.session_state["secret"]
    wrong = 1 if new_secret != 1 else 2
    _submit(at, str(wrong))
    assert at.session_state["attempts"] == 1
    assert len(at.warning) == 1


def test_bug1_submit_responds_after_new_game():
    at = _start_app()
    _submit(at, str(at.session_state["secret"]))
    _click_new_game(at)

    # Submit must reach the handler (it is below the status gate).
    secret = at.session_state["secret"]
    _submit(at, str(secret))
    assert at.session_state["status"] == "won"


def test_bug3_out_of_range_guess_is_rejected_and_costs_no_attempt():
    at = _start_app()
    attempts_before = at.session_state["attempts"]

    for bad in ["1000000", "-1", "0", "101"]:
        _submit(at, bad)
        assert any("between 1 and 100" in e.value for e in at.error), bad
        assert at.session_state["attempts"] == attempts_before, bad
        assert at.session_state["history"] == [], bad
        assert len(at.warning) == 0, bad  # no "Go HIGHER/LOWER" hint shown


def test_hint_direction_in_live_app():
    at = _start_app()
    secret = at.session_state["secret"]

    if secret < 100:
        _submit(at, "100")
        assert any("LOWER" in w.value for w in at.warning)
    else:
        _submit(at, "1")
        assert any("HIGHER" in w.value for w in at.warning)


# ---------------------------------------------------------------------------
# Challenge 1: advanced edge cases at the UI layer.
# ---------------------------------------------------------------------------

def test_edge_case_1_huge_float_does_not_crash_the_app():
    # Before the fix this raised OverflowError inside the script run and
    # Streamlit rendered a traceback instead of the game.
    at = _start_app()
    _submit(at, "1.0e999")
    assert not at.exception, [e.value for e in at.exception]
    assert any("not a number" in e.value for e in at.error)
    assert at.session_state["attempts"] == 0


def test_edge_case_3_difficulty_change_resets_secret_into_range():
    # Normal is 1-100, Hard is 1-50. Pin a Normal secret of 87, switch to Hard,
    # and confirm the secret is regenerated inside the new range. Before the
    # fix the secret stayed at 87 and the range check rejected the only
    # winning guess, so the round was unwinnable.
    at = _start_app()
    at.session_state["secret"] = 87
    at.run()

    at.sidebar.selectbox[0].set_value("Hard")
    at.run()

    assert 1 <= at.session_state["secret"] <= 50
    assert at.session_state["attempts"] == 0
    assert at.session_state["status"] == "playing"
    assert "between 1 and 50" in at.info[0].value

    # And the round is winnable: guessing the new secret wins.
    _submit(at, str(at.session_state["secret"]))
    assert at.session_state["status"] == "won"


def test_edge_case_3_difficulty_change_clears_stale_progress():
    at = _start_app()
    secret = at.session_state["secret"]
    _submit(at, "1" if secret != 1 else "2")
    assert at.session_state["attempts"] == 1
    assert at.session_state["score"] == -5

    at.sidebar.selectbox[0].set_value("Easy")
    at.run()

    assert at.session_state["attempts"] == 0
    assert at.session_state["score"] == 0
    assert at.session_state["history"] == []


def test_bug2_attempts_left_counts_down_from_limit_to_zero():
    # Normal has an 8-attempt limit. Before the fix attempts started at 1, so
    # the caption read 7 on load and the sequence ended at -1.
    at = _start_app()
    assert "Attempts left: 8" in at.info[0].value

    secret = at.session_state["secret"]
    wrong = "100" if secret != 100 else "1"
    for remaining in range(7, -1, -1):
        _submit(at, wrong)
        assert f"Attempts left: {remaining}" in at.info[0].value

    assert at.session_state["status"] == "lost"
    assert any("Out of attempts" in e.value for e in at.error)
