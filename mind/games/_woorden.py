"""Dutch word material shared by the language games.

Everything is plain A-Z (the IJ is written as I + J) so words can be put in
letter grids. ``THEMES`` feeds Woordzoeker and Letterchaos, ``BONUS`` holds
the bonus words of Letterchaos, ``SPREEKWOORDEN`` feeds Codekraker and the
lists at the bottom feed Geheugentraining.
"""

# (title, words, hidden solution phrases for the word search)
THEMES = [
    ("Op de fiets",
     "ZADEL STUUR PEDAAL KETTING VELG SPAAK HELM POMP SLOT NAAF VORK BIDON "
     "FRAME TRAPPER VENTIEL ROTONDE HELLING PELOTON ZIJWIND FIETSBEL FIETSPAD "
     "SPATBORD TANDWIEL REMKABEL VOUWFIETS REFLECTOR STANDAARD TEGENWIND "
     "KNOOPPUNT BINNENBAND WIELRENNER FIETSROUTE VERSNELLING BAGAGEDRAGER",
     ["TRAP ZE", "LEKKE BAND", "WIND IN DE RUG", "ALTIJD WIND TEGEN",
      "EEN FRISSE NEUS HALEN", "MET DE FIETS BEN JE ER ZO",
      "WIE FIETST ZIET MEER VAN DE WERELD",
      "OP DE FIETS BEGINT DE DAG MET EEN FRISSE NEUS",
      "TRAPPEN MAAR", "BERGOP TRAPPEN EN BERGAF GENIETEN"]),
    ("Volleybal",
     "BLOK PASS TEAM PUNT LIJN VELD ZAAL SMASH FLUIT SCORE RALLY TOETS COACH "
     "OPSLAG AANVAL SPELER LIBERO SETBAL DUIKEN SPRONG WISSEL TRAINER ANTENNE "
     "NETFOUT ZIJLIJN ROTATIE KAPITEIN TRAINING VOETFOUT SPORTHAL KAMPIOEN "
     "WEDSTRIJD OPWARMING MATCHPUNT ACHTERLIJN COMPETITIE ONDERHANDS "
     "BOVENHANDS VERDEDIGING BEACHVOLLEY TEGENSTANDER SPELVERDELER",
     ["DRIE KEER RAKEN", "BAL OVER HET NET", "SAMEN STERK AAN HET NET",
      "HOOG SPRINGEN EN HARD SLAAN", "WINNEN DOE JE ALS TEAM",
      "DE BAL MAG DE GROND NIET RAKEN", "EEN GOEDE PASS IS HET HALVE PUNT",
      "ZES SPELERS EEN BAL EN EEN NET VOL SPANNING", "SETWINST",
      "PUNT VOOR ONS"]),
    ("Aan zee",
     "ZAND ZOUT BOOT PIER DIJK KRAB KWAL MEEUW HAVEN VLOED ANKER STRAND "
     "DUINEN GOLVEN SCHELP MOSSEL OESTER REDDER BADPAK GARNAAL ZEEHOND "
     "HORIZON PARASOL ZEEWIER ZEESTER VLIEGER BRANDING GETIJDEN ZEELUCHT "
     "KUSTTRAM HANDDOEK VUURTOREN SURFPLANK ZWEMBROEK WINDSCHERM GOLFBREKER "
     "ZONNEBRAND VISSERSBOOT STRANDSTOEL ZANDKASTEEL STRANDCABINE",
     ["EB EN VLOED", "ZILTE LUCHT", "UITWAAIEN", "ZAND TUSSEN JE TENEN",
      "EEN FRISSE NEUS AAN ZEE", "GARNAALKROKETTEN OP DE DIJK",
      "DE ZEE GEEFT EN DE ZEE NEEMT", "EEN DAGJE OOSTENDE", "WAFELS",
      "MET JE VOETEN IN HET WATER EN JE HOOFD IN DE WIND"]),
    ("In de keuken",
     "VORK BORD GLAS OVEN ZEEF RASP DEEG SAUS SOEP LEPEL BOTER PEPER GARDE "
     "MIXER SCHAAL DEKSEL SCHORT RECEPT SPATEL FORNUIS VERGIET BLENDER "
     "BAKVORM DAMPKAP KOELKAST POLLEPEL KOOKBOEK BROODMES THEEDOEK AANRECHT "
     "OVENWANT STEELPAN FRITEUSE KOEKENPAN SNIJPLANK KEUKENROL MAATBEKER "
     "KOOKPLAAT BAKPAPIER WEEGSCHAAL WATERKOKER VAATWASSER PEPERMOLEN "
     "SCHUIMSPAAN DUNSCHILLER BROODROOSTER KNOFLOOKPERS",
     ["SMAKELIJK", "AAN TAFEL", "EET SMAKELIJK", "ROEREN",
      "LIEFDE GAAT DOOR DE MAAG", "HONGER IS DE BESTE SAUS",
      "VEEL KOKS BEDERVEN DE BRIJ", "DE CHEF PROEFT ALTIJD EERST",
      "WIE KOOKT HOEFT NIET AF TE WASSEN",
      "MET VERSE KRUIDEN SMAAKT ALLES BETER",
      "EEN SNUFJE ZOUT EN EEN FLINKE SCHEUT GEDULD"]),
    ("Op reis",
     "TENT GIDS KAART HOTEL TREIN VISUM GRENS ROUTE FJORD KOFFER TICKET "
     "VLUCHT CAMPER RUGZAK DOUANE SAFARI EILAND MUSEUM KOMPAS BAGAGE TOLWEG "
     "TERRAS CAMPING UITSTAP BERGPAS PASPOORT SOUVENIR UITZICHT VAKANTIE "
     "AVONTUUR REISGIDS VEERBOOT RONDREIS SLAAPZAK WANDELING ZONNEBRIL "
     "INCHECKEN BOOTTOCHT LUCHTHAVEN WEGENKAART BESTEMMING VERTREKHAL "
     "REISVERHAAL ANSICHTKAART",
     ["GOEDE REIS", "OP AVONTUUR", "ONDERWEG", "DE WIJDE WERELD IN",
      "KOFFERS PAKKEN EN WEG", "OOST WEST THUIS BEST",
      "MET DE CAMPER NAAR HET NOORDEN",
      "REIZEN IS THUISKOMEN MET VERHALEN",
      "WIE VERRE REIZEN DOET KAN VEEL VERHALEN",
      "DE REIS IS BELANGRIJKER DAN DE BESTEMMING"]),
    ("Fotografie",
     "LENS ZOOM FILM FOTO FLITS FOCUS PIXEL KADER ALBUM MACRO LICHT KLEUR "
     "BEELD DRONE CAMERA FILTER SENSOR ZOEKER AFDRUK KORREL OPNAME MOMENT "
     "STATIEF SLUITER PORTRET SCHADUW SPIEGEL SCHERPTE CONTRAST TELELENS "
     "BATTERIJ ZONNEKAP UITSNEDE FOTOBOEK PANORAMA BEWEGING DIAFRAGMA "
     "LANDSCHAP OBJECTIEF GROOTHOEK STILLEVEN FOTOGRAAF VOORGROND BELICHTING "
     "TEGENLICHT COMPOSITIE LICHTMETER FLITSLICHT ONTSPANKNOP NACHTOPNAME "
     "ACHTERGROND PERSPECTIEF",
     ["EVEN LACHEN", "HET JUISTE MOMENT", "LICHT IS ALLES", "SCHERP",
      "KIJKEN IS EEN KUNST", "HET GOUDEN UUR", "EERST KIJKEN DAN KLIKKEN",
      "VASTGELEGD VOOR ALTIJD", "DE BESTE CAMERA IS DIE DIE JE BIJ HEBT",
      "EEN BEELD ZEGT MEER DAN DUIZEND WOORDEN"]),
    ("Het weer",
     "WIND MIST WOLK DOOI DAUW RIJP REGEN STORM HAGEL VORST HITTE IJZEL "
     "NEVEL HEMEL VOCHT GRAAD ZWOEL SNEEUW DONDER ONWEER ORKAAN BLIKSEM "
     "BEWOLKT DROOGTE KLIMAAT WEERMAN PARAPLU MOTREGEN WINDSTIL STORTBUI "
     "NEERSLAG GLADHEID WINDHOOS REGENBOOG LUCHTDRUK BAROMETER WOLKENDEK "
     "SNEEUWBUI HITTEGOLF OPKLARING WINDVLAAG DRUILERIG WINDKRACHT "
     "NACHTVORST KOUDEFRONT TEMPERATUUR WEERBERICHT THERMOMETER ZONNESCHIJN "
     "WARMTEFRONT",
     ["PARAPLU MEE", "NA REGEN KOMT ZONNESCHIJN", "APRIL DOET WAT HIJ WIL",
      "HET REGENT PIJPENSTELEN", "WEER OF GEEN WEER", "BELGISCH WEER",
      "VIER SEIZOENEN OP EEN DAG", "ZON EN WOLKEN", "MORGEN WORDT HET BETER",
      "HET WEER VAN MORGEN IS ALTIJD EEN VERRASSING",
      "ER BESTAAT GEEN SLECHT WEER ALLEEN SLECHTE KLEDING"]),
    ("In de tuin",
     "GRAS BOOM HAAG HARK TULP ROOS EGEL WORM SLAK ZAAD BLAD BLOEM SCHOP "
     "SERRE MEREL GAZON BIJEN STRUIK VIJVER GIETER SCHUUR WORTEL BORDER "
     "KLIMOP HOMMEL TOMAAT ONKRUID COMPOST VLINDER PERGOLA HANGMAT AARDBEI "
     "MOESTUIN BLOEMBOL LAVENDEL REGENTON MADELIEF RABARBER FRAMBOOS "
     "KRUIWAGEN HORTENSIA APPELBOOM TUINSLANG TUINSTOEL COURGETTE GRASMAAIER "
     "ZONNEBLOEM SNOEISCHAAR VOGELHUISJE PAARDENBLOEM",
     ["GROENE VINGERS", "ZAAIEN EN OOGSTEN", "LENTE IN DE LUCHT", "BLOEIEN",
      "WIE ZAAIT ZAL OOGSTEN", "BUITEN ZIJN", "ONKRUID VERGAAT NIET",
      "MET DE VOETEN IN HET GRAS", "SNOEIEN DOET BLOEIEN", "GENIETEN",
      "HET GRAS IS ALTIJD GROENER BIJ DE BUREN",
      "EEN TUIN IS NOOIT AF EN DAT IS MAAR GOED OOK"]),
    ("Muziek",
     "STEM TOON MAAT KOOR LIED ZANG HARP DUET RITME PIANO VIOOL FLUIT DRUMS "
     "ORGEL CELLO OPERA TEMPO KLANK SNAAR GITAAR ORKEST SOLIST PODIUM SONATE "
     "TROMPET CONCERT MELODIE REFREIN AKKOORD TROMMEL APPLAUS FANFARE "
     "BEIAARD KLAVIER DIRIGENT FESTIVAL SAXOFOON KLARINET ZANGERES MUZIKANT "
     "STEMVORK SYMFONIE HARMONIE PARTITUUR MICROFOON ACCORDEON CONTRABAS "
     "NOTENBALK COMPONIST REPETITIE TOONLADDER VERSTERKER BLADMUZIEK "
     "STRIJKSTOK KOPTELEFOON",
     ["BISNUMMER", "MUZIEK MAAKT BLIJ", "DE TOON ZETTEN", "STILTE",
      "EEN VALSE NOOT", "DE EERSTE VIOOL SPELEN", "MAAT HOUDEN",
      "ALLE REGISTERS OPEN", "DAT KLINKT ALS MUZIEK IN DE OREN",
      "ZONDER MUZIEK IS HET LEVEN EEN VERGISSING",
      "WAAR WOORDEN TEKORTSCHIETEN SPREEKT MUZIEK"]),
    ("Dieren",
     "HOND GEIT EEND GANS WOLF BEER HERT MUIS HAAS HAAI VALK PAARD ZWAAN "
     "OTTER BEVER ZEBRA LEEUW GIRAF AREND LIBEL SCHAAP VARKEN KONIJN TIJGER "
     "WALVIS KAMEEL SPECHT ZWALUW KIKKER REIGER OLIFANT PINGUIN DOLFIJN "
     "IJSBEER RENDIER HAGEDIS BUIZERD EEKHOORN FLAMINGO OOIEVAAR PAPEGAAI "
     "KROKODIL LUIPAARD NIJLPAARD NEUSHOORN KANGOEROE VLEERMUIS SCHILDPAD "
     "SALAMANDER SPRINKHAAN CHIMPANSEE ROODBORSTJE STRUISVOGEL STEKELVARKEN",
     ["BEESTENBOEL", "DIERENTUIN", "OP SAFARI", "ZO SLIM ALS EEN VOS",
      "EEN OLIFANT VERGEET NOOIT", "ZO TROTS ALS EEN PAUW", "SAVANNE",
      "DE LEEUW IS DE KONING DER DIEREN", "EEN GEHEUGEN ALS EEN OLIFANT",
      "ALS DE KAT VAN HUIS IS DANSEN DE MUIZEN",
      "IN TANZANIA ZIE JE ZE ALLEMAAL IN HET WILD"]),
    ("Wetenschap",
     "LABO DATA ATOOM MASSA PROEF GETAL VIRUS MODEL LASER KRACHT METING "
     "BEWIJS CHEMIE FYSICA PROTON LOGICA AXIOMA PRISMA VOLUME ENERGIE "
     "THEORIE FORMULE MAGNEET GRAFIEK PLANEET NEUTRON KWANTUM ELEMENT "
     "FOSSIEL MOLECULE ELEKTRON STELLING EVOLUTIE BACTERIE BIOLOGIE WISKUNDE "
     "SNELHEID ZUURSTOF KOOLSTOF SPECTRUM TELESCOOP HYPOTHESE ONDERZOEK "
     "LICHTJAAR WATERSTOF DICHTHEID MICROSCOOP EXPERIMENT UITVINDING "
     "ONTDEKKING FREQUENTIE GOLFLENGTE REAGEERBUIS STERRENKUNDE LABORATORIUM",
     ["EUREKA", "METEN IS WETEN", "KENNIS IS MACHT", "BEWEZEN",
      "NIEUWSGIERIG BLIJVEN", "DE AARDE DRAAIT OM DE ZON",
      "VRAGEN STAAT VRIJ", "WAAROM IS DE HEMEL BLAUW",
      "EERST DENKEN DAN DOEN", "TWIJFEL IS HET BEGIN VAN WIJSHEID",
      "ELKE GROTE ONTDEKKING BEGINT MET EEN VRAAG"]),
    ("Op kantoor",
     "TEAM TAAK DOEL KANS LIFT MUIS STOEL KLANT BADGE BALIE PLOEG BUREAU "
     "SCHERM LAPTOP AGENDA KOFFIE BUDGET RISICO BALPEN ORDNER PROCES KENNIS "
     "PRINTER COLLEGA DOSSIER PROJECT OFFERTE FACTUUR BERICHT NOTITIE "
     "RAPPORT ANALYSE ONTHAAL SYSTEEM OVERLEG VERSLAG PLANNING CONTRACT "
     "MIJLPAAL TELEFOON GEGEVENS WORKSHOP FLEXPLEK DEADLINE STRATEGIE "
     "WERKGROEP ARCHITECT DASHBOARD ACTIEPUNT THUISWERK STUURGROEP "
     "OPLEVERING BRAINSTORM CONSULTANT TOETSENBORD VERGADERING PRESENTATIE "
     "KOFFIEPAUZE NIEUWSBRIEF HANDTEKENING",
     ["WEEKEND", "KOFFIETIJD", "SAMEN STERKER", "EERST KOFFIE", "VRIJDAG",
      "AFSPRAAK IS AFSPRAAK", "VELE HANDEN MAKEN LICHT WERK", "TIJD IS GELD",
      "EEN GOED BEGIN IS HET HALVE WERK", "ARBEID ADELT",
      "GOEDE AFSPRAKEN MAKEN GOEDE VRIENDEN",
      "DEZE VERGADERING HAD OOK EEN MAILTJE KUNNEN ZIJN"]),
    ("Belgische steden en gemeenten",
     "GENT LUIK GENK LIER GEEL BOOM AALST NAMEN IEPER DIEST HALLE RONSE "
     "EEKLO TIELT BRUGGE LEUVEN BERGEN TIENEN DINANT AARLEN KNOKKE VEURNE "
     "NINOVE BILZEN DUFFEL HASSELT DOORNIK BRUSSEL LOKEREN WAREGEM MAASEIK "
     "WILRIJK HOBOKEN MORTSEL MECHELEN KORTRIJK OOSTENDE TURNHOUT TONGEREN "
     "ANTWERPEN CHARLEROI ROESELARE VILVOORDE HERENTALS POPERINGE DIKSMUIDE "
     "BASTENAKEN NIEUWPOORT OUDENAARDE DENDERMONDE BLANKENBERGE",
     ["EENDRACHT MAAKT MACHT", "FRIETJES", "WAFELS EN CHOCOLADE", "ATOMIUM",
      "VAN DE KUST TOT DE ARDENNEN", "MIJN VLAKKE LAND", "MANNEKEN PIS",
      "KLEIN LAND GROOT HART", "ELF MILJOEN BELGEN", "DE KOEKENSTAD",
      "HET LAND VAN FRIETEN BIER EN CHOCOLADE",
      "TUSSEN SCHELDE EN MAAS LIGT EEN LAND VOL VERHALEN"]),
    ("Water",
     "BRON BEEK MEER DIJK GOLF POMP DAMP WOLK MAAS KLEP BUIS SLUIS KRAAN "
     "RIOOL OEVER DELTA GETIJ STOOM RIVIER KANAAL FILTER STROOM VIJVER "
     "GRACHT POLDER OCEAAN LAGUNE MOERAS DOUCHE AFVOER DRUPPEL LEIDING "
     "MONDING IJSBERG FONTEIN BADKUIP DROOGTE SCHELDE STUWMEER WATERVAL "
     "REGENPUT GLETSJER ZUIVERING COLLECTOR OVERSTORT RESERVOIR WATERPEIL "
     "BRONWATER GRONDWATER DRINKWATER WATERTOREN WATERMETER AFVALWATER "
     "HEMELWATER KRAANWATER SPAARBEKKEN PERSLEIDING BUFFERBEKKEN",
     ["ELKE DRUPPEL TELT", "WATER IS LEVEN", "PROPER WATER", "ZUIVER",
      "VAN BRON TOT KRAAN", "WATER NAAR DE ZEE DRAGEN", "KRISTALHELDER",
      "HET WATER STAAT AAN DE LIPPEN", "SPAARZAAM",
      "ZONDER WATER GEEN LEVEN OP AARDE",
      "STILLE WATERS HEBBEN DIEPE GRONDEN",
      "ER VLOEIT NOG VEEL WATER DOOR DE SCHELDE"]),
    ("Energie",
     "VOLT WATT LAMP ACCU VONK OLIE KABEL METER KOLEN MOTOR SNOER LICHT "
     "STROOM OPSLAG DYNAMO TARIEF WARMTE TURBINE AARDGAS REACTOR PIEKUUR "
     "STEKKER STUWDAM SPANNING BATTERIJ CENTRALE LAADPAAL VERBRUIK KILOWATT "
     "ZEKERING ISOLATIE BIOMASSA WINDPARK VERMOGEN OMVORMER UITSTOOT "
     "DUURZAAM WINDMOLEN GENERATOR WATERSTOF NETBEHEER BRANDSTOF WARMTENET "
     "STEENKOOL ROTORBLAD WARMTEPOMP SCHAKELAAR ZONNEPANEEL KERNENERGIE "
     "STOPCONTACT ZONNEBOILER THERMOSTAAT HOOGSPANNING HERNIEUWBAAR "
     "GELIJKSTROOM WISSELSTROOM",
     ["VOLLE KRACHT", "ONDER STROOM", "GROENE STROOM", "OPGELADEN",
      "WIND IN DE ZEILEN", "DE ZON STUURT GEEN FACTUUR", "LICHT UIT",
      "ENERGIE BESPAREN BEGINT THUIS", "VOL ENERGIE", "SPANNEND",
      "MET DE WIND OP ZEE DRAAIT DE TOEKOMST",
      "DE GROENSTE ENERGIE IS DIE DIE JE NIET VERBRUIKT"]),
    ("Ruimtevaart",
     "MAAN MARS STER BAAN LUIK STOF RAKET NEVEL VENUS PLUTO AARDE SONDE "
     "KOMEET KRATER HEELAL KOSMOS URANUS MISSIE VLUCHT MODULE RINGEN PLANEET "
     "CAPSULE MELKWEG METEOOR JUPITER AFTELLEN ROBOTARM SATURNUS NEPTUNUS "
     "POOLSTER ASTRONAUT RUIMTEPAK LANCERING TELESCOOP LICHTJAAR MERCURIUS "
     "DAMPKRING KOPPELING ZONNEWIND MAANWAGEN BEMANNING MAANSTEEN SATELLIET "
     "OMLOOPBAAN STUWKRACHT GEWICHTLOOS MAANLANDING RUIMTESONDE HITTESCHILD "
     "LANCEERBASIS VERREKIJKER ZONNESTELSEL STERRENBEELD STERRENHEMEL "
     "NOORDERLICHT",
     ["DRIE TWEE EEN START", "NAAR DE MAAN", "TOT DE STERREN EN VERDER",
      "EEN KLEINE STAP VOOR EEN MENS", "REIK NAAR DE STERREN", "ONEINDIG",
      "DE AARDE IS EEN BLAUWE KNIKKER", "LANCERING GESLAAGD", "RUIMTE",
      "AFTELLEN MAAR", "WE ZIJN ALLEMAAL GEMAAKT VAN STERRENSTOF",
      "GEWICHTLOOS ZWEVEN BOVEN DE BLAUWE PLANEET"]),
    ("Wintersport",
     "LIFT HELM BERG SLEE STOK MUTS GIPS PISTE SJAAL ALPEN BOCHT SPOOR VORST "
     "SNEEUW GONDEL LAWINE CHALET SLALOM SKIPAS WANTEN SKIPAK SCHANS SCHAATS "
     "SKILIFT BERGHUT IJSBAAN RODELEN BOBSLEE BERGTOP SKIBRIL BIATLON "
     "CURLING AFDALING LANGLAUF GLETSJER IJSPEGEL MEDAILLE SNOWBOARD "
     "SKISCHOEN SNEEUWPOP SNEEUWBAL SKILERAAR KABELBAAN WINTERJAS HAARDVUUR "
     "BOOMGRENS SLEEPLIFT IJSHOCKEY HANDSCHOEN KAASFONDUE SNEEUWKANON "
     "SPRINGSCHANS POEDERSNEEUW SNEEUWSCHOEN",
     ["SKI HEIL", "LATTEN ONDER", "WITTE PRACHT", "DE PISTE OP", "POEDER",
      "VERSE SNEEUW EN BLAUWE LUCHT", "GLIJDEN MAAR", "SNEEUWPRET",
      "BERGAF GAAT VANZELF", "KOUDE NEUS EN WARME HANDEN",
      "EERST SKIEN DAN WARME CHOCOLADEMELK",
      "NA DE LAATSTE AFDALING SMAAKT ALLES BETER"]),
    ("In het bos",
     "BLAD BEUK BERK SPAR HERT NEST MIER SPIN HARS KNOP LAAN WILD VAREN "
     "EIKEL BRAAM HEIDE KEVER KRUIN TWIJG DREEF STRONK WORTEL SCHORS BOSBES "
     "SPECHT HERFST STILTE BOSUIL SCHADUW LOOFBOS BOSRAND EEKHOORN KASTANJE "
     "BLADEREN NAALDBOS PICKNICK HAZELAAR BOOMSTAM JAARRING EVERZWIJN "
     "WANDELPAD VOGELZANG WEGWIJZER BEUKENNOOT HOUTHAKKER BOSWACHTER "
     "MIERENHOOP LIJSTERBES HOUTSTAPEL PADDENSTOEL DENNENAPPEL VLIEGENZWAM "
     "ZONNESTRAAL UITKIJKTOREN",
     ["FRISSE LUCHT", "BOSWANDELING", "STIL ZIJN EN LUISTEREN", "BOSLUCHT",
      "HERFSTKLEUREN", "DE GEUR VAN NAT MOS", "ZUURSTOF TANKEN", "VERDWALEN",
      "HOGE BOMEN VANGEN VEEL WIND",
      "DOOR DE BOMEN HET BOS NIET MEER ZIEN",
      "RITSELENDE BLADEREN ONDER JE VOETEN",
      "IN HET BOS KOMT JE HOOFD VANZELF TOT RUST"]),
]
THEMES = [(t, w.split(), s) for t, w, s in THEMES]

