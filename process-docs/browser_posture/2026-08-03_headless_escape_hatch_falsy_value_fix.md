# WEBSEARCH_HEADLESS falsy-value defect, caught in review (2026-08-03)

Follow-up correction to the Milestone 3 rebuild (`2026-08-03_browser_py_headed_default_rebuild.md`,
same area), caught in review of the merged commit rather than during the milestone itself.

## The defect

`build_options()` read the new escape hatch as `bool(os.environ.get("WEBSEARCH_HEADLESS"))`. Every
non-empty string is truthy in Python, so `WEBSEARCH_HEADLESS=0` and `WEBSEARCH_HEADLESS=false` both
forced headless — the opposite of what someone writing either value would mean. The old
`WEBSEARCH_HEADED` var had the identical shape and it never mattered: it was a pure opt-in whose only
sane use was setting it to anything at all, so there was no "off" spelling to get wrong. Making headed
the default and the env var a documented two-way switch changed that — a wrong value now silently
selects the wrong mode with no error, which is exactly the class of defect this whole area has been
finding and removing (documented/assumed behavior silently diverging from what actually happens).

## The fix

`_FALSY_ENV_VALUES = {"", "0", "false", "no", "off"}` (case-insensitive, stripped), `options.headless
= os.environ.get("WEBSEARCH_HEADLESS", "").strip().lower() not in _FALSY_ENV_VALUES`. Verified against
12 cases (unset, `""`, `"0"`, `"false"`, `"FALSE"`, `"no"`, `"off"`, whitespace-only → headed;
`"1"`, `"true"`, `"yes"`, an arbitrary non-empty string → headless) — all resolved correctly.

## The second defect: the template shipped the value active

`.env.example`'s new line read `WEBSEARCH_HEADLESS=1`, uncommented — unlike the file's other two
entries (a path, an email placeholder), this was a live, working value meaning "force headless."
Nothing loads `.env` in this project today, so it was inert, but the file is the template a user
copies; the day `.env`-loading is ever added, every copy of the template would default to headless —
the exact opposite of what this milestone established as the default. Fixed by commenting out the
assignment (`# WEBSEARCH_HEADLESS=1`), letting the surrounding two lines of prose carry the meaning
instead of an active value.

## Test suite re-check

9 failed, 83 passed, 2 collection errors — unchanged from both the pre-Milestone-3 baseline and the
post-rebuild run recorded in the Milestone 3 entry. Neither fix altered the failure set.
