# 💭 Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

The game rendered correctly on first run (title, difficulty selector, guess input, three controls), but one full round exposed three bugs. First, both buttons stop responding after a win, which locks the game permanently. Second, the attempt display reaches `-1` by the 5th guess instead of stopping at 0. Third, the input accepts out-of-range values such as `1000000` and `-1`, even though the UI states the range is 1 to 100. Each bug traces to a specific defect in `app.py`, detailed below.

### Bug 1: Submit Guess and New Game buttons stop working after winning

- **Input / trigger:** Submit the correct guess to win, then click **New Game** or **Submit Guess**.
- **Expected:** New Game resets all game state and starts a fresh round. Submit Guess responds to the click.
- **Actual:** Neither button has any effect. Every click redisplays "You already won. Start a new game to play again." The player cannot continue without restarting the app process.
- **Code location:** `app.py`, New Game handler (lines 134–138) and status gate (lines 140–145). The handler resets `attempts` and `secret` but not `st.session_state.status`, which stays `"won"`. The gate calls `st.stop()` whenever `status != "playing"`, so every rerun halts before the `if submit:` block at line 147 executes. This makes both buttons dead. The handler also fails to reset `score` and `history`.

### Bug 2: Attempt display reaches -1 by the 5th guess

- **Input / trigger:** Submit 5 consecutive wrong guesses (Hard difficulty, 5-attempt limit).
- **Expected:** Attempts count up from 1 to 5, "Attempts left" counts down from 5 to 0, and the game ends at the limit.
- **Actual:** The display starts one attempt short on the first guess and reaches `-1` by the 5th. Hints also invert on alternating attempts: a guess of 60 against a secret of 7 returns "Go HIGHER!" on even-numbered attempts.
- **Code location:** Four defects in `app.py`:
  - Line 96: `st.session_state.attempts = 1` initializes the counter to 1 instead of 0, which offsets every count by one.
  - Line 148: `st.session_state.attempts += 1` runs before input validation, so blank or non-numeric input consumes an attempt.
  - Line 111: the display math `attempt_limit - st.session_state.attempts` inherits the off-by-one and renders `-1` once attempts exceed the limit.
  - Lines 158–162: the code converts the secret to a string on every even-numbered attempt (`secret = str(st.session_state.secret)`). This forces `check_guess` (lines 32–47) into its `TypeError` fallback, which compares strings lexicographically (`"60" > "7"` is False), producing inverted hints on exactly those attempts.

### Bug 3: No input range validation (accepts 1000000 and -1)

- **Input / trigger:** Enter `1000000` or `-1` in the guess box and click Submit Guess.
- **Expected:** The app rejects the value with "Enter a number between 1 and 100" and consumes no attempt, matching the stated 1 to 100 range.
- **Actual:** The app accepts the value, consumes an attempt, and returns a "Go LOWER!" or "Go HIGHER!" hint for a number outside the valid range.
- **Code location:** `app.py`, `parse_guess` (lines 14–29). The function checks only that the input is numeric (`int(raw)` or `int(float(raw))`) and never checks `low <= value <= high`. The submit handler (lines 147–163) also never compares the parsed guess against the `low, high` values returned by `get_range_for_difficulty` (lines 4–11). A contributing factor: `logic_utils.py` contains only `NotImplementedError` stubs, so no validation logic is centralized or unit-tested.

**Bug Reproduction Log**

Document at least 3 bugs you found. Add rows as needed.

| Input Used | Expected Behavior | Actual Behavior | Console Error / Output | Suspected Code Location |
|------------|-------------------|-----------------|------------------------|-------------------------|
| Winning guess, then click "New Game" or "Submit Guess" | New Game resets the round, Submit responds | Both buttons do nothing, app stays on "You already won. Start a new game to play again." | none (app halts silently via `st.stop()`) | `app.py` lines 134–138 (New Game handler, missing `status = "playing"` reset) and lines 140–145 (status gate) |
| 5 consecutive wrong guesses (Hard, 5-attempt limit) | Attempts count 1 to 5, "Attempts left" counts down to 0 | Count off by one from the first guess, display reaches `-1`, hints invert on even attempts | none | `app.py` line 96 (`attempts = 1` init), line 148 (increment before validation), line 111 (attempts-left math), lines 158–162 (`str(secret)` on even attempts) feeding `check_guess` fallback (lines 42–47) |
| Guess of `1000000` (also `-1`) | Error "Enter a number between 1 and 100", no attempt consumed | Guess accepted, attempt consumed, invalid "Go LOWER!" / "Go HIGHER!" hint shown | none | `app.py`, `parse_guess` (lines 14–29), no `low <= value <= high` check, and submit handler (lines 147–163) never validates against range |

