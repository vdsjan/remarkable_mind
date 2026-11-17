# Remarkable Mind

**Hersengym op papier** — 16 hersenspellen, 400 puzzels en een trainingsplan van 30 dagen, volledig offline op de reMarkable Paper Pro.

![Cover, startscherm en een puzzel](docs/screens.jpg)

| | |
|---|---|
| **De app** | [`dist/RemarkableMind.pdf`](dist/RemarkableMind.pdf) — zet dit bestand op je reMarkable |
| **De promofilm** | [`promo/RemarkableMind-promo.mp4`](promo/RemarkableMind-promo.mp4) — 66 seconden, Nederlands gesproken |

## Wat is het?

De reMarkable heeft geen app-store. Remarkable Mind is daarom gebouwd als één
interactieve PDF: elke knop is een link, je navigeert door te tikken en je lost
op met je pen. Dat werkt op een standaard toestel, zonder developer mode,
zonder account en zonder netwerk.

- **16 spellen in 4 denkspieren**
  - *Getallen*: Sudoku, Calcudoku, Rekenpiramide, Getallenreeksen
  - *Logica*: Binairo, Wolkenkrabbers, Logigram, Bruggen
  - *Ruimte*: Doolhof, Japanse puzzel, Kleurlink, Lucifers
  - *Taal & Geheugen*: Woordzoeker, Codekraker, Letterchaos, Geheugentraining
- **400 puzzels** in drie niveaus (Opwarmen, Pittig, Meesterlijk), 25 per spel.
- **Eén oplossing, nooit gokken**: elke logische puzzel is door een solver
  nagerekend op precies één oplossing.
- **30 dagen hersengym**: elke dag vier puzzels, één per denkspier, met
  oplopende moeilijkheid en afvinkvakjes.
- **Gemaakt voor kleuren-e-ink**: pagina's op exact schermformaat (3:4),
  vette steunkleuren, vectorlijnen, grote tik- en schrijfvlakken.
- **Oplossingen achteraan**, bereikbaar via de knop *Oplossing* op elke puzzel,
  in blauw "handschrift".

## Op je reMarkable zetten

1. Download [`dist/RemarkableMind.pdf`](dist/RemarkableMind.pdf).
2. Sleep het bestand in de reMarkable-app (desktop of mobiel), of zet het
   over via USB (in *Settings → Storage* de *USB web interface* aanzetten en
   in je browser naar `http://10.11.99.1` gaan).
3. Open het boek, verberg de werkbalk en tik op *Tik om te starten*.

Tips: tik met je vinger op knoppen, schrijf met de pen. Je inkt staat los van
het boek, dus wissen of een nieuwe laag gebruiken maakt een puzzel weer leeg.

## Zelf een nieuwe editie bouwen

Elke editie is een compleet nieuw boek met 400 andere puzzels.

```bash
pip install -r requirements.txt
```

```bash
python -m mind.book --seed 2027 --out dist/RemarkableMind-2027.pdf
```

```bash
python -m pytest -q
```

Eén spel bekijken op schermresolutie (1620 × 2160):

```bash
python -m mind.preview sudoku --out build/preview
```

## Hoe het in elkaar zit

```
mind/
  theme.py        formaat, kleuren, lettertypes
  draw.py         tekenhulpen (rooster, knoppen, pictogrammen)
  pages.py        navigatiebalk, puzzel- en oplossingspagina
  book.py         cover, startscherm, hubs, dagplan, scorebord + PDF-opbouw
  games/          één module per spel: generate(), verify(), draw(), icon()
  assets/         e-ink-versies van de illustraties
  fonts/          Fraunces, Inter, Caveat (SIL OFL)
tests/            per spel: geldig, uniek, deterministisch; plus de navigatie
promo/            artwork, clips, voice-over, muziek en make_film.py
tools/            prepare_assets.py
```

Een nieuw spel toevoegen is één bestand in `mind/games/` dat de klasse `Game`
uit `mind/games/base.py` invult, plus de sleutel in `ORDER` in
`mind/games/__init__.py`.

## De promofilm

`promo/make_film.py` monteert de film volledig uit code:

- vier geanimeerde scènes en al het artwork zijn gegenereerd met ElevenLabs
  (beeld → video), in één risografie-stijl met vier inkten;
- de voice-over (Vlaamse stem) en de muziek komen van ElevenLabs;
- alle schermen in de film zijn echte pagina's uit de PDF.

```bash
python promo/make_film.py
```

## Credits

- Illustraties, videoclips, stem en muziek: gegenereerd met ElevenLabs.
- Lettertypes: Fraunces, Inter en Caveat (SIL Open Font License, zie `mind/fonts/`).
- PDF: ReportLab en PyMuPDF.

reMarkable is een merk van reMarkable AS. Dit is een onafhankelijk project,
niet verbonden met of goedgekeurd door reMarkable AS.