# Fallback solutions that fit any theme (used only when no theme phrase fits).
GENERIC_SOLUTIONS = [
    "GEVONDEN", "GOED GEDAAN", "KNAP GEZOCHT", "SCHERPE OGEN",
    "ALLES GEVONDEN", "PUZZEL OPGELOST", "WIE ZOEKT DIE VINDT",
    "JE HEBT ZE ALLEMAAL", "OEFENING BAART KUNST", "DE AANHOUDER WINT",
    "ZOEKT EN GIJ ZULT VINDEN", "GEDULD IS EEN SCHONE ZAAK",
    "HOUD JE BREIN IN BEWEGING", "GOED GEZOCHT IS HALF GEVONDEN",
    "RUST ROEST", "EIND GOED AL GOED", "KLAAR", "PRIMA WERK", "TOPPER",
    "ELKE DAG EEN BEETJE SLIMMER", "WIE HET LAATST LACHT LACHT HET BEST",
    "ZOEKEN IS OOK EEN VORM VAN ONTSPANNEN",
    "NU IS HET TIJD VOOR EEN KOP KOFFIE", "KNAP",
    "MET EEN SCHERPE BLIK ZIE JE ALLES",
]

# Bonus words for Letterchaos, by length.
BONUS = {
    8: ("OPLOSSEN GEHEUGEN NADENKEN ANTWOORD KAMPIOEN GEWONNEN GESLAAGD "
        "HERSENEN PRACHTIG AVONTUUR KNAPPERD GELUKKIG OEFENING TRAINING "
        "DENKWERK RAADSELS SLIMMERD GENIETEN GEWELDIG BRILJANT GEDULDIG "
        "WIJSNEUS TEVREDEN OPGELOST GEVONDEN VERSTAND SCHERPTE BEHENDIG "
        "LEERRIJK LEERZAAM GEKRAAKT WINNAARS").split(),
    9: ("OPLOSSING DENKSPORT UITDAGING WOORDSPEL SPEURWERK ONTHOUDEN "
        "LETTERTJE BOLLEBOOS SLIMMERIK VOLHOUDEN VOLBRACHT GELUKWENS "
        "SUCCESVOL INZICHTEN PROFICIAT SPELLETJE BEGRIJPEN VOLTOOIEN "
        "ONTRAFELD HERSENCEL HOOFDZAAK ZEGETOCHT").split(),
    10: ("DOORZETTER VOLTREFFER UITSTEKEND HERSENWERK LETTERSOEP KAMPIOENEN "
         "DENKKRACHT VERRASSING ONTDEKKING TAALGEVOEL WOORDKUNST HELDERHEID "
         "DOORDENKER BEDENKTIJD EINDSPRINT DOORZETTEN VERSTANDIG TAALKUNDIG "
         "ONTSPANNEN NAUWKEURIG ZORGVULDIG VOLDOENING GLIMLACHEN").split(),
}
# Shorter bonus words for the smaller Letterchaos of the 7.3" Paper Pro Move.
BONUS[6] = ("DENKEN HELDER ZOEKEN KRAKEN TOPPER WINNEN GELUKT SLAGEN OPGAVE "
            "SLIMME KNAPPE LEZERS GEVOEL ROUTES KLASSE SPELEN DENKER TALENT "
            "STERKE BINNEN").split()
