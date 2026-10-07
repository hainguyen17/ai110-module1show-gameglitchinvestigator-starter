# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF8)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

<!-- Describe the goal you asked the agent to accomplish -->

**What did the agent do?**

<!-- List the steps the agent took (files edited, commands run, etc.) -->

**What did you have to verify or fix manually?**

<!-- Describe anything the agent got wrong or that required human review -->

---

## Test Generation (SF7)

> Document how you used AI to help generate or improve tests.

**Approach.** After the Phase 2 fixes were in and 23 tests passed, I asked the agent to attack the repaired game instead of confirming it worked. The first prompt asked for hostile inputs, the second asked it to probe them against the real `parse_guess` before writing any tests, and the third asked for a state-level edge case that was not a text input at all. Each row below records the exact probe result, whether the generated test passed on the first run, and why the case earned a test.

**Prompt 1 (discovery):**

```
Challenge 1: find three edge-case inputs that STILL break the game after
the Phase 2 fixes. Think negative numbers, decimals, extremely large values,
and anything float() or int() accepts that a player does not expect. Before
writing tests, run each candidate through parse_guess(raw, 1, 100) and show me
the actual return value or exception.
```

**Prompt 2 (state, not text):**

```
Those are all text inputs. Is there a non-text action in the UI that leaves the
game in an inconsistent state? Use AppTest to probe it against the real app.py.
```

**Prompt 3 (tests):**

```
Write pytest cases for each confirmed break. Unit tests in
tests/test_game_logic.py for parse_guess, AppTest cases in tests/test_app_ui.py
for anything that needs session state. Each test must fail on the current code
and pass after the fix. Replace, do not keep, any existing test that now
asserts the old behavior.
```

| Edge Case | Prompt Used | AI-Suggested Test | Did It Pass? | Your Reasoning |
|-----------|-------------|-------------------|--------------|----------------|
| `1.0e999` (float overflow to infinity) | Prompt 1 | `test_edge_case_1_huge_float_does_not_crash` (parametrized over `1.0e999`, `1.5e400`, `-1.0e999`) and `test_edge_case_1_huge_float_does_not_crash_the_app` (UI) | Failed first with `OverflowError: cannot convert float infinity to integer`. Passed after adding `OverflowError` to the except clause and a `math.isfinite` guard. | Chosen because `except (ValueError, TypeError)` looked complete but was not. `float("1.0e999")` returns `inf` without raising, then `int(inf)` raises a third exception type. A single typed character crashed the whole app with a traceback. |
| `nan`, `inf`, `infinity` (non-finite words) | Prompt 1 follow-up | `test_edge_case_1_non_finite_words_are_rejected` | Passed first run. `int("inf")` already raised `ValueError` because there is no `.` in the string. | Chosen as a companion to the overflow case. `float()` accepts these spellings, so if the parser ever routes them through `float()` first, they need an explicit guard. The test locks that in. |
| `42.9` and `100.7` (fractional truncation) | Prompt 1 | `test_edge_case_2_fractional_input_is_rejected` (parametrized) and `test_edge_case_2_truncation_cannot_bypass_range_check` | Failed first: `parse_guess("100.7")` returned `(True, 100, None)`. Passed after adding `is_integer()` check with the message "Enter a whole number." | Chosen because `100.7 > 100` yet it passed the range check. Truncation ran before validation, so the Bug 3 fix had a bypass. I also decided a whole-number game has no business guessing what `42.9` means. This replaced my own earlier `test_parse_guess_truncates_decimal_input`, which had asserted the buggy behavior as if it were intended. |
| Difficulty switch mid-game (Normal secret 87, then Hard range 1 to 50) | Prompt 2 | `test_edge_case_3_difficulty_change_resets_secret_into_range` and `test_edge_case_3_difficulty_change_clears_stale_progress` | Failed first: secret stayed 87 and the guess `87` returned "Enter a number between 1 and 50." Passed after adding a `start_new_round()` call whenever `session_state.difficulty` differs from the selectbox. | Chosen because it is a state edge case, not a text one, and because my Bug 3 fix made it worse: the range check now rejected the only winning answer. The round was unwinnable with no error. This is the case I am most glad was caught. |
| "Attempts left" lagging one guess behind | Found by Prompt 3, not planned | `test_bug2_attempts_left_counts_down_from_limit_to_zero` | Failed first: expected "Attempts left: 7" after one wrong guess, saw 8. Passed after moving the banner into an `st.empty()` placeholder filled after the submit handler. | Not an input at all. The test was written to verify the Bug 2 fix (attempts start at 0) and exposed a second defect: `st.info` rendered at the top of the script before `attempts` was incremented, so the number on screen was always stale. A good example of a test finding more than it was written for. |
| `+50`, `1_0`, full-width `４２`, 5000-digit string | Prompt 1 | `test_parse_guess_tolerates_unusual_but_valid_integers` and `test_parse_guess_rejects_extremely_long_digit_string` | Passed first run. | Chosen to document current behavior instead of changing it. Python's `int()` accepts underscores and Unicode digits, and caps string parsing at 4300 digits. None of these break the game today. A future parser change is the risk, and the tests make any behavior shift visible. |

**What I changed from the first draft.** Two things. First, the agent's initial NaN and infinity guard was written as `if as_float != as_float or as_float in (float("inf"), float("-inf"))`, which is correct but unreadable. I had it replaced with `math.isfinite(as_float)`, which says the same thing in one call. Second, the agent's first fix for the difficulty switch added a reset block directly under the existing `if "secret" not in st.session_state` init, leaving two competing initialization paths and a now-dead `attempts = 1` line. I asked for a single `start_new_round()` helper called from both the difficulty check and the New Game button, which also became the natural place to fix Bug 2 instead of letting it get fixed by accident.

**Result.** 44 passed, up from 23. The four new defects were all in code that had already been "fixed" and had passing tests. Every Challenge 1 test was confirmed to fail on the pre-fix code before the fix was applied.

---

## Linting & Style (SF9)

> Document your use of AI for linting or code style improvements.

**Prompt used:**

```
<!-- Paste the prompt you gave the AI -->
```

**Linting output before:**

```
<!-- Paste relevant linter warnings/errors -->
```

**Changes applied:**

<!-- Describe what you changed based on the AI's suggestions -->

---

## Model Comparison (SF11)

> Compare two AI models on the same task.

**Task given to both models:**

<!-- Describe what you asked each model to do -->

| | Model A | Model B |
|-|---------|---------|
| **Model name** | | |
| **Response summary** | | |
| **More Pythonic?** | | |
| **Clearer explanation?** | | |

**Which did you prefer and why?**

<!-- Your conclusion -->
