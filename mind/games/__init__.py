"""Game registry. Order here is the order on the home screen."""
import importlib

ORDER = [
    # getallen
    "sudoku", "calcudoku", "piramide", "reeksen", "lucifers", "dominodetective",
    # logica
    "binairo", "wolkenkrabbers", "logigram", "bruggen", "lichtplan", "eilandenrijk",
    # ruimte
    "doolhof", "nonogram", "kleurlink", "spiegelkamer", "sterrenstelsels", "vouwcode",
    # taal & geheugen
    "woordzoeker", "codekraker", "letterchaos", "geheugen", "woordladder", "plaatsdelict",
]
# Added in version 2; the website marks these as new.
NEW = {"dominodetective", "lichtplan", "eilandenrijk", "spiegelkamer",
       "sterrenstelsels", "vouwcode", "woordladder", "plaatsdelict"}


def get(key):
    return importlib.import_module(f"{__name__}.{key}").GAME


def all_games(strict=True):
    games = []
    for key in ORDER:
        try:
            games.append(get(key))
        except Exception:           # a missing/broken game only passes in dev builds
            if strict:
                raise
    return games
