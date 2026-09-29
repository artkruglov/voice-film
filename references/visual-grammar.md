# Visual grammar

1. **One hero per frame**; everything else ≤ 40 % of its visual weight.
2. **Three type levels per frame at most** — `TYPE` in `tokens.ts` (display / headline / body / label). Minimums: 24 px on 16:9, 28 px on 9:16; captions 44 / 52.
3. **A number always comes with its unit and its source** in one block ("model", "measured 12.03", "illustration").
4. **One move at a time**: text lands, then the object, then the camera. Never all at once.
5. **Timing**: enter 0.3–0.45 s (ease-out), exit 0.2 s, hold ≥ 1.5 s after a landing. Something changes every 2–4 s, but nothing moves constantly.
6. **Match moves**: the hero object travels between scenes (same rect → new rect), it doesn't dissolve and reappear. Reuse its rect for the ending (echo).
7. **Screenshots** always in a frame (radius, 1 px ring, soft shadow), zoomed to the part that matters, ring on the target. Re-typeset small UI (buttons, cards) instead of shrinking a screenshot until it's unreadable.
8. **9:16 is its own layout**, not a squeezed 16:9: one column, stacked comparisons, zoom ≥ 2× into screenshots, the key object ≥ 55 % of the stage.
9. **Captions never duplicate scene text.** When a kinetic phrase is on screen, it *is* the caption: hide those captions (`<Captions hide={…}>`).
10. **Safe zones**: nothing important in the caption band; 5 % margins on 16:9, 8 % on 9:16, keep the top ~200 px of 9:16 free of key content (feed UI).
11. **Colour roles**: one accent for "the product / the result", one warm colour for "the problem / rejected", everything else neutral. Use the product's real palette and fonts.
12. **Real media first**: the product's own screenshots, generated outputs and clips (`OffthreadVideo` in a `Loop`) beat drawn illustrations. If something is illustrative, label it.
13. **Groups**: stagger ≤ 0.12 s per item, ≤ 0.5 s per group; 6+ items in a grid, never one by one.
14. **The last word of a line is static**: a landing finishes before the voice does.
15. **Review like a viewer**: stills of every scene in both formats → your own look → `review_frames.py` (it catches small text and dead space; ignore flags on mid-fade captions and intentional kinetic frames).
