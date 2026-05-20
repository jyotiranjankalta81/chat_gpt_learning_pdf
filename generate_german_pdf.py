#!/usr/bin/env python3
"""
Comprehensive German Language Reference PDF Generator
Covers: Alphabet, Numbers, Grammar categories, and 500 most common words
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas


# ─── Color Palette ────────────────────────────────────────────────────────────
DARK_BLUE   = colors.HexColor("#1a3a5c")
MED_BLUE    = colors.HexColor("#2e6da4")
LIGHT_BLUE  = colors.HexColor("#d0e4f7")
ACCENT_GOLD = colors.HexColor("#c8960c")
LIGHT_GOLD  = colors.HexColor("#fef9e7")
LIGHT_GREY  = colors.HexColor("#f5f5f5")
MED_GREY    = colors.HexColor("#cccccc")
WHITE       = colors.white
BLACK       = colors.black
GREEN_BG    = colors.HexColor("#e8f5e9")
PURPLE_BG   = colors.HexColor("#f3e5f5")
ORANGE_BG   = colors.HexColor("#fff3e0")
TEAL_BG     = colors.HexColor("#e0f7fa")
PINK_BG     = colors.HexColor("#fce4ec")
YELLOW_BG   = colors.HexColor("#fffde7")


# ─── Page numbering ───────────────────────────────────────────────────────────
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#888888"))
        self.drawCentredString(
            A4[0] / 2,
            1.0 * cm,
            f"German Language Reference  •  Page {self._pageNumber} of {page_count}"
        )
        self.restoreState()


def build_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        "CoverTitle",
        fontSize=34, fontName="Helvetica-Bold",
        textColor=WHITE, alignment=TA_CENTER,
        spaceAfter=8, leading=42,
    ))
    styles.add(ParagraphStyle(
        "CoverSubtitle",
        fontSize=16, fontName="Helvetica",
        textColor=colors.HexColor("#cce0ff"),
        alignment=TA_CENTER, spaceAfter=6, leading=22,
    ))
    styles.add(ParagraphStyle(
        "SectionTitle",
        fontSize=18, fontName="Helvetica-Bold",
        textColor=WHITE, alignment=TA_CENTER,
        spaceAfter=4, leading=24, spaceBefore=4,
    ))
    styles.add(ParagraphStyle(
        "SubTitle",
        fontSize=13, fontName="Helvetica-Bold",
        textColor=DARK_BLUE, alignment=TA_LEFT,
        spaceAfter=4, spaceBefore=10, leading=18,
    ))
    styles.add(ParagraphStyle(
        "BodyText2",
        fontSize=9.5, fontName="Helvetica",
        textColor=BLACK, alignment=TA_JUSTIFY,
        spaceAfter=4, leading=14,
    ))
    styles.add(ParagraphStyle(
        "TableHeader",
        fontSize=9, fontName="Helvetica-Bold",
        textColor=WHITE, alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        "Cell",
        fontSize=8.5, fontName="Helvetica",
        textColor=BLACK, alignment=TA_LEFT, leading=12,
    ))
    styles.add(ParagraphStyle(
        "CellCenter",
        fontSize=8.5, fontName="Helvetica",
        textColor=BLACK, alignment=TA_CENTER, leading=12,
    ))
    styles.add(ParagraphStyle(
        "CellBold",
        fontSize=8.5, fontName="Helvetica-Bold",
        textColor=DARK_BLUE, alignment=TA_LEFT, leading=12,
    ))
    styles.add(ParagraphStyle(
        "Note",
        fontSize=8, fontName="Helvetica-Oblique",
        textColor=colors.HexColor("#555555"),
        alignment=TA_LEFT, spaceAfter=4, leading=12,
    ))
    return styles


def section_banner(title, styles, bg=DARK_BLUE):
    """Returns a full-width colored banner for section headers."""
    data = [[Paragraph(title, styles["SectionTitle"])]]
    t = Table(data, colWidths=[17.5 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
    ]))
    return t


def std_table(header_row, data_rows, col_widths, styles, row_bg=None):
    """Generic styled table builder."""
    header = [Paragraph(h, styles["TableHeader"]) for h in header_row]
    body = []
    for i, row in enumerate(data_rows):
        bg = (row_bg[i] if row_bg else (LIGHT_GREY if i % 2 == 0 else WHITE))
        body.append([Paragraph(str(c), styles["Cell"]) for c in row])

    table_data = [header] + body
    t = Table(table_data, colWidths=col_widths, repeatRows=1)

    row_styles = [
        ("BACKGROUND",    (0, 0), (-1, 0),  DARK_BLUE),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  9),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  WHITE),
        ("GRID",          (0, 0), (-1, -1), 0.4, MED_GREY),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]
    for i in range(len(data_rows)):
        bg = (row_bg[i] if row_bg else (LIGHT_GREY if i % 2 == 0 else WHITE))
        row_styles.append(("BACKGROUND", (0, i + 1), (-1, i + 1), bg))

    t.setStyle(TableStyle(row_styles))
    return t


# ══════════════════════════════════════════════════════════════════════════════
#  DATA
# ══════════════════════════════════════════════════════════════════════════════

ALPHABET = [
    ("A a", "ah",        "like 'a' in father"),
    ("B b", "beh",       "like English 'b'"),
    ("C c", "tseh",      "like 'ts' before e/i; like 'k' elsewhere"),
    ("D d", "deh",       "like English 'd'"),
    ("E e", "eh",        "like 'e' in bed"),
    ("F f", "eff",       "like English 'f'"),
    ("G g", "geh",       "like English 'g' (hard)"),
    ("H h", "hah",       "like English 'h'; silent after vowels"),
    ("I i", "ee",        "like 'ee' in see (short: like 'i' in bit)"),
    ("J j", "yot",       "like English 'y' in yes"),
    ("K k", "kah",       "like English 'k'"),
    ("L l", "ell",       "like English 'l'"),
    ("M m", "emm",       "like English 'm'"),
    ("N n", "enn",       "like English 'n'"),
    ("O o", "oh",        "like 'o' in go (rounded)"),
    ("P p", "peh",       "like English 'p'"),
    ("Q q", "koo",       "always followed by 'u'; like 'kv'"),
    ("R r", "err",       "guttural/rolled at back of throat"),
    ("S s", "ess",       "like 'z' before vowels; like 's' elsewhere"),
    ("T t", "teh",       "like English 't'"),
    ("U u", "oo",        "like 'oo' in moon (short: like 'u' in put)"),
    ("V v", "fow",       "like English 'f'"),
    ("W w", "veh",       "like English 'v'"),
    ("X x", "iks",       "like 'ks'"),
    ("Y y", "üpsilon",   "like German 'ü'; in loanwords like English 'y'"),
    ("Z z", "tset",      "like 'ts' in cats"),
    # Umlauts & ß
    ("Ä ä", "ah-Umlaut", "like 'e' in bed"),
    ("Ö ö", "oh-Umlaut", "like 'eu' in French feu (rounded 'e')"),
    ("Ü ü", "oo-Umlaut", "like French 'u' (rounded 'ee')"),
    ("ß",   "ess-tset",  "like a double 's'; used after long vowels/diphthongs"),
]

NUMBERS = [
    ("0", "null",        "nool",           "zero"),
    ("1", "eins",        "ayns",           "one"),
    ("2", "zwei",        "tsvay",          "two"),
    ("3", "drei",        "dry",            "three"),
    ("4", "vier",        "feer",           "four"),
    ("5", "fünf",        "fewnf",          "five"),
    ("6", "sechs",       "zeks",           "six"),
    ("7", "sieben",      "zee-ben",        "seven"),
    ("8", "acht",        "akht",           "eight"),
    ("9", "neun",        "noyn",           "nine"),
    ("10", "zehn",       "tsayn",          "ten"),
    ("11", "elf",        "elf",            "eleven"),
    ("12", "zwölf",      "tsvurlf",        "twelve"),
    ("13", "dreizehn",   "dry-tsayn",      "thirteen"),
    ("14", "vierzehn",   "feer-tsayn",     "fourteen"),
    ("15", "fünfzehn",   "fewnf-tsayn",    "fifteen"),
    ("16", "sechzehn",   "zekh-tsayn",     "sixteen"),
    ("17", "siebzehn",   "zeep-tsayn",     "seventeen"),
    ("18", "achtzehn",   "akht-tsayn",     "eighteen"),
    ("19", "neunzehn",   "noyn-tsayn",     "nineteen"),
    ("20", "zwanzig",    "tsvan-tsikh",    "twenty"),
    ("21", "einundzwanzig", "ayn-oont-tsvan-tsikh", "twenty-one"),
    ("30", "dreißig",    "dry-sikh",       "thirty"),
    ("40", "vierzig",    "feer-tsikh",     "forty"),
    ("50", "fünfzig",    "fewnf-tsikh",    "fifty"),
    ("60", "sechzig",    "zekh-tsikh",     "sixty"),
    ("70", "siebzig",    "zeep-tsikh",     "seventy"),
    ("80", "achtzig",    "akht-tsikh",     "eighty"),
    ("90", "neunzig",    "noyn-tsikh",     "ninety"),
    ("100", "hundert",   "hoon-dert",      "one hundred"),
    ("1000", "tausend",  "tow-zent",       "one thousand"),
    ("1000000", "eine Million", "ay-neh meel-yohn", "one million"),
    ("1st", "erste",     "ers-teh",        "first"),
    ("2nd", "zweite",    "tsvay-teh",      "second"),
    ("3rd", "dritte",    "drit-teh",       "third"),
    ("4th", "vierte",    "feer-teh",       "fourth"),
    ("5th", "fünfte",    "fewnf-teh",      "fifth"),
    ("10th", "zehnte",   "tsayn-teh",      "tenth"),
    ("100th", "hundertste", "hoon-derts-teh", "hundredth"),
]

NOUNS = [
    ("der Mann",         "dair mahn",        "the man",           "m"),
    ("die Frau",         "dee frow",         "the woman",         "f"),
    ("das Kind",         "dahs kint",        "the child",         "n"),
    ("das Haus",         "dahs hows",        "the house",         "n"),
    ("die Straße",       "dee shtrah-seh",   "the street/road",   "f"),
    ("das Wasser",       "dahs vah-ser",     "the water",         "n"),
    ("das Brot",         "dahs broht",       "the bread",         "n"),
    ("die Zeit",         "dee tsayt",        "the time",          "f"),
    ("das Jahr",         "dahs yahr",        "the year",          "n"),
    ("der Tag",          "dair tahk",        "the day",           "m"),
    ("die Nacht",        "dee nakht",        "the night",         "f"),
    ("die Woche",        "dee voh-kheh",     "the week",          "f"),
    ("der Monat",        "dair moh-naht",    "the month",         "m"),
    ("die Stadt",        "dee shtaht",       "the city/town",     "f"),
    ("das Land",         "dahs lahnt",       "the country/land",  "n"),
    ("der Mensch",       "dair mensh",       "the person/human",  "m"),
    ("das Geld",         "dahs gelt",        "the money",         "n"),
    ("das Auto",         "dahs ow-toh",      "the car",           "n"),
    ("der Zug",          "dair tsook",       "the train",         "m"),
    ("das Flugzeug",     "dahs flook-tsoyg", "the airplane",      "n"),
    ("der Weg",          "dair vayk",        "the way/path",      "m"),
    ("die Arbeit",       "dee ar-bayt",      "the work/job",      "f"),
    ("die Schule",       "dee shoo-leh",     "the school",        "f"),
    ("der Arzt",         "dair artst",       "the doctor (m)",    "m"),
    ("das Krankenhaus",  "dahs krank-en-hows","the hospital",     "n"),
    ("die Familie",      "dee fah-meel-yeh", "the family",        "f"),
    ("der Vater",        "dair fah-ter",     "the father",        "m"),
    ("die Mutter",       "dee moo-ter",      "the mother",        "f"),
    ("der Bruder",       "dair broo-der",    "the brother",       "m"),
    ("die Schwester",    "dee shves-ter",    "the sister",        "f"),
    ("der Freund",       "dair froynt",      "the friend (m)",    "m"),
    ("die Freundin",     "dee froyn-din",    "the friend (f)",    "f"),
    ("das Essen",        "dahs es-en",       "the food/meal",     "n"),
    ("das Buch",         "dahs bookh",       "the book",          "n"),
    ("die Sprache",      "dee shprah-kheh",  "the language",      "f"),
    ("die Tür",          "dee tewer",        "the door",          "f"),
    ("das Fenster",      "dahs fen-ster",    "the window",        "n"),
    ("der Stuhl",        "dair shtool",      "the chair",         "m"),
    ("der Tisch",        "dair tish",        "the table",         "m"),
    ("das Bett",         "dahs bet",         "the bed",           "n"),
    ("die Küche",        "dee kew-kheh",     "the kitchen",       "f"),
    ("das Zimmer",       "dahs tsim-er",     "the room",          "n"),
    ("die Wohnung",      "dee voh-noong",    "the apartment",     "f"),
    ("der Baum",         "dair bowm",        "the tree",          "m"),
    ("die Blume",        "dee bloo-meh",     "the flower",        "f"),
    ("der Hund",         "dair hoont",       "the dog",           "m"),
    ("die Katze",        "dee kaht-seh",     "the cat",           "f"),
    ("das Tier",         "dahs teer",        "the animal",        "n"),
    ("das Licht",        "dahs likht",       "the light",         "n"),
    ("die Luft",         "dee looft",        "the air",           "f"),
    ("die Erde",         "dee air-deh",      "the earth/ground",  "f"),
    ("die Sonne",        "dee zon-eh",       "the sun",           "f"),
    ("der Mond",         "dair mohnt",       "the moon",          "m"),
    ("der Stern",        "dair shtern",      "the star",          "m"),
    ("das Feuer",        "dahs foy-er",      "the fire",          "n"),
    ("das Meer",         "dahs mayr",        "the sea",           "n"),
    ("der Fluss",        "dair floos",       "the river",         "m"),
    ("der Berg",         "dair bairk",       "the mountain",      "m"),
    ("der Wald",         "dair vahlt",       "the forest",        "m"),
    ("der Himmel",       "dair him-el",      "the sky/heaven",    "m"),
    ("der Regen",        "dair ray-gen",     "the rain",          "m"),
    ("der Schnee",       "dair shnay",       "the snow",          "m"),
    ("die Farbe",        "dee far-beh",      "the color",         "f"),
    ("die Frage",        "dee frah-geh",     "the question",      "f"),
    ("die Antwort",      "dee ant-vort",     "the answer",        "f"),
    ("das Problem",      "dahs proh-blaym",  "the problem",       "n"),
    ("die Lösung",       "dee lur-zoong",    "the solution",      "f"),
    ("die Idee",         "dee ee-day",       "the idea",          "f"),
    ("der Kopf",         "dair kopf",        "the head",          "m"),
    ("die Hand",         "dee hahnt",        "the hand",          "f"),
    ("der Arm",          "dair arm",         "the arm",           "m"),
    ("das Bein",         "dahs bayn",        "the leg",           "n"),
    ("das Auge",         "dahs ow-geh",      "the eye",           "n"),
    ("das Ohr",          "dahs or",          "the ear",           "n"),
    ("der Mund",         "dair moont",       "the mouth",         "m"),
    ("die Nase",         "dee nah-zeh",      "the nose",          "f"),
    ("das Herz",         "dahs hairts",      "the heart",         "n"),
    ("die Stimme",       "dee shtim-eh",     "the voice",         "f"),
    ("der Name",         "dair nah-meh",     "the name",          "m"),
    ("das Wort",         "dahs vort",        "the word",          "n"),
    ("der Satz",         "dair zahts",       "the sentence",      "m"),
    ("das Lied",         "dahs leet",        "the song",          "n"),
    ("die Musik",        "dee moo-zeek",     "the music",         "f"),
    ("der Film",         "dair film",        "the film/movie",    "m"),
    ("das Spiel",        "dahs shpeel",      "the game",          "n"),
    ("der Sport",        "dair shport",      "the sport",         "m"),
    ("das Leben",        "dahs lay-ben",     "the life",          "n"),
    ("der Tod",          "dair toht",        "the death",         "m"),
    ("die Liebe",        "dee lee-beh",      "the love",          "f"),
    ("die Hoffnung",     "dee hof-noong",    "the hope",          "f"),
    ("die Angst",        "dee angst",        "the fear/anxiety",  "f"),
    ("die Freude",       "dee froy-deh",     "the joy",           "f"),
    ("der Hunger",       "dair hoong-er",    "the hunger",        "m"),
    ("der Durst",        "dair doorst",      "the thirst",        "m"),
    ("die Gesundheit",   "dee geh-zoont-hayt","the health",       "f"),
    ("die Krankheit",    "dee krank-hayt",   "the illness",       "f"),
]

PRONOUNS = [
    ("ich",        "ikh",         "I",               "1st sing."),
    ("du",         "doo",         "you (informal)",  "2nd sing."),
    ("er",         "air",         "he",              "3rd sing. m"),
    ("sie",        "zee",         "she",             "3rd sing. f"),
    ("es",         "es",          "it",              "3rd sing. n"),
    ("wir",        "veer",        "we",              "1st pl."),
    ("ihr",        "eer",         "you (plural inf)","2nd pl."),
    ("sie/Sie",    "zee",         "they / You (formal)", "3rd pl./formal"),
    ("mich",       "mikh",        "me (accusative)", "1st sing. acc"),
    ("dich",       "dikh",        "you (accusative)","2nd sing. acc"),
    ("ihn",        "een",         "him",             "3rd sing. m acc"),
    ("uns",        "oons",        "us",              "1st pl. acc/dat"),
    ("euch",       "oykh",        "you (pl. acc/dat)","2nd pl."),
    ("mir",        "meer",        "me (dative)",     "1st sing. dat"),
    ("dir",        "deer",        "you (dative)",    "2nd sing. dat"),
    ("ihm",        "eem",         "him/it (dative)", "3rd sing. dat"),
    ("ihr",        "eer",         "her/their (dat)", "3rd sing. f dat"),
    ("ihnen/Ihnen","ee-nen",      "them / You (formal dat)", "3rd pl./formal"),
    ("mein",       "mayn",        "my",              "possessive"),
    ("dein",       "dayn",        "your (inform.)",  "possessive"),
    ("sein",       "zayn",        "his/its",         "possessive"),
    ("ihr",        "eer",         "her/their",       "possessive"),
    ("unser",      "oon-zer",     "our",             "possessive"),
    ("euer",       "oy-er",       "your (pl.)",      "possessive"),
    ("dieser",     "dee-zer",     "this",            "demonstrative"),
    ("jener",      "yay-ner",     "that",            "demonstrative"),
    ("welcher",    "vel-kher",    "which/what",      "interrogative"),
    ("wer",        "vayr",        "who",             "interrogative"),
    ("was",        "vahs",        "what",            "interrogative"),
    ("jeder",      "yay-der",     "every/each",      "indefinite"),
    ("alle",       "al-eh",       "all",             "indefinite"),
    ("einige",     "ay-ni-geh",   "some/a few",      "indefinite"),
    ("niemand",    "nee-mahnt",   "nobody",          "indefinite"),
    ("jemand",     "yay-mahnt",   "somebody",        "indefinite"),
    ("sich",       "zikh",        "oneself (refl.)", "reflexive"),
    ("selbst",     "zelpst",      "self/itself",     "reflexive"),
]

VERBS = [
    ("sein",          "zayn",           "to be",             "ich bin / du bist / er ist"),
    ("haben",         "hah-ben",        "to have",           "ich habe / du hast / er hat"),
    ("werden",        "vair-den",       "to become/will",    "ich werde / du wirst / er wird"),
    ("können",        "kur-nen",        "can / to be able",  "ich kann / du kannst"),
    ("müssen",        "mew-sen",        "must / to have to", "ich muss / du musst"),
    ("wollen",        "vol-en",         "to want to",        "ich will / du willst"),
    ("dürfen",        "dewr-fen",       "may / to be allowed","ich darf / du darfst"),
    ("sollen",        "zol-en",         "should / to be supposed to","ich soll / du sollst"),
    ("mögen",         "mur-gen",        "to like",           "ich mag / du magst"),
    ("gehen",         "gay-en",         "to go",             "ich gehe / du gehst"),
    ("kommen",        "kom-en",         "to come",           "ich komme / du kommst"),
    ("machen",        "makh-en",        "to do/make",        "ich mache / du machst"),
    ("sagen",         "zah-gen",        "to say",            "ich sage / du sagst"),
    ("geben",         "gay-ben",        "to give",           "ich gebe / du gibst"),
    ("nehmen",        "nay-men",        "to take",           "ich nehme / du nimmst"),
    ("sehen",         "zay-en",         "to see",            "ich sehe / du siehst"),
    ("wissen",        "vis-en",         "to know (fact)",    "ich weiß / du weißt"),
    ("kennen",        "ken-en",         "to know (person)",  "ich kenne / du kennst"),
    ("denken",        "denk-en",        "to think",          "ich denke / du denkst"),
    ("sprechen",      "shprekh-en",     "to speak",          "ich spreche / du sprichst"),
    ("hören",         "hur-en",         "to hear",           "ich höre / du hörst"),
    ("essen",         "es-en",          "to eat",            "ich esse / du isst"),
    ("trinken",       "trink-en",       "to drink",          "ich trinke / du trinkst"),
    ("schlafen",      "shlah-fen",      "to sleep",          "ich schlafe / du schläfst"),
    ("arbeiten",      "ar-bay-ten",     "to work",           "ich arbeite / du arbeitest"),
    ("lernen",        "lair-nen",       "to learn",          "ich lerne / du lernst"),
    ("lesen",         "lay-zen",        "to read",           "ich lese / du liest"),
    ("schreiben",     "shray-ben",      "to write",          "ich schreibe / du schreibst"),
    ("kaufen",        "kow-fen",        "to buy",            "ich kaufe / du kaufst"),
    ("verkaufen",     "fair-kow-fen",   "to sell",           "ich verkaufe / du verkaufst"),
    ("helfen",        "hel-fen",        "to help",           "ich helfe / du hilfst"),
    ("fragen",        "frah-gen",       "to ask",            "ich frage / du fragst"),
    ("antworten",     "ant-vor-ten",    "to answer",         "ich antworte / du antwortest"),
    ("finden",        "fin-den",        "to find",           "ich finde / du findest"),
    ("suchen",        "zoo-khen",       "to search",         "ich suche / du suchst"),
    ("wohnen",        "voh-nen",        "to live/reside",    "ich wohne / du wohnst"),
    ("fahren",        "fah-ren",        "to drive/travel",   "ich fahre / du fährst"),
    ("fliegen",       "flee-gen",       "to fly",            "ich fliege / du fliegst"),
    ("laufen",        "low-fen",        "to run/walk",       "ich laufe / du läufst"),
    ("stehen",        "shtay-en",       "to stand",          "ich stehe / du stehst"),
    ("sitzen",        "zit-sen",        "to sit",            "ich sitze / du sitzt"),
    ("liegen",        "lee-gen",        "to lie (down)",     "ich liege / du liegst"),
    ("öffnen",        "urf-nen",        "to open",           "ich öffne / du öffnest"),
    ("schließen",     "shlee-sen",      "to close",          "ich schließe / du schließt"),
    ("bringen",       "bring-en",       "to bring",          "ich bringe / du bringst"),
    ("halten",        "hal-ten",        "to hold/stop",      "ich halte / du hältst"),
    ("lassen",        "las-en",         "to let/leave",      "ich lasse / du lässt"),
    ("spielen",       "shpee-len",      "to play",           "ich spiele / du spielst"),
    ("lieben",        "lee-ben",        "to love",           "ich liebe / du liebst"),
    ("leben",         "lay-ben",        "to live",           "ich lebe / du lebst"),
    ("sterben",       "shtair-ben",     "to die",            "ich sterbe / du stirbst"),
    ("warten",        "var-ten",        "to wait",           "ich warte / du wartest"),
    ("beginnen",      "beh-gin-en",     "to begin",          "ich beginne / du beginnst"),
    ("enden",         "en-den",         "to end",            "ich ende / du endest"),
    ("verstehen",     "fair-shtay-en",  "to understand",     "ich verstehe / du verstehst"),
    ("erklären",      "air-klair-en",   "to explain",        "ich erkläre / du erklärst"),
    ("zeigen",        "tsay-gen",       "to show",           "ich zeige / du zeigst"),
    ("starten",       "shtar-ten",      "to start",          "ich starte / du startest"),
    ("zählen",        "tsay-len",       "to count",          "ich zähle / du zählst"),
    ("bezahlen",      "beh-tsah-len",   "to pay",            "ich bezahle / du bezahlst"),
    ("kochen",        "kokh-en",        "to cook",           "ich koche / du kochst"),
    ("waschen",       "vash-en",        "to wash",           "ich wasche / du wäschst"),
]

PREVERBS = [
    ("ab-",    "ap",       "off / away",         "abfahren – to depart"),
    ("an-",    "an",       "on / at / to",       "ankommen – to arrive"),
    ("auf-",   "owf",      "up / open",          "aufmachen – to open"),
    ("aus-",   "ows",      "out / off",          "ausgehen – to go out"),
    ("be-",    "beh",      "to affect directly (insep.)", "besuchen – to visit"),
    ("bei-",   "bay",      "with / alongside",   "beistehen – to stand by"),
    ("ein-",   "ayn",      "in / into",          "eintreten – to enter"),
    ("emp-",   "emp",      "receives (insep.)",  "empfangen – to receive"),
    ("ent-",   "ent",      "away / removal (insep.)", "entfernen – to remove"),
    ("er-",    "air",      "resultative (insep.)","erklären – to explain"),
    ("ge-",    "geh",      "past participle marker (insep.)", "gemacht – made"),
    ("her-",   "hair",     "towards speaker",    "herkommen – to come here"),
    ("hin-",   "hin",      "away from speaker",  "hingehen – to go there"),
    ("miss-",  "mis",      "mis- / wrong",       "missverstehen – to misunderstand"),
    ("mit-",   "mit",      "with / along",       "mitnehmen – to take along"),
    ("nach-",  "nakh",     "after / following",  "nachahmen – to imitate"),
    ("um-",    "oom",      "around / over (sep.); re- (insep.)", "umbauen – to rebuild"),
    ("unter-", "oon-ter",  "under / sub- (insep.)", "untersuchen – to examine"),
    ("ver-",   "fair",     "transforms / worsens (insep.)", "vergessen – to forget"),
    ("vor-",   "for",      "before / pre-",      "vorstellen – to introduce"),
    ("weg-",   "vek",      "away",               "weggehen – to go away"),
    ("wieder-","vee-der",  "again / re-",        "wiederholen – to repeat"),
    ("zer-",   "tsair",    "apart / to pieces (insep.)", "zerbrechen – to break apart"),
    ("zu-",    "tsoo",     "to / closed",        "zumachen – to close"),
    ("zurück-","tsoo-rewk","back",               "zurückgehen – to go back"),
    ("zusammen-","tsoo-zam-en","together",       "zusammenarbeiten – to work together"),
]

PREPOSITIONS = [
    ("an",        "an",         "at / on / to",          "Dative or Accusative"),
    ("auf",       "owf",        "on / onto / at",        "Dative or Accusative"),
    ("aus",       "ows",        "out of / from",         "Dative"),
    ("außer",     "ow-ser",     "except / besides",      "Dative"),
    ("bei",       "bay",        "at / near / with",      "Dative"),
    ("bis",       "bis",        "until / up to",         "Accusative"),
    ("durch",     "dookh",      "through / by",          "Accusative"),
    ("entlang",   "ent-lang",   "along",                 "Accusative (postpos.)"),
    ("für",       "fewr",       "for",                   "Accusative"),
    ("gegen",     "gay-gen",    "against / around",      "Accusative"),
    ("gegenüber", "gay-gen-ew-ber","opposite / across",  "Dative"),
    ("hinter",    "hin-ter",    "behind",                "Dative or Accusative"),
    ("in",        "in",         "in / into",             "Dative or Accusative"),
    ("mit",       "mit",        "with / by (transport)", "Dative"),
    ("nach",      "nakh",       "after / to (place)",    "Dative"),
    ("neben",     "nay-ben",    "next to / beside",      "Dative or Accusative"),
    ("ohne",      "oh-neh",     "without",               "Accusative"),
    ("seit",      "zayt",       "since / for (time)",    "Dative"),
    ("statt",     "shtat",      "instead of",            "Genitive"),
    ("über",      "ew-ber",     "over / above / about",  "Dative or Accusative"),
    ("um",        "oom",        "around / at (time)",    "Accusative"),
    ("unter",     "oon-ter",    "under / among",         "Dative or Accusative"),
    ("von",       "fon",        "from / of / by",        "Dative"),
    ("vor",       "for",        "in front of / ago",     "Dative or Accusative"),
    ("während",   "vay-rent",   "during",                "Genitive"),
    ("wegen",     "vay-gen",    "because of",            "Genitive"),
    ("zu",        "tsoo",       "to / at",               "Dative"),
    ("zwischen",  "tsvish-en",  "between",               "Dative or Accusative"),
    ("innerhalb", "in-er-halp", "inside / within",       "Genitive"),
    ("außerhalb", "ow-ser-halp","outside / beyond",      "Genitive"),
]

CONJUNCTIONS = [
    ("aber",         "ah-ber",        "but / however",          "coordinating"),
    ("als",          "ahls",          "when / than (past)",     "subordinating"),
    ("also",         "al-zoh",        "so / therefore",         "coordinating"),
    ("bevor",        "beh-for",       "before",                 "subordinating"),
    ("bis",          "bis",           "until",                  "subordinating"),
    ("da",           "dah",           "since / because",        "subordinating"),
    ("damit",        "dah-mit",       "so that",                "subordinating"),
    ("dann",         "dahn",          "then",                   "adverbial conj."),
    ("dass",         "dahs",          "that",                   "subordinating"),
    ("denn",         "den",           "because / for",          "coordinating"),
    ("deshalb",      "des-halp",      "therefore / that's why", "adverbial conj."),
    ("entweder...oder","ent-vay-der...oh-der","either...or",   "correlative"),
    ("falls",        "fahls",         "in case / if",           "subordinating"),
    ("jedoch",       "yeh-dokh",      "however",                "adverbial conj."),
    ("nachdem",      "nakh-daym",     "after",                  "subordinating"),
    ("nicht nur...sondern auch","nikht noor...zon-dern owkh","not only...but also","correlative"),
    ("ob",           "op",            "whether / if",           "subordinating"),
    ("obwohl",       "op-vohl",       "although / even though", "subordinating"),
    ("oder",         "oh-der",        "or",                     "coordinating"),
    ("seit / seitdem","zayt/zayt-daym","since",                 "subordinating"),
    ("sodass",       "zoh-dahs",      "so that (result)",       "subordinating"),
    ("sobald",       "zoh-bahlt",     "as soon as",             "subordinating"),
    ("sofern",       "zoh-fairn",     "provided that",          "subordinating"),
    ("solange",      "zoh-lang-eh",   "as long as",             "subordinating"),
    ("sondern",      "zon-dern",      "but rather",             "coordinating"),
    ("sowohl...als auch","zoh-vohl...ahls owkh","both...and",  "correlative"),
    ("trotzdem",     "trots-daym",    "nevertheless",           "adverbial conj."),
    ("und",          "oont",          "and",                    "coordinating"),
    ("weil",         "vayl",          "because",                "subordinating"),
    ("wenn",         "ven",           "when / if (present)",    "subordinating"),
    ("während",      "vay-rent",      "while / whereas",        "subordinating"),
    ("weder...noch", "vay-der...nokh","neither...nor",          "correlative"),
    ("wie",          "vee",           "as / like / how",        "subordinating"),
    ("wo",           "voh",           "where",                  "subordinating"),
]

INTERJECTIONS = [
    ("Ach!",         "akh",          "Oh! / Ah! (mild regret)"),
    ("Ach so!",      "akh zoh",      "Oh I see! / Ah right!"),
    ("Au! / Aua!",   "ow / ow-ah",   "Ouch!"),
    ("Bitte!",       "bit-eh",       "Please! / Here you go! / Pardon?"),
    ("Bravo!",       "brah-voh",     "Bravo! / Well done!"),
    ("Bäh!",         "beh",          "Yuck! / Blech!"),
    ("Danke!",       "dank-eh",      "Thank you!"),
    ("Doch!",        "dokh",         "Yes it is! (contradicting negative)"),
    ("Echt?",        "ekht",         "Really? / Seriously?"),
    ("Egal!",        "eh-gahl",      "Doesn't matter! / Whatever!"),
    ("Gott sei Dank!","got zay dank","Thank God!"),
    ("Hallo!",       "hah-loh",      "Hello!"),
    ("Hey!",         "hey",          "Hey!"),
    ("Hilfe!",       "hil-feh",      "Help!"),
    ("Hmm",          "hm",           "Hmm (thinking)"),
    ("Hurra!",       "hoo-rah",      "Hooray!"),
    ("Ja!",          "yah",          "Yes!"),
    ("Nein!",        "nayn",         "No!"),
    ("Naja",         "nah-yah",      "Well... / Sort of"),
    ("Na!",          "nah",          "Well! / Come on!"),
    ("Oh!",          "oh",           "Oh!"),
    ("Prost!",       "prohst",       "Cheers! (toasting)"),
    ("Schade!",      "shah-deh",     "What a pity! / Too bad!"),
    ("Super!",       "zoo-per",      "Super! / Great!"),
    ("Toll!",        "tol",          "Great! / Awesome!"),
    ("Tschüss!",     "chews",        "Bye! (informal)"),
    ("Ui!",          "ooi",          "Wow! / Ooh! (surprise)"),
    ("Ups!",         "oops",         "Oops!"),
    ("Vorsicht!",    "for-zikht",    "Careful! / Watch out!"),
    ("Wunderbar!",   "voon-der-bar", "Wonderful!"),
]

ADVERBS = [
    ("auch",         "owkh",        "also / too"),
    ("außerdem",     "ow-ser-daym", "besides / moreover"),
    ("bald",         "bahlt",       "soon"),
    ("bereits",      "beh-rayts",   "already"),
    ("besonders",    "beh-zon-ders","especially"),
    ("dann",         "dahn",        "then"),
    ("danach",       "dah-nakh",    "afterwards"),
    ("davor",        "dah-for",     "before that"),
    ("deshalb",      "des-halp",    "therefore"),
    ("dort",         "dort",        "there"),
    ("endlich",      "end-likh",    "finally / at last"),
    ("fast",         "fahst",       "almost"),
    ("ganz",         "gahnts",      "quite / entirely"),
    ("genauso",      "geh-now-zoh", "just as / equally"),
    ("gerne",        "gair-neh",    "gladly / with pleasure"),
    ("gestern",      "ges-tern",    "yesterday"),
    ("heute",        "hoy-teh",     "today"),
    ("hier",         "heer",        "here"),
    ("immer",        "im-er",       "always"),
    ("jetzt",        "yetst",       "now"),
    ("leider",       "lay-der",     "unfortunately"),
    ("manchmal",     "manch-mahl",  "sometimes"),
    ("meistens",     "mays-tens",   "mostly / usually"),
    ("mehr",         "mayr",        "more"),
    ("morgen",       "mor-gen",     "tomorrow"),
    ("nie",          "nee",         "never"),
    ("noch",         "nokh",        "still / yet"),
    ("normalerweise","nor-mahl-er-vay-seh","normally"),
    ("nun",          "noon",        "now (formal)"),
    ("nur",          "noor",        "only / just"),
    ("oft",          "oft",         "often"),
    ("plötzlich",    "plurts-likh", "suddenly"),
    ("schon",        "shohn",       "already"),
    ("sehr",         "zayr",        "very"),
    ("selten",       "zel-ten",     "rarely"),
    ("so",           "zoh",         "so / thus"),
    ("sofort",       "zoh-fort",    "immediately"),
    ("trotzdem",     "trots-daym",  "nevertheless"),
    ("überall",      "ew-ber-al",   "everywhere"),
    ("viel",         "feel",        "much / a lot"),
    ("vielleicht",   "feel-aykt",   "maybe / perhaps"),
    ("wenig",        "vay-nikh",    "little / few"),
    ("wieder",       "vee-der",     "again"),
    ("wirklich",     "virk-likh",   "really / truly"),
    ("zusammen",     "tsoo-zam-en", "together"),
    ("zuerst",       "tsoo-ayrst",  "first of all"),
    ("zuletzt",      "tsoo-letst",  "lastly / in the end"),
    ("ziemlich",     "tseem-likh",  "quite / fairly"),
    ("zweimal",      "tsvay-mahl",  "twice"),
]

ADJECTIVES = [
    ("alt",          "ahlt",        "old"),
    ("jung",         "yoong",       "young"),
    ("neu",          "noy",         "new"),
    ("groß",         "grohs",       "big / tall"),
    ("klein",        "klayn",       "small / little"),
    ("lang",         "lang",        "long / tall"),
    ("kurz",         "koorts",      "short"),
    ("gut",          "goot",        "good"),
    ("schlecht",     "shlekhkt",    "bad"),
    ("schön",        "shurn",       "beautiful / nice"),
    ("hässlich",     "hes-likh",    "ugly"),
    ("stark",        "shtark",      "strong"),
    ("schwach",      "shvakh",      "weak"),
    ("schnell",      "shnel",       "fast / quick"),
    ("langsam",      "lang-zahm",   "slow"),
    ("leicht",       "laykt",       "light / easy"),
    ("schwer",       "shvayr",      "heavy / difficult"),
    ("einfach",      "ayn-fakh",    "simple / easy"),
    ("schwierig",    "shvee-rikh",  "difficult"),
    ("wichtig",      "vikh-tikh",   "important"),
    ("richtig",      "rikh-tikh",   "right / correct"),
    ("falsch",       "falsh",       "wrong / false"),
    ("wahr",         "vahr",        "true"),
    ("klar",         "klahr",       "clear"),
    ("warm",         "varm",        "warm"),
    ("kalt",         "kahlt",       "cold"),
    ("heiß",         "hays",        "hot"),
    ("kühl",         "kewl",        "cool"),
    ("laut",         "lowt",        "loud"),
    ("leise",        "lay-zeh",     "quiet / soft"),
    ("frei",         "fray",        "free"),
    ("teuer",        "toy-er",      "expensive"),
    ("billig",       "bil-ikh",     "cheap"),
    ("sauber",       "zow-ber",     "clean"),
    ("schmutzig",    "shmoot-tsikh","dirty"),
    ("müde",         "mew-deh",     "tired"),
    ("wach",         "vakh",        "awake"),
    ("glücklich",    "glewk-likh",  "happy"),
    ("traurig",      "trow-rikh",   "sad"),
    ("hungrig",      "hoong-rikh",  "hungry"),
    ("durstig",      "doorst-ikh",  "thirsty"),
    ("krank",        "krank",       "sick / ill"),
    ("gesund",       "geh-zoont",   "healthy"),
    ("neu",          "noy",         "new"),
    ("ganz",         "gahnts",      "whole / complete"),
    ("gleich",       "glaykhk",     "same / equal"),
    ("anders",       "an-ders",     "different"),
    ("möglich",      "murg-likh",   "possible"),
    ("unmöglich",    "oon-murg-likh","impossible"),
    ("nett",         "net",         "nice / kind"),
    ("freundlich",   "froynt-likh", "friendly"),
]

WORDS_500 = [
    # ESSENTIALS & GREETINGS
    ("Hallo",          "hah-loh",         "Hello"),
    ("Guten Morgen",   "goo-ten mor-gen", "Good morning"),
    ("Guten Tag",      "goo-ten tahk",    "Good day / Hello"),
    ("Guten Abend",    "goo-ten ah-bent",  "Good evening"),
    ("Gute Nacht",     "goo-teh nakht",   "Good night"),
    ("Tschüss",        "chews",           "Bye (informal)"),
    ("Auf Wiedersehen","owf vee-der-zayn","Goodbye (formal)"),
    ("Bitte",          "bit-eh",          "Please / You're welcome"),
    ("Danke",          "dank-eh",         "Thank you"),
    ("Danke schön",    "dank-eh shurn",   "Thank you very much"),
    ("Bitte schön",    "bit-eh shurn",    "You're very welcome"),
    ("Entschuldigung", "ent-shool-di-goong","Excuse me / Sorry"),
    ("Es tut mir leid","es toot meer layt","I'm sorry"),
    ("Kein Problem",   "kayn proh-blaym", "No problem"),
    ("Ja",             "yah",             "Yes"),
    ("Nein",           "nayn",            "No"),
    ("Vielleicht",     "feel-aykt",       "Maybe / Perhaps"),
    ("Ich verstehe",   "ikh fair-shtay-eh","I understand"),
    ("Ich verstehe nicht","ikh fair-shtay-eh nikht","I don't understand"),
    ("Sprechen Sie Englisch?","shprekh-en zee eng-lish","Do you speak English?"),
    ("Ich spreche Deutsch","ikh shprekh-eh doych","I speak German"),
    ("Wie bitte?",     "vee bit-eh",      "Pardon? / Come again?"),
    ("Können Sie das wiederholen?","kur-nen zee dahs vee-der-hoh-len","Can you repeat that?"),
    ("Langsamer bitte","lang-zahm-er bit-eh","Slower please"),

    # WATER, NATURE & BASIC NEEDS
    ("Wasser",         "vah-ser",         "water"),
    ("Essen",          "es-en",           "food"),
    ("Brot",           "broht",           "bread"),
    ("Milch",          "milkh",           "milk"),
    ("Suppe",          "zoo-peh",         "soup"),
    ("Fleisch",        "flaysh",          "meat"),
    ("Obst",           "ohpst",           "fruit"),
    ("Gemüse",         "geh-mew-zeh",     "vegetables"),
    ("Salz",           "zahlt",           "salt"),
    ("Zucker",         "tsoo-ker",        "sugar"),
    ("Öl",             "url",             "oil"),
    ("Kaffee",         "kah-fay",         "coffee"),
    ("Tee",            "tay",             "tea"),
    ("Bier",           "beer",            "beer"),
    ("Wein",           "vayn",            "wine"),
    ("Saft",           "zahft",           "juice"),
    ("Luft",           "looft",           "air"),
    ("Erde",           "air-deh",         "earth / ground / soil"),
    ("Feuer",          "foy-er",          "fire"),
    ("Licht",          "likht",           "light"),
    ("Schatten",       "shah-ten",        "shadow / shade"),
    ("Wärme",          "vair-meh",        "warmth / heat"),
    ("Kälte",          "kelt-eh",         "cold (noun)"),

    # ROAD, TRANSPORT & DIRECTIONS
    ("Straße",         "shtrah-seh",      "road / street"),
    ("Weg",            "vayk",            "way / path"),
    ("Autobahn",       "ow-toh-bahn",     "motorway / highway"),
    ("Kreuzung",       "kroyts-oong",     "intersection / crossroads"),
    ("Ampel",          "am-pel",          "traffic light"),
    ("Brücke",         "brew-keh",        "bridge"),
    ("Tunnel",         "too-nel",         "tunnel"),
    ("Bahnhof",        "bahn-hohf",       "train station"),
    ("Flughafen",      "flook-hah-fen",   "airport"),
    ("Bushaltestelle", "boos-hal-teh-shtel-eh","bus stop"),
    ("U-Bahn",         "oo-bahn",         "subway / underground"),
    ("Bus",            "boos",            "bus"),
    ("Taxi",           "tak-see",         "taxi"),
    ("Fahrrad",        "fahr-raht",       "bicycle"),
    ("Auto",           "ow-toh",          "car"),
    ("Motorrad",       "moh-tor-raht",    "motorcycle"),
    ("Zug",            "tsook",           "train"),
    ("Schiff",         "shif",            "ship"),
    ("Flugzeug",       "flook-tsoyg",     "airplane"),
    ("Ticket",         "tik-et",          "ticket"),
    ("Fahrkarte",      "fahr-kar-teh",    "travel ticket"),
    ("Links",          "links",           "left"),
    ("Rechts",         "rekhts",          "right"),
    ("Geradeaus",      "geh-rah-deh-ows", "straight ahead"),
    ("Norden",         "nor-den",         "north"),
    ("Süden",          "zew-den",         "south"),
    ("Osten",          "os-ten",          "east"),
    ("Westen",         "ves-ten",         "west"),
    ("Karte",          "kar-teh",         "map"),
    ("Entfernung",     "ent-fair-noong",  "distance"),
    ("Kilometer",      "kee-loh-may-ter", "kilometer"),

    # PLACES
    ("Hotel",          "hoh-tel",         "hotel"),
    ("Restaurant",     "res-tow-rant",    "restaurant"),
    ("Café",           "kah-fay",         "café"),
    ("Markt",          "markt",           "market"),
    ("Supermarkt",     "zoo-per-markt",   "supermarket"),
    ("Geschäft",       "geh-sheft",       "shop / store"),
    ("Apotheke",       "ah-poh-tay-keh",  "pharmacy"),
    ("Krankenhaus",    "krank-en-hows",   "hospital"),
    ("Polizei",        "poh-li-tsay",     "police"),
    ("Feuerwehr",      "foy-er-vayr",     "fire department"),
    ("Bank",           "bank",            "bank"),
    ("Post",           "post",            "post office"),
    ("Bibliothek",     "bib-lee-oh-tayk", "library"),
    ("Museum",         "moo-zay-oom",     "museum"),
    ("Park",           "park",            "park"),
    ("Kirche",         "keer-kheh",       "church"),
    ("Schule",         "shoo-leh",        "school"),
    ("Universität",    "oo-ni-vair-zi-tayt","university"),
    ("Büro",           "bew-roh",         "office"),
    ("Fabrik",         "fah-breek",       "factory"),
    ("Strand",         "shtrant",         "beach"),
    ("See",            "zay",             "lake"),
    ("Fluss",          "floos",           "river"),
    ("Meer",           "mayr",            "sea / ocean"),
    ("Berg",           "bairk",           "mountain"),
    ("Tal",            "tahl",            "valley"),
    ("Feld",           "felt",            "field"),
    ("Wald",           "vahlt",           "forest"),
    ("Garten",         "gar-ten",         "garden"),

    # BODY
    ("Körper",         "kur-per",         "body"),
    ("Kopf",           "kopf",            "head"),
    ("Haar",           "hahr",            "hair"),
    ("Gesicht",        "geh-zikht",       "face"),
    ("Stirn",          "shtirn",          "forehead"),
    ("Auge",           "ow-geh",          "eye"),
    ("Ohr",            "or",              "ear"),
    ("Nase",           "nah-zeh",         "nose"),
    ("Mund",           "moont",           "mouth"),
    ("Zahn",           "tsahn",           "tooth"),
    ("Zunge",          "tsoong-eh",       "tongue"),
    ("Lippe",          "lip-eh",          "lip"),
    ("Hals",           "hahls",           "neck / throat"),
    ("Schulter",       "shool-ter",       "shoulder"),
    ("Arm",            "arm",             "arm"),
    ("Ellbogen",       "el-boh-gen",      "elbow"),
    ("Handgelenk",     "hahnt-geh-lenk",  "wrist"),
    ("Hand",           "hahnt",           "hand"),
    ("Finger",         "fing-er",         "finger"),
    ("Daumen",         "dow-men",         "thumb"),
    ("Nagel",          "nah-gel",         "nail"),
    ("Brust",          "broost",          "chest"),
    ("Rücken",         "rew-ken",         "back"),
    ("Bauch",          "bowkh",           "belly / stomach"),
    ("Hüfte",          "hewf-teh",        "hip"),
    ("Bein",           "bayn",            "leg"),
    ("Knie",           "k-nee",           "knee"),
    ("Fuß",            "foos",            "foot"),
    ("Zehe",           "tsay-eh",         "toe"),
    ("Herz",           "hairts",          "heart"),
    ("Lunge",          "loong-eh",        "lung"),
    ("Magen",          "mah-gen",         "stomach"),
    ("Blut",           "bloot",           "blood"),
    ("Haut",           "howt",            "skin"),
    ("Knochen",        "kno-khen",        "bone"),

    # FAMILY & PEOPLE
    ("Familie",        "fah-meel-yeh",    "family"),
    ("Eltern",         "el-tern",         "parents"),
    ("Vater",          "fah-ter",         "father"),
    ("Mutter",         "moo-ter",         "mother"),
    ("Sohn",           "zohn",            "son"),
    ("Tochter",        "tokh-ter",        "daughter"),
    ("Kind",           "kint",            "child"),
    ("Geschwister",    "geh-shvis-ter",   "siblings"),
    ("Bruder",         "broo-der",        "brother"),
    ("Schwester",      "shves-ter",       "sister"),
    ("Großvater",      "grohs-fah-ter",   "grandfather"),
    ("Großmutter",     "grohs-moo-ter",   "grandmother"),
    ("Enkel",          "en-kel",          "grandson/grandchild"),
    ("Enkelin",        "en-kel-in",       "granddaughter"),
    ("Onkel",          "on-kel",          "uncle"),
    ("Tante",          "tan-teh",         "aunt"),
    ("Cousin",         "koo-zan",         "cousin (m)"),
    ("Cousine",        "koo-zee-neh",     "cousin (f)"),
    ("Mann",           "mahn",            "man / husband"),
    ("Frau",           "frow",            "woman / wife"),
    ("Junge",          "yoong-eh",        "boy"),
    ("Mädchen",        "mayt-khen",       "girl"),
    ("Baby",           "bay-bee",         "baby"),
    ("Freund",         "froynt",          "friend (m) / boyfriend"),
    ("Freundin",       "froyn-din",       "friend (f) / girlfriend"),
    ("Nachbar",        "nakh-bar",        "neighbor (m)"),
    ("Kollege",        "ko-lay-geh",      "colleague (m)"),
    ("Chef",           "shef",            "boss"),

    # HOUSE & HOME
    ("Haus",           "hows",            "house"),
    ("Wohnung",        "voh-noong",       "apartment"),
    ("Zimmer",         "tsim-er",         "room"),
    ("Schlafzimmer",   "shlahf-tsim-er",  "bedroom"),
    ("Wohnzimmer",     "vohn-tsim-er",    "living room"),
    ("Küche",          "kew-kheh",        "kitchen"),
    ("Badezimmer",     "bah-deh-tsim-er", "bathroom"),
    ("Toilette",       "toa-let-eh",      "toilet"),
    ("Keller",         "kel-er",          "basement / cellar"),
    ("Dach",           "dakh",            "roof"),
    ("Boden",          "boh-den",         "floor / ground"),
    ("Wand",           "vahnt",           "wall"),
    ("Decke",          "dek-eh",          "ceiling"),
    ("Tür",            "tewr",            "door"),
    ("Fenster",        "fen-ster",        "window"),
    ("Treppe",         "trep-eh",         "stairs"),
    ("Aufzug",         "owf-tsook",       "elevator / lift"),
    ("Schlüssel",      "shlew-sel",       "key"),
    ("Lampe",          "lam-peh",         "lamp"),
    ("Tisch",          "tish",            "table"),
    ("Stuhl",          "shtool",          "chair"),
    ("Sofa",           "zoh-fah",         "sofa"),
    ("Bett",           "bet",             "bed"),
    ("Schrank",        "shrank",          "wardrobe / cupboard"),
    ("Regal",          "reh-gahl",        "shelf"),

    # TIME
    ("Zeit",           "tsayt",           "time"),
    ("Uhr",            "oor",             "clock / o'clock"),
    ("Minute",         "mi-noo-teh",      "minute"),
    ("Stunde",         "shtoon-deh",      "hour"),
    ("Tag",            "tahk",            "day"),
    ("Nacht",          "nakht",           "night"),
    ("Woche",          "voh-kheh",        "week"),
    ("Monat",          "moh-naht",        "month"),
    ("Jahr",           "yahr",            "year"),
    ("Heute",          "hoy-teh",         "today"),
    ("Morgen",         "mor-gen",         "tomorrow / morning"),
    ("Gestern",        "ges-tern",        "yesterday"),
    ("Früh",           "frew",            "early / morning"),
    ("Abend",          "ah-bent",         "evening"),
    ("Mittag",         "mit-tahk",        "noon / midday"),
    ("Mitternacht",    "mit-er-nakht",    "midnight"),
    ("Jetzt",          "yetst",           "now"),
    ("Bald",           "bahlt",           "soon"),
    ("Immer",          "im-er",           "always"),
    ("Nie",            "nee",             "never"),
    ("Oft",            "oft",             "often"),
    ("Manchmal",       "manch-mahl",      "sometimes"),
    ("Montag",         "mohn-tahk",       "Monday"),
    ("Dienstag",       "deens-tahk",      "Tuesday"),
    ("Mittwoch",       "mit-vokh",        "Wednesday"),
    ("Donnerstag",     "don-ers-tahk",    "Thursday"),
    ("Freitag",        "fray-tahk",       "Friday"),
    ("Samstag",        "zahms-tahk",      "Saturday"),
    ("Sonntag",        "zon-tahk",        "Sunday"),
    ("Januar",         "yah-noo-ar",      "January"),
    ("Februar",        "fay-broo-ar",     "February"),
    ("März",           "mairts",          "March"),
    ("April",          "ah-pril",         "April"),
    ("Mai",            "my",              "May"),
    ("Juni",           "yoo-nee",         "June"),
    ("Juli",           "yoo-lee",         "July"),
    ("August",         "ow-goost",        "August"),
    ("September",      "sep-tem-ber",     "September"),
    ("Oktober",        "ok-toh-ber",      "October"),
    ("November",       "noh-vem-ber",     "November"),
    ("Dezember",       "deh-tsem-ber",    "December"),

    # WEATHER
    ("Wetter",         "vet-er",          "weather"),
    ("Sonne",          "zon-eh",          "sun"),
    ("Regen",          "ray-gen",         "rain"),
    ("Schnee",         "shnay",           "snow"),
    ("Wind",           "vint",            "wind"),
    ("Sturm",          "shtoorm",         "storm"),
    ("Nebel",          "nay-bel",         "fog / mist"),
    ("Gewitter",       "geh-vit-er",      "thunderstorm"),
    ("Wolke",          "vol-keh",         "cloud"),
    ("Eis",            "ays",             "ice"),
    ("Frost",          "frost",           "frost"),
    ("Temperatur",     "tem-peh-rah-toor","temperature"),
    ("Grad",           "grahd",           "degree"),
    ("Es regnet",      "es rayg-net",     "It is raining"),
    ("Es schneit",     "es shnayt",       "It is snowing"),

    # COLORS
    ("rot",            "roht",            "red"),
    ("blau",           "blow",            "blue"),
    ("grün",           "grewn",           "green"),
    ("gelb",           "gelp",            "yellow"),
    ("orange",         "oh-ran-zheh",     "orange"),
    ("lila / violett", "lee-lah / vee-oh-let","purple / violet"),
    ("rosa",           "roh-zah",         "pink"),
    ("braun",          "brown",           "brown"),
    ("schwarz",        "shvarts",         "black"),
    ("weiß",           "vayss",           "white"),
    ("grau",           "grow",            "grey"),
    ("golden",         "gol-den",         "golden"),
    ("silbern",        "zil-bern",        "silver"),

    # SCHOOL & LEARNING
    ("Schule",         "shoo-leh",        "school"),
    ("Lehrer",         "lay-rer",         "teacher (m)"),
    ("Lehrerin",       "lay-rer-in",      "teacher (f)"),
    ("Schüler",        "shew-ler",        "student/pupil (m)"),
    ("Klasse",         "klas-eh",         "class"),
    ("Unterricht",     "oon-ter-rikht",   "lesson / instruction"),
    ("Prüfung",        "prew-foong",      "exam / test"),
    ("Hausaufgabe",    "hows-owf-gah-beh","homework"),
    ("Buch",           "bookh",           "book"),
    ("Heft",           "heft",            "notebook"),
    ("Stift",          "shtift",          "pen / pencil"),
    ("Tafel",          "tah-fel",         "blackboard"),
    ("Wörterbuch",     "vur-ter-bookh",   "dictionary"),
    ("Sprache",        "shprah-kheh",     "language"),
    ("Grammatik",      "grah-mah-tik",    "grammar"),
    ("Aussprache",     "ows-shprah-kheh", "pronunciation"),
    ("Vokabular",      "voh-kah-boo-lahr","vocabulary"),
    ("Alphabet",       "al-fah-bayt",     "alphabet"),

    # HEALTH
    ("Arzt",           "artst",           "doctor (m)"),
    ("Ärztin",         "airts-tin",       "doctor (f)"),
    ("Krankenschwester","krank-en-shves-ter","nurse"),
    ("Medikament",     "meh-di-kah-ment", "medication"),
    ("Tablette",       "tah-blet-eh",     "tablet / pill"),
    ("Schmerz",        "shmairts",        "pain"),
    ("Fieber",         "fee-ber",         "fever"),
    ("Erkältung",      "air-kel-toong",   "cold (illness)"),
    ("Grippe",         "grip-eh",         "flu / influenza"),
    ("Allergie",       "al-air-gee",      "allergy"),
    ("Impfung",        "impf-oong",       "vaccination"),
    ("Notfall",        "noht-fal",        "emergency"),
    ("Ambulanz",       "am-boo-lants",    "ambulance / ER"),
    ("Operation",      "op-eh-rah-tsyohn","operation / surgery"),

    # SHOPPING & MONEY
    ("Geld",           "gelt",            "money"),
    ("Euro",           "oy-roh",          "euro"),
    ("Cent",           "tsent",           "cent"),
    ("Preis",          "prays",           "price"),
    ("Rechnung",       "rekh-noong",      "bill / invoice"),
    ("Quittung",       "kvit-oong",       "receipt"),
    ("Rabatt",         "rah-baht",        "discount"),
    ("Angebot",        "an-geh-boht",     "offer / deal"),
    ("Kasse",          "kas-eh",          "checkout / cash register"),
    ("Kredit",         "kreh-dit",        "credit"),
    ("Bargeld",        "bar-gelt",        "cash"),
    ("Kaufen",         "kow-fen",         "to buy"),
    ("Verkaufen",      "fair-kow-fen",    "to sell"),
    ("Kosten",         "kos-ten",         "to cost / costs"),

    # WORK & PROFESSIONS
    ("Arbeit",         "ar-bayt",         "work / job"),
    ("Beruf",          "beh-roof",        "profession"),
    ("Büro",           "bew-roh",         "office"),
    ("Firma",          "feer-mah",        "company / firm"),
    ("Chef",           "shef",            "boss"),
    ("Mitarbeiter",    "mit-ar-bay-ter",  "employee / colleague"),
    ("Gehalt",         "geh-hahlt",       "salary"),
    ("Urlaub",         "oor-lowp",        "vacation / holiday"),
    ("Ingenieur",      "in-zheh-nyur",    "engineer"),
    ("Anwalt",         "an-vahlt",        "lawyer"),
    ("Polizist",       "poh-li-tsist",    "police officer (m)"),
    ("Koch",           "kokh",            "cook / chef (m)"),
    ("Fahrer",         "fah-rer",         "driver"),
    ("Bauer",          "bow-er",          "farmer"),
    ("Kellner",        "kel-ner",         "waiter (m)"),

    # TECHNOLOGY
    ("Computer",       "kom-pyoo-ter",    "computer"),
    ("Handy",          "hen-dee",         "mobile phone"),
    ("Telefon",        "teh-leh-fohn",    "telephone"),
    ("Internet",       "in-ter-net",      "internet"),
    ("E-Mail",         "ee-mayl",         "email"),
    ("Passwort",       "pas-vort",        "password"),
    ("Bildschirm",     "bilt-shirm",      "screen / monitor"),
    ("Tastatur",       "tas-tah-toor",    "keyboard"),
    ("Drucker",        "droo-ker",        "printer"),
    ("Kamera",         "kah-meh-rah",     "camera"),
    ("Fernseher",      "fairn-zay-er",    "television"),
    ("Radio",          "rah-dee-oh",      "radio"),
    ("Batterie",       "bah-teh-ree",     "battery"),
    ("Ladegerät",      "lah-deh-geh-rayt","charger"),

    # NATURE & ANIMALS
    ("Tier",           "teer",            "animal"),
    ("Hund",           "hoont",           "dog"),
    ("Katze",          "kaht-seh",        "cat"),
    ("Vogel",          "foh-gel",         "bird"),
    ("Fisch",          "fish",            "fish"),
    ("Pferd",          "pfairt",          "horse"),
    ("Kuh",            "koo",             "cow"),
    ("Schwein",        "shvayn",          "pig"),
    ("Schaf",          "shahf",           "sheep"),
    ("Huhn",           "hoon",            "chicken"),
    ("Baum",           "bowm",            "tree"),
    ("Blume",          "bloo-meh",        "flower"),
    ("Gras",           "grahs",           "grass"),
    ("Blatt",          "blaht",           "leaf"),
    ("Wurzel",         "voor-tsel",       "root"),
    ("Samen",          "zah-men",         "seed"),

    # ABSTRACT & COMMON
    ("Welt",           "velt",            "world"),
    ("Leben",          "lay-ben",         "life"),
    ("Tod",            "toht",            "death"),
    ("Geschichte",     "geh-shikh-teh",   "history / story"),
    ("Zukunft",        "tsoo-koonft",     "future"),
    ("Vergangenheit",  "fair-gang-en-hayt","past"),
    ("Gegenwart",      "gay-gen-vart",    "present"),
    ("Recht",          "rekht",           "right / law"),
    ("Pflicht",        "pflikt",          "duty / obligation"),
    ("Freiheit",       "fray-hayt",       "freedom"),
    ("Frieden",        "free-den",        "peace"),
    ("Krieg",          "kreeg",           "war"),
    ("Macht",          "makht",           "power"),
    ("Kraft",          "kraft",           "strength / force"),
    ("Energie",        "eh-nair-gee",     "energy"),
    ("Natur",          "nah-toor",        "nature"),
    ("Wissenschaft",   "vis-en-shaft",    "science"),
    ("Technik",        "tekh-nik",        "technology / technique"),
    ("Kunst",          "koonst",          "art"),
    ("Kultur",         "kool-toor",       "culture"),
    ("Religion",       "reh-li-gyohn",    "religion"),
    ("Gott",           "got",             "God"),
    ("Glaube",         "glow-beh",        "belief / faith"),
    ("Wahrheit",       "vahr-hayt",       "truth"),
    ("Lüge",           "lew-geh",         "lie"),
    ("Freundschaft",   "froynt-shaft",    "friendship"),
    ("Vertrauen",      "fair-trow-en",    "trust"),
    ("Respekt",        "reh-spekt",       "respect"),
    ("Glück",          "glewk",           "luck / happiness"),
    ("Schicksal",      "shik-zahl",       "fate / destiny"),
    ("Traum",          "trowm",           "dream"),
    ("Geheimnis",      "geh-haym-nis",    "secret"),
    ("Bedeutung",      "beh-doy-toong",   "meaning / significance"),

    # QUESTION WORDS
    ("Wer",            "vayr",            "Who"),
    ("Was",            "vahs",            "What"),
    ("Wann",           "vahn",            "When"),
    ("Wo",             "voh",             "Where"),
    ("Warum",          "vah-room",        "Why"),
    ("Wie",            "vee",             "How"),
    ("Wie viel",       "vee feel",        "How much"),
    ("Wie viele",      "vee fee-leh",     "How many"),
    ("Welch-",         "velkh",           "Which"),
    ("Wohin",          "voh-hin",         "Where to"),
    ("Woher",          "voh-hayr",        "Where from"),
    ("Womit",          "voh-mit",         "With what"),

    # USEFUL PHRASES
    ("Ich heiße...",   "ikh hay-seh",     "My name is..."),
    ("Ich bin aus...", "ikh bin ows",     "I am from..."),
    ("Ich wohne in...", "ikh voh-neh in", "I live in..."),
    ("Wie alt sind Sie?","vee ahlt zint zee","How old are you? (formal)"),
    ("Ich bin ... Jahre alt","ikh bin ... yah-reh ahlt","I am ... years old"),
    ("Was kostet das?","vahs kos-tet dahs","How much does that cost?"),
    ("Wo ist die Toilette?","voh ist dee toa-let-eh","Where is the toilet?"),
    ("Ich brauche Hilfe","ikh brow-kheh hil-feh","I need help"),
    ("Rufen Sie einen Arzt!","roo-fen zee ay-nen artst","Call a doctor!"),
    ("Wo ist...?",     "voh ist",         "Where is...?"),
    ("Wie komme ich zu...?","vee kom-eh ikh tsoo","How do I get to...?"),
    ("Gibt es hier...?","gipt es heer",   "Is there ... here?"),
    ("Haben Sie...?",  "hah-ben zee",     "Do you have...?"),
    ("Ich möchte...",  "ikh murk-teh",    "I would like..."),
    ("Einmal bitte",   "ayn-mahl bit-eh", "One (portion/ticket) please"),
    ("Die Rechnung bitte","dee rekh-noong bit-eh","The bill please"),
    ("Können Sie mir helfen?","kur-nen zee meer hel-fen","Can you help me?"),
    ("Was ist das?",   "vahs ist dahs",   "What is that?"),
    ("Ich weiß nicht", "ikh vays nikht",  "I don't know"),
    ("Ich bin müde",   "ikh bin mew-deh", "I am tired"),
    ("Ich habe Hunger","ikh hah-beh hoong-er","I am hungry"),
    ("Ich habe Durst", "ikh hah-beh doorst","I am thirsty"),
    ("Es ist heiß",    "es ist hays",     "It is hot"),
    ("Es ist kalt",    "es ist kahlt",    "It is cold"),
    ("Schönen Tag noch!","shur-nen tahk nokh","Have a nice day!"),
    ("Gute Reise!",    "goo-teh ray-zeh", "Have a good trip!"),
    ("Herzlichen Glückwunsch!","hairts-likh-en glewk-voonsh","Congratulations!"),
    ("Alles Gute!",    "al-es goo-teh",   "All the best!"),
    ("Ich liebe dich", "ikh lee-beh dikh","I love you"),
    ("Ich vermisse dich","ikh fair-mis-eh dikh","I miss you"),

    # NUMBERS IN CONTEXT
    ("einmal",         "ayn-mahl",        "once"),
    ("zweimal",        "tsvay-mahl",      "twice"),
    ("dreimal",        "dry-mahl",        "three times"),
    ("das erste Mal",  "dahs ers-teh mahl","the first time"),
    ("halb",           "halp",            "half"),
    ("ein Drittel",    "ayn drit-el",     "one third"),
    ("ein Viertel",    "ayn feer-tel",    "one quarter"),
    ("beide",          "bay-deh",         "both"),
    ("mehrere",        "mayr-eh-reh",     "several"),
    ("genug",          "geh-nook",        "enough"),

    # OPPOSITES & COMMON PAIRS
    ("oben",           "oh-ben",          "above / up"),
    ("unten",          "oon-ten",         "below / down"),
    ("vorne",          "for-neh",         "in front"),
    ("hinten",         "hin-ten",         "behind / at the back"),
    ("innen",          "in-en",           "inside"),
    ("außen",          "ow-sen",          "outside"),
    ("anfang",         "an-fang",         "beginning / start"),
    ("Ende",           "en-deh",          "end"),
    ("Mitte",          "mit-eh",          "middle / center"),
    ("Seite",          "zay-teh",         "side / page"),
    ("offen",          "of-en",           "open"),
    ("geschlossen",    "geh-shlos-en",    "closed / shut"),
    ("leer",           "layr",            "empty"),
    ("voll",           "fol",             "full"),
    ("trocken",        "trok-en",         "dry"),
    ("nass",           "nas",             "wet"),
    ("weich",          "vaykh",           "soft"),
    ("hart",           "hart",            "hard"),
    ("glatt",          "glaht",           "smooth"),
    ("rau",            "row",             "rough"),
    ("dünn",           "dewn",            "thin"),
    ("dick",           "dik",             "thick / fat"),
    ("eng",            "eng",             "narrow / tight"),
    ("breit",          "brayt",           "wide / broad"),
    ("hoch",           "hokh",            "high / tall"),
    ("tief",           "teef",            "deep / low"),
    ("früh",           "frew",            "early"),
    ("spät",           "shpayt",          "late"),
    ("richtig",        "rikh-tikh",       "right / correct"),
    ("falsch",         "falsh",           "wrong / false"),
    ("hell",           "hel",             "bright / light"),
    ("dunkel",         "doong-kel",       "dark"),
    ("echt",           "ekht",            "genuine / real"),
    ("künstlich",      "kewnst-likh",     "artificial"),
    ("privat",         "pri-vaht",        "private"),
    ("öffentlich",     "urf-ent-likh",    "public"),

    # SCHOOL SUBJECTS
    ("Mathematik",     "mah-teh-mah-tik", "mathematics"),
    ("Biologie",       "bee-oh-loh-gee",  "biology"),
    ("Chemie",         "kheh-mee",        "chemistry"),
    ("Physik",         "few-zeek",        "physics"),
    ("Geschichte",     "geh-shikh-teh",   "history"),
    ("Geografie",      "geh-oh-gra-fee",  "geography"),
    ("Musik",          "moo-zeek",        "music"),
    ("Sport",          "shport",          "sport / PE"),
    ("Kunst",          "koonst",          "art"),
    ("Informatik",     "in-for-mah-tik",  "computer science"),
    ("Literatur",      "li-teh-rah-toor", "literature"),
    ("Philosophie",    "fee-loh-zoh-fee", "philosophy"),

    # FOOD DETAILS
    ("Kartoffel",      "kar-tof-el",      "potato"),
    ("Reis",           "rays",            "rice"),
    ("Nudeln",         "noo-deln",        "noodles / pasta"),
    ("Ei",             "ay",              "egg"),
    ("Käse",           "kay-zeh",         "cheese"),
    ("Butter",         "boo-ter",         "butter"),
    ("Marmelade",      "mar-meh-lah-deh", "jam"),
    ("Honig",          "hoh-nikh",        "honey"),
    ("Kuchen",         "koo-khen",        "cake"),
    ("Schokolade",     "sho-koh-lah-deh", "chocolate"),
    ("Eis",            "ays",             "ice cream"),
    ("Fisch",          "fish",            "fish"),
    ("Hähnchen",       "hayn-khen",       "chicken (meat)"),
    ("Wurst",          "voorst",          "sausage"),
    ("Schinken",       "shin-ken",        "ham"),
    ("Salat",          "zah-laht",        "salad / lettuce"),
    ("Tomate",         "toh-mah-teh",     "tomato"),
    ("Zwiebel",        "tsvee-bel",       "onion"),
    ("Knoblauch",      "k-noh-blowkh",    "garlic"),
    ("Pfeffer",        "pfef-er",         "pepper"),

    # EMOTIONS & FEELINGS
    ("Gefühl",         "geh-fewl",        "feeling / emotion"),
    ("Wut",            "voot",            "anger / rage"),
    ("Überraschung",   "ew-ber-rah-shoong","surprise"),
    ("Einsamkeit",     "ayn-zahm-kayt",   "loneliness"),
    ("Stolz",          "shtolts",         "pride"),
    ("Scham",          "shahm",           "shame"),
    ("Eifersucht",     "ay-fer-zookht",   "jealousy"),
    ("Neugier",        "noy-geer",        "curiosity"),
    ("Langeweile",     "lang-eh-vay-leh", "boredom"),
    ("Begeisterung",   "beh-guys-ter-oong","enthusiasm / excitement"),
    ("Zufriedenheit",  "tsoo-free-den-hayt","contentment / satisfaction"),
    ("Dankbarkeit",    "dank-bar-kayt",   "gratitude"),
    ("Mitgefühl",      "mit-geh-fewl",    "sympathy / compassion"),

    # USEFUL VERBS (EXTRA)
    ("erinnern",       "air-in-ern",      "to remember"),
    ("vergessen",      "fair-ges-en",     "to forget"),
    ("verlieren",      "fair-lee-ren",    "to lose"),
    ("gewinnen",       "geh-vin-en",      "to win"),
    ("versuchen",      "fair-zoo-khen",   "to try / attempt"),
    ("entscheiden",    "ent-shay-den",    "to decide"),
    ("planen",         "plah-nen",        "to plan"),
    ("träumen",        "troy-men",        "to dream"),
    ("hoffen",         "hof-en",          "to hope"),
    ("glauben",        "glow-ben",        "to believe"),
    ("zweifeln",       "tsvay-feln",      "to doubt"),
    ("lächeln",        "lekh-eln",        "to smile"),
    ("lachen",         "lakh-en",         "to laugh"),
    ("weinen",         "vay-nen",         "to cry"),
    ("schreien",       "shray-en",        "to shout / scream"),
    ("flüstern",       "flewss-tern",     "to whisper"),
    ("singen",         "zing-en",         "to sing"),
    ("tanzen",         "tants-en",        "to dance"),
    ("malen",          "mah-len",         "to paint / draw"),
    ("bauen",          "bow-en",          "to build"),
    ("reparieren",     "reh-pah-ree-ren", "to repair"),
    ("besuchen",       "beh-zoo-khen",    "to visit"),
    ("einladen",       "ayn-lah-den",     "to invite"),
    ("feiern",         "fay-ern",         "to celebrate"),
]


# ══════════════════════════════════════════════════════════════════════════════
#  BUILD PDF
# ══════════════════════════════════════════════════════════════════════════════

def build_pdf(filename="German_Language_Reference.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=2.0 * cm,
        bottomMargin=2.0 * cm,
    )
    styles = build_styles()
    story = []
    W = 17.5 * cm  # usable width

    # ── COVER ─────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 3 * cm))
    cover_data = [[Paragraph(
        "🇩🇪  Complete German Language Reference",
        styles["CoverTitle"]
    )]]
    cover_table = Table(cover_data, colWidths=[W])
    cover_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK_BLUE),
        ("TOPPADDING",    (0, 0), (-1, -1), 24),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 24),
        ("LEFTPADDING",   (0, 0), (-1, -1), 20),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 20),
    ]))
    story.append(cover_table)
    story.append(Spacer(1, 0.5 * cm))

    subtitle_data = [[Paragraph(
        "Alphabet · Numbers · Nouns · Pronouns · Verbs · Preverbs · Prepositions<br/>"
        "Conjunctions · Interjections · Adverbs · Adjectives · 500 Essential Words",
        styles["CoverSubtitle"]
    )]]
    sub_table = Table(subtitle_data, colWidths=[W])
    sub_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), MED_BLUE),
        ("TOPPADDING",    (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING",   (0, 0), (-1, -1), 20),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 20),
    ]))
    story.append(sub_table)
    story.append(Spacer(1, 1 * cm))

    info_rows = [
        ["Column Guide", ""],
        ["German", "The written German word / phrase"],
        ["Pronunciation", "Phonetic guide (English-speaker friendly)"],
        ["English Meaning", "Translation / explanation"],
    ]
    info_t = Table(info_rows, colWidths=[4 * cm, W - 4 * cm])
    info_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT_GOLD),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, 0), 11),
        ("TEXTCOLOR",  (0, 0), (-1, 0), WHITE),
        ("BACKGROUND", (0, 1), (-1, -1), LIGHT_GOLD),
        ("FONTNAME",   (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 1), (-1, -1), 9.5),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#d0a010")),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("SPAN",       (0, 0), (-1, 0)),
        ("ALIGN",      (0, 0), (-1, 0), "CENTER"),
    ]))
    story.append(info_t)
    story.append(PageBreak())

    # ── HELPER: two-column section ────────────────────────────────────────────
    def style_subtable(t, rows, bg_even):
        row_s = [
            ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("TEXTCOLOR",  (0, 0), (-1, 0), WHITE),
            ("FONTSIZE",   (0, 0), (-1, 0), 8.5),
            ("GRID",       (0, 0), (-1, -1), 0.3, MED_GREY),
            ("TOPPADDING",    (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING",   (0, 0), (-1, -1), 4),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ]
        for i in range(1, len(rows)):
            bg = bg_even if i % 2 == 1 else WHITE
            row_s.append(("BACKGROUND", (0, i), (-1, i), bg))
        t.setStyle(TableStyle(row_s))

    def two_col_table(rows_left, rows_right, col_w):
        """Combine two sub-tables side by side."""
        left  = Table(rows_left,  colWidths=col_w)
        right = Table(rows_right, colWidths=col_w)
        style_subtable(left,  rows_left,  LIGHT_BLUE)
        style_subtable(right, rows_right, LIGHT_GOLD)

        wrapper = Table([[left, right]], colWidths=[W / 2, W / 2])
        wrapper.setStyle(TableStyle([
            ("VALIGN",       (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING",   (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 0),
        ]))
        return wrapper

    # ── 1. ALPHABET ───────────────────────────────────────────────────────────
    story.append(section_banner("1.  The German Alphabet", styles))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "German uses 26 standard letters plus three umlauts (Ä, Ö, Ü) and the ligature ß. "
        "Each letter has one consistent pronunciation — unlike English.",
        styles["BodyText2"]
    ))
    story.append(Spacer(1, 0.2 * cm))

    alpha_header = ["Letter", "German Name", "Pronunciation Guide"]
    alpha_cw = [2.5 * cm, 4 * cm, 11 * cm]
    story.append(std_table(alpha_header, ALPHABET, alpha_cw, styles))
    story.append(PageBreak())

    # ── 2. NUMBERS ────────────────────────────────────────────────────────────
    story.append(section_banner("2.  Numbers (Zahlen)", styles, bg=MED_BLUE))
    story.append(Spacer(1, 0.2 * cm))

    # split into two columns
    mid = len(NUMBERS) // 2
    left_h = [["#", "German", "Pronunciation", "English"]]
    right_h = [["#", "German", "Pronunciation", "English"]]
    cw4 = [1.0*cm, 3.0*cm, 3.2*cm, 1.6*cm]
    for num, de, pr, en in NUMBERS[:mid]:
        left_h.append([num, de, pr, en])
    for num, de, pr, en in NUMBERS[mid:]:
        right_h.append([num, de, pr, en])

    num_left  = Table(left_h,  colWidths=cw4)
    num_right = Table(right_h, colWidths=cw4)
    for t, bg, rows in [(num_left, LIGHT_BLUE, left_h), (num_right, GREEN_BG, right_h)]:
        rs = [
            ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("TEXTCOLOR",  (0, 0), (-1, 0), WHITE),
            ("FONTSIZE",   (0, 0), (-1, 0), 8),
            ("GRID",       (0, 0), (-1, -1), 0.3, MED_GREY),
            ("TOPPADDING",    (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ]
        for i in range(1, len(rows)):
            rs.append(("BACKGROUND", (0, i), (-1, i), bg if i % 2 == 1 else WHITE))
        t.setStyle(TableStyle(rs))

    wrapper = Table([[num_left, num_right]], colWidths=[W / 2, W / 2])
    wrapper.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(wrapper)
    story.append(PageBreak())

    # ── 3. NOUNS ──────────────────────────────────────────────────────────────
    story.append(section_banner("3.  Nouns (Substantive / Nomen)", styles, bg=colors.HexColor("#1a5c3a")))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "<b>Articles:</b> <b>der</b> (masculine), <b>die</b> (feminine), <b>das</b> (neuter). "
        "Every German noun has a grammatical gender — it must be memorised with its article. "
        "Plural is typically formed by adding endings like -e, -en, -er, -s or by umlaut change.",
        styles["BodyText2"]
    ))
    story.append(Spacer(1, 0.15 * cm))
    noun_header = ["Noun (with article)", "Pronunciation", "English Meaning", "Gender"]
    noun_cw = [4.5*cm, 4.5*cm, 5.5*cm, 3.0*cm]
    story.append(std_table(noun_header, NOUNS, noun_cw, styles))
    story.append(PageBreak())

    # ── 4. PRONOUNS ───────────────────────────────────────────────────────────
    story.append(section_banner("4.  Pronouns (Pronomen)", styles, bg=colors.HexColor("#6a1a5c")))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "German pronouns change form (case) depending on their role in the sentence: "
        "<b>Nominative</b> (subject), <b>Accusative</b> (direct object), <b>Dative</b> (indirect object), "
        "<b>Genitive</b> (possession). Possessives, demonstratives and indefinite pronouns are also included.",
        styles["BodyText2"]
    ))
    story.append(Spacer(1, 0.15 * cm))
    pro_header = ["Pronoun", "Pronunciation", "English Meaning", "Type / Case"]
    pro_cw = [3.5*cm, 3.5*cm, 6*cm, 4.5*cm]
    story.append(std_table(pro_header, PRONOUNS, pro_cw, styles, row_bg=[PURPLE_BG if i%2==0 else WHITE for i in range(len(PRONOUNS))]))
    story.append(PageBreak())

    # ── 5. VERBS ──────────────────────────────────────────────────────────────
    story.append(section_banner("5.  Verbs (Verben) — Common Infinitives", styles, bg=colors.HexColor("#5c1a1a")))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "German verbs conjugate for person and number. Modal verbs (können, müssen, wollen, etc.) "
        "are used with an infinitive. Strong/irregular verbs change their stem vowel. "
        "The present-tense conjugation examples show ich (I) and du (you) forms.",
        styles["BodyText2"]
    ))
    story.append(Spacer(1, 0.15 * cm))
    verb_header = ["Infinitive", "Pronunciation", "English Meaning", "ich / du (present)"]
    verb_cw = [3.5*cm, 4*cm, 4.5*cm, 5.5*cm]
    story.append(std_table(verb_header, VERBS, verb_cw, styles, row_bg=[ORANGE_BG if i%2==0 else WHITE for i in range(len(VERBS))]))
    story.append(PageBreak())

    # ── 6. PREVERBS ───────────────────────────────────────────────────────────
    story.append(section_banner("6.  Preverbs / Verbal Prefixes (Vorsilben)", styles, bg=colors.HexColor("#0d4a4a")))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "German prefixes attach to verb stems to create new meanings. "
        "<b>Separable prefixes</b> (trennbar) split off to the end of the clause in main clauses. "
        "<b>Inseparable prefixes</b> (untrennbar — be-, emp-, ent-, er-, ge-, miss-, ver-, zer-) "
        "never separate and take no <i>ge-</i> in the past participle.",
        styles["BodyText2"]
    ))
    story.append(Spacer(1, 0.15 * cm))
    pv_header = ["Prefix", "Pronunciation", "Meaning / Function", "Example"]
    pv_cw = [2.0*cm, 2.5*cm, 5.5*cm, 7.5*cm]
    story.append(std_table(pv_header, PREVERBS, pv_cw, styles, row_bg=[TEAL_BG if i%2==0 else WHITE for i in range(len(PREVERBS))]))
    story.append(PageBreak())

    # ── 7. PREPOSITIONS ───────────────────────────────────────────────────────
    story.append(section_banner("7.  Prepositions (Präpositionen)", styles, bg=colors.HexColor("#1a3a1a")))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "Every German preposition governs a specific <b>case</b>. "
        "Two-way prepositions (an, auf, hinter, in, neben, über, unter, vor, zwischen) "
        "use <b>Dative</b> for location/state (Wo?) and <b>Accusative</b> for direction/movement (Wohin?).",
        styles["BodyText2"]
    ))
    story.append(Spacer(1, 0.15 * cm))
    prep_header = ["Preposition", "Pronunciation", "English Meaning", "Case Required"]
    prep_cw = [3.0*cm, 3.5*cm, 6.0*cm, 5.0*cm]
    story.append(std_table(prep_header, PREPOSITIONS, prep_cw, styles, row_bg=[GREEN_BG if i%2==0 else WHITE for i in range(len(PREPOSITIONS))]))
    story.append(PageBreak())

    # ── 8. CONJUNCTIONS ───────────────────────────────────────────────────────
    story.append(section_banner("8.  Conjunctions (Konjunktionen)", styles, bg=colors.HexColor("#3a1a5c")))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "<b>Coordinating conjunctions</b> (und, oder, aber, denn, sondern) join clauses of equal rank — "
        "word order is unchanged. <b>Subordinating conjunctions</b> (weil, dass, wenn, ob, etc.) "
        "send the verb to the <b>end</b> of the subordinate clause. "
        "<b>Adverbial conjunctions</b> (deshalb, trotzdem, etc.) cause subject-verb inversion.",
        styles["BodyText2"]
    ))
    story.append(Spacer(1, 0.15 * cm))
    conj_header = ["Conjunction", "Pronunciation", "English Meaning", "Type"]
    conj_cw = [3.5*cm, 4.0*cm, 5.5*cm, 4.5*cm]
    story.append(std_table(conj_header, CONJUNCTIONS, conj_cw, styles, row_bg=[PURPLE_BG if i%2==0 else WHITE for i in range(len(CONJUNCTIONS))]))
    story.append(PageBreak())

    # ── 9. INTERJECTIONS ─────────────────────────────────────────────────────
    story.append(section_banner("9.  Interjections (Interjektionen)", styles, bg=colors.HexColor("#5c3a00")))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "Interjections are spontaneous exclamations that express emotion, reaction or social interaction. "
        "They are grammatically independent and do not inflect.",
        styles["BodyText2"]
    ))
    story.append(Spacer(1, 0.15 * cm))
    inj_header = ["Interjection", "Pronunciation", "English Meaning / Use"]
    inj_cw = [3.5*cm, 3.5*cm, 10.5*cm]
    story.append(std_table(inj_header, INTERJECTIONS, inj_cw, styles, row_bg=[YELLOW_BG if i%2==0 else WHITE for i in range(len(INTERJECTIONS))]))
    story.append(PageBreak())

    # ── 10. ADVERBS ───────────────────────────────────────────────────────────
    story.append(section_banner("10.  Adverbs (Adverbien)", styles, bg=colors.HexColor("#1a4a1a")))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "German adverbs modify verbs, adjectives or other adverbs and do not inflect. "
        "They include temporal (time), local (place), modal (manner) and causal (reason) types.",
        styles["BodyText2"]
    ))
    story.append(Spacer(1, 0.15 * cm))
    adv_header = ["Adverb", "Pronunciation", "English Meaning"]
    adv_cw = [4*cm, 4.5*cm, 9*cm]
    story.append(std_table(adv_header, ADVERBS, adv_cw, styles, row_bg=[TEAL_BG if i%2==0 else WHITE for i in range(len(ADVERBS))]))
    story.append(PageBreak())

    # ── 11. ADJECTIVES ────────────────────────────────────────────────────────
    story.append(section_banner("11.  Adjectives (Adjektive)", styles, bg=colors.HexColor("#4a1a00")))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "Adjectives agree with their noun in gender, number and case when used attributively "
        "(before a noun). When used predicatively (after <i>sein</i>), they do not inflect. "
        "Example: <b>Der alte Mann</b> (attributive) vs <b>Der Mann ist alt</b> (predicative).",
        styles["BodyText2"]
    ))
    story.append(Spacer(1, 0.15 * cm))
    adj_header = ["Adjective", "Pronunciation", "English Meaning"]
    adj_cw = [4*cm, 4.5*cm, 9*cm]
    story.append(std_table(adj_header, ADJECTIVES, adj_cw, styles, row_bg=[ORANGE_BG if i%2==0 else WHITE for i in range(len(ADJECTIVES))]))
    story.append(PageBreak())

    # ── 12. 500 ESSENTIAL WORDS ───────────────────────────────────────────────
    story.append(section_banner("12.  500 Most Essential German Words & Phrases", styles, bg=DARK_BLUE))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "This section covers everyday vocabulary across all key topics: greetings, basic needs "
        "(water, food, road), directions, family, home, time, weather, colors, health, shopping, "
        "work, technology, nature, abstract concepts, question words, and survival phrases. "
        f"Total entries: <b>{len(WORDS_500)}</b>.",
        styles["BodyText2"]
    ))
    story.append(Spacer(1, 0.15 * cm))

    # Split into pages of ~50 rows each for readability
    chunk_size = 50
    for i in range(0, len(WORDS_500), chunk_size):
        chunk = WORDS_500[i:i + chunk_size]
        row_bg = [LIGHT_BLUE if j % 2 == 0 else WHITE for j in range(len(chunk))]
        t = std_table(
            ["German", "Pronunciation", "English Meaning"],
            chunk,
            [5.5*cm, 5.5*cm, 6.5*cm],
            styles,
            row_bg=row_bg
        )
        story.append(t)
        if i + chunk_size < len(WORDS_500):
            story.append(PageBreak())

    story.append(PageBreak())

    # ── GRAMMAR QUICK-REFERENCE ───────────────────────────────────────────────
    story.append(section_banner("Bonus: German Grammar Quick-Reference", styles, bg=ACCENT_GOLD))
    story.append(Spacer(1, 0.3 * cm))

    grammar_sections = [
        ("Articles — Definite (the)", [
            ["Case", "Masculine", "Feminine", "Neuter", "Plural"],
            ["Nominative", "der", "die", "das", "die"],
            ["Accusative", "den", "die", "das", "die"],
            ["Dative", "dem", "der", "dem", "den"],
            ["Genitive", "des", "der", "des", "der"],
        ], [3*cm, 3*cm, 3*cm, 3*cm, 3*cm]),
        ("Articles — Indefinite (a/an)", [
            ["Case", "Masculine", "Feminine", "Neuter"],
            ["Nominative", "ein", "eine", "ein"],
            ["Accusative", "einen", "eine", "ein"],
            ["Dative", "einem", "einer", "einem"],
            ["Genitive", "eines", "einer", "eines"],
        ], [3*cm, 3.5*cm, 3.5*cm, 3.5*cm]),
        ("Personal Pronouns — All Cases", [
            ["Person", "Nominative", "Accusative", "Dative"],
            ["I / me", "ich", "mich", "mir"],
            ["you (sing.)", "du", "dich", "dir"],
            ["he / him", "er", "ihn", "ihm"],
            ["she / her", "sie", "sie", "ihr"],
            ["it", "es", "es", "ihm"],
            ["we / us", "wir", "uns", "uns"],
            ["you (pl.)", "ihr", "euch", "euch"],
            ["they / them", "sie", "sie", "ihnen"],
            ["You (formal)", "Sie", "Sie", "Ihnen"],
        ], [3.5*cm, 3.5*cm, 3.5*cm, 3.5*cm]),
        ("Verb 'sein' (to be) — Present Tense", [
            ["Person", "German", "Pronunciation", "English"],
            ["ich", "bin", "bin", "I am"],
            ["du", "bist", "bist", "you are"],
            ["er/sie/es", "ist", "ist", "he/she/it is"],
            ["wir", "sind", "zint", "we are"],
            ["ihr", "seid", "zayt", "you (pl.) are"],
            ["sie/Sie", "sind", "zint", "they/You are"],
        ], [3*cm, 3*cm, 3.5*cm, 3.5*cm]),
        ("Verb 'haben' (to have) — Present Tense", [
            ["Person", "German", "Pronunciation", "English"],
            ["ich", "habe", "hah-beh", "I have"],
            ["du", "hast", "hahst", "you have"],
            ["er/sie/es", "hat", "haht", "he/she/it has"],
            ["wir", "haben", "hah-ben", "we have"],
            ["ihr", "habt", "hahpt", "you (pl.) have"],
            ["sie/Sie", "haben", "hah-ben", "they/You have"],
        ], [3*cm, 3*cm, 3.5*cm, 3.5*cm]),
        ("Common Tense Formation", [
            ["Tense", "Formation", "Example"],
            ["Present", "stem + ending (-e/-st/-t/-en/-t/-en)", "ich mache (I make)"],
            ["Past simple (Präteritum)", "stem + te-endings or irregular", "ich machte / ich war"],
            ["Perfect (Perfekt)", "haben/sein + past participle", "ich habe gemacht / ich bin gegangen"],
            ["Future", "werden + infinitive", "ich werde gehen (I will go)"],
            ["Subjunctive II", "würde + infinitive (polite req.)", "ich würde gerne... (I would like to...)"],
        ], [3*cm, 7*cm, 7*cm]),
    ]

    for title, table_data, col_widths in grammar_sections:
        story.append(Paragraph(title, styles["SubTitle"]))
        header_row = table_data[0]
        data_rows  = table_data[1:]
        t = std_table(
            header_row, data_rows, col_widths, styles,
            row_bg=[LIGHT_GOLD if i%2==0 else WHITE for i in range(len(data_rows))]
        )
        story.append(KeepTogether([t, Spacer(1, 0.3*cm)]))

    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width=W, thickness=2, color=DARK_BLUE))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "<b>Tip:</b> The best way to learn German pronunciation is to listen and repeat. "
        "Vowel length (short vs. long) changes meaning: <i>der Weg</i> (the way) vs <i>weg</i> (away). "
        "Keep a vocabulary notebook and review 10–15 new words daily for steady progress. "
        "<b>Viel Erfolg!</b> (Good luck!)",
        styles["BodyText2"]
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"✅  PDF generated: {filename}")
    print(f"    Total words/phrases in section 12: {len(WORDS_500)}")
    total = (len(ALPHABET) + len(NUMBERS) + len(NOUNS) + len(PRONOUNS) +
             len(VERBS) + len(PREVERBS) + len(PREPOSITIONS) + len(CONJUNCTIONS) +
             len(INTERJECTIONS) + len(ADVERBS) + len(ADJECTIVES) + len(WORDS_500))
    print(f"    Total entries across all sections: {total}")


if __name__ == "__main__":
    build_pdf("/workspace/German_Language_Reference.pdf")
