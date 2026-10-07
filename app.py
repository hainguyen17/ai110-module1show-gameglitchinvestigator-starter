import random
import streamlit as st

# FIX: Refactored game logic into logic_utils.py using Cursor agent mode so
# app.py only handles UI and session state. Reviewed the full diff of both
# files before accepting; the only behavior changes are the ones marked FIX.
from logic_utils import (
    check_guess,
    get_range_for_difficulty,
    hint_message,
    parse_guess,
    update_score,
)

st.set_page_config(page_title="Glitchy Guesser", page_icon="🎮")

st.title("🎮 Game Glitch Investigator")
st.caption("An AI-generated guessing game. Something is off.")

st.sidebar.header("Settings")

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Normal", "Hard"],
    index=1,
)

attempt_limit_map = {
    "Easy": 6,
    "Normal": 8,
    "Hard": 5,
}
attempt_limit = attempt_limit_map[difficulty]

low, high = get_range_for_difficulty(difficulty)

st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")


def start_new_round():
    """Reset every piece of game state for the current difficulty."""
    st.session_state.difficulty = difficulty
    st.session_state.secret = random.randint(low, high)
    st.session_state.attempts = 0
    st.session_state.score = 0
    st.session_state.history = []
    st.session_state.status = "playing"


# FIX (Challenge 1, edge case 3): Changing difficulty mid-game used to leave
# the old secret in place. Going from Normal (secret 87) to Hard (range 1-50)
# made the game unwinnable, and the Bug 3 range check then rejected the correct
# answer. The game now resets whenever the difficulty changes. Found by an
# AppTest probe, verified by test_difficulty_change_resets_secret_into_range.
#
# This also runs on the first load (no "difficulty" key yet), so it is the
# single place all game state is initialized.
#
# FIX (Bug 2): The old init set attempts = 1, which made "Attempts left" read
# one short from the first guess and reach -1. attempts now starts at 0 in
# start_new_round(), and the separate per-key init blocks were removed.
if st.session_state.get("difficulty") != difficulty:
    start_new_round()

st.subheader("Make a guess")

# FIX (Challenge 1, edge case 4): This banner used to be rendered here, before
# the submit handler ran, so "Attempts left" always lagged one guess behind the
# real counter. Found by test_bug2_attempts_left_counts_down_from_limit_to_zero,
# which expected 7 after the first wrong guess and saw 8. The slot is reserved
# here with st.empty() and filled by render_attempts_banner() after state is
# final, in both the normal path and the early-exit path.
attempts_banner = st.empty()


def render_attempts_banner():
    attempts_banner.info(
        f"Guess a number between {low} and {high}. "
        f"Attempts left: {attempt_limit - st.session_state.attempts}"
    )


with st.expander("Developer Debug Info"):
    st.write("Secret:", st.session_state.secret)
    st.write("Attempts:", st.session_state.attempts)
    st.write("Score:", st.session_state.score)
    st.write("Difficulty:", difficulty)
    st.write("History:", st.session_state.history)

raw_guess = st.text_input(
    "Enter your guess:",
    key=f"guess_input_{difficulty}"
)

col1, col2, col3 = st.columns(3)
with col1:
    submit = st.button("Submit Guess 🚀")
with col2:
    new_game = st.button("New Game 🔁")
with col3:
    show_hint = st.checkbox("Show hint", value=True)

if new_game:
    # FIX (Bug 1): The original reset attempts and secret but never reset
    # status, so the gate below kept calling st.stop() and both buttons looked
    # dead after a win. start_new_round() resets every piece of game state and
    # draws the secret from the current difficulty range instead of 1-100.
    # Suggested by Cursor chat after I pointed it at the FIXME marker; verified
    # by winning a round and confirming New Game starts a fresh playable round.
    start_new_round()
    st.success("New game started.")
    st.rerun()

if st.session_state.status != "playing":
    render_attempts_banner()
    if st.session_state.status == "won":
        st.success("You already won. Start a new game to play again.")
    else:
        st.error("Game over. Start a new game to try again.")
    st.stop()

if submit:
    # FIX (Bug 3): parse_guess now receives the difficulty range and rejects
    # anything outside it. The attempt counter is incremented only after the
    # guess passes validation, so typing 1000000, -1, or "abc" no longer burns
    # an attempt. Verified in the live app and with test_parse_guess_* in
    # tests/test_game_logic.py.
    ok, guess_int, err = parse_guess(raw_guess, low, high)

    if not ok:
        st.error(err)
    else:
        st.session_state.attempts += 1
        st.session_state.history.append(guess_int)

        # FIX: Removed the original "convert secret to a string on even
        # attempts" block. It forced check_guess into a lexicographic string
        # comparison and inverted the hint on every other guess. check_guess
        # now always compares integers.
        outcome = check_guess(guess_int, st.session_state.secret)

        if show_hint:
            st.warning(hint_message(outcome))

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts,
        )

        if outcome == "Win":
            st.balloons()
            st.session_state.status = "won"
            st.success(
                f"You won! The secret was {st.session_state.secret}. "
                f"Final score: {st.session_state.score}"
            )
        else:
            if st.session_state.attempts >= attempt_limit:
                st.session_state.status = "lost"
                st.error(
                    f"Out of attempts! "
                    f"The secret was {st.session_state.secret}. "
                    f"Score: {st.session_state.score}"
                )

render_attempts_banner()

st.divider()
st.caption("Built by an AI that claims this code is production-ready.")
