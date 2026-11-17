"""Game registry. Order here is the order on the home screen."""
import importlib

ORDER = [
    # getallen
    "sudoku", "calcudoku", "piramide", "reeksen",
    # logica
    "binairo", "wolkenkrabbers", "logigram", "bruggen",
    # ruimte
    "doolhof", "nonogram", "kleurlink", "lucifers",
    # taal & geheugen
    "woordzoeker", "codekraker", "letterchaos", "geheugen",
]


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