BONUS[7] = ("RAADSEL SNUGGER PIENTER GENIAAL GEHAALD BEDACHT LETTERS SPELLEN "
            "DENKERS WINNAAR TOPPERS GEDACHT ONTDEKT PLEZIER SLIMMER SPELERS "
            "HELDERE KRANIGE STERKER SNELLER").split()

# (spreekwoord, betekenis)
SPREEKWOORDEN = [
    ("De appel valt niet ver van de boom",
     "Kinderen lijken vaak op hun ouders."),
    ("Wie het kleine niet eert is het grote niet weerd",
     "Wees ook dankbaar voor kleine dingen."),
    ("Beter een vogel in de hand dan tien in de lucht",
     "Wees tevreden met wat je zeker hebt."),
    ("Als de kat van huis is dansen de muizen op tafel",
     "Zonder toezicht doet iedereen wat hij wil."),
    ("De morgenstond heeft goud in de mond",
     "Wie vroeg begint, bereikt meer."),
    ("Wie een kuil graaft voor een ander valt er zelf in",
     "Wie een ander kwaad wil doen, wordt er zelf het slachtoffer van."),
    ("Zoals het klokje thuis tikt tikt het nergens",
     "Nergens is het zo fijn als thuis."),
    ("Een goed begin is het halve werk",
     "Wie goed start, is al een heel eind op weg."),
    ("Men moet het ijzer smeden als het heet is",
     "Grijp je kans op het juiste moment."),
    ("Wie zijn billen brandt moet op de blaren zitten",
     "Je moet de gevolgen van je eigen fouten dragen."),
    ("De kruik gaat zo lang te water tot ze breekt",
     "Wie risico's blijft nemen, loopt vroeg of laat tegen de lamp."),
    ("Wie het laatst lacht lacht het best",
     "Pas aan het einde blijkt wie echt gewonnen heeft."),
    ("Een gewaarschuwd man is er twee waard",
     "Wie het gevaar kent, kan zich voorbereiden."),
    ("Al draagt een aap een gouden ring het is en blijft een lelijk ding",
     "Uiterlijk vertoon verandert iemands aard niet."),
    ("Het is niet al goud wat er blinkt",
     "Schijn bedriegt."),
    ("Je moet de huid niet verkopen voor de beer geschoten is",
     "Reken niet op iets wat nog niet zeker is."),
    ("De beste stuurlui staan aan wal",
     "Kritiek geven is makkelijker dan het zelf doen."),
    ("Zachte heelmeesters maken stinkende wonden",
     "Wie te voorzichtig ingrijpt, maakt het probleem groter."),
    ("Schoenmaker blijf bij je leest",
     "Doe waar je goed in bent."),
    ("Er is geen roos zonder doornen",
     "Aan elk mooi ding zit ook een nadeel."),
    ("Beter ten halve gekeerd dan ten hele gedwaald",
     "Een fout halverwege rechtzetten is beter dan koppig doorgaan."),
    ("In het land der blinden is eenoog koning",
     "Tussen mensen die weinig kunnen, valt een middelmatige al op."),
    ("De pot verwijt de ketel dat hij zwart ziet",
     "Iemand verwijt een ander een fout die hij zelf ook heeft."),
    ("Je moet roeien met de riemen die je hebt",
     "Je moet het doen met de middelen die er zijn."),
    ("Een ezel stoot zich geen twee keer aan dezelfde steen",
     "Een verstandig mens maakt dezelfde fout geen tweede keer."),
    ("Blaffende honden bijten niet",
     "Wie veel dreigt, doet meestal niets."),
    ("Het zijn sterke benen die de weelde kunnen dragen",
     "Niet iedereen kan goed met rijkdom omgaan."),
    ("Wie de schoen past trekke hem aan",
     "Wie zich aangesproken voelt, mag de kritiek ter harte nemen."),
    ("Als het kalf verdronken is dempt men de put",
     "Maatregelen komen vaak pas na het ongeluk."),
    ("Stille waters hebben diepe gronden",
     "Rustige mensen hebben vaak meer in zich dan je denkt."),
    ("De gestage drup holt de steen uit",
     "Wie volhoudt, bereikt uiteindelijk zijn doel."),
    ("Vele handen maken licht werk",
     "Samen gaat het sneller."),
    ("Wie niet horen wil moet voelen",
     "Wie niet luistert, leert het op de harde manier."),
    ("Het oog van de meester maakt het paard vet",
     "Persoonlijk toezicht geeft het beste resultaat."),
    ("Een vliegende kraai vangt altijd wat",
     "Wie erop uit trekt, vindt altijd wel iets."),
    ("Rome is niet op een dag gebouwd",
     "Grote dingen vragen tijd."),
    ("Men moet de dag niet prijzen voor het avond is",
     "Juich niet te vroeg."),
    ("Waar gehakt wordt vallen spaanders",
     "Bij elk groot werk gaat er wel iets mis."),
    ("Als twee honden vechten om een been loopt de derde ermee heen",
     "Als twee ruziën, gaat een derde met de winst lopen."),
    ("Een kinderhand is gauw gevuld",
     "Een kind is met weinig tevreden."),
    ("Wie zijn neus schendt schendt zijn aangezicht",
     "Wie kwaad spreekt van zijn familie, schaadt zichzelf."),
    ("Met de hoed in de hand komt men door het ganse land",
     "Met beleefdheid bereik je overal veel."),
    ("Zoals de ouden zongen piepen de jongen",
     "Kinderen doen hun ouders na."),
    ("Elk huisje heeft zijn kruisje",
     "Iedereen heeft zijn eigen zorgen."),
    ("Lekker is maar een vinger lang",
     "Genot duurt maar kort."),
    ("De wens is de vader van de gedachte",
     "Je gelooft graag wat je hoopt."),
    ("Kleine potjes hebben grote oren",
     "Kinderen horen meer dan je denkt."),
    ("Zoveel hoofden zoveel zinnen",
     "Iedereen heeft zijn eigen mening."),
    ("Wie wind zaait zal storm oogsten",
     "Wie onrust stookt, krijgt er zelf veel meer van terug."),
    ("Een goede buur is beter dan een verre vriend",
     "Aan iemand dichtbij heb je meer dan aan iemand ver weg."),
    ("Het is zaliger te geven dan te ontvangen",
     "Geven maakt gelukkiger dan krijgen."),
    ("De eerste klap is een daalder waard",
     "Wie als eerste handelt, heeft een voorsprong."),
    ("Wie met pek omgaat wordt ermee besmet",
     "Slecht gezelschap heeft een slechte invloed."),
    ("Aan de vruchten kent men de boom",
     "Aan de resultaten zie je wat iemand waard is."),
    ("Spreken is zilver zwijgen is goud",
     "Soms is het wijzer om niets te zeggen."),
    ("De laatste loodjes wegen het zwaarst",
     "Het einde van een karwei valt het moeilijkst."),
    ("Na gedane arbeid is het goed rusten",
     "Na het werk smaakt de rust het best."),
    ("Een zwaluw maakt nog geen zomer",
     "Eén goed teken is nog geen bewijs."),
    ("Wie een hond wil slaan vindt licht een stok",
     "Wie iemand iets wil verwijten, vindt altijd wel een reden."),
    ("Het gras is altijd groener aan de overkant",
     "Wat een ander heeft, lijkt altijd beter."),
    ("Zo de wind waait waait zijn jasje",
     "Hij past zijn mening aan aan wie het voor het zeggen heeft."),
    ("Hoe meer zielen hoe meer vreugd",
     "Met meer mensen is het gezelliger."),
    ("Een rollende steen vergaart geen mos",
     "Wie nooit ergens blijft, bouwt niets op."),
]