---

## 2. How did you use AI as a teammate?

**Tools used.** I used Cursor's agent mode (Claude) for the whole repair. The workflow was: mark each crime scene in `app.py` with a `# FIXME` comment, point the agent at that marker with `app.py` and `logic_utils.py` attached, and review every diff before accepting. I committed the FIXME markers first (commit `af27d7b`) so the before state is preserved in git history.

**A suggestion that was correct.** For Bug 1, the agent identified that the New Game handler reset `attempts` and `secret` but never reset `st.session_state.status`, so the status gate at line 140 kept calling `st.stop()` before the submit handler ran. It proposed resetting all five state keys (`attempts`, `score`, `history`, `status`, `secret`) and drawing the new secret from `random.randint(low, high)` instead of the hardcoded `1, 100`. I verified this two ways. First, I ran a Streamlit `AppTest` script against the original `app.py` and confirmed the bug: after winning and clicking New Game, `status` stayed `"won"` and the "You already won" banner was still rendered. Second, I ran the same script against the fixed file and `status` returned to `"playing"`, `attempts` reset to 0, and a follow-up wrong guess produced a hint, proving the game was playable again.

**A suggestion I did not accept as written.** When the agent moved `update_score` into `logic_utils.py`, its first draft rewrote the scoring rules: it replaced `100 - 10 * (attempt_number + 1)` with `max(10, 100 - 10 * attempt_number)` and collapsed the `Too High` and `Too Low` branches into a single `-5` penalty. The simplified version was cleaner, and the original `+5 on even-numbered Too High` branch looks like a bug. I rejected it anyway because it was out of scope for the two bugs I was targeting, it silently changed the player's score, and it made the refactor diff harder to review since I was no longer able to confirm "moved, not modified" at a glance. I asked for the original body restored verbatim with a `# FIXME` comment marking the suspicious branch for a later pass. I verified the result by diffing the `update_score` body in `logic_utils.py` against the original in `git show af27d7b:app.py` and confirming the logic lines matched.

---

## 3. Debugging and testing your fixes

**How I decided a bug was fixed.** I required evidence at three layers before calling a fix done. Layer one is unit tests on the pure logic in `logic_utils.py`. Layer two is UI-level tests that drive the real `app.py` through Streamlit's `AppTest` harness and simulate the exact click sequence that reproduced the bug in the browser. Layer three is a before/after check: the same reproduction script run against the original `app.py` must fail, and run against the fixed `app.py` must pass. A test that passes on both versions proves nothing, so this third layer mattered most.

**Tests I ran.** `pytest tests/` now reports 23 passed in 1.07s: the 3 starter tests, 16 new unit tests in `tests/test_game_logic.py`, and 4 UI tests in `tests/test_app_ui.py`. The three starter tests failed with `NotImplementedError` before the refactor and pass now. The test that taught me the most was `test_bug3_out_of_range_guess_is_rejected_and_costs_no_attempt`. It submits `1000000`, `-1`, `0`, and `101` through the live app and asserts an error is shown, no hint is shown, and `attempts` does not change. On the original code the same inputs produced no error, rendered a "Go LOWER!" hint, and incremented `attempts` from 1 to 2, which confirmed the increment-before-validation ordering was part of the bug and not just the missing range check. A second useful test was `test_check_guess_integer_comparison_not_string`, which asserts `check_guess(60, 7) == "Too High"`. Lexicographically `"60" < "7"`, so this single pair catches any regression toward the string-comparison fallback the original code relied on.

**How AI helped with testing.** Two contributions were decisive. First, the agent pointed out that the starter tests assert `check_guess(60, 50) == "Too High"`, a plain string, while the `app.py` version returned a `(outcome, message)` tuple. That observation shaped the refactor: `check_guess` returns only the outcome string and the UI text moved to a new `hint_message` function. Second, I did not know Streamlit had a `streamlit.testing.v1.AppTest` harness. The agent suggested it as a way to verify the New Game fix without clicking through the browser, and it turned a manual "did the buttons work" check into a repeatable 1-second test. I still ran `streamlit run app.py` and confirmed the server returned HTTP 200 on `/` and `ok` on `/_stcore/health` with no tracebacks in the log.

---

## 4. What did you learn about Streamlit and state?

- How would you explain Streamlit "reruns" and session state to a friend who has never used Streamlit?

---

## 5. Looking ahead: your developer habits

- What is one habit or strategy from this project that you want to reuse in future labs or projects?
  - This could be a testing habit, a prompting strategy, or a way you used Git.
- What is one thing you would do differently next time you work with AI on a coding task?
- In one or two sentences, describe how this project changed the way you think about AI generated code.
