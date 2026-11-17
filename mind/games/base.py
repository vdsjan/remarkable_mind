"""The contract every game module implements.

A game module lives in ``mind/games/<key>.py`` and exposes ``GAME``, an
instance of a :class:`Game` subclass. Puzzles are plain JSON-serialisable
dicts (so they can be cached), and always carry their own solution.
"""


class Game:
    key = ""                 # module name, e.g. "sudoku"
    name = ""                # Dutch display name
    category = ""            # "getallen" | "logica" | "ruimte" | "taal"
    tagline = ""             # one short sentence for the hub page
    rules = []               # 2-5 short Dutch sentences
    tips = []                # 1-3 short strategy tips
    counts = (9, 8, 8)       # number of puzzles per level (1, 2, 3)
    parts = 1                # pages per puzzle (2 for study -> question games)
    example = True           # show a small worked example on the hub page

    # -- puzzle logic ---------------------------------------------------------
    def generate(self, rng, level):
        """Return a new puzzle dict for level 1..3 using ``rng`` only."""
        raise NotImplementedError

    def verify(self, puz):
        """Raise AssertionError unless ``puz`` is valid: the stored solution
        obeys every rule and (where the game promises it) is the only one."""
        raise NotImplementedError

    def fingerprints(self, puz):
        """Keys that should not repeat within one book (a theme, a proverb, a
        picture). The book builder re-rolls a puzzle whose key was used."""
        return []

    # -- presentation ---------------------------------------------------------
    def instruction(self, puz, part=0):
        """Optional one-line task description shown above the puzzle."""
        return ""

    def draw(self, c, box, puz, solved=False, part=0):
        """Draw the puzzle inside box=(x, y, w, h). With ``solved`` the
        solution is drawn on top in the PEN colour."""
        raise NotImplementedError

    def icon(self, c, cx, cy, s, color):
        """Draw a pictogram of about s x s points centred on (cx, cy)."""
        from ..draw import text_mid
        text_mid(c, cx, cy, self.name[:1], "SerifX", s * 0.9, color)