# --- Geheugentraining ---------------------------------------------------------
LIJSTEN = [
    ("Boodschappenlijst",
     ["melk", "brood", "eieren", "kaas", "boter", "appels", "bananen",
      "tomaten", "uien", "wortelen", "rijst", "pasta", "koffie", "thee",
      "suiker", "bloem", "yoghurt", "zalm", "sla", "komkommer", "paprika",
      "citroenen", "aardappelen", "olijfolie", "honing", "confituur",
      "chocolade", "muesli", "champignons", "spinazie", "druiven", "peren",
      "speculaas", "wafels", "mosterd", "mayonaise", "tandpasta", "zeep",
      "afwasmiddel", "keukenrol"]),
    ("Te doen vandaag",
     ["fiets oppompen", "planten water geven", "tandarts bellen",
      "pakje ophalen", "was ophangen", "vuilnis buitenzetten",
      "verjaardagskaart sturen", "boek terugbrengen", "auto wassen",
      "rekening betalen", "lamp vervangen", "gras maaien", "oma bellen",
      "foto's afdrukken", "koffer inpakken", "treinticket kopen",
      "kapper boeken", "sleutel laten bijmaken", "sporttas klaarzetten",
      "batterijen kopen", "ramen poetsen", "brief posten",
      "schoenen poetsen", "brood halen", "tafel reserveren"]),
    ("Paklijst voor de reis",
     ["paspoort", "zonnebril", "tandenborstel", "oplader", "regenjas",
      "wandelschoenen", "zwembroek", "fototoestel", "reisgids", "zaklamp",
      "handdoek", "pet", "sokken", "trui", "verrekijker", "drinkfles",
      "pleisters", "boek", "slippers", "rugzak", "sjaal", "muts",
      "kaartspel", "hoofdtelefoon", "wekker", "paraplu", "zakmes",
      "slaapzak", "notitieboekje", "zonnehoed"]),
]

NAMEN = ["Emma", "Noor", "Lotte", "Tom", "Bram", "Sara", "Milan", "Jef",
         "Koen", "Lies", "Wout", "Hanne", "Ruben", "Elke", "Pieter", "Fien"]
STEDEN = ["Gent", "Brugge", "Leuven", "Hasselt", "Oostende", "Mechelen",
          "Kortrijk", "Namen", "Luik", "Antwerpen"]
DAGEN = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag"]
STRATEN = ["Kerkstraat", "Stationsstraat", "Molenweg", "Lindenlaan",
           "Schoolstraat", "Dorpsplein", "Beukenlaan", "Kasteeldreef"]
KLEUREN_VOORWERP = ["rode", "blauwe", "groene", "gele", "zwarte", "witte",
                    "oranje"]
