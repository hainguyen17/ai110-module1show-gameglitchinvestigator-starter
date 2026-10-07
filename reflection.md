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

**Challenge 1 addendum.** With 23 tests green, I asked the agent to break the repaired game instead of confirming it. Probing `parse_guess` with 15 hostile strings found two real defects in code I had already "fixed": `1.0e999` crashed the app with `OverflowError` because `float()` returns infinity without raising, and `100.7` truncated to 100 and slipped past the range check. An `AppTest` probe found a third that was not a text input at all: switching difficulty from Normal to Hard kept a secret of 87 in a 1 to 50 range, and my own Bug 3 validation then rejected the only winning guess. Writing the test for the Bug 2 fix exposed a fourth, the "Attempts left" banner rendering before the counter updated. All four are fixed and the suite is now 44 tests. The lesson I took is that a passing suite measures the questions I thought to ask, and the fastest way to find the questions I missed was to hand the AI the fixed code and ask it to attack it. Prompts and per-case reasoning are in `ai_interactions.md`.

---

## 4. What did you learn about Streamlit and state?

Here is how I explain it to a friend. A Streamlit app is not a program that starts once and then waits for clicks. Every time you touch anything on the page, Streamlit throws away the whole script and runs it again from line 1 to the bottom. That is a rerun. Every normal Python variable is reborn on each rerun, so if you write `secret = random.randint(1, 100)` at the top of the file, you get a brand new secret on every click, which is exactly why the original README says the secret "has commitment issues." `st.session_state` is the one dictionary that survives reruns. Anything you store there on one run is still there on the next, so the secret, the attempt count, and the score all have to live in it.

The part that bit this project is that session state only persists what you tell it to. The New Game handler stored `attempts` and `secret` but forgot `status`, so `status` stayed `"won"` across every rerun and the `st.stop()` gate kept firing. The rerun model also explains why that gate made both buttons look dead: `st.stop()` ends the script early, so the `if submit:` block lower in the file never executed. Once I understood that the file is a top-to-bottom script that runs on every click, the fix was obvious, and writing `tests/test_app_ui.py` with `AppTest` made the model concrete because each `.run()` call is literally one rerun.

---

## 5. Looking ahead: your developer habits

**Habit to reuse.** Prove the bug before proving the fix. For both bugs I fixed, I ran the reproduction against the original `app.py` first (via `git show af27d7b:app.py`) and recorded the failure: `status` stayed `"won"` after New Game, and a guess of `1000000` incremented `attempts` from 1 to 2 with no error. Only then did I run the same script against the fixed file. A test that passes on both versions proves nothing, and this before-and-after habit caught that the attempt counter ordering was part of bug 3, a detail that a range-check-only fix misses. I also want to keep the two-commit pattern: one commit with `# FIXME` markers and the written bug report, one commit with the fix, so the diff for the fix stays small and reviewable.

**What I will do differently.** Next time I will give the AI a tighter scope before it writes any code. When I asked the agent to move `update_score` into `logic_utils.py`, I said "move the logic" and it took that as permission to rewrite the scoring formula. The result was cleaner but changed player scores and was out of scope for the two bugs I was fixing. I caught it in the diff and had it restored verbatim with a `# FIXME` instead, but a one-line instruction up front ("move as-is, do not change behavior, flag anything suspicious in a comment") saves that round trip. I will also start one chat per bug as the assignment suggested instead of fixing both in a single session, because by the end the shared refactor made it harder to attribute each change to one bug.

**How this changed my view of AI-generated code.** The starter code looked finished: it had docstrings, a settings sidebar, a debug panel, and a caption claiming it was production-ready, and it had 3 state bugs and a backwards hint message. I now read AI-generated code as a first draft from a confident collaborator who has not run it, and I treat "does the test fail on the old version and pass on the new one" as the minimum bar for calling anything fixed.
