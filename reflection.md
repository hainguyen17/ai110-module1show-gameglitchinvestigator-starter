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

- Which AI tools did you use on this project (for example: ChatGPT, Gemini, Copilot)?
- Give one example of an AI suggestion that was correct (including what the AI suggested and how you verified the result).
- Give one example of an AI suggestion you did not accept as written (including what the AI suggested, why you rejected or changed it, and how you verified your version). It does not have to be a suggestion that was wrong: over-engineered, out of scope, harder to read, or a poor fit for this codebase all count.

---

## 3. Debugging and testing your fixes

- How did you decide whether a bug was really fixed?
- Describe at least one test you ran (manual or using pytest)  
  and what it showed you about your code.
- Did AI help you design or understand any tests? How?

---

## 4. What did you learn about Streamlit and state?

- How would you explain Streamlit "reruns" and session state to a friend who has never used Streamlit?

---

## 5. Looking ahead: your developer habits

- What is one habit or strategy from this project that you want to reuse in future labs or projects?
  - This could be a testing habit, a prompting strategy, or a way you used Git.
- What is one thing you would do differently next time you work with AI on a coding task?
- In one or two sentences, describe how this project changed the way you think about AI generated code.
