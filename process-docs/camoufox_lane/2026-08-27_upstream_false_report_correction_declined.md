# Upstream false-report correction: drafted, declined, thread closed (2026-08-27)

Continues the `camoufox_lane` area. The 2026-08-26 AXMain entry named three follow-ups; two of
them (the multi-URL live check, the watchdog and instrument removal) were executed and are
recorded in this area's two other 2026-08-27 entries. This entry closes the third follow-up — the
correction of the upstream report `daijro/camoufox#739` — without executing it, so no future
reader re-opens it as pending work.

## The decision

The upstream report describes a window-creation-time key-window steal residual. On this project's
evidence (five human-judged single-URL runs plus a 5-URL sustained-load sequence, 0/81 frontmost
deviations, zero perceived focus loss, no watchdog in the code), that report is a false positive:
the AXMain signal it rests on does not indicate activation for an LSUIElement accessory process.
A correction comment was drafted and presented on 2026-08-27; the decision was to NOT post it.
The thread is thereby closed as "will not do", not deferred.

## The drafted correction, preserved verbatim

Kept here so the work is not lost if the decision is ever revisited:

> Follow-up: this report turned out to be a false positive — closing-worthy, with apologies for
> the noise.
>
> The "window-creation-time key-window steal" I reported was inferred from polling `AXMain of
> front window` on the Camoufox process via macOS System Events. Further live verification showed
> that signal does not mean what I assumed: with `LSUIElement=true` set on the bundle and
> `-foreground` dropped via `ignoreDefaultArgs`, Camoufox runs as an accessory app that is never
> activated — but its own front window can still legitimately report `AXMain=true` (it is that
> app's main window, which carries no consequence for the user's focus).
>
> Verification: multiple live runs with a human typing in another app throughout — including a
> sustained sequence of 5 real URLs, one fresh Camoufox launch each (~50s total) — showed zero
> perceived focus loss and zero frontmost-app deviations (0/81 samples), while the AXMain poll
> "fired" on 72/81 samples. Reading Gecko's `nsCocoaWindow.mm` confirms `makeKeyAndOrderFront`
> fires at window show, but for an LSUIElement process this never translates into stealing the
> user's focus.
>
> Conclusion: `LSUIElement=true` + `ignoreDefaultArgs: ['-foreground']` fully solves background
> operation on macOS; there is no residual steal. Feel free to close.
