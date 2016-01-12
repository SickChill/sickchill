/* For Unicode version 8.0.0 */

#include "_regex_unicode.h"

#define RE_BLANK_MASK ((1 << RE_PROP_ZL) | (1 << RE_PROP_ZP))
#define RE_GRAPH_MASK ((1 << RE_PROP_CC) | (1 << RE_PROP_CS) | (1 << RE_PROP_CN))
#define RE_WORD_MASK (RE_PROP_M_MASK | (1 << RE_PROP_ND) | (1 << RE_PROP_PC))

typedef struct RE_AllCases {
    RE_INT32 diffs[RE_MAX_CASES - 1];
} RE_AllCases;

typedef struct RE_FullCaseFolding {
    RE_INT32 diff;
    RE_UINT16 codepoints[RE_MAX_FOLDED - 1];
} RE_FullCaseFolding;

/* strings. */

char* re_strings[] = {
    "-1/2",
    "0",
    "1",
    "1/10",
    "1/12",
    "1/16",
    "1/2",
    "1/3",
    "1/4",
    "1/5",
    "1/6",
    "1/7",
    "1/8",
    "1/9",
    "10",
    "100",
    "1000",
    "10000",
    "100000",
    "1000000",
    "100000000",
    "10000000000",
    "1000000000000",
    "103",
    "107",
    "11",
    "11/12",
    "11/2",
    "118",
    "12",
    "122",
    "129",
    "13",
    "13/2",
    "130",
    "132",
    "133",
    "14",
    "15",
    "15/2",
    "16",
    "17",
    "17/2",
    "18",
    "19",
    "2",
    "2/3",
    "2/5",
    "20",
    "200",
    "2000",
    "20000",
    "200000",
    "202",
    "21",
    "214",
    "216",
    "216000",
    "218",
    "22",
    "220",
    "222",
    "224",
    "226",
    "228",
    "23",
    "230",
    "232",
    "233",
    "234",
    "24",
    "240",
    "25",
    "26",
    "27",
    "28",
    "29",
    "3",
    "3/16",
    "3/2",
    "3/4",
    "3/5",
    "3/8",
    "30",
    "300",
    "3000",
    "30000",
    "300000",
    "31",
    "32",
    "33",
    "34",
    "35",
    "36",
    "37",
    "38",
    "39",
    "4",
    "4/5",
    "40",
    "400",
    "4000",
    "40000",
    "400000",
    "41",
    "42",
    "43",
    "432000",
    "44",
    "45",
    "46",
    "47",
    "48",
    "49",
    "5",
    "5/12",
    "5/2",
    "5/6",
    "5/8",
    "50",
    "500",
    "5000",
    "50000",
    "500000",
    "6",
    "60",
    "600",
    "6000",
    "60000",
    "600000",
    "7",
    "7/12",
    "7/2",
    "7/8",
    "70",
    "700",
    "7000",
    "70000",
    "700000",
    "8",
    "80",
    "800",
    "8000",
    "80000",
    "800000",
    "84",
    "9",
    "9/2",
    "90",
    "900",
    "9000",
    "90000",
    "900000",
    "91",
    "A",
    "ABOVE",
    "ABOVELEFT",
    "ABOVERIGHT",
    "AEGEANNUMBERS",
    "AGHB",
    "AHEX",
    "AHOM",
    "AI",
    "AIN",
    "AL",
    "ALAPH",
    "ALCHEMICAL",
    "ALCHEMICALSYMBOLS",
    "ALEF",
    "ALETTER",
    "ALNUM",
    "ALPHA",
    "ALPHABETIC",
    "ALPHABETICPF",
    "ALPHABETICPRESENTATIONFORMS",
    "ALPHANUMERIC",
    "AMBIGUOUS",
    "AN",
    "ANATOLIANHIEROGLYPHS",
    "ANCIENTGREEKMUSIC",
    "ANCIENTGREEKMUSICALNOTATION",
    "ANCIENTGREEKNUMBERS",
    "ANCIENTSYMBOLS",
    "ANY",
    "AR",
    "ARAB",
    "ARABIC",
    "ARABICEXTA",
    "ARABICEXTENDEDA",
    "ARABICLETTER",
    "ARABICMATH",
    "ARABICMATHEMATICALALPHABETICSYMBOLS",
    "ARABICNUMBER",
    "ARABICPFA",
    "ARABICPFB",
    "ARABICPRESENTATIONFORMSA",
    "ARABICPRESENTATIONFORMSB",
    "ARABICSUP",
    "ARABICSUPPLEMENT",
    "ARMENIAN",
    "ARMI",
    "ARMN",
    "ARROWS",
    "ASCII",
    "ASCIIHEXDIGIT",
    "ASSIGNED",
    "AT",
    "ATA",
    "ATAR",
    "ATB",
    "ATBL",
    "ATERM",
    "ATTACHEDABOVE",
    "ATTACHEDABOVERIGHT",
    "ATTACHEDBELOW",
    "ATTACHEDBELOWLEFT",
    "AVAGRAHA",
    "AVESTAN",
    "AVST",
    "B",
    "B2",
    "BA",
    "BALI",
    "BALINESE",
    "BAMU",
    "BAMUM",
    "BAMUMSUP",
    "BAMUMSUPPLEMENT",
    "BASICLATIN",
    "BASS",
    "BASSAVAH",
    "BATAK",
    "BATK",
    "BB",
    "BC",
    "BEH",
    "BELOW",
    "BELOWLEFT",
    "BELOWRIGHT",
    "BENG",
    "BENGALI",
    "BETH",
    "BIDIC",
    "BIDICLASS",
    "BIDICONTROL",
    "BIDIM",
    "BIDIMIRRORED",
    "BINDU",
    "BK",
    "BL",
    "BLANK",
    "BLK",
    "BLOCK",
    "BLOCKELEMENTS",
    "BN",
    "BOPO",
    "BOPOMOFO",
    "BOPOMOFOEXT",
    "BOPOMOFOEXTENDED",
    "BOTTOM",
    "BOTTOMANDRIGHT",
    "BOUNDARYNEUTRAL",
    "BOXDRAWING",
    "BR",
    "BRAH",
    "BRAHMI",
    "BRAHMIJOININGNUMBER",
    "BRAI",
    "BRAILLE",
    "BRAILLEPATTERNS",
    "BREAKAFTER",
    "BREAKBEFORE",
    "BREAKBOTH",
    "BREAKSYMBOLS",
    "BUGI",
    "BUGINESE",
    "BUHD",
    "BUHID",
    "BURUSHASKIYEHBARREE",
    "BYZANTINEMUSIC",
    "BYZANTINEMUSICALSYMBOLS",
    "C",
    "C&",
    "CAKM",
    "CAN",
    "CANADIANABORIGINAL",
    "CANADIANSYLLABICS",
    "CANONICAL",
    "CANONICALCOMBININGCLASS",
    "CANS",
    "CANTILLATIONMARK",
    "CARI",
    "CARIAN",
    "CARRIAGERETURN",
    "CASED",
    "CASEDLETTER",
    "CASEIGNORABLE",
    "CAUCASIANALBANIAN",
    "CB",
    "CC",
    "CCC",
    "CCC10",
    "CCC103",
    "CCC107",
    "CCC11",
    "CCC118",
    "CCC12",
    "CCC122",
    "CCC129",
    "CCC13",
    "CCC130",
    "CCC132",
    "CCC133",
    "CCC14",
    "CCC15",
    "CCC16",
    "CCC17",
    "CCC18",
    "CCC19",
    "CCC20",
    "CCC21",
    "CCC22",
    "CCC23",
    "CCC24",
    "CCC25",
    "CCC26",
    "CCC27",
    "CCC28",
    "CCC29",
    "CCC30",
    "CCC31",
    "CCC32",
    "CCC33",
    "CCC34",
    "CCC35",
    "CCC36",
    "CCC84",
    "CCC91",
    "CF",
    "CHAKMA",
    "CHAM",
    "CHANGESWHENCASEFOLDED",
    "CHANGESWHENCASEMAPPED",
    "CHANGESWHENLOWERCASED",
    "CHANGESWHENTITLECASED",
    "CHANGESWHENUPPERCASED",
    "CHER",
    "CHEROKEE",
    "CHEROKEESUP",
    "CHEROKEESUPPLEMENT",
    "CI",
    "CIRCLE",
    "CJ",
    "CJK",
    "CJKCOMPAT",
    "CJKCOMPATFORMS",
    "CJKCOMPATIBILITY",
    "CJKCOMPATIBILITYFORMS",
    "CJKCOMPATIBILITYIDEOGRAPHS",
    "CJKCOMPATIBILITYIDEOGRAPHSSUPPLEMENT",
    "CJKCOMPATIDEOGRAPHS",
    "CJKCOMPATIDEOGRAPHSSUP",
    "CJKEXTA",
    "CJKEXTB",
    "CJKEXTC",
    "CJKEXTD",
    "CJKEXTE",
    "CJKRADICALSSUP",
    "CJKRADICALSSUPPLEMENT",
    "CJKSTROKES",
    "CJKSYMBOLS",
    "CJKSYMBOLSANDPUNCTUATION",
    "CJKUNIFIEDIDEOGRAPHS",
    "CJKUNIFIEDIDEOGRAPHSEXTENSIONA",
    "CJKUNIFIEDIDEOGRAPHSEXTENSIONB",
    "CJKUNIFIEDIDEOGRAPHSEXTENSIONC",
    "CJKUNIFIEDIDEOGRAPHSEXTENSIOND",
    "CJKUNIFIEDIDEOGRAPHSEXTENSIONE",
    "CL",
    "CLOSE",
    "CLOSEPARENTHESIS",
    "CLOSEPUNCTUATION",
    "CM",
    "CN",
    "CNTRL",
    "CO",
    "COM",
    "COMBININGDIACRITICALMARKS",
    "COMBININGDIACRITICALMARKSEXTENDED",
    "COMBININGDIACRITICALMARKSFORSYMBOLS",
    "COMBININGDIACRITICALMARKSSUPPLEMENT",
    "COMBININGHALFMARKS",
    "COMBININGMARK",
    "COMBININGMARKSFORSYMBOLS",
    "COMMON",
    "COMMONINDICNUMBERFORMS",
    "COMMONSEPARATOR",
    "COMPAT",
    "COMPATJAMO",
    "COMPLEXCONTEXT",
    "CONDITIONALJAPANESESTARTER",
    "CONNECTORPUNCTUATION",
    "CONSONANT",
    "CONSONANTDEAD",
    "CONSONANTFINAL",
    "CONSONANTHEADLETTER",
    "CONSONANTKILLER",
    "CONSONANTMEDIAL",
    "CONSONANTPLACEHOLDER",
    "CONSONANTPRECEDINGREPHA",
    "CONSONANTPREFIXED",
    "CONSONANTSUBJOINED",
    "CONSONANTSUCCEEDINGREPHA",
    "CONSONANTWITHSTACKER",
    "CONTINGENTBREAK",
    "CONTROL",
    "CONTROLPICTURES",
    "COPT",
    "COPTIC",
    "COPTICEPACTNUMBERS",
    "COUNTINGROD",
    "COUNTINGRODNUMERALS",
    "CP",
    "CPRT",
    "CR",
    "CS",
    "CUNEIFORM",
    "CUNEIFORMNUMBERS",
    "CUNEIFORMNUMBERSANDPUNCTUATION",
    "CURRENCYSYMBOL",
    "CURRENCYSYMBOLS",
    "CWCF",
    "CWCM",
    "CWL",
    "CWT",
    "CWU",
    "CYPRIOT",
    "CYPRIOTSYLLABARY",
    "CYRILLIC",
    "CYRILLICEXTA",
    "CYRILLICEXTB",
    "CYRILLICEXTENDEDA",
    "CYRILLICEXTENDEDB",
    "CYRILLICSUP",
    "CYRILLICSUPPLEMENT",
    "CYRILLICSUPPLEMENTARY",
    "CYRL",
    "D",
    "DA",
    "DAL",
    "DALATHRISH",
    "DASH",
    "DASHPUNCTUATION",
    "DB",
    "DE",
    "DECIMAL",
    "DECIMALNUMBER",
    "DECOMPOSITIONTYPE",
    "DEFAULTIGNORABLECODEPOINT",
    "DEP",
    "DEPRECATED",
    "DESERET",
    "DEVA",
    "DEVANAGARI",
    "DEVANAGARIEXT",
    "DEVANAGARIEXTENDED",
    "DI",
    "DIA",
    "DIACRITIC",
    "DIACRITICALS",
    "DIACRITICALSEXT",
    "DIACRITICALSFORSYMBOLS",
    "DIACRITICALSSUP",
    "DIGIT",
    "DINGBATS",
    "DOMINO",
    "DOMINOTILES",
    "DOUBLEABOVE",
    "DOUBLEBELOW",
    "DOUBLEQUOTE",
    "DQ",
    "DSRT",
    "DT",
    "DUALJOINING",
    "DUPL",
    "DUPLOYAN",
    "E",
    "EA",
    "EARLYDYNASTICCUNEIFORM",
    "EASTASIANWIDTH",
    "EGYP",
    "EGYPTIANHIEROGLYPHS",
    "ELBA",
    "ELBASAN",
    "EMOTICONS",
    "EN",
    "ENC",
    "ENCLOSEDALPHANUM",
    "ENCLOSEDALPHANUMERICS",
    "ENCLOSEDALPHANUMERICSUPPLEMENT",
    "ENCLOSEDALPHANUMSUP",
    "ENCLOSEDCJK",
    "ENCLOSEDCJKLETTERSANDMONTHS",
    "ENCLOSEDIDEOGRAPHICSUP",
    "ENCLOSEDIDEOGRAPHICSUPPLEMENT",
    "ENCLOSINGMARK",
    "ES",
    "ET",
    "ETHI",
    "ETHIOPIC",
    "ETHIOPICEXT",
    "ETHIOPICEXTA",
    "ETHIOPICEXTENDED",
    "ETHIOPICEXTENDEDA",
    "ETHIOPICSUP",
    "ETHIOPICSUPPLEMENT",
    "EUROPEANNUMBER",
    "EUROPEANSEPARATOR",
    "EUROPEANTERMINATOR",
    "EX",
    "EXCLAMATION",
    "EXT",
    "EXTEND",
    "EXTENDER",
    "EXTENDNUMLET",
    "F",
    "FALSE",
    "FARSIYEH",
    "FE",
    "FEH",
    "FIN",
    "FINAL",
    "FINALPUNCTUATION",
    "FINALSEMKATH",
    "FIRSTSTRONGISOLATE",
    "FO",
    "FONT",
    "FORMAT",
    "FRA",
    "FRACTION",
    "FSI",
    "FULLWIDTH",
    "GAF",
    "GAMAL",
    "GC",
    "GCB",
    "GEMINATIONMARK",
    "GENERALCATEGORY",
    "GENERALPUNCTUATION",
    "GEOMETRICSHAPES",
    "GEOMETRICSHAPESEXT",
    "GEOMETRICSHAPESEXTENDED",
    "GEOR",
    "GEORGIAN",
    "GEORGIANSUP",
    "GEORGIANSUPPLEMENT",
    "GL",
    "GLAG",
    "GLAGOLITIC",
    "GLUE",
    "GOTH",
    "GOTHIC",
    "GRAN",
    "GRANTHA",
    "GRAPH",
    "GRAPHEMEBASE",
    "GRAPHEMECLUSTERBREAK",
    "GRAPHEMEEXTEND",
    "GRAPHEMELINK",
    "GRBASE",
    "GREEK",
    "GREEKANDCOPTIC",
    "GREEKEXT",
    "GREEKEXTENDED",
    "GREK",
    "GREXT",
    "GRLINK",
    "GUJARATI",
    "GUJR",
    "GURMUKHI",
    "GURU",
    "H",
    "H2",
    "H3",
    "HAH",
    "HALFANDFULLFORMS",
    "HALFMARKS",
    "HALFWIDTH",
    "HALFWIDTHANDFULLWIDTHFORMS",
    "HAMZAONHEHGOAL",
    "HAN",
    "HANG",
    "HANGUL",
    "HANGULCOMPATIBILITYJAMO",
    "HANGULJAMO",
    "HANGULJAMOEXTENDEDA",
    "HANGULJAMOEXTENDEDB",
    "HANGULSYLLABLES",
    "HANGULSYLLABLETYPE",
    "HANI",
    "HANO",
    "HANUNOO",
    "HATR",
    "HATRAN",
    "HE",
    "HEBR",
    "HEBREW",
    "HEBREWLETTER",
    "HEH",
    "HEHGOAL",
    "HETH",
    "HEX",
    "HEXDIGIT",
    "HIGHPRIVATEUSESURROGATES",
    "HIGHPUSURROGATES",
    "HIGHSURROGATES",
    "HIRA",
    "HIRAGANA",
    "HL",
    "HLUW",
    "HMNG",
    "HRKT",
    "HST",
    "HUNG",
    "HY",
    "HYPHEN",
    "ID",
    "IDC",
    "IDCONTINUE",
    "IDEO",
    "IDEOGRAPHIC",
    "IDEOGRAPHICDESCRIPTIONCHARACTERS",
    "IDS",
    "IDSB",
    "IDSBINARYOPERATOR",
    "IDST",
    "IDSTART",
    "IDSTRINARYOPERATOR",
    "IMPERIALARAMAIC",
    "IN",
    "INDICNUMBERFORMS",
    "INDICPOSITIONALCATEGORY",
    "INDICSYLLABICCATEGORY",
    "INFIXNUMERIC",
    "INHERITED",
    "INIT",
    "INITIAL",
    "INITIALPUNCTUATION",
    "INPC",
    "INSC",
    "INSCRIPTIONALPAHLAVI",
    "INSCRIPTIONALPARTHIAN",
    "INSEPARABLE",
    "INSEPERABLE",
    "INVISIBLESTACKER",
    "IOTASUBSCRIPT",
    "IPAEXT",
    "IPAEXTENSIONS",
    "IS",
    "ISO",
    "ISOLATED",
    "ITAL",
    "JAMO",
    "JAMOEXTA",
    "JAMOEXTB",
    "JAVA",
    "JAVANESE",
    "JG",
    "JL",
    "JOINC",
    "JOINCAUSING",
    "JOINCONTROL",
    "JOINER",
    "JOININGGROUP",
    "JOININGTYPE",
    "JT",
    "JV",
    "KA",
    "KAF",
    "KAITHI",
    "KALI",
    "KANA",
    "KANASUP",
    "KANASUPPLEMENT",
    "KANAVOICING",
    "KANBUN",
    "KANGXI",
    "KANGXIRADICALS",
    "KANNADA",
    "KAPH",
    "KATAKANA",
    "KATAKANAEXT",
    "KATAKANAORHIRAGANA",
    "KATAKANAPHONETICEXTENSIONS",
    "KAYAHLI",
    "KHAPH",
    "KHAR",
    "KHAROSHTHI",
    "KHMER",
    "KHMERSYMBOLS",
    "KHMR",
    "KHOJ",
    "KHOJKI",
    "KHUDAWADI",
    "KNDA",
    "KNOTTEDHEH",
    "KTHI",
    "KV",
    "L",
    "L&",
    "LAM",
    "LAMADH",
    "LANA",
    "LAO",
    "LAOO",
    "LATIN",
    "LATIN1",
    "LATIN1SUP",
    "LATIN1SUPPLEMENT",
    "LATINEXTA",
    "LATINEXTADDITIONAL",
    "LATINEXTB",
    "LATINEXTC",
    "LATINEXTD",
    "LATINEXTE",
    "LATINEXTENDEDA",
    "LATINEXTENDEDADDITIONAL",
    "LATINEXTENDEDB",
    "LATINEXTENDEDC",
    "LATINEXTENDEDD",
    "LATINEXTENDEDE",
    "LATN",
    "LB",
    "LC",
    "LE",
    "LEADINGJAMO",
    "LEFT",
    "LEFTANDRIGHT",
    "LEFTJOINING",
    "LEFTTORIGHT",
    "LEFTTORIGHTEMBEDDING",
    "LEFTTORIGHTISOLATE",
    "LEFTTORIGHTOVERRIDE",
    "LEPC",
    "LEPCHA",
    "LETTER",
    "LETTERLIKESYMBOLS",
    "LETTERNUMBER",
    "LF",
    "LIMB",
    "LIMBU",
    "LINA",
    "LINB",
    "LINEARA",
    "LINEARB",
    "LINEARBIDEOGRAMS",
    "LINEARBSYLLABARY",
    "LINEBREAK",
    "LINEFEED",
    "LINESEPARATOR",
    "LISU",
    "LL",
    "LM",
    "LO",
    "LOE",
    "LOGICALORDEREXCEPTION",
    "LOWER",
    "LOWERCASE",
    "LOWERCASELETTER",
    "LOWSURROGATES",
    "LRE",
    "LRI",
    "LRO",
    "LT",
    "LU",
    "LV",
    "LVSYLLABLE",
    "LVT",
    "LVTSYLLABLE",
    "LYCI",
    "LYCIAN",
    "LYDI",
    "LYDIAN",
    "M",
    "M&",
    "MAHAJANI",
    "MAHJ",
    "MAHJONG",
    "MAHJONGTILES",
    "MALAYALAM",
    "MAND",
    "MANDAIC",
    "MANDATORYBREAK",
    "MANI",
    "MANICHAEAN",
    "MANICHAEANALEPH",
    "MANICHAEANAYIN",
    "MANICHAEANBETH",
    "MANICHAEANDALETH",
    "MANICHAEANDHAMEDH",
    "MANICHAEANFIVE",
    "MANICHAEANGIMEL",
    "MANICHAEANHETH",
    "MANICHAEANHUNDRED",
    "MANICHAEANKAPH",
    "MANICHAEANLAMEDH",
    "MANICHAEANMEM",
    "MANICHAEANNUN",
    "MANICHAEANONE",
    "MANICHAEANPE",
    "MANICHAEANQOPH",
    "MANICHAEANRESH",
    "MANICHAEANSADHE",
    "MANICHAEANSAMEKH",
    "MANICHAEANTAW",
    "MANICHAEANTEN",
    "MANICHAEANTETH",
    "MANICHAEANTHAMEDH",
    "MANICHAEANTWENTY",
    "MANICHAEANWAW",
    "MANICHAEANYODH",
    "MANICHAEANZAYIN",
    "MARK",
    "MATH",
    "MATHALPHANUM",
    "MATHEMATICALALPHANUMERICSYMBOLS",
    "MATHEMATICALOPERATORS",
    "MATHOPERATORS",
    "MATHSYMBOL",
    "MB",
    "MC",
    "ME",
    "MED",
    "MEDIAL",
    "MEEM",
    "MEETEIMAYEK",
    "MEETEIMAYEKEXT",
    "MEETEIMAYEKEXTENSIONS",
    "MEND",
    "MENDEKIKAKUI",
    "MERC",
    "MERO",
    "MEROITICCURSIVE",
    "MEROITICHIEROGLYPHS",
    "MIAO",
    "MIDLETTER",
    "MIDNUM",
    "MIDNUMLET",
    "MIM",
    "MISCARROWS",
    "MISCELLANEOUSMATHEMATICALSYMBOLSA",
    "MISCELLANEOUSMATHEMATICALSYMBOLSB",
    "MISCELLANEOUSSYMBOLS",
    "MISCELLANEOUSSYMBOLSANDARROWS",
    "MISCELLANEOUSSYMBOLSANDPICTOGRAPHS",
    "MISCELLANEOUSTECHNICAL",
    "MISCMATHSYMBOLSA",
    "MISCMATHSYMBOLSB",
    "MISCPICTOGRAPHS",
    "MISCSYMBOLS",
    "MISCTECHNICAL",
    "ML",
    "MLYM",
    "MN",
    "MODI",
    "MODIFIERLETTER",
    "MODIFIERLETTERS",
    "MODIFIERSYMBOL",
    "MODIFIERTONELETTERS",
    "MODIFYINGLETTER",
    "MONG",
    "MONGOLIAN",
    "MRO",
    "MROO",
    "MTEI",
    "MULT",
    "MULTANI",
    "MUSIC",
    "MUSICALSYMBOLS",
    "MYANMAR",
    "MYANMAREXTA",
    "MYANMAREXTB",
    "MYANMAREXTENDEDA",
    "MYANMAREXTENDEDB",
    "MYMR",
    "N",
    "N&",
    "NA",
    "NABATAEAN",
    "NAN",
    "NAR",
    "NARB",
    "NARROW",
    "NB",
    "NBAT",
    "NCHAR",
    "ND",
    "NEUTRAL",
    "NEWLINE",
    "NEWTAILUE",
    "NEXTLINE",
    "NK",
    "NKO",
    "NKOO",
    "NL",
    "NO",
    "NOBLOCK",
    "NOBREAK",
    "NOJOININGGROUP",
    "NONCHARACTERCODEPOINT",
    "NONE",
    "NONJOINER",
    "NONJOINING",
    "NONSPACINGMARK",
    "NONSTARTER",
    "NOON",
    "NOTAPPLICABLE",
    "NOTREORDERED",
    "NR",
    "NS",
    "NSM",
    "NT",
    "NU",
    "NUKTA",
    "NUMBER",
    "NUMBERFORMS",
    "NUMBERJOINER",
    "NUMERIC",
    "NUMERICTYPE",
    "NUMERICVALUE",
    "NUN",
    "NV",
    "NYA",
    "OALPHA",
    "OCR",
    "ODI",
    "OGAM",
    "OGHAM",
    "OGREXT",
    "OIDC",
    "OIDS",
    "OLCHIKI",
    "OLCK",
    "OLDHUNGARIAN",
    "OLDITALIC",
    "OLDNORTHARABIAN",
    "OLDPERMIC",
    "OLDPERSIAN",
    "OLDSOUTHARABIAN",
    "OLDTURKIC",
    "OLETTER",
    "OLOWER",
    "OMATH",
    "ON",
    "OP",
    "OPENPUNCTUATION",
    "OPTICALCHARACTERRECOGNITION",
    "ORIYA",
    "ORKH",
    "ORNAMENTALDINGBATS",
    "ORYA",
    "OSMA",
    "OSMANYA",
    "OTHER",
    "OTHERALPHABETIC",
    "OTHERDEFAULTIGNORABLECODEPOINT",
    "OTHERGRAPHEMEEXTEND",
    "OTHERIDCONTINUE",
    "OTHERIDSTART",
    "OTHERLETTER",
    "OTHERLOWERCASE",
    "OTHERMATH",
    "OTHERNEUTRAL",
    "OTHERNUMBER",
    "OTHERPUNCTUATION",
    "OTHERSYMBOL",
    "OTHERUPPERCASE",
    "OUPPER",
    "OV",
    "OVERLAY",
    "OVERSTRUCK",
    "P",
    "P&",
    "PAHAWHHMONG",
    "PALM",
    "PALMYRENE",
    "PARAGRAPHSEPARATOR",
    "PATSYN",
    "PATTERNSYNTAX",
    "PATTERNWHITESPACE",
    "PATWS",
    "PAUC",
    "PAUCINHAU",
    "PC",
    "PD",
    "PDF",
    "PDI",
    "PE",
    "PERM",
    "PF",
    "PHAG",
    "PHAGSPA",
    "PHAISTOS",
    "PHAISTOSDISC",
    "PHLI",
    "PHLP",
    "PHNX",
    "PHOENICIAN",
    "PHONETICEXT",
    "PHONETICEXTENSIONS",
    "PHONETICEXTENSIONSSUPPLEMENT",
    "PHONETICEXTSUP",
    "PI",
    "PLAYINGCARDS",
    "PLRD",
    "PO",
    "POPDIRECTIONALFORMAT",
    "POPDIRECTIONALISOLATE",
    "POSIXALNUM",
    "POSIXDIGIT",
    "POSIXPUNCT",
    "POSIXXDIGIT",
    "POSTFIXNUMERIC",
    "PP",
    "PR",
    "PREFIXNUMERIC",
    "PREPEND",
    "PRINT",
    "PRIVATEUSE",
    "PRIVATEUSEAREA",
    "PRTI",
    "PS",
    "PSALTERPAHLAVI",
    "PUA",
    "PUNCT",
    "PUNCTUATION",
    "PUREKILLER",
    "QAAC",
    "QAAI",
    "QAF",
    "QAPH",
    "QMARK",
    "QU",
    "QUOTATION",
    "QUOTATIONMARK",
    "R",
    "RADICAL",
    "REGIONALINDICATOR",
    "REGISTERSHIFTER",
    "REH",
    "REJANG",
    "REVERSEDPE",
    "RI",
    "RIGHT",
    "RIGHTJOINING",
    "RIGHTTOLEFT",
    "RIGHTTOLEFTEMBEDDING",
    "RIGHTTOLEFTISOLATE",
    "RIGHTTOLEFTOVERRIDE",
    "RJNG",
    "RLE",
    "RLI",
    "RLO",
    "ROHINGYAYEH",
    "RUMI",
    "RUMINUMERALSYMBOLS",
    "RUNIC",
    "RUNR",
    "S",
    "S&",
    "SA",
    "SAD",
    "SADHE",
    "SAMARITAN",
    "SAMR",
    "SARB",
    "SAUR",
    "SAURASHTRA",
    "SB",
    "SC",
    "SCONTINUE",
    "SCRIPT",
    "SD",
    "SE",
    "SEEN",
    "SEGMENTSEPARATOR",
    "SEMKATH",
    "SENTENCEBREAK",
    "SEP",
    "SEPARATOR",
    "SG",
    "SGNW",
    "SHARADA",
    "SHAVIAN",
    "SHAW",
    "SHIN",
    "SHORTHANDFORMATCONTROLS",
    "SHRD",
    "SIDD",
    "SIDDHAM",
    "SIGNWRITING",
    "SIND",
    "SINGLEQUOTE",
    "SINH",
    "SINHALA",
    "SINHALAARCHAICNUMBERS",
    "SK",
    "SM",
    "SMALL",
    "SMALLFORMS",
    "SMALLFORMVARIANTS",
    "SML",
    "SO",
    "SOFTDOTTED",
    "SORA",
    "SORASOMPENG",
    "SP",
    "SPACE",
    "SPACESEPARATOR",
    "SPACINGMARK",
    "SPACINGMODIFIERLETTERS",
    "SPECIALS",
    "SQ",
    "SQR",
    "SQUARE",
    "ST",
    "STERM",
    "STRAIGHTWAW",
    "SUB",
    "SUND",
    "SUNDANESE",
    "SUNDANESESUP",
    "SUNDANESESUPPLEMENT",
    "SUP",
    "SUPARROWSA",
    "SUPARROWSB",
    "SUPARROWSC",
    "SUPER",
    "SUPERANDSUB",
    "SUPERSCRIPTSANDSUBSCRIPTS",
    "SUPMATHOPERATORS",
    "SUPPLEMENTALARROWSA",
    "SUPPLEMENTALARROWSB",
    "SUPPLEMENTALARROWSC",
    "SUPPLEMENTALMATHEMATICALOPERATORS",
    "SUPPLEMENTALPUNCTUATION",
    "SUPPLEMENTALSYMBOLSANDPICTOGRAPHS",
    "SUPPLEMENTARYPRIVATEUSEAREAA",
    "SUPPLEMENTARYPRIVATEUSEAREAB",
    "SUPPUAA",
    "SUPPUAB",
    "SUPPUNCTUATION",
    "SUPSYMBOLSANDPICTOGRAPHS",
    "SURROGATE",
    "SUTTONSIGNWRITING",
    "SWASHKAF",
    "SY",
    "SYLLABLEMODIFIER",
    "SYLO",
    "SYLOTINAGRI",
    "SYMBOL",
    "SYRC",
    "SYRIAC",
    "SYRIACWAW",
    "T",
    "TAGALOG",
    "TAGB",
    "TAGBANWA",
    "TAGS",
    "TAH",
    "TAILE",
    "TAITHAM",
    "TAIVIET",
    "TAIXUANJING",
    "TAIXUANJINGSYMBOLS",
    "TAKR",
    "TAKRI",
    "TALE",
    "TALU",
    "TAMIL",
    "TAML",
    "TAVT",
    "TAW",
    "TEHMARBUTA",
    "TEHMARBUTAGOAL",
    "TELU",
    "TELUGU",
    "TERM",
    "TERMINALPUNCTUATION",
    "TETH",
    "TFNG",
    "TGLG",
    "THAA",
    "THAANA",
    "THAI",
    "TIBETAN",
    "TIBT",
    "TIFINAGH",
    "TIRH",
    "TIRHUTA",
    "TITLECASELETTER",
    "TONELETTER",
    "TONEMARK",
    "TOP",
    "TOPANDBOTTOM",
    "TOPANDBOTTOMANDRIGHT",
    "TOPANDLEFT",
    "TOPANDLEFTANDRIGHT",
    "TOPANDRIGHT",
    "TRAILINGJAMO",
    "TRANSPARENT",
    "TRANSPORTANDMAP",
    "TRANSPORTANDMAPSYMBOLS",
    "TRUE",
    "U",
    "UCAS",
    "UCASEXT",
    "UGAR",
    "UGARITIC",
    "UIDEO",
    "UNASSIGNED",
    "UNIFIEDCANADIANABORIGINALSYLLABICS",
    "UNIFIEDCANADIANABORIGINALSYLLABICSEXTENDED",
    "UNIFIEDIDEOGRAPH",
    "UNKNOWN",
    "UP",
    "UPPER",
    "UPPERCASE",
    "UPPERCASELETTER",
    "V",
    "VAI",
    "VAII",
    "VARIATIONSELECTOR",
    "VARIATIONSELECTORS",
    "VARIATIONSELECTORSSUPPLEMENT",
    "VEDICEXT",
    "VEDICEXTENSIONS",
    "VERT",
    "VERTICAL",
    "VERTICALFORMS",
    "VIRAMA",
    "VISARGA",
    "VISUALORDERLEFT",
    "VOWEL",
    "VOWELDEPENDENT",
    "VOWELINDEPENDENT",
    "VOWELJAMO",
    "VR",
    "VS",
    "VSSUP",
    "W",
    "WARA",
    "WARANGCITI",
    "WAW",
    "WB",
    "WHITESPACE",
    "WIDE",
    "WJ",
    "WORD",
    "WORDBREAK",
    "WORDJOINER",
    "WS",
    "WSPACE",
    "XDIGIT",
    "XIDC",
    "XIDCONTINUE",
    "XIDS",
    "XIDSTART",
    "XPEO",
    "XSUX",
    "XX",
    "Y",
    "YEH",
    "YEHBARREE",
    "YEHWITHTAIL",
    "YES",
    "YI",
    "YIII",
    "YIJING",
    "YIJINGHEXAGRAMSYMBOLS",
    "YIRADICALS",
    "YISYLLABLES",
    "YUDH",
    "YUDHHE",
    "Z",
    "Z&",
    "ZAIN",
    "ZHAIN",
    "ZINH",
    "ZL",
    "ZP",
    "ZS",
    "ZW",
    "ZWSPACE",
    "ZYYY",
    "ZZZZ",
};

/* strings: 12240 bytes. */

/* properties. */

RE_Property re_properties[] = {
    { 547,  0,  0},
    { 544,  0,  0},
    { 252,  1,  1},
    { 251,  1,  1},
    {1081,  2,  2},
    {1079,  2,  2},
    {1259,  3,  3},
    {1254,  3,  3},
    { 566,  4,  4},
    { 545,  4,  4},
    {1087,  5,  5},
    {1078,  5,  5},
    { 823,  6,  6},
    { 172,  7,  6},
    { 171,  7,  6},
    { 767,  8,  6},
    { 766,  8,  6},
    {1227,  9,  6},
    {1226,  9,  6},
    { 294, 10,  6},
    { 296, 11,  6},
    { 350, 11,  6},
    { 343, 12,  6},
    { 433, 12,  6},
    { 345, 13,  6},
    { 435, 13,  6},
    { 344, 14,  6},
    { 434, 14,  6},
    { 341, 15,  6},
    { 431, 15,  6},
    { 342, 16,  6},
    { 432, 16,  6},
    { 636, 17,  6},
    { 632, 17,  6},
    { 628, 18,  6},
    { 627, 18,  6},
    {1267, 19,  6},
    {1266, 19,  6},
    {1265, 20,  6},
    {1264, 20,  6},
    { 458, 21,  6},
    { 466, 21,  6},
    { 567, 22,  6},
    { 575, 22,  6},
    { 565, 23,  6},
    { 569, 23,  6},
    { 568, 24,  6},
    { 576, 24,  6},
    {1255, 25,  6},
    {1262, 25,  6},
    {1117, 25,  6},
    { 244, 26,  6},
    { 242, 26,  6},
    { 671, 27,  6},
    { 669, 27,  6},
    { 451, 28,  6},
    { 625, 29,  6},
    {1044, 30,  6},
    {1041, 30,  6},
    {1188, 31,  6},
    {1187, 31,  6},
    { 971, 32,  6},
    { 952, 32,  6},
    { 612, 33,  6},
    { 611, 33,  6},
    { 204, 34,  6},
    { 160, 34,  6},
    { 964, 35,  6},
    { 933, 35,  6},
    { 630, 36,  6},
    { 629, 36,  6},
    { 468, 37,  6},
    { 467, 37,  6},
    { 523, 38,  6},
    { 521, 38,  6},
    { 970, 39,  6},
    { 951, 39,  6},
    { 976, 40,  6},
    { 977, 40,  6},
    { 909, 41,  6},
    { 895, 41,  6},
    { 966, 42,  6},
    { 938, 42,  6},
    { 634, 43,  6},
    { 633, 43,  6},
    { 637, 44,  6},
    { 635, 44,  6},
    {1046, 45,  6},
    {1223, 46,  6},
    {1219, 46,  6},
    { 965, 47,  6},
    { 935, 47,  6},
    { 460, 48,  6},
    { 459, 48,  6},
    {1113, 49,  6},
    {1082, 49,  6},
    { 765, 50,  6},
    { 764, 50,  6},
    { 968, 51,  6},
    { 940, 51,  6},
    { 967, 52,  6},
    { 939, 52,  6},
    {1126, 53,  6},
    {1232, 54,  6},
    {1248, 54,  6},
    { 989, 55,  6},
    { 990, 55,  6},
    { 988, 56,  6},
    { 987, 56,  6},
    { 598, 57,  7},
    { 622, 57,  7},
    { 243, 58,  8},
    { 234, 58,  8},
    { 288, 59,  9},
    { 300, 59,  9},
    { 457, 60, 10},
    { 482, 60, 10},
    { 489, 61, 11},
    { 487, 61, 11},
    { 673, 62, 12},
    { 667, 62, 12},
    { 674, 63, 13},
    { 675, 63, 13},
    { 757, 64, 14},
    { 732, 64, 14},
    { 928, 65, 15},
    { 921, 65, 15},
    { 929, 66, 16},
    { 931, 66, 16},
    { 246, 67,  6},
    { 245, 67,  6},
    { 641, 68, 17},
    { 648, 68, 17},
    { 642, 69, 18},
    { 649, 69, 18},
    { 175, 70,  6},
    { 170, 70,  6},
    { 183, 71,  6},
    { 250, 72,  6},
    { 564, 73,  6},
    {1027, 74,  6},
    {1258, 75,  6},
    {1263, 76,  6},
    {1019, 77,  6},
    {1018, 78,  6},
    {1020, 79,  6},
    {1021, 80,  6},
};

/* properties: 588 bytes. */

/* property values. */

RE_PropertyValue re_property_values[] = {
    {1220,  0,   0},
    { 383,  0,   0},
    {1228,  0,   1},
    { 774,  0,   1},
    { 768,  0,   2},
    { 761,  0,   2},
    {1200,  0,   3},
    { 773,  0,   3},
    { 865,  0,   4},
    { 762,  0,   4},
    { 969,  0,   5},
    { 763,  0,   5},
    { 913,  0,   6},
    { 863,  0,   6},
    { 505,  0,   7},
    { 831,  0,   7},
    {1119,  0,   8},
    { 830,  0,   8},
    { 456,  0,   9},
    { 896,  0,   9},
    { 473,  0,   9},
    { 747,  0,  10},
    { 904,  0,  10},
    { 973,  0,  11},
    { 905,  0,  11},
    {1118,  0,  12},
    {1291,  0,  12},
    { 759,  0,  13},
    {1289,  0,  13},
    { 986,  0,  14},
    {1290,  0,  14},
    { 415,  0,  15},
    { 299,  0,  15},
    { 384,  0,  15},
    { 537,  0,  16},
    { 338,  0,  16},
    {1028,  0,  17},
    { 385,  0,  17},
    {1153,  0,  18},
    { 425,  0,  18},
    { 452,  0,  19},
    { 994,  0,  19},
    { 955,  0,  20},
    {1031,  0,  20},
    { 381,  0,  21},
    { 997,  0,  21},
    { 401,  0,  22},
    { 993,  0,  22},
    { 974,  0,  23},
    {1015,  0,  23},
    { 828,  0,  24},
    {1107,  0,  24},
    { 429,  0,  25},
    {1079,  0,  25},
    { 867,  0,  26},
    {1106,  0,  26},
    { 975,  0,  27},
    {1112,  0,  27},
    { 647,  0,  28},
    {1012,  0,  28},
    { 532,  0,  29},
    { 999,  0,  29},
    { 963,  0,  30},
    { 281,  0,  30},
    { 282,  0,  30},
    { 745,  0,  31},
    { 708,  0,  31},
    { 709,  0,  31},
    { 822,  0,  32},
    { 783,  0,  32},
    { 392,  0,  32},
    { 784,  0,  32},
    { 924,  0,  33},
    { 885,  0,  33},
    { 886,  0,  33},
    {1035,  0,  34},
    { 981,  0,  34},
    {1034,  0,  34},
    { 982,  0,  34},
    {1160,  0,  35},
    {1068,  0,  35},
    {1069,  0,  35},
    {1089,  0,  36},
    {1284,  0,  36},
    {1285,  0,  36},
    { 295,  0,  37},
    { 733,  0,  37},
    { 205,  0,  38},
    { 906,  1,   0},
    { 893,  1,   0},
    { 228,  1,   1},
    { 203,  1,   1},
    { 718,  1,   2},
    { 717,  1,   2},
    { 716,  1,   2},
    { 725,  1,   3},
    { 719,  1,   3},
    { 727,  1,   4},
    { 721,  1,   4},
    { 657,  1,   5},
    { 656,  1,   5},
    {1120,  1,   6},
    { 866,  1,   6},
    { 387,  1,   7},
    { 469,  1,   7},
    { 571,  1,   8},
    { 570,  1,   8},
    { 438,  1,   9},
    { 444,  1,  10},
    { 443,  1,  10},
    { 445,  1,  10},
    { 199,  1,  11},
    { 606,  1,  12},
    { 186,  1,  13},
    {1162,  1,  14},
    { 198,  1,  15},
    { 197,  1,  15},
    {1193,  1,  16},
    { 902,  1,  17},
    {1073,  1,  18},
    { 791,  1,  19},
    { 188,  1,  20},
    { 187,  1,  20},
    { 463,  1,  21},
    { 240,  1,  22},
    { 579,  1,  23},
    { 577,  1,  24},
    { 957,  1,  25},
    {1179,  1,  26},
    {1186,  1,  27},
    { 688,  1,  28},
    { 789,  1,  29},
    {1104,  1,  30},
    {1194,  1,  31},
    { 713,  1,  32},
    {1195,  1,  33},
    { 879,  1,  34},
    { 553,  1,  35},
    { 594,  1,  36},
    { 662,  1,  36},
    { 509,  1,  37},
    { 515,  1,  38},
    { 514,  1,  38},
    { 347,  1,  39},
    {1221,  1,  40},
    {1215,  1,  40},
    { 286,  1,  40},
    { 937,  1,  41},
    {1066,  1,  42},
    {1165,  1,  43},
    { 601,  1,  44},
    { 277,  1,  45},
    {1167,  1,  46},
    { 698,  1,  47},
    { 871,  1,  48},
    {1222,  1,  49},
    {1216,  1,  49},
    { 750,  1,  50},
    {1170,  1,  51},
    { 899,  1,  52},
    { 699,  1,  53},
    { 275,  1,  54},
    {1171,  1,  55},
    { 388,  1,  56},
    { 470,  1,  56},
    { 223,  1,  57},
    {1130,  1,  58},
    { 231,  1,  59},
    { 744,  1,  60},
    { 941,  1,  61},
    {1132,  1,  62},
    {1131,  1,  62},
    {1236,  1,  63},
    {1235,  1,  63},
    {1009,  1,  64},
    {1008,  1,  64},
    {1010,  1,  65},
    {1011,  1,  65},
    { 390,  1,  66},
    { 472,  1,  66},
    { 726,  1,  67},
    { 720,  1,  67},
    { 573,  1,  68},
    { 572,  1,  68},
    { 548,  1,  69},
    {1035,  1,  69},
    {1139,  1,  70},
    {1138,  1,  70},
    { 430,  1,  71},
    { 389,  1,  72},
    { 471,  1,  72},
    { 393,  1,  72},
    { 746,  1,  73},
    { 925,  1,  74},
    { 202,  1,  75},
    { 826,  1,  76},
    { 827,  1,  76},
    { 855,  1,  77},
    { 860,  1,  77},
    { 416,  1,  78},
    { 956,  1,  79},
    { 934,  1,  79},
    { 498,  1,  80},
    { 497,  1,  80},
    { 262,  1,  81},
    { 253,  1,  82},
    { 549,  1,  83},
    { 852,  1,  84},
    { 859,  1,  84},
    { 474,  1,  85},
    { 850,  1,  86},
    { 856,  1,  86},
    {1141,  1,  87},
    {1134,  1,  87},
    { 269,  1,  88},
    { 268,  1,  88},
    {1142,  1,  89},
    {1135,  1,  89},
    { 851,  1,  90},
    { 857,  1,  90},
    {1144,  1,  91},
    {1140,  1,  91},
    { 853,  1,  92},
    { 849,  1,  92},
    { 558,  1,  93},
    { 728,  1,  94},
    { 722,  1,  94},
    { 418,  1,  95},
    { 555,  1,  96},
    { 554,  1,  96},
    {1197,  1,  97},
    { 512,  1,  98},
    { 510,  1,  98},
    { 441,  1,  99},
    { 439,  1,  99},
    {1145,  1, 100},
    {1151,  1, 100},
    { 368,  1, 101},
    { 367,  1, 101},
    { 687,  1, 102},
    { 686,  1, 102},
    { 631,  1, 103},
    { 627,  1, 103},
    { 371,  1, 104},
    { 370,  1, 104},
    { 617,  1, 105},
    { 690,  1, 106},
    { 256,  1, 107},
    { 593,  1, 108},
    { 398,  1, 108},
    { 685,  1, 109},
    { 258,  1, 110},
    { 257,  1, 110},
    { 369,  1, 111},
    { 693,  1, 112},
    { 691,  1, 112},
    { 502,  1, 113},
    { 501,  1, 113},
    { 356,  1, 114},
    { 354,  1, 114},
    { 373,  1, 115},
    { 362,  1, 115},
    {1279,  1, 116},
    {1278,  1, 116},
    { 372,  1, 117},
    { 353,  1, 117},
    {1281,  1, 118},
    {1280,  1, 119},
    { 760,  1, 120},
    {1230,  1, 121},
    { 442,  1, 122},
    { 440,  1, 122},
    { 225,  1, 123},
    { 868,  1, 124},
    { 729,  1, 125},
    { 723,  1, 125},
    {1159,  1, 126},
    { 395,  1, 127},
    { 640,  1, 127},
    {1001,  1, 128},
    {1077,  1, 129},
    { 465,  1, 130},
    { 464,  1, 130},
    { 694,  1, 131},
    {1050,  1, 132},
    { 595,  1, 133},
    { 663,  1, 133},
    { 666,  1, 134},
    { 883,  1, 135},
    { 881,  1, 135},
    { 340,  1, 136},
    { 882,  1, 137},
    { 880,  1, 137},
    {1172,  1, 138},
    { 837,  1, 139},
    { 836,  1, 139},
    { 513,  1, 140},
    { 511,  1, 140},
    { 730,  1, 141},
    { 724,  1, 141},
    { 349,  1, 142},
    { 348,  1, 142},
    { 835,  1, 143},
    { 597,  1, 144},
    { 592,  1, 144},
    { 596,  1, 145},
    { 664,  1, 145},
    { 615,  1, 146},
    { 613,  1, 147},
    { 614,  1, 147},
    { 769,  1, 148},
    {1029,  1, 149},
    {1033,  1, 149},
    {1028,  1, 149},
    { 358,  1, 150},
    { 360,  1, 150},
    { 174,  1, 151},
    { 173,  1, 151},
    { 195,  1, 152},
    { 193,  1, 152},
    {1233,  1, 153},
    {1248,  1, 153},
    {1239,  1, 154},
    { 391,  1, 155},
    { 586,  1, 155},
    { 357,  1, 156},
    { 355,  1, 156},
    {1110,  1, 157},
    {1109,  1, 157},
    { 196,  1, 158},
    { 194,  1, 158},
    { 588,  1, 159},
    { 585,  1, 159},
    {1121,  1, 160},
    { 756,  1, 161},
    { 755,  1, 162},
    { 158,  1, 163},
    { 181,  1, 164},
    { 182,  1, 165},
    {1003,  1, 166},
    {1002,  1, 166},
    { 780,  1, 167},
    { 292,  1, 168},
    { 419,  1, 169},
    { 944,  1, 170},
    { 561,  1, 171},
    { 946,  1, 172},
    {1218,  1, 173},
    { 947,  1, 174},
    { 461,  1, 175},
    {1093,  1, 176},
    { 962,  1, 177},
    { 493,  1, 178},
    { 297,  1, 179},
    { 753,  1, 180},
    { 437,  1, 181},
    { 638,  1, 182},
    { 985,  1, 183},
    { 888,  1, 184},
    { 603,  1, 185},
    {1007,  1, 186},
    { 782,  1, 187},
    { 843,  1, 188},
    { 842,  1, 189},
    { 697,  1, 190},
    { 948,  1, 191},
    { 945,  1, 192},
    { 794,  1, 193},
    { 217,  1, 194},
    { 651,  1, 195},
    { 650,  1, 196},
    {1032,  1, 197},
    { 949,  1, 198},
    { 943,  1, 199},
    {1065,  1, 200},
    {1064,  1, 200},
    { 265,  1, 201},
    { 679,  1, 202},
    {1115,  1, 203},
    { 339,  1, 204},
    { 785,  1, 205},
    {1092,  1, 206},
    {1105,  1, 207},
    { 702,  1, 208},
    { 876,  1, 209},
    { 703,  1, 210},
    { 563,  1, 211},
    {1199,  1, 212},
    {1099,  1, 213},
    { 864,  1, 214},
    {1176,  1, 215},
    { 161,  1, 216},
    {1252,  1, 217},
    { 992,  1, 218},
    { 426,  1, 219},
    { 428,  1, 220},
    { 427,  1, 220},
    { 488,  1, 221},
    { 491,  1, 222},
    { 178,  1, 223},
    { 227,  1, 224},
    { 226,  1, 224},
    { 872,  1, 225},
    { 230,  1, 226},
    { 983,  1, 227},
    { 844,  1, 228},
    { 683,  1, 229},
    { 682,  1, 229},
    { 485,  1, 230},
    {1096,  1, 231},
    { 280,  1, 232},
    { 279,  1, 232},
    { 878,  1, 233},
    { 877,  1, 233},
    { 180,  1, 234},
    { 179,  1, 234},
    {1174,  1, 235},
    {1173,  1, 235},
    { 421,  1, 236},
    { 420,  1, 236},
    { 825,  1, 237},
    { 824,  1, 237},
    {1154,  1, 238},
    { 839,  1, 239},
    { 191,  1, 240},
    { 190,  1, 240},
    { 788,  1, 241},
    { 787,  1, 241},
    { 476,  1, 242},
    { 475,  1, 242},
    {1013,  1, 243},
    { 499,  1, 244},
    { 500,  1, 244},
    { 504,  1, 245},
    { 503,  1, 245},
    { 854,  1, 246},
    { 858,  1, 246},
    { 494,  1, 247},
    { 959,  1, 248},
    {1212,  1, 249},
    {1211,  1, 249},
    { 167,  1, 250},
    { 166,  1, 250},
    { 551,  1, 251},
    { 550,  1, 251},
    {1143,  1, 252},
    {1136,  1, 252},
    {1146,  1, 253},
    {1152,  1, 253},
    { 374,  1, 254},
    { 363,  1, 254},
    { 375,  1, 255},
    { 364,  1, 255},
    { 376,  1, 256},
    { 365,  1, 256},
    { 377,  1, 257},
    { 366,  1, 257},
    { 359,  1, 258},
    { 361,  1, 258},
    {1168,  1, 259},
    {1234,  1, 260},
    {1249,  1, 260},
    {1147,  1, 261},
    {1149,  1, 261},
    {1148,  1, 262},
    {1150,  1, 262},
    {1224,  2,   0},
    {1295,  2,   0},
    { 394,  2,   1},
    {1294,  2,   1},
    { 715,  2,   2},
    { 731,  2,   2},
    { 570,  2,   3},
    { 574,  2,   3},
    { 438,  2,   4},
    { 446,  2,   4},
    { 199,  2,   5},
    { 201,  2,   5},
    { 606,  2,   6},
    { 605,  2,   6},
    { 186,  2,   7},
    { 185,  2,   7},
    {1162,  2,   8},
    {1161,  2,   8},
    {1193,  2,   9},
    {1192,  2,   9},
    { 463,  2,  10},
    { 462,  2,  10},
    { 240,  2,  11},
    { 239,  2,  11},
    { 579,  2,  12},
    { 580,  2,  12},
    { 577,  2,  13},
    { 578,  2,  13},
    { 957,  2,  14},
    { 960,  2,  14},
    {1179,  2,  15},
    {1180,  2,  15},
    {1186,  2,  16},
    {1185,  2,  16},
    { 688,  2,  17},
    { 704,  2,  17},
    { 789,  2,  18},
    { 862,  2,  18},
    {1104,  2,  19},
    {1103,  2,  19},
    {1194,  2,  20},
    { 713,  2,  21},
    { 714,  2,  21},
    {1195,  2,  22},
    {1196,  2,  22},
    { 879,  2,  23},
    { 884,  2,  23},
    { 553,  2,  24},
    { 552,  2,  24},
    { 592,  2,  25},
    { 591,  2,  25},
    { 509,  2,  26},
    { 508,  2,  26},
    { 347,  2,  27},
    { 346,  2,  27},
    { 285,  2,  28},
    { 289,  2,  28},
    { 937,  2,  29},
    { 936,  2,  29},
    {1066,  2,  30},
    {1067,  2,  30},
    { 698,  2,  31},
    { 700,  2,  31},
    { 871,  2,  32},
    { 870,  2,  32},
    { 617,  2,  33},
    { 616,  2,  33},
    { 690,  2,  34},
    { 681,  2,  34},
    { 256,  2,  35},
    { 255,  2,  35},
    { 590,  2,  36},
    { 599,  2,  36},
    {1276,  2,  37},
    {1277,  2,  37},
    { 944,  2,  38},
    { 661,  2,  38},
    { 561,  2,  39},
    { 560,  2,  39},
    { 461,  2,  40},
    { 481,  2,  40},
    { 644,  2,  41},
    {1288,  2,  41},
    {1038,  2,  41},
    {1165,  2,  42},
    {1191,  2,  42},
    { 601,  2,  43},
    { 600,  2,  43},
    { 277,  2,  44},
    { 276,  2,  44},
    {1167,  2,  45},
    {1166,  2,  45},
    { 750,  2,  46},
    { 749,  2,  46},
    {1170,  2,  47},
    {1177,  2,  47},
    { 754,  2,  48},
    { 752,  2,  48},
    {1218,  2,  49},
    {1217,  2,  49},
    {1093,  2,  50},
    {1094,  2,  50},
    { 962,  2,  51},
    { 961,  2,  51},
    { 436,  2,  52},
    { 423,  2,  52},
    { 268,  2,  53},
    { 267,  2,  53},
    { 275,  2,  54},
    { 274,  2,  54},
    { 418,  2,  55},
    { 417,  2,  55},
    {1037,  2,  55},
    { 899,  2,  56},
    {1178,  2,  56},
    { 558,  2,  57},
    { 557,  2,  57},
    {1197,  2,  58},
    {1190,  2,  58},
    {1159,  2,  59},
    {1158,  2,  59},
    { 947,  2,  60},
    {1268,  2,  60},
    { 697,  2,  61},
    { 696,  2,  61},
    { 223,  2,  62},
    { 222,  2,  62},
    { 426,  2,  63},
    {1269,  2,  63},
    {1007,  2,  64},
    {1006,  2,  64},
    {1001,  2,  65},
    {1000,  2,  65},
    { 902,  2,  66},
    { 903,  2,  66},
    {1130,  2,  67},
    {1129,  2,  67},
    { 744,  2,  68},
    { 743,  2,  68},
    { 941,  2,  69},
    { 942,  2,  69},
    {1230,  2,  70},
    {1231,  2,  70},
    {1077,  2,  71},
    {1076,  2,  71},
    { 694,  2,  72},
    { 680,  2,  72},
    {1050,  2,  73},
    {1059,  2,  73},
    { 780,  2,  74},
    { 779,  2,  74},
    { 292,  2,  75},
    { 291,  2,  75},
    { 782,  2,  76},
    { 781,  2,  76},
    { 340,  2,  77},
    {1171,  2,  78},
    { 712,  2,  78},
    {1172,  2,  79},
    {1181,  2,  79},
    { 217,  2,  80},
    { 218,  2,  80},
    { 491,  2,  81},
    { 490,  2,  81},
    {1073,  2,  82},
    {1074,  2,  82},
    { 760,  2,  83},
    { 225,  2,  84},
    { 224,  2,  84},
    { 666,  2,  85},
    { 665,  2,  85},
    { 835,  2,  86},
    { 874,  2,  86},
    { 638,  2,  87},
    { 200,  2,  87},
    { 948,  2,  88},
    {1075,  2,  88},
    { 651,  2,  89},
    {1030,  2,  89},
    { 650,  2,  90},
    {1004,  2,  90},
    { 949,  2,  91},
    { 958,  2,  91},
    { 679,  2,  92},
    { 706,  2,  92},
    { 231,  2,  93},
    { 232,  2,  93},
    { 265,  2,  94},
    { 264,  2,  94},
    { 791,  2,  95},
    { 790,  2,  95},
    { 339,  2,  96},
    { 283,  2,  96},
    { 842,  2,  97},
    { 840,  2,  97},
    { 843,  2,  98},
    { 841,  2,  98},
    { 844,  2,  99},
    {1014,  2,  99},
    {1092,  2, 100},
    {1097,  2, 100},
    {1115,  2, 101},
    {1114,  2, 101},
    {1176,  2, 102},
    {1175,  2, 102},
    { 297,  2, 103},
    { 159,  2, 103},
    { 230,  2, 104},
    { 229,  2, 104},
    { 485,  2, 105},
    { 484,  2, 105},
    { 493,  2, 106},
    { 492,  2, 106},
    { 563,  2, 107},
    { 562,  2, 107},
    { 983,  2, 108},
    { 620,  2, 108},
    { 702,  2, 109},
    { 701,  2, 109},
    { 753,  2, 110},
    { 751,  2, 110},
    { 785,  2, 111},
    { 786,  2, 111},
    { 794,  2, 112},
    { 793,  2, 112},
    { 839,  2, 113},
    { 838,  2, 113},
    { 864,  2, 114},
    { 872,  2, 115},
    { 873,  2, 115},
    { 945,  2, 116},
    { 891,  2, 116},
    { 888,  2, 117},
    { 894,  2, 117},
    { 985,  2, 118},
    { 984,  2, 118},
    { 992,  2, 119},
    { 991,  2, 119},
    { 946,  2, 120},
    { 998,  2, 120},
    {1032,  2, 121},
    {1005,  2, 121},
    {1099,  2, 122},
    {1098,  2, 122},
    { 703,  2, 123},
    {1101,  2, 123},
    {1199,  2, 124},
    {1198,  2, 124},
    {1252,  2, 125},
    {1251,  2, 125},
    { 161,  2, 126},
    { 178,  2, 127},
    { 619,  2, 127},
    { 603,  2, 128},
    { 602,  2, 128},
    { 876,  2, 129},
    { 875,  2, 129},
    { 943,  2, 130},
    { 623,  2, 130},
    {1100,  2, 131},
    {1091,  2, 131},
    { 692,  2, 132},
    { 621,  2, 132},
    { 963,  3,   0},
    {1270,  3,   0},
    { 479,  3,   1},
    { 480,  3,   1},
    {1102,  3,   2},
    {1122,  3,   2},
    { 607,  3,   3},
    { 618,  3,   3},
    { 424,  3,   4},
    { 748,  3,   5},
    { 898,  3,   6},
    { 904,  3,   6},
    { 522,  3,   7},
    {1047,  3,   8},
    {1052,  3,   8},
    { 537,  3,   9},
    { 535,  3,   9},
    { 690,  3,  10},
    { 677,  3,  10},
    { 169,  3,  11},
    { 734,  3,  11},
    { 845,  3,  12},
    { 861,  3,  12},
    { 846,  3,  13},
    { 863,  3,  13},
    { 847,  3,  14},
    { 829,  3,  14},
    { 927,  3,  15},
    { 922,  3,  15},
    { 524,  3,  16},
    { 519,  3,  16},
    { 963,  4,   0},
    {1270,  4,   0},
    { 424,  4,   1},
    { 748,  4,   2},
    { 415,  4,   3},
    { 383,  4,   3},
    { 522,  4,   4},
    { 519,  4,   4},
    {1047,  4,   5},
    {1052,  4,   5},
    {1119,  4,   6},
    {1107,  4,   6},
    { 708,  4,   7},
    {1229,  4,   8},
    {1164,  4,   9},
    { 775,  4,  10},
    { 777,  4,  11},
    {1026,  4,  12},
    {1023,  4,  12},
    { 963,  5,   0},
    {1270,  5,   0},
    { 424,  5,   1},
    { 748,  5,   2},
    { 522,  5,   3},
    { 519,  5,   3},
    {1088,  5,   4},
    {1083,  5,   4},
    { 537,  5,   5},
    { 535,  5,   5},
    {1116,  5,   6},
    { 766,  5,   7},
    { 763,  5,   7},
    {1226,  5,   8},
    {1225,  5,   8},
    { 950,  5,   9},
    { 734,  5,   9},
    { 927,  5,  10},
    { 922,  5,  10},
    { 211,  5,  11},
    { 206,  5,  11},
    {1126,  5,  12},
    {1125,  5,  12},
    { 379,  5,  13},
    { 378,  5,  13},
    {1080,  5,  14},
    {1079,  5,  14},
    { 905,  6,   0},
    { 885,  6,   0},
    { 525,  6,   0},
    { 526,  6,   0},
    {1275,  6,   1},
    {1271,  6,   1},
    {1164,  6,   1},
    {1213,  6,   1},
    { 916,  7,   0},
    { 887,  7,   0},
    { 735,  7,   1},
    { 708,  7,   1},
    {1246,  7,   2},
    {1229,  7,   2},
    {1209,  7,   3},
    {1164,  7,   3},
    { 776,  7,   4},
    { 775,  7,   4},
    { 778,  7,   5},
    { 777,  7,   5},
    { 739,  8,   0},
    { 708,  8,   0},
    {1055,  8,   1},
    {1045,  8,   1},
    { 516,  8,   2},
    { 495,  8,   2},
    { 517,  8,   3},
    { 506,  8,   3},
    { 518,  8,   4},
    { 507,  8,   4},
    { 192,  8,   5},
    { 177,  8,   5},
    { 396,  8,   6},
    { 425,  8,   6},
    { 986,  8,   7},
    { 219,  8,   7},
    {1085,  8,   8},
    {1068,  8,   8},
    {1255,  8,   9},
    {1261,  8,   9},
    { 972,  8,  10},
    { 953,  8,  10},
    { 261,  8,  11},
    { 254,  8,  11},
    { 913,  8,  12},
    { 920,  8,  12},
    { 189,  8,  13},
    { 164,  8,  13},
    { 742,  8,  14},
    { 772,  8,  14},
    {1058,  8,  15},
    {1062,  8,  15},
    { 740,  8,  16},
    { 770,  8,  16},
    {1056,  8,  17},
    {1060,  8,  17},
    {1016,  8,  18},
    { 995,  8,  18},
    { 741,  8,  19},
    { 771,  8,  19},
    {1057,  8,  20},
    {1061,  8,  20},
    { 534,  8,  21},
    { 540,  8,  21},
    {1017,  8,  22},
    { 996,  8,  22},
    { 917,  9,   0},
    {   1,  9,   0},
    { 918,  9,   0},
    { 979,  9,   1},
    {   2,  9,   1},
    { 978,  9,   1},
    { 923,  9,   2},
    { 130,  9,   2},
    { 901,  9,   2},
    { 684,  9,   3},
    { 139,  9,   3},
    { 707,  9,   3},
    {1240,  9,   4},
    { 146,  9,   4},
    {1247,  9,   4},
    { 301,  9,   5},
    {  14,  9,   5},
    { 304,  9,   6},
    {  25,  9,   6},
    { 306,  9,   7},
    {  29,  9,   7},
    { 309,  9,   8},
    {  32,  9,   8},
    { 313,  9,   9},
    {  37,  9,   9},
    { 314,  9,  10},
    {  38,  9,  10},
    { 315,  9,  11},
    {  40,  9,  11},
    { 316,  9,  12},
    {  41,  9,  12},
    { 317,  9,  13},
    {  43,  9,  13},
    { 318,  9,  14},
    {  44,  9,  14},
    { 319,  9,  15},
    {  48,  9,  15},
    { 320,  9,  16},
    {  54,  9,  16},
    { 321,  9,  17},
    {  59,  9,  17},
    { 322,  9,  18},
    {  65,  9,  18},
    { 323,  9,  19},
    {  70,  9,  19},
    { 324,  9,  20},
    {  72,  9,  20},
    { 325,  9,  21},
    {  73,  9,  21},
    { 326,  9,  22},
    {  74,  9,  22},
    { 327,  9,  23},
    {  75,  9,  23},
    { 328,  9,  24},
    {  76,  9,  24},
    { 329,  9,  25},
    {  83,  9,  25},
    { 330,  9,  26},
    {  88,  9,  26},
    { 331,  9,  27},
    {  89,  9,  27},
    { 332,  9,  28},
    {  90,  9,  28},
    { 333,  9,  29},
    {  91,  9,  29},
    { 334,  9,  30},
    {  92,  9,  30},
    { 335,  9,  31},
    {  93,  9,  31},
    { 336,  9,  32},
    { 145,  9,  32},
    { 337,  9,  33},
    { 153,  9,  33},
    { 302,  9,  34},
    {  23,  9,  34},
    { 303,  9,  35},
    {  24,  9,  35},
    { 305,  9,  36},
    {  28,  9,  36},
    { 307,  9,  37},
    {  30,  9,  37},
    { 308,  9,  38},
    {  31,  9,  38},
    { 310,  9,  39},
    {  34,  9,  39},
    { 311,  9,  40},
    {  35,  9,  40},
    { 214,  9,  41},
    {  53,  9,  41},
    { 209,  9,  41},
    { 212,  9,  42},
    {  55,  9,  42},
    { 207,  9,  42},
    { 213,  9,  43},
    {  56,  9,  43},
    { 208,  9,  43},
    { 237,  9,  44},
    {  58,  9,  44},
    { 249,  9,  44},
    { 236,  9,  45},
    {  60,  9,  45},
    { 219,  9,  45},
    { 238,  9,  46},
    {  61,  9,  46},
    { 263,  9,  46},
    { 736,  9,  47},
    {  62,  9,  47},
    { 708,  9,  47},
    {1053,  9,  48},
    {  63,  9,  48},
    {1045,  9,  48},
    { 156,  9,  49},
    {  64,  9,  49},
    { 164,  9,  49},
    { 155,  9,  50},
    {  66,  9,  50},
    { 154,  9,  50},
    { 157,  9,  51},
    {  67,  9,  51},
    { 184,  9,  51},
    { 478,  9,  52},
    {  68,  9,  52},
    { 453,  9,  52},
    { 477,  9,  53},
    {  69,  9,  53},
    { 448,  9,  53},
    { 655,  9,  54},
    {  71,  9,  54},
    { 658,  9,  54},
    { 312,  9,  55},
    {  36,  9,  55},
    { 215,  9,  56},
    {  49,  9,  56},
    { 210,  9,  56},
    { 910, 10,   0},
    { 287, 10,   1},
    { 284, 10,   1},
    { 397, 10,   2},
    { 386, 10,   2},
    { 536, 10,   3},
    { 907, 10,   4},
    { 893, 10,   4},
    { 646, 10,   5},
    { 645, 10,   5},
    { 833, 10,   6},
    { 832, 10,   6},
    { 531, 10,   7},
    { 530, 10,   7},
    { 660, 10,   8},
    { 659, 10,   8},
    { 351, 10,   9},
    { 496, 10,   9},
    {1137, 10,  10},
    {1133, 10,  10},
    {1128, 10,  11},
    {1238, 10,  12},
    {1237, 10,  12},
    {1256, 10,  13},
    { 892, 10,  14},
    { 890, 10,  14},
    {1108, 10,  15},
    {1111, 10,  15},
    {1124, 10,  16},
    {1123, 10,  16},
    { 539, 10,  17},
    { 538, 10,  17},
    { 897, 11,   0},
    { 885, 11,   0},
    { 176, 11,   1},
    { 154, 11,   1},
    { 587, 11,   2},
    { 581, 11,   2},
    {1256, 11,   3},
    {1250, 11,   3},
    { 541, 11,   4},
    { 525, 11,   4},
    { 892, 11,   5},
    { 887, 11,   5},
    { 908, 12,   0},
    { 163, 12,   1},
    { 165, 12,   2},
    { 168, 12,   3},
    { 235, 12,   4},
    { 241, 12,   5},
    { 449, 12,   6},
    { 450, 12,   7},
    { 486, 12,   8},
    { 529, 12,   9},
    { 533, 12,  10},
    { 542, 12,  11},
    { 543, 12,  12},
    { 584, 12,  13},
    { 589, 12,  14},
    {1184, 12,  14},
    { 604, 12,  15},
    { 608, 12,  16},
    { 609, 12,  17},
    { 610, 12,  18},
    { 678, 12,  19},
    { 689, 12,  20},
    { 705, 12,  21},
    { 710, 12,  22},
    { 711, 12,  23},
    { 834, 12,  24},
    { 848, 12,  25},
    { 915, 12,  26},
    { 930, 12,  27},
    { 997, 12,  28},
    {1039, 12,  29},
    {1040, 12,  30},
    {1049, 12,  31},
    {1051, 12,  32},
    {1071, 12,  33},
    {1072, 12,  34},
    {1084, 12,  35},
    {1086, 12,  36},
    {1095, 12,  37},
    {1155, 12,  38},
    {1169, 12,  39},
    {1182, 12,  40},
    {1183, 12,  41},
    {1189, 12,  42},
    {1253, 12,  43},
    {1163, 12,  44},
    {1272, 12,  45},
    {1273, 12,  46},
    {1274, 12,  47},
    {1282, 12,  48},
    {1283, 12,  49},
    {1286, 12,  50},
    {1287, 12,  51},
    { 695, 12,  52},
    { 528, 12,  53},
    { 278, 12,  54},
    { 527, 12,  55},
    { 932, 12,  56},
    {1063, 12,  57},
    {1127, 12,  58},
    { 795, 12,  59},
    { 796, 12,  60},
    { 797, 12,  61},
    { 798, 12,  62},
    { 799, 12,  63},
    { 800, 12,  64},
    { 801, 12,  65},
    { 802, 12,  66},
    { 803, 12,  67},
    { 804, 12,  68},
    { 805, 12,  69},
    { 806, 12,  70},
    { 807, 12,  71},
    { 808, 12,  72},
    { 809, 12,  73},
    { 810, 12,  74},
    { 811, 12,  75},
    { 812, 12,  76},
    { 813, 12,  77},
    { 814, 12,  78},
    { 815, 12,  79},
    { 816, 12,  80},
    { 817, 12,  81},
    { 818, 12,  82},
    { 819, 12,  83},
    { 820, 12,  84},
    { 821, 12,  85},
    { 912, 13,   0},
    {1214, 13,   0},
    { 670, 13,   1},
    { 281, 13,   1},
    { 483, 13,   2},
    { 447, 13,   2},
    {1054, 13,   3},
    {1045, 13,   3},
    { 738, 13,   4},
    { 708, 13,   4},
    {1210, 13,   5},
    {1164, 13,   5},
    {1224, 14,   0},
    {1270, 14,   0},
    { 955, 14,   1},
    { 954, 14,   1},
    { 381, 14,   2},
    { 378, 14,   2},
    {1043, 14,   3},
    {1042, 14,   3},
    { 559, 14,   4},
    { 556, 14,   4},
    { 914, 14,   5},
    { 919, 14,   5},
    { 520, 14,   6},
    { 519, 14,   6},
    { 273, 14,   7},
    {1156, 14,   7},
    { 643, 14,   8},
    { 658, 14,   8},
    {1025, 14,   9},
    {1024, 14,   9},
    {1022, 14,  10},
    {1015, 14,  10},
    { 927, 14,  11},
    { 922, 14,  11},
    { 172, 14,  12},
    { 164, 14,  12},
    { 630, 14,  13},
    { 626, 14,  13},
    { 652, 14,  14},
    { 639, 14,  14},
    { 653, 14,  14},
    { 625, 14,  15},
    { 624, 14,  15},
    { 392, 14,  16},
    { 382, 14,  16},
    { 271, 14,  17},
    { 233, 14,  17},
    { 270, 14,  18},
    { 221, 14,  18},
    {1117, 14,  19},
    {1116, 14,  19},
    { 792, 14,  20},
    { 248, 14,  20},
    { 293, 14,  21},
    { 424, 14,  21},
    { 758, 14,  22},
    { 748, 14,  22},
    { 414, 14,  23},
    { 298, 14,  23},
    { 399, 14,  24},
    {1070, 14,  24},
    { 176, 14,  25},
    { 162, 14,  25},
    { 272, 14,  26},
    { 220, 14,  26},
    {1153, 14,  27},
    {1090, 14,  27},
    {1293, 14,  28},
    {1292, 14,  28},
    { 900, 14,  29},
    { 904, 14,  29},
    {1260, 14,  30},
    {1257, 14,  30},
    { 668, 14,  31},
    { 676, 14,  32},
    { 675, 14,  33},
    { 582, 14,  34},
    { 583, 14,  35},
    { 380, 14,  36},
    { 422, 14,  36},
    { 607, 14,  37},
    { 618, 14,  37},
    { 400, 14,  38},
    { 352, 14,  38},
    {1047, 14,  39},
    {1052, 14,  39},
    { 910, 15,   0},
    { 927, 15,   1},
    { 922, 15,   1},
    { 473, 15,   2},
    { 466, 15,   2},
    { 455, 15,   3},
    { 454, 15,   3},
    { 889, 16,   0},
    {   0, 16,   1},
    {   1, 16,   2},
    {   5, 16,   3},
    {   4, 16,   4},
    {   3, 16,   5},
    {  13, 16,   6},
    {  12, 16,   7},
    {  11, 16,   8},
    {  10, 16,   9},
    {  78, 16,  10},
    {   9, 16,  11},
    {   8, 16,  12},
    {   7, 16,  13},
    {  82, 16,  14},
    {  47, 16,  15},
    { 115, 16,  16},
    {   6, 16,  17},
    { 131, 16,  18},
    {  81, 16,  19},
    { 118, 16,  20},
    {  46, 16,  21},
    {  80, 16,  22},
    {  98, 16,  23},
    { 117, 16,  24},
    { 133, 16,  25},
    {  26, 16,  26},
    {   2, 16,  27},
    {  79, 16,  28},
    {  45, 16,  29},
    { 116, 16,  30},
    {  77, 16,  31},
    { 132, 16,  32},
    {  97, 16,  33},
    { 147, 16,  34},
    { 114, 16,  35},
    {  27, 16,  36},
    { 124, 16,  37},
    {  33, 16,  38},
    { 130, 16,  39},
    {  39, 16,  40},
    { 139, 16,  41},
    {  42, 16,  42},
    { 146, 16,  43},
    {  14, 16,  44},
    {  25, 16,  45},
    {  29, 16,  46},
    {  32, 16,  47},
    {  37, 16,  48},
    {  38, 16,  49},
    {  40, 16,  50},
    {  41, 16,  51},
    {  43, 16,  52},
    {  44, 16,  53},
    {  48, 16,  54},
    {  54, 16,  55},
    {  59, 16,  56},
    {  65, 16,  57},
    {  70, 16,  58},
    {  72, 16,  59},
    {  73, 16,  60},
    {  74, 16,  61},
    {  75, 16,  62},
    {  76, 16,  63},
    {  83, 16,  64},
    {  88, 16,  65},
    {  89, 16,  66},
    {  90, 16,  67},
    {  91, 16,  68},
    {  92, 16,  69},
    {  93, 16,  70},
    {  94, 16,  71},
    {  95, 16,  72},
    {  96, 16,  73},
    {  99, 16,  74},
    { 104, 16,  75},
    { 105, 16,  76},
    { 106, 16,  77},
    { 108, 16,  78},
    { 109, 16,  79},
    { 110, 16,  80},
    { 111, 16,  81},
    { 112, 16,  82},
    { 113, 16,  83},
    { 119, 16,  84},
    { 125, 16,  85},
    { 134, 16,  86},
    { 140, 16,  87},
    { 148, 16,  88},
    {  15, 16,  89},
    {  49, 16,  90},
    {  84, 16,  91},
    { 100, 16,  92},
    { 120, 16,  93},
    { 126, 16,  94},
    { 135, 16,  95},
    { 141, 16,  96},
    { 149, 16,  97},
    {  16, 16,  98},
    {  50, 16,  99},
    {  85, 16, 100},
    { 101, 16, 101},
    { 121, 16, 102},
    { 127, 16, 103},
    { 136, 16, 104},
    { 142, 16, 105},
    { 150, 16, 106},
    {  17, 16, 107},
    {  51, 16, 108},
    {  86, 16, 109},
    { 102, 16, 110},
    { 122, 16, 111},
    { 128, 16, 112},
    { 137, 16, 113},
    { 143, 16, 114},
    { 151, 16, 115},
    {  18, 16, 116},
    {  52, 16, 117},
    {  57, 16, 118},
    {  87, 16, 119},
    { 103, 16, 120},
    { 107, 16, 121},
    { 123, 16, 122},
    { 129, 16, 123},
    { 138, 16, 124},
    { 144, 16, 125},
    { 152, 16, 126},
    {  19, 16, 127},
    {  20, 16, 128},
    {  21, 16, 129},
    {  22, 16, 130},
    { 887, 17,   0},
    {1053, 17,   1},
    { 736, 17,   2},
    {1242, 17,   3},
    { 737, 17,   4},
    {1203, 17,   5},
    { 259, 17,   6},
    {1204, 17,   7},
    {1208, 17,   8},
    {1206, 17,   9},
    {1207, 17,  10},
    { 260, 17,  11},
    {1205, 17,  12},
    { 980, 17,  13},
    { 963, 18,   0},
    { 247, 18,   1},
    {1241, 18,   2},
    { 216, 18,   3},
    { 923, 18,   4},
    {1240, 18,   5},
    {1036, 18,   6},
    { 654, 18,   7},
    {1245, 18,   8},
    {1244, 18,   9},
    {1243, 18,  10},
    { 408, 18,  11},
    { 402, 18,  12},
    { 403, 18,  13},
    { 413, 18,  14},
    { 410, 18,  15},
    { 409, 18,  16},
    { 412, 18,  17},
    { 411, 18,  18},
    { 407, 18,  19},
    { 404, 18,  20},
    { 405, 18,  21},
    { 869, 18,  22},
    {1201, 18,  23},
    {1202, 18,  24},
    { 546, 18,  25},
    { 290, 18,  26},
    {1048, 18,  27},
    {1157, 18,  28},
    { 406, 18,  29},
    { 911, 18,  30},
    { 672, 18,  31},
    { 926, 18,  32},
    { 924, 18,  33},
    { 266, 18,  34},
};

/* property values: 5648 bytes. */

/* Codepoints which expand on full case-folding. */

RE_UINT16 re_expand_on_folding[] = {
      223,   304,   329,   496,   912,   944,  1415,  7830,
     7831,  7832,  7833,  7834,  7838,  8016,  8018,  8020,
     8022,  8064,  8065,  8066,  8067,  8068,  8069,  8070,
     8071,  8072,  8073,  8074,  8075,  8076,  8077,  8078,
     8079,  8080,  8081,  8082,  8083,  8084,  8085,  8086,
     8087,  8088,  8089,  8090,  8091,  8092,  8093,  8094,
     8095,  8096,  8097,  8098,  8099,  8100,  8101,  8102,
     8103,  8104,  8105,  8106,  8107,  8108,  8109,  8110,
     8111,  8114,  8115,  8116,  8118,  8119,  8124,  8130,
     8131,  8132,  8134,  8135,  8140,  8146,  8147,  8150,
     8151,  8162,  8163,  8164,  8166,  8167,  8178,  8179,
     8180,  8182,  8183,  8188, 64256, 64257, 64258, 64259,
    64260, 64261, 64262, 64275, 64276, 64277, 64278, 64279,
};

/* expand_on_folding: 208 bytes. */

/* General_Category. */

static RE_UINT8 re_general_category_stage_1[] = {
     0,  1,  2,  3,  4,  5,  6,  7,  7,  8,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  9, 10, 11,  7,  7,  7,  7, 12, 13, 14, 14, 14, 15,
    16, 17, 18, 19, 20, 21, 22, 21, 23, 21, 21, 21, 21, 24, 21, 21,
    21, 21, 21, 21, 21, 21, 25, 26, 21, 21, 27, 28, 21, 29, 30, 31,
     7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  7, 32,  7, 33, 34,  7, 35, 21, 21, 21, 21, 21, 36,
    21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21,
    21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21,
    21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21,
    21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21,
    21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21,
    21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21,
    21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21,
    21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21,
    21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21,
    21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21,
    21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21,
    21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21,
    21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21,
    21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21,
    21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21,
    21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21,
    21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21,
    21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21,
    21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21,
    21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21,
    21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21,
    21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21,
    37, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21,
    21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21,
    14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14,
    14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 38,
    14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14,
    14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 38,
};

static RE_UINT8 re_general_category_stage_2[] = {
      0,   1,   2,   3,   4,   5,   6,   7,   8,   9,  10,  11,  12,  13,  14,  15,
     16,  17,  18,  19,  20,  21,  22,  23,  24,  25,  26,  27,  28,  29,  30,  31,
     32,  33,  34,  34,  35,  36,  37,  38,  39,  34,  34,  34,  40,  41,  42,  43,
     44,  45,  46,  47,  48,  49,  50,  51,  52,  53,  54,  55,  56,  57,  58,  59,
     60,  61,  62,  63,  64,  64,  65,  66,  67,  68,  69,  70,  71,  69,  72,  73,
     69,  69,  64,  74,  64,  64,  75,  76,  77,  78,  79,  80,  81,  82,  69,  83,
     84,  85,  86,  87,  88,  89,  69,  69,  34,  34,  34,  34,  34,  34,  34,  34,
     34,  34,  34,  34,  34,  34,  34,  34,  34,  34,  34,  34,  34,  34,  34,  34,
     34,  34,  34,  34,  34,  34,  34,  34,  34,  34,  34,  90,  34,  34,  34,  34,
     34,  34,  34,  34,  34,  34,  34,  34,  34,  34,  34,  34,  34,  34,  34,  91,
     92,  34,  34,  34,  34,  34,  34,  34,  34,  93,  34,  34,  94,  95,  96,  97,
     98,  99, 100, 101, 102, 103, 104, 105,  34,  34,  34,  34,  34,  34,  34,  34,
     34,  34,  34,  34,  34,  34,  34,  34,  34,  34,  34,  34,  34,  34,  34, 106,
    107, 107, 107, 107, 107, 107, 107, 107, 107, 107, 107, 107, 107, 107, 107, 107,
    108, 108, 108, 108, 108, 108, 108, 108, 108, 108, 108, 108, 108, 108, 108, 108,
    108, 108,  34,  34, 109, 110, 111, 112,  34,  34, 113, 114, 115, 116, 117, 118,
    119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 123,  34,  34, 130, 123,
    131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 123, 123, 141, 123, 123, 123,
    142, 143, 144, 145, 146, 147, 148, 123, 123, 149, 123, 150, 151, 152, 153, 123,
    123, 154, 123, 123, 123, 155, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123,
     34,  34,  34,  34,  34,  34,  34, 156, 157,  34, 158, 123, 123, 123, 123, 123,
    123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123,
     34,  34,  34,  34,  34,  34,  34,  34, 159, 123, 123, 123, 123, 123, 123, 123,
    123, 123, 123, 123, 123, 123, 123, 123,  34,  34,  34,  34, 160, 123, 123, 123,
     34,  34,  34,  34, 161, 162, 163, 164, 123, 123, 123, 123, 123, 123, 165, 166,
    167, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123,
    123, 123, 123, 123, 123, 123, 123, 123, 168, 169, 123, 123, 123, 123, 123, 123,
     69, 170, 171, 172, 173, 123, 174, 123, 175, 176, 177, 178, 179, 180, 181, 182,
     69,  69,  69,  69, 183, 184, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123,
     34, 185, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 186, 187, 123, 123,
    188, 189, 190, 191, 192, 123,  69, 193,  69,  69, 194, 195,  69, 196, 197, 198,
    199, 200, 201, 202, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123,
     34,  34,  34,  34,  34,  34,  34,  34,  34,  34,  34,  34,  34, 203,  34,  34,
     34,  34,  34,  34,  34,  34,  34,  34,  34,  34,  34,  34,  34,  34, 204,  34,
    205,  34,  34,  34,  34,  34,  34,  34,  34,  34,  34,  34,  34,  34,  34,  34,
     34,  34,  34,  34,  34,  34,  34,  34,  34,  34,  34,  34,  34, 206, 123, 123,
     34,  34,  34,  34, 207, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123,
    208, 123, 209, 210, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123, 123,
    108, 108, 108, 108, 108, 108, 108, 108, 108, 108, 108, 108, 108, 108, 108, 211,
};

static RE_UINT16 re_general_category_stage_3[] = {
      0,   0,   1,   2,   3,   4,   5,   6,   0,   0,   7,   8,   9,  10,  11,  12,
     13,  13,  13,  14,  15,  13,  13,  16,  17,  18,  19,  20,  21,  22,  13,  23,
     13,  13,  13,  24,  25,  11,  11,  11,  11,  26,  11,  27,  28,  29,  30,  31,
     32,  32,  32,  32,  32,  32,  32,  33,  34,  35,  36,  11,  37,  38,  13,  39,
      9,   9,   9,  11,  11,  11,  13,  13,  40,  13,  13,  13,  41,  13,  13,  13,
     13,  13,  13,  42,   9,  43,  44,  11,  45,  46,  32,  47,  48,  49,  50,  51,
     52,  53,  49,  49,  54,  32,  55,  56,  49,  49,  49,  49,  49,  57,  58,  59,
     60,  61,  49,  32,  62,  49,  49,  49,  49,  49,  63,  64,  65,  49,  66,  67,
     49,  68,  69,  70,  49,  71,  72,  72,  72,  72,  49,  73,  72,  72,  74,  32,
     75,  49,  49,  76,  77,  78,  79,  80,  81,  82,  83,  84,  85,  86,  87,  88,
     89,  82,  83,  90,  91,  92,  93,  94,  95,  96,  83,  97,  98,  99,  87, 100,
    101,  82,  83, 102, 103, 104,  87, 105, 106, 107, 108, 109, 110, 111,  93, 112,
    113, 114,  83, 115, 116, 117,  87, 118, 119, 114,  83, 120, 121, 122,  87, 123,
    119, 114,  49, 124, 125, 126,  87, 127, 128, 129,  49, 130, 131, 132,  93, 133,
    134,  49,  49, 135, 136, 137,  72,  72, 138, 139, 140, 141, 142, 143,  72,  72,
    144, 145, 146, 147, 148,  49, 149, 150, 151, 152,  32, 153, 154, 155,  72,  72,
     49,  49, 156, 157, 158, 159, 160, 161, 162, 163,   9,   9, 164,  49,  49, 165,
     49,  49,  49,  49,  49,  49,  49,  49,  49,  49,  49,  49, 166, 167,  49,  49,
    166,  49,  49, 168, 169, 170,  49,  49,  49, 169,  49,  49,  49, 171, 172, 173,
     49, 174,   9,   9,   9,   9,   9, 175, 176,  49,  49,  49,  49,  49,  49,  49,
     49,  49,  49,  49,  49,  49, 177,  49, 178, 179,  49,  49,  49,  49, 180, 181,
    182, 183,  49, 184,  49, 185, 182, 186,  49,  49,  49, 187, 188, 189, 190, 191,
    192, 190,  49,  49, 193,  49,  49, 194,  49,  49, 195,  49,  49,  49,  49, 196,
     49, 197, 198, 199, 200,  49, 201,  73,  49,  49, 202,  49, 203, 204, 205, 205,
     49, 206,  49,  49,  49, 207, 208, 209, 190, 190, 210, 211,  72,  72,  72,  72,
    212,  49,  49, 213, 214, 158, 215, 216, 217,  49, 218,  65,  49,  49, 219, 220,
     49,  49, 221, 222, 223,  65,  49, 224,  72,  72,  72,  72, 225, 226, 227, 228,
     11,  11, 229,  27,  27,  27, 230, 231,  11, 232,  27,  27,  32,  32,  32, 233,
     13,  13,  13,  13,  13,  13,  13,  13,  13, 234,  13,  13,  13,  13,  13,  13,
    235, 236, 235, 235, 236, 237, 235, 238, 239, 239, 239, 240, 241, 242, 243, 244,
    245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256,  72, 257, 258, 259,
    260, 261, 262, 263, 264, 265, 266, 266, 267, 268, 269, 205, 270, 271, 205, 272,
    273, 273, 273, 273, 273, 273, 273, 273, 274, 205, 275, 205, 205, 205, 205, 276,
    205, 277, 273, 278, 205, 279, 280, 281, 205, 205, 282,  72, 281,  72, 265, 265,
    265, 283, 205, 205, 205, 205, 284, 265, 205, 205, 205, 205, 205, 205, 205, 205,
    205, 205, 205, 285, 286, 205, 205, 287, 205, 205, 205, 205, 205, 205, 288, 205,
    205, 205, 205, 205, 205, 205, 289, 290, 265, 291, 205, 205, 292, 273, 293, 273,
    294, 295, 273, 273, 273, 296, 273, 297, 205, 205, 205, 273, 298, 205, 205, 299,
    205, 300, 205, 301, 302, 303, 304,  72,   9,   9, 305,  11,  11, 306, 307, 308,
     13,  13,  13,  13,  13,  13, 309, 310,  11,  11, 311,  49,  49,  49, 312, 313,
     49, 314, 315, 315, 315, 315,  32,  32, 316, 317, 318, 319, 320,  72,  72,  72,
    205, 321, 205, 205, 205, 205, 205, 322, 205, 205, 205, 205, 205, 323,  72, 324,
    325, 326, 327, 328, 134,  49,  49,  49,  49, 329, 176,  49,  49,  49,  49, 330,
    331,  49, 201, 134,  49,  49,  49,  49, 197, 332,  49,  50, 205, 205, 322,  49,
    205, 333, 334, 205, 335, 336, 205, 205, 334, 205, 205, 336, 205, 205, 205, 333,
     49,  49,  49, 196, 205, 205, 205, 205,  49,  49,  49,  49,  49, 196,  72,  72,
     49, 337,  49,  49,  49,  49,  49,  49, 149, 205, 205, 205, 282,  49,  49, 224,
    338,  49, 339,  72,  13,  13, 340, 341,  13, 342,  49,  49,  49,  49, 343, 344,
     31, 345, 346, 347,  13,  13,  13, 348, 349, 350, 351, 352,  72,  72,  72, 353,
    354,  49, 355, 356,  49,  49,  49, 357, 358,  49,  49, 359, 360, 190,  32, 361,
     65,  49, 362,  49, 363, 364,  49, 149,  75,  49,  49, 365, 366, 367, 368, 369,
     49,  49, 370, 371, 372, 373,  49, 374,  49,  49,  49, 375, 376, 377, 378, 379,
    380, 381, 315,  11,  11, 382, 383,  11,  11,  11,  11,  11,  49,  49, 384, 190,
     49,  49, 385,  49, 386,  49,  49, 202, 387, 387, 387, 387, 387, 387, 387, 387,
    388, 388, 388, 388, 388, 388, 388, 388,  49,  49,  49,  49,  49,  49, 201,  49,
     49,  49,  49,  49,  49, 203,  72,  72, 389, 390, 391, 392, 393,  49,  49,  49,
     49,  49,  49, 394, 395, 396,  49,  49,  49,  49,  49, 397,  72,  49,  49,  49,
     49, 398,  49,  49, 194,  72,  72, 399,  32, 400,  32, 401, 402, 403, 404, 405,
     49,  49,  49,  49,  49,  49,  49, 406, 407,   2,   3,   4,   5, 408, 409, 410,
     49, 411,  49, 197, 412, 413, 414, 415, 416,  49, 170, 417, 201, 201,  72,  72,
     49,  49,  49,  49,  49,  49,  49,  50, 418, 265, 265, 419, 266, 266, 266, 420,
    421, 324, 422,  72,  72, 205, 205, 423,  72,  72,  72,  72,  72,  72,  72,  72,
     49, 149,  49,  49,  49,  99, 424, 425,  49,  49, 426,  49, 427,  49,  49, 428,
     49, 429,  49,  49, 430, 431,  72,  72,   9,   9, 432,  11,  11,  49,  49,  49,
     49, 201, 190,  72,  72,  72,  72,  72,  49,  49, 194,  49,  49,  49, 433,  72,
     49,  49,  49, 314,  49, 196, 194,  72, 434,  49,  49, 435,  49, 436,  49, 437,
     49, 197, 438,  72,  72,  72,  49, 439,  49, 440,  49, 441,  72,  72,  72,  72,
     49,  49,  49, 442, 265, 443, 265, 265, 444, 445,  49, 446, 447, 448,  49, 449,
     49, 450,  72,  72, 451,  49, 452, 453,  49,  49,  49, 454,  49, 455,  49, 456,
     49, 457, 458,  72,  72,  72,  72,  72,  49,  49,  49,  49, 459,  72,  72,  72,
      9,   9,   9, 460,  11,  11,  11, 461,  72,  72,  72,  72,  72,  72, 265, 462,
    463,  49,  49, 464, 465, 443, 466, 467, 217,  49,  49, 468, 469,  49, 459, 190,
    470,  49, 471, 472, 473,  49,  49, 474, 217,  49,  49, 475, 476, 477, 478, 479,
     49,  96, 480, 481,  72,  72,  72,  72, 482, 483, 484,  49,  49, 485, 486, 190,
    487,  82,  83,  97, 488, 489, 490, 491,  49,  49,  49, 492, 493, 190,  72,  72,
     49,  49, 494, 495, 496, 497,  72,  72,  49,  49,  49, 498, 499, 190,  72,  72,
     49,  49, 500, 501, 190,  72,  72,  72,  49, 502, 503, 504,  72,  72,  72,  72,
     72,  72,   9,   9,  11,  11, 146, 505,  72,  72,  72,  72,  49,  49,  49, 459,
     49, 203,  72,  72,  72,  72,  72,  72, 266, 266, 266, 266, 266, 266, 506, 507,
     49,  49,  49,  49, 385,  72,  72,  72,  49,  49, 197,  72,  72,  72,  72,  72,
     49,  49,  49,  49, 314,  72,  72,  72,  49,  49,  49, 459,  49, 197, 367,  72,
     72,  72,  72,  72,  72,  49, 201, 508,  49,  49,  49, 509, 510, 511, 512, 513,
     49,  72,  72,  72,  72,  72,  72,  72,  49,  49,  49,  49,  73, 514, 515, 516,
    467, 517,  72,  72,  72,  72,  72,  72, 518,  72,  72,  72,  72,  72,  72,  72,
     49,  49,  49,  49,  49,  49,  50, 149, 459, 519, 520,  72,  72,  72,  72,  72,
    205, 205, 205, 205, 205, 205, 205, 323, 205, 205, 521, 205, 205, 205, 522, 523,
    524, 205, 525, 205, 205, 205, 526,  72, 205, 205, 205, 205, 527,  72,  72,  72,
    205, 205, 205, 205, 205, 282, 265, 528,   9, 529,  11, 530, 531, 532, 235,   9,
    533, 534, 535, 536, 537,   9, 529,  11, 538, 539,  11, 540, 541, 542, 543,   9,
    544,  11,   9, 529,  11, 530, 531,  11, 235,   9, 533, 543,   9, 544,  11,   9,
    529,  11, 545,   9, 546, 547, 548, 549,  11, 550,   9, 551, 552, 553, 554,  11,
    555,   9, 556,  11, 557, 558, 558, 558,  32,  32,  32, 559,  32,  32, 560, 561,
    562, 563,  46,  72,  72,  72,  72,  72,  49,  49,  49,  49, 564, 565,  72,  72,
    566,  49, 567, 568, 569, 570, 571, 572, 573, 202, 574, 202,  72,  72,  72, 575,
    205, 205, 324, 205, 205, 205, 205, 205, 205, 322, 333, 576, 576, 576, 205, 323,
    173, 205, 333, 205, 205, 205, 324, 205, 205, 281,  72,  72,  72,  72, 577, 205,
    578, 205, 205, 281, 526, 303,  72,  72, 205, 205, 205, 205, 205, 205, 205, 579,
    205, 205, 205, 205, 205, 205, 205, 321, 205, 205, 580, 205, 205, 205, 205, 205,
    205, 205, 205, 205, 205, 422, 581, 322, 205, 205, 205, 205, 205, 205, 205, 322,
    205, 205, 205, 205, 205, 582,  72,  72, 324, 205, 205, 205, 583, 174, 205, 205,
    583, 205, 584,  72,  72,  72,  72,  72,  72, 526,  72,  72,  72,  72,  72,  72,
    582,  72,  72,  72, 422,  72,  72,  72,  49,  49,  49,  49,  49, 314,  72,  72,
     49,  49,  49,  73,  49,  49,  49,  49,  49, 201,  49,  49,  49,  49,  49,  49,
     49,  49, 518,  72,  72,  72,  72,  72,  49, 201,  72,  72,  72,  72,  72,  72,
    585,  72, 586, 586, 586, 586, 586, 586,  32,  32,  32,  32,  32,  32,  32,  32,
     32,  32,  32,  32,  32,  32,  32,  72, 388, 388, 388, 388, 388, 388, 388, 587,
};

static RE_UINT8 re_general_category_stage_4[] = {
      0,   0,   0,   0,   0,   0,   0,   0,   1,   2,   3,   2,   4,   5,   6,   2,
      7,   7,   7,   7,   7,   2,   8,   9,  10,  11,  11,  11,  11,  11,  11,  11,
     11,  11,  11,  11,  11,  12,  13,  14,  15,  16,  16,  16,  16,  16,  16,  16,
     16,  16,  16,  16,  16,  17,  18,  19,   1,  20,  20,  21,  22,  23,  24,  25,
     26,  27,  15,   2,  28,  29,  27,  30,  11,  11,  11,  11,  11,  11,  11,  11,
     11,  11,  11,  31,  11,  11,  11,  32,  16,  16,  16,  16,  16,  16,  16,  16,
     16,  16,  16,  33,  16,  16,  16,  16,  32,  32,  32,  32,  32,  32,  32,  32,
     32,  32,  32,  32,  34,  34,  34,  34,  34,  34,  34,  34,  16,  32,  32,  32,
     32,  32,  32,  32,  11,  34,  34,  16,  34,  32,  32,  11,  34,  11,  16,  11,
     11,  34,  32,  11,  32,  16,  11,  34,  32,  32,  32,  11,  34,  16,  32,  11,
     34,  11,  34,  34,  32,  35,  32,  16,  36,  36,  37,  34,  38,  37,  34,  34,
     34,  34,  34,  34,  34,  34,  16,  32,  34,  38,  32,  11,  32,  32,  32,  32,
     32,  32,  16,  16,  16,  11,  34,  32,  34,  34,  11,  32,  32,  32,  32,  32,
     16,  16,  39,  16,  16,  16,  16,  16,  40,  40,  40,  40,  40,  40,  40,  40,
     40,  41,  41,  40,  40,  40,  40,  40,  40,  41,  41,  41,  41,  41,  41,  41,
     40,  40,  42,  41,  41,  41,  42,  42,  41,  41,  41,  41,  41,  41,  41,  41,
     43,  43,  43,  43,  43,  43,  43,  43,  32,  32,  42,  32,  44,  45,  16,  10,
     44,  44,  41,  46,  11,  47,  47,  11,  34,  11,  11,  11,  11,  11,  11,  11,
     11,  48,  11,  11,  11,  11,  16,  16,  16,  16,  16,  16,  16,  16,  16,  34,
     16,  11,  32,  16,  32,  32,  32,  32,  16,  16,  32,  49,  34,  32,  34,  11,
     32,  50,  43,  43,  51,  32,  32,  32,  11,  34,  34,  34,  34,  34,  34,  16,
     48,  11,  11,  11,  11,  11,  11,  11,  11,  11,  11,  47,  52,   2,   2,   2,
     53,  16,  16,  16,  16,  16,  16,  16,  16,  16,  16,  16,  54,  55,  56,  57,
     58,  43,  43,  43,  43,  43,  43,  43,  43,  43,  43,  43,  43,  43,  43,  59,
     60,  61,  43,  60,  44,  44,  44,  44,  36,  36,  36,  36,  36,  36,  36,  36,
     36,  36,  36,  36,  36,  62,  44,  44,  36,  63,  64,  44,  44,  44,  44,  44,
     65,  65,  65,   8,   9,  66,   2,  67,  43,  43,  43,  43,  43,  61,  68,   2,
     69,  36,  36,  36,  36,  70,  43,  43,   7,   7,   7,   7,   7,   2,   2,  36,
     71,  36,  36,  36,  36,  36,  36,  36,  36,  36,  72,  43,  43,  43,  73,  50,
     43,  43,  74,  75,  76,  43,  43,  36,   7,   7,   7,   7,   7,  36,  77,  78,
      2,   2,   2,   2,   2,   2,   2,  79,  70,  36,  36,  36,  36,  36,  36,  36,
     43,  43,  43,  43,  43,  80,  81,  36,  36,  36,  36,  43,  43,  43,  43,  43,
     71,  44,  44,  44,  44,  44,  44,  44,   7,   7,   7,   7,   7,  36,  36,  36,
     36,  36,  36,  36,  36,  70,  43,  43,  43,  43,  40,  21,   2,  82,  44,  44,
     36,  36,  36,  43,  43,  75,  43,  43,  43,  43,  75,  43,  75,  43,  43,  44,
      2,   2,   2,   2,   2,   2,   2,  64,  36,  36,  36,  36,  70,  43,  44,  64,
     44,  44,  44,  44,  44,  44,  44,  44,  36,  36,  62,  44,  44,  44,  44,  44,
     44,  58,  43,  43,  43,  43,  43,  43,  43,  83,  36,  36,  36,  36,  36,  36,
     36,  36,  36,  36,  36,  83,  71,  84,  85,  43,  43,  43,  83,  84,  85,  84,
     70,  43,  43,  43,  36,  36,  36,  36,  36,  43,   2,   7,   7,   7,   7,   7,
     86,  36,  36,  36,  36,  36,  36,  36,  70,  84,  81,  36,  36,  36,  62,  81,
     62,  81,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  62,  36,  36,  36,
     62,  62,  44,  36,  36,  44,  71,  84,  85,  43,  80,  87,  88,  87,  85,  62,
     44,  44,  44,  87,  44,  44,  36,  81,  36,  43,  44,   7,   7,   7,   7,   7,
     36,  20,  27,  27,  27,  57,  44,  44,  58,  83,  81,  36,  36,  62,  44,  81,
     62,  36,  81,  62,  36,  44,  80,  84,  85,  80,  44,  58,  80,  58,  43,  44,
     58,  44,  44,  44,  81,  36,  62,  62,  44,  44,  44,   7,   7,   7,   7,   7,
     43,  36,  70,  44,  44,  44,  44,  44,  58,  83,  81,  36,  36,  36,  36,  81,
     36,  81,  36,  36,  36,  36,  36,  36,  62,  36,  81,  36,  36,  44,  71,  84,
     85,  43,  43,  58,  83,  87,  85,  44,  62,  44,  44,  44,  44,  44,  44,  44,
     66,  44,  44,  44,  81,  44,  44,  44,  58,  84,  81,  36,  36,  36,  62,  81,
     62,  36,  81,  36,  36,  44,  71,  85,  85,  43,  80,  87,  88,  87,  85,  44,
     44,  44,  44,  83,  44,  44,  36,  81,  78,  27,  27,  27,  44,  44,  44,  44,
     44,  71,  81,  36,  36,  62,  44,  36,  62,  36,  36,  44,  81,  62,  62,  36,
     44,  81,  62,  44,  36,  62,  44,  36,  36,  36,  36,  36,  36,  44,  44,  84,
     83,  88,  44,  84,  88,  84,  85,  44,  62,  44,  44,  87,  44,  44,  44,  44,
     27,  89,  67,  67,  57,  90,  44,  44,  83,  84,  81,  36,  36,  36,  62,  36,
     62,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  44,  81,  43,
     83,  84,  88,  43,  80,  43,  43,  44,  44,  44,  58,  80,  36,  62,  44,  44,
     44,  44,  44,  44,  27,  27,  27,  89,  58,  84,  81,  36,  36,  36,  62,  36,
     36,  36,  81,  36,  36,  44,  71,  85,  84,  84,  88,  83,  88,  84,  43,  44,
     44,  44,  87,  88,  44,  44,  44,  62,  81,  62,  44,  44,  44,  44,  44,  44,
     36,  36,  36,  36,  36,  62,  81,  84,  85,  43,  80,  84,  88,  84,  85,  62,
     44,  44,  44,  87,  44,  44,  44,  81,  27,  27,  27,  44,  56,  36,  36,  36,
     44,  84,  81,  36,  36,  36,  36,  36,  36,  36,  36,  62,  44,  36,  36,  36,
     36,  81,  36,  36,  36,  36,  81,  44,  36,  36,  36,  62,  44,  80,  44,  87,
     84,  43,  80,  80,  84,  84,  84,  84,  44,  84,  64,  44,  44,  44,  44,  44,
     81,  36,  36,  36,  36,  36,  36,  36,  70,  36,  43,  43,  43,  80,  44,  91,
     36,  36,  36,  75,  43,  43,  43,  61,   7,   7,   7,   7,   7,   2,  44,  44,
     81,  62,  62,  81,  62,  62,  81,  44,  44,  44,  36,  36,  81,  36,  36,  36,
     81,  36,  81,  81,  44,  36,  81,  36,  70,  36,  43,  43,  43,  58,  71,  44,
     36,  36,  62,  82,  43,  43,  43,  44,   7,   7,   7,   7,   7,  44,  36,  36,
     77,  67,   2,   2,   2,   2,   2,   2,   2,  92,  92,  67,  43,  67,  67,  67,
      7,   7,   7,   7,   7,  27,  27,  27,  27,  27,  50,  50,  50,   4,   4,  84,
     36,  36,  36,  36,  81,  36,  36,  36,  36,  36,  36,  36,  36,  36,  62,  44,
     58,  43,  43,  43,  43,  43,  43,  83,  43,  43,  61,  43,  36,  36,  70,  43,
     43,  43,  43,  43,  58,  43,  43,  43,  43,  43,  43,  43,  43,  43,  80,  67,
     67,  67,  67,  76,  67,  67,  90,  67,   2,   2,  92,  67,  21,  64,  44,  44,
     36,  36,  36,  36,  36,  93,  85,  43,  83,  43,  43,  43,  85,  83,  85,  71,
      7,   7,   7,   7,   7,   2,   2,   2,  36,  36,  36,  84,  43,  36,  36,  43,
     71,  84,  94,  93,  84,  84,  84,  36,  70,  43,  71,  36,  36,  36,  36,  36,
     36,  83,  85,  83,  84,  84,  85,  93,   7,   7,   7,   7,   7,  84,  85,  67,
     11,  11,  11,  48,  44,  44,  48,  44,  36,  36,  36,  36,  36,  63,  69,  36,
     36,  36,  36,  36,  62,  36,  36,  44,  36,  36,  36,  62,  62,  36,  36,  44,
     62,  36,  36,  44,  36,  36,  36,  62,  62,  36,  36,  44,  36,  36,  36,  36,
     36,  36,  36,  62,  36,  36,  36,  36,  36,  36,  36,  36,  36,  62,  58,  43,
      2,   2,   2,   2,  95,  27,  27,  27,  27,  27,  27,  27,  27,  27,  96,  44,
     67,  67,  67,  67,  67,  44,  44,  44,  11,  11,  11,  44,  16,  16,  16,  44,
     97,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  63,  72,
     98,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  99, 100,  44,
     36,  36,  36,  36,  36,  63,   2, 101, 102,  36,  36,  36,  62,  44,  44,  44,
     36,  36,  36,  36,  36,  36,  62,  36,  36,  43,  80,  44,  44,  44,  44,  44,
     36,  43,  61,  64,  44,  44,  44,  44,  36,  43,  44,  44,  44,  44,  44,  44,
     62,  43,  44,  44,  44,  44,  44,  44,  36,  36,  43,  85,  43,  43,  43,  84,
     84,  84,  84,  83,  85,  43,  43,  43,  43,  43,   2,  86,   2,  66,  70,  44,
      7,   7,   7,   7,   7,  44,  44,  44,  27,  27,  27,  27,  27,  44,  44,  44,
      2,   2,   2, 103,   2,  60,  43,  68,  36, 104,  36,  36,  36,  36,  36,  36,
     36,  36,  36,  36,  44,  44,  44,  44,  36,  36,  36,  36,  70,  62,  44,  44,
     36,  36,  36,  44,  44,  44,  44,  44,  36,  36,  36,  36,  36,  36,  36,  62,
     43,  83,  84,  85,  83,  84,  44,  44,  84,  83,  84,  84,  85,  43,  44,  44,
     90,  44,   2,   7,   7,   7,   7,   7,  36,  36,  36,  36,  36,  36,  36,  44,
     36,  36,  36,  36,  36,  36,  44,  44,  36,  36,  36,  36,  36,  44,  44,  44,
      7,   7,   7,   7,   7,  96,  44,  67,  67,  67,  67,  67,  67,  67,  67,  67,
     36,  36,  36,  70,  83,  85,  44,   2,  36,  36,  93,  83,  43,  43,  43,  80,
     83,  83,  85,  43,  43,  43,  83,  84,  84,  85,  43,  43,  43,  43,  80,  58,
      2,   2,   2,  86,   2,   2,   2,  44,  43,  43,  43,  43,  43,  43,  43, 105,
     43,  43,  94,  36,  36,  36,  36,  36,  36,  36,  83,  43,  43,  83,  83,  84,
     84,  83,  94,  36,  36,  36,  44,  44,  92,  67,  67,  67,  67,  50,  43,  43,
     43,  43,  67,  67,  67,  67,  90,  44,  43,  94,  36,  36,  36,  36,  36,  36,
     93,  43,  43,  84,  43,  85,  43,  36,  36,  36,  36,  83,  43,  84,  85,  85,
     43,  84,  44,  44,  44,  44,   2,   2,  36,  36,  84,  84,  84,  84,  43,  43,
     43,  43,  84,  43,  44,  54,   2,   2,   7,   7,   7,   7,   7,  44,  81,  36,
     36,  36,  36,  36,  40,  40,  40,   2,   2,   2,   2,   2,  44,  44,  44,  44,
     43,  61,  43,  43,  43,  43,  43,  43,  83,  43,  43,  43,  71,  36,  70,  36,
     36,  84,  71,  62,  43,  44,  44,  44,  16,  16,  16,  16,  16,  16,  40,  40,
     40,  40,  40,  40,  40,  45,  16,  16,  16,  16,  16,  16,  45,  16,  16,  16,
     16,  16,  16,  16,  16, 106,  40,  40,  43,  43,  43,  44,  44,  44,  43,  43,
     32,  32,  32,  16,  16,  16,  16,  32,  16,  16,  16,  16,  11,  11,  11,  11,
     16,  16,  16,  44,  11,  11,  11,  44,  16,  16,  16,  16,  48,  48,  48,  48,
     16,  16,  16,  16,  16,  16,  16,  44,  16,  16,  16,  16, 107, 107, 107, 107,
     16,  16, 108,  16,  11,  11, 109, 110,  41,  16, 108,  16,  11,  11, 109,  41,
     16,  16,  44,  16,  11,  11, 111,  41,  16,  16,  16,  16,  11,  11, 112,  41,
     44,  16, 108,  16,  11,  11, 109, 113, 114, 114, 114, 114, 114, 115,  65,  65,
    116, 116, 116,   2, 117, 118, 117, 118,   2,   2,   2,   2, 119,  65,  65, 120,
      2,   2,   2,   2, 121, 122,   2, 123, 124,   2, 125, 126,   2,   2,   2,   2,
      2,   9, 124,   2,   2,   2,   2, 127,  65,  65,  68,  65,  65,  65,  65,  65,
    128,  44,  27,  27,  27,   8, 125, 129,  27,  27,  27,  27,  27,   8, 125, 100,
     40,  40,  40,  40,  40,  40,  82,  44,  20,  20,  20,  20,  20,  20,  20,  20,
     20,  20,  20,  20,  20,  20,  20, 130,  43,  43,  43,  43,  43,  43, 131,  51,
    132,  51, 132,  43,  43,  43,  43,  43,  80,  44,  44,  44,  44,  44,  44,  44,
     67, 133,  67, 134,  67,  34,  11,  16,  11,  32, 134,  67,  49,  11,  11,  67,
     67,  67, 133, 133, 133,  11,  11, 135,  11,  11,  35,  36,  39,  67,  16,  11,
      8,   8,  49,  16,  16,  26,  67, 136,  27,  27,  27,  27,  27,  27,  27,  27,
    101, 101, 101, 101, 101, 101, 101, 101, 101, 137, 138, 101, 139,  67,  44,  44,
      8,   8, 140,  67,  67,   8,  67,  67, 140,  26,  67, 140,  67,  67,  67, 140,
     67,  67,  67,  67,  67,  67,  67,   8,  67, 140, 140,  67,  67,  67,  67,  67,
     67,  67,   8,   8,   8,   8,   8,   8,   8,   8,   8,   8,   8,   8,   8,   8,
     67,  67,  67,  67,   4,   4,  67,  67,   8,  67,  67,  67, 141, 142,  67,  67,
     67,  67,  67,  67,  67,  67, 140,  67,  67,  67,  67,  67,  67,  26,   8,   8,
      8,   8,  67,  67,  67,  67,  67,  67,  67,  67,  67,  67,  67,  67,   8,   8,
      8,  67,  67,  67,  67,  67,  67,  67,  67,  67,  67,  67,  67,  90,  44,  44,
     67,  67,  67,  90,  44,  44,  44,  44,  27,  27,  27,  27,  27,  27,  67,  67,
     67,  67,  67,  67,  67,  27,  27,  27,  67,  67,  67,  26,  67,  67,  67,  67,
     26,  67,  67,  67,  67,  67,  67,  67,  67,  67,  67,  67,   8,   8,   8,   8,
     67,  67,  67,  67,  67,  67,  67,  26,  67,  67,  67,  67,   4,   4,   4,   4,
      4,   4,   4,  27,  27,  27,  27,  27,  27,  27,  67,  67,  67,  67,  67,  67,
      8,   8, 125, 143,   8,   8,   8,   8,   8,   8,   8,   4,   4,   4,   4,   4,
      8, 125, 144, 144, 144, 144, 144, 144, 144, 144, 144, 144, 143,   8,   8,   8,
      8,   8,   8,   8,   4,   4,   8,   8,   8,   8,   8,   8,   8,   8,   4,   8,
      8,   8, 140,  26,   8,   8, 140,  67,  67,  67,  44,  67,  67,  67,  67,  67,
     67,  67,  67,  44,  67,  67,  67,  67,  67,  67,  67,  67,  67,  44,  56,  67,
     67,  67,  67,  67,  90,  67,  67,  67,  67,  44,  44,  44,  44,  44,  44,  44,
     44,  44,  44,  44,  44,  44,  67,  67,  11,  11,  11,  11,  11,  11,  11,  47,
     16,  16,  16,  16,  16,  16,  16, 108,  32,  11,  32,  34,  34,  34,  34,  11,
     32,  32,  34,  16,  16,  16,  40,  11,  32,  32, 136,  67,  67, 134,  34, 145,
     43,  32,  44,  44,  54,   2,  95,   2,  16,  16,  16,  53,  44,  44,  53,  44,
     36,  36,  36,  36,  44,  44,  44,  52,  64,  44,  44,  44,  44,  44,  44,  58,
     36,  36,  36,  62,  44,  44,  44,  44,  36,  36,  36,  62,  36,  36,  36,  62,
      2, 117, 117,   2, 121, 122, 117,   2,   2,   2,   2,   6,   2, 103, 117,   2,
    117,   4,   4,   4,   4,   2,   2,  86,   2,   2,   2,   2,   2, 116,   2,   2,
    103, 146,  44,  44,  44,  44,  44,  44,  67,  67,  67,  67,  67,  56,  67,  67,
     67,  67,  44,  44,  44,  44,  44,  44,  67,  67,  67,  44,  44,  44,  44,  44,
     67,  67,  67,  67,  67,  67,  44,  44,   1,   2, 147, 148,   4,   4,   4,   4,
      4,  67,   4,   4,   4,   4, 149, 150, 151, 101, 101, 101, 101,  43,  43,  84,
    152,  40,  40,  67, 101, 153,  63,  67,  36,  36,  36,  62,  58, 154, 155,  69,
     36,  36,  36,  36,  36,  63,  40,  69,  44,  44,  81,  36,  36,  36,  36,  36,
     67,  27,  27,  67,  67,  67,  67,  67,  67,  67,  67,  67,  67,  67,  67,  90,
     27,  27,  27,  27,  27,  67,  67,  67,  67,  67,  67,  67,  27,  27,  27,  27,
    156,  27,  27,  27,  27,  27,  27,  27,  36,  36, 104,  36,  36,  36,  36,  36,
     36,  36,  36,  36,  36,  36, 157,   2,   7,   7,   7,   7,   7,  36,  44,  44,
     32,  32,  32,  32,  32,  32,  32,  70,  51, 158,  43,  43,  43,  43,  43,  86,
     32,  32,  32,  32,  32,  32,  40,  43,  36,  36,  36, 101, 101, 101, 101, 101,
     43,   2,   2,   2,  44,  44,  44,  44,  41,  41,  41, 155,  40,  40,  40,  40,
     41,  32,  32,  32,  32,  32,  32,  32,  16,  32,  32,  32,  32,  32,  32,  32,
     45,  16,  16,  16,  34,  34,  34,  32,  32,  32,  32,  32,  42, 159,  34,  35,
     32,  32,  16,  32,  32,  32,  32,  32,  32,  32,  32,  32,  32,  11,  11,  44,
     11,  11,  32,  32,  44,  44,  44,  44,  44,  44,  44,  81,  40,  35,  36,  36,
     36,  71,  36,  71,  36,  70,  36,  36,  36,  93,  85,  83,  67,  67,  44,  44,
     27,  27,  27,  67, 160,  44,  44,  44,  36,  36,   2,   2,  44,  44,  44,  44,
     84,  36,  36,  36,  36,  36,  36,  36,  36,  36,  84,  84,  84,  84,  84,  84,
     84,  84,  80,  44,  44,  44,  44,   2,  43,  36,  36,  36,   2,  72,  72,  44,
     36,  36,  36,  43,  43,  43,  43,   2,  36,  36,  36,  70,  43,  43,  43,  43,
     43,  84,  44,  44,  44,  44,  44,  54,  36,  70,  84,  43,  43,  84,  83,  84,
    161,   2,   2,   2,   2,   2,   2,  52,   7,   7,   7,   7,   7,  44,  44,   2,
     36,  36,  70,  69,  36,  36,  36,  36,   7,   7,   7,   7,   7,  36,  36,  62,
     36,  36,  36,  36,  70,  43,  43,  83,  85,  83,  85,  80,  44,  44,  44,  44,
     36,  70,  36,  36,  36,  36,  83,  44,   7,   7,   7,   7,   7,  44,   2,   2,
     69,  36,  36,  77,  67,  93,  83,  36,  71,  43,  71,  70,  71,  36,  36,  43,
     70,  62,  44,  44,  44,  44,  44,  44,  44,  44,  44,  44,  44,  81, 104,   2,
     36,  36,  36,  36,  36,  93,  43,  84,   2, 104, 162,  80,  44,  44,  44,  44,
     81,  36,  36,  62,  81,  36,  36,  62,  81,  36,  36,  62,  44,  44,  44,  44,
     16,  16,  16,  16,  16, 110,  40,  40,  16,  16,  16,  44,  44,  44,  44,  44,
     36,  93,  85,  84,  83, 161,  85,  44,  36,  36,  44,  44,  44,  44,  44,  44,
     36,  36,  36,  62,  44,  81,  36,  36, 163, 163, 163, 163, 163, 163, 163, 163,
    164, 164, 164, 164, 164, 164, 164, 164,  16,  16,  16, 108,  44,  44,  44,  44,
     44,  53,  16,  16,  44,  44,  81,  71,  36,  36,  36,  36, 165,  36,  36,  36,
     36,  36,  36,  62,  36,  36,  62,  62,  36,  81,  62,  36,  36,  36,  36,  36,
     36,  41,  41,  41,  41,  41,  41,  41,  41,  44,  44,  44,  44,  44,  44,  44,
     44,  81,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36, 144,
     44,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36, 160,  44,
      2,   2,   2, 166, 126,  44,  44,  44,   6, 167, 168, 144, 144, 144, 144, 144,
    144, 144, 126, 166, 126,   2, 123, 169,   2,  64,   2,   2, 149, 144, 144, 126,
      2, 170,   8, 171,  66,   2,  44,  44,  36,  36,  62,  36,  36,  36,  36,  36,
     36,  36,  36,  36,  36,  36,  62,  79,  54,   2,   3,   2,   4,   5,   6,   2,
     16,  16,  16,  16,  16,  17,  18, 125, 126,   4,   2,  36,  36,  36,  36,  36,
     69,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  40,
     44,  36,  36,  36,  44,  36,  36,  36,  44,  36,  36,  36,  44,  36,  62,  44,
     20, 172,  57, 130,  26,   8, 140,  90,  44,  44,  44,  44,  79,  65,  67,  44,
     36,  36,  36,  36,  36,  36,  81,  36,  36,  36,  36,  36,  36,  62,  36,  81,
      2,  64,  44, 173,  27,  27,  27,  27,  27,  27,  44,  56,  67,  67,  67,  67,
    101, 101, 139,  27,  89,  67,  67,  67,  67,  67,  67,  67,  67,  27,  90,  44,
     90,  44,  44,  44,  44,  44,  44,  44,  67,  67,  67,  67,  67,  67,  50,  44,
    174,  27,  27,  27,  27,  27,  27,  27,  27,  27,  27,  27,  27,  27,  44,  44,
     27,  27,  44,  44,  44,  44,  44,  44, 148,  36,  36,  36,  36, 175,  44,  44,
     36,  36,  36,  43,  43,  80,  44,  44,  36,  36,  36,  36,  36,  36,  36,  54,
     36,  36,  44,  44,  36,  36,  36,  36, 176, 101, 101,  44,  44,  44,  44,  44,
     11,  11,  11,  11,  16,  16,  16,  16,  36,  36,  44,  44,  44,  44,  44,  54,
     36,  36,  36,  44,  62,  36,  36,  36,  36,  36,  36,  81,  62,  44,  62,  81,
     36,  36,  36,  54,  27,  27,  27,  27,  36,  36,  36,  77, 156,  27,  27,  27,
     44,  44,  44, 173,  27,  27,  27,  27,  36,  62,  36,  44,  44, 173,  27,  27,
     36,  36,  36,  27,  27,  27,  44,  54,  36,  36,  36,  36,  36,  44,  44,  54,
     36,  36,  36,  36,  44,  44,  27,  36,  44,  27,  27,  27,  27,  27,  27,  27,
     70,  43,  58,  80,  44,  44,  43,  43,  36,  36,  81,  36,  81,  36,  36,  36,
     36,  36,  44,  44,  43,  80,  44,  58,  27,  27,  27,  27,  44,  44,  44,  44,
      2,   2,   2,   2,  64,  44,  44,  44,  36,  36,  36,  36,  36,  36, 177,  30,
     36,  36,  36,  36,  36,  36, 177,  27,  36,  36,  36,  36,  78,  36,  36,  36,
     36,  36,  70,  80,  44, 173,  27,  27,   2,   2,   2,  64,  44,  44,  44,  44,
     36,  36,  36,  44,  54,   2,   2,   2,  36,  36,  36,  44,  27,  27,  27,  27,
     36,  62,  44,  44,  27,  27,  27,  27,  36,  44,  44,  44,  54,   2,  64,  44,
     44,  44,  44,  44, 173,  27,  27,  27,  36,  36,  36,  36,  62,  44,  44,  44,
     11,  47,  44,  44,  44,  44,  44,  44,  16, 108,  44,  44,  44,  27,  27,  27,
     27,  27,  27,  27,  27,  27,  27,  96,  85,  94,  36,  36,  36,  36,  36,  36,
     36,  36,  36,  36,  43,  43,  43,  43,  43,  43,  43,  61,   2,   2,   2,  44,
     27,  27,  27,   7,   7,   7,   7,   7,  44,  44,  44,  44,  44,  44,  44,  58,
     84,  85,  43,  83,  85,  61, 178,   2,   2,  44,  44,  44,  44,  44,  44,  44,
     43,  71,  36,  36,  36,  36,  36,  36,  36,  36,  36,  70,  43,  43,  85,  43,
     43,  43,  80,   7,   7,   7,   7,   7,   2,   2,  44,  44,  44,  44,  44,  44,
     36,  70,   2,  62,  44,  44,  44,  44,  36,  93,  84,  43,  43,  43,  43,  83,
     94,  36,  63,   2,   2,  43,  61,  44,   7,   7,   7,   7,   7,  63,  63,   2,
    173,  27,  27,  27,  27,  27,  27,  27,  27,  27,  96,  44,  44,  44,  44,  44,
     36,  36,  36,  36,  36,  36,  84,  85,  43,  84,  83,  43,   2,   2,   2,  44,
     36,  36,  36,  62,  62,  36,  36,  81,  36,  36,  36,  36,  36,  36,  36,  81,
     36,  36,  36,  36,  63,  44,  44,  44,  36,  36,  36,  36,  36,  36,  36,  70,
     84,  85,  43,  43,  43,  80,  44,  44,  43,  84,  81,  36,  36,  36,  62,  81,
     83,  84,  88,  87,  88,  87,  84,  44,  62,  44,  44,  87,  44,  44,  81,  36,
     36,  84,  44,  43,  43,  43,  80,  44,  43,  43,  80,  44,  44,  44,  44,  44,
     84,  85,  43,  43,  83,  83,  84,  85,  83,  43,  36,  72,  44,  44,  44,  44,
     36,  36,  36,  36,  36,  36,  36,  93,  84,  43,  43,  44,  84,  84,  43,  85,
     61,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,  36,  36,  43,  44,
     84,  85,  43,  43,  43,  83,  85,  85,  61,   2,  62,  44,  44,  44,  44,  44,
     36,  36,  36,  36,  36,  70,  85,  84,  43,  43,  43,  85,  44,  44,  44,  44,
     36,  36,  36,  36,  36,  44,  58,  43,  84,  43,  43,  85,  43,  43,  44,  44,
      7,   7,   7,   7,   7,  27,   2,  92,  27,  96,  44,  44,  44,  44,  44,  81,
    101, 101, 101, 101, 101, 101, 101, 175,   2,   2,  64,  44,  44,  44,  44,  44,
     43,  43,  61,  44,  44,  44,  44,  44,  43,  43,  43,  61,   2,   2,  67,  67,
     40,  40,  92,  44,  44,  44,  44,  44,   7,   7,   7,   7,   7, 173,  27,  27,
     27,  81,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  44,  44,  81,  36,
     93,  84,  84,  84,  84,  84,  84,  84,  84,  84,  84,  84,  84,  84,  84,  84,
     84,  84,  84,  84,  84,  84,  84,  88,  43,  74,  40,  40,  40,  40,  40,  40,
     36,  44,  44,  44,  44,  44,  44,  44,  36,  36,  36,  36,  36,  44,  50,  61,
     65,  65,  44,  44,  44,  44,  44,  44,  67,  67,  67,  90,  56,  67,  67,  67,
     67,  67, 179,  85,  43,  67, 179,  84,  84, 180,  65,  65,  65, 181,  43,  43,
     43,  76,  50,  43,  43,  43,  67,  67,  67,  67,  67,  67,  67,  43,  43,  67,
     67,  67,  67,  67,  90,  44,  44,  44,  67,  43,  76,  44,  44,  44,  44,  44,
     27,  44,  44,  44,  44,  44,  44,  44,  11,  11,  11,  11,  11,  16,  16,  16,
     16,  16,  11,  11,  11,  11,  11,  11,  11,  11,  11,  11,  11,  11,  11,  16,
     16,  16, 108,  16,  16,  16,  16,  16,  11,  16,  16,  16,  16,  16,  16,  16,
     16,  16,  16,  16,  16,  16,  47,  11,  44,  47,  48,  47,  48,  11,  47,  11,
     11,  11,  11,  16,  16,  53,  53,  16,  16,  16,  53,  16,  16,  16,  16,  16,
     16,  16,  11,  48,  11,  47,  48,  11,  11,  11,  47,  11,  11,  11,  47,  16,
     16,  16,  16,  16,  11,  48,  11,  47,  11,  11,  47,  47,  44,  11,  11,  11,
     47,  16,  16,  16,  16,  16,  16,  16,  16,  16,  16,  16,  16,  16,  11,  11,
     11,  11,  11,  16,  16,  16,  16,  16,  16,  16,  16,  44,  11,  11,  11,  11,
     31,  16,  16,  16,  16,  16,  16,  16,  16,  16,  16,  16,  16,  33,  16,  16,
     16,  11,  11,  11,  11,  11,  11,  11,  11,  11,  11,  11,  11,  31,  16,  16,
     16,  16,  33,  16,  16,  16,  11,  11,  11,  11,  31,  16,  16,  16,  16,  16,
     16,  16,  16,  16,  16,  16,  16,  33,  16,  16,  16,  11,  11,  11,  11,  11,
     11,  11,  11,  11,  11,  11,  11,  31,  16,  16,  16,  16,  33,  16,  16,  16,
     11,  11,  11,  11,  31,  16,  16,  16,  16,  33,  16,  16,  16,  32,  44,   7,
      7,   7,   7,   7,   7,   7,   7,   7,  43,  43,  43,  76,  67,  50,  43,  43,
     43,  43,  43,  43,  43,  43,  76,  67,  67,  67,  50,  67,  67,  67,  67,  67,
     67,  67,  76,  21,   2,   2,  44,  44,  44,  44,  44,  44,  44,  58,  43,  43,
     36,  36,  62, 173,  27,  27,  27,  27,  43,  43,  43,  80,  44,  44,  44,  44,
     36,  36,  81,  36,  36,  36,  36,  36,  81,  62,  62,  81,  81,  36,  36,  36,
     36,  62,  36,  36,  81,  81,  44,  44,  44,  62,  44,  81,  81,  81,  81,  36,
     81,  62,  62,  81,  81,  81,  81,  81,  81,  62,  62,  81,  36,  62,  36,  36,
     36,  62,  36,  36,  81,  36,  62,  62,  36,  36,  36,  36,  36,  81,  36,  36,
     81,  36,  81,  36,  36,  81,  36,  36,   8,  44,  44,  44,  44,  44,  44,  44,
     56,  67,  67,  67,  67,  67,  67,  67,  44,  44,  44,  67,  67,  67,  67,  67,
     67,  90,  44,  44,  44,  44,  44,  44,  67,  67,  67,  67,  67,  25,  41,  41,
     67,  67,  56,  67,  67,  67,  67,  67,  67,  67,  67,  67,  67,  67,  90,  44,
     67,  67,  90,  44,  44,  44,  44,  44,  67,  67,  67,  67,  44,  44,  44,  44,
     67,  67,  67,  67,  67,  67,  67,  44,  79,  44,  44,  44,  44,  44,  44,  44,
     65,  65,  65,  65,  65,  65,  65,  65, 164, 164, 164, 164, 164, 164, 164,  44,
};

static RE_UINT8 re_general_category_stage_5[] = {
    15, 15, 12, 23, 23, 23, 25, 23, 20, 21, 23, 24, 23, 19,  9,  9,
    24, 24, 24, 23, 23,  1,  1,  1,  1, 20, 23, 21, 26, 22, 26,  2,
     2,  2,  2, 20, 24, 21, 24, 15, 25, 25, 27, 23, 26, 27,  5, 28,
    24, 16, 27, 26, 27, 24, 11, 11, 26, 11,  5, 29, 11, 23,  1, 24,
     1,  2,  2, 24,  2,  1,  2,  5,  5,  5,  1,  3,  3,  2,  5,  2,
     4,  4, 26, 26,  4, 26,  6,  6,  0,  0,  4,  2,  1, 23,  1,  0,
     0,  1, 24,  1, 27,  6,  7,  7,  0,  4,  0,  2,  0, 23, 19,  0,
     0, 27, 27, 25,  0,  6, 19,  6, 23,  6,  6, 23,  5,  0,  5, 23,
    23,  0, 16, 16, 23, 25, 27, 27, 16,  0,  4,  5,  5,  6,  6,  5,
    23,  5,  6, 16,  6,  4,  4,  6,  6, 27,  5, 27, 27,  5,  0, 16,
     6,  0,  0,  5,  4,  0,  6,  8,  8,  8,  8,  6, 23,  4,  0,  8,
     8,  0, 11, 27, 27,  0,  0, 25, 23, 27,  5,  8,  8,  5, 23, 11,
    11,  0, 19,  5, 12,  5,  5, 20, 21,  0, 10, 10, 10,  5, 19, 23,
     5,  4,  7,  0,  2,  4,  3,  3,  2,  0,  3, 26,  2, 26,  0, 26,
     1, 26, 26,  0, 12, 12, 12, 16, 19, 19, 28, 29, 20, 28, 13, 14,
    16, 12, 23, 28, 29, 23, 23, 22, 22, 23, 24, 20, 21, 23, 23, 12,
    11,  4, 21,  4, 25,  0,  6,  7,  7,  6,  1, 27, 27,  1, 27,  2,
     2, 27, 10,  1,  2, 10, 10, 11, 24, 27, 27, 20, 21, 27, 21, 24,
    21, 20,  2,  6, 20,  0, 27,  4,  5, 10, 19, 20, 21, 21, 27, 10,
    19,  4, 10,  4,  6, 26, 26,  4, 27, 11,  4, 23,  7, 23, 26,  1,
    25, 27,  8, 23,  4,  8, 18, 18, 17, 17,  5, 24, 23, 20, 19, 22,
    22, 20, 22, 22, 24, 19, 24,  0, 24, 26,  0, 11,  6, 11, 10,  0,
    23, 10,  5, 11, 23, 16, 27,  8,  8, 16, 16,  6,
};

/* General_Category: 9628 bytes. */

RE_UINT32 re_get_general_category(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 11;
    code = ch ^ (f << 11);
    pos = (RE_UINT32)re_general_category_stage_1[f] << 4;
    f = code >> 7;
    code ^= f << 7;
    pos = (RE_UINT32)re_general_category_stage_2[pos + f] << 3;
    f = code >> 4;
    code ^= f << 4;
    pos = (RE_UINT32)re_general_category_stage_3[pos + f] << 3;
    f = code >> 1;
    code ^= f << 1;
    pos = (RE_UINT32)re_general_category_stage_4[pos + f] << 1;
    value = re_general_category_stage_5[pos + code];

    return value;
}

/* Block. */

static RE_UINT8 re_block_stage_1[] = {
     0,  1,  2,  3,  4,  5,  5,  5,  5,  5,  6,  7,  7,  8,  9, 10,
    11, 12, 13, 14, 15, 16, 17, 16, 16, 16, 16, 18, 16, 19, 20, 21,
    22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 23, 24, 25, 16, 16, 26,
    16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16,
    16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16,
    16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16,
    16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16,
    16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16,
    16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16,
    16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16,
    16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16,
    16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16,
    16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16,
    16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16,
    27, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16,
    28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28,
    29, 29, 29, 29, 29, 29, 29, 29, 29, 29, 29, 29, 29, 29, 29, 29,
};

static RE_UINT8 re_block_stage_2[] = {
      0,   1,   2,   3,   4,   5,   6,   7,   8,   8,   9,  10,  11,  11,  12,  13,
     14,  15,  16,  17,  18,  19,  20,  21,  22,  23,  24,  25,  26,  27,  28,  28,
     29,  30,  31,  31,  32,  32,  32,  33,  34,  34,  34,  34,  34,  35,  36,  37,
     38,  39,  40,  41,  42,  43,  44,  45,  46,  47,  48,  49,  50,  50,  51,  51,
     52,  53,  54,  55,  56,  56,  57,  57,  58,  59,  60,  61,  62,  62,  63,  64,
     65,  65,  66,  67,  68,  68,  69,  69,  70,  71,  72,  73,  74,  75,  76,  77,
     78,  79,  80,  81,  82,  82,  83,  83,  84,  84,  84,  84,  84,  84,  84,  84,
     84,  84,  84,  84,  84,  84,  84,  84,  84,  84,  84,  84,  84,  84,  84,  84,
     84,  84,  84,  84,  84,  84,  84,  84,  84,  84,  84,  84,  84,  84,  84,  84,
     84,  84,  84,  84,  84,  84,  84,  84,  84,  84,  84,  85,  86,  86,  86,  86,
     86,  86,  86,  86,  86,  86,  86,  86,  86,  86,  86,  86,  86,  86,  86,  86,
     86,  86,  86,  86,  86,  86,  86,  86,  86,  86,  86,  86,  86,  86,  86,  86,
     87,  87,  87,  87,  87,  87,  87,  87,  87,  88,  89,  89,  90,  91,  92,  93,
     94,  95,  96,  97,  98,  99, 100, 101, 102, 102, 102, 102, 102, 102, 102, 102,
    102, 102, 102, 102, 102, 102, 102, 102, 102, 102, 102, 102, 102, 102, 102, 102,
    102, 102, 102, 102, 102, 102, 102, 102, 102, 102, 102, 102, 102, 102, 102, 102,
    102, 102, 102, 102, 102, 102, 102, 102, 102, 102, 102, 102, 102, 102, 102, 103,
    104, 104, 104, 104, 104, 104, 104, 105, 106, 106, 106, 106, 106, 106, 106, 106,
    107, 107, 107, 107, 107, 107, 107, 107, 107, 107, 107, 107, 107, 107, 107, 107,
    107, 107, 107, 107, 107, 107, 107, 107, 107, 107, 107, 107, 107, 107, 107, 107,
    107, 107, 107, 107, 107, 107, 107, 107, 107, 107, 107, 107, 107, 107, 107, 107,
    107, 107, 108, 108, 108, 108, 109, 110, 110, 110, 110, 110, 111, 112, 113, 114,
    115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 119, 126, 126, 126, 119,
    127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 119, 119, 137, 119, 119, 119,
    138, 139, 140, 141, 142, 143, 144, 119, 119, 145, 119, 146, 147, 148, 149, 119,
    119, 150, 119, 119, 119, 151, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119,
    152, 152, 152, 152, 152, 152, 152, 152, 153, 154, 155, 119, 119, 119, 119, 119,
    119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119,
    156, 156, 156, 156, 156, 156, 156, 156, 157, 119, 119, 119, 119, 119, 119, 119,
    119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119,
    119, 119, 119, 119, 119, 119, 119, 119, 158, 158, 158, 158, 158, 119, 119, 119,
    119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119,
    119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119,
    119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119,
    119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119,
    159, 159, 159, 159, 160, 161, 162, 163, 119, 119, 119, 119, 119, 119, 164, 165,
    166, 166, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119,
    119, 119, 119, 119, 119, 119, 119, 119, 167, 168, 119, 119, 119, 119, 119, 119,
    169, 169, 170, 170, 171, 119, 172, 119, 173, 173, 173, 173, 173, 173, 173, 173,
    174, 174, 174, 174, 174, 175, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119,
    119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119,
    176, 177, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 178, 178, 119, 119,
    179, 180, 181, 181, 182, 182, 183, 183, 183, 183, 183, 183, 184, 185, 186, 187,
    188, 188, 189, 189, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119,
    190, 190, 190, 190, 190, 190, 190, 190, 190, 190, 190, 190, 190, 190, 190, 190,
    190, 190, 190, 190, 190, 190, 190, 190, 190, 190, 190, 190, 190, 190, 190, 190,
    190, 190, 190, 190, 190, 190, 190, 190, 190, 190, 190, 190, 190, 191, 192, 192,
    192, 192, 192, 192, 192, 192, 192, 192, 192, 192, 192, 192, 192, 192, 192, 192,
    192, 192, 192, 192, 192, 192, 192, 192, 192, 192, 192, 192, 192, 192, 193, 194,
    195, 196, 196, 196, 196, 196, 196, 196, 196, 196, 196, 196, 196, 196, 196, 196,
    196, 196, 196, 196, 196, 196, 196, 196, 196, 196, 196, 196, 196, 196, 196, 196,
    196, 196, 196, 196, 196, 196, 196, 196, 196, 196, 196, 196, 196, 197, 119, 119,
    119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119,
    198, 198, 198, 198, 199, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119,
    200, 119, 201, 202, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119,
    119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119, 119,
    203, 203, 203, 203, 203, 203, 203, 203, 203, 203, 203, 203, 203, 203, 203, 203,
    203, 203, 203, 203, 203, 203, 203, 203, 203, 203, 203, 203, 203, 203, 203, 203,
    204, 204, 204, 204, 204, 204, 204, 204, 204, 204, 204, 204, 204, 204, 204, 204,
    204, 204, 204, 204, 204, 204, 204, 204, 204, 204, 204, 204, 204, 204, 204, 204,
};

static RE_UINT16 re_block_stage_3[] = {
      0,   0,   0,   0,   0,   0,   0,   0,   1,   1,   1,   1,   1,   1,   1,   1,
      2,   2,   2,   2,   2,   2,   2,   2,   3,   3,   3,   3,   3,   3,   3,   3,
      3,   3,   3,   3,   3,   4,   4,   4,   4,   4,   4,   5,   5,   5,   5,   5,
      6,   6,   6,   6,   6,   6,   6,   7,   7,   7,   7,   7,   7,   7,   7,   7,
      8,   8,   8,   8,   8,   8,   8,   8,   9,   9,   9,  10,  10,  10,  10,  10,
     10,  11,  11,  11,  11,  11,  11,  11,  12,  12,  12,  12,  12,  12,  12,  12,
     13,  13,  13,  13,  13,  14,  14,  14,  15,  15,  15,  15,  16,  16,  16,  16,
     17,  17,  17,  17,  18,  18,  19,  19,  19,  19,  20,  20,  20,  20,  20,  20,
     21,  21,  21,  21,  21,  21,  21,  21,  22,  22,  22,  22,  22,  22,  22,  22,
     23,  23,  23,  23,  23,  23,  23,  23,  24,  24,  24,  24,  24,  24,  24,  24,
     25,  25,  25,  25,  25,  25,  25,  25,  26,  26,  26,  26,  26,  26,  26,  26,
     27,  27,  27,  27,  27,  27,  27,  27,  28,  28,  28,  28,  28,  28,  28,  28,
     29,  29,  29,  29,  29,  29,  29,  29,  30,  30,  30,  30,  30,  30,  30,  30,
     31,  31,  31,  31,  31,  31,  31,  31,  32,  32,  32,  32,  32,  32,  32,  32,
     33,  33,  33,  33,  33,  33,  33,  33,  34,  34,  34,  34,  34,  34,  34,  34,
     34,  34,  35,  35,  35,  35,  35,  35,  36,  36,  36,  36,  36,  36,  36,  36,
     37,  37,  37,  37,  37,  37,  37,  37,  38,  38,  39,  39,  39,  39,  39,  39,
     40,  40,  40,  40,  40,  40,  40,  40,  41,  41,  42,  42,  42,  42,  42,  42,
     43,  43,  44,  44,  45,  45,  46,  46,  47,  47,  47,  47,  47,  47,  47,  47,
     48,  48,  48,  48,  48,  48,  48,  48,  48,  48,  48,  49,  49,  49,  49,  49,
     50,  50,  50,  50,  50,  51,  51,  51,  52,  52,  52,  52,  52,  52,  53,  53,
     54,  54,  55,  55,  55,  55,  55,  55,  55,  55,  55,  56,  56,  56,  56,  56,
     57,  57,  57,  57,  57,  57,  57,  57,  58,  58,  58,  58,  59,  59,  59,  59,
     60,  60,  60,  60,  60,  61,  61,  61,  19,  19,  19,  19,  62,  63,  63,  63,
     64,  64,  64,  64,  64,  64,  64,  64,  65,  65,  65,  65,  66,  66,  66,  66,
     67,  67,  67,  67,  67,  67,  67,  67,  68,  68,  68,  68,  68,  68,  68,  68,
     69,  69,  69,  69,  69,  69,  69,  70,  70,  70,  71,  71,  71,  72,  72,  72,
     73,  73,  73,  73,  73,  74,  74,  74,  74,  75,  75,  75,  75,  75,  75,  75,
     76,  76,  76,  76,  76,  76,  76,  76,  77,  77,  77,  77,  77,  77,  77,  77,
     78,  78,  78,  78,  79,  79,  80,  80,  80,  80,  80,  80,  80,  80,  80,  80,
     81,  81,  81,  81,  81,  81,  81,  81,  82,  82,  83,  83,  83,  83,  83,  83,
     84,  84,  84,  84,  84,  84,  84,  84,  85,  85,  85,  85,  85,  85,  85,  85,
     85,  85,  85,  85,  86,  86,  86,  87,  88,  88,  88,  88,  88,  88,  88,  88,
     89,  89,  89,  89,  89,  89,  89,  89,  90,  90,  90,  90,  90,  90,  90,  90,
     91,  91,  91,  91,  91,  91,  91,  91,  92,  92,  92,  92,  92,  92,  92,  92,
     93,  93,  93,  93,  93,  93,  94,  94,  95,  95,  95,  95,  95,  95,  95,  95,
     96,  96,  96,  97,  97,  97,  97,  97,  98,  98,  98,  98,  98,  98,  99,  99,
    100, 100, 100, 100, 100, 100, 100, 100, 101, 101, 101, 101, 101, 101, 101, 101,
    102, 102, 102, 102, 102, 102, 102, 102, 102, 102, 102, 102, 102, 102,  19, 103,
    104, 104, 104, 104, 105, 105, 105, 105, 105, 105, 106, 106, 106, 106, 106, 106,
    107, 107, 107, 108, 108, 108, 108, 108, 108, 109, 110, 110, 111, 111, 111, 112,
    113, 113, 113, 113, 113, 113, 113, 113, 114, 114, 114, 114, 114, 114, 114, 114,
    115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 116, 116, 116, 116,
    117, 117, 117, 117, 117, 117, 117, 117, 118, 118, 118, 118, 118, 118, 118, 118,
    118, 119, 119, 119, 119, 120, 120, 120, 121, 121, 121, 121, 121, 121, 121, 121,
    121, 121, 121, 121, 122, 122, 122, 122, 122, 122, 123, 123, 123, 123, 123, 123,
    124, 124, 125, 125, 125, 125, 125, 125, 125, 125, 125, 125, 125, 125, 125, 125,
    126, 126, 126, 127, 128, 128, 128, 128, 129, 129, 129, 129, 129, 129, 130, 130,
    131, 131, 131, 132, 132, 132, 133, 133, 134, 134, 134, 134, 134, 134, 135, 135,
    136, 136, 136, 136, 136, 136, 137, 137, 138, 138, 138, 138, 138, 138, 139, 139,
    140, 140, 140, 141, 141, 141, 141, 142, 142, 142, 142, 142, 143, 143, 143, 143,
    144, 144, 144, 144, 144, 144, 144, 144, 144, 144, 144, 145, 145, 145, 145, 145,
    146, 146, 146, 146, 146, 146, 146, 146, 147, 147, 147, 147, 147, 147, 147, 147,
    148, 148, 148, 148, 148, 148, 148, 148, 149, 149, 149, 149, 149, 149, 149, 149,
    150, 150, 150, 150, 150, 150, 150, 150, 151, 151, 151, 151, 151, 152, 152, 152,
    152, 152, 152, 152, 152, 152, 152, 152, 153, 154, 155, 156, 156, 157, 157, 158,
    158, 158, 158, 158, 158, 158, 158, 158, 159, 159, 159, 159, 159, 159, 159, 159,
    159, 159, 159, 159, 159, 159, 159, 160, 161, 161, 161, 161, 161, 161, 161, 161,
    162, 162, 162, 162, 162, 162, 162, 162, 163, 163, 163, 163, 164, 164, 164, 164,
    164, 165, 165, 165, 165, 166, 166, 166,  19,  19,  19,  19,  19,  19,  19,  19,
    167, 167, 168, 168, 168, 168, 169, 169, 170, 170, 170, 171, 171, 172, 172, 172,
    173, 173, 174, 174, 174, 174,  19,  19, 175, 175, 175, 175, 175, 176, 176, 176,
    177, 177, 177,  19,  19,  19,  19,  19, 178, 178, 178, 179, 179, 179, 179,  19,
    180, 180, 180, 180, 180, 180, 180, 180, 181, 181, 181, 181, 182, 182, 183, 183,
    184, 184, 184,  19,  19,  19, 185, 185, 186, 186, 187, 187,  19,  19,  19,  19,
    188, 188, 189, 189, 189, 189, 189, 189, 190, 190, 190, 190, 190, 190, 191, 191,
    192, 192,  19,  19, 193, 193, 193, 193, 194, 194, 194, 194, 195, 195, 196, 196,
    197, 197, 197,  19,  19,  19,  19,  19, 198, 198, 198, 198, 198,  19,  19,  19,
    199, 199, 199, 199, 199, 199, 199, 199,  19,  19,  19,  19,  19,  19, 200, 200,
    201, 201, 201, 201, 201, 201, 201, 201, 202, 202, 202, 202, 202, 203, 203, 203,
    204, 204, 204, 204, 204, 205, 205, 205, 206, 206, 206, 206, 206, 206, 207, 207,
    208, 208, 208, 208, 208,  19,  19,  19, 209, 209, 209, 210, 210, 210, 210, 210,
    211, 211, 211, 211, 211, 211, 211, 211, 212, 212, 212, 212, 212, 212,  19,  19,
    213, 213, 213, 213, 213, 213, 213, 213, 214, 214, 214, 214, 214, 214,  19,  19,
    215, 215, 215, 215, 215,  19,  19,  19, 216, 216, 216, 216,  19,  19,  19,  19,
     19,  19, 217, 217, 217, 217, 217, 217,  19,  19,  19,  19, 218, 218, 218, 218,
    219, 219, 219, 219, 219, 219, 219, 219, 220, 220, 220, 220, 220, 220, 220, 220,
    221, 221, 221, 221, 221, 221, 221, 221, 221, 221, 221, 221, 221,  19,  19,  19,
    222, 222, 222, 222, 222, 222, 222, 222, 222, 222, 222,  19,  19,  19,  19,  19,
    223, 223, 223, 223, 223, 223, 223, 223, 224, 224, 224, 224, 224, 224, 224, 224,
    224, 224, 224, 224, 225, 225, 225,  19,  19,  19,  19,  19,  19, 226, 226, 226,
    227, 227, 227, 227, 227, 227, 227, 227, 227,  19,  19,  19,  19,  19,  19,  19,
    228, 228, 228, 228, 228, 228, 228, 228, 228, 228,  19,  19,  19,  19,  19,  19,
    229, 229, 229, 229, 229, 229, 229, 229, 230, 230, 230, 230, 230, 230, 230, 230,
    230, 230, 231,  19,  19,  19,  19,  19, 232, 232, 232, 232, 232, 232, 232, 232,
    233, 233, 233, 233, 233, 233, 233, 233, 234, 234, 234, 234, 234,  19,  19,  19,
    235, 235, 235, 235, 235, 235, 236, 236, 237, 237, 237, 237, 237, 237, 237, 237,
    238, 238, 238, 238, 238, 238, 238, 238, 238, 238, 238,  19,  19,  19,  19,  19,
    239, 239, 239, 239, 239, 239, 239, 239, 239, 239, 239, 239, 239, 239,  19,  19,
    240, 240, 240, 240, 240, 240, 240, 240, 241, 241, 241, 242, 242, 242, 242, 242,
    242, 242, 243, 243, 243, 243, 243, 243, 244, 244, 244, 244, 244, 244, 244, 244,
    245, 245, 245, 245, 245, 245, 245, 245, 246, 246, 246, 246, 246, 246, 246, 246,
    247, 247, 247, 247, 247, 248, 248, 248, 249, 249, 249, 249, 249, 249, 249, 249,
    250, 250, 250, 250, 250, 250, 250, 250, 251, 251, 251, 251, 251, 251, 251, 251,
    252, 252, 252, 252, 252, 252, 252, 252, 253, 253, 253, 253, 253, 253, 253, 253,
    254, 254, 254, 254, 254, 254, 254, 254, 254, 254, 254, 254, 254, 254,  19,  19,
    255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 256, 256, 256, 256,
    256, 256, 256, 256, 256, 256, 256, 256, 256, 256, 257, 257, 257, 257, 257, 257,
    257, 257, 257, 257, 257, 257, 257, 257, 257, 257, 257,  19,  19,  19,  19,  19,
    258, 258, 258, 258, 258, 258, 258, 258, 258, 258,  19,  19,  19,  19,  19,  19,
    259, 259, 259, 259, 259, 259, 259, 259, 260, 260, 260, 260, 260, 260, 260, 260,
    260, 260, 260, 260, 260, 260, 260,  19, 261, 261, 261, 261, 261, 261, 261, 261,
    262, 262, 262, 262, 262, 262, 262, 262,
};

static RE_UINT16 re_block_stage_4[] = {
      0,   0,   0,   0,   1,   1,   1,   1,   2,   2,   2,   2,   3,   3,   3,   3,
      4,   4,   4,   4,   5,   5,   5,   5,   6,   6,   6,   6,   7,   7,   7,   7,
      8,   8,   8,   8,   9,   9,   9,   9,  10,  10,  10,  10,  11,  11,  11,  11,
     12,  12,  12,  12,  13,  13,  13,  13,  14,  14,  14,  14,  15,  15,  15,  15,
     16,  16,  16,  16,  17,  17,  17,  17,  18,  18,  18,  18,  19,  19,  19,  19,
     20,  20,  20,  20,  21,  21,  21,  21,  22,  22,  22,  22,  23,  23,  23,  23,
     24,  24,  24,  24,  25,  25,  25,  25,  26,  26,  26,  26,  27,  27,  27,  27,
     28,  28,  28,  28,  29,  29,  29,  29,  30,  30,  30,  30,  31,  31,  31,  31,
     32,  32,  32,  32,  33,  33,  33,  33,  34,  34,  34,  34,  35,  35,  35,  35,
     36,  36,  36,  36,  37,  37,  37,  37,  38,  38,  38,  38,  39,  39,  39,  39,
     40,  40,  40,  40,  41,  41,  41,  41,  42,  42,  42,  42,  43,  43,  43,  43,
     44,  44,  44,  44,  45,  45,  45,  45,  46,  46,  46,  46,  47,  47,  47,  47,
     48,  48,  48,  48,  49,  49,  49,  49,  50,  50,  50,  50,  51,  51,  51,  51,
     52,  52,  52,  52,  53,  53,  53,  53,  54,  54,  54,  54,  55,  55,  55,  55,
     56,  56,  56,  56,  57,  57,  57,  57,  58,  58,  58,  58,  59,  59,  59,  59,
     60,  60,  60,  60,  61,  61,  61,  61,  62,  62,  62,  62,  63,  63,  63,  63,
     64,  64,  64,  64,  65,  65,  65,  65,  66,  66,  66,  66,  67,  67,  67,  67,
     68,  68,  68,  68,  69,  69,  69,  69,  70,  70,  70,  70,  71,  71,  71,  71,
     72,  72,  72,  72,  73,  73,  73,  73,  74,  74,  74,  74,  75,  75,  75,  75,
     76,  76,  76,  76,  77,  77,  77,  77,  78,  78,  78,  78,  79,  79,  79,  79,
     80,  80,  80,  80,  81,  81,  81,  81,  82,  82,  82,  82,  83,  83,  83,  83,
     84,  84,  84,  84,  85,  85,  85,  85,  86,  86,  86,  86,  87,  87,  87,  87,
     88,  88,  88,  88,  89,  89,  89,  89,  90,  90,  90,  90,  91,  91,  91,  91,
     92,  92,  92,  92,  93,  93,  93,  93,  94,  94,  94,  94,  95,  95,  95,  95,
     96,  96,  96,  96,  97,  97,  97,  97,  98,  98,  98,  98,  99,  99,  99,  99,
    100, 100, 100, 100, 101, 101, 101, 101, 102, 102, 102, 102, 103, 103, 103, 103,
    104, 104, 104, 104, 105, 105, 105, 105, 106, 106, 106, 106, 107, 107, 107, 107,
    108, 108, 108, 108, 109, 109, 109, 109, 110, 110, 110, 110, 111, 111, 111, 111,
    112, 112, 112, 112, 113, 113, 113, 113, 114, 114, 114, 114, 115, 115, 115, 115,
    116, 116, 116, 116, 117, 117, 117, 117, 118, 118, 118, 118, 119, 119, 119, 119,
    120, 120, 120, 120, 121, 121, 121, 121, 122, 122, 122, 122, 123, 123, 123, 123,
    124, 124, 124, 124, 125, 125, 125, 125, 126, 126, 126, 126, 127, 127, 127, 127,
    128, 128, 128, 128, 129, 129, 129, 129, 130, 130, 130, 130, 131, 131, 131, 131,
    132, 132, 132, 132, 133, 133, 133, 133, 134, 134, 134, 134, 135, 135, 135, 135,
    136, 136, 136, 136, 137, 137, 137, 137, 138, 138, 138, 138, 139, 139, 139, 139,
    140, 140, 140, 140, 141, 141, 141, 141, 142, 142, 142, 142, 143, 143, 143, 143,
    144, 144, 144, 144, 145, 145, 145, 145, 146, 146, 146, 146, 147, 147, 147, 147,
    148, 148, 148, 148, 149, 149, 149, 149, 150, 150, 150, 150, 151, 151, 151, 151,
    152, 152, 152, 152, 153, 153, 153, 153, 154, 154, 154, 154, 155, 155, 155, 155,
    156, 156, 156, 156, 157, 157, 157, 157, 158, 158, 158, 158, 159, 159, 159, 159,
    160, 160, 160, 160, 161, 161, 161, 161, 162, 162, 162, 162, 163, 163, 163, 163,
    164, 164, 164, 164, 165, 165, 165, 165, 166, 166, 166, 166, 167, 167, 167, 167,
    168, 168, 168, 168, 169, 169, 169, 169, 170, 170, 170, 170, 171, 171, 171, 171,
    172, 172, 172, 172, 173, 173, 173, 173, 174, 174, 174, 174, 175, 175, 175, 175,
    176, 176, 176, 176, 177, 177, 177, 177, 178, 178, 178, 178, 179, 179, 179, 179,
    180, 180, 180, 180, 181, 181, 181, 181, 182, 182, 182, 182, 183, 183, 183, 183,
    184, 184, 184, 184, 185, 185, 185, 185, 186, 186, 186, 186, 187, 187, 187, 187,
    188, 188, 188, 188, 189, 189, 189, 189, 190, 190, 190, 190, 191, 191, 191, 191,
    192, 192, 192, 192, 193, 193, 193, 193, 194, 194, 194, 194, 195, 195, 195, 195,
    196, 196, 196, 196, 197, 197, 197, 197, 198, 198, 198, 198, 199, 199, 199, 199,
    200, 200, 200, 200, 201, 201, 201, 201, 202, 202, 202, 202, 203, 203, 203, 203,
    204, 204, 204, 204, 205, 205, 205, 205, 206, 206, 206, 206, 207, 207, 207, 207,
    208, 208, 208, 208, 209, 209, 209, 209, 210, 210, 210, 210, 211, 211, 211, 211,
    212, 212, 212, 212, 213, 213, 213, 213, 214, 214, 214, 214, 215, 215, 215, 215,
    216, 216, 216, 216, 217, 217, 217, 217, 218, 218, 218, 218, 219, 219, 219, 219,
    220, 220, 220, 220, 221, 221, 221, 221, 222, 222, 222, 222, 223, 223, 223, 223,
    224, 224, 224, 224, 225, 225, 225, 225, 226, 226, 226, 226, 227, 227, 227, 227,
    228, 228, 228, 228, 229, 229, 229, 229, 230, 230, 230, 230, 231, 231, 231, 231,
    232, 232, 232, 232, 233, 233, 233, 233, 234, 234, 234, 234, 235, 235, 235, 235,
    236, 236, 236, 236, 237, 237, 237, 237, 238, 238, 238, 238, 239, 239, 239, 239,
    240, 240, 240, 240, 241, 241, 241, 241, 242, 242, 242, 242, 243, 243, 243, 243,
    244, 244, 244, 244, 245, 245, 245, 245, 246, 246, 246, 246, 247, 247, 247, 247,
    248, 248, 248, 248, 249, 249, 249, 249, 250, 250, 250, 250, 251, 251, 251, 251,
    252, 252, 252, 252, 253, 253, 253, 253, 254, 254, 254, 254, 255, 255, 255, 255,
    256, 256, 256, 256, 257, 257, 257, 257, 258, 258, 258, 258, 259, 259, 259, 259,
    260, 260, 260, 260, 261, 261, 261, 261, 262, 262, 262, 262,
};

static RE_UINT16 re_block_stage_5[] = {
      1,   1,   1,   1,   2,   2,   2,   2,   3,   3,   3,   3,   4,   4,   4,   4,
      5,   5,   5,   5,   6,   6,   6,   6,   7,   7,   7,   7,   8,   8,   8,   8,
      9,   9,   9,   9,  10,  10,  10,  10,  11,  11,  11,  11,  12,  12,  12,  12,
     13,  13,  13,  13,  14,  14,  14,  14,  15,  15,  15,  15,  16,  16,  16,  16,
     17,  17,  17,  17,  18,  18,  18,  18,  19,  19,  19,  19,   0,   0,   0,   0,
     20,  20,  20,  20,  21,  21,  21,  21,  22,  22,  22,  22,  23,  23,  23,  23,
     24,  24,  24,  24,  25,  25,  25,  25,  26,  26,  26,  26,  27,  27,  27,  27,
     28,  28,  28,  28,  29,  29,  29,  29,  30,  30,  30,  30,  31,  31,  31,  31,
     32,  32,  32,  32,  33,  33,  33,  33,  34,  34,  34,  34,  35,  35,  35,  35,
     36,  36,  36,  36,  37,  37,  37,  37,  38,  38,  38,  38,  39,  39,  39,  39,
     40,  40,  40,  40,  41,  41,  41,  41,  42,  42,  42,  42,  43,  43,  43,  43,
     44,  44,  44,  44,  45,  45,  45,  45,  46,  46,  46,  46,  47,  47,  47,  47,
     48,  48,  48,  48,  49,  49,  49,  49,  50,  50,  50,  50,  51,  51,  51,  51,
     52,  52,  52,  52,  53,  53,  53,  53,  54,  54,  54,  54,  55,  55,  55,  55,
     56,  56,  56,  56,  57,  57,  57,  57,  58,  58,  58,  58,  59,  59,  59,  59,
     60,  60,  60,  60,  61,  61,  61,  61,  62,  62,  62,  62,  63,  63,  63,  63,
     64,  64,  64,  64,  65,  65,  65,  65,  66,  66,  66,  66,  67,  67,  67,  67,
     68,  68,  68,  68,  69,  69,  69,  69,  70,  70,  70,  70,  71,  71,  71,  71,
     72,  72,  72,  72,  73,  73,  73,  73,  74,  74,  74,  74,  75,  75,  75,  75,
     76,  76,  76,  76,  77,  77,  77,  77,  78,  78,  78,  78,  79,  79,  79,  79,
     80,  80,  80,  80,  81,  81,  81,  81,  82,  82,  82,  82,  83,  83,  83,  83,
     84,  84,  84,  84,  85,  85,  85,  85,  86,  86,  86,  86,  87,  87,  87,  87,
     88,  88,  88,  88,  89,  89,  89,  89,  90,  90,  90,  90,  91,  91,  91,  91,
     92,  92,  92,  92,  93,  93,  93,  93,  94,  94,  94,  94,  95,  95,  95,  95,
     96,  96,  96,  96,  97,  97,  97,  97,  98,  98,  98,  98,  99,  99,  99,  99,
    100, 100, 100, 100, 101, 101, 101, 101, 102, 102, 102, 102, 103, 103, 103, 103,
    104, 104, 104, 104, 105, 105, 105, 105, 106, 106, 106, 106, 107, 107, 107, 107,
    108, 108, 108, 108, 109, 109, 109, 109, 110, 110, 110, 110, 111, 111, 111, 111,
    112, 112, 112, 112, 113, 113, 113, 113, 114, 114, 114, 114, 115, 115, 115, 115,
    116, 116, 116, 116, 117, 117, 117, 117, 118, 118, 118, 118, 119, 119, 119, 119,
    120, 120, 120, 120, 121, 121, 121, 121, 122, 122, 122, 122, 123, 123, 123, 123,
    124, 124, 124, 124, 125, 125, 125, 125, 126, 126, 126, 126, 127, 127, 127, 127,
    128, 128, 128, 128, 129, 129, 129, 129, 130, 130, 130, 130, 131, 131, 131, 131,
    132, 132, 132, 132, 133, 133, 133, 133, 134, 134, 134, 134, 135, 135, 135, 135,
    136, 136, 136, 136, 137, 137, 137, 137, 138, 138, 138, 138, 139, 139, 139, 139,
    140, 140, 140, 140, 141, 141, 141, 141, 142, 142, 142, 142, 143, 143, 143, 143,
    144, 144, 144, 144, 145, 145, 145, 145, 146, 146, 146, 146, 147, 147, 147, 147,
    148, 148, 148, 148, 149, 149, 149, 149, 150, 150, 150, 150, 151, 151, 151, 151,
    152, 152, 152, 152, 153, 153, 153, 153, 154, 154, 154, 154, 155, 155, 155, 155,
    156, 156, 156, 156, 157, 157, 157, 157, 158, 158, 158, 158, 159, 159, 159, 159,
    160, 160, 160, 160, 161, 161, 161, 161, 162, 162, 162, 162, 163, 163, 163, 163,
    164, 164, 164, 164, 165, 165, 165, 165, 166, 166, 166, 166, 167, 167, 167, 167,
    168, 168, 168, 168, 169, 169, 169, 169, 170, 170, 170, 170, 171, 171, 171, 171,
    172, 172, 172, 172, 173, 173, 173, 173, 174, 174, 174, 174, 175, 175, 175, 175,
    176, 176, 176, 176, 177, 177, 177, 177, 178, 178, 178, 178, 179, 179, 179, 179,
    180, 180, 180, 180, 181, 181, 181, 181, 182, 182, 182, 182, 183, 183, 183, 183,
    184, 184, 184, 184, 185, 185, 185, 185, 186, 186, 186, 186, 187, 187, 187, 187,
    188, 188, 188, 188, 189, 189, 189, 189, 190, 190, 190, 190, 191, 191, 191, 191,
    192, 192, 192, 192, 193, 193, 193, 193, 194, 194, 194, 194, 195, 195, 195, 195,
    196, 196, 196, 196, 197, 197, 197, 197, 198, 198, 198, 198, 199, 199, 199, 199,
    200, 200, 200, 200, 201, 201, 201, 201, 202, 202, 202, 202, 203, 203, 203, 203,
    204, 204, 204, 204, 205, 205, 205, 205, 206, 206, 206, 206, 207, 207, 207, 207,
    208, 208, 208, 208, 209, 209, 209, 209, 210, 210, 210, 210, 211, 211, 211, 211,
    212, 212, 212, 212, 213, 213, 213, 213, 214, 214, 214, 214, 215, 215, 215, 215,
    216, 216, 216, 216, 217, 217, 217, 217, 218, 218, 218, 218, 219, 219, 219, 219,
    220, 220, 220, 220, 221, 221, 221, 221, 222, 222, 222, 222, 223, 223, 223, 223,
    224, 224, 224, 224, 225, 225, 225, 225, 226, 226, 226, 226, 227, 227, 227, 227,
    228, 228, 228, 228, 229, 229, 229, 229, 230, 230, 230, 230, 231, 231, 231, 231,
    232, 232, 232, 232, 233, 233, 233, 233, 234, 234, 234, 234, 235, 235, 235, 235,
    236, 236, 236, 236, 237, 237, 237, 237, 238, 238, 238, 238, 239, 239, 239, 239,
    240, 240, 240, 240, 241, 241, 241, 241, 242, 242, 242, 242, 243, 243, 243, 243,
    244, 244, 244, 244, 245, 245, 245, 245, 246, 246, 246, 246, 247, 247, 247, 247,
    248, 248, 248, 248, 249, 249, 249, 249, 250, 250, 250, 250, 251, 251, 251, 251,
    252, 252, 252, 252, 253, 253, 253, 253, 254, 254, 254, 254, 255, 255, 255, 255,
    256, 256, 256, 256, 257, 257, 257, 257, 258, 258, 258, 258, 259, 259, 259, 259,
    260, 260, 260, 260, 261, 261, 261, 261, 262, 262, 262, 262,
};

/* Block: 8720 bytes. */

RE_UINT32 re_get_block(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 12;
    code = ch ^ (f << 12);
    pos = (RE_UINT32)re_block_stage_1[f] << 5;
    f = code >> 7;
    code ^= f << 7;
    pos = (RE_UINT32)re_block_stage_2[pos + f] << 3;
    f = code >> 4;
    code ^= f << 4;
    pos = (RE_UINT32)re_block_stage_3[pos + f] << 2;
    f = code >> 2;
    code ^= f << 2;
    pos = (RE_UINT32)re_block_stage_4[pos + f] << 2;
    value = re_block_stage_5[pos + code];

    return value;
}

/* Script. */

static RE_UINT8 re_script_stage_1[] = {
     0,  1,  2,  3,  4,  5,  6,  7,  7,  8,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  9, 10, 11, 12, 12, 12, 12, 13, 14, 14, 14, 14, 15,
    16, 17, 18, 19, 20, 14, 21, 14, 22, 14, 14, 14, 14, 23, 14, 14,
    14, 14, 14, 14, 14, 14, 24, 25, 14, 14, 26, 27, 14, 28, 29, 30,
     7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  7, 31,  7, 32, 33,  7, 34, 14, 14, 14, 14, 14, 35,
    14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14,
    14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14,
    14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14,
    14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14,
    14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14,
    14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14,
    14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14,
    14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14,
    14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14,
    14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14,
    14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14,
    14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14,
    14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14,
    14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14,
    14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14,
    14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14,
    14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14,
    14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14,
    14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14,
    14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14,
    14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14,
    14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14,
    36, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14,
    14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14,
    14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14,
    14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14,
    14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14,
    14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14,
};

static RE_UINT8 re_script_stage_2[] = {
      0,   1,   2,   2,   2,   3,   4,   5,   6,   7,   8,   9,  10,  11,  12,  13,
     14,  15,  16,  17,  18,  19,  20,  21,  22,  23,  24,  25,  26,  27,  28,  29,
     30,  31,  32,  32,  33,  34,  35,  36,  37,  37,  37,  37,  37,  38,  39,  40,
     41,  42,  43,  44,  45,  46,  47,  48,  49,  50,  51,  52,   2,   2,  53,  54,
     55,  56,  57,  58,  59,  59,  59,  60,  61,  59,  59,  59,  59,  59,  59,  59,
     62,  62,  59,  59,  59,  59,  63,  64,  65,  66,  67,  68,  69,  70,  71,  72,
     73,  74,  75,  76,  77,  78,  79,  59,  71,  71,  71,  71,  71,  71,  71,  71,
     71,  71,  71,  71,  71,  71,  71,  71,  71,  71,  71,  71,  71,  71,  71,  71,
     71,  71,  71,  71,  71,  71,  71,  71,  71,  71,  71,  80,  71,  71,  71,  71,
     71,  71,  71,  71,  71,  71,  71,  71,  71,  71,  71,  71,  71,  71,  71,  81,
     82,  82,  82,  82,  82,  82,  82,  82,  82,  83,  84,  84,  85,  86,  87,  88,
     89,  90,  91,  92,  93,  94,  95,  96,  32,  32,  32,  32,  32,  32,  32,  32,
     32,  32,  32,  32,  32,  32,  32,  32,  32,  32,  32,  32,  32,  32,  32,  32,
     32,  32,  32,  32,  32,  32,  32,  32,  32,  32,  32,  32,  32,  32,  32,  97,
     98,  98,  98,  98,  98,  98,  98,  98,  98,  98,  98,  98,  98,  98,  98,  98,
     98,  98,  71,  71,  99, 100, 101, 102, 103, 103, 104, 105, 106, 107, 108, 109,
    110, 111, 112, 113,  98, 114, 115, 116, 117, 118, 119,  98, 120, 120, 121,  98,
    122, 123, 124, 125, 126, 127, 128, 129, 130, 131,  98,  98, 132,  98,  98,  98,
    133, 134, 135, 136, 137, 138, 139,  98,  98, 140,  98, 141, 142, 143, 144,  98,
     98, 145,  98,  98,  98, 146,  98,  98,  98,  98,  98,  98,  98,  98,  98,  98,
    147, 147, 147, 147, 147, 147, 147, 148, 149, 147, 150,  98,  98,  98,  98,  98,
    151, 151, 151, 151, 151, 151, 151, 151, 152,  98,  98,  98,  98,  98,  98,  98,
     98,  98,  98,  98,  98,  98,  98,  98, 153, 153, 153, 153, 154,  98,  98,  98,
    155, 155, 155, 155, 156, 157, 158, 159,  98,  98,  98,  98,  98,  98, 160, 161,
    162,  98,  98,  98,  98,  98,  98,  98,  98,  98,  98,  98,  98,  98,  98,  98,
     98,  98,  98,  98,  98,  98,  98,  98, 163, 164,  98,  98,  98,  98,  98,  98,
     59, 165, 166, 167, 168,  98, 169,  98, 170, 171, 172,  59,  59, 173,  59, 174,
    175, 175, 175, 175, 175, 176,  98,  98,  98,  98,  98,  98,  98,  98,  98,  98,
    177, 178,  98,  98,  98,  98,  98,  98,  98,  98,  98,  98, 179, 180,  98,  98,
    181, 182, 183, 184, 185,  98,  59,  59,  59,  59, 186, 187,  59, 188, 189, 190,
    191, 192, 193, 194,  98,  98,  98,  98,  98,  98,  98,  98,  98,  98,  98,  98,
     71,  71,  71,  71,  71,  71,  71,  71,  71,  71,  71,  71,  71, 195,  71,  71,
     71,  71,  71,  71,  71,  71,  71,  71,  71,  71,  71,  71,  71,  71, 196,  71,
    197,  71,  71,  71,  71,  71,  71,  71,  71,  71,  71,  71,  71,  71,  71,  71,
     71,  71,  71,  71,  71,  71,  71,  71,  71,  71,  71,  71,  71, 198,  98,  98,
     71,  71,  71,  71, 199,  98,  98,  98,  98,  98,  98,  98,  98,  98,  98,  98,
    200,  98, 201, 202,  98,  98,  98,  98,  98,  98,  98,  98,  98,  98,  98,  98,
};

static RE_UINT16 re_script_stage_3[] = {
      0,   0,   0,   0,   1,   2,   1,   2,   0,   0,   3,   3,   4,   5,   4,   5,
      4,   4,   4,   4,   4,   4,   4,   4,   4,   4,   4,   6,   0,   0,   7,   0,
      8,   8,   8,   8,   8,   8,   8,   9,  10,  11,  12,  11,  11,  11,  13,  11,
     14,  14,  14,  14,  14,  14,  14,  14,  15,  14,  14,  14,  14,  14,  14,  14,
     14,  14,  14,  16,  17,  18,  16,  17,  19,  20,  21,  21,  22,  21,  23,  24,
     25,  26,  27,  27,  28,  29,  27,  30,  27,  27,  27,  27,  27,  31,  27,  27,
     32,  33,  33,  33,  34,  27,  27,  27,  35,  35,  35,  36,  37,  37,  37,  38,
     39,  39,  40,  41,  42,  43,  44,  44,  44,  44,  27,  45,  44,  44,  46,  27,
     47,  47,  47,  47,  47,  48,  49,  47,  50,  51,  52,  53,  54,  55,  56,  57,
     58,  59,  60,  61,  62,  63,  64,  65,  66,  67,  68,  69,  70,  71,  72,  73,
     74,  75,  76,  77,  78,  79,  80,  81,  82,  83,  84,  85,  86,  87,  88,  89,
     90,  91,  92,  93,  94,  95,  96,  97,  98,  99, 100, 101, 102, 103, 104, 105,
    106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121,
    122, 123, 123, 124, 123, 125,  44,  44, 126, 127, 128, 129, 130, 131,  44,  44,
    132, 132, 132, 132, 133, 132, 134, 135, 132, 133, 132, 136, 136, 137,  44,  44,
    138, 138, 138, 138, 138, 138, 138, 138, 138, 138, 139, 139, 140, 139, 139, 141,
    142, 142, 142, 142, 142, 142, 142, 142, 143, 143, 143, 143, 144, 145, 143, 143,
    144, 143, 143, 146, 147, 148, 143, 143, 143, 147, 143, 143, 143, 149, 143, 150,
    143, 151, 152, 152, 152, 152, 152, 153, 154, 154, 154, 154, 154, 154, 154, 154,
    155, 156, 157, 157, 157, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167,
    168, 168, 168, 168, 168, 169, 170, 170, 171, 172, 173, 173, 173, 173, 173, 174,
    173, 173, 175, 154, 154, 154, 154, 176, 177, 178, 179, 179, 180, 181, 182, 183,
    184, 184, 185, 184, 186, 187, 168, 168, 188, 189, 190, 190, 190, 191, 190, 192,
    193, 193, 194, 195,  44,  44,  44,  44, 196, 196, 196, 196, 197, 196, 196, 198,
    199, 199, 199, 199, 200, 200, 200, 201, 202, 202, 202, 203, 204, 205, 205, 205,
     44,  44,  44,  44, 206, 207, 208, 209,   4,   4, 210,   4,   4, 211, 212, 213,
      4,   4,   4, 214,   8,   8,   8, 215,  11, 216,  11,  11, 216, 217,  11, 218,
     11,  11,  11, 219, 219, 220,  11, 221, 222,   0,   0,   0,   0,   0, 223, 224,
    225, 226,   0, 225,  44,   8,   8, 227,   0,   0, 228, 229, 230,   0,   4,   4,
    231,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0, 232,   0,   0, 233,  44, 232,  44,   0,   0,
    234, 234, 234, 234, 234, 234, 234, 234,   0,   0,   0,   0,   0,   0,   0, 235,
      0, 236,   0, 237, 238, 239, 240,  44, 241, 241, 242, 241, 241, 242,   4,   4,
    243, 243, 243, 243, 243, 243, 243, 244, 139, 139, 140, 245, 245, 245, 246, 247,
    143, 248, 249, 249, 249, 249,  14,  14,   0,   0,   0,   0, 250,  44,  44,  44,
    251, 252, 251, 251, 251, 251, 251, 253, 251, 251, 251, 251, 251, 251, 251, 251,
    251, 251, 251, 251, 251, 254,  44, 255, 256,   0, 257, 258, 259, 260, 260, 260,
    260, 261, 262, 263, 263, 263, 263, 264, 265, 266, 267, 268, 142, 142, 142, 142,
    269,   0, 266, 270,   0,   0, 271, 263, 142, 269,   0,   0,   0,   0, 142, 272,
      0,   0,   0,   0,   0, 263, 263, 273, 263, 263, 263, 263, 263, 274,   0,   0,
    251, 251, 251, 254,   0,   0,   0,   0, 251, 251, 251, 251, 251, 254,  44,  44,
    275, 275, 275, 275, 275, 275, 275, 275, 276, 275, 275, 275, 277, 278, 278, 278,
    279, 279, 279, 279, 279, 279, 279, 279, 279, 279, 280,  44,  14,  14,  14,  14,
     14,  14, 281, 281, 281, 281, 281, 282,   0,   0, 283,   4,   4,   4,   4,   4,
    284,   4, 285, 286,  44,  44,  44, 287, 288, 288, 289, 290, 291, 291, 291, 292,
    293, 293, 293, 293, 294, 295,  47, 296, 297, 297, 298, 299, 299, 300, 142, 301,
    302, 302, 302, 302, 303, 304, 138, 305, 306, 306, 306, 307, 308, 309, 138, 138,
    310, 310, 310, 310, 311, 312, 313, 314, 315, 316, 249,   4,   4, 317, 318, 152,
    152, 152, 152, 152, 313, 313, 319, 320, 142, 142, 321, 142, 322, 142, 142, 323,
     44,  44,  44,  44,  44,  44,  44,  44, 251, 251, 251, 251, 251, 251, 324, 251,
    251, 251, 251, 251, 251, 325,  44,  44, 326, 327,  21, 328, 329,  27,  27,  27,
     27,  27,  27,  27, 330,  46,  27,  27,  27,  27,  27,  27,  27,  27,  27,  27,
     27,  27,  27, 331,  44,  27,  27,  27,  27, 332,  27,  27, 333,  44,  44, 334,
      8, 290, 335,   0,   0, 336, 337, 338,  27,  27,  27,  27,  27,  27,  27, 339,
    340,   0,   1,   2,   1,   2, 341, 262, 263, 342, 142, 269, 343, 344, 345, 346,
    347, 348, 349, 350, 351, 351,  44,  44, 348, 348, 348, 348, 348, 348, 348, 352,
    353,   0,   0, 354,  11,  11,  11,  11, 355, 255, 356,  44,  44,   0,   0, 357,
    358, 359, 360, 360, 360, 361, 362, 255, 363, 363, 364, 365, 366, 367, 367, 368,
    369, 370, 371, 371, 372, 373,  44,  44, 374, 374, 374, 374, 374, 375, 375, 375,
    376, 377, 378,  44,  44,  44,  44,  44, 379, 379, 380, 381, 381, 381, 382,  44,
    383, 383, 383, 383, 383, 383, 383, 383, 383, 383, 383, 384, 383, 385, 386,  44,
    387, 388, 388, 389, 390, 391, 392, 392, 393, 394, 395,  44,  44,  44, 396, 397,
    398, 399, 400, 401,  44,  44,  44,  44, 402, 402, 403, 404, 403, 405, 403, 403,
    406, 407, 408, 409, 410, 411, 412, 412, 413, 413,  44,  44, 414, 414, 415, 416,
    417, 417, 417, 418, 419, 420, 421, 422, 423, 424, 425,  44,  44,  44,  44,  44,
    426, 426, 426, 426, 427,  44,  44,  44, 428, 428, 428, 429, 428, 428, 428, 430,
     44,  44,  44,  44,  44,  44,  27, 431, 432, 432, 432, 432, 433, 434, 432, 435,
    436, 436, 436, 436, 437, 438, 439, 440, 441, 441, 441, 442, 443, 444, 444, 445,
    446, 446, 446, 446, 447, 446, 448, 449, 450, 451, 450, 452,  44,  44,  44,  44,
    453, 454, 455, 456, 456, 456, 457, 458, 459, 460, 461, 462, 463, 464, 465, 466,
    467, 467, 467, 467, 468, 469,  44,  44, 470, 470, 470, 471, 470, 472,  44,  44,
    473, 473, 473, 473, 474, 475,  44,  44, 476, 476, 476, 477, 478,  44,  44,  44,
    479, 480, 481, 479,  44,  44,  44,  44,  44,  44, 482, 482, 482, 482, 482, 483,
     44,  44,  44,  44, 484, 484, 484, 485, 486, 486, 486, 486, 486, 486, 486, 486,
    486, 487,  44,  44,  44,  44,  44,  44, 486, 486, 486, 486, 486, 486, 488, 489,
    486, 486, 486, 486, 490,  44,  44,  44, 491, 491, 491, 491, 491, 491, 491, 491,
    491, 491, 492,  44,  44,  44,  44,  44, 493, 493, 493, 493, 493, 493, 493, 493,
    493, 493, 493, 493, 494,  44,  44,  44, 281, 281, 281, 281, 281, 281, 281, 281,
    281, 281, 281, 495, 496, 497, 498,  44,  44,  44,  44,  44,  44, 499, 500, 501,
    502, 502, 502, 502, 503, 504, 505, 506, 502,  44,  44,  44,  44,  44,  44,  44,
    507, 507, 507, 507, 508, 507, 507, 509, 510, 507,  44,  44,  44,  44,  44,  44,
    511,  44,  44,  44,  44,  44,  44,  44, 512, 512, 512, 512, 512, 512, 513, 514,
    515, 516, 271,  44,  44,  44,  44,  44,   0,   0,   0,   0,   0,   0,   0, 517,
      0,   0, 518,   0,   0,   0, 519, 520, 521,   0, 522,   0,   0,   0, 523,  44,
     11,  11,  11,  11, 524,  44,  44,  44,   0,   0,   0,   0,   0, 233,   0, 239,
      0,   0,   0,   0,   0, 223,   0,   0,   0, 525, 526, 527, 528,   0,   0,   0,
    529, 530,   0, 531, 532, 533,   0,   0,   0,   0, 236,   0,   0,   0,   0,   0,
      0,   0,   0,   0, 534,   0,   0,   0, 535, 535, 535, 535, 535, 535, 535, 535,
    536, 537, 538,  44,  44,  44,  44,  44, 539, 539, 539, 539, 539, 539, 539, 539,
    539, 539, 539, 539, 540, 541,  44,  44, 542,  27, 543, 544, 545, 546, 547, 548,
    549, 550, 551, 550,  44,  44,  44, 330,   0,   0, 255,   0,   0,   0,   0,   0,
      0, 271, 225, 340, 340, 340,   0, 517, 552,   0, 225,   0,   0,   0, 255,   0,
      0, 232,  44,  44,  44,  44, 553,   0, 554,   0,   0, 232, 523, 239,  44,  44,
      0,   0,   0,   0,   0,   0,   0, 555,   0,   0, 528,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0, 556, 552, 271,   0,   0,   0,   0,   0,   0,   0, 271,
      0,   0,   0,   0,   0, 557,  44,  44, 255,   0,   0,   0, 558, 290,   0,   0,
    558,   0, 559,  44,  44,  44,  44,  44,  44, 523,  44,  44,  44,  44,  44,  44,
    557,  44,  44,  44, 556,  44,  44,  44, 251, 251, 251, 251, 251, 560,  44,  44,
    251, 251, 251, 561, 251, 251, 251, 251, 251, 324, 251, 251, 251, 251, 251, 251,
    251, 251, 562,  44,  44,  44,  44,  44, 251, 324,  44,  44,  44,  44,  44,  44,
    563,  44,   0,   0,   0,   0,   0,   0,   8,   8,   8,   8,   8,   8,   8,   8,
      8,   8,   8,   8,   8,   8,   8,  44,
};

static RE_UINT16 re_script_stage_4[] = {
      0,   0,   0,   0,   1,   2,   2,   2,   2,   2,   3,   0,   0,   0,   4,   0,
      2,   2,   2,   2,   2,   3,   2,   2,   2,   2,   5,   0,   2,   5,   6,   0,
      7,   7,   7,   7,   8,   9,  10,  11,  12,  13,  14,  15,   8,   8,   8,   8,
     16,   8,   8,   8,  17,  18,  18,  18,  19,  19,  19,  19,  19,  20,  19,  19,
     21,  22,  22,  22,  22,  22,  22,  22,  22,  23,  21,  22,  22,  22,  24,  21,
     25,  26,  26,  26,  26,  26,  26,  26,  26,  26,  12,  12,  26,  26,  27,  12,
     26,  28,  12,  12,  29,  30,  29,  31,  29,  29,  32,  33,  29,  29,  29,  29,
     31,  29,  34,   7,   7,  35,  29,  29,  36,  29,  29,  29,  29,  29,  29,  30,
     37,  37,  37,  38,  37,  37,  37,  37,  37,  37,  39,  40,  41,  41,  41,  41,
     42,  12,  12,  12,  43,  43,  43,  43,  43,  43,  44,  12,  45,  45,  45,  45,
     45,  45,  45,  46,  45,  45,  45,  47,  48,  48,  48,  48,  48,  48,  48,  49,
     12,  12,  12,  12,  29,  50,  12,  12,  51,  29,  29,  29,  52,  52,  52,  52,
     53,  52,  52,  52,  52,  54,  52,  52,  55,  56,  55,  57,  57,  55,  55,  55,
     55,  55,  58,  55,  59,  60,  61,  55,  55,  57,  57,  62,  12,  63,  12,  64,
     55,  60,  55,  55,  55,  55,  55,  12,  65,  65,  66,  67,  68,  69,  69,  69,
     69,  69,  70,  69,  70,  71,  72,  70,  66,  67,  68,  72,  73,  12,  65,  74,
     12,  75,  69,  69,  69,  72,  12,  12,  76,  76,  77,  78,  78,  77,  77,  77,
     77,  77,  79,  77,  79,  76,  80,  77,  77,  78,  78,  80,  81,  12,  12,  12,
     77,  82,  77,  77,  80,  12,  83,  12,  84,  84,  85,  86,  86,  85,  85,  85,
     85,  85,  87,  85,  87,  84,  88,  85,  85,  86,  86,  88,  12,  89,  12,  90,
     85,  89,  85,  85,  85,  85,  12,  12,  91,  92,  93,  91,  94,  95,  96,  94,
     97,  98,  93,  91,  99,  99,  95,  91,  93,  91,  94,  95,  98,  97,  12,  12,
     12,  91,  99,  99,  99,  99,  93,  12, 100, 101, 100, 102, 102, 100, 100, 100,
    100, 100, 102, 100, 100, 100, 103, 101, 100, 102, 102, 103,  12, 104, 105,  12,
    100, 106, 100, 100,  12,  12, 100, 100, 107, 107, 108, 109, 109, 108, 108, 108,
    108, 108, 109, 108, 108, 107, 110, 108, 108, 109, 109, 110,  12, 111,  12, 112,
    108, 113, 108, 108, 111,  12,  12,  12, 114, 114, 115, 116, 116, 115, 115, 115,
    115, 115, 115, 115, 115, 115, 117, 114, 115, 116, 116, 117,  12, 118,  12, 118,
    115, 119, 115, 115, 115, 120, 114, 115, 121, 122, 123, 123, 123, 124, 121, 123,
    123, 123, 123, 123, 125, 123, 123, 126, 123, 124, 127, 128, 123, 129, 123, 123,
     12, 121, 123, 123, 121, 130,  12,  12, 131, 132, 132, 132, 132, 132, 132, 132,
    132, 132, 133, 134, 132, 132, 132,  12, 135, 136, 137, 138,  12, 139, 140, 139,
    140, 141, 142, 140, 139, 139, 143, 144, 139, 137, 139, 144, 139, 139, 144, 139,
    145, 145, 145, 145, 145, 145, 146, 145, 145, 145, 145, 147, 146, 145, 145, 145,
    145, 145, 145, 148, 145, 149, 150,  12, 151, 151, 151, 151, 152, 152, 152, 152,
    152, 153,  12, 154, 152, 152, 155, 152, 156, 156, 156, 156, 157, 157, 157, 157,
    157, 157, 158, 159, 157, 160, 158, 159, 158, 159, 157, 160, 158, 159, 157, 157,
    157, 160, 157, 157, 157, 157, 160, 161, 157, 157, 157, 162, 157, 157, 159,  12,
    163, 163, 163, 163, 163, 164, 163, 164, 165, 165, 165, 165, 166, 166, 166, 166,
    166, 166, 166, 167, 168, 168, 168, 168, 168, 168, 169, 170, 168, 168, 171,  12,
    172, 172, 172, 173, 172, 174,  12,  12, 175, 175, 175, 175, 175, 176,  12,  12,
    177, 177, 177, 177, 177,  12,  12,  12, 178, 178, 178, 179, 179,  12,  12,  12,
    180, 180, 180, 180, 180, 180, 180, 181, 180, 180, 181,  12, 182, 183, 184, 185,
    184, 184, 186,  12, 184, 184, 184, 184, 184, 184,  12,  12, 184, 184, 185,  12,
    165, 187,  12,  12, 188, 188, 188, 188, 188, 188, 188, 189, 188, 188, 188,  12,
    190, 188, 188, 188, 191, 191, 191, 191, 191, 191, 191, 192, 191, 193,  12,  12,
    194, 194, 194, 194, 194, 194, 194,  12, 194, 194, 195,  12, 194, 194, 196, 197,
    198, 198, 198, 198, 198, 198, 198, 199, 200, 200, 200, 200, 200, 200, 200, 201,
    200, 200, 200, 202, 200, 200, 203,  12, 200, 200, 200, 203,   7,   7,   7, 204,
    205, 205, 205, 205, 205, 205, 205,  12, 205, 205, 205, 206, 207, 207, 207, 207,
    208, 208, 208, 208, 208,  12,  12, 208, 209, 209, 209, 209, 209, 209, 210, 209,
    209, 209, 211, 212, 213, 213, 213, 213, 207, 207,  12,  12, 214,   7,   7,   7,
    215,   7, 216, 217,   0, 218, 219,  12,   2, 220, 221,   2,   2,   2,   2, 222,
    223, 220, 224,   2,   2,   2, 225,   2,   2,   2,   2, 226,   7, 219,  12,   7,
      8, 227,   8, 227,   8,   8, 228, 228,   8,   8,   8, 227,   8,  15,   8,   8,
      8,  10,   8, 229,  10,  15,   8,  14,   0,   0,   0, 230,   0, 231,   0,   0,
    232,   0,   0, 233,   0,   0,   0, 234,   2,   2,   2, 235, 236,  12,  12,  12,
      0, 237, 238,   0,   4,   0,   0,   0,   0,   0,   0,   4,   2,   2,   5,  12,
      0,   0, 234,  12,   0, 234,  12,  12, 239, 239, 239, 239,   0, 240,   0,   0,
      0, 241,   0,   0,   0,   0, 241, 242,   0,   0, 231,   0, 241,  12,  12,  12,
     12,  12,  12,   0, 243, 243, 243, 243, 243, 243, 243, 244,  18,  18,  18,  18,
     18,  12, 245,  18, 246, 246, 246, 246, 246, 246,  12, 247, 248,  12,  12, 247,
    157, 160,  12,  12, 157, 160, 157, 160, 234,  12,  12,  12, 249, 249, 249, 249,
    249, 249, 250, 249, 249,  12,  12,  12, 249, 251,  12,  12,   0,   0,   0,  12,
      0, 252,   0,   0, 253, 249, 254, 255,   0,   0, 249,   0, 256, 257, 257, 257,
    257, 257, 257, 257, 257, 258, 259, 260, 261, 262, 262, 262, 262, 262, 262, 262,
    262, 262, 263, 261,  12, 264, 265, 265, 265, 265, 265, 265, 265, 265, 265, 266,
    267, 156, 156, 156, 156, 156, 156, 268, 265, 265, 269,  12,   0,  12,  12,  12,
    156, 156, 156, 270, 262, 262, 262, 271, 262, 262,   0,   0, 272, 272, 272, 272,
    272, 272, 272, 273, 272, 274,  12,  12, 275, 275, 275, 275, 276, 276, 276, 276,
    276, 276, 276,  12, 277, 277, 277, 277, 277, 277,  12,  12, 238,   2,   2,   2,
      2,   2, 233,   2,   2,   2,   2, 278,   2,   2,  12,  12,  12, 279,   2,   2,
    280, 280, 280, 280, 280, 280, 280,  12,   0,   0, 241,  12, 281, 281, 281, 281,
    281, 281,  12,  12, 282, 282, 282, 282, 282, 283,  12, 284, 282, 282, 285,  12,
     52,  52,  52, 286, 287, 287, 287, 287, 287, 287, 287, 288, 289, 289, 289, 289,
    289,  12,  12, 290, 156, 156, 156, 291, 292, 292, 292, 292, 292, 292, 292, 293,
    292, 292, 294, 295, 151, 151, 151, 296, 297, 297, 297, 297, 297, 298,  12,  12,
    297, 297, 297, 299, 297, 297, 299, 297, 300, 300, 300, 300, 301,  12,  12,  12,
     12,  12, 302, 300, 303, 303, 303, 303, 303, 304,  12,  12, 161, 160, 161, 160,
    161, 160,  12,  12,   2,   2,   3,   2,   2, 305,  12,  12, 303, 303, 303, 306,
    303, 303, 306,  12, 156,  12,  12,  12, 156, 268, 307, 156, 156, 156, 156,  12,
    249, 249, 249, 251, 249, 249, 251,  12,   2, 308,  12,  12, 309,  22,  12,  25,
     26,  27,  26, 310, 311, 312,  26,  26, 313,  12,  12,  12,  29,  29,  29, 314,
    315,  29,  29,  29,  29,  29,  12,  12,  29,  29,  29, 313,   7,   7,   7, 316,
    234,   0,   0,   0,   0, 234,   0,  12,  29, 317,  29,  29,  29,  29,  29, 318,
    242,   0,   0,   0,   0, 319, 262, 262, 262, 262, 262, 320, 321, 156, 321, 156,
    321, 156, 321, 291,   0, 234,   0, 234,  12,  12, 242, 241, 322, 322, 322, 323,
    322, 322, 322, 322, 322, 324, 322, 322, 322, 322, 324, 325, 322, 322, 322, 326,
    322, 322, 324,  12, 234, 134,   0,   0,   0, 134,   0,   0,   8,   8,   8, 327,
    327,  12,  12,  12,   0,   0,   0, 328, 329, 329, 329, 329, 329, 329, 329, 330,
    331, 331, 331, 331, 332,  12,  12,  12, 216,   0,   0,   0, 333, 333, 333, 333,
    333,  12,  12,  12, 334, 334, 334, 334, 334, 334, 335,  12, 336, 336, 336, 336,
    336, 336, 337,  12, 338, 338, 338, 338, 338, 338, 338, 339, 340, 340, 340, 340,
    340,  12, 340, 340, 340, 341,  12,  12, 342, 342, 342, 342, 343, 343, 343, 343,
    344, 344, 344, 344, 344, 344, 344, 345, 344, 344, 345,  12, 346, 346, 346, 346,
    346, 346,  12,  12, 347, 347, 347, 347, 347,  12,  12, 348, 349, 349, 349, 349,
    349, 350,  12,  12, 349, 351,  12,  12, 349, 349,  12,  12, 352, 353, 354, 352,
    352, 352, 352, 352, 352, 355, 356, 357, 358, 358, 358, 358, 358, 359, 358, 358,
    360, 360, 360, 360, 361, 361, 361, 361, 361, 361, 361, 362,  12, 363, 361, 361,
    364, 364, 364, 364, 365, 366, 367, 364, 368, 368, 368, 368, 368, 368, 368, 369,
    370, 370, 370, 370, 370, 370, 371, 372, 373, 373, 373, 373, 374, 374, 374, 374,
    374, 374,  12, 374, 375, 374, 374, 374, 376, 377,  12, 376, 376, 378, 378, 376,
    376, 376, 376, 376, 376,  12, 379, 380, 376, 376,  12,  12, 376, 376, 381,  12,
    382, 382, 382, 382, 383, 383, 383, 383, 384, 384, 384, 384, 384, 385, 386, 384,
    384, 385,  12,  12, 387, 387, 387, 387, 387, 388, 389, 387, 390, 390, 390, 390,
    390, 391, 390, 390, 392, 392, 392, 392, 393,  12, 392, 392, 394, 394, 394, 394,
    395,  12, 396, 397,  12,  12, 396, 394, 398, 398, 398, 398, 398, 398, 399,  12,
    400, 400, 400, 400, 401,  12,  12,  12, 401,  12, 402, 400,  29,  29,  29, 403,
    404, 404, 404, 404, 404, 404, 404, 405, 406, 404, 404, 404,  12,  12,  12, 407,
    408, 408, 408, 408, 409,  12,  12,  12, 410, 410, 410, 410, 410, 410, 411,  12,
    410, 410, 412,  12, 413, 413, 413, 413, 413, 414, 413, 413, 413,  12,  12,  12,
    415, 415, 415, 415, 415, 416,  12,  12, 417, 417, 417, 417, 417, 417, 417, 418,
    122, 123, 123, 123, 123, 130,  12,  12, 419, 419, 419, 419, 420, 419, 419, 419,
    419, 419, 419, 421, 422, 423, 424, 425, 422, 422, 422, 425, 422, 422, 426,  12,
    427, 427, 427, 427, 427, 427, 428,  12, 427, 427, 429,  12, 430, 431, 430, 432,
    432, 430, 430, 430, 430, 430, 433, 430, 433, 431, 434, 430, 430, 432, 432, 434,
    435, 436,  12, 431, 430, 437, 430, 435, 430, 435,  12,  12, 438, 438, 438, 438,
    438, 438,  12,  12, 438, 438, 439,  12, 440, 440, 440, 440, 440, 441, 440, 440,
    440, 440, 440, 441, 442, 442, 442, 442, 442, 443,  12,  12, 442, 442, 444,  12,
    445, 445, 445, 445, 445, 445,  12,  12, 445, 445, 446,  12, 447, 447, 447, 447,
    447, 447, 448, 449, 447, 447, 447,  12, 450, 450, 450, 450, 451,  12,  12, 452,
    453, 453, 453, 453, 453, 453, 454,  12, 455, 455, 455, 455, 455, 455, 456,  12,
    455, 455, 455, 457, 455, 458,  12,  12, 455,  12,  12,  12, 459, 459, 459, 459,
    459, 459, 459, 460, 461, 461, 461, 461, 461, 462,  12,  12, 277, 277, 463,  12,
    464, 464, 464, 464, 464, 464, 464, 465, 464, 464, 466, 467, 468, 468, 468, 468,
    468, 468, 468, 469, 468, 469,  12,  12, 470, 470, 470, 470, 470, 471,  12,  12,
    470, 470, 472, 470, 472, 470, 470, 470, 470, 470,  12, 473, 474, 474, 474, 474,
    474, 475,  12,  12, 474, 474, 474, 476,  12,  12,  12, 477, 478,  12,  12,  12,
    479, 479, 479, 479, 479, 479, 480,  12, 479, 479, 479, 481, 479, 479, 481,  12,
    479, 479, 482, 479,   0, 241,  12,  12,   0, 234, 242,   0,   0, 483, 230,   0,
      0,   0, 483,   7, 214, 484,   7,   0,   0,   0, 485, 230,   0,   0, 486,  12,
      8, 227,  12,  12,   0,   0,   0, 231, 487, 488, 242, 231,   0,   0, 489, 242,
      0, 242,   0,   0,   0, 489, 234, 242,   0, 231,   0, 231,   0,   0, 489, 234,
      0, 490, 240,   0, 231,   0,   0,   0,   0,   0,   0, 240, 491, 491, 491, 491,
    491, 491, 491,  12,  12,  12, 492, 491, 493, 491, 491, 491, 494, 494, 494, 494,
    494, 495, 494, 494, 494, 496,  12,  12,  29, 497,  29,  29, 498, 499, 497,  29,
    403,  29, 500,  12, 501,  51, 500, 497, 498, 499, 500, 500, 498, 499, 403,  29,
    403,  29, 497, 502,  29,  29, 503,  29,  29,  29,  29,  12, 497, 497, 503,  29,
      0,   0,   0, 486,  12, 240,   0,   0, 504,  12,  12,  12,   0,   0, 489,   0,
    486,  12,  12,  12,   0, 486,  12,  12,   0,   0,  12,  12,   0,   0,   0, 241,
    249, 505,  12,  12, 249, 506,  12,  12, 251,  12,  12,  12, 507,  12,  12,  12,
};

static RE_UINT8 re_script_stage_5[] = {
      1,   1,   1,   1,   1,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   1,
      1,   1,   2,   1,   2,   1,   1,   1,   1,   1,  35,  35,  41,  41,  41,  41,
      3,   3,   3,   3,   1,   3,   3,   3,   0,   0,   3,   3,   3,   3,   1,   3,
      0,   0,   0,   0,   3,   1,   3,   1,   3,   3,   3,   0,   3,   0,   3,   3,
      3,   3,   0,   3,   3,   3,  55,  55,  55,  55,  55,  55,   4,   4,   4,   4,
      4,  41,  41,   4,   0,   5,   5,   5,   5,   5,   5,   5,   5,   5,   5,   0,
      0,   1,   5,   0,   0,   6,   6,   6,   6,   6,   6,   6,   6,   6,   6,   0,
      6,   0,   0,   0,   7,   7,   7,   7,   7,   1,   7,   7,   1,   7,   7,   7,
      7,   7,   7,   1,   1,   0,   7,   1,   7,   7,   7,  41,  41,  41,   7,   7,
     41,   7,   7,   7,   8,   8,   8,   8,   8,   8,   0,   8,   8,   8,   8,   0,
      0,   8,   8,   8,   9,   9,   9,   9,   9,   9,   0,   0,  66,  66,  66,  66,
     66,  66,  66,   0,  82,  82,  82,  82,  82,  82,   0,   0,  82,  82,  82,   0,
     95,  95,  95,  95,   0,   0,  95,   0,   7,   0,   0,   0,   0,   0,   0,   7,
     10,  10,  10,  10,  10,  41,  41,  10,   1,   1,  10,  10,  11,  11,  11,  11,
      0,  11,  11,  11,  11,   0,   0,  11,  11,   0,  11,  11,  11,   0,  11,   0,
      0,   0,  11,  11,  11,  11,   0,   0,  11,  11,  11,   0,   0,   0,   0,  11,
     11,  11,   0,  11,   0,  12,  12,  12,  12,  12,  12,   0,   0,   0,   0,  12,
     12,   0,   0,  12,  12,  12,  12,  12,  12,   0,  12,  12,   0,  12,  12,   0,
     12,  12,   0,   0,   0,  12,   0,   0,  12,   0,  12,   0,   0,   0,  12,  12,
      0,  13,  13,  13,  13,  13,  13,  13,  13,  13,   0,  13,  13,   0,  13,  13,
     13,  13,   0,   0,  13,   0,   0,   0,   0,   0,  13,  13,   0,  13,   0,   0,
      0,  14,  14,  14,  14,  14,  14,  14,  14,   0,   0,  14,  14,   0,  14,  14,
     14,  14,   0,   0,   0,   0,  14,  14,  14,  14,   0,  14,   0,   0,  15,  15,
      0,  15,  15,  15,  15,  15,  15,   0,  15,   0,  15,  15,  15,  15,   0,   0,
      0,  15,  15,   0,   0,   0,   0,  15,  15,   0,   0,   0,  15,  15,  15,  15,
     16,  16,  16,  16,   0,  16,  16,  16,  16,   0,  16,  16,  16,  16,   0,   0,
      0,  16,  16,   0,  16,  16,  16,   0,   0,   0,  16,  16,   0,  17,  17,  17,
     17,  17,  17,  17,  17,   0,  17,  17,  17,  17,   0,   0,   0,  17,  17,   0,
      0,   0,  17,   0,   0,   0,  17,  17,   0,  18,  18,  18,  18,  18,  18,  18,
     18,   0,  18,  18,  18,  18,  18,   0,   0,   0,   0,  18,   0,   0,  18,  18,
     18,  18,   0,   0,   0,   0,  19,  19,   0,  19,  19,  19,  19,  19,  19,  19,
     19,  19,  19,   0,  19,  19,   0,  19,   0,  19,   0,   0,   0,   0,  19,   0,
      0,   0,   0,  19,  19,   0,  19,   0,  19,   0,   0,   0,   0,  20,  20,  20,
     20,  20,  20,  20,  20,  20,  20,   0,   0,   0,   0,   1,   0,  21,  21,   0,
     21,   0,   0,  21,  21,   0,  21,   0,   0,  21,   0,   0,  21,  21,  21,  21,
      0,  21,  21,  21,   0,  21,   0,  21,   0,   0,  21,  21,  21,  21,   0,  21,
     21,  21,   0,   0,  22,  22,  22,  22,   0,  22,  22,  22,  22,   0,   0,   0,
     22,   0,  22,  22,  22,   1,   1,   1,   1,  22,  22,   0,  23,  23,  23,  23,
     24,  24,  24,  24,  24,  24,   0,  24,   0,  24,   0,   0,  24,  24,  24,   1,
     25,  25,  25,  25,  26,  26,  26,  26,  26,   0,  26,  26,  26,  26,   0,   0,
     26,  26,  26,   0,   0,  26,  26,  26,  26,   0,   0,   0,  27,  27,  27,  27,
     27,  27,   0,   0,  28,  28,  28,  28,  29,  29,  29,  29,  29,   0,   0,   0,
     30,  30,  30,  30,  30,  30,  30,   1,   1,   1,  30,  30,  30,   0,   0,   0,
     42,  42,  42,  42,  42,   0,  42,  42,  42,   0,   0,   0,  43,  43,  43,  43,
     43,   1,   1,   0,  44,  44,  44,  44,  45,  45,  45,  45,  45,   0,  45,  45,
     31,  31,  31,  31,  31,  31,   0,   0,  32,  32,   1,   1,  32,   1,  32,  32,
     32,  32,  32,  32,  32,  32,  32,   0,  32,  32,   0,   0,  28,  28,   0,   0,
     46,  46,  46,  46,  46,  46,  46,   0,  46,   0,   0,   0,  47,  47,  47,  47,
     47,  47,   0,   0,  47,   0,   0,   0,  56,  56,  56,  56,  56,  56,   0,   0,
     56,  56,  56,   0,   0,   0,  56,  56,  54,  54,  54,  54,   0,   0,  54,  54,
     78,  78,  78,  78,  78,  78,  78,   0,  78,   0,   0,  78,  78,  78,   0,   0,
     41,  41,  41,   0,  62,  62,  62,  62,  62,   0,   0,   0,  67,  67,  67,  67,
     93,  93,  93,  93,  68,  68,  68,  68,   0,   0,   0,  68,  68,  68,   0,   0,
      0,  68,  68,  68,  69,  69,  69,  69,  41,  41,  41,   1,  41,   1,  41,  41,
     41,   1,   1,   1,   1,  41,   1,   1,  41,   1,   1,   0,  41,  41,   0,   0,
      2,   2,   3,   3,   3,   3,   3,   4,   2,   3,   3,   3,   3,   3,   2,   2,
      3,   3,   3,   2,   4,   2,   2,   2,   2,   2,   2,   3,   3,   3,   0,   0,
      0,   3,   0,   3,   0,   3,   3,   3,  41,  41,   1,   1,   1,   0,   1,   1,
      1,   2,   0,   0,   1,   1,   1,   2,   1,   1,   1,   0,   2,   0,   0,   0,
     41,   0,   0,   0,   1,   1,   3,   1,   1,   1,   2,   2,  53,  53,  53,  53,
      0,   0,   1,   1,   1,   1,   0,   0,   0,   1,   1,   1,  57,  57,  57,  57,
     57,  57,  57,   0,   0,  55,  55,  55,  58,  58,  58,  58,   0,   0,   0,  58,
     58,   0,   0,   0,  36,  36,  36,  36,  36,  36,   0,  36,  36,  36,   0,   0,
      1,  36,   1,  36,   1,  36,  36,  36,  36,  36,  41,  41,  41,  41,  25,  25,
      0,  33,  33,  33,  33,  33,  33,  33,  33,  33,  33,   0,   0,  41,  41,   1,
      1,  33,  33,  33,   1,  34,  34,  34,  34,  34,  34,  34,  34,  34,  34,   1,
      0,  35,  35,  35,  35,  35,  35,  35,  35,  35,   0,   0,   0,  25,  25,  25,
     25,  25,  25,   0,  35,  35,  35,   0,  25,  25,  25,   1,  34,  34,  34,   0,
     37,  37,  37,  37,  37,   0,   0,   0,  37,  37,  37,   0,  83,  83,  83,  83,
     70,  70,  70,  70,  84,  84,  84,  84,   2,   2,   0,   0,   0,   0,   0,   2,
     59,  59,  59,  59,  65,  65,  65,  65,  71,  71,  71,  71,  71,   0,   0,   0,
      0,   0,  71,  71,  71,  71,   0,   0,  10,  10,   0,   0,  72,  72,  72,  72,
     72,  72,   1,  72,  73,  73,  73,  73,   0,   0,   0,  73,  25,   0,   0,   0,
     85,  85,  85,  85,  85,  85,   0,   1,  85,  85,   0,   0,   0,   0,  85,  85,
     23,  23,  23,   0,  77,  77,  77,  77,  77,  77,  77,   0,  77,  77,   0,   0,
     79,  79,  79,  79,  79,  79,  79,   0,   0,   0,   0,  79,  86,  86,  86,  86,
     86,  86,  86,   0,   2,   3,   0,   0,  86,  86,   0,   0,   0,   0,   0,  25,
      2,   2,   2,   0,   0,   0,   0,   5,   6,   0,   6,   0,   6,   6,   0,   6,
      6,   0,   6,   6,   7,   7,   0,   0,   7,   7,   1,   1,   0,   0,   7,   7,
     41,  41,   4,   4,   7,   0,   7,   7,   7,   0,   0,   1,   1,   1,  34,  34,
     34,  34,   1,   1,   0,   0,  25,  25,  48,  48,  48,  48,   0,  48,  48,  48,
     48,  48,  48,   0,  48,  48,   0,  48,  48,  48,   0,   0,   3,   0,   0,   0,
      1,  41,   0,   0,  74,  74,  74,  74,  74,   0,   0,   0,  75,  75,  75,  75,
     75,   0,   0,   0,  38,  38,  38,  38,  39,  39,  39,  39,  39,  39,  39,   0,
    120, 120, 120, 120, 120, 120, 120,   0,  49,  49,  49,  49,  49,  49,   0,  49,
     60,  60,  60,  60,  60,  60,   0,   0,  40,  40,  40,  40,  50,  50,  50,  50,
     51,  51,  51,  51,  51,  51,   0,   0, 106, 106, 106, 106, 103, 103, 103, 103,
      0,   0,   0, 103, 110, 110, 110, 110, 110, 110, 110,   0, 110, 110,   0,   0,
     52,  52,  52,  52,  52,  52,   0,   0,  52,   0,  52,  52,  52,  52,   0,  52,
     52,   0,   0,   0,  52,   0,   0,  52,  87,  87,  87,  87,  87,  87,   0,  87,
    118, 118, 118, 118, 117, 117, 117, 117, 117, 117, 117,   0,   0,   0,   0, 117,
    128, 128, 128, 128, 128, 128, 128,   0, 128, 128,   0,   0,   0,   0,   0, 128,
     64,  64,  64,  64,   0,   0,   0,  64,  76,  76,  76,  76,  76,  76,   0,   0,
      0,   0,   0,  76,  98,  98,  98,  98,  97,  97,  97,  97,   0,   0,  97,  97,
     61,  61,  61,  61,   0,  61,  61,   0,   0,  61,  61,  61,  61,  61,  61,   0,
      0,   0,   0,  61,  61,   0,   0,   0,  88,  88,  88,  88, 116, 116, 116, 116,
    112, 112, 112, 112, 112, 112, 112,   0,   0,   0,   0, 112,  80,  80,  80,  80,
     80,  80,   0,   0,   0,  80,  80,  80,  89,  89,  89,  89,  89,  89,   0,   0,
     90,  90,  90,  90,  90,  90,  90,   0, 121, 121, 121, 121, 121, 121,   0,   0,
      0, 121, 121, 121, 121,   0,   0,   0,  91,  91,  91,  91,  91,   0,   0,   0,
    130, 130, 130, 130, 130, 130, 130,   0,   0,   0, 130, 130,   7,   7,   7,   0,
     94,  94,  94,  94,  94,  94,   0,   0,   0,   0,  94,  94,   0,   0,   0,  94,
     92,  92,  92,  92,  92,  92,   0,   0, 101, 101, 101, 101, 101,   0,   0,   0,
    101, 101,   0,   0,  96,  96,  96,  96,  96,   0,  96,  96, 111, 111, 111, 111,
    111, 111, 111,   0, 100, 100, 100, 100, 100, 100,   0,   0, 109, 109, 109, 109,
    109, 109,   0, 109, 109, 109,   0,   0, 129, 129, 129, 129, 129, 129, 129,   0,
    129,   0, 129, 129, 129, 129,   0, 129, 129, 129,   0,   0, 123, 123, 123, 123,
    123, 123, 123,   0, 123, 123,   0,   0, 107, 107, 107, 107,   0, 107, 107, 107,
    107,   0,   0, 107, 107,   0, 107, 107, 107, 107,   0,   0, 107,   0,   0,   0,
      0,   0,   0, 107,   0,   0, 107, 107, 124, 124, 124, 124, 124, 124,   0,   0,
    122, 122, 122, 122, 122, 122,   0,   0, 114, 114, 114, 114, 114,   0,   0,   0,
    114, 114,   0,   0, 102, 102, 102, 102, 102, 102,   0,   0, 126, 126, 126, 126,
    126, 126,   0,   0,   0, 126, 126, 126, 125, 125, 125, 125, 125, 125, 125,   0,
      0,   0,   0, 125, 119, 119, 119, 119, 119,   0,   0,   0,  63,  63,  63,  63,
     63,  63,   0,   0,  63,  63,  63,   0,  63,   0,   0,   0,  81,  81,  81,  81,
     81,  81,  81,   0, 127, 127, 127, 127, 127, 127, 127,   0,  84,   0,   0,   0,
    115, 115, 115, 115, 115, 115, 115,   0, 115, 115,   0,   0,   0,   0, 115, 115,
    104, 104, 104, 104, 104, 104,   0,   0, 108, 108, 108, 108, 108, 108,   0,   0,
    108, 108,   0, 108,   0, 108, 108, 108,  99,  99,  99,  99,  99,   0,   0,   0,
     99,  99,  99,   0,   0,   0,   0,  99,  34,  33,   0,   0, 105, 105, 105, 105,
    105, 105, 105,   0, 105,   0,   0,   0, 105, 105,   0,   0,   1,   1,   1,  41,
      1,  41,  41,  41,   1,   1,  41,  41,   1,   0,   0,   0,   0,   0,   1,   0,
      0,   1,   1,   0,   1,   1,   0,   1,   1,   0,   1,   0, 131, 131, 131, 131,
      0,   0,   0, 131,   0, 131, 131, 131, 113, 113, 113, 113, 113,   0,   0, 113,
    113, 113, 113,   0,   0,   7,   7,   7,   0,   7,   7,   0,   7,   0,   0,   7,
      0,   7,   0,   7,   0,   0,   7,   0,   7,   0,   7,   0,   7,   7,   0,   7,
     33,   1,   1,   0,  36,  36,  36,   0,  36,   0,   0,   0,   0,   1,   0,   0,
};

/* Script: 10928 bytes. */

RE_UINT32 re_get_script(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 11;
    code = ch ^ (f << 11);
    pos = (RE_UINT32)re_script_stage_1[f] << 4;
    f = code >> 7;
    code ^= f << 7;
    pos = (RE_UINT32)re_script_stage_2[pos + f] << 3;
    f = code >> 4;
    code ^= f << 4;
    pos = (RE_UINT32)re_script_stage_3[pos + f] << 2;
    f = code >> 2;
    code ^= f << 2;
    pos = (RE_UINT32)re_script_stage_4[pos + f] << 2;
    value = re_script_stage_5[pos + code];

    return value;
}

/* Word_Break. */

static RE_UINT8 re_word_break_stage_1[] = {
     0,  1,  2,  3,  4,  4,  4,  4,  4,  4,  5,  6,  6,  7,  4,  8,
     9, 10, 11, 12, 13,  4, 14,  4,  4,  4,  4, 15,  4, 16, 17, 18,
     4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,
     4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,
     4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,
     4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,
     4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,
     4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,
     4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,
     4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,
     4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,
     4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,
     4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,
     4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,
    19,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,
     4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,
     4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,
};

static RE_UINT8 re_word_break_stage_2[] = {
      0,   1,   2,   2,   2,   3,   4,   5,   2,   6,   7,   8,   9,  10,  11,  12,
     13,  14,  15,  16,  17,  18,  19,  20,  21,  22,  23,  24,  25,  26,  27,  28,
     29,  30,   2,   2,  31,  32,  33,  34,  35,   2,   2,   2,  36,  37,  38,  39,
     40,  41,  42,  43,  44,  45,  46,  47,  48,  49,   2,  50,   2,   2,  51,  52,
     53,  54,  55,  56,  57,  57,  57,  57,  57,  58,  57,  57,  57,  57,  57,  57,
     57,  57,  57,  57,  57,  57,  57,  57,  59,  60,  61,  62,  63,  57,  57,  57,
     64,  65,  66,  67,  57,  68,  69,  57,  57,  57,  57,  57,  57,  57,  57,  57,
     57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,
     57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,
     57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,
      2,   2,   2,   2,   2,   2,   2,   2,   2,  70,   2,   2,  71,  72,  73,  74,
     75,  76,  77,  78,  79,  80,  81,  82,   2,   2,   2,   2,   2,   2,   2,   2,
      2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,
      2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,
      2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,  83,
     57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,
     57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,
     57,  57,  57,  57,  57,  57,  84,  85,   2,   2,  86,  87,  88,  89,  90,  91,
     92,  93,  94,  95,  57,  96,  97,  98,   2,  99, 100,  57,   2,   2, 101,  57,
    102, 103, 104, 105, 106, 107, 108, 109, 110, 111,  57,  57,  57,  57,  57,  57,
    112, 113, 114, 115, 116, 117, 118,  57,  57, 119,  57, 120, 121, 122, 123,  57,
     57, 124,  57,  57,  57, 125,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,
      2,   2,   2,   2,   2,   2,   2, 126, 127,   2, 128,  57,  57,  57,  57,  57,
     57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,
      2,   2,   2,   2,   2,   2,   2,   2, 129,  57,  57,  57,  57,  57,  57,  57,
     57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,
     57,  57,  57,  57,  57,  57,  57,  57,   2,   2,   2,   2, 130,  57,  57,  57,
     57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,
     57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,
      2,   2,   2,   2, 131, 132, 133, 134,  57,  57,  57,  57,  57,  57, 135, 136,
    137,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,
     57,  57,  57,  57,  57,  57,  57,  57, 138, 139,  57,  57,  57,  57,  57,  57,
     57,  57, 140, 141, 142,  57,  57,  57, 143, 144, 145,   2,   2, 146, 147, 148,
     57,  57,  57,  57, 149, 150,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,
     57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,
      2, 151,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57, 152, 153,  57,  57,
     57,  57, 154, 155,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,
     57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,
    156,  57, 157, 158,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,
     57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,  57,
};

static RE_UINT8 re_word_break_stage_3[] = {
      0,   1,   0,   0,   2,   3,   4,   5,   6,   7,   7,   8,   6,   7,   7,   9,
     10,   0,   0,   0,   0,  11,  12,  13,   7,   7,  14,   7,   7,   7,  14,   7,
      7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,
      7,   7,   7,   7,   7,   7,   7,   7,  15,   7,  16,   0,  17,  18,   0,   0,
     19,  19,  19,  19,  19,  19,  19,  19,  19,  19,  19,  19,  19,  19,  20,  21,
     22,  23,   7,   7,  24,   7,   7,   7,   7,   7,   7,   7,   7,   7,  25,   7,
     26,  27,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,
      7,   7,   7,   7,   7,   7,   6,   7,   7,   7,  14,  28,   6,   7,   7,   7,
      7,  29,  30,  19,  19,  19,  19,  31,  32,   0,  33,  33,  33,  34,  35,   0,
     36,  37,  19,  38,   7,   7,   7,   7,   7,  39,  19,  19,   4,  40,  41,   7,
      7,   7,   7,   7,   7,   7,   7,   7,   7,   7,  42,  43,  44,  45,   4,  46,
      0,  47,  48,   7,   7,   7,  19,  19,  19,  49,   7,   7,   7,   7,   7,   7,
      7,   7,   7,   7,  50,  19,  51,   0,   4,  52,   7,   7,   7,  39,  53,  54,
      7,   7,  50,  55,  56,  57,   0,   0,   7,   7,   7,  58,   0,   0,   0,   0,
      0,   0,   0,   0,   7,   7,  17,   0,   0,   0,   0,   0,  59,  19,  19,  19,
     60,   7,   7,   7,   7,   7,   7,  61,  19,  19,  62,   7,  63,   4,   6,   7,
     64,  65,  66,   7,   7,  67,  68,  69,  70,  71,  72,  73,  63,   4,  74,   0,
     75,  76,  66,   7,   7,  67,  77,  78,  79,  80,  81,  82,  83,   4,  84,   0,
     75,  25,  24,   7,   7,  67,  85,  69,  31,  86,  87,   0,  63,   4,   0,  28,
     75,  65,  66,   7,   7,  67,  85,  69,  70,  80,  88,  73,  63,   4,  28,   0,
     89,  90,  91,  92,  93,  90,   7,  94,  95,  96,  97,   0,  83,   4,   0,   0,
     98,  20,  67,   7,   7,  67,   7,  99, 100,  96, 101,   9,  63,   4,   0,   0,
     75,  20,  67,   7,   7,  67, 102,  69, 100,  96, 101, 103,  63,   4, 104,   0,
     75,  20,  67,   7,   7,   7,   7, 105, 100, 106,  72, 107,  63,   4,   0, 108,
    109,   7,  14, 108,   7,   7,  24, 110,  14, 111, 112,  19,  83,   4, 113,   0,
      0,   0,   0,   0,   0,   0, 114, 115,  72, 116,   4, 117,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0, 114, 118,   0, 119,   4, 117,   0,   0,   0,   0,
     87,   0,   0, 120,   4, 117, 121, 122,   7,   6,   7,   7,   7,  17,  30,  19,
    100, 123,  19,  30,  19,  19,  19, 124, 125,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,  59,  19, 116,   4, 117,  88, 126, 127, 119, 128,   0,
    129,  31,   4, 130,   7,   7,   7,   7,  25, 131,   7,   7,   7,   7,   7, 132,
      7,   7,   7,   7,   7,   7,   7,   7,   7,  91,  14,  91,   7,   7,   7,   7,
      7,  91,   7,   7,   7,   7,  91,  14,  91,   7,  14,   7,   7,   7,   7,   7,
      7,   7,  91,   7,   7,   7,   7,   7,   7,   7,   7, 133,   0,   0,   0,   0,
      7,   7,   0,   0,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7, 134, 134,
      6,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,
      7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,  65,   7,   7,
      6,   7,   7,   9,   7,   7,   7,   7,   7,   7,   7,   7,   7,  90,   7,  87,
      7,  20, 135,   0,   7,   7, 135,   0,   7,   7, 136,   0,   7,  20, 137,   0,
      0,   0,   0,   0,   0,   0, 138,  19,  19,  19, 139, 140,   4, 117,   0,   0,
      0, 141,   4, 117,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   0,
      7,   7,   7,   7,   7, 142,   7,   7,   7,   7,   7,   7,   7,   7, 134,   0,
      7,   7,   7,  14,  19, 139,  19, 139,  83,   4,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   4, 117,   0,   0,   0,   0,
      7,   7, 143, 139,   0,   0,   0,   0,   0,   0, 144, 116,  19,  19,  19,  70,
      4, 117,   4, 117,   0,   0,  19, 116,   0,   0,   0,   0,   0,   0,   0,   0,
    145,   7,   7,   7,   7,   7, 146,  19, 145, 147,   4, 117,   0,  59, 139,   0,
    148,   7,   7,   7,  62, 149,   4,  52,   7,   7,   7,   7,  50,  19, 139,   0,
      7,   7,   7,   7, 146,  19,  19,   0,   4, 150,   4,  52,   7,   7,   7, 134,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 151,  19,  19, 152, 153, 120,
      7,   7,   7,   7,   7,   7,   7,   7,  19,  19,  19,  19,  19,  19, 119, 138,
      7,   7, 134, 134,   7,   7,   7,   7, 134, 134,   7, 154,   7,   7,   7, 134,
      7,   7,   7,   7,   7,   7,  20, 155, 156,  17, 157, 147,   7,  17, 156,  17,
      0, 158,   0, 159, 160, 161,   0, 162, 163,   0, 164,   0, 165, 166,  28, 107,
      0,   0,   7,  17,   0,   0,   0,   0,   0,   0,  19,  19,  19,  19, 167,   0,
    168, 108, 110, 169,  18, 170,   7, 171, 172, 173,   0,   0,   7,   7,   7,   7,
      7,  87,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0, 174,   7,   7,   7,   7,   7,   7,  74,   0,   0,
      7,   7,   7,   7,   7,  14,   7,   7,   7,   7,   7,  14,   7,   7,   7,   7,
      7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,  17, 175, 176,   0,
      7,   7,   7,   7,  25, 131,   7,   7,   7,   7,   7,   7,   7, 107,   0,  72,
      7,   7,  14,   0,  14,  14,  14,  14,  14,  14,  14,  14,  19,  19,  19,  19,
      0,   0,   0,   0,   0, 107,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
    131,   0,   0,   0,   0, 129, 177,  93,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0, 178, 179, 179, 179, 179, 179, 179, 179, 179, 179, 179, 179, 180,
    172,   7,   7,   7,   7, 134,   6,   7,   7,   7,   7,   7,   7,   7,   7,   7,
      7,  14,   0,   0,   7,   7,   7,   9,   0,   0,   0,   0,   0,   0, 179, 179,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 179, 179, 179, 179, 179, 181,
    179, 179, 179, 179, 179, 179, 179, 179, 179, 179, 179,   0,   0,   0,   0,   0,
      7,  17,   0,   0,   0,   0,   0,   0,   0,   0,   7,   7,   7,   7,   7, 134,
      7,  17,   7,   7,   4, 182,   0,   0,   7,   7,   7,   7,   7, 143, 151, 183,
      7,   7,   7,  50,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7, 120,   0,
      0,   0, 107,   7, 108,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,
      7,  66,   7,   7,   7, 134,   7,   0,   0,   0,   0,   0,   0,   0, 107,   7,
    184, 185,   7,   7,  39,   0,   0,   0,   7,   7,   7,   7,   7,   7, 147,   0,
     27,   7,   7,   7,   7,   7, 146,  19, 124,   0,   4, 117,  19,  19,  27, 186,
      4,  52,   7,   7,  50, 119,   7,   7, 143,  19, 139,   0,   7,   7,   7,  17,
     60,   7,   7,   7,   7,   7,  39,  19, 167, 107,   4, 117, 140,   0,   4, 117,
      7,   7,   7,   7,   7,  62, 116,   0, 185, 187,   4, 117,   0,   0,   0, 188,
      0,   0,   0,   0,   0,   0, 127, 189,  81,   0,   0,   0,   7,  39, 190,   0,
    191, 191, 191,   0,  14,  14,   7,   7,   7,   7,   7, 132, 134,   0,   7,   7,
      7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,  39, 192,   4, 117,
      7,   7,   7,   7, 147,   0,   7,   7,  14, 193,   7,   7,   7,   7,   7, 147,
     14,   0, 193, 194,  33, 195, 196, 197, 198,  33,   7,   7,   7,   7,   7,   7,
      7,   7,   7,   7,   7,   7,  74,   0,   0,   0, 193,   7,   7,   7,   7,   7,
      7,   7,   7,   7,   7,   7,   7, 134,   0,   0,   7,   7,   7,   7,   7,   7,
      7,   7, 108,   7,   7,   7,   7,   7,   7,   0,   0,   0,   0,   0,   7, 147,
     19,  19, 199,   0,  19,  19, 200,   0,   0, 201, 202,   0,   0,   0,  20,   7,
      7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7, 203,
    204,   3,   0, 205,   6,   7,   7,   8,   6,   7,   7,   9, 206, 179, 179, 179,
    179, 179, 179, 207,   7,   7,   7,  14, 108, 108, 108, 208,   0,   0,   0, 209,
      7, 102,   7,   7,  14,   7,   7, 210,   7, 134,   7, 134,   0,   0,   0,   0,
      7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   9,
      0,   0,   0,   0,   0,   0,   0,   0,   7,   7,   7,   7,   7,   7,  17,   0,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 140,
      7,   7,   7,  17,   7,   7,   7,   7,   7,   7,  87,   0, 167,   0,   0,   0,
      7,   7,   7,   7,   0,   0,   7,   7,   7,   9,   7,   7,   7,   7,  50, 115,
      7,   7,   7, 134,   7,   7,   7,   7, 147,   7, 169,   0,   0,   0,   0,   0,
      7,   7,   7, 134,   4, 117,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      7,   7,   7,   7,   7,   0,   7,   7,   7,   7,   7,   7, 147,   0,   0,   0,
      7,   7,   7,   7,   7,   7,  14,   0,   7,   7, 134,   0,   7,   0,   0,   0,
    134,  67,   7,   7,   7,   7,  25, 211,   7,   7, 134,   0,   7,   7,  14,   0,
      7,   7,   7,  14,   0,   0,   0,   0,   0,   0,   0,   0,   7,   7, 212,   0,
      7,   7, 134,   0,   7,   7,   7,  74,   0,   0,   0,   0,   0,   0,   0,   0,
      7,   7,   7,   7,   7,   7,   7, 174,   0,   0,   0,   0,   0,   0,   0,   0,
    213, 138, 102,   6,   7,   7, 147,  79,   0,   0,   0,   0,   7,   7,   7,  17,
      7,   7,   7,  17,   0,   0,   0,   0,   7,   6,   7,   7, 214,   0,   0,   0,
      7,   7,   7,   7,   7,   7, 134,   0,   7,   7, 134,   0,   7,   7,   9,   0,
      7,   7,  74,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      7,   7,   7,   7,   7,   7,   7,   7,   7,  87,   0,   0,   0,   0,   0,   0,
      7,   7,   7,   7,   7,   7,   9,   0,   7,   7,   7,   7,   7,   7,   9,   0,
    148,   7,   7,   7,   7,   7,   7,  19, 116,   0,   0,   0,  83,   4,   0,  72,
    148,   7,   7,   7,   7,   7,  19, 215,   0,   0,   7,   7,   7,  87,   4, 117,
    148,   7,   7,   7, 143,  19, 216,   4,   0,   0,   7,   7,   7,   7, 217,   0,
    148,   7,   7,   7,   7,   7,  39,  19, 218, 219,   4, 220,   0,   0,   0,   0,
      7,   7,  24,   7,   7, 146,  19,   0,   0,   0,   0,   0,   0,   0,   0,   0,
     14, 170,   7,  25,   7,  87,   7,   7,   7,   7,   7, 143,  19, 115,   4, 117,
     98,  65,  66,   7,   7,  67,  85,  69,  70,  80,  97, 172, 221, 124, 124,   0,
      7,   7,   7,   7,   7,   7,  19,  19, 222,   0,   4, 117,   0,   0,   0,   0,
      7,   7,   7,   7,   7, 143, 119,  19, 167,   0,   0, 187,   0,   0,   0,   0,
      7,   7,   7,   7,   7,   7,  19,  19, 223,   0,   4, 117,   0,   0,   0,   0,
      7,   7,   7,   7,   7,  39,  19,   0,   4, 117,   0,   0,   0,   0,   0,   0,
      0,   0,   0, 144,  19, 139,   4, 117,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   7,   7,   7,   7,   7,   7,   7,   7,   4, 117,   0, 107,
      0,   0,   0,   0,   0,   0,   0,   0,   7,   7,   7,   7,   7,   7,   7,  87,
      7,   7,   7,  74,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,  14,   0,   0,
      7,   7,   7,   7,   7,   7,   7,   7, 147,   0,   0,   0,   0,   0,   0,   0,
      7,   7,   7,   7,   7,  14,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      7,   7,   7,   7,   7,   7,   7,   7,  14,   0,   0,   0,   0,   0,   0,   0,
      7,   7,   7,   7,   7,   7,   7,  87,   7,   7,   7,  14,   4, 117,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   7,   7,   7, 134, 124,   0,
      7,   7,   7,   7,   7,   7, 116,   0, 147,   0,   4, 117, 193,   7,   7, 172,
      7,   7,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      7,   7,   7,   7,   7,   7,   7,   7,  17,   0,  62,  19,  19,  19,  19, 116,
      0,  72, 148,   7,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
    224,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   7,   9,   7,  17,
      7,  87,   7, 225, 226,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 144, 227, 228, 229,
    230, 139,   0,   0,   0, 231,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0, 219,   0,   0,   0,   0,   0,   0,   0,
      7,   7,   7,   7,   7,   7,   7,   7,   7,   7,  20,   7,   7,   7,   7,   7,
      7,   7,   7,  20, 232, 233,   7, 234, 102,   7,   7,   7,   7,   7,   7,   7,
     25, 235,  20,  20,   7,   7,   7, 236, 155, 108,  67,   7,   7,   7,   7,   7,
      7,   7,   7,   7, 134,   7,   7,   7,  67,   7,   7, 132,   7,   7,   7, 132,
      7,   7,  20,   7,   7,   7,  20,   7,   7,  14,   7,   7,   7,  14,   7,   7,
      7,  67,   7,   7,   7,  67,   7,   7, 132, 237,   4,   4,   4,   4,   4,   4,
     19,  19,  19,  19,  19,  19, 116,  59,  19,  19,  19,  19,  19, 124, 140,   0,
    238,   0,   0,  59,  30,  19,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      7,   7,   7,   7,   7,   7,   7,   7,  17,   0, 116,   0,   0,   0,   0,   0,
    102,   7,   7,   7, 239,   6, 132, 240, 168, 241, 239, 154, 239, 132, 132,  82,
      7,  24,   7, 147, 242,  24,   7, 147,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   7,   7,   7,  74,   7,   7,   7,  74,   7,   7,
      7,  74,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 243, 244, 244, 244,
    245,   0,   0,   0, 166, 166, 166, 166, 166, 166, 166, 166, 166, 166, 166, 166,
     19,  19,  19,  19,  19,  19,  19,  19,  19,  19,  19,  19,  19,  19,  19,  19,
     19,  19,  19,  19,  19,  19,  19,  19,  19,  19,  19,  19,  19,  19,   0,   0,
};

static RE_UINT8 re_word_break_stage_4[] = {
      0,   0,   1,   2,   3,   4,   0,   5,   6,   6,   7,   0,   8,   9,   9,   9,
     10,  11,  10,   0,   0,  12,  13,  14,   0,  15,  13,   0,   9,  10,  16,  17,
     16,  18,   9,  19,   0,  20,  21,  21,   9,  22,  17,  23,   0,  24,  10,  22,
     25,   9,   9,  25,  26,  21,  27,   9,  28,   0,  29,   0,  30,  21,  21,  31,
     32,  31,  33,  33,  34,   0,  35,  36,  37,  38,   0,  39,  40,  41,  42,  21,
     43,  44,  45,   9,   9,  46,  21,  47,  21,  48,  49,  27,  50,  51,   0,  52,
     53,   9,  40,   8,   9,  54,  55,   0,  50,   9,  21,  16,  56,   0,  57,  21,
     21,  58,  58,  59,  58,   0,  60,  21,  21,   9,  54,  61,  58,  21,  54,  62,
     58,   8,   9,  51,  51,   9,  22,   9,  20,  17,  16,  61,  21,  63,  63,  64,
      0,  60,   0,  25,  16,   0,  30,   8,  10,  65,  22,  66,  16,  49,  40,  60,
     63,  59,  67,   0,   8,  20,   0,  62,  27,  68,  22,   8,  31,  59,  19,   0,
      0,  69,  70,   8,  10,  17,  22,  16,  66,  22,  65,  19,  16,  69,  40,  69,
     49,  59,  19,  60,  21,   8,  16,  46,  21,  49,   0,  32,   9,   8,   0,  13,
     66,   0,  10,  46,  49,  64,   0,  65,  17,   9,  69,   8,   9,  28,  71,  60,
     21,  72,  69,   0,  67,  21,  40,   0,  21,  40,  73,   0,  31,  74,  21,  59,
     59,   0,   0,  75,  67,  69,   9,  58,  21,  74,   0,  71,  59,  69,  49,  63,
     30,  74,  69,  21,  76,  59,   0,  28,  10,   9,  10,  30,   9,  16,  54,  74,
     54,   0,  77,   0,   0,  21,  21,   0,   0,  67,  60,  78,  79,   0,   9,  42,
      0,  30,  21,  45,   9,  21,   9,   0,  80,   9,  21,  27,  73,   8,  40,  21,
     45,  53,  54,  81,  82,  82,   9,  20,  17,  22,   9,  17,   0,  83,  84,   0,
      0,  85,  86,  87,   0,  11,  88,  89,   0,  88,  37,  90,  37,  37,  74,   0,
     13,  65,   8,  16,  22,  25,  16,   9,   0,   8,  16,  13,   0,  17,  65,  42,
     27,   0,  91,  92,  93,  94,  95,  95,  96,  95,  95,  96,  50,   0,  21,  97,
     98,  98,  42,   9,  65,  28,   9,  59,  60,  59,  74,  69,  17,  99,   8,  10,
     40,  59,  65,   9,   0, 100, 101,  33,  33,  34,  33, 102, 103, 101, 104,  89,
     11,  88,   0, 105,   5, 106,   9, 107,   0, 108, 109,   0,   0, 110,  95, 111,
     17,  19, 112,   0,  10,  25,  19,  51,  10,  16,  58,  32,   9,  99,  40,  14,
     21, 113,  42,  13,  45,  19,  69,  74, 114,  19,  54,  69,  21,  25,  74,  19,
     94,   0,  16,  32,  37,   0,  59,  30, 115,  37, 116,  21,  40,  30,  69,  59,
     13,  66,   8,  22,  25,   8,  10,   8,  25,  10,   9,  62,   0,  74,  66,  51,
     82,   0,  82,   8,   8,   8,   0, 117, 118, 118,  14,   0,
};

static RE_UINT8 re_word_break_stage_5[] = {
     0,  0,  0,  0,  0,  0,  5,  6,  6,  4,  0,  0,  0,  0,  1,  0,
     0,  0,  0,  2, 13,  0, 14,  0, 15, 15, 15, 15, 15, 15, 12, 13,
     0, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11,  0,  0,  0,  0, 16,
     0,  6,  0,  0,  0,  0, 11,  0,  0,  9,  0,  0,  0, 11,  0, 12,
    11, 11,  0,  0,  0,  0, 11, 11,  0,  0,  0, 12, 11,  0,  0,  0,
    11,  0, 11,  0,  7,  7,  7,  7, 11,  0, 11, 11, 11, 11, 13, 11,
     0,  0, 11, 12, 11, 11,  0, 11, 11, 11,  0,  7,  7,  7, 11, 11,
     0, 11,  0,  0,  0, 13,  0,  0,  0,  7,  7,  7,  7,  7,  0,  7,
     0,  7,  7,  0,  3,  3,  3,  3,  3,  3,  3,  0,  3,  3,  3, 11,
    12,  0,  0,  0,  9,  9,  9,  9,  9,  9,  0,  0, 13, 13,  0,  0,
     7,  7,  7,  0,  9,  0,  0,  0, 11, 11, 11,  7, 15, 15,  0, 15,
    13,  0, 11, 11,  7, 11, 11, 11,  0, 11,  7,  7,  7,  9,  0,  7,
     7, 11, 11,  7,  7,  0,  7,  7, 15, 15, 11, 11, 11,  0,  0, 11,
     0,  0,  0,  9, 11,  7, 11, 11, 11, 11,  7,  7,  7, 11,  0,  0,
    13,  0, 11,  0,  7,  7, 11,  7, 11,  7,  7,  7,  7,  7,  0,  0,
     0,  0,  0,  7,  7, 11,  7,  7,  0,  0, 15, 15,  7,  0,  0,  7,
     7,  7, 11,  0,  0,  0,  0, 11,  0, 11, 11,  0,  0,  7,  0,  0,
    11,  7,  0,  0,  0,  0,  7,  7,  0,  0,  7, 11,  0,  0,  7,  0,
     7,  0,  7,  0, 15, 15,  0,  0,  7,  0,  0,  0,  0,  7,  0,  7,
    15, 15,  7,  7, 11,  0,  7,  7,  7,  7,  9,  0, 11,  7, 11,  0,
     7,  7,  7, 11,  7, 11, 11,  0,  0, 11,  0, 11,  7,  7,  9,  9,
    14, 14,  0,  0, 14,  0,  0, 12,  6,  6,  9,  9,  9,  9,  9,  0,
    16,  0,  0,  0, 13,  0,  0,  0,  9,  0,  9,  9,  0, 10, 10, 10,
    10, 10,  0,  0,  0,  7,  7, 10, 10,  0,  0,  0, 10, 10, 10, 10,
    10, 10, 10,  0,  7,  7,  0, 11, 11, 11,  7, 11, 11,  7,  7,  0,
     0,  3,  7,  3,  3,  0,  3,  3,  3,  0,  3,  0,  3,  3,  0,  3,
    13,  0,  0, 12,  0, 16, 16, 16, 13, 12,  0,  0, 11,  0,  0,  9,
     0,  0,  0, 14,  0,  0, 12, 13,  0,  0, 10, 10, 10, 10,  7,  7,
     0,  9,  9,  9,  7,  0, 15, 15, 15, 15, 11,  0,  7,  7,  7,  9,
     9,  9,  9,  7,  0,  0,  8,  8,  8,  8,  8,  8,
};

/* Word_Break: 4424 bytes. */

RE_UINT32 re_get_word_break(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 12;
    code = ch ^ (f << 12);
    pos = (RE_UINT32)re_word_break_stage_1[f] << 5;
    f = code >> 7;
    code ^= f << 7;
    pos = (RE_UINT32)re_word_break_stage_2[pos + f] << 4;
    f = code >> 3;
    code ^= f << 3;
    pos = (RE_UINT32)re_word_break_stage_3[pos + f] << 1;
    f = code >> 2;
    code ^= f << 2;
    pos = (RE_UINT32)re_word_break_stage_4[pos + f] << 2;
    value = re_word_break_stage_5[pos + code];

    return value;
}

/* Grapheme_Cluster_Break. */

static RE_UINT8 re_grapheme_cluster_break_stage_1[] = {
     0,  1,  2,  2,  2,  3,  4,  5,  6,  2,  2,  7,  2,  8,  9, 10,
     2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,
     2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,
     2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,
     2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,
     2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,
     2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,
    11,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,
     2,  2,  2,  2,  2,  2,  2,  2,
};

static RE_UINT8 re_grapheme_cluster_break_stage_2[] = {
     0,  1,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14,
    15, 16,  1, 17,  1,  1,  1, 18, 19, 20, 21, 22, 23, 24,  1,  1,
    25,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1, 26, 27,  1,  1,
    28,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1, 29,  1, 30, 31, 32, 33, 34, 35, 36, 37,
    38, 39, 40, 34, 35, 36, 37, 38, 39, 40, 34, 35, 36, 37, 38, 39,
    40, 34, 35, 36, 37, 38, 39, 40, 34, 35, 36, 37, 38, 39, 40, 34,
    35, 36, 37, 38, 39, 40, 34, 41, 42, 42, 42, 42, 42, 42, 42, 42,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1, 43,  1,  1, 44, 45,
     1, 46, 47, 48,  1,  1,  1,  1,  1,  1, 49,  1,  1,  1,  1,  1,
    50, 51, 52, 53, 54, 55, 56, 57,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1, 58, 59,  1,  1,  1, 60,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1, 61,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1, 62, 63,  1,  1,  1,  1,  1,  1,  1, 64,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1, 65,  1,  1,  1,  1,  1,  1,  1,
     1, 66,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
    42, 67, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
};

static RE_UINT8 re_grapheme_cluster_break_stage_3[] = {
      0,   1,   2,   2,   2,   2,   2,   3,   1,   1,   4,   2,   2,   2,   2,   2,
      2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,
      5,   5,   5,   5,   5,   5,   5,   2,   2,   2,   2,   2,   2,   2,   2,   2,
      2,   2,   2,   2,   2,   2,   2,   2,   6,   2,   2,   2,   2,   2,   2,   2,
      2,   2,   2,   2,   2,   2,   2,   2,   2,   7,   5,   8,   9,   2,   2,   2,
     10,  11,   2,   2,  12,   5,   2,  13,   2,   2,   2,   2,   2,  14,  15,   2,
      3,  16,   2,   5,  17,   2,   2,   2,   2,   2,  18,  13,   2,   2,  12,  19,
      2,  20,  21,   2,   2,  22,   2,   2,   2,   2,   2,   2,   2,   2,  23,   5,
     24,   2,   2,  25,  26,  27,  28,   2,  29,   2,   2,  30,  31,  32,  28,   2,
     33,   2,   2,  34,  35,  16,   2,  36,  33,   2,   2,  34,  37,   2,  28,   2,
     29,   2,   2,  38,  31,  39,  28,   2,  40,   2,   2,  41,  42,  32,   2,   2,
     43,   2,   2,  44,  45,  46,  28,   2,  29,   2,   2,  47,  48,  46,  28,   2,
     29,   2,   2,  41,  49,  32,  28,   2,  50,   2,   2,   2,  51,  52,   2,  50,
      2,   2,   2,  53,  54,   2,   2,   2,   2,   2,   2,  55,  56,   2,   2,   2,
      2,  57,   2,  58,   2,   2,   2,  59,  60,  61,   5,  62,  63,   2,   2,   2,
      2,   2,  64,  65,   2,  66,  13,  67,  68,  69,   2,   2,   2,   2,   2,   2,
     70,  70,  70,  70,  70,  70,  71,  71,  71,  71,  72,  73,  73,  73,  73,  73,
      2,   2,   2,   2,   2,  64,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,
      2,  74,   2,  74,   2,  28,   2,  28,   2,   2,   2,  75,  76,  77,   2,   2,
     78,   2,   2,   2,   2,   2,   2,   2,   2,   2,  79,   2,   2,   2,   2,   2,
      2,   2,  80,  81,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,
      2,  82,   2,   2,   2,  83,  84,  85,   2,   2,   2,  86,   2,   2,   2,   2,
     87,   2,   2,  88,  89,   2,  12,  19,  90,   2,  91,   2,   2,   2,  92,  93,
      2,   2,  94,  95,   2,   2,   2,   2,   2,   2,   2,   2,   2,  96,  97,  98,
      2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   5,   5,   5,  99,
    100,   2, 101,   2,   2,   2,   1,   2,   2,   2,   2,   2,   2,   5,   5,  13,
      2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2, 102, 103,
      2,   2,   2,   2,   2,   2,   2, 102,   2,   2,   2,   2,   2,   2,   5,   5,
      2,   2, 104,   2,   2,   2,   2,   2,   2, 105,   2,   2,   2,   2,   2,   2,
      2,   2,   2,   2,   2,   2, 102, 106,   2,  44,   2,   2,   2,   2,   2, 103,
    107,   2, 108,   2,   2,   2,   2,   2, 109,   2,   2, 110, 111,   2,   5, 103,
      2,   2, 112,   2, 113,  93,  70, 114,  24,   2,   2, 115, 116,   2, 117,   2,
      2,   2, 118, 119, 120,   2,   2, 121,   2,   2,   2, 122,  16,   2, 123, 124,
      2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2, 125,   2,
    126, 127, 128, 129, 128, 130, 128, 126, 127, 128, 129, 128, 130, 128, 126, 127,
    128, 129, 128, 130, 128, 126, 127, 128, 129, 128, 130, 128, 126, 127, 128, 129,
    128, 130, 128, 126, 127, 128, 129, 128, 130, 128, 126, 127, 128, 129, 128, 130,
    128, 126, 127, 128, 129, 128, 130, 128, 126, 127, 128, 129, 128, 130, 128, 126,
    127, 128, 129, 128, 130, 128, 126, 127, 128, 129, 128, 130, 128, 126, 127, 128,
    129, 128, 130, 128, 126, 127, 128, 129, 128, 130, 128, 126, 127, 128, 129, 128,
    130, 128, 126, 127, 128, 129, 128, 130, 128, 126, 127, 128, 129, 128, 130, 128,
    128, 129, 128, 130, 128, 126, 127, 128, 129, 128, 131,  71, 132,  73,  73, 133,
      1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,
      2, 134,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,
      5,   2,   5,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   3,
      2,   2,   2,   2,   2,   2,   2,   2,   2,  44,   2,   2,   2,   2,   2, 135,
      2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,  69,
      2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,  13,   2,
      2,   2,   2,   2,   2,   2,   2, 136,   2,   2,   2,   2,   2,   2,   2,   2,
    137,   2,   2, 138,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,  46,   2,
    139,   2,   2, 140, 141,   2,   2, 102,  90,   2,   2, 142,   2,   2,   2,   2,
    143,   2, 144, 145,   2,   2,   2, 146,  90,   2,   2, 147, 148,   2,   2,   2,
      2,   2, 149, 150,   2,   2,   2,   2,   2,   2,   2,   2,   2, 102, 151,   2,
     93,   2,   2,  30, 152,  32, 153, 145,   2,   2,   2,   2,   2,   2,   2,   2,
      2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2, 154, 155,   2,   2,   2,
      2,   2,   2,   2,   2,   2,   2,   2,   2,   2, 102, 156,  13, 157,   2,   2,
      2,   2,   2, 158,  13,   2,   2,   2,   2,   2, 159, 160,   2,   2,   2,   2,
      2,  64, 161,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,
      2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2, 145,
      2,   2,   2, 141,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,
      2,   2,   2,   2,   2, 162, 163, 164, 102, 143,   2,   2,   2,   2,   2,   2,
      2,   2,   2,   2,   2,   2,   2,   2,   2, 165, 166,   2,   2,   2,   2,   2,
      2,   2,   2,   2,   2,   2, 167, 168, 169,   2, 170,   2,   2,   2,   2,   2,
      2,   2,   2,   2,  74,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,
      5,   5,   5, 171,   5,   5,  62, 117, 172,  12,   7,   2,   2,   2,   2,   2,
      2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2, 141,   2,   2,
      2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2, 173, 174,
      5,   5,   5,   5,   5,   5,   5,   5,   5,   5,   5,   5,   5,   5,   5,   1,
};

static RE_UINT8 re_grapheme_cluster_break_stage_4[] = {
     0,  0,  1,  2,  0,  0,  0,  0,  3,  3,  3,  3,  3,  3,  3,  4,
     3,  3,  3,  5,  6,  6,  6,  6,  7,  6,  8,  3,  9,  6,  6,  6,
     6,  6,  6, 10, 11, 10,  3,  3,  0, 12,  3,  3,  6,  6, 13, 14,
     3,  3,  7,  6, 15,  3,  3,  3,  3, 16,  6, 17,  6, 18, 19,  8,
    20,  3,  3,  3,  6,  6, 13,  3,  3, 16,  6,  6,  6,  3,  3,  3,
     3, 16, 10,  6,  6,  9,  9,  8,  3,  3,  9,  3,  7,  6,  6,  6,
    21,  3,  3,  3,  3,  3, 22, 23, 24,  6, 25, 26,  9,  6,  3,  3,
    16,  3,  3,  3, 27,  3,  3,  3,  3,  3,  3, 28, 24, 29, 30, 31,
     3,  7,  3,  3, 32,  3,  3,  3,  3,  3,  3, 23, 33,  7, 18,  8,
     8, 20,  3,  3, 24, 10, 34, 31,  3,  3,  3, 19,  3, 16,  3,  3,
    35,  3,  3,  3,  3,  3,  3, 22, 36, 37, 38, 31, 25,  3,  3,  3,
     3,  3,  3, 16, 25, 39, 19,  8,  3, 11,  3,  3,  3,  3,  3, 40,
    41, 42, 38,  8, 24, 23, 38, 31, 37,  3,  3,  3,  3,  3, 35,  7,
    43, 44, 45, 46, 47,  6, 13,  3,  3,  7,  6, 13, 47,  6, 10, 15,
     3,  3,  6,  8,  3,  3,  8,  3,  3, 48, 20, 37,  9,  6,  6, 21,
     6, 19,  3,  9,  6,  6,  9,  6,  6,  6,  6, 15,  3, 35,  3,  3,
     3,  3,  3,  9, 49,  6, 32, 33,  3, 37,  8, 16,  9, 15,  3,  3,
    35, 33,  3, 20,  3,  3,  3, 20, 50, 50, 50, 50, 51, 51, 51, 51,
    51, 51, 52, 52, 52, 52, 52, 52, 16, 15,  3,  3,  3, 53,  6, 54,
    45, 41, 24,  6,  6,  3,  3, 20,  3,  3,  7, 55,  3,  3, 20,  3,
    21, 46, 25,  3, 41, 45, 24,  3,  3,  7, 56,  3,  3, 57,  6, 13,
    44,  9,  6, 25, 46,  6,  6, 18,  6,  6,  6, 13,  6, 58,  3,  3,
     3, 49, 21, 25, 41, 58,  3,  3, 59,  3,  3,  3, 60, 54, 53,  8,
     3, 22, 54, 61, 54,  3,  3,  3,  3, 45, 45,  6,  6, 43,  3,  3,
    13,  6,  6,  6, 49,  6, 15, 20, 37, 15,  8,  3,  6,  8,  3,  6,
     3,  3,  4, 62,  3,  3,  0, 63,  3,  3,  3,  7,  8,  3,  3,  3,
     3,  3, 16,  6,  3,  3, 11,  3, 13,  6,  6,  8, 35, 35,  7,  3,
    64, 65,  3,  3, 66,  3,  3,  3,  3, 45, 45, 45, 45, 15,  3,  3,
     3, 16,  6,  8,  3,  7,  6,  6, 50, 50, 50, 67,  7, 43, 54, 25,
    58,  3,  3,  3,  3, 20,  3,  3,  3,  3,  9, 21, 65, 33,  3,  3,
     7,  3,  3, 68,  3,  3,  3, 15, 19, 18, 15, 16,  3,  3, 64, 54,
     3, 69,  3,  3, 64, 26, 36, 31, 70, 71, 71, 71, 71, 71, 71, 70,
    71, 71, 71, 71, 71, 71, 70, 71, 71, 70, 71, 71, 71,  3,  3,  3,
    51, 72, 73, 52, 52, 52, 52,  3,  3,  3,  3, 35,  0,  0,  0,  3,
     3, 16, 13,  3,  9, 11,  3,  6,  3,  3, 13,  7, 74,  3,  3,  3,
     3,  3,  6,  6,  6, 13,  3,  3, 46, 21, 33,  5, 13,  3,  3,  3,
     3,  7,  6, 24,  6, 15,  3,  3,  7,  3,  3,  3, 64, 43,  6, 21,
    58,  3, 16, 15,  3,  3,  3, 46, 54, 49,  3,  3, 46,  6, 13,  3,
    25, 30, 30, 66, 37, 16,  6, 15, 56,  6, 75, 61, 49,  3,  3,  3,
    43,  8, 45, 53,  3,  3,  3,  8, 46,  6, 21, 61,  3,  3,  7, 26,
     6, 53,  3,  3, 43, 53,  6,  3, 76, 45, 45, 45, 45, 45, 45, 45,
    45, 45, 45, 77,  3,  3,  3, 11,  0,  3,  3,  3,  3, 78,  8, 60,
    79,  0, 80,  6, 13,  9,  6,  3,  3,  3, 16,  8,  6, 13,  7,  6,
     3, 15,  3,  3,  3, 81, 82, 82, 82, 82, 82, 82,
};

static RE_UINT8 re_grapheme_cluster_break_stage_5[] = {
     3,  3,  3,  3,  3,  3,  2,  3,  3,  1,  3,  3,  0,  0,  0,  0,
     0,  0,  0,  3,  0,  3,  0,  0,  4,  4,  4,  4,  0,  0,  0,  4,
     4,  4,  0,  0,  0,  4,  4,  4,  4,  4,  0,  4,  0,  4,  4,  0,
     3,  3,  0,  0,  4,  4,  4,  0,  3,  0,  0,  0,  4,  0,  0,  0,
     0,  0,  4,  4,  4,  3,  0,  4,  4,  0,  0,  4,  4,  0,  4,  4,
     0,  4,  0,  0,  4,  4,  4,  6,  0,  0,  4,  6,  4,  0,  6,  6,
     6,  4,  4,  4,  4,  6,  6,  6,  6,  4,  6,  6,  0,  4,  6,  6,
     4,  0,  4,  6,  4,  0,  0,  6,  6,  0,  0,  6,  6,  4,  0,  0,
     0,  4,  4,  6,  6,  4,  4,  0,  4,  6,  0,  6,  0,  0,  4,  0,
     4,  6,  6,  0,  0,  0,  6,  6,  6,  0,  6,  6,  6,  0,  4,  4,
     4,  0,  6,  4,  6,  6,  4,  6,  6,  0,  4,  6,  6,  6,  4,  4,
     4,  0,  4,  0,  6,  6,  6,  6,  6,  6,  6,  4,  0,  4,  0,  6,
     0,  4,  0,  4,  4,  6,  4,  4,  7,  7,  7,  7,  8,  8,  8,  8,
     9,  9,  9,  9,  4,  4,  6,  4,  4,  4,  6,  6,  4,  4,  3,  0,
     4,  6,  6,  4,  0,  6,  4,  6,  6,  0,  0,  0,  4,  4,  6,  0,
     0,  6,  4,  4,  6,  4,  6,  4,  4,  4,  3,  3,  3,  3,  3,  0,
     0,  0,  0,  6,  6,  4,  4,  6,  6,  6,  0,  0,  7,  0,  0,  0,
     4,  6,  0,  0,  0,  6,  4,  0, 10, 11, 11, 11, 11, 11, 11, 11,
     8,  8,  8,  0,  0,  0,  0,  9,  6,  4,  6,  0,  4,  6,  4,  6,
     0,  6,  6,  6,  6,  6,  6,  0,  0,  4,  6,  4,  4,  4,  4,  3,
     3,  3,  3,  4,  0,  0,  5,  5,  5,  5,  5,  5,
};

/* Grapheme_Cluster_Break: 2640 bytes. */

RE_UINT32 re_get_grapheme_cluster_break(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 13;
    code = ch ^ (f << 13);
    pos = (RE_UINT32)re_grapheme_cluster_break_stage_1[f] << 5;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_grapheme_cluster_break_stage_2[pos + f] << 4;
    f = code >> 4;
    code ^= f << 4;
    pos = (RE_UINT32)re_grapheme_cluster_break_stage_3[pos + f] << 2;
    f = code >> 2;
    code ^= f << 2;
    pos = (RE_UINT32)re_grapheme_cluster_break_stage_4[pos + f] << 2;
    value = re_grapheme_cluster_break_stage_5[pos + code];

    return value;
}

/* Sentence_Break. */

static RE_UINT8 re_sentence_break_stage_1[] = {
     0,  1,  2,  3,  4,  5,  5,  5,  5,  6,  7,  5,  5,  8,  9, 10,
    11, 12, 13, 14, 15,  9, 16,  9,  9,  9,  9, 17,  9, 18, 19, 20,
     5,  5,  5,  5,  5,  5,  5,  5,  5,  5, 21, 22, 23,  9,  9, 24,
     9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,
     9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,
     9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,
     9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,
     9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,
     9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,
     9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,
     9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,
     9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,
     9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,
     9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,
    25,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,
     9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,
     9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,
};

static RE_UINT8 re_sentence_break_stage_2[] = {
      0,   1,   2,   3,   4,   5,   6,   7,   8,   9,  10,  11,  12,  13,  14,  15,
     16,  17,  18,  19,  20,  17,  21,  22,  23,  24,  25,  26,  27,  28,  29,  30,
     31,  32,  33,  34,  35,  33,  33,  36,  33,  37,  33,  33,  38,  39,  40,  33,
     41,  42,  33,  33,  17,  17,  17,  17,  17,  17,  17,  17,  17,  17,  17,  17,
     17,  17,  17,  17,  17,  17,  17,  17,  17,  17,  17,  17,  17,  43,  17,  17,
     17,  17,  17,  17,  17,  17,  17,  17,  17,  17,  17,  17,  17,  17,  17,  17,
     17,  17,  17,  17,  17,  17,  17,  17,  17,  17,  17,  17,  17,  17,  17,  44,
     17,  17,  17,  17,  45,  17,  46,  47,  48,  49,  50,  51,  17,  17,  17,  17,
     17,  17,  17,  17,  17,  17,  17,  52,  33,  33,  33,  33,  33,  33,  33,  33,
     33,  33,  33,  33,  33,  33,  33,  33,  33,  33,  33,  33,  33,  33,  33,  33,
     33,  33,  33,  33,  33,  33,  33,  33,  33,  17,  53,  54,  17,  55,  56,  57,
     58,  59,  60,  61,  62,  63,  17,  64,  65,  66,  67,  68,  69,  33,  33,  33,
     70,  71,  72,  73,  74,  75,  76,  77,  78,  33,  79,  33,  33,  33,  33,  33,
     17,  17,  17,  80,  81,  82,  33,  33,  33,  33,  33,  33,  33,  33,  33,  33,
     17,  17,  17,  17,  83,  33,  33,  33,  33,  33,  33,  33,  33,  33,  33,  33,
     33,  33,  33,  33,  17,  17,  84,  33,  33,  33,  33,  33,  33,  33,  33,  33,
     33,  33,  33,  33,  33,  33,  33,  33,  17,  17,  85,  86,  33,  33,  33,  87,
     88,  33,  33,  33,  33,  33,  33,  33,  33,  33,  33,  33,  89,  33,  33,  33,
     33,  90,  91,  33,  92,  93,  94,  95,  33,  33,  96,  33,  33,  33,  33,  33,
     33,  33,  33,  33,  33,  33,  33,  33,  97,  33,  33,  33,  33,  33,  98,  33,
     33,  99,  33,  33,  33,  33, 100,  33,  33,  33,  33,  33,  33,  33,  33,  33,
     17,  17,  17,  17,  17,  17, 101,  17,  17,  17,  17,  17,  17,  17,  17,  17,
     17,  17,  17,  17,  17,  17,  17, 102, 103,  17,  17,  17,  17,  17,  17,  17,
     17,  17,  17,  17,  17,  17,  17,  17,  17,  17,  17,  17,  17,  17, 104,  33,
     33,  33,  33,  33,  33,  33,  33,  33,  17,  17, 105,  33,  33,  33,  33,  33,
    106, 107,  33,  33,  33,  33,  33,  33,  33,  33,  33,  33,  33,  33,  33,  33,
};

static RE_UINT16 re_sentence_break_stage_3[] = {
      0,   1,   2,   3,   4,   5,   6,   7,   8,   9,  10,  11,  12,  13,  14,  15,
      8,  16,  17,  18,  19,  20,  21,  22,  23,  23,  23,  24,  25,  26,  27,  28,
     29,  30,  18,   8,  31,   8,  32,   8,   8,  33,  34,  35,  36,  37,  38,  39,
     40,  41,  42,  43,  41,  41,  44,  45,  46,  47,  48,  41,  41,  49,  50,  51,
     52,  53,  54,  55,  55,  56,  55,  57,  58,  59,  60,  61,  62,  63,  64,  65,
     66,  67,  68,  69,  70,  71,  72,  73,  74,  71,  75,  76,  77,  78,  79,  80,
     81,  82,  83,  84,  85,  86,  87,  88,  85,  89,  90,  91,  92,  93,  94,  95,
     96,  97,  98,  55,  99, 100, 101,  55, 102, 103, 104, 105, 106, 107, 108,  55,
     41, 109, 110, 111, 112,  29, 113, 114,  41,  41,  41,  41,  41,  41,  41,  41,
     41,  41, 115,  41, 116, 117, 118,  41, 119,  41, 120, 121, 122,  29,  29, 123,
     96,  41,  41,  41,  41,  41,  41,  41,  41,  41,  41, 124, 125,  41,  41, 126,
    127, 128, 129, 130,  41, 131, 132, 133, 134,  41,  41, 135,  41, 136,  41, 137,
    138, 139, 140, 141,  41, 142, 143,  55, 144,  41, 145, 146, 147, 148,  55,  55,
    149, 131, 150, 151, 152, 153,  41, 154,  41, 155, 156, 157,  55,  55, 158, 159,
     18,  18,  18,  18,  18,  18,  23, 160,   8,   8,   8,   8, 161,   8,   8,   8,
    162, 163, 164, 165, 163, 166, 167, 168, 169, 170, 171, 172, 173,  55, 174, 175,
    176, 177, 178,  30, 179,  55,  55,  55,  55,  55,  55,  55,  55,  55,  55,  55,
    180, 181,  55,  55,  55,  55,  55,  55,  55,  55,  55,  55,  55, 182,  30, 183,
     55,  55, 184, 185,  55,  55, 186, 187,  55,  55,  55,  55, 188,  55, 189, 190,
     29, 191, 192, 193,   8,   8,   8, 194,  18, 195,  41, 196, 197, 198, 198,  23,
    199, 200, 201,  55,  55,  55,  55,  55, 202, 203,  96,  41, 204,  96,  41, 114,
    205, 206,  41,  41, 207, 208,  55, 209,  41,  41,  41,  41,  41, 137,  55,  55,
     41,  41,  41,  41,  41,  41, 137,  55,  41,  41,  41,  41, 210,  55, 209, 211,
    212, 213,   8, 214, 215,  41,  41, 216, 217, 218,   8, 219, 220, 221,  55, 222,
    223, 224,  41, 225, 226, 131, 227, 228,  50, 229, 230, 231,  58, 232, 233, 234,
     41, 235, 236, 237,  41, 238, 239, 240, 241, 242, 243, 244,  18,  18,  41, 245,
     41,  41,  41,  41,  41, 246, 247, 248,  41,  41,  41, 249,  41,  41, 250,  55,
    251, 252, 253,  41,  41, 254, 255,  41,  41, 256, 209,  41, 257,  41, 258, 259,
    260, 261, 262, 263,  41,  41,  41, 264, 265,   2, 266, 267, 268, 138, 269, 270,
    271, 272, 273,  55,  41,  41,  41, 208,  55,  55,  41,  56,  55,  55,  55, 274,
     55,  55,  55,  55, 231,  41, 275, 276,  41, 209, 277, 278, 279,  41, 280,  55,
     29, 281, 282,  41, 279, 133,  55,  55,  41, 283,  41, 284,  55,  55,  55,  55,
     41, 197, 137, 258,  55,  55,  55,  55, 285, 286, 137, 197, 138,  55,  55, 287,
    137, 250,  55,  55,  41, 288,  55,  55, 289, 290, 291, 231, 231,  55, 104, 292,
     41, 137, 137, 293, 254,  55,  55,  55,  41,  41, 294,  55,  29, 295,  18, 296,
    152, 297, 298, 299, 152, 300, 301, 302, 152, 303, 304, 305, 152, 232, 306,  55,
    307, 308,  55,  55, 309, 310, 311, 312, 313,  71, 314, 315,  55,  55,  55,  55,
     55,  55,  55,  55,  41,  47, 316,  55,  55,  55,  55,  55,  41, 317, 318,  55,
     41,  47, 319,  55,  41, 320, 133,  55, 321, 322,  55,  55,  55,  55,  55,  55,
     55,  55,  55,  55,  55,  29,  18, 323,  55,  55,  55,  55,  55,  55,  41, 324,
     41,  41,  41,  41, 250,  55,  55,  55,  41,  41,  41, 207,  41,  41,  41,  41,
     41,  41, 284,  55,  55,  55,  55,  55,  41, 207,  55,  55,  55,  55,  55,  55,
     41,  41, 325,  55,  55,  55,  55,  55,  41, 324, 138, 326,  55,  55, 209, 327,
     41, 328, 329, 330, 122,  55,  55,  55,  41,  41, 331, 332, 333,  55,  55,  55,
    334,  55,  55,  55,  55,  55,  55,  55,  41,  41,  41, 335, 336, 337,  55,  55,
     55,  55,  55, 338, 339, 340,  55,  55,  55,  55, 341,  55,  55,  55,  55,  55,
    342, 343, 344, 345, 346, 347, 348, 349, 350, 351, 352, 353, 354, 342, 343, 355,
    345, 356, 357, 358, 349, 359, 360, 361, 362, 363, 364, 191, 365, 366, 367, 368,
     23, 369,  23, 370, 371, 372,  55,  55,  41,  41,  41,  41,  41,  41, 373,  55,
    374, 375, 376, 377, 378, 379,  55,  55,  55, 380, 381, 381, 382,  55,  55,  55,
     55,  55,  55, 383,  55,  55,  55,  55,  41,  41,  41,  41,  41,  41, 197,  55,
     41,  56,  41,  41,  41,  41,  41,  41, 279,  41,  41,  41,  41,  41,  41,  41,
     41,  41,  41,  41,  41, 334,  55,  55, 279,  55,  55,  55,  55,  55,  55,  55,
    384, 385, 385, 385,  55,  55,  55,  55,  23,  23,  23,  23,  23,  23,  23, 386,
};

static RE_UINT8 re_sentence_break_stage_4[] = {
      0,   0,   1,   2,   0,   0,   0,   0,   3,   4,   5,   6,   7,   7,   8,   9,
     10,  11,  11,  11,  11,  11,  12,  13,  14,  15,  15,  15,  15,  15,  16,  13,
      0,  17,   0,   0,   0,   0,   0,   0,  18,   0,  19,  20,   0,  21,  19,   0,
     11,  11,  11,  11,  11,  22,  11,  23,  15,  15,  15,  15,  15,  24,  15,  15,
     25,  25,  25,  25,  25,  25,  25,  25,  25,  25,  25,  25,  25,  25,  26,  26,
     26,  26,  27,  25,  25,  25,  25,  25,  25,  25,  25,  25,  25,  25,  28,  29,
     30,  31,  32,  33,  28,  31,  34,  28,  25,  31,  29,  31,  32,  26,  35,  34,
     36,  28,  31,  26,  26,  26,  26,  27,  25,  25,  25,  25,  30,  31,  25,  25,
     25,  25,  25,  25,  25,  15,  33,  30,  26,  23,  25,  25,  15,  15,  15,  15,
     15,  15,  15,  15,  15,  15,  15,  15,  15,  15,  15,  15,  15,  37,  15,  15,
     15,  15,  15,  15,  15,  15,  38,  36,  39,  40,  36,  36,  41,   0,   0,   0,
     15,  42,   0,  43,   0,   0,   0,   0,  44,  44,  44,  44,  44,  44,  44,  44,
     44,  44,  44,  44,  25,  45,  46,  47,   0,  48,  22,  49,  32,  11,  11,  11,
     50,  11,  11,  15,  15,  15,  15,  15,  15,  15,  15,  51,  33,  34,  25,  25,
     25,  25,  25,  25,  15,  52,  30,  32,  11,  11,  11,  11,  11,  11,  11,  11,
     11,  11,  11,  11,  15,  15,  15,  15,  53,  44,  54,  25,  25,  25,  25,  25,
     28,  26,  26,  29,  25,  25,  25,  25,  25,  25,  25,  25,  10,  11,  11,  11,
     11,  11,  11,  11,  11,  22,  55,  56,  14,  15,  15,  15,  15,  15,  15,  15,
     15,  15,  57,   0,  58,  44,  44,  44,  44,  44,  44,  44,  44,  44,  44,  59,
     60,  59,   0,   0,  36,  36,  36,  36,  36,  36,  61,   0,  36,   0,   0,   0,
     62,  63,   0,  64,  44,  44,  65,  66,  36,  36,  36,  36,  36,  36,  36,  36,
     36,  36,  67,  44,  44,  44,  44,  44,   7,   7,  68,  69,  70,  36,  36,  36,
     36,  36,  36,  36,  36,  71,  44,  72,  44,  73,  74,  75,   7,   7,  76,  77,
     78,   0,   0,  79,  80,  36,  36,  36,  36,  36,  36,  36,  44,  44,  44,  44,
     44,  44,  65,  81,  36,  36,  36,  36,  36,  82,  44,  44,  83,   0,   0,   0,
      7,   7,  76,  36,  36,  36,  36,  36,  36,  36,  67,  44,  44,  41,  84,   0,
     36,  36,  36,  36,  36,  82,  85,  44,  44,  86,  86,  87,   0,   0,   0,   0,
     36,  36,  36,  36,  36,  36,  86,   0,   0,   0,   0,   0,   0,   0,   0,   0,
     36,  36,  36,  36,  36,  88,   0,   0,  89,  44,  44,  44,  44,  44,  44,  44,
     44,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  82,  90,
     44,  44,  44,  44,  86,  44,  36,  36,  82,  91,   7,   7,  81,  36,  36,  36,
     86,  81,  36,  77,  77,  36,  36,  36,  36,  36,  92,  36,  43,  40,  41,  90,
     44,  93,  93,  94,   0,  89,   0,  95,  82,  96,   7,   7,  41,   0,   0,   0,
     58,  81,  61,  97,  77,  36,  36,  36,  36,  36,  92,  36,  92,  98,  41,  74,
     65,  89,  93,  87,  99,   0,  81,  43,   0,  96,   7,   7,  75, 100,   0,   0,
     58,  81,  36,  95,  95,  36,  36,  36,  36,  36,  92,  36,  92,  81,  41,  90,
     44,  59,  59,  87,  88,   0,   0,   0,  82,  96,   7,   7,   0,   0,  55,   0,
     58,  81,  36,  77,  77,  36,  36,  36,  44,  93,  93,  87,   0, 101,   0,  95,
     82,  96,   7,   7,  55,   0,   0,   0, 102,  81,  61,  40,  92,  41,  98,  92,
     97,  88,  61,  40,  36,  36,  41, 101,  65, 101,  74,  87,  88,  89,   0,   0,
      0,  96,   7,   7,   0,   0,   0,   0,  44,  81,  36,  92,  92,  36,  36,  36,
     36,  36,  92,  36,  36,  36,  41, 103,  44,  74,  74,  87,   0,  60,  61,   0,
     82,  96,   7,   7,   0,   0,   0,   0,  58,  81,  36,  92,  92,  36,  36,  36,
     36,  36,  92,  36,  36,  81,  41,  90,  44,  74,  74,  87,   0,  60,   0, 104,
     82,  96,   7,   7,  98,   0,   0,   0,  36,  36,  36,  36,  36,  36,  61, 103,
     44,  74,  74,  94,   0,  89,   0,  97,  82,  96,   7,   7,   0,   0,  40,  36,
    101,  81,  36,  36,  36,  61,  40,  36,  36,  36,  36,  36,  95,  36,  36,  55,
     36,  61, 105,  89,  44, 106,  44,  44,   0,  96,   7,   7, 101,   0,   0,   0,
     81,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  80,  44,  65,   0,
     36,  67,  44,  65,   7,   7, 107,   0,  98,  77,  43,  55,   0,  36,  81,  36,
     81, 108,  40,  81,  80,  44,  59,  83,  36,  43,  44,  87,   7,   7, 107,  36,
     88,   0,   0,   0,   0,   0,  87,   0,   7,   7, 107,   0,   0, 109, 110, 111,
     36,  36,  81,  36,  36,  36,  36,  36,  36,  36,  36,  88,  58,  44,  44,  44,
     44,  74,  36,  86,  44,  44,  58,  44,  44,  44,  44,  44,  44,  44,  44, 112,
      0, 105,   0,   0,   0,   0,   0,   0,  36,  36,  67,  44,  44,  44,  44, 113,
      7,   7, 114,   0,  36,  82,  75,  82,  90,  73,  44,  75,  86,  70,  36,  36,
     82,  44,  44,  85,   7,   7, 115,  87,  11,  50,   0, 116,  36,  36,  36,  36,
     36,  36,  36,  36,  36,  36,  61,  36,  36,  36,  92,  41,  36,  61,  92,  41,
     36,  36,  92,  41,  36,  36,  36,  36,  36,  36,  36,  36,  92,  41,  36,  61,
     92,  41,  36,  36,  36,  61,  36,  36,  36,  36,  36,  36,  92,  41,  36,  36,
     36,  36,  36,  36,  36,  36,  61,  58, 117,   9, 118,   0,   0,   0,   0,   0,
     36,  36,  36,  36,   0,   0,   0,   0,  11,  11,  11,  11,  11, 119,  15,  39,
     36,  36,  36, 120,  36,  36,  36,  36, 121,  36,  36,  36,  36,  36, 122, 123,
     36,  36,  61,  40,  36,  36,  88,   0,  36,  36,  36,  92,  82, 112,   0,   0,
     36,  36,  36,  36,  82, 124,   0,   0,  36,  36,  36,  36,  82,   0,   0,   0,
     36,  36,  36,  92, 125,   0,   0,   0,  36,  36,  36,  36,  36,  44,  44,  44,
     44,  44,  44,  44,  44,  97,   0, 100,   7,   7, 107,   0,   0,   0,   0,   0,
    126,   0, 127, 128,   7,   7, 107,   0,  36,  36,  36,  36,  36,  36,   0,   0,
     36,  36, 129,   0,  36,  36,  36,  36,  36,  36,  36,  36,  36,  41,   0,   0,
     36,  36,  36,  36,  36,  36,  36,  61,  44,  44,  44,   0,  44,  44,  44,   0,
      0,  91,   7,   7,  36,  36,  36,  36,  36,  36,  36,  41,  36,  88,   0,   0,
     36,  36,  36,   0,  36,  36,  36,  36,  36,  36,  41,   0,   7,   7, 107,   0,
     36,  36,  36,  36,  36,  67,  44,   0,  36,  36,  36,  36,  36,  86,  44,  65,
     44,  44,  44,  44,  44,  44,  44,  93,   7,   7, 107,   0,   7,   7, 107,   0,
      0,  97, 130,   0,  44,  44,  44,  65,  44,  70,  36,  36,  36,  36,  36,  36,
     44,  70,  36,   0,   7,   7, 114, 131,   0,   0,  89,  44,  44,   0,   0,   0,
    113,  36,  36,  36,  36,  36,  36,  36,  86,  44,  44,  75,   7,   7,  76,  36,
     36,  82,  44,  44,  44,   0,   0,   0,  36,  44,  44,  44,  44,  44,   9, 118,
      7,   7, 107,  81,   7,   7,  76,  36,  36,  36,  36,  36,  36,  36,  36, 132,
      0,   0,   0,   0,  65,  44,  44,  44,  44,  44,  70,  80,  82, 133,  87,   0,
     44,  44,  44,  44,  44,  87,   0,  44,  25,  25,  25,  25,  25,  34,  15,  27,
     15,  15,  11,  11,  15,  39,  11, 119,  15,  15,  11,  11,  15,  15,  11,  11,
     15,  39,  11, 119,  15,  15, 134, 134,  15,  15,  11,  11,  15,  15,  15,  39,
     15,  15,  11,  11,  15, 135,  11, 136,  46, 135,  11, 137,  15,  46,  11,   0,
     15,  15,  11, 137,  46, 135,  11, 137, 138, 138, 139, 140, 141, 142, 143, 143,
      0, 144, 145, 146,   0,   0, 147, 148,   0, 149, 148,   0,   0,   0,   0, 150,
     62, 151,  62,  62,  21,   0,   0, 152,   0,   0,   0, 147,  15,  15,  15,  42,
      0,   0,   0,   0,  44,  44,  44,  44,  44,  44,  44,  44, 112,   0,   0,   0,
     48, 153, 154, 155,  23, 116,  10, 119,   0, 156,  49, 157,  11,  38, 158,  33,
      0, 159,  39, 160,   0,   0,   0,   0, 161,  38,  88,   0,   0,   0,   0,   0,
      0,   0, 143,   0,   0,   0,   0,   0,   0,   0, 147,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0, 162,  11,  11,  15,  15,  39,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   4, 143, 123,   0, 143, 143, 143,   5,   0,   0,
      0, 147,   0,   0,   0,   0,   0,   0,   0, 163, 143, 143,   0,   0,   0,   0,
      4, 143, 143, 143, 143, 143, 123,   0,   0,   0,   0,   0,   0,   0, 143,   0,
      0,   0,   0,   0,   0,   0,   0,   5,  11,  11,  11,  22,  15,  15,  15,  15,
     15,  15,  15,  15,  15,  15,  15,  24,  31, 164,  26,  32,  25,  29,  15,  33,
     25,  42, 153, 165,  54,   0,   0,   0,  15, 166,   0,  21,  36,  36,  36,  36,
     36,  36,   0,  97,   0,   0,   0,  89,  36,  36,  36,  36,  36,  61,   0,   0,
     36,  61,  36,  61,  36,  61,  36,  61, 143, 143, 143,   5,   0,   0,   0,   5,
    143, 143,   5, 167,   0,   0,   0, 118, 168,   0,   0,   0,   0,   0,   0,   0,
    169,  81, 143, 143,   5, 143, 143, 170,  81,  36,  82,  44,  81,  41,  36,  88,
     36,  36,  36,  36,  36,  61,  60,  81,   0,  81,  36,  36,  36,  36,  36,  36,
     36,  36,  36,  41,  81,  36,  36,  36,  36,  36,  36,  61,   0,   0,   0,   0,
     36,  36,  36,  36,  36,  36,  61,   0,   0,   0,   0,   0,  36,  36,  36,  36,
     36,  36,  36,  88,   0,   0,   0,   0,  36,  36,  36,  36,  36,  36,  36, 171,
     36,  36,  36, 172,  36,  36,  36,  36,   7,   7,  76,   0,   0,   0,   0,   0,
     25,  25,  25, 173,  65,  44,  44, 174,  25,  25,  25,  25,  25,  25,  25, 175,
     36,  36,  36,  36, 176,   9,   0,   0,   0,   0,   0,   0,   0,  97,  36,  36,
    177,  25,  25,  25,  27,  25,  25,  25,  25,  25,  25,  25,  15,  15,  26,  30,
     25,  25, 178, 179,  25,  27,  25,  25,  25,  25,  31, 119,  11,  25,   0,   0,
      0,   0,   0,   0,   0,  97, 180,  36, 181, 181,  67,  36,  36,  36,  36,  36,
     67,  44,   0,   0,   0,   0,   0,   0,  36,  36,  36,  36,  36, 131,   0,   0,
     75,  36,  36,  36,  36,  36,  36,  36,  44, 112,   0, 131,   7,   7, 107,   0,
     44,  44,  44,  44,  75,  36,  97,  55,  36,  82,  44, 176,  36,  36,  36,  36,
     36,  67,  44,  44,  44,   0,   0,   0,  36,  36,  36,  36,  36,  36,  36,  88,
     36,  36,  36,  36,  67,  44,  44,  44, 112,   0, 148,  97,   7,   7, 107,   0,
     36,  80,  36,  36,   7,   7,  76,  61,  36,  36,  86,  44,  44,  65,   0,   0,
     67,  36,  36,  87,   7,   7, 107, 182,  36,  36,  36,  36,  36,  61, 183,  75,
     36,  36,  36,  36,  90,  73,  70,  82, 129,   0,   0,   0,   0,   0,  97,  41,
     36,  36,  67,  44, 184, 185,   0,   0,  81,  61,  81,  61,  81,  61,   0,   0,
     36,  61,  36,  61,  15,  15,  15,  15,  15,  15,  15,  15,  15,  15,  24,  15,
     15,  39,   0,   0,  15,  15,  15,  15,  67,  44, 186,  87,   7,   7, 107,   0,
     36,   0,   0,   0,  36,  36,  36,  36,  36,  61,  97,  36,  36,  36,  36,  36,
     36,  36,  36,  36,  36,  36,  36,   0,  36,  36,  36,  41,  36,  36,  36,  36,
     36,  36,  36,  36,  36,  36,  41,   0,  15,  24,   0,   0, 187,  15,   0, 188,
     36,  36,  92,  36,  36,  61,  36,  43,  95,  92,  36,  36,  36,  36,  36,  36,
     36,  36,  36,  36,  41,   0,   0,   0,   0,   0,   0,   0,  97,  36,  36,  36,
     36,  36,  36,  36,  36,  36,  36, 189,  36,  36,  36,  36,  40,  36,  36,  36,
     36,  36,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  36,  36,  36,   0,
     44,  44,  44,  44, 190,   4, 123,   0,  44,  44,  44,  44, 191, 170, 143, 143,
    143, 192, 123,   0,   6, 193, 194, 195, 141,   0,   0,   0,  36,  92,  36,  36,
     36,  36,  36,  36,  36,  36,  36, 196,  57,   0,   5,   6,   0,   0, 197,   9,
     14,  15,  15,  15,  15,  15,  16, 198, 199, 200,  36,  36,  36,  36,  36,  36,
     36,  36,  36,  36,  36,  36,  36,  82,  40,  36,  40,  36,  40,  36,  40,  88,
      0,   0,   0,   0,   0,   0, 201,   0,  36,  36,  36,  81,  36,  36,  36,  36,
     36,  61,  36,  36,  36,  36,  61,  95,  36,  36,  36,  41,  36,  36,  36,  41,
      0,   0,   0,   0,   0,   0,   0,  99,  36,  36,  36,  36,  88,   0,   0,   0,
    112,   0,   0,   0,   0,   0,   0,   0,  36,  36,  61,   0,  36,  36,  36,  36,
     36,  36,  36,  36,  36,  82,  65,   0,  36,  36,  36,  36,  36,  36,  36,  41,
     36,   0,  36,  36,  81,  41,   0,   0,  11,  11,  15,  15,  15,  15,  15,  15,
     15,  15,  15,  15,  36,  36,  36,  36,  36,  36,   0,   0,  36,  36,  36,  36,
     36,   0,   0,   0,   0,   0,   0,   0,  36,  41,  92,  36,  36,  36,  36,  36,
     36,  36,  36,  36,  36,  95,  88,  77,  36,  36,  36,  36,  61,  41,   0,   0,
     36,  36,  36,  36,  36,  36,   0,  40,  86,  60,   0,  44,  36,  81,  81,  36,
     36,  36,  36,  36,  36,   0,  65,  89,   0,   0,   0,   0,   0, 131,   0,   0,
     36, 185,   0,   0,   0,   0,   0,   0,  36,  36,  36,  36,  61,   0,   0,   0,
     36,  36,  88,   0,   0,   0,   0,   0,  11,  11,  11,  11,  22,   0,   0,   0,
     15,  15,  15,  15,  24,   0,   0,   0,  36,  36,  36,  36,  36,  36,  44,  44,
     44, 186, 118,   0,   0,   0,   0,   0,   0,  96,   7,   7,   0,   0,   0,  89,
     36,  36,  36,  36,  44,  44,  65, 202, 148,   0,   0,   0,  36,  36,  36,  36,
     36,  36,  88,   0,   7,   7, 107,   0,  36,  67,  44,  44,  44, 203,   7,   7,
    182,   0,   0,   0,  36,  36,  36,  36,  36,  36,  36,  36,  67, 104,   0,   0,
     70, 204, 101, 205,   7,   7, 206, 172,  36,  36,  36,  36,  95,  36,  36,  36,
     36,  36,  36,  44,  44,  44, 207, 118,  36,  61,  92,  95,  36,  36,  36,  95,
     36,  36, 208,   0,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  67,
     44,  44,  65,   0,   7,   7, 107,   0,  44,  81,  36,  77,  77,  36,  36,  36,
     44,  93,  93,  87,  88,  89,   0,  81,  82, 101,  44, 112,  44, 112,   0,   0,
     44,  95,   0,   0,   7,   7, 107,   0,  36,  36,  36,  67,  44,  87,  44,  44,
    209,   0, 182, 130, 130, 130,  36,  87, 124,  88,   0,   0,   7,   7, 107,   0,
     36,  36,  67,  44,  44,  44,   0,   0,  36,  36,  36,  36,  36,  36,  41,  58,
     44,  44,  44,   0,   7,   7, 107,  78,   7,   7, 107,   0,   0,   0,   0,  97,
     36,  36,  36,  36,  36,  36,  88,   0,  36,  61,   0,   0,   0,   0,   0,   0,
      7,   7, 107, 131,   0,   0,   0,   0,  36,  36,  36,  41,  44, 205,   0,   0,
     36,  36,  36,  36,  44, 186, 118,   0,  36, 118,   0,   0,   7,   7, 107,   0,
     97,  36,  36,  36,  36,  36,   0,  81,  36,  88,   0,   0,  86,  44,  44,  44,
     44,  44,  44,  44,  44,  44,  44,  65,   0,   0,   0,  89, 113,  36,  36,  36,
     41,   0,   0,   0,   0,   0,   0,   0,  36,  36,  61,   0,  36,  36,  36,  88,
     36,  36,  88,   0,  36,  36,  41, 210,  62,   0,   0,   0,   0,   0,   0,   0,
      0,  58,  87,  58, 211,  62, 212,  44,  65,  58,  44,   0,   0,   0,   0,   0,
      0,   0, 101,  87,   0,   0,   0,   0, 101, 112,   0,   0,   0,   0,   0,   0,
     11,  11,  11,  11,  11,  11, 155,  15,  15,  15,  15,  15,  15,  11,  11,  11,
     11,  11,  11, 155,  15, 135,  15,  15,  15,  15,  11,  11,  11,  11,  11,  11,
    155,  15,  15,  15,  15,  15,  15,  49,  48, 213,  10,  49,  11, 155, 166,  14,
     15,  14,  15,  15,  11,  11,  11,  11,  11,  11, 155,  15,  15,  15,  15,  15,
     15,  50,  22,  10,  11,  49,  11, 214,  15,  15,  15,  15,  15,  15,  50,  22,
     11, 156, 162,  11, 214,  15,  15,  15,  15,  15,  15,  11,  11,  11,  11,  11,
     11, 155,  15,  15,  15,  15,  15,  15,  11,  11,  11, 155,  15,  15,  15,  15,
    155,  15,  15,  15,  15,  15,  15,  11,  11,  11,  11,  11,  11, 155,  15,  15,
     15,  15,  15,  15,  11,  11,  11,  11,  15,  39,  11,  11,  11,  11,  11,  11,
    214,  15,  15,  15,  15,  15,  24,  15,  33,  11,  11,  11,  11,  11,  22,  15,
     15,  15,  15,  15,  15, 135,  15,  11,  11,  11,  11,  11,  11, 214,  15,  15,
     15,  15,  15,  24,  15,  33,  11,  11,  15,  15, 135,  15,  11,  11,  11,  11,
     11,  11, 214,  15,  15,  15,  15,  15,  24,  15,  27,  96,   7,   7,   7,   7,
      7,   7,   7,   7,   7,   7,   7,   7,  44,  44,  44,  44,  44,  65,  89,  44,
     44,  44,  44, 112,   0,  99,   0,   0,   0, 112, 118,   0,   0,   0,  89,  44,
     58,  44,  44,  44,   0,   0,   0,   0,  36,  88,   0,   0,  44,  65,   0,   0,
     36,  81,  36,  36,  36,  36,  36,  36,  98,  77,  81,  36,  61,  36, 108,   0,
    104,  97, 108,  81,  98,  77, 108, 108,  98,  77,  61,  36,  61,  36,  81,  43,
     36,  36,  95,  36,  36,  36,  36,   0,  81,  81,  95,  36,  36,  36,  36,   0,
      0,   0,   0,   0,  11,  11,  11,  11,  11,  11, 119,   0,  11,  11,  11,  11,
     11,  11, 119,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 163, 123,   0,
     20,   0,   0,   0,   0,   0,   0,   0,  62,  62,  62,  62,  62,  62,  62,  62,
     44,  44,  44,  44,   0,   0,   0,   0,
};

static RE_UINT8 re_sentence_break_stage_5[] = {
     0,  0,  0,  0,  0,  6,  2,  6,  6,  1,  0,  0,  6, 12, 13,  0,
     0,  0,  0, 13, 13, 13,  0,  0, 14, 14, 11,  0, 10, 10, 10, 10,
    10, 10, 14,  0,  0,  0,  0, 12,  0,  8,  8,  8,  8,  8,  8,  8,
     8,  8,  8, 13,  0, 13,  0,  0,  0,  7,  7,  7,  7,  7,  7,  7,
     7,  7,  7, 13,  0,  4,  0,  0,  6,  0,  0,  0,  0,  0,  7, 13,
     0,  5,  0,  0,  0,  7,  0,  0,  8,  8,  8,  0,  8,  8,  8,  7,
     7,  7,  7,  0,  8,  7,  8,  7,  7,  8,  7,  8,  7,  7,  8,  7,
     8,  8,  7,  8,  7,  8,  7,  7,  7,  8,  8,  7,  8,  7,  8,  8,
     7,  8,  8,  8,  7,  7,  8,  8,  8,  7,  7,  7,  8,  7,  7,  9,
     9,  9,  9,  9,  9,  7,  7,  7,  7,  9,  9,  9,  7,  7,  0,  0,
     0,  0,  9,  9,  9,  9,  0,  0,  7,  0,  0,  0,  9,  0,  9,  0,
     3,  3,  3,  3,  9,  0,  8,  7,  0,  0,  7,  7,  7,  7,  0,  8,
     0,  0,  8,  0,  8,  0,  8,  8,  8,  8,  0,  8,  7,  7,  7,  8,
     8,  7,  0,  8,  8,  7,  0,  3,  3,  3,  8,  7,  0,  9,  0,  0,
     0, 14,  0,  0,  0, 12,  0,  0,  0,  3,  3,  3,  3,  3,  0,  3,
     0,  3,  3,  0,  9,  9,  9,  0,  5,  5,  5,  5,  5,  5,  0,  0,
    14, 14,  0,  0,  3,  3,  3,  0,  5,  0,  0, 12,  9,  9,  9,  3,
    10, 10,  0, 10, 10,  0,  9,  9,  3,  9,  9,  9, 12,  9,  3,  3,
     3,  5,  0,  3,  3,  9,  9,  3,  3,  0,  3,  3,  3,  3,  9,  9,
    10, 10,  9,  9,  9,  0,  0,  9, 12, 12, 12,  0,  0,  0,  0,  5,
     9,  3,  9,  9,  0,  9,  9,  9,  9,  9,  3,  3,  3,  9,  0,  0,
    14, 12,  9,  0,  3,  3,  9,  3,  9,  3,  3,  3,  3,  3,  0,  0,
     9,  0,  0,  0,  0,  0,  0,  3,  3,  9,  3,  3, 12, 12, 10, 10,
     9,  0,  9,  9,  3,  0,  0,  3,  3,  3,  9,  0,  9,  9,  0,  9,
     0,  0, 10, 10,  0,  0,  0,  9,  0,  9,  9,  0,  0,  3,  0,  0,
     9,  3,  0,  0,  0,  0,  3,  3,  0,  0,  3,  9,  0,  9,  3,  3,
     0,  0,  9,  0,  0,  0,  3,  0,  3,  0,  3,  0, 10, 10,  0,  0,
     0,  9,  0,  9,  0,  3,  0,  3,  0,  3, 13, 13, 13, 13,  3,  3,
     3,  0,  0,  0,  3,  3,  3,  9, 10, 10, 12, 12, 10, 10,  3,  3,
     0,  8,  0,  0,  0,  0, 12,  0, 12,  0,  0,  0,  8,  8,  0,  0,
     9,  0, 12,  9,  6,  9,  9,  9,  9,  9,  9, 13, 13,  0,  0,  0,
     3, 12, 12,  0,  9,  0,  3,  3,  0,  0, 14, 12, 14, 12,  0,  3,
     3,  3,  5,  0,  9,  3,  9,  0, 12, 12, 12, 12,  0,  0, 12, 12,
     9,  9, 12, 12,  3,  9,  9,  0,  0,  8,  0,  8,  7,  0,  7,  7,
     8,  0,  7,  0,  8,  0,  0,  0,  6,  6,  6,  6,  6,  6,  6,  5,
     3,  3,  5,  5,  0,  0,  0, 14, 14,  0,  0,  0, 13, 13, 13, 13,
    11,  0,  0,  0,  4,  4,  5,  5,  5,  5,  5,  6,  0, 13, 13,  0,
    12, 12,  0,  0,  0, 13, 13, 12,  0,  0,  0,  6,  5,  0,  5,  5,
     0, 13, 13,  7,  0,  0,  0,  8,  0,  0,  7,  8,  8,  8,  7,  7,
     8,  0,  8,  0,  8,  8,  0,  7,  9,  7,  0,  0,  0,  8,  7,  7,
     0,  0,  7,  0,  9,  9,  9,  8,  0,  0,  8,  8,  0,  0, 13, 13,
     8,  7,  7,  8,  7,  8,  7,  3,  7,  7,  0,  7,  0,  0, 12,  9,
     0,  0, 13,  0,  6, 14, 12,  0,  0, 13, 13, 13,  9,  9,  0, 12,
     9,  0, 12, 12,  8,  7,  9,  3,  3,  3,  0,  9,  7,  7,  3,  3,
     3,  3,  0, 12,  0,  0,  8,  7,  9,  0,  0,  8,  7,  8,  7,  9,
     7,  7,  7,  9,  9,  9,  3,  9,  0, 12, 12, 12,  0,  0,  9,  3,
    12, 12,  9,  9,  9,  3,  3,  0,  3,  3,  3, 12,  0,  0,  0,  7,
     0,  9,  3,  9,  9,  9, 13, 13, 14, 14,  0, 14,  0, 14, 14,  0,
    13,  0,  0, 13,  0, 14, 12, 12, 14, 13, 13, 13, 13, 13, 13,  0,
     9,  0,  0,  5,  0,  0, 14,  0,  0, 13,  0, 13, 13, 12, 13, 13,
    14,  0,  9,  9,  0,  5,  5,  5,  0,  5, 12, 12,  3,  0, 10, 10,
     9, 12, 12,  0,  3, 12,  0,  0, 10, 10,  9,  0, 12, 12,  0, 12,
     9, 12,  0,  0,  3,  0, 12, 12,  0,  3,  3, 12,  3,  3,  3,  5,
     5,  5,  5,  3,  0,  8,  8,  0,  8,  0,  7,  7,
};

/* Sentence_Break: 6372 bytes. */

RE_UINT32 re_get_sentence_break(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 12;
    code = ch ^ (f << 12);
    pos = (RE_UINT32)re_sentence_break_stage_1[f] << 4;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_sentence_break_stage_2[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_sentence_break_stage_3[pos + f] << 3;
    f = code >> 2;
    code ^= f << 2;
    pos = (RE_UINT32)re_sentence_break_stage_4[pos + f] << 2;
    value = re_sentence_break_stage_5[pos + code];

    return value;
}

/* Math. */

static RE_UINT8 re_math_stage_1[] = {
    0, 1, 2, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2,
};

static RE_UINT8 re_math_stage_2[] = {
    0, 1, 1, 1, 2, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 4,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 5, 1, 1, 6, 1, 1,
};

static RE_UINT8 re_math_stage_3[] = {
     0,  1,  1,  2,  1,  1,  3,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     4,  5,  6,  7,  1,  8,  9, 10,  1,  6,  6, 11,  1,  1,  1,  1,
     1,  1,  1, 12,  1,  1, 13, 14,  1,  1,  1,  1, 15, 16, 17, 18,
     1,  1,  1,  1,  1,  1, 19,  1,
};

static RE_UINT8 re_math_stage_4[] = {
     0,  1,  2,  3,  0,  4,  5,  5,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  6,  7,  8,  0,  0,  0,  0,  0,  0,  0,
     9, 10, 11, 12, 13,  0, 14, 15, 16, 17, 18,  0, 19, 20, 21, 22,
    23, 23, 23, 23, 23, 23, 23, 23, 24, 25,  0, 26, 27, 28, 29, 30,
     0,  0,  0,  0,  0, 31, 32, 33, 34,  0, 35, 36,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0, 23, 23,  0, 19, 37,  0,  0,  0,  0,  0,
     0, 38,  0,  0,  0,  0,  0,  0,  0,  0,  0, 39,  0,  0,  0,  0,
     1,  3,  3,  0,  0,  0,  0, 40, 23, 23, 41, 23, 42, 43, 44, 23,
    45, 46, 47, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 48, 23, 23,
    23, 23, 23, 23, 23, 23, 49, 23, 44, 50, 51, 52, 53, 54,  0, 55,
};

static RE_UINT8 re_math_stage_5[] = {
      0,   0,   0,   0,   0,   8,   0, 112,   0,   0,   0,  64,   0,   0,   0,  80,
      0,  16,   2,   0,   0,   0, 128,   0,   0,   0,  39,   0,   0,   0, 115,   0,
    192,   1,   0,   0,   0,   0,  64,   0,   0,   0,  28,   0,  17,   0,   4,   0,
     30,   0,   0, 124,   0, 124,   0,   0,   0,   0, 255,  31,  98, 248,   0,   0,
    132, 252,  47,  63,  16, 179, 251, 241, 255,  11,   0,   0,   0,   0, 255, 255,
    255, 126, 195, 240, 255, 255, 255,  47,  48,   0, 240, 255, 255, 255, 255, 255,
      0,  15,   0,   0,   3,   0,   0,   0,   0,   0,   0,  16,   0,   0,   0, 248,
    255, 255, 191,   0,   0,   0,   1, 240,   7,   0,   0,   0,   3, 192, 255, 240,
    195, 140,  15,   0, 148,  31,   0, 255,  96,   0,   0,   0,   5,   0,   0,   0,
     15, 224,   0,   0, 159,  31,   0,   0,   0,   2,   0,   0, 126,   1,   0,   0,
      4,  30,   0,   0, 255, 255, 223, 255, 255, 255, 255, 223, 100, 222, 255, 235,
    239, 255, 255, 255, 191, 231, 223, 223, 255, 255, 255, 123,  95, 252, 253, 255,
     63, 255, 255, 255, 255, 207, 255, 255, 150, 254, 247,  10, 132, 234, 150, 170,
    150, 247, 247,  94, 255, 251, 255,  15, 238, 251, 255,  15,   0,   0,   3,   0,
};

/* Math: 538 bytes. */

RE_UINT32 re_get_math(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 15;
    code = ch ^ (f << 15);
    pos = (RE_UINT32)re_math_stage_1[f] << 4;
    f = code >> 11;
    code ^= f << 11;
    pos = (RE_UINT32)re_math_stage_2[pos + f] << 3;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_math_stage_3[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_math_stage_4[pos + f] << 5;
    pos += code;
    value = (re_math_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Alphabetic. */

static RE_UINT8 re_alphabetic_stage_1[] = {
    0, 1, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
    3,
};

static RE_UINT8 re_alphabetic_stage_2[] = {
     0,  1,  2,  3,  4,  5,  6,  7,  7,  8,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  9, 10, 11,  7,  7,  7,  7, 12, 13, 13, 13, 13, 14,
    15, 16, 17, 18, 19, 13, 20, 13, 21, 13, 13, 13, 13, 22, 13, 13,
    13, 13, 13, 13, 13, 13, 23, 24, 13, 13, 25, 13, 13, 26, 27, 13,
     7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  7, 28,  7, 29, 30,  7, 31, 13, 13, 13, 13, 13, 32,
    13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13,
    13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13,
};

static RE_UINT8 re_alphabetic_stage_3[] = {
     0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15,
    16,  1, 17, 18, 19,  1, 20, 21, 22, 23, 24, 25, 26, 27,  1, 28,
    29, 30, 31, 31, 32, 31, 31, 31, 31, 31, 31, 31, 33, 34, 35, 31,
    36, 37, 31, 31,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1, 38,  1,  1,  1,  1,  1,  1,  1,  1,  1, 39,
     1,  1,  1,  1, 40,  1, 41, 42, 43, 44, 45, 46,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1, 47, 31, 31, 31, 31, 31, 31, 31, 31,
    31,  1, 48, 49,  1, 50, 51, 52, 53, 54, 55, 56, 57, 58,  1, 59,
    60, 61, 62, 63, 64, 31, 31, 31, 65, 66, 67, 68, 69, 70, 71, 72,
    73, 31, 74, 31, 31, 31, 31, 31,  1,  1,  1, 75, 76, 77, 31, 31,
     1,  1,  1,  1, 78, 31, 31, 31, 31, 31, 31, 31,  1,  1, 79, 31,
     1,  1, 80, 81, 31, 31, 31, 82, 83, 31, 31, 31, 31, 31, 31, 31,
    31, 31, 31, 31, 84, 31, 31, 31, 31, 31, 31, 31, 85, 86, 87, 88,
    89, 31, 31, 31, 31, 31, 90, 31, 31, 91, 31, 31, 31, 31, 31, 31,
     1,  1,  1,  1,  1,  1, 92,  1,  1,  1,  1,  1,  1,  1,  1, 93,
    94,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1, 95, 31,
     1,  1, 96, 31, 31, 31, 31, 31,
};

static RE_UINT8 re_alphabetic_stage_4[] = {
      0,   0,   1,   1,   0,   2,   3,   3,   4,   4,   4,   4,   4,   4,   4,   4,
      4,   4,   4,   4,   4,   4,   5,   6,   0,   0,   7,   8,   9,  10,   4,  11,
      4,   4,   4,   4,  12,   4,   4,   4,   4,  13,  14,  15,  16,  17,  18,  19,
     20,   4,  21,  22,   4,   4,  23,  24,  25,   4,  26,   4,   4,  27,  28,  29,
     30,  31,  32,   0,   0,  33,   0,  34,   4,  35,  36,  37,  38,  39,  40,  41,
     42,  43,  44,  45,  46,  47,  48,  49,  50,  47,  51,  52,  53,  54,  55,   0,
     56,  57,  58,  59,  60,  61,  62,  63,  60,  64,  65,  66,  67,  68,  69,  70,
     15,  71,  72,   0,  73,  74,  75,   0,  76,   0,  77,  78,  79,  80,   0,   0,
      4,  81,  25,  82,  83,   4,  84,  85,   4,   4,  86,   4,  87,  88,  89,   4,
     90,   4,  91,   0,  92,   4,   4,  93,  15,   4,   4,   4,   4,   4,   4,   4,
      4,   4,   4,  94,   1,   4,   4,  95,  96,  97,  97,  98,   4,  99, 100,   0,
      0,   4,   4, 101,   4, 102,   4, 103, 104, 105,  25, 106,   4, 107, 108,   0,
    109,   4, 104, 110,   0, 111,   0,   0,   4, 112, 113,   0,   4, 114,   4, 115,
      4, 103, 116, 117,   0,   0,   0, 118,   4,   4,   4,   4,   4,   4,   0, 119,
     93,   4, 120, 117,   4, 121, 122, 123,   0,   0,   0, 124, 125,   0,   0,   0,
    126, 127, 128,   4, 129,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0, 130,   4, 108,   4, 131, 104,   4,   4,   4,   4, 132,
      4,  84,   4, 133, 134, 135, 135,   4,   0, 136,   0,   0,   0,   0,   0,   0,
    137, 138,  15,   4, 139,  15,   4,  85, 140, 141,   4,   4, 142,  71,   0,  25,
      4,   4,   4,   4,   4, 103,   0,   0,   4,   4,   4,   4,   4,   4, 103,   0,
      4,   4,   4,   4,  31,   0,  25, 117, 143, 144,   4, 145,   4,   4,   4,  92,
    146, 147,   4,   4, 148, 149,   0, 146, 150,  16,   4,  97,   4,   4,  59, 151,
     28, 102, 152,  80,   4, 153, 136, 154,   4, 134, 155, 156,   4, 104, 157, 158,
    159, 160,  85, 161,   4,   4,   4, 162,   4,   4,   4,   4,   4, 163, 164, 109,
      4,   4,   4, 165,   4,   4, 166,   0, 167, 168, 169,   4,   4,  27, 170,   4,
      4, 117,  25,   4, 171,   4,  16, 172,   0,   0,   0, 173,   4,   4,   4,  80,
      0,   1,   1, 174,   4, 104, 175,   0, 176, 177, 178,   0,   4,   4,   4,  71,
      0,   0,   4,  33,   0,   0,   0,   0,   0,   0,   0,   0,  80,   4, 179,   0,
      4,  25, 102,  71, 117,   4, 180,   0,   4,   4,   4,   4, 117,   0,   0,   0,
      4, 181,   4,  59,   0,   0,   0,   0,   4, 134, 103,  16,   0,   0,   0,   0,
    182, 183, 103, 134, 104,   0,   0, 184, 103, 166,   0,   0,   4, 185,   0,   0,
    186,  97,   0,  80,  80,   0,  77, 187,   4, 103, 103, 152,  27,   0,   0,   0,
      4,   4, 129,   0,   4, 152,   4, 152,   4,   4, 188,   0, 147,  32,  25, 129,
      4, 152,  25, 189,   4,   4, 190,   0, 191, 192,   0,   0, 193, 194,   4, 129,
     38,  47, 195,  59,   0,   0,   0,   0,   0,   0,   0,   0,   4,   4, 196,   0,
      0,   0,   0,   0,   4, 197, 198,   0,   4, 104, 199,   0,   4, 103,   0,   0,
    200, 162,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   4,   4, 201,
      0,   0,   0,   0,   0,   0,   4,  32,   4,   4,   4,   4, 166,   0,   0,   0,
      4,   4,   4, 142,   4,   4,   4,   4,   4,   4,  59,   0,   0,   0,   0,   0,
      4, 142,   0,   0,   0,   0,   0,   0,   4,   4, 202,   0,   0,   0,   0,   0,
      4,  32, 104,   0,   0,   0,  25, 155,   4, 134,  59, 203,  92,   0,   0,   0,
      4,   4, 204, 104, 170,   0,   0,   0, 205,   0,   0,   0,   0,   0,   0,   0,
      4,   4,   4, 206, 207,   0,   0,   0,   4,   4, 208,   4, 209, 210, 211,   4,
    212, 213, 214,   4,   4,   4,   4,   4,   4,   4,   4,   4,   4, 215, 216,  85,
    208, 208, 131, 131, 217, 217, 218,   0,   4,   4,   4,   4,   4,   4, 187,   0,
    211, 219, 220, 221, 222, 223,   0,   0,   0,  25, 224, 224, 108,   0,   0,   0,
      4,   4,   4,   4,   4,   4, 134,   0,   4,  33,   4,   4,   4,   4,   4,   4,
    117,   4,   4,   4,   4,   4,   4,   4,   4,   4,   4,   4,   4, 205,   0,   0,
    117,   0,   0,   0,   0,   0,   0,   0,
};

static RE_UINT8 re_alphabetic_stage_5[] = {
      0,   0,   0,   0, 254, 255, 255,   7,   0,   4,  32,   4, 255, 255, 127, 255,
    255, 255, 255, 255, 195, 255,   3,   0,  31,  80,   0,   0,  32,   0,   0,   0,
      0,   0, 223, 188,  64, 215, 255, 255, 251, 255, 255, 255, 255, 255, 191, 255,
      3, 252, 255, 255, 255, 255, 254, 255, 255, 255, 127,   2, 254, 255, 255, 255,
    255,   0,   0,   0,   0,   0, 255, 191, 182,   0, 255, 255, 255,   7,   7,   0,
      0,   0, 255,   7, 255, 255, 255, 254,   0, 192, 255, 255, 255, 255, 239,  31,
    254, 225,   0, 156,   0,   0, 255, 255,   0, 224, 255, 255, 255, 255,   3,   0,
      0, 252, 255, 255, 255,   7,  48,   4, 255, 255, 255, 252, 255,  31,   0,   0,
    255, 255, 255,   1, 255, 255,  31,   0, 248,   3, 255, 255, 255, 255, 255, 239,
    255, 223, 225, 255,  15,   0, 254, 255, 239, 159, 249, 255, 255, 253, 197, 227,
    159,  89, 128, 176,  15,   0,   3,   0, 238, 135, 249, 255, 255, 253, 109, 195,
    135,  25,   2,  94,   0,   0,  63,   0, 238, 191, 251, 255, 255, 253, 237, 227,
    191,  27,   1,   0,  15,   0,   0,   2, 238, 159, 249, 255, 159,  25, 192, 176,
     15,   0,   2,   0, 236, 199,  61, 214,  24, 199, 255, 195, 199,  29, 129,   0,
    239, 223, 253, 255, 255, 253, 255, 227, 223,  29,  96,   7,  15,   0,   0,   0,
    238, 223, 253, 255, 255, 253, 239, 227, 223,  29,  96,  64,  15,   0,   6,   0,
    255, 255, 255, 231, 223,  93, 128, 128,  15,   0,   0, 252, 236, 255, 127, 252,
    255, 255, 251,  47, 127, 128,  95, 255,   0,   0,  12,   0, 255, 255, 255,   7,
    127,  32,   0,   0, 150,  37, 240, 254, 174, 236, 255,  59,  95,  32,   0, 240,
      1,   0,   0,   0, 255, 254, 255, 255, 255,  31, 254, 255,   3, 255, 255, 254,
    255, 255, 255,  31, 255, 255, 127, 249, 231, 193, 255, 255, 127,  64,   0,  48,
    191,  32, 255, 255, 255, 255, 255, 247, 255,  61, 127,  61, 255,  61, 255, 255,
    255, 255,  61, 127,  61, 255, 127, 255, 255, 255,  61, 255, 255, 255, 255, 135,
    255, 255,   0,   0, 255, 255,  63,  63, 255, 159, 255, 255, 255, 199, 255,   1,
    255, 223,  15,   0, 255, 255,  15,   0, 255, 223,  13,   0, 255, 255, 207, 255,
    255,   1, 128,  16, 255, 255, 255,   0, 255,   7, 255, 255, 255, 255,  63,   0,
    255, 255, 255, 127, 255,  15, 255,   1, 255,  63,  31,   0, 255,  15, 255, 255,
    255,   3,   0,   0, 255, 255, 255,  15, 254, 255,  31,   0, 128,   0,   0,   0,
    255, 255, 239, 255, 239,  15,   0,   0, 255, 243,   0, 252, 191, 255,   3,   0,
      0, 224,   0, 252, 255, 255, 255,  63,   0, 222, 111,   0, 128, 255,  31,   0,
     63,  63, 255, 170, 255, 255, 223,  95, 220,  31, 207,  15, 255,  31, 220,  31,
      0,   0,   2, 128,   0,   0, 255,  31, 132, 252,  47,  62,  80, 189, 255, 243,
    224,  67,   0,   0, 255,   1,   0,   0,   0,   0, 192, 255, 255, 127, 255, 255,
     31, 120,  12,   0, 255, 128,   0,   0, 255, 255, 127,   0, 127, 127, 127, 127,
      0, 128,   0,   0, 224,   0,   0,   0, 254,   3,  62,  31, 255, 255, 127, 224,
    224, 255, 255, 255, 255,  63, 254, 255, 255, 127,   0,   0, 255,  31, 255, 255,
      0,  12,   0,   0, 255, 127, 240, 143,   0,   0, 128, 255, 252, 255, 255, 255,
    255, 249, 255, 255, 255,  63, 255,   0, 187, 247, 255, 255,   0,   0, 252,  40,
    255, 255,   7,   0, 255, 255, 247, 255, 223, 255,   0, 124, 255,  63,   0,   0,
    255, 255, 127, 196,   5,   0,   0,  56, 255, 255,  60,   0, 126, 126, 126,   0,
    127, 127, 255, 255,  63,   0, 255, 255, 255,   7,   0,   0,  15,   0, 255, 255,
    127, 248, 255, 255, 255,  63, 255, 255, 255, 255, 255,   3, 127,   0, 248, 224,
    255, 253, 127,  95, 219, 255, 255, 255,   0,   0, 248, 255, 255, 255, 252, 255,
      0,   0, 255,  15,   0,   0, 223, 255, 192, 255, 255, 255, 252, 252, 252,  28,
    255, 239, 255, 255, 127, 255, 255, 183, 255,  63, 255,  63, 255, 255,   1,   0,
     15, 255,  62,   0, 255,   0, 255, 255,  63, 253, 255, 255, 255, 255, 191, 145,
    255, 255,  55,   0, 255, 255, 255, 192, 111, 240, 239, 254,  31,   0,   0,   0,
     63,   0,   0,   0, 255, 255,  71,   0,  30,   0,   0,  20, 255, 255, 251, 255,
    255, 255, 159,   0, 127, 189, 255, 191, 255,   1, 255, 255, 159,  25, 129, 224,
    179,   0,   0,   0, 255, 255,  63, 127,   0,   0,   0,  63,  17,   0,   0,   0,
    255, 255, 255, 227,   0,   0,   0, 128, 127,   0,   0,   0, 248, 255, 255, 224,
     31,   0, 255, 255,   3,   0,   0,   0, 255,   7, 255,  31, 255,   1, 255,  67,
    255, 255, 223, 255, 255, 255, 255, 223, 100, 222, 255, 235, 239, 255, 255, 255,
    191, 231, 223, 223, 255, 255, 255, 123,  95, 252, 253, 255,  63, 255, 255, 255,
    253, 255, 255, 247, 255, 253, 255, 255, 247,  15,   0,   0, 150, 254, 247,  10,
    132, 234, 150, 170, 150, 247, 247,  94, 255, 251, 255,  15, 238, 251, 255,  15,
    255,   3, 255, 255,
};

/* Alphabetic: 2085 bytes. */

RE_UINT32 re_get_alphabetic(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_alphabetic_stage_1[f] << 5;
    f = code >> 11;
    code ^= f << 11;
    pos = (RE_UINT32)re_alphabetic_stage_2[pos + f] << 3;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_alphabetic_stage_3[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_alphabetic_stage_4[pos + f] << 5;
    pos += code;
    value = (re_alphabetic_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Lowercase. */

static RE_UINT8 re_lowercase_stage_1[] = {
    0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2,
};

static RE_UINT8 re_lowercase_stage_2[] = {
    0, 1, 2, 3, 3, 3, 3, 3, 3, 3, 4, 3, 3, 3, 3, 5,
    6, 7, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 8, 3, 3,
    3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
};

static RE_UINT8 re_lowercase_stage_3[] = {
     0,  1,  2,  3,  4,  5,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     6,  6,  6,  7,  6,  6,  6,  6,  6,  6,  6,  6,  6,  8,  9, 10,
    11, 12,  6,  6, 13,  6,  6,  6,  6,  6,  6,  6, 14, 15,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     6,  6,  6,  6,  6,  6, 16, 17,  6,  6,  6, 18,  6,  6,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6, 19,  6,  6,  6, 20,
     6,  6,  6,  6, 21,  6,  6,  6,  6,  6,  6,  6, 22,  6,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6, 23,  6,  6,  6,  6,  6,  6,  6,
     6,  6,  6,  6, 24, 25, 26, 27,  6,  6,  6,  6,  6,  6,  6,  6,
};

static RE_UINT8 re_lowercase_stage_4[] = {
     0,  0,  0,  1,  0,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12,
     5, 13, 14, 15, 16, 17, 18, 19,  0,  0, 20, 21, 22, 23, 24, 25,
     0, 26, 15,  5, 27,  5, 28,  5,  5, 29,  0, 30, 31,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 32,
    15, 15, 15, 15, 15, 15,  0,  0,  5,  5,  5,  5, 33,  5,  5,  5,
    34, 35, 36, 37, 35, 38, 39, 40,  0,  0,  0, 41, 42,  0,  0,  0,
    43, 44, 45, 26, 46,  0,  0,  0,  0,  0,  0,  0,  0,  0, 26, 47,
     0, 26, 48, 49,  5,  5,  5, 50, 15, 51,  0,  0,  0,  0,  0,  0,
     0,  0,  5, 52, 53,  0,  0,  0,  0, 54,  5, 55, 56, 57,  0, 58,
     0, 26, 59, 60, 15, 15,  0,  0, 61,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  1,  0,  0,  0,  0,  0,  0, 62, 63,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0, 15, 64,  0,  0,  0,  0,  0,  0, 15,  0,
    65, 66, 67, 31, 68, 69, 70, 71, 72, 73, 74, 75, 76, 65, 66, 77,
    31, 68, 78, 63, 71, 79, 80, 81, 82, 78, 83, 26, 84, 71, 85,  0,
};

static RE_UINT8 re_lowercase_stage_5[] = {
      0,   0,   0,   0, 254, 255, 255,   7,   0,   4,  32,   4,   0,   0,   0, 128,
    255, 255, 127, 255, 170, 170, 170, 170, 170, 170, 170,  85,  85, 171, 170, 170,
    170, 170, 170, 212,  41,  49,  36,  78,  42,  45,  81, 230,  64,  82,  85, 181,
    170, 170,  41, 170, 170, 170, 250, 147, 133, 170, 255, 255, 255, 255, 255, 255,
    255, 255, 239, 255, 255, 255, 255,   1,   3,   0,   0,   0,  31,   0,   0,   0,
     32,   0,   0,   0,   0,   0, 138,  60,   0,   0,   1,   0,   0, 240, 255, 255,
    255, 127, 227, 170, 170, 170,  47,  25,   0,   0, 255, 255,   2, 168, 170, 170,
     84, 213, 170, 170, 170, 170,   0,   0, 254, 255, 255, 255, 255,   0,   0,   0,
      0,   0,   0,  63, 170, 170, 234, 191, 255,   0,  63,   0, 255,   0, 255,   0,
     63,   0, 255,   0, 255,   0, 255,  63, 255,   0, 223,  64, 220,   0, 207,   0,
    255,   0, 220,   0,   0,   0,   2, 128,   0,   0, 255,  31,   0, 196,   8,   0,
      0, 128,  16,  50, 192,  67,   0,   0,  16,   0,   0,   0, 255,   3,   0,   0,
    255, 255, 255, 127,  98,  21, 218,  63,  26,  80,   8,   0, 191,  32,   0,   0,
    170,  42,   0,   0, 170, 170, 170,  58, 168, 170, 171, 170, 170, 170, 255, 149,
    170,  80, 186, 170, 170,   2, 160,   0,   0,   0,   0,   7, 255, 255, 255, 247,
     63,   0, 255, 255, 127,   0, 248,   0,   0, 255, 255, 255, 255, 255,   0,   0,
    255, 255,   7,   0,   0,   0,   0, 252, 255, 255,  15,   0,   0, 192, 223, 255,
    252, 255, 255,  15,   0,   0, 192, 235, 239, 255,   0,   0,   0, 252, 255, 255,
     15,   0,   0, 192, 255, 255, 255,   0,   0,   0, 252, 255, 255,  15,   0,   0,
    192, 255, 255, 255,   0, 192, 255, 255,   0,   0, 192, 255,  63,   0,   0,   0,
    252, 255, 255, 247,   3,   0,   0, 240, 255, 255, 223,  15, 255, 127,  63,   0,
    255, 253,   0,   0, 247,  11,   0,   0,
};

/* Lowercase: 777 bytes. */

RE_UINT32 re_get_lowercase(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_lowercase_stage_1[f] << 4;
    f = code >> 12;
    code ^= f << 12;
    pos = (RE_UINT32)re_lowercase_stage_2[pos + f] << 4;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_lowercase_stage_3[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_lowercase_stage_4[pos + f] << 5;
    pos += code;
    value = (re_lowercase_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Uppercase. */

static RE_UINT8 re_uppercase_stage_1[] = {
    0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2,
};

static RE_UINT8 re_uppercase_stage_2[] = {
     0,  1,  2,  3,  4,  5,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  6,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  7,
     8,  9,  1, 10,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1, 11,  1,  1,  1, 12,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
};

static RE_UINT8 re_uppercase_stage_3[] = {
     0,  1,  2,  3,  4,  5,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     7,  6,  6,  8,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  9, 10,
     6, 11,  6,  6, 12,  6,  6,  6,  6,  6,  6,  6, 13,  6,  6,  6,
     6,  6,  6,  6,  6,  6, 14, 15,  6,  6,  6,  6,  6,  6,  6, 16,
     6,  6,  6,  6, 17,  6,  6,  6,  6,  6,  6,  6, 18,  6,  6,  6,
    19,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6, 20, 21, 22, 23,
     6, 24,  6,  6,  6,  6,  6,  6,
};

static RE_UINT8 re_uppercase_stage_4[] = {
     0,  0,  1,  0,  0,  0,  2,  0,  3,  4,  5,  6,  7,  8,  9, 10,
     3, 11, 12,  0,  0,  0,  0,  0,  0,  0,  0, 13, 14, 15, 16, 17,
    18, 19,  0,  3, 20,  3, 21,  3,  3, 22, 23,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 18, 24,  0,
     0,  0,  0,  0,  0, 18, 18, 25,  3,  3,  3,  3, 26,  3,  3,  3,
    27, 28, 29, 30,  0, 31, 32, 33, 34, 35, 36, 19, 37,  0,  0,  0,
     0,  0,  0,  0,  0, 38, 19,  0, 18, 39,  0, 40,  3,  3,  3, 41,
     0,  0,  3, 42, 43,  0,  0,  0,  0, 44,  3, 45, 46, 47,  0,  0,
     0,  1,  0,  0,  0,  0,  0,  0, 18, 48,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0, 18, 49,  0,  0,  0,  0,  0,  0,  0, 18,  0,  0,
    50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 50, 51, 52,
    53, 63, 25, 56, 57, 53, 64, 65, 66, 67, 38, 39, 56, 68, 69,  0,
     0, 56, 70, 70, 57,  0,  0,  0,
};

static RE_UINT8 re_uppercase_stage_5[] = {
      0,   0,   0,   0, 254, 255, 255,   7, 255, 255, 127, 127,  85,  85,  85,  85,
     85,  85,  85, 170, 170,  84,  85,  85,  85,  85,  85,  43, 214, 206, 219, 177,
    213, 210, 174,  17, 144, 164, 170,  74,  85,  85, 210,  85,  85,  85,   5, 108,
    122,  85,   0,   0,   0,   0,  69, 128,  64, 215, 254, 255, 251,  15,   0,   0,
      0, 128,  28,  85,  85,  85, 144, 230, 255, 255, 255, 255, 255, 255,   0,   0,
      1,  84,  85,  85, 171,  42,  85,  85,  85,  85, 254, 255, 255, 255, 127,   0,
    191,  32,   0,   0, 255, 255,  63,   0,  85,  85,  21,  64,   0, 255,   0,  63,
      0, 255,   0, 255,   0,  63,   0, 170,   0, 255,   0,   0,   0,   0,   0,  15,
      0,  15,   0,  15,   0,  31,   0,  15, 132,  56,  39,  62,  80,  61,  15, 192,
     32,   0,   0,   0,   8,   0,   0,   0,   0,   0, 192, 255, 255, 127,   0,   0,
    157, 234,  37, 192,   5,  40,   4,   0,  85,  21,   0,   0,  85,  85,  85,   5,
     84,  85,  84,  85,  85,  85,   0, 106,  85,  40,  69,  85,  85,  61,  95,   0,
    255,   0,   0,   0, 255, 255,   7,   0, 255, 255, 255,   3,   0,   0, 240, 255,
    255,  63,   0,   0,   0, 255, 255, 255,   3,   0,   0, 208, 100, 222,  63,   0,
      0,   0, 255, 255, 255,   3,   0,   0, 176, 231, 223,  31,   0,   0,   0, 123,
     95, 252,   1,   0,   0, 240, 255, 255,  63,   0,   0,   0,   3,   0,   0, 240,
      1,   0,   0,   0, 252, 255, 255,   7,   0,   0,   0, 240, 255, 255,  31,   0,
    255,   1,   0,   0,   0,   4,   0,   0, 255,   3, 255, 255,
};

/* Uppercase: 701 bytes. */

RE_UINT32 re_get_uppercase(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_uppercase_stage_1[f] << 5;
    f = code >> 11;
    code ^= f << 11;
    pos = (RE_UINT32)re_uppercase_stage_2[pos + f] << 3;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_uppercase_stage_3[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_uppercase_stage_4[pos + f] << 5;
    pos += code;
    value = (re_uppercase_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Cased. */

static RE_UINT8 re_cased_stage_1[] = {
    0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2,
};

static RE_UINT8 re_cased_stage_2[] = {
     0,  1,  2,  3,  4,  5,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  6,  7,  1,  1,  1,  1,  1,  1,  1,  1,  1,  8,
     9, 10,  1, 11,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1, 12,  1,  1,  1, 13,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
};

static RE_UINT8 re_cased_stage_3[] = {
     0,  1,  2,  3,  4,  5,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     7,  6,  6,  8,  6,  6,  6,  6,  6,  6,  6,  6,  6,  9, 10, 11,
    12, 13,  6,  6, 14,  6,  6,  6,  6,  6,  6,  6, 15, 16,  6,  6,
     6,  6,  6,  6,  6,  6, 17, 18,  6,  6,  6, 19,  6,  6,  6,  6,
     6,  6,  6, 20,  6,  6,  6, 21,  6,  6,  6,  6, 22,  6,  6,  6,
     6,  6,  6,  6, 23,  6,  6,  6, 24,  6,  6,  6,  6,  6,  6,  6,
     6,  6,  6,  6, 25, 26, 27, 28,  6, 29,  6,  6,  6,  6,  6,  6,
};

static RE_UINT8 re_cased_stage_4[] = {
     0,  0,  1,  1,  0,  2,  3,  3,  4,  4,  4,  4,  4,  5,  6,  4,
     4,  4,  4,  4,  7,  8,  9, 10,  0,  0, 11, 12, 13, 14,  4, 15,
     4,  4,  4,  4, 16,  4,  4,  4,  4, 17, 18, 19, 20,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  4, 21,  0,
     0,  0,  0,  0,  0,  4,  4, 22,  4,  4,  4,  4,  4,  4,  0,  0,
     4,  4,  4,  4,  4,  4,  4,  4, 22,  4, 23, 24,  4, 25, 26, 27,
     0,  0,  0, 28, 29,  0,  0,  0, 30, 31, 32,  4, 33,  0,  0,  0,
     0,  0,  0,  0,  0, 34,  4, 35,  4, 36, 37,  4,  4,  4,  4, 38,
     4, 21,  0,  0,  0,  0,  0,  0,  0,  0,  4, 39, 24,  0,  0,  0,
     0, 40,  4,  4, 41, 42,  0, 43,  0, 44,  5, 45,  4,  4,  0,  0,
    46,  0,  0,  0,  0,  0,  0,  0,  0,  1,  1,  0,  0,  0,  0,  0,
     4,  4, 47,  0,  0,  0,  0,  0,  0,  0,  0,  0,  4, 48,  4, 48,
     0,  0,  0,  0,  0,  4,  4,  0,  4,  4, 49,  4, 50, 51, 52,  4,
    53, 54, 55,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4, 56, 57,  5,
    49, 49, 36, 36, 58, 58, 59,  0,  0, 44, 60, 60, 35,  0,  0,  0,
};

static RE_UINT8 re_cased_stage_5[] = {
      0,   0,   0,   0, 254, 255, 255,   7,   0,   4,  32,   4, 255, 255, 127, 255,
    255, 255, 255, 255, 255, 255, 255, 247, 240, 255, 255, 255, 255, 255, 239, 255,
    255, 255, 255,   1,   3,   0,   0,   0,  31,   0,   0,   0,  32,   0,   0,   0,
      0,   0, 207, 188,  64, 215, 255, 255, 251, 255, 255, 255, 255, 255, 191, 255,
      3, 252, 255, 255, 255, 255, 254, 255, 255, 255, 127,   0, 254, 255, 255, 255,
    255,   0,   0,   0, 191,  32,   0,   0, 255, 255,  63,  63,  63,  63, 255, 170,
    255, 255, 255,  63, 255, 255, 223,  95, 220,  31, 207,  15, 255,  31, 220,  31,
      0,   0,   2, 128,   0,   0, 255,  31, 132, 252,  47,  62,  80, 189,  31, 242,
    224,  67,   0,   0,  24,   0,   0,   0,   0,   0, 192, 255, 255,   3,   0,   0,
    255, 127, 255, 255, 255, 255, 255, 127,  31, 120,  12,   0, 255,  63,   0,   0,
    252, 255, 255, 255, 255, 120, 255, 255, 255,  63, 255,   0,   0,   0,   0,   7,
      0,   0, 255, 255,  63,   0, 255, 255, 127,   0, 248,   0, 255, 255,   0,   0,
    255, 255,   7,   0, 255, 255, 223, 255, 255, 255, 255, 223, 100, 222, 255, 235,
    239, 255, 255, 255, 191, 231, 223, 223, 255, 255, 255, 123,  95, 252, 253, 255,
     63, 255, 255, 255, 253, 255, 255, 247, 255, 253, 255, 255, 247,  15,   0,   0,
    255,   3, 255, 255,
};

/* Cased: 709 bytes. */

RE_UINT32 re_get_cased(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_cased_stage_1[f] << 5;
    f = code >> 11;
    code ^= f << 11;
    pos = (RE_UINT32)re_cased_stage_2[pos + f] << 3;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_cased_stage_3[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_cased_stage_4[pos + f] << 5;
    pos += code;
    value = (re_cased_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Case_Ignorable. */

static RE_UINT8 re_case_ignorable_stage_1[] = {
    0, 1, 2, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
    4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 4, 4, 4,
    4, 4,
};

static RE_UINT8 re_case_ignorable_stage_2[] = {
     0,  1,  2,  3,  4,  5,  6,  7,  7,  7,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  7,  8,  9,  7,  7,  7,  7,  7,  7,  7,  7,  7, 10,
    11, 12, 13,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7, 14,  7,  7,
     7,  7,  7,  7,  7,  7,  7, 15,  7,  7, 16, 17,  7, 18, 19,  7,
     7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,
    20,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,
};

static RE_UINT8 re_case_ignorable_stage_3[] = {
     0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15,
    16,  1,  1, 17,  1,  1,  1, 18, 19, 20, 21, 22, 23, 24,  1, 25,
    26,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1, 27, 28, 29,  1,
    30,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
    31,  1,  1,  1, 32,  1, 33, 34, 35, 36, 37, 38,  1,  1,  1,  1,
     1,  1,  1, 39,  1,  1, 40, 41,  1, 42, 43, 44,  1,  1,  1,  1,
     1,  1, 45,  1,  1,  1,  1,  1, 46, 47, 48, 49, 50, 51, 52, 53,
     1,  1, 54, 55,  1,  1,  1, 56,  1,  1,  1,  1, 57,  1,  1,  1,
     1, 58, 59,  1,  1,  1,  1,  1,  1,  1, 60,  1,  1,  1,  1,  1,
    61,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1, 62,  1,  1,  1,  1,
    63, 64,  1,  1,  1,  1,  1,  1,
};

static RE_UINT8 re_case_ignorable_stage_4[] = {
      0,   1,   2,   3,   0,   4,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   5,   6,   6,   6,   6,   6,   7,   8,   0,   0,   0,
      0,   0,   0,   0,   9,   0,   0,   0,   0,   0,  10,   0,  11,  12,  13,  14,
     15,   0,  16,  17,   0,   0,  18,  19,  20,   5,  21,   0,   0,  22,   0,  23,
     24,  25,  26,   0,   0,   0,   0,  27,  28,  29,  30,  31,  32,  33,  34,  35,
     36,  33,  37,  38,  36,  33,  39,  35,  32,  40,  41,  35,  42,   0,  43,   0,
      3,  44,  45,  35,  32,  40,  46,  35,  32,   0,  34,  35,   0,   0,  47,   0,
      0,  48,  49,   0,   0,  50,  51,   0,  52,  53,   0,  54,  55,  56,  57,   0,
      0,  58,  59,  60,  61,   0,   0,  33,   0,   0,  62,   0,   0,   0,   0,   0,
     63,  63,  64,  64,   0,  65,  66,   0,  67,   0,  68,   0,   0,  69,   0,   0,
      0,  70,   0,   0,   0,   0,   0,   0,  71,   0,  72,  73,   0,  74,   0,   0,
     75,  76,  42,  77,  78,  79,   0,  80,   0,  81,   0,  82,   0,   0,  83,  84,
      0,  85,   6,  86,  87,   6,   6,  88,   0,   0,   0,   0,   0,  89,  90,  91,
     92,  93,   0,  94,  95,   0,   5,  96,   0,   0,   0,  97,   0,   0,   0,  98,
      0,   0,   0,  99,   0,   0,   0,   6,   0, 100,   0,   0,   0,   0,   0,   0,
    101, 102,   0,   0, 103,   0,   0, 104, 105,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,  82, 106,   0,   0, 107, 108,   0,   0, 109,
      6,  78,   0,  17, 110,   0,   0,  52, 111, 112,   0,   0,   0,   0, 113, 114,
      0, 115, 116,   0,  28, 117, 100, 112,   0, 118, 119, 120,   0, 121, 122, 123,
      0,   0,  87,   0,   0,   0,   0, 124,   2,   0,   0,   0,   0, 125,  78,   0,
    126, 127, 128,   0,   0,   0,   0, 129,   1,   2,   3,  17,  44,   0,   0, 130,
      0,   0,   0,   0,   0,   0,   0, 131,   0,   0,   0,   0,   0,   0,   0,   3,
      0,   0,   0, 132,   0,   0,   0,   0, 133, 134,   0,   0,   0,   0,   0, 112,
     32, 135, 136, 129,  78, 137,   0,   0,  28, 138,   0, 139,  78, 140, 141,   0,
      0, 142,   0,   0,   0,   0, 129, 143,  78,  33,   3, 144,   0,   0,   0,   0,
      0,   0,   0,   0,   0, 145, 146,   0,   0,   0,   0,   0,   0, 147, 148,   0,
      0, 149,   3,   0,   0, 150,   0,   0,  62, 151,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0, 152,   0, 153,  75,   0,   0,   0,   0,   0,
      0,   0,   0,   0, 154,   0,   0,   0,   0,   0,   0,   0, 155,  75,   0,   0,
      0,   0,   0, 156, 157, 158,   0,   0,   0,   0, 159,   0,   0,   0,   0,   0,
      6, 160,   6, 161, 162, 163,   0,   0,   0,   0,   0,   0,   0,   0, 153,   0,
      0,   0,   0,   0,   0,   0,   0,  87,  32,   6,   6,   6,   0,   0,   0,   0,
      6,   6,   6,   6,   6,   6,   6, 127,
};

static RE_UINT8 re_case_ignorable_stage_5[] = {
      0,   0,   0,   0, 128,  64,   0,   4,   0,   0,   0,  64,   1,   0,   0,   0,
      0, 161, 144,   1,   0,   0, 255, 255, 255, 255, 255, 255, 255, 255,  48,   4,
    176,   0,   0,   0, 248,   3,   0,   0,   0,   0,   0,   2,   0,   0, 254, 255,
    255, 255, 255, 191, 182,   0,   0,   0,   0,   0,  16,   0,  63,   0, 255,  23,
      1, 248, 255, 255,   0,   0,   1,   0,   0,   0, 192, 191, 255,  61,   0,   0,
      0, 128,   2,   0, 255,   7,   0,   0, 192, 255,   1,   0,   0, 248,  63,   4,
      0,   0, 192, 255, 255,  63,   0,   0,   0,   0,   0,  14, 248, 255, 255, 255,
      7,   0,   0,   0,   0,   0,   0,  20, 254,  33, 254,   0,  12,   0,   2,   0,
      2,   0,   0,   0,   0,   0,   0,  16,  30,  32,   0,   0,  12,   0,   0,   0,
      6,   0,   0,   0, 134,  57,   2,   0,   0,   0,  35,   0, 190,  33,   0,   0,
      0,   0,   0, 144,  30,  32,  64,   0,   4,   0,   0,   0,   1,  32,   0,   0,
      0,   0,   0, 192, 193,  61,  96,   0,  64,  48,   0,   0,   0,   4,  92,   0,
      0,   0, 242,   7, 192, 127,   0,   0,   0,   0, 242,  27,  64,  63,   0,   0,
      0,   0,   0,   3,   0,   0, 160,   2,   0,   0, 254, 127, 223, 224, 255, 254,
    255, 255, 255,  31,  64,   0,   0,   0,   0, 224, 253, 102,   0,   0,   0, 195,
      1,   0,  30,   0, 100,  32,   0,  32,   0,   0,   0, 224,   0,   0,  28,   0,
      0,   0,  12,   0,   0,   0, 176,  63,  64, 254, 143,  32,   0, 120,   0,   0,
      8,   0,   0,   0,   0,   2,   0,   0, 135,   1,   4,  14,   0,   0, 128,   9,
      0,   0,  64, 127, 229,  31, 248, 159, 128,   0, 255, 127,  15,   0,   0,   0,
      0,   0, 208,  23,   0, 248,  15,   0,   3,   0,   0,   0,  60,  59,   0,   0,
     64, 163,   3,   0,   0, 240, 207,   0,   0,   0,   0,  63,   0,   0, 247, 255,
    253,  33,  16,   3,   0, 240, 255, 255, 255,   7,   0,   1,   0,   0,   0, 248,
    255, 255,  63, 240,   0,   0,   0, 160,   3, 224,   0, 224,   0, 224,   0,  96,
      0, 248,   0,   3, 144, 124,   0,   0, 223, 255,   2, 128,   0,   0, 255,  31,
    255, 255,   1,   0,   0,   0,   0,  48,   0, 128,   3,   0,   0, 128,   0, 128,
      0, 128,   0,   0,  32,   0,   0,   0,   0,  60,  62,   8,   0,   0,   0, 126,
      0,   0,   0, 112,   0,   0,  32,   0,   0,  16,   0,   0,   0, 128, 247, 191,
      0,   0,   0, 240,   0,   0,   3,   0,   0,   7,   0,   0,  68,   8,   0,   0,
     96,   0,   0,   0,  16,   0,   0,   0, 255, 255,   3,   0, 192,  63,   0,   0,
    128, 255,   3,   0,   0,   0, 200,  19,   0, 126, 102,   0,   8,  16,   0,   0,
      0,   0,   1,  16,   0,   0, 157, 193,   2,   0,   0,  32,   0,  48,  88,   0,
     32,  33,   0,   0,   0,   0, 252, 255, 255, 255,   8,   0, 255, 255,   0,   0,
      0,   0,  36,   0,   0,   0,   0, 128,   8,   0,   0,  14,   0,   0,   0,  32,
      0,   0, 192,   7, 110, 240,   0,   0,   0,   0,   0, 135,   0,   0,   0, 255,
    127,   0,   0,   0,   0,   0, 120,  38, 128, 239,  31,   0,   0,   0,   8,   0,
      0,   0, 192, 127,   0,  28,   0,   0,   0, 128, 211,   0, 248,   7,   0,   0,
    192,  31,  31,   0,   0,   0, 248, 133,  13,   0,   0,   0,   0,   0,  60, 176,
      1,   0,   0,  48,   0,   0, 248, 167,   0,  40, 191,   0, 188,  15,   0,   0,
      0,   0,  31,   0,   0,   0, 127,   0,   0, 128, 255, 255,   0,   0,   0,  96,
    128,   3, 248, 255, 231,  15,   0,   0,   0,  60,   0,   0,  28,   0,   0,   0,
    255, 255, 127, 248, 255,  31,  32,   0,  16,   0,   0, 248, 254, 255,   0,   0,
};

/* Case_Ignorable: 1474 bytes. */

RE_UINT32 re_get_case_ignorable(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 15;
    code = ch ^ (f << 15);
    pos = (RE_UINT32)re_case_ignorable_stage_1[f] << 4;
    f = code >> 11;
    code ^= f << 11;
    pos = (RE_UINT32)re_case_ignorable_stage_2[pos + f] << 3;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_case_ignorable_stage_3[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_case_ignorable_stage_4[pos + f] << 5;
    pos += code;
    value = (re_case_ignorable_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Changes_When_Lowercased. */

static RE_UINT8 re_changes_when_lowercased_stage_1[] = {
    0, 1, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
    3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
    3, 3,
};

static RE_UINT8 re_changes_when_lowercased_stage_2[] = {
     0,  1,  2,  3,  4,  5,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  6,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  7,
     8,  9,  1, 10,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
};

static RE_UINT8 re_changes_when_lowercased_stage_3[] = {
     0,  1,  2,  3,  4,  5,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     7,  6,  6,  8,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  9, 10,
     6, 11,  6,  6, 12,  6,  6,  6,  6,  6,  6,  6, 13,  6,  6,  6,
     6,  6,  6,  6,  6,  6, 14, 15,  6,  6,  6,  6,  6,  6,  6, 16,
     6,  6,  6,  6, 17,  6,  6,  6,  6,  6,  6,  6, 18,  6,  6,  6,
    19,  6,  6,  6,  6,  6,  6,  6,
};

static RE_UINT8 re_changes_when_lowercased_stage_4[] = {
     0,  0,  1,  0,  0,  0,  2,  0,  3,  4,  5,  6,  7,  8,  9, 10,
     3, 11, 12,  0,  0,  0,  0,  0,  0,  0,  0, 13, 14, 15, 16, 17,
    18, 19,  0,  3, 20,  3, 21,  3,  3, 22, 23,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 18, 24,  0,
     0,  0,  0,  0,  0, 18, 18, 25,  3,  3,  3,  3, 26,  3,  3,  3,
    27, 28, 29, 30, 28, 31, 32, 33,  0, 34,  0, 19, 35,  0,  0,  0,
     0,  0,  0,  0,  0, 36, 19,  0, 18, 37,  0, 38,  3,  3,  3, 39,
     0,  0,  3, 40, 41,  0,  0,  0,  0, 42,  3, 43, 44, 45,  0,  0,
     0,  1,  0,  0,  0,  0,  0,  0, 18, 46,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0, 18, 47,  0,  0,  0,  0,  0,  0,  0, 18,  0,  0,
};

static RE_UINT8 re_changes_when_lowercased_stage_5[] = {
      0,   0,   0,   0, 254, 255, 255,   7, 255, 255, 127, 127,  85,  85,  85,  85,
     85,  85,  85, 170, 170,  84,  85,  85,  85,  85,  85,  43, 214, 206, 219, 177,
    213, 210, 174,  17, 176, 173, 170,  74,  85,  85, 214,  85,  85,  85,   5, 108,
    122,  85,   0,   0,   0,   0,  69, 128,  64, 215, 254, 255, 251,  15,   0,   0,
      0, 128,   0,  85,  85,  85, 144, 230, 255, 255, 255, 255, 255, 255,   0,   0,
      1,  84,  85,  85, 171,  42,  85,  85,  85,  85, 254, 255, 255, 255, 127,   0,
    191,  32,   0,   0, 255, 255,  63,   0,  85,  85,  21,  64,   0, 255,   0,  63,
      0, 255,   0, 255,   0,  63,   0, 170,   0, 255,   0,   0,   0, 255,   0,  31,
      0,  31,   0,  15,   0,  31,   0,  31,  64,  12,   4,   0,   8,   0,   0,   0,
      0,   0, 192, 255, 255, 127,   0,   0, 157, 234,  37, 192,   5,  40,   4,   0,
     85,  21,   0,   0,  85,  85,  85,   5,  84,  85,  84,  85,  85,  85,   0, 106,
     85,  40,  69,  85,  85,  61,  95,   0, 255,   0,   0,   0, 255, 255,   7,   0,
};

/* Changes_When_Lowercased: 538 bytes. */

RE_UINT32 re_get_changes_when_lowercased(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 15;
    code = ch ^ (f << 15);
    pos = (RE_UINT32)re_changes_when_lowercased_stage_1[f] << 4;
    f = code >> 11;
    code ^= f << 11;
    pos = (RE_UINT32)re_changes_when_lowercased_stage_2[pos + f] << 3;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_changes_when_lowercased_stage_3[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_changes_when_lowercased_stage_4[pos + f] << 5;
    pos += code;
    value = (re_changes_when_lowercased_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Changes_When_Uppercased. */

static RE_UINT8 re_changes_when_uppercased_stage_1[] = {
    0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2,
};

static RE_UINT8 re_changes_when_uppercased_stage_2[] = {
    0, 1, 2, 3, 3, 3, 3, 3, 3, 3, 4, 3, 3, 3, 3, 5,
    6, 7, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
    3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
};

static RE_UINT8 re_changes_when_uppercased_stage_3[] = {
     0,  1,  2,  3,  4,  5,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     6,  6,  6,  7,  6,  6,  6,  6,  6,  6,  6,  6,  6,  8,  9, 10,
     6, 11,  6,  6, 12,  6,  6,  6,  6,  6,  6,  6, 13, 14,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     6,  6,  6,  6,  6,  6, 15, 16,  6,  6,  6, 17,  6,  6,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6, 18,  6,  6,  6, 19,
     6,  6,  6,  6, 20,  6,  6,  6,  6,  6,  6,  6, 21,  6,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6, 22,  6,  6,  6,  6,  6,  6,  6,
};

static RE_UINT8 re_changes_when_uppercased_stage_4[] = {
     0,  0,  0,  1,  0,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12,
     5, 13, 14, 15, 16,  0,  0,  0,  0,  0, 17, 18, 19, 20, 21, 22,
     0, 23, 24,  5, 25,  5, 26,  5,  5, 27,  0, 28, 29,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 30,
     0,  0,  0, 31,  0,  0,  0,  0,  5,  5,  5,  5, 32,  5,  5,  5,
    33, 34, 35, 36, 24, 37, 38, 39,  0,  0, 40, 23, 41,  0,  0,  0,
     0,  0,  0,  0,  0,  0, 23, 42,  0, 23, 43, 44,  5,  5,  5, 45,
    24, 46,  0,  0,  0,  0,  0,  0,  0,  0,  5, 47, 48,  0,  0,  0,
     0, 49,  5, 50, 51, 52,  0,  0,  0,  0, 53, 23, 24, 24,  0,  0,
    54,  0,  0,  0,  0,  0,  0,  0,  0,  0,  1,  0,  0,  0,  0,  0,
     0, 55, 56,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 24, 57,
     0,  0,  0,  0,  0,  0, 24,  0,
};

static RE_UINT8 re_changes_when_uppercased_stage_5[] = {
      0,   0,   0,   0, 254, 255, 255,   7,   0,   0,  32,   0,   0,   0,   0, 128,
    255, 255, 127, 255, 170, 170, 170, 170, 170, 170, 170,  84,  85, 171, 170, 170,
    170, 170, 170, 212,  41,  17,  36,  70,  42,  33,  81, 162,  96,  91,  85, 181,
    170, 170,  45, 170, 168, 170,  10, 144, 133, 170, 223,  26, 107, 155,  38,  32,
    137,  31,   4,  96,  32,   0,   0,   0,   0,   0, 138,  56,   0,   0,   1,   0,
      0, 240, 255, 255, 255, 127, 227, 170, 170, 170,  47,   9,   0,   0, 255, 255,
    255, 255, 255, 255,   2, 168, 170, 170,  84, 213, 170, 170, 170, 170,   0,   0,
    254, 255, 255, 255, 255,   0,   0,   0,   0,   0,   0,  63,   0,   0,   0,  34,
    170, 170, 234,  15, 255,   0,  63,   0, 255,   0, 255,   0,  63,   0, 255,   0,
    255,   0, 255,  63, 255, 255, 223,  80, 220,  16, 207,   0, 255,   0, 220,  16,
      0,  64,   0,   0,  16,   0,   0,   0, 255,   3,   0,   0, 255, 255, 255, 127,
     98,  21,  72,   0,  10,  80,   8,   0, 191,  32,   0,   0, 170,  42,   0,   0,
    170, 170, 170,  10, 168, 170, 168, 170, 170, 170,   0, 148, 170,  16, 138, 170,
    170,   2, 160,   0,   0,   0,   8,   0, 127,   0, 248,   0,   0, 255, 255, 255,
    255, 255,   0,   0, 255, 255,   7,   0,
};

/* Changes_When_Uppercased: 609 bytes. */

RE_UINT32 re_get_changes_when_uppercased(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_changes_when_uppercased_stage_1[f] << 4;
    f = code >> 12;
    code ^= f << 12;
    pos = (RE_UINT32)re_changes_when_uppercased_stage_2[pos + f] << 4;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_changes_when_uppercased_stage_3[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_changes_when_uppercased_stage_4[pos + f] << 5;
    pos += code;
    value = (re_changes_when_uppercased_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Changes_When_Titlecased. */

static RE_UINT8 re_changes_when_titlecased_stage_1[] = {
    0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2,
};

static RE_UINT8 re_changes_when_titlecased_stage_2[] = {
    0, 1, 2, 3, 3, 3, 3, 3, 3, 3, 4, 3, 3, 3, 3, 5,
    6, 7, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
    3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
};

static RE_UINT8 re_changes_when_titlecased_stage_3[] = {
     0,  1,  2,  3,  4,  5,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     6,  6,  6,  7,  6,  6,  6,  6,  6,  6,  6,  6,  6,  8,  9, 10,
     6, 11,  6,  6, 12,  6,  6,  6,  6,  6,  6,  6, 13, 14,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     6,  6,  6,  6,  6,  6, 15, 16,  6,  6,  6, 17,  6,  6,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6, 18,  6,  6,  6, 19,
     6,  6,  6,  6, 20,  6,  6,  6,  6,  6,  6,  6, 21,  6,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6, 22,  6,  6,  6,  6,  6,  6,  6,
};

static RE_UINT8 re_changes_when_titlecased_stage_4[] = {
     0,  0,  0,  1,  0,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12,
     5, 13, 14, 15, 16,  0,  0,  0,  0,  0, 17, 18, 19, 20, 21, 22,
     0, 23, 24,  5, 25,  5, 26,  5,  5, 27,  0, 28, 29,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 30,
     0,  0,  0, 31,  0,  0,  0,  0,  5,  5,  5,  5, 32,  5,  5,  5,
    33, 34, 35, 36, 34, 37, 38, 39,  0,  0, 40, 23, 41,  0,  0,  0,
     0,  0,  0,  0,  0,  0, 23, 42,  0, 23, 43, 44,  5,  5,  5, 45,
    24, 46,  0,  0,  0,  0,  0,  0,  0,  0,  5, 47, 48,  0,  0,  0,
     0, 49,  5, 50, 51, 52,  0,  0,  0,  0, 53, 23, 24, 24,  0,  0,
    54,  0,  0,  0,  0,  0,  0,  0,  0,  0,  1,  0,  0,  0,  0,  0,
     0, 55, 56,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 24, 57,
     0,  0,  0,  0,  0,  0, 24,  0,
};

static RE_UINT8 re_changes_when_titlecased_stage_5[] = {
      0,   0,   0,   0, 254, 255, 255,   7,   0,   0,  32,   0,   0,   0,   0, 128,
    255, 255, 127, 255, 170, 170, 170, 170, 170, 170, 170,  84,  85, 171, 170, 170,
    170, 170, 170, 212,  41,  17,  36,  70,  42,  33,  81, 162, 208,  86,  85, 181,
    170, 170,  43, 170, 168, 170,  10, 144, 133, 170, 223,  26, 107, 155,  38,  32,
    137,  31,   4,  96,  32,   0,   0,   0,   0,   0, 138,  56,   0,   0,   1,   0,
      0, 240, 255, 255, 255, 127, 227, 170, 170, 170,  47,   9,   0,   0, 255, 255,
    255, 255, 255, 255,   2, 168, 170, 170,  84, 213, 170, 170, 170, 170,   0,   0,
    254, 255, 255, 255, 255,   0,   0,   0,   0,   0,   0,  63,   0,   0,   0,  34,
    170, 170, 234,  15, 255,   0,  63,   0, 255,   0, 255,   0,  63,   0, 255,   0,
    255,   0, 255,  63, 255,   0, 223,  64, 220,   0, 207,   0, 255,   0, 220,   0,
      0,  64,   0,   0,  16,   0,   0,   0, 255,   3,   0,   0, 255, 255, 255, 127,
     98,  21,  72,   0,  10,  80,   8,   0, 191,  32,   0,   0, 170,  42,   0,   0,
    170, 170, 170,  10, 168, 170, 168, 170, 170, 170,   0, 148, 170,  16, 138, 170,
    170,   2, 160,   0,   0,   0,   8,   0, 127,   0, 248,   0,   0, 255, 255, 255,
    255, 255,   0,   0, 255, 255,   7,   0,
};

/* Changes_When_Titlecased: 609 bytes. */

RE_UINT32 re_get_changes_when_titlecased(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_changes_when_titlecased_stage_1[f] << 4;
    f = code >> 12;
    code ^= f << 12;
    pos = (RE_UINT32)re_changes_when_titlecased_stage_2[pos + f] << 4;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_changes_when_titlecased_stage_3[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_changes_when_titlecased_stage_4[pos + f] << 5;
    pos += code;
    value = (re_changes_when_titlecased_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Changes_When_Casefolded. */

static RE_UINT8 re_changes_when_casefolded_stage_1[] = {
    0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2,
};

static RE_UINT8 re_changes_when_casefolded_stage_2[] = {
    0, 1, 2, 3, 3, 3, 3, 3, 3, 3, 4, 3, 3, 3, 3, 5,
    6, 7, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
    3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
};

static RE_UINT8 re_changes_when_casefolded_stage_3[] = {
     0,  1,  2,  3,  4,  5,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     7,  6,  6,  8,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  9, 10,
     6, 11,  6,  6, 12,  6,  6,  6,  6,  6,  6,  6, 13,  6,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     6,  6,  6,  6,  6,  6, 14, 15,  6,  6,  6, 16,  6,  6,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6, 17,  6,  6,  6, 18,
     6,  6,  6,  6, 19,  6,  6,  6,  6,  6,  6,  6, 20,  6,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6, 21,  6,  6,  6,  6,  6,  6,  6,
};

static RE_UINT8 re_changes_when_casefolded_stage_4[] = {
     0,  0,  1,  0,  0,  2,  3,  0,  4,  5,  6,  7,  8,  9, 10, 11,
     4, 12, 13,  0,  0,  0,  0,  0,  0,  0, 14, 15, 16, 17, 18, 19,
    20, 21,  0,  4, 22,  4, 23,  4,  4, 24, 25,  0, 26,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 20, 27,  0,
     0,  0,  0,  0,  0,  0,  0, 28,  4,  4,  4,  4, 29,  4,  4,  4,
    30, 31, 32, 33, 20, 34, 35, 36,  0, 37,  0, 21, 38,  0,  0,  0,
     0,  0,  0,  0,  0, 39, 21,  0, 20, 40,  0, 41,  4,  4,  4, 42,
     0,  0,  4, 43, 44,  0,  0,  0,  0, 45,  4, 46, 47, 48,  0,  0,
     0,  0,  0, 49, 20, 20,  0,  0, 50,  0,  0,  0,  0,  0,  0,  0,
     0,  1,  0,  0,  0,  0,  0,  0, 20, 51,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0, 20, 52,  0,  0,  0,  0,  0,  0,  0, 20,  0,  0,
};

static RE_UINT8 re_changes_when_casefolded_stage_5[] = {
      0,   0,   0,   0, 254, 255, 255,   7,   0,   0,  32,   0, 255, 255, 127, 255,
     85,  85,  85,  85,  85,  85,  85, 170, 170,  86,  85,  85,  85,  85,  85, 171,
    214, 206, 219, 177, 213, 210, 174,  17, 176, 173, 170,  74,  85,  85, 214,  85,
     85,  85,   5, 108, 122,  85,   0,   0,  32,   0,   0,   0,   0,   0,  69, 128,
     64, 215, 254, 255, 251,  15,   0,   0,   4, 128,  99,  85,  85,  85, 179, 230,
    255, 255, 255, 255, 255, 255,   0,   0,   1,  84,  85,  85, 171,  42,  85,  85,
     85,  85, 254, 255, 255, 255, 127,   0, 128,   0,   0,   0, 191,  32,   0,   0,
      0,   0,   0,  63,  85,  85,  21,  76,   0, 255,   0,  63,   0, 255,   0, 255,
      0,  63,   0, 170,   0, 255,   0,   0, 255, 255, 156,  31, 156,  31,   0,  15,
      0,  31, 156,  31,  64,  12,   4,   0,   8,   0,   0,   0,   0,   0, 192, 255,
    255, 127,   0,   0, 157, 234,  37, 192,   5,  40,   4,   0,  85,  21,   0,   0,
     85,  85,  85,   5,  84,  85,  84,  85,  85,  85,   0, 106,  85,  40,  69,  85,
     85,  61,  95,   0,   0,   0, 255, 255, 127,   0, 248,   0, 255,   0,   0,   0,
    255, 255,   7,   0,
};

/* Changes_When_Casefolded: 581 bytes. */

RE_UINT32 re_get_changes_when_casefolded(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_changes_when_casefolded_stage_1[f] << 4;
    f = code >> 12;
    code ^= f << 12;
    pos = (RE_UINT32)re_changes_when_casefolded_stage_2[pos + f] << 4;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_changes_when_casefolded_stage_3[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_changes_when_casefolded_stage_4[pos + f] << 5;
    pos += code;
    value = (re_changes_when_casefolded_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Changes_When_Casemapped. */

static RE_UINT8 re_changes_when_casemapped_stage_1[] = {
    0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2,
};

static RE_UINT8 re_changes_when_casemapped_stage_2[] = {
    0, 1, 2, 3, 3, 3, 3, 3, 3, 3, 4, 3, 3, 3, 3, 5,
    6, 7, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
    3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
};

static RE_UINT8 re_changes_when_casemapped_stage_3[] = {
     0,  1,  2,  3,  4,  5,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     7,  6,  6,  8,  6,  6,  6,  6,  6,  6,  6,  6,  6,  9, 10, 11,
     6, 12,  6,  6, 13,  6,  6,  6,  6,  6,  6,  6, 14, 15,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     6,  6,  6,  6,  6,  6, 16, 17,  6,  6,  6, 18,  6,  6,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6, 19,  6,  6,  6, 20,
     6,  6,  6,  6, 21,  6,  6,  6,  6,  6,  6,  6, 22,  6,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6, 23,  6,  6,  6,  6,  6,  6,  6,
};

static RE_UINT8 re_changes_when_casemapped_stage_4[] = {
     0,  0,  1,  1,  0,  2,  3,  3,  4,  5,  4,  4,  6,  7,  8,  4,
     4,  9, 10, 11, 12,  0,  0,  0,  0,  0, 13, 14, 15, 16, 17, 18,
     4,  4,  4,  4, 19,  4,  4,  4,  4, 20, 21, 22, 23,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  4, 24,  0,
     0,  0,  0,  0,  0,  4,  4, 25,  0,  0,  0, 26,  0,  0,  0,  0,
     4,  4,  4,  4, 27,  4,  4,  4, 25,  4, 28, 29,  4, 30, 31, 32,
     0, 33, 34,  4, 35,  0,  0,  0,  0,  0,  0,  0,  0, 36,  4, 37,
     4, 38, 39, 40,  4,  4,  4, 41,  4, 24,  0,  0,  0,  0,  0,  0,
     0,  0,  4, 42, 43,  0,  0,  0,  0, 44,  4, 45, 46, 47,  0,  0,
     0,  0, 48, 49,  4,  4,  0,  0, 50,  0,  0,  0,  0,  0,  0,  0,
     0,  1,  1,  0,  0,  0,  0,  0,  4,  4, 51,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  4, 52,  4, 52,  0,  0,  0,  0,  0,  4,  4,  0,
};

static RE_UINT8 re_changes_when_casemapped_stage_5[] = {
      0,   0,   0,   0, 254, 255, 255,   7,   0,   0,  32,   0, 255, 255, 127, 255,
    255, 255, 255, 255, 255, 255, 255, 254, 255, 223, 255, 247, 255, 243, 255, 179,
    240, 255, 255, 255, 253, 255,  15, 252, 255, 255, 223,  26, 107, 155,  38,  32,
    137,  31,   4,  96,  32,   0,   0,   0,   0,   0, 207, 184,  64, 215, 255, 255,
    251, 255, 255, 255, 255, 255, 227, 255, 255, 255, 191, 239,   3, 252, 255, 255,
    255, 255, 254, 255, 255, 255, 127,   0, 254, 255, 255, 255, 255,   0,   0,   0,
    191,  32,   0,   0, 255, 255,  63,  63,   0,   0,   0,  34, 255, 255, 255,  79,
     63,  63, 255, 170, 255, 255, 255,  63, 255, 255, 223,  95, 220,  31, 207,  15,
    255,  31, 220,  31,  64,  12,   4,   0,   0,  64,   0,   0,  24,   0,   0,   0,
      0,   0, 192, 255, 255,   3,   0,   0, 255, 127, 255, 255, 255, 255, 255, 127,
    255, 255, 109, 192,  15, 120,  12,   0, 255,  63,   0,   0, 255, 255, 255,  15,
    252, 255, 252, 255, 255, 255,   0, 254, 255,  56, 207, 255, 255,  63, 255,   0,
      0,   0,   8,   0,   0,   0, 255, 255, 127,   0, 248,   0, 255, 255,   0,   0,
    255, 255,   7,   0,
};

/* Changes_When_Casemapped: 597 bytes. */

RE_UINT32 re_get_changes_when_casemapped(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_changes_when_casemapped_stage_1[f] << 4;
    f = code >> 12;
    code ^= f << 12;
    pos = (RE_UINT32)re_changes_when_casemapped_stage_2[pos + f] << 4;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_changes_when_casemapped_stage_3[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_changes_when_casemapped_stage_4[pos + f] << 5;
    pos += code;
    value = (re_changes_when_casemapped_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* ID_Start. */

static RE_UINT8 re_id_start_stage_1[] = {
    0, 1, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
    3,
};

static RE_UINT8 re_id_start_stage_2[] = {
     0,  1,  2,  3,  4,  5,  6,  7,  7,  8,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  9, 10, 11,  7,  7,  7,  7, 12, 13, 13, 13, 13, 14,
    15, 16, 17, 18, 19, 13, 20, 13, 21, 13, 13, 13, 13, 22, 13, 13,
    13, 13, 13, 13, 13, 13, 23, 24, 13, 13, 25, 13, 13, 26, 13, 13,
     7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  7, 27,  7, 28, 29,  7, 30, 13, 13, 13, 13, 13, 31,
    13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13,
    13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13,
};

static RE_UINT8 re_id_start_stage_3[] = {
     0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15,
    16,  1, 17, 18, 19,  1, 20, 21, 22, 23, 24, 25, 26, 27,  1, 28,
    29, 30, 31, 31, 31, 31, 31, 31, 31, 31, 31, 31, 32, 33, 31, 31,
    34, 35, 31, 31,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1, 36,  1,  1,  1,  1,  1,  1,  1,  1,  1, 37,
     1,  1,  1,  1, 38,  1, 39, 40, 41, 42, 43, 44,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1, 45, 31, 31, 31, 31, 31, 31, 31, 31,
    31,  1, 46, 47,  1, 48, 49, 50, 51, 52, 53, 54, 55, 56,  1, 57,
    58, 59, 60, 61, 62, 31, 31, 31, 63, 64, 65, 66, 67, 68, 69, 70,
    71, 31, 72, 31, 31, 31, 31, 31,  1,  1,  1, 73, 74, 75, 31, 31,
     1,  1,  1,  1, 76, 31, 31, 31, 31, 31, 31, 31,  1,  1, 77, 31,
     1,  1, 78, 79, 31, 31, 31, 80, 81, 31, 31, 31, 31, 31, 31, 31,
    31, 31, 31, 31, 82, 31, 31, 31, 31, 31, 31, 31, 83, 84, 85, 86,
    87, 31, 31, 31, 31, 31, 88, 31,  1,  1,  1,  1,  1,  1, 89,  1,
     1,  1,  1,  1,  1,  1,  1, 90, 91,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1, 92, 31,  1,  1, 93, 31, 31, 31, 31, 31,
};

static RE_UINT8 re_id_start_stage_4[] = {
      0,   0,   1,   1,   0,   2,   3,   3,   4,   4,   4,   4,   4,   4,   4,   4,
      4,   4,   4,   4,   4,   4,   5,   6,   0,   0,   0,   7,   8,   9,   4,  10,
      4,   4,   4,   4,  11,   4,   4,   4,   4,  12,  13,  14,  15,   0,  16,  17,
      0,   4,  18,  19,   4,   4,  20,  21,  22,  23,  24,   4,   4,  25,  26,  27,
     28,  29,  30,   0,   0,  31,   0,   0,  32,  33,  34,  35,  36,  37,  38,  39,
     40,  41,  42,  43,  44,  45,  46,  47,  48,  45,  49,  50,  51,  52,  46,   0,
     53,  54,  55,  56,  53,  57,  58,  59,  53,  60,  61,  62,  63,  64,  65,   0,
     14,  66,  65,   0,  67,  68,  69,   0,  70,   0,  71,  72,  73,   0,   0,   0,
      4,  74,  75,  76,  77,   4,  78,  79,   4,   4,  80,   4,  81,  82,  83,   4,
     84,   4,  85,   0,  23,   4,   4,  86,  14,   4,   4,   4,   4,   4,   4,   4,
      4,   4,   4,  87,   1,   4,   4,  88,  89,  90,  90,  91,   4,  92,  93,   0,
      0,   4,   4,  94,   4,  95,   4,  96,  97,   0,  16,  98,   4,  99, 100,   0,
    101,   4,  31,   0,   0, 102,   0,   0, 103,  92, 104,   0, 105, 106,   4, 107,
      4, 108, 109, 110,   0,   0,   0, 111,   4,   4,   4,   4,   4,   4,   0,   0,
     86,   4, 112, 110,   4, 113, 114, 115,   0,   0,   0, 116, 117,   0,   0,   0,
    118, 119, 120,   4, 121,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      4, 122,  97,   4,   4,   4,   4, 123,   4,  78,   4, 124, 101, 125, 125,   0,
    126, 127,  14,   4, 128,  14,   4,  79, 103, 129,   4,   4, 130,  85,   0,  16,
      4,   4,   4,   4,   4,  96,   0,   0,   4,   4,   4,   4,   4,   4,  96,   0,
      4,   4,   4,   4,  72,   0,  16, 110, 131, 132,   4, 133, 110,   4,   4,  23,
    134, 135,   4,   4, 136, 137,   0, 134, 138, 139,   4,  92, 135,  92,   0, 140,
     26, 141,  65, 142,  32, 143, 144, 145,   4, 121, 146, 147,   4, 148, 149, 150,
    151, 152,  79, 141,   4,   4,   4, 139,   4,   4,   4,   4,   4, 153, 154, 155,
      4,   4,   4, 156,   4,   4, 157,   0, 158, 159, 160,   4,   4,  90, 161,   4,
      4, 110,  16,   4, 162,   4,  15, 163,   0,   0,   0, 164,   4,   4,   4, 142,
      0,   1,   1, 165,   4,  97, 166,   0, 167, 168, 169,   0,   4,   4,   4,  85,
      0,   0,   4,  31,   0,   0,   0,   0,   0,   0,   0,   0, 142,   4, 170,   0,
      4,  16, 171,  96, 110,   4, 172,   0,   4,   4,   4,   4, 110,   0,   0,   0,
      4, 173,   4, 108,   0,   0,   0,   0,   4, 101,  96,  15,   0,   0,   0,   0,
    174, 175,  96, 101,  97,   0,   0, 176,  96, 157,   0,   0,   4, 177,   0,   0,
    178,  92,   0, 142, 142,   0,  71, 179,   4,  96,  96, 143,  90,   0,   0,   0,
      4,   4, 121,   0,   4, 143,   4, 143, 105,  94,   0,   0, 105,  23,  16, 121,
    105,  65,  16, 180, 105, 143, 181,   0, 182, 183,   0,   0, 184, 185,  97,   0,
     48,  45, 186,  56,   0,   0,   0,   0,   0,   0,   0,   0,   4,  23, 187,   0,
      0,   0,   0,   0,   4, 130, 188,   0,   4,  23, 189,   0,   4,  18,   0,   0,
    157,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   4,   4, 190,
      0,   0,   0,   0,   0,   0,   4,  30,   4,   4,   4,   4, 157,   0,   0,   0,
      4,   4,   4, 130,   4,   4,   4,   4,   4,   4, 108,   0,   0,   0,   0,   0,
      4, 130,   0,   0,   0,   0,   0,   0,   4,   4,  65,   0,   0,   0,   0,   0,
      4,  30,  97,   0,   0,   0,  16, 191,   4,  23, 108, 192,  23,   0,   0,   0,
      4,   4, 193,   0, 161,   0,   0,   0,  56,   0,   0,   0,   0,   0,   0,   0,
      4,   4,   4, 194, 195,   0,   0,   0,   4,   4, 196,   4, 197, 198, 199,   4,
    200, 201, 202,   4,   4,   4,   4,   4,   4,   4,   4,   4,   4, 203, 204,  79,
    196, 196, 122, 122, 205, 205, 146,   0,   4,   4,   4,   4,   4,   4, 179,   0,
    199, 206, 207, 208, 209, 210,   0,   0,   4,   4,   4,   4,   4,   4, 101,   0,
      4,  31,   4,   4,   4,   4,   4,   4, 110,   4,   4,   4,   4,   4,   4,   4,
      4,   4,   4,   4,   4,  56,   0,   0, 110,   0,   0,   0,   0,   0,   0,   0,
};

static RE_UINT8 re_id_start_stage_5[] = {
      0,   0,   0,   0, 254, 255, 255,   7,   0,   4,  32,   4, 255, 255, 127, 255,
    255, 255, 255, 255, 195, 255,   3,   0,  31,  80,   0,   0,   0,   0, 223, 188,
     64, 215, 255, 255, 251, 255, 255, 255, 255, 255, 191, 255,   3, 252, 255, 255,
    255, 255, 254, 255, 255, 255, 127,   2, 254, 255, 255, 255, 255,   0,   0,   0,
      0,   0, 255, 255, 255,   7,   7,   0, 255,   7,   0,   0,   0, 192, 254, 255,
    255, 255,  47,   0,  96, 192,   0, 156,   0,   0, 253, 255, 255, 255,   0,   0,
      0, 224, 255, 255,  63,   0,   2,   0,   0, 252, 255, 255, 255,   7,  48,   4,
    255, 255,  63,   4,  16,   1,   0,   0, 255, 255, 255,   1, 255, 255,  31,   0,
    240, 255, 255, 255, 255, 255, 255,  35,   0,   0,   1, 255,   3,   0, 254, 255,
    225, 159, 249, 255, 255, 253, 197,  35,   0,  64,   0, 176,   3,   0,   3,   0,
    224, 135, 249, 255, 255, 253, 109,   3,   0,   0,   0,  94,   0,   0,  28,   0,
    224, 191, 251, 255, 255, 253, 237,  35,   0,   0,   1,   0,   3,   0,   0,   2,
    224, 159, 249, 255,   0,   0,   0, 176,   3,   0,   2,   0, 232, 199,  61, 214,
     24, 199, 255,   3, 224, 223, 253, 255, 255, 253, 255,  35,   0,   0,   0,   7,
      3,   0,   0,   0, 255, 253, 239,  35,   0,   0,   0,  64,   3,   0,   6,   0,
    255, 255, 255,  39,   0,  64,   0, 128,   3,   0,   0, 252, 224, 255, 127, 252,
    255, 255, 251,  47, 127,   0,   0,   0, 255, 255,  13,   0, 150,  37, 240, 254,
    174, 236,  13,  32,  95,   0,   0, 240,   1,   0,   0,   0, 255, 254, 255, 255,
    255,  31,   0,   0,   0,  31,   0,   0, 255,   7,   0, 128,   0,   0,  63,  60,
     98, 192, 225, 255,   3,  64,   0,   0, 191,  32, 255, 255, 255, 255, 255, 247,
    255,  61, 127,  61, 255,  61, 255, 255, 255, 255,  61, 127,  61, 255, 127, 255,
    255, 255,  61, 255, 255, 255, 255,   7, 255, 255,  63,  63, 255, 159, 255, 255,
    255, 199, 255,   1, 255, 223,   3,   0, 255, 255,   3,   0, 255, 223,   1,   0,
    255, 255,  15,   0,   0,   0, 128,  16, 255, 255, 255,   0, 255,   5, 255, 255,
    255, 255,  63,   0, 255, 255, 255, 127, 255,  63,  31,   0, 255,  15, 255, 255,
    255,   3,   0,   0, 255, 255, 127,   0, 128,   0,   0,   0, 224, 255, 255, 255,
    224,  15,   0,   0, 248, 255, 255, 255,   1, 192,   0, 252,  63,   0,   0,   0,
     15,   0,   0,   0,   0, 224,   0, 252, 255, 255, 255,  63,   0, 222,  99,   0,
     63,  63, 255, 170, 255, 255, 223,  95, 220,  31, 207,  15, 255,  31, 220,  31,
      0,   0,   2, 128,   0,   0, 255,  31, 132, 252,  47,  63,  80, 253, 255, 243,
    224,  67,   0,   0, 255,   1,   0,   0, 255, 127, 255, 255,  31, 120,  12,   0,
    255, 128,   0,   0, 127, 127, 127, 127, 224,   0,   0,   0, 254,   3,  62,  31,
    255, 255, 127, 248, 255,  63, 254, 255, 255, 127,   0,   0, 255,  31, 255, 255,
      0,  12,   0,   0, 255, 127,   0, 128,   0,   0, 128, 255, 252, 255, 255, 255,
    255, 249, 255, 255, 255,  63, 255,   0, 187, 247, 255, 255,   7,   0,   0,   0,
      0,   0, 252,  40,  63,   0, 255, 255, 255, 255, 255,  31, 255, 255,   7,   0,
      0, 128,   0,   0, 223, 255,   0, 124, 247,  15,   0,   0, 255, 255, 127, 196,
    255, 255,  98,  62,   5,   0,   0,  56, 255,   7,  28,   0, 126, 126, 126,   0,
    127, 127, 255, 255,  15,   0, 255, 255, 127, 248, 255, 255, 255, 255, 255,  15,
    255,  63, 255, 255, 255, 255, 255,   3, 127,   0, 248, 160, 255, 253, 127,  95,
    219, 255, 255, 255,   0,   0, 248, 255, 255, 255, 252, 255,   0,   0, 255,  15,
      0,   0, 223, 255, 192, 255, 255, 255, 252, 252, 252,  28, 255, 239, 255, 255,
    127, 255, 255, 183, 255,  63, 255,  63, 255, 255,   1,   0, 255,   7, 255, 255,
     15, 255,  62,   0, 255,   0, 255, 255,  63, 253, 255, 255, 255, 255, 191, 145,
    255, 255,  55,   0, 255, 255, 255, 192,   1,   0, 239, 254,  31,   0,   0,   0,
    255, 255,  71,   0,  30,   0,   0,  20, 255, 255, 251, 255, 255,  15,   0,   0,
    127, 189, 255, 191, 255,   1, 255, 255,   0,   0,   1, 224, 176,   0,   0,   0,
      0,   0,   0,  15,  16,   0,   0,   0,   0,   0,   0, 128, 255,  63,   0,   0,
    248, 255, 255, 224,  31,   0,   1,   0, 255,   7, 255,  31, 255,   1, 255,   3,
    255, 255, 223, 255, 255, 255, 255, 223, 100, 222, 255, 235, 239, 255, 255, 255,
    191, 231, 223, 223, 255, 255, 255, 123,  95, 252, 253, 255,  63, 255, 255, 255,
    253, 255, 255, 247, 255, 253, 255, 255, 150, 254, 247,  10, 132, 234, 150, 170,
    150, 247, 247,  94, 255, 251, 255,  15, 238, 251, 255,  15,
};

/* ID_Start: 1997 bytes. */

RE_UINT32 re_get_id_start(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_id_start_stage_1[f] << 5;
    f = code >> 11;
    code ^= f << 11;
    pos = (RE_UINT32)re_id_start_stage_2[pos + f] << 3;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_id_start_stage_3[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_id_start_stage_4[pos + f] << 5;
    pos += code;
    value = (re_id_start_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* ID_Continue. */

static RE_UINT8 re_id_continue_stage_1[] = {
    0, 1, 2, 3, 4, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6,
    6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 7, 6, 6, 6,
    6, 6,
};

static RE_UINT8 re_id_continue_stage_2[] = {
     0,  1,  2,  3,  4,  5,  6,  7,  7,  8,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  9, 10, 11,  7,  7,  7,  7, 12, 13, 13, 13, 13, 14,
    15, 16, 17, 18, 19, 13, 20, 13, 21, 13, 13, 13, 13, 22, 13, 13,
    13, 13, 13, 13, 13, 13, 23, 24, 13, 13, 25, 26, 13, 27, 13, 13,
     7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  7, 28,  7, 29, 30,  7, 31, 13, 13, 13, 13, 13, 32,
    13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13,
    33, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13,
};

static RE_UINT8 re_id_continue_stage_3[] = {
     0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15,
    16,  1, 17, 18, 19,  1, 20, 21, 22, 23, 24, 25, 26, 27,  1, 28,
    29, 30, 31, 31, 31, 31, 31, 31, 31, 31, 31, 31, 32, 33, 31, 31,
    34, 35, 31, 31,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1, 36,  1,  1,  1,  1,  1,  1,  1,  1,  1, 37,
     1,  1,  1,  1, 38,  1, 39, 40, 41, 42, 43, 44,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1, 45, 31, 31, 31, 31, 31, 31, 31, 31,
    31,  1, 46, 47,  1, 48, 49, 50, 51, 52, 53, 54, 55, 56,  1, 57,
    58, 59, 60, 61, 62, 31, 31, 31, 63, 64, 65, 66, 67, 68, 69, 70,
    71, 31, 72, 31, 31, 31, 31, 31,  1,  1,  1, 73, 74, 75, 31, 31,
     1,  1,  1,  1, 76, 31, 31, 31, 31, 31, 31, 31,  1,  1, 77, 31,
     1,  1, 78, 79, 31, 31, 31, 80, 81, 31, 31, 31, 31, 31, 31, 31,
    31, 31, 31, 31, 82, 31, 31, 31, 31, 83, 84, 31, 85, 86, 87, 88,
    31, 31, 89, 31, 31, 31, 31, 31, 90, 31, 31, 31, 31, 31, 91, 31,
     1,  1,  1,  1,  1,  1, 92,  1,  1,  1,  1,  1,  1,  1,  1, 93,
    94,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1, 95, 31,
     1,  1, 96, 31, 31, 31, 31, 31, 31, 97, 31, 31, 31, 31, 31, 31,
};

static RE_UINT8 re_id_continue_stage_4[] = {
      0,   1,   2,   3,   0,   4,   5,   5,   6,   6,   6,   6,   6,   6,   6,   6,
      6,   6,   6,   6,   6,   6,   7,   8,   6,   6,   6,   9,  10,  11,   6,  12,
      6,   6,   6,   6,  13,   6,   6,   6,   6,  14,  15,  16,  17,  18,  19,  20,
     21,   6,   6,  22,   6,   6,  23,  24,  25,   6,  26,   6,   6,  27,   6,  28,
      6,  29,  30,   0,   0,  31,   0,  32,   6,   6,   6,  33,  34,  35,  36,  37,
     38,  39,  40,  41,  42,  43,  44,  45,  46,  43,  47,  48,  49,  50,  51,  52,
     53,  54,  55,  56,  57,  58,  59,  60,  57,  61,  62,  63,  64,  65,  66,  67,
     16,  68,  69,   0,  70,  71,  72,   0,  73,  74,  75,  76,  77,  78,  79,   0,
      6,   6,  80,   6,  81,   6,  82,  83,   6,   6,  84,   6,  85,  86,  87,   6,
     88,   6,  61,  89,  90,   6,   6,  91,  16,   6,   6,   6,   6,   6,   6,   6,
      6,   6,   6,  92,   3,   6,   6,  93,  94,  31,  95,  96,   6,   6,  97,  98,
     99,   6,   6, 100,   6, 101,   6, 102, 103, 104, 105, 106,   6, 107, 108,   0,
     30,   6, 103, 109, 110, 111,   0,   0,   6,   6, 112, 113,   6,   6,   6,  95,
      6, 100, 114,  81,   0,   0, 115, 116,   6,   6,   6,   6,   6,   6,   6, 117,
     91,   6, 118,  81,   6, 119, 120, 121,   0, 122, 123, 124, 125,   0, 125, 126,
    127, 128, 129,   6, 130,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      6, 131, 103,   6,   6,   6,   6, 132,   6,  82,   6, 133, 134, 135, 135,   6,
    136, 137,  16,   6, 138,  16,   6,  83, 139, 140,   6,   6, 141,  68,   0,  25,
      6,   6,   6,   6,   6, 102,   0,   0,   6,   6,   6,   6,   6,   6, 102,   0,
      6,   6,   6,   6, 142,   0,  25,  81, 143, 144,   6, 145,   6,   6,   6,  27,
    146, 147,   6,   6, 148, 149,   0, 146,   6, 150,   6,  95,   6,   6, 151, 152,
      6, 153,  95,  78,   6,   6, 154, 103,   6, 134, 155, 156,   6,   6, 157, 158,
    159, 160,  83, 161,   6,   6,   6, 162,   6,   6,   6,   6,   6, 163, 164,  30,
      6,   6,   6, 153,   6,   6, 165,   0, 166, 167, 168,   6,   6,  27, 169,   6,
      6,  81,  25,   6, 170,   6, 150, 171,  90, 172, 173, 174,   6,   6,   6,  78,
      1,   2,   3, 105,   6, 103, 175,   0, 176, 177, 178,   0,   6,   6,   6,  68,
      0,   0,   6,  31,   0,   0,   0, 179,   0,   0,   0,   0,  78,   6, 180, 181,
      6,  25, 101,  68,  81,   6, 182,   0,   6,   6,   6,   6,  81,  98,   0,   0,
      6, 183,   6, 184,   0,   0,   0,   0,   6, 134, 102, 150,   0,   0,   0,   0,
    185, 186, 102, 134, 103,   0,   0, 187, 102, 165,   0,   0,   6, 188,   0,   0,
    189, 190,   0,  78,  78,   0,  75, 191,   6, 102, 102, 192,  27,   0,   0,   0,
      6,   6, 130,   0,   6, 192,   6, 192,   6,   6, 191, 193,   6,  68,  25, 194,
      6, 195,  25, 196,   6,   6, 197,   0, 198, 100,   0,   0, 199, 200,   6, 201,
     34,  43, 202, 203,   0,   0,   0,   0,   0,   0,   0,   0,   6,   6, 204,   0,
      0,   0,   0,   0,   6, 205, 206,   0,   6,   6, 207,   0,   6, 100,  98,   0,
    208, 112,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   6,   6, 209,
      0,   0,   0,   0,   0,   0,   6, 210,   6,   6,   6,   6, 165,   0,   0,   0,
      6,   6,   6, 141,   6,   6,   6,   6,   6,   6, 184,   0,   0,   0,   0,   0,
      6, 141,   0,   0,   0,   0,   0,   0,   6,   6, 191,   0,   0,   0,   0,   0,
      6, 210, 103,  98,   0,   0,  25, 106,   6, 134, 211, 212,  90,   0,   0,   0,
      6,   6, 213, 103, 214,   0,   0,   0, 215,   0,   0,   0,   0,   0,   0,   0,
      6,   6,   6, 216, 217,   0,   0,   0,   0,   0,   0, 218, 219, 220,   0,   0,
      0,   0, 221,   0,   0,   0,   0,   0,   6,   6, 195,   6, 222, 223, 224,   6,
    225, 226, 227,   6,   6,   6,   6,   6,   6,   6,   6,   6,   6, 228, 229,  83,
    195, 195, 131, 131, 230, 230, 231,   6,   6, 232,   6, 233, 234, 235,   0,   0,
      6,   6,   6,   6,   6,   6, 236,   0, 224, 237, 238, 239, 240, 241,   0,   0,
      6,   6,   6,   6,   6,   6, 134,   0,   6,  31,   6,   6,   6,   6,   6,   6,
     81,   6,   6,   6,   6,   6,   6,   6,   6,   6,   6,   6,   6, 215,   0,   0,
     81,   0,   0,   0,   0,   0,   0,   0,   6,   6,   6,   6,   6,   6,   6,  90,
};

static RE_UINT8 re_id_continue_stage_5[] = {
      0,   0,   0,   0,   0,   0, 255,   3, 254, 255, 255, 135, 254, 255, 255,   7,
      0,   4, 160,   4, 255, 255, 127, 255, 255, 255, 255, 255, 195, 255,   3,   0,
     31,  80,   0,   0, 255, 255, 223, 188, 192, 215, 255, 255, 251, 255, 255, 255,
    255, 255, 191, 255, 251, 252, 255, 255, 255, 255, 254, 255, 255, 255, 127,   2,
    254, 255, 255, 255, 255,   0, 254, 255, 255, 255, 255, 191, 182,   0, 255, 255,
    255,   7,   7,   0,   0,   0, 255,   7, 255, 195, 255, 255, 255, 255, 239, 159,
    255, 253, 255, 159,   0,   0, 255, 255, 255, 231, 255, 255, 255, 255,   3,   0,
    255, 255,  63,   4, 255,  63,   0,   0, 255, 255, 255,  15, 255, 255,  31,   0,
    248, 255, 255, 255, 207, 255, 254, 255, 239, 159, 249, 255, 255, 253, 197, 243,
    159, 121, 128, 176, 207, 255,   3,   0, 238, 135, 249, 255, 255, 253, 109, 211,
    135,  57,   2,  94, 192, 255,  63,   0, 238, 191, 251, 255, 255, 253, 237, 243,
    191,  59,   1,   0, 207, 255,   0,   2, 238, 159, 249, 255, 159,  57, 192, 176,
    207, 255,   2,   0, 236, 199,  61, 214,  24, 199, 255, 195, 199,  61, 129,   0,
    192, 255,   0,   0, 239, 223, 253, 255, 255, 253, 255, 227, 223,  61,  96,   7,
    207, 255,   0,   0, 238, 223, 253, 255, 255, 253, 239, 243, 223,  61,  96,  64,
    207, 255,   6,   0, 255, 255, 255, 231, 223, 125, 128, 128, 207, 255,   0, 252,
    236, 255, 127, 252, 255, 255, 251,  47, 127, 132,  95, 255, 192, 255,  12,   0,
    255, 255, 255,   7, 255, 127, 255,   3, 150,  37, 240, 254, 174, 236, 255,  59,
     95,  63, 255, 243,   1,   0,   0,   3, 255,   3, 160, 194, 255, 254, 255, 255,
    255,  31, 254, 255, 223, 255, 255, 254, 255, 255, 255,  31,  64,   0,   0,   0,
    255,   3, 255, 255, 255, 255, 255,  63, 191,  32, 255, 255, 255, 255, 255, 247,
    255,  61, 127,  61, 255,  61, 255, 255, 255, 255,  61, 127,  61, 255, 127, 255,
    255, 255,  61, 255,   0, 254,   3,   0, 255, 255,   0,   0, 255, 255,  63,  63,
    255, 159, 255, 255, 255, 199, 255,   1, 255, 223,  31,   0, 255, 255,  15,   0,
    255, 223,  13,   0, 255, 255, 143,  48, 255,   3,   0,   0,   0,  56, 255,   3,
    255, 255, 255,   0, 255,   7, 255, 255, 255, 255,  63,   0, 255, 255, 255, 127,
    255,  15, 255,  15, 192, 255, 255, 255, 255,  63,  31,   0, 255,  15, 255, 255,
    255,   3, 255,   7, 255, 255, 255, 159, 255,   3, 255,   3, 128,   0, 255,  63,
    255,  15, 255,   3,   0, 248,  15,   0, 255, 227, 255, 255,   0,   0, 247, 255,
    255, 255, 127,   3, 255, 255,  63, 240,  63,  63, 255, 170, 255, 255, 223,  95,
    220,  31, 207,  15, 255,  31, 220,  31,   0,   0,   0, 128,   1,   0,  16,   0,
      0,   0,   2, 128,   0,   0, 255,  31, 226, 255,   1,   0, 132, 252,  47,  63,
     80, 253, 255, 243, 224,  67,   0,   0, 255,   1,   0,   0, 255, 127, 255, 255,
     31, 248,  15,   0, 255, 128,   0, 128, 255, 255, 127,   0, 127, 127, 127, 127,
    224,   0,   0,   0, 254, 255,  62,  31, 255, 255, 127, 254, 224, 255, 255, 255,
    255,  63, 254, 255, 255, 127,   0,   0, 255,  31,   0,   0, 255,  31, 255, 255,
    255,  15,   0,   0, 255, 255, 240, 191,   0,   0, 128, 255, 252, 255, 255, 255,
    255, 249, 255, 255, 255,  63, 255,   0, 255,   0,   0,   0,  31,   0, 255,   3,
    255, 255, 255,  40, 255,  63, 255, 255,   1, 128, 255,   3, 255,  63, 255,   3,
    255, 255, 127, 252,   7,   0,   0,  56, 255, 255, 124,   0, 126, 126, 126,   0,
    127, 127, 255, 255,  63,   0, 255, 255, 255,  55, 255,   3,  15,   0, 255, 255,
    127, 248, 255, 255, 255, 255, 255,   3, 127,   0, 248, 224, 255, 253, 127,  95,
    219, 255, 255, 255,   0,   0, 248, 255, 255, 255, 252, 255,   0,   0, 255,  15,
    255, 255,  24,   0,   0, 224,   0,   0,   0,   0, 223, 255, 252, 252, 252,  28,
    255, 239, 255, 255, 127, 255, 255, 183, 255,  63, 255,  63,   0,   0,   0,  32,
    255, 255,   1,   0,   1,   0,   0,   0,  15, 255,  62,   0, 255,   0, 255, 255,
     15,   0,   0,   0,  63, 253, 255, 255, 255, 255, 191, 145, 255, 255,  55,   0,
    255, 255, 255, 192, 111, 240, 239, 254, 255, 255,  15, 135, 127,   0,   0,   0,
    255, 255,   7,   0, 192, 255,   0, 128, 255,   1, 255,   3, 255, 255, 223, 255,
    255, 255,  79,   0,  31,  28, 255,  23, 255, 255, 251, 255, 127, 189, 255, 191,
    255,   1, 255, 255, 255,   7, 255,   3, 159,  57, 129, 224, 207,  31,  31,   0,
    191,   0, 255,   3, 255, 255,  63, 255,   1,   0,   0,  63,  17,   0, 255,   3,
    255, 255, 255, 227, 255,   3,   0, 128, 255, 255, 255,   1,  15,   0, 255,   3,
    248, 255, 255, 224,  31,   0, 255, 255,   0, 128, 255, 255,   3,   0,   0,   0,
    255,   7, 255,  31, 255,   1, 255,  99, 224, 227,   7, 248, 231,  15,   0,   0,
      0,  60,   0,   0,  28,   0,   0,   0, 255, 255, 255, 223, 100, 222, 255, 235,
    239, 255, 255, 255, 191, 231, 223, 223, 255, 255, 255, 123,  95, 252, 253, 255,
     63, 255, 255, 255, 253, 255, 255, 247, 255, 253, 255, 255, 247, 207, 255, 255,
    255, 255, 127, 248, 255,  31,  32,   0,  16,   0,   0, 248, 254, 255,   0,   0,
     31,   0, 127,   0, 150, 254, 247,  10, 132, 234, 150, 170, 150, 247, 247,  94,
    255, 251, 255,  15, 238, 251, 255,  15,
};

/* ID_Continue: 2186 bytes. */

RE_UINT32 re_get_id_continue(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 15;
    code = ch ^ (f << 15);
    pos = (RE_UINT32)re_id_continue_stage_1[f] << 4;
    f = code >> 11;
    code ^= f << 11;
    pos = (RE_UINT32)re_id_continue_stage_2[pos + f] << 3;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_id_continue_stage_3[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_id_continue_stage_4[pos + f] << 5;
    pos += code;
    value = (re_id_continue_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* XID_Start. */

static RE_UINT8 re_xid_start_stage_1[] = {
    0, 1, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
    3,
};

static RE_UINT8 re_xid_start_stage_2[] = {
     0,  1,  2,  3,  4,  5,  6,  7,  7,  8,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  9, 10, 11,  7,  7,  7,  7, 12, 13, 13, 13, 13, 14,
    15, 16, 17, 18, 19, 13, 20, 13, 21, 13, 13, 13, 13, 22, 13, 13,
    13, 13, 13, 13, 13, 13, 23, 24, 13, 13, 25, 13, 13, 26, 13, 13,
     7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  7, 27,  7, 28, 29,  7, 30, 13, 13, 13, 13, 13, 31,
    13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13,
    13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13,
};

static RE_UINT8 re_xid_start_stage_3[] = {
     0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15,
    16,  1, 17, 18, 19,  1, 20, 21, 22, 23, 24, 25, 26, 27,  1, 28,
    29, 30, 31, 31, 31, 31, 31, 31, 31, 31, 31, 31, 32, 33, 31, 31,
    34, 35, 31, 31,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1, 36,  1,  1,  1,  1,  1,  1,  1,  1,  1, 37,
     1,  1,  1,  1, 38,  1, 39, 40, 41, 42, 43, 44,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1, 45, 31, 31, 31, 31, 31, 31, 31, 31,
    31,  1, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57,  1, 58,
    59, 60, 61, 62, 63, 31, 31, 31, 64, 65, 66, 67, 68, 69, 70, 71,
    72, 31, 73, 31, 31, 31, 31, 31,  1,  1,  1, 74, 75, 76, 31, 31,
     1,  1,  1,  1, 77, 31, 31, 31, 31, 31, 31, 31,  1,  1, 78, 31,
     1,  1, 79, 80, 31, 31, 31, 81, 82, 31, 31, 31, 31, 31, 31, 31,
    31, 31, 31, 31, 83, 31, 31, 31, 31, 31, 31, 31, 84, 85, 86, 87,
    88, 31, 31, 31, 31, 31, 89, 31,  1,  1,  1,  1,  1,  1, 90,  1,
     1,  1,  1,  1,  1,  1,  1, 91, 92,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1, 93, 31,  1,  1, 94, 31, 31, 31, 31, 31,
};

static RE_UINT8 re_xid_start_stage_4[] = {
      0,   0,   1,   1,   0,   2,   3,   3,   4,   4,   4,   4,   4,   4,   4,   4,
      4,   4,   4,   4,   4,   4,   5,   6,   0,   0,   0,   7,   8,   9,   4,  10,
      4,   4,   4,   4,  11,   4,   4,   4,   4,  12,  13,  14,  15,   0,  16,  17,
      0,   4,  18,  19,   4,   4,  20,  21,  22,  23,  24,   4,   4,  25,  26,  27,
     28,  29,  30,   0,   0,  31,   0,   0,  32,  33,  34,  35,  36,  37,  38,  39,
     40,  41,  42,  43,  44,  45,  46,  47,  48,  45,  49,  50,  51,  52,  46,   0,
     53,  54,  55,  56,  53,  57,  58,  59,  53,  60,  61,  62,  63,  64,  65,   0,
     14,  66,  65,   0,  67,  68,  69,   0,  70,   0,  71,  72,  73,   0,   0,   0,
      4,  74,  75,  76,  77,   4,  78,  79,   4,   4,  80,   4,  81,  82,  83,   4,
     84,   4,  85,   0,  23,   4,   4,  86,  14,   4,   4,   4,   4,   4,   4,   4,
      4,   4,   4,  87,   1,   4,   4,  88,  89,  90,  90,  91,   4,  92,  93,   0,
      0,   4,   4,  94,   4,  95,   4,  96,  97,   0,  16,  98,   4,  99, 100,   0,
    101,   4,  31,   0,   0, 102,   0,   0, 103,  92, 104,   0, 105, 106,   4, 107,
      4, 108, 109, 110,   0,   0,   0, 111,   4,   4,   4,   4,   4,   4,   0,   0,
     86,   4, 112, 110,   4, 113, 114, 115,   0,   0,   0, 116, 117,   0,   0,   0,
    118, 119, 120,   4, 121,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      4, 122,  97,   4,   4,   4,   4, 123,   4,  78,   4, 124, 101, 125, 125,   0,
    126, 127,  14,   4, 128,  14,   4,  79, 103, 129,   4,   4, 130,  85,   0,  16,
      4,   4,   4,   4,   4,  96,   0,   0,   4,   4,   4,   4,   4,   4,  96,   0,
      4,   4,   4,   4,  72,   0,  16, 110, 131, 132,   4, 133, 110,   4,   4,  23,
    134, 135,   4,   4, 136, 137,   0, 134, 138, 139,   4,  92, 135,  92,   0, 140,
     26, 141,  65, 142,  32, 143, 144, 145,   4, 121, 146, 147,   4, 148, 149, 150,
    151, 152,  79, 141,   4,   4,   4, 139,   4,   4,   4,   4,   4, 153, 154, 155,
      4,   4,   4, 156,   4,   4, 157,   0, 158, 159, 160,   4,   4,  90, 161,   4,
      4,   4, 110,  32,   4,   4,   4,   4,   4, 110,  16,   4, 162,   4,  15, 163,
      0,   0,   0, 164,   4,   4,   4, 142,   0,   1,   1, 165, 110,  97, 166,   0,
    167, 168, 169,   0,   4,   4,   4,  85,   0,   0,   4,  31,   0,   0,   0,   0,
      0,   0,   0,   0, 142,   4, 170,   0,   4,  16, 171,  96, 110,   4, 172,   0,
      4,   4,   4,   4, 110,   0,   0,   0,   4, 173,   4, 108,   0,   0,   0,   0,
      4, 101,  96,  15,   0,   0,   0,   0, 174, 175,  96, 101,  97,   0,   0, 176,
     96, 157,   0,   0,   4, 177,   0,   0, 178,  92,   0, 142, 142,   0,  71, 179,
      4,  96,  96, 143,  90,   0,   0,   0,   4,   4, 121,   0,   4, 143,   4, 143,
    105,  94,   0,   0, 105,  23,  16, 121, 105,  65,  16, 180, 105, 143, 181,   0,
    182, 183,   0,   0, 184, 185,  97,   0,  48,  45, 186,  56,   0,   0,   0,   0,
      0,   0,   0,   0,   4,  23, 187,   0,   0,   0,   0,   0,   4, 130, 188,   0,
      4,  23, 189,   0,   4,  18,   0,   0, 157,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   4,   4, 190,   0,   0,   0,   0,   0,   0,   4,  30,
      4,   4,   4,   4, 157,   0,   0,   0,   4,   4,   4, 130,   4,   4,   4,   4,
      4,   4, 108,   0,   0,   0,   0,   0,   4, 130,   0,   0,   0,   0,   0,   0,
      4,   4,  65,   0,   0,   0,   0,   0,   4,  30,  97,   0,   0,   0,  16, 191,
      4,  23, 108, 192,  23,   0,   0,   0,   4,   4, 193,   0, 161,   0,   0,   0,
     56,   0,   0,   0,   0,   0,   0,   0,   4,   4,   4, 194, 195,   0,   0,   0,
      4,   4, 196,   4, 197, 198, 199,   4, 200, 201, 202,   4,   4,   4,   4,   4,
      4,   4,   4,   4,   4, 203, 204,  79, 196, 196, 122, 122, 205, 205, 146,   0,
      4,   4,   4,   4,   4,   4, 179,   0, 199, 206, 207, 208, 209, 210,   0,   0,
      4,   4,   4,   4,   4,   4, 101,   0,   4,  31,   4,   4,   4,   4,   4,   4,
    110,   4,   4,   4,   4,   4,   4,   4,   4,   4,   4,   4,   4,  56,   0,   0,
    110,   0,   0,   0,   0,   0,   0,   0,
};

static RE_UINT8 re_xid_start_stage_5[] = {
      0,   0,   0,   0, 254, 255, 255,   7,   0,   4,  32,   4, 255, 255, 127, 255,
    255, 255, 255, 255, 195, 255,   3,   0,  31,  80,   0,   0,   0,   0, 223, 184,
     64, 215, 255, 255, 251, 255, 255, 255, 255, 255, 191, 255,   3, 252, 255, 255,
    255, 255, 254, 255, 255, 255, 127,   2, 254, 255, 255, 255, 255,   0,   0,   0,
      0,   0, 255, 255, 255,   7,   7,   0, 255,   7,   0,   0,   0, 192, 254, 255,
    255, 255,  47,   0,  96, 192,   0, 156,   0,   0, 253, 255, 255, 255,   0,   0,
      0, 224, 255, 255,  63,   0,   2,   0,   0, 252, 255, 255, 255,   7,  48,   4,
    255, 255,  63,   4,  16,   1,   0,   0, 255, 255, 255,   1, 255, 255,  31,   0,
    240, 255, 255, 255, 255, 255, 255,  35,   0,   0,   1, 255,   3,   0, 254, 255,
    225, 159, 249, 255, 255, 253, 197,  35,   0,  64,   0, 176,   3,   0,   3,   0,
    224, 135, 249, 255, 255, 253, 109,   3,   0,   0,   0,  94,   0,   0,  28,   0,
    224, 191, 251, 255, 255, 253, 237,  35,   0,   0,   1,   0,   3,   0,   0,   2,
    224, 159, 249, 255,   0,   0,   0, 176,   3,   0,   2,   0, 232, 199,  61, 214,
     24, 199, 255,   3, 224, 223, 253, 255, 255, 253, 255,  35,   0,   0,   0,   7,
      3,   0,   0,   0, 255, 253, 239,  35,   0,   0,   0,  64,   3,   0,   6,   0,
    255, 255, 255,  39,   0,  64,   0, 128,   3,   0,   0, 252, 224, 255, 127, 252,
    255, 255, 251,  47, 127,   0,   0,   0, 255, 255,   5,   0, 150,  37, 240, 254,
    174, 236,   5,  32,  95,   0,   0, 240,   1,   0,   0,   0, 255, 254, 255, 255,
    255,  31,   0,   0,   0,  31,   0,   0, 255,   7,   0, 128,   0,   0,  63,  60,
     98, 192, 225, 255,   3,  64,   0,   0, 191,  32, 255, 255, 255, 255, 255, 247,
    255,  61, 127,  61, 255,  61, 255, 255, 255, 255,  61, 127,  61, 255, 127, 255,
    255, 255,  61, 255, 255, 255, 255,   7, 255, 255,  63,  63, 255, 159, 255, 255,
    255, 199, 255,   1, 255, 223,   3,   0, 255, 255,   3,   0, 255, 223,   1,   0,
    255, 255,  15,   0,   0,   0, 128,  16, 255, 255, 255,   0, 255,   5, 255, 255,
    255, 255,  63,   0, 255, 255, 255, 127, 255,  63,  31,   0, 255,  15, 255, 255,
    255,   3,   0,   0, 255, 255, 127,   0, 128,   0,   0,   0, 224, 255, 255, 255,
    224,  15,   0,   0, 248, 255, 255, 255,   1, 192,   0, 252,  63,   0,   0,   0,
     15,   0,   0,   0,   0, 224,   0, 252, 255, 255, 255,  63,   0, 222,  99,   0,
     63,  63, 255, 170, 255, 255, 223,  95, 220,  31, 207,  15, 255,  31, 220,  31,
      0,   0,   2, 128,   0,   0, 255,  31, 132, 252,  47,  63,  80, 253, 255, 243,
    224,  67,   0,   0, 255,   1,   0,   0, 255, 127, 255, 255,  31, 120,  12,   0,
    255, 128,   0,   0, 127, 127, 127, 127, 224,   0,   0,   0, 254,   3,  62,  31,
    255, 255, 127, 224, 255,  63, 254, 255, 255, 127,   0,   0, 255,  31, 255, 255,
      0,  12,   0,   0, 255, 127,   0, 128,   0,   0, 128, 255, 252, 255, 255, 255,
    255, 249, 255, 255, 255,  63, 255,   0, 187, 247, 255, 255,   7,   0,   0,   0,
      0,   0, 252,  40,  63,   0, 255, 255, 255, 255, 255,  31, 255, 255,   7,   0,
      0, 128,   0,   0, 223, 255,   0, 124, 247,  15,   0,   0, 255, 255, 127, 196,
    255, 255,  98,  62,   5,   0,   0,  56, 255,   7,  28,   0, 126, 126, 126,   0,
    127, 127, 255, 255,  15,   0, 255, 255, 127, 248, 255, 255, 255, 255, 255,  15,
    255,  63, 255, 255, 255, 255, 255,   3, 127,   0, 248, 160, 255, 253, 127,  95,
    219, 255, 255, 255,   0,   0, 248, 255, 255, 255, 252, 255,   0,   0, 255,   3,
      0,   0, 138, 170, 192, 255, 255, 255, 252, 252, 252,  28, 255, 239, 255, 255,
    127, 255, 255, 183, 255,  63, 255,  63, 255, 255,   1,   0, 255,   7, 255, 255,
     15, 255,  62,   0, 255,   0, 255, 255,  63, 253, 255, 255, 255, 255, 191, 145,
    255, 255,  55,   0, 255, 255, 255, 192,   1,   0, 239, 254,  31,   0,   0,   0,
    255, 255,  71,   0,  30,   0,   0,  20, 255, 255, 251, 255, 255,  15,   0,   0,
    127, 189, 255, 191, 255,   1, 255, 255,   0,   0,   1, 224, 176,   0,   0,   0,
      0,   0,   0,  15,  16,   0,   0,   0,   0,   0,   0, 128, 255,  63,   0,   0,
    248, 255, 255, 224,  31,   0,   1,   0, 255,   7, 255,  31, 255,   1, 255,   3,
    255, 255, 223, 255, 255, 255, 255, 223, 100, 222, 255, 235, 239, 255, 255, 255,
    191, 231, 223, 223, 255, 255, 255, 123,  95, 252, 253, 255,  63, 255, 255, 255,
    253, 255, 255, 247, 255, 253, 255, 255, 150, 254, 247,  10, 132, 234, 150, 170,
    150, 247, 247,  94, 255, 251, 255,  15, 238, 251, 255,  15,
};

/* XID_Start: 2005 bytes. */

RE_UINT32 re_get_xid_start(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_xid_start_stage_1[f] << 5;
    f = code >> 11;
    code ^= f << 11;
    pos = (RE_UINT32)re_xid_start_stage_2[pos + f] << 3;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_xid_start_stage_3[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_xid_start_stage_4[pos + f] << 5;
    pos += code;
    value = (re_xid_start_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* XID_Continue. */

static RE_UINT8 re_xid_continue_stage_1[] = {
    0, 1, 2, 3, 4, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6,
    6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 7, 6, 6, 6,
    6, 6,
};

static RE_UINT8 re_xid_continue_stage_2[] = {
     0,  1,  2,  3,  4,  5,  6,  7,  7,  8,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  9, 10, 11,  7,  7,  7,  7, 12, 13, 13, 13, 13, 14,
    15, 16, 17, 18, 19, 13, 20, 13, 21, 13, 13, 13, 13, 22, 13, 13,
    13, 13, 13, 13, 13, 13, 23, 24, 13, 13, 25, 26, 13, 27, 13, 13,
     7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  7, 28,  7, 29, 30,  7, 31, 13, 13, 13, 13, 13, 32,
    13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13,
    33, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13,
};

static RE_UINT8 re_xid_continue_stage_3[] = {
     0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15,
    16,  1, 17, 18, 19,  1, 20, 21, 22, 23, 24, 25, 26, 27,  1, 28,
    29, 30, 31, 31, 31, 31, 31, 31, 31, 31, 31, 31, 32, 33, 31, 31,
    34, 35, 31, 31,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1, 36,  1,  1,  1,  1,  1,  1,  1,  1,  1, 37,
     1,  1,  1,  1, 38,  1, 39, 40, 41, 42, 43, 44,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1, 45, 31, 31, 31, 31, 31, 31, 31, 31,
    31,  1, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57,  1, 58,
    59, 60, 61, 62, 63, 31, 31, 31, 64, 65, 66, 67, 68, 69, 70, 71,
    72, 31, 73, 31, 31, 31, 31, 31,  1,  1,  1, 74, 75, 76, 31, 31,
     1,  1,  1,  1, 77, 31, 31, 31, 31, 31, 31, 31,  1,  1, 78, 31,
     1,  1, 79, 80, 31, 31, 31, 81, 82, 31, 31, 31, 31, 31, 31, 31,
    31, 31, 31, 31, 83, 31, 31, 31, 31, 84, 85, 31, 86, 87, 88, 89,
    31, 31, 90, 31, 31, 31, 31, 31, 91, 31, 31, 31, 31, 31, 92, 31,
     1,  1,  1,  1,  1,  1, 93,  1,  1,  1,  1,  1,  1,  1,  1, 94,
    95,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1, 96, 31,
     1,  1, 97, 31, 31, 31, 31, 31, 31, 98, 31, 31, 31, 31, 31, 31,
};

static RE_UINT8 re_xid_continue_stage_4[] = {
      0,   1,   2,   3,   0,   4,   5,   5,   6,   6,   6,   6,   6,   6,   6,   6,
      6,   6,   6,   6,   6,   6,   7,   8,   6,   6,   6,   9,  10,  11,   6,  12,
      6,   6,   6,   6,  13,   6,   6,   6,   6,  14,  15,  16,  17,  18,  19,  20,
     21,   6,   6,  22,   6,   6,  23,  24,  25,   6,  26,   6,   6,  27,   6,  28,
      6,  29,  30,   0,   0,  31,   0,  32,   6,   6,   6,  33,  34,  35,  36,  37,
     38,  39,  40,  41,  42,  43,  44,  45,  46,  43,  47,  48,  49,  50,  51,  52,
     53,  54,  55,  56,  57,  58,  59,  60,  57,  61,  62,  63,  64,  65,  66,  67,
     16,  68,  69,   0,  70,  71,  72,   0,  73,  74,  75,  76,  77,  78,  79,   0,
      6,   6,  80,   6,  81,   6,  82,  83,   6,   6,  84,   6,  85,  86,  87,   6,
     88,   6,  61,  89,  90,   6,   6,  91,  16,   6,   6,   6,   6,   6,   6,   6,
      6,   6,   6,  92,   3,   6,   6,  93,  94,  31,  95,  96,   6,   6,  97,  98,
     99,   6,   6, 100,   6, 101,   6, 102, 103, 104, 105, 106,   6, 107, 108,   0,
     30,   6, 103, 109, 110, 111,   0,   0,   6,   6, 112, 113,   6,   6,   6,  95,
      6, 100, 114,  81,   0,   0, 115, 116,   6,   6,   6,   6,   6,   6,   6, 117,
     91,   6, 118,  81,   6, 119, 120, 121,   0, 122, 123, 124, 125,   0, 125, 126,
    127, 128, 129,   6, 130,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      6, 131, 103,   6,   6,   6,   6, 132,   6,  82,   6, 133, 134, 135, 135,   6,
    136, 137,  16,   6, 138,  16,   6,  83, 139, 140,   6,   6, 141,  68,   0,  25,
      6,   6,   6,   6,   6, 102,   0,   0,   6,   6,   6,   6,   6,   6, 102,   0,
      6,   6,   6,   6, 142,   0,  25,  81, 143, 144,   6, 145,   6,   6,   6,  27,
    146, 147,   6,   6, 148, 149,   0, 146,   6, 150,   6,  95,   6,   6, 151, 152,
      6, 153,  95,  78,   6,   6, 154, 103,   6, 134, 155, 156,   6,   6, 157, 158,
    159, 160,  83, 161,   6,   6,   6, 162,   6,   6,   6,   6,   6, 163, 164,  30,
      6,   6,   6, 153,   6,   6, 165,   0, 166, 167, 168,   6,   6,  27, 169,   6,
      6,   6,  81, 170,   6,   6,   6,   6,   6,  81,  25,   6, 171,   6, 150,   1,
     90, 172, 173, 174,   6,   6,   6,  78,   1,   2,   3, 105,   6, 103, 175,   0,
    176, 177, 178,   0,   6,   6,   6,  68,   0,   0,   6,  31,   0,   0,   0, 179,
      0,   0,   0,   0,  78,   6, 180, 181,   6,  25, 101,  68,  81,   6, 182,   0,
      6,   6,   6,   6,  81,  98,   0,   0,   6, 183,   6, 184,   0,   0,   0,   0,
      6, 134, 102, 150,   0,   0,   0,   0, 185, 186, 102, 134, 103,   0,   0, 187,
    102, 165,   0,   0,   6, 188,   0,   0, 189, 190,   0,  78,  78,   0,  75, 191,
      6, 102, 102, 192,  27,   0,   0,   0,   6,   6, 130,   0,   6, 192,   6, 192,
      6,   6, 191, 193,   6,  68,  25, 194,   6, 195,  25, 196,   6,   6, 197,   0,
    198, 100,   0,   0, 199, 200,   6, 201,  34,  43, 202, 203,   0,   0,   0,   0,
      0,   0,   0,   0,   6,   6, 204,   0,   0,   0,   0,   0,   6, 205, 206,   0,
      6,   6, 207,   0,   6, 100,  98,   0, 208, 112,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   6,   6, 209,   0,   0,   0,   0,   0,   0,   6, 210,
      6,   6,   6,   6, 165,   0,   0,   0,   6,   6,   6, 141,   6,   6,   6,   6,
      6,   6, 184,   0,   0,   0,   0,   0,   6, 141,   0,   0,   0,   0,   0,   0,
      6,   6, 191,   0,   0,   0,   0,   0,   6, 210, 103,  98,   0,   0,  25, 106,
      6, 134, 211, 212,  90,   0,   0,   0,   6,   6, 213, 103, 214,   0,   0,   0,
    215,   0,   0,   0,   0,   0,   0,   0,   6,   6,   6, 216, 217,   0,   0,   0,
      0,   0,   0, 218, 219, 220,   0,   0,   0,   0, 221,   0,   0,   0,   0,   0,
      6,   6, 195,   6, 222, 223, 224,   6, 225, 226, 227,   6,   6,   6,   6,   6,
      6,   6,   6,   6,   6, 228, 229,  83, 195, 195, 131, 131, 230, 230, 231,   6,
      6, 232,   6, 233, 234, 235,   0,   0,   6,   6,   6,   6,   6,   6, 236,   0,
    224, 237, 238, 239, 240, 241,   0,   0,   6,   6,   6,   6,   6,   6, 134,   0,
      6,  31,   6,   6,   6,   6,   6,   6,  81,   6,   6,   6,   6,   6,   6,   6,
      6,   6,   6,   6,   6, 215,   0,   0,  81,   0,   0,   0,   0,   0,   0,   0,
      6,   6,   6,   6,   6,   6,   6,  90,
};

static RE_UINT8 re_xid_continue_stage_5[] = {
      0,   0,   0,   0,   0,   0, 255,   3, 254, 255, 255, 135, 254, 255, 255,   7,
      0,   4, 160,   4, 255, 255, 127, 255, 255, 255, 255, 255, 195, 255,   3,   0,
     31,  80,   0,   0, 255, 255, 223, 184, 192, 215, 255, 255, 251, 255, 255, 255,
    255, 255, 191, 255, 251, 252, 255, 255, 255, 255, 254, 255, 255, 255, 127,   2,
    254, 255, 255, 255, 255,   0, 254, 255, 255, 255, 255, 191, 182,   0, 255, 255,
    255,   7,   7,   0,   0,   0, 255,   7, 255, 195, 255, 255, 255, 255, 239, 159,
    255, 253, 255, 159,   0,   0, 255, 255, 255, 231, 255, 255, 255, 255,   3,   0,
    255, 255,  63,   4, 255,  63,   0,   0, 255, 255, 255,  15, 255, 255,  31,   0,
    248, 255, 255, 255, 207, 255, 254, 255, 239, 159, 249, 255, 255, 253, 197, 243,
    159, 121, 128, 176, 207, 255,   3,   0, 238, 135, 249, 255, 255, 253, 109, 211,
    135,  57,   2,  94, 192, 255,  63,   0, 238, 191, 251, 255, 255, 253, 237, 243,
    191,  59,   1,   0, 207, 255,   0,   2, 238, 159, 249, 255, 159,  57, 192, 176,
    207, 255,   2,   0, 236, 199,  61, 214,  24, 199, 255, 195, 199,  61, 129,   0,
    192, 255,   0,   0, 239, 223, 253, 255, 255, 253, 255, 227, 223,  61,  96,   7,
    207, 255,   0,   0, 238, 223, 253, 255, 255, 253, 239, 243, 223,  61,  96,  64,
    207, 255,   6,   0, 255, 255, 255, 231, 223, 125, 128, 128, 207, 255,   0, 252,
    236, 255, 127, 252, 255, 255, 251,  47, 127, 132,  95, 255, 192, 255,  12,   0,
    255, 255, 255,   7, 255, 127, 255,   3, 150,  37, 240, 254, 174, 236, 255,  59,
     95,  63, 255, 243,   1,   0,   0,   3, 255,   3, 160, 194, 255, 254, 255, 255,
    255,  31, 254, 255, 223, 255, 255, 254, 255, 255, 255,  31,  64,   0,   0,   0,
    255,   3, 255, 255, 255, 255, 255,  63, 191,  32, 255, 255, 255, 255, 255, 247,
    255,  61, 127,  61, 255,  61, 255, 255, 255, 255,  61, 127,  61, 255, 127, 255,
    255, 255,  61, 255,   0, 254,   3,   0, 255, 255,   0,   0, 255, 255,  63,  63,
    255, 159, 255, 255, 255, 199, 255,   1, 255, 223,  31,   0, 255, 255,  15,   0,
    255, 223,  13,   0, 255, 255, 143,  48, 255,   3,   0,   0,   0,  56, 255,   3,
    255, 255, 255,   0, 255,   7, 255, 255, 255, 255,  63,   0, 255, 255, 255, 127,
    255,  15, 255,  15, 192, 255, 255, 255, 255,  63,  31,   0, 255,  15, 255, 255,
    255,   3, 255,   7, 255, 255, 255, 159, 255,   3, 255,   3, 128,   0, 255,  63,
    255,  15, 255,   3,   0, 248,  15,   0, 255, 227, 255, 255,   0,   0, 247, 255,
    255, 255, 127,   3, 255, 255,  63, 240,  63,  63, 255, 170, 255, 255, 223,  95,
    220,  31, 207,  15, 255,  31, 220,  31,   0,   0,   0, 128,   1,   0,  16,   0,
      0,   0,   2, 128,   0,   0, 255,  31, 226, 255,   1,   0, 132, 252,  47,  63,
     80, 253, 255, 243, 224,  67,   0,   0, 255,   1,   0,   0, 255, 127, 255, 255,
     31, 248,  15,   0, 255, 128,   0, 128, 255, 255, 127,   0, 127, 127, 127, 127,
    224,   0,   0,   0, 254, 255,  62,  31, 255, 255, 127, 230, 224, 255, 255, 255,
    255,  63, 254, 255, 255, 127,   0,   0, 255,  31,   0,   0, 255,  31, 255, 255,
    255,  15,   0,   0, 255, 255, 240, 191,   0,   0, 128, 255, 252, 255, 255, 255,
    255, 249, 255, 255, 255,  63, 255,   0, 255,   0,   0,   0,  31,   0, 255,   3,
    255, 255, 255,  40, 255,  63, 255, 255,   1, 128, 255,   3, 255,  63, 255,   3,
    255, 255, 127, 252,   7,   0,   0,  56, 255, 255, 124,   0, 126, 126, 126,   0,
    127, 127, 255, 255,  63,   0, 255, 255, 255,  55, 255,   3,  15,   0, 255, 255,
    127, 248, 255, 255, 255, 255, 255,   3, 127,   0, 248, 224, 255, 253, 127,  95,
    219, 255, 255, 255,   0,   0, 248, 255, 240, 255, 255, 255, 255, 255, 252, 255,
    255, 255,  24,   0,   0, 224,   0,   0,   0,   0, 138, 170, 252, 252, 252,  28,
    255, 239, 255, 255, 127, 255, 255, 183, 255,  63, 255,  63,   0,   0,   0,  32,
    255, 255,   1,   0,   1,   0,   0,   0,  15, 255,  62,   0, 255,   0, 255, 255,
     15,   0,   0,   0,  63, 253, 255, 255, 255, 255, 191, 145, 255, 255,  55,   0,
    255, 255, 255, 192, 111, 240, 239, 254, 255, 255,  15, 135, 127,   0,   0,   0,
    255, 255,   7,   0, 192, 255,   0, 128, 255,   1, 255,   3, 255, 255, 223, 255,
    255, 255,  79,   0,  31,  28, 255,  23, 255, 255, 251, 255, 127, 189, 255, 191,
    255,   1, 255, 255, 255,   7, 255,   3, 159,  57, 129, 224, 207,  31,  31,   0,
    191,   0, 255,   3, 255, 255,  63, 255,   1,   0,   0,  63,  17,   0, 255,   3,
    255, 255, 255, 227, 255,   3,   0, 128, 255, 255, 255,   1,  15,   0, 255,   3,
    248, 255, 255, 224,  31,   0, 255, 255,   0, 128, 255, 255,   3,   0,   0,   0,
    255,   7, 255,  31, 255,   1, 255,  99, 224, 227,   7, 248, 231,  15,   0,   0,
      0,  60,   0,   0,  28,   0,   0,   0, 255, 255, 255, 223, 100, 222, 255, 235,
    239, 255, 255, 255, 191, 231, 223, 223, 255, 255, 255, 123,  95, 252, 253, 255,
     63, 255, 255, 255, 253, 255, 255, 247, 255, 253, 255, 255, 247, 207, 255, 255,
    255, 255, 127, 248, 255,  31,  32,   0,  16,   0,   0, 248, 254, 255,   0,   0,
     31,   0, 127,   0, 150, 254, 247,  10, 132, 234, 150, 170, 150, 247, 247,  94,
    255, 251, 255,  15, 238, 251, 255,  15,
};

/* XID_Continue: 2194 bytes. */

RE_UINT32 re_get_xid_continue(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 15;
    code = ch ^ (f << 15);
    pos = (RE_UINT32)re_xid_continue_stage_1[f] << 4;
    f = code >> 11;
    code ^= f << 11;
    pos = (RE_UINT32)re_xid_continue_stage_2[pos + f] << 3;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_xid_continue_stage_3[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_xid_continue_stage_4[pos + f] << 5;
    pos += code;
    value = (re_xid_continue_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Default_Ignorable_Code_Point. */

static RE_UINT8 re_default_ignorable_code_point_stage_1[] = {
    0, 1, 2, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 4, 2, 2, 2,
    2, 2,
};

static RE_UINT8 re_default_ignorable_code_point_stage_2[] = {
    0, 1, 2, 3, 4, 1, 5, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 6,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 7, 1, 1, 8, 1, 1, 1, 1, 1,
    9, 9, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
};

static RE_UINT8 re_default_ignorable_code_point_stage_3[] = {
     0,  1,  1,  2,  1,  1,  3,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  4,  1,  1,  1,  1,  1,  5,  6,  1,  1,  1,  1,  1,  1,  1,
     7,  1,  1,  1,  1,  1,  1,  1,  1,  8,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  9, 10,  1,  1,  1,  1, 11,  1,  1,  1,
     1, 12,  1,  1,  1,  1,  1,  1, 13, 13, 13, 13, 13, 13, 13, 13,
};

static RE_UINT8 re_default_ignorable_code_point_stage_4[] = {
     0,  0,  0,  0,  0,  1,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  2,  0,  0,  0,  0,  0,  3,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  4,  5,  0,  0,  0,  0,  0,  0,  0,  0,  0,  6,  0,  0,
     7,  0,  0,  0,  0,  0,  0,  0,  8,  9,  0, 10,  0,  0,  0,  0,
     0,  0,  0, 11,  0,  0,  0,  0, 10,  0,  0,  0,  0,  0,  0,  4,
     0,  0,  0,  0,  0,  5,  0, 12,  0,  0,  0,  0,  0, 13,  0,  0,
     0,  0,  0, 14,  0,  0,  0,  0, 15, 15, 15, 15, 15, 15, 15, 15,
};

static RE_UINT8 re_default_ignorable_code_point_stage_5[] = {
      0,   0,   0,   0,   0,  32,   0,   0,   0, 128,   0,   0,   0,   0,   0,  16,
      0,   0,   0, 128,   1,   0,   0,   0,   0,   0,  48,   0,   0, 120,   0,   0,
      0, 248,   0,   0,   0, 124,   0,   0, 255, 255,   0,   0,  16,   0,   0,   0,
      0,   0, 255,   1,  15,   0,   0,   0,   0,   0, 248,   7, 255, 255, 255, 255,
};

/* Default_Ignorable_Code_Point: 370 bytes. */

RE_UINT32 re_get_default_ignorable_code_point(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 15;
    code = ch ^ (f << 15);
    pos = (RE_UINT32)re_default_ignorable_code_point_stage_1[f] << 4;
    f = code >> 11;
    code ^= f << 11;
    pos = (RE_UINT32)re_default_ignorable_code_point_stage_2[pos + f] << 3;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_default_ignorable_code_point_stage_3[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_default_ignorable_code_point_stage_4[pos + f] << 5;
    pos += code;
    value = (re_default_ignorable_code_point_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Grapheme_Extend. */

static RE_UINT8 re_grapheme_extend_stage_1[] = {
    0, 1, 2, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
    4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 4, 4, 4,
    4, 4,
};

static RE_UINT8 re_grapheme_extend_stage_2[] = {
     0,  1,  2,  3,  4,  5,  6,  7,  7,  7,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  7,  8,  9,  7,  7,  7,  7,  7,  7,  7,  7,  7, 10,
    11, 12, 13,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7, 14,  7,  7,
     7,  7,  7,  7,  7,  7,  7, 15,  7,  7, 16, 17,  7, 18,  7,  7,
     7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,
    19,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,
};

static RE_UINT8 re_grapheme_extend_stage_3[] = {
     0,  0,  0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13,
    14,  0,  0, 15,  0,  0,  0, 16, 17, 18, 19, 20, 21, 22,  0,  0,
    23,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 24, 25,  0,  0,
    26,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0, 27,  0, 28, 29, 30, 31,  0,  0,  0,  0,
     0,  0,  0, 32,  0,  0, 33, 34,  0, 35, 36, 37,  0,  0,  0,  0,
     0,  0, 38,  0,  0,  0,  0,  0, 39, 40, 41, 42, 43, 44, 45, 46,
     0,  0, 47, 48,  0,  0,  0, 49,  0,  0,  0,  0, 50,  0,  0,  0,
     0, 51, 52,  0,  0,  0,  0,  0,  0,  0, 53,  0,  0,  0,  0,  0,
    54,  0,  0,  0,  0,  0,  0,  0,  0, 55,  0,  0,  0,  0,  0,  0,
};

static RE_UINT8 re_grapheme_extend_stage_4[] = {
      0,   0,   0,   0,   0,   0,   0,   0,   1,   1,   1,   2,   0,   0,   0,   0,
      0,   0,   0,   0,   3,   0,   0,   0,   0,   0,   0,   0,   4,   5,   6,   0,
      7,   0,   8,   9,   0,   0,  10,  11,  12,  13,  14,   0,   0,  15,   0,  16,
     17,  18,  19,   0,   0,   0,   0,  20,  21,  22,  23,  24,  25,  26,  27,  24,
     28,  29,  30,  31,  28,  29,  32,  24,  25,  33,  34,  24,  35,  36,  37,   0,
     38,  39,  40,  24,  25,  41,  42,  24,  25,  36,  27,  24,   0,   0,  43,   0,
      0,  44,  45,   0,   0,  46,  47,   0,  48,  49,   0,  50,  51,  52,  53,   0,
      0,  54,  55,  56,  57,   0,   0,   0,   0,   0,  58,   0,   0,   0,   0,   0,
     59,  59,  60,  60,   0,  61,  62,   0,  63,   0,   0,   0,   0,  64,   0,   0,
      0,  65,   0,   0,   0,   0,   0,   0,  66,   0,  67,  68,   0,  69,   0,   0,
     70,  71,  35,  16,  72,  73,   0,  74,   0,  75,   0,   0,   0,   0,  76,  77,
      0,   0,   0,   0,   0,   0,   1,  78,  79,   0,   0,   0,   0,   0,  13,  80,
      0,   0,   0,   0,   0,   0,   0,  81,   0,   0,   0,  82,   0,   0,   0,   1,
      0,  83,   0,   0,  84,   0,   0,   0,   0,   0,   0,  85,  39,   0,   0,  86,
     87,  88,   0,   0,   0,   0,  89,  90,   0,  91,  92,   0,  21,  93,   0,  94,
      0,  95,  96,  29,   0,  97,  25,  98,   0,   0,   0,   0,   0,   0,   0,  99,
     36,   0,   0,   0,   0,   0,   0,   0,   2,   2,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,  39,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 100,
      0,   0,   0,   0,   0,   0,   0,  38,   0,   0,   0, 101,   0,   0,   0,   0,
    102, 103,   0,   0,   0,   0,   0,  88,  25, 104, 105,  82,  72, 106,   0,   0,
     21, 107,   0, 108,  72, 109, 110,   0,   0, 111,   0,   0,   0,   0,  82, 112,
     72,  26, 113, 114,   0,   0,   0,   0,   0,   0,   0,   0,   0, 115, 116,   0,
      0,   0,   0,   0,   0, 117, 118,   0,   0, 119,  38,   0,   0, 120,   0,   0,
     58, 121,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 122,
      0, 123,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 124,   0,   0,   0,
      0,   0,   0,   0, 125,   0,   0,   0,   0,   0,   0, 126, 127, 128,   0,   0,
      0,   0, 129,   0,   0,   0,   0,   0,   1, 130,   1, 131, 132, 133,   0,   0,
      0,   0,   0,   0,   0,   0, 123,   0,   1,   1,   1,   1,   1,   1,   1,   2,
};

static RE_UINT8 re_grapheme_extend_stage_5[] = {
      0,   0,   0,   0, 255, 255, 255, 255, 255, 255,   0,   0, 248,   3,   0,   0,
      0,   0, 254, 255, 255, 255, 255, 191, 182,   0,   0,   0,   0,   0, 255,   7,
      0, 248, 255, 255,   0,   0,   1,   0,   0,   0, 192, 159, 159,  61,   0,   0,
      0,   0,   2,   0,   0,   0, 255, 255, 255,   7,   0,   0, 192, 255,   1,   0,
      0, 248,  15,   0,   0,   0, 192, 251, 239,  62,   0,   0,   0,   0,   0,  14,
    248, 255, 255, 255,   7,   0,   0,   0,   0,   0,   0,  20, 254,  33, 254,   0,
     12,   0,   0,   0,   2,   0,   0,   0,   0,   0,   0,  80,  30,  32, 128,   0,
      6,   0,   0,   0,   0,   0,   0,  16, 134,  57,   2,   0,   0,   0,  35,   0,
    190,  33,   0,   0,   0,   0,   0, 208,  30,  32, 192,   0,   4,   0,   0,   0,
      0,   0,   0,  64,   1,  32, 128,   0,   1,   0,   0,   0,   0,   0,   0, 192,
    193,  61,  96,   0,   0,   0,   0, 144,  68,  48,  96,   0,   0, 132,  92, 128,
      0,   0, 242,   7, 128, 127,   0,   0,   0,   0, 242,  27,   0,  63,   0,   0,
      0,   0,   0,   3,   0,   0, 160,   2,   0,   0, 254, 127, 223, 224, 255, 254,
    255, 255, 255,  31,  64,   0,   0,   0,   0, 224, 253, 102,   0,   0,   0, 195,
      1,   0,  30,   0, 100,  32,   0,  32,   0,   0,   0, 224,   0,   0,  28,   0,
      0,   0,  12,   0,   0,   0, 176,  63,  64, 254,  15,  32,   0,  56,   0,   0,
      0,   2,   0,   0, 135,   1,   4,  14,   0,   0, 128,   9,   0,   0,  64, 127,
    229,  31, 248, 159,   0,   0, 255, 127,  15,   0,   0,   0,   0,   0, 208,  23,
      3,   0,   0,   0,  60,  59,   0,   0,  64, 163,   3,   0,   0, 240, 207,   0,
      0,   0, 247, 255, 253,  33,  16,   3, 255, 255,  63, 240,   0,  48,   0,   0,
    255, 255,   1,   0,   0, 128,   3,   0,   0,   0,   0, 128,   0, 252,   0,   0,
      0,   0,   0,   6,   0, 128, 247,  63,   0,   0,   3,   0,  68,   8,   0,   0,
     96,   0,   0,   0,  16,   0,   0,   0, 255, 255,   3,   0, 192,  63,   0,   0,
    128, 255,   3,   0,   0,   0, 200,  19,  32,   0,   0,   0,   0, 126, 102,   0,
      8,  16,   0,   0,   0,   0, 157, 193,   0,  48,  64,   0,  32,  33,   0,   0,
      0,   0,   0,  32,   0,   0, 192,   7, 110, 240,   0,   0,   0,   0,   0, 135,
      0,   0,   0, 255, 127,   0,   0,   0,   0,   0, 120,   6, 128, 239,  31,   0,
      0,   0,   8,   0,   0,   0, 192, 127,   0,  28,   0,   0,   0, 128, 211,   0,
    248,   7,   0,   0,   1,   0, 128,   0, 192,  31,  31,   0,   0,   0, 249, 165,
     13,   0,   0,   0,   0, 128,  60, 176,   1,   0,   0,  48,   0,   0, 248, 167,
      0,  40, 191,   0, 188,  15,   0,   0,   0,   0,  31,   0,   0,   0, 127,   0,
      0, 128,   7,   0,   0,   0,   0,  96, 160, 195,   7, 248, 231,  15,   0,   0,
      0,  60,   0,   0,  28,   0,   0,   0, 255, 255, 127, 248, 255,  31,  32,   0,
     16,   0,   0, 248, 254, 255,   0,   0,
};

/* Grapheme_Extend: 1274 bytes. */

RE_UINT32 re_get_grapheme_extend(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 15;
    code = ch ^ (f << 15);
    pos = (RE_UINT32)re_grapheme_extend_stage_1[f] << 4;
    f = code >> 11;
    code ^= f << 11;
    pos = (RE_UINT32)re_grapheme_extend_stage_2[pos + f] << 3;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_grapheme_extend_stage_3[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_grapheme_extend_stage_4[pos + f] << 5;
    pos += code;
    value = (re_grapheme_extend_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Grapheme_Base. */

static RE_UINT8 re_grapheme_base_stage_1[] = {
    0, 1, 2, 3, 4, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6,
    6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6,
    6, 6,
};

static RE_UINT8 re_grapheme_base_stage_2[] = {
     0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 13, 13,
    13, 13, 13, 14, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13,
    13, 13, 13, 13, 13, 13, 13, 15, 13, 16, 17, 13, 13, 13, 13, 13,
    13, 13, 13, 13, 13, 18, 19, 19, 19, 19, 19, 19, 19, 19, 20, 21,
    22, 23, 24, 25, 26, 27, 28, 19, 29, 30, 19, 19, 13, 31, 19, 19,
    19, 32, 19, 19, 19, 19, 19, 19, 19, 19, 33, 34, 19, 19, 19, 19,
    19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 35, 19, 19, 36,
    19, 19, 19, 19, 37, 38, 39, 19, 19, 19, 40, 41, 42, 43, 44, 19,
    13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13,
    13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13,
    13, 13, 13, 13, 13, 13, 13, 13, 13, 45, 13, 13, 13, 46, 47, 13,
    13, 13, 13, 48, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 49, 19,
    19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19,
    19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19,
};

static RE_UINT8 re_grapheme_base_stage_3[] = {
      0,   1,   2,   2,   2,   2,   3,   4,   2,   5,   6,   7,   8,   9,  10,  11,
     12,  13,  14,  15,  16,  17,  18,  19,  20,  21,  22,  23,  24,  25,  26,  27,
     28,  29,   2,   2,  30,  31,  32,  33,   2,   2,   2,   2,   2,  34,  35,  36,
     37,  38,  39,  40,  41,  42,  43,  44,  45,  46,   2,  47,   2,   2,  48,  49,
     50,  51,   2,  52,   2,   2,   2,  53,  54,   2,   2,   2,   2,   2,   2,   2,
      2,   2,   2,   2,   2,   2,  55,  56,  57,  58,  59,  60,  61,  62,   2,  63,
     64,  65,  66,  67,  68,  69,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,
      2,   2,   2,  70,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,  71,
      2,  72,   2,   2,  73,  74,   2,  75,  76,  77,  78,  79,  80,  81,  82,  83,
      2,   2,   2,   2,   2,   2,   2,  84,  85,  85,  85,  85,  85,  85,  85,  85,
     85,  85,   2,   2,  86,  87,  88,  89,   2,   2,  90,  91,  92,  93,  94,  95,
     96,  53,  97,  98,  85,  99, 100, 101,   2, 102, 103,  85,   2,   2, 104,  85,
    105, 106, 107, 108, 109, 110, 111, 112, 113, 114,  85,  85, 115,  85,  85,  85,
    116, 117, 118, 119, 120, 121, 122,  85,  85, 123,  85, 124, 125, 126, 127,  85,
     85, 128,  85,  85,  85, 129,  85,  85,   2,   2,   2,   2,   2,   2,   2, 130,
    131,   2, 132,  85,  85,  85,  85,  85, 133,  85,  85,  85,  85,  85,  85,  85,
      2,   2,   2,   2, 134,  85,  85,  85,   2,   2,   2,   2, 135, 136, 137, 138,
     85,  85,  85,  85,  85,  85, 139, 140, 141,  85,  85,  85,  85,  85,  85,  85,
    142, 143,  85,  85,  85,  85,  85,  85,   2, 144, 145, 146, 147,  85, 148,  85,
    149, 150, 151,   2,   2, 152,   2, 153,   2,   2,   2,   2, 154, 155,  85,  85,
      2, 156,  85,  85,  85,  85,  85,  85,  85,  85,  85,  85, 157, 158,  85,  85,
    159, 160, 161, 162, 163,  85,   2,   2,   2,   2, 164, 165,   2, 166, 167, 168,
    169, 170, 171, 172,  85,  85,  85,  85,   2,   2,   2,   2,   2, 173,   2,   2,
      2,   2,   2,   2,   2,   2, 174,   2, 175,   2,   2,   2,   2,   2,   2,   2,
      2,   2,   2,   2,   2, 176,  85,  85,   2,   2,   2,   2, 177,  85,  85,  85,
};

static RE_UINT8 re_grapheme_base_stage_4[] = {
      0,   0,   1,   1,   1,   1,   1,   2,   0,   0,   3,   1,   1,   1,   1,   1,
      1,   1,   1,   1,   1,   1,   1,   1,   0,   0,   0,   0,   0,   0,   0,   4,
      5,   1,   6,   1,   1,   1,   1,   1,   7,   1,   1,   1,   1,   1,   1,   1,
      1,   1,   1,   8,   1,   9,   8,   1,  10,   0,   0,  11,  12,   1,  13,  14,
     15,  16,   1,   1,  13,   0,   1,   8,   1,   1,   1,   1,   1,  17,  18,   1,
     19,  20,   1,   0,  21,   1,   1,   1,   1,   1,  22,  23,   1,   1,  13,  24,
      1,  25,  26,   2,   1,  27,   0,   0,   0,   0,   1,  14,   0,   0,   0,   0,
     28,   1,   1,  29,  30,  31,  32,   1,  33,  34,  35,  36,  37,  38,  39,  40,
     41,  34,  35,  42,  43,  44,  15,  45,  46,   6,  35,  47,  48,  43,  39,  49,
     50,  34,  35,  51,  52,  38,  39,  53,  54,  55,  56,  57,  58,  43,  15,  13,
     59,  20,  35,  60,  61,  62,  39,  63,  64,  20,  35,  65,  66,  11,  39,  67,
     64,  20,   1,  68,  69,  70,  39,  71,  72,  73,   1,  74,  75,  76,  15,  45,
      8,   1,   1,  77,  78,  40,   0,   0,  79,  80,  81,  82,  83,  84,   0,   0,
      1,   4,   1,  85,  86,   1,  87,  70,  88,   0,   0,  89,  90,  13,   0,   0,
      1,   1,  87,  91,   1,  92,   8,  93,  94,   3,   1,   1,  95,   1,   1,   1,
      1,   1,   1,   1,  96,  97,   1,   1,  96,   1,   1,  98,  99, 100,   1,   1,
      1,  99,   1,   1,   1,  13,   1,  87,   1, 101,   1,   1,   1,   1,   1, 102,
      1,  87,   1,   1,   1,   1,   1, 103,   3, 104,   1, 105,   1, 104,   3,  43,
      1,   1,   1, 106, 107, 108, 101, 101,  13, 101,   1,   1,   1,   1,   1,  53,
      1,   1, 109,   1,   1,   1,   1,  22,   1,   2, 110, 111, 112,   1,  19,  14,
      1,   1,  40,   1, 101, 113,   1,   1,   1, 114,   1,   1,   1, 115, 116, 117,
    101, 101,  19,   0,   0,   0,   0,   0, 118,   1,   1, 119, 120,   1,  13, 108,
    121,   1, 122,   1,   1,   1, 123, 124,   1,   1,  40, 125, 126,   1,   1,   1,
      0,   0,   0,   0,  53, 127, 128, 129,   1,   1,   1,   1,   0,   0,   0,   0,
      1, 102,   1,   1, 102, 130,   1,  19,   1,   1,   1, 131, 131, 132,   1, 133,
     13,   1, 134,   1,   1,   1,   0,  32,   2,  87,   1,   2,   0,   0,   0,   0,
     40,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,  13,
      1,   1,  75,   0,  13,   0,   1,   1,   1,   1,   1,   1,   1,   1,   1, 135,
      1, 136,   1, 126,  35, 104, 137,   0,   1,   1,   2,   1,   1,   2,   1,   1,
      1,   1,   1,   1,   1,   1,   2, 138,   1,   1,  95,   1,   1,   1, 134,  43,
      1,  75, 139, 139, 139, 139,   0,   0,   1,   1,   1,   1, 117,   0,   0,   0,
      1, 140,   1,   1,   1,   1,   1, 141,   1,   1,   1,   1,   1,  22,   0,  40,
      1,   1, 101,   1,   8,   1,   1,   1,   1, 142,   1,   1,   1,   1,   1,   1,
    143,   1,  19,   8,   1,   1,   1,   1,   2,   1,   1,  13,   1,   1, 141,   1,
      1,   2,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   2,
      1,   1,   1,  22,   1,   1,   1,   1,   1,   1,   1,   1,   1,  22,   0,   0,
     87,   1,   1,   1,  75,   1,   1,   1,   1,   1,  40,   0,   1,   1,   2, 144,
      1,  19,   1,   1,   1,   1,   1, 145,   1,   1,  19,  53,   0,   0,   0, 146,
    147,   1, 148, 101,   1,   1,   1,  53,   1,   1,   1,   1, 149, 101,   0, 150,
      1,   1, 151,   1,  75, 152,   1,  87,  28,   1,   1, 153, 154, 155, 131,   2,
      1,   1, 156, 157, 158,  84,   1, 159,   1,   1,   1, 160, 161, 162, 163,  22,
    164, 165, 139,   1,   1,   1,  22,   1,   1,   1,   1,   1,   1,   1, 166, 101,
      1,   1, 141,   1, 142,   1,   1,  40,   0,   0,   0,   0,   0,   0,   0,   0,
      1,   1,   1,   1,   1,   1,  19,   1,   1,   1,   1,   1,   1, 101,   0,   0,
     75, 167,   1, 168, 169,   1,   1,   1,   1,   1,   1,   1, 104,  28,   1,   1,
      1,   1,   1,   1,   0,   1,   1,   1,   1, 121,   1,   1,  53,   0,   0,  19,
      0, 101,   0,   1,   1, 170, 171, 131,   1,   1,   1,   1,   1,   1,   1,  87,
      8,   1,   1,   1,   1,   1,   1,   1,   1,  19,   1,   2, 172, 173, 139, 174,
    159,   1, 100, 175,  19,  19,   0,   0, 176,   1,   1, 177,   1,   1,   1,   1,
     87,  40,  43,   0,   0,   1,   1,  87,   1,  87,   1,   1,   1,  43,   8,  40,
      1,   1, 141,   1,  13,   1,   1,  22,   1, 154,   1,   1, 178,  22,   0,   0,
      1,  19, 101,   0,   0,   0,   0,   0,   1,   1,  53,   1,   1,   1, 179,   0,
      1,   1,   1,  75,   1,  22,  53,   0, 180,   1,   1, 181,   1, 182,   1,   1,
      1,   2, 146,   0,   0,   0,   1, 183,   1, 184,   1,  57,   0,   0,   0,   0,
      1,   1,   1, 185,   1, 121,   1,   1,  43, 186,   1, 141,  53, 103,   1,   1,
      1,   1,   0,   0,   1,   1, 187,  75,   1,   1,   1,  71,   1, 136,   1, 188,
      1, 189, 190,   0,   0,   0,   0,   0,   1,   1,   1,   1, 103,   0,   0,   0,
      1,   1,   1, 117,   1,   1,   1,   7,   0,   0,   0,   0,   0,   0,   1,   2,
     20,   1,   1,  53, 191, 121,   1,   0, 121,   1,   1, 192, 104,   1, 103, 101,
     28,   1, 193,  15, 141,   1,   1, 194, 121,   1,   1, 195,  60,   1,   8,  14,
      1,   6,   2, 196,   0,   0,   0,   0, 197, 154, 101,   1,   1,   2, 117, 101,
     50,  34,  35, 198, 199, 200, 141,   0,   1,   1,   1, 201, 202, 101,   0,   0,
      1,   1,   2, 203,   8,  40,   0,   0,   1,   1,   1, 204,  61, 101,   0,   0,
      1,   1, 205, 206, 101,   0,   0,   0,   1, 101, 207,   1,   0,   0,   0,   0,
      0,   0,   1,   1,   1,   1,   1, 208,   0,   0,   0,   0,   1,   1,   1, 103,
      1, 101,   0,   0,   0,   0,   0,   0,   1,   1,   1,   1,   1,   1,   2,  14,
      1,   1,   1,   1, 141,   0,   0,   0,   1,   1,   2,   0,   0,   0,   0,   0,
      1,   1,   1,   1,  75,   0,   0,   0,   1,   1,   1, 103,   1,   2, 155,   0,
      0,   0,   0,   0,   0,   1,  19, 209,   1,   1,   1, 146,  22, 140,   6, 210,
      1,   0,   0,   0,   0,   0,   0,   0,   1,   1,   1,   1,  14,   1,   1,   2,
      0,  28,   0,   0,   0,   0,   0,   0, 104,   0,   0,   0,   0,   0,   0,   0,
      1,   1,   1,   1,   1,   1,  13,  87, 103, 211,   0,   0,   0,   0,   0,   0,
      1,   1,   1,   1,   1,   1,   1,  22,   1,   1,   9,   1,   1,   1, 212,   0,
    213,   1, 155,   1,   1,   1, 103,   0,   1,   1,   1,   1, 214,   0,   0,   0,
      1,   1,   1,   1,   1,  75,   1, 104,   1,   1,   1,   1,   1, 131,   1,   1,
      1,   3, 215,  29, 216,   1,   1,   1, 217, 218,   1, 219, 220,  20,   1,   1,
      1,   1, 136,   1,   1,   1,   1,   1,   1,   1,   1,   1, 163,   1,   1,   1,
      0,   0,   0, 221,   0,   0,  21, 131, 222,   0,   0,   0,   0,   0,   0,   0,
      1,   1,   1,   1, 223,   0,   0,   0, 216,   1, 224, 225, 226, 227, 228, 229,
    140,  40, 230,  40,   0,   0,   0, 104,   1,   1,  40,   1,   1,   1,   1,   1,
      1, 141,   2,   8,   8,   8,   1,  22,  87,   1,   2,   1,   1,   1,  40,   1,
      1,  13,   0,   0,   0,   0,  15,   1, 117,   1,   1,  13, 103, 104,   0,   0,
      1,   1,   1,   1,   1,   1,   1, 140,   1,   1, 216,   1,   1,   1,   1,   1,
      1,   1,   1,   1,   1,  43,  87, 141,   1,   1,   1,   1,   1,   1,   1, 141,
      1,   1,   1,   1,   1,  14,   0,   0,  40,   1,   1,   1,  53, 101,   1,   1,
     53,   1,  19,   0,   0,   0,   0,   0,   0, 103,   0,   0,   0,   0,   0,   0,
     14,   0,   0,   0,  43,   0,   0,   0,   1,   1,   1,   1,   1,  75,   0,   0,
      1,   1,   1,  14,   1,   1,   1,   1,   1,  19,   1,   1,   1,   1,   1,   1,
      1,   1, 104,   0,   0,   0,   0,   0,   1,  19,   0,   0,   0,   0,   0,   0,
};

static RE_UINT8 re_grapheme_base_stage_5[] = {
      0,   0, 255, 255, 255, 127, 255, 223, 255, 252, 240, 215, 251, 255,   7, 252,
    254, 255, 127, 254, 255, 230,   0,  64,  73,   0, 255,   7,  31,   0, 192, 255,
      0, 200,  63,  64,  96, 194, 255,  63, 253, 255,   0, 224,  63,   0,   2,   0,
    240,   7,  63,   4,  16,   1, 255,  65, 248, 255, 255, 235,   1, 222,   1, 255,
    243, 255, 237, 159, 249, 255, 255, 253, 197, 163, 129,  89,   0, 176, 195, 255,
    255,  15, 232, 135, 109, 195,   1,   0,   0,  94,  28,   0, 232, 191, 237, 227,
      1,  26,   3,   2, 236, 159, 237,  35, 129,  25, 255,   0, 232, 199,  61, 214,
     24, 199, 255, 131, 198,  29, 238, 223, 255,  35,  30,   0,   0,   7,   0, 255,
    236, 223, 239,  99, 155,  13,   6,   0, 255, 167, 193,  93,   0, 128,  63, 254,
    236, 255, 127, 252, 251,  47, 127,   0,   3, 127,  13, 128, 127, 128, 150,  37,
    240, 254, 174, 236,  13,  32,  95,   0, 255, 243,  95, 253, 255, 254, 255,  31,
     32,  31,   0, 192, 191, 223,   2, 153, 255,  60, 225, 255, 155, 223, 191,  32,
    255,  61, 127,  61,  61, 127,  61, 255, 127, 255, 255,   3,  63,  63, 255,   1,
      3,   0,  99,   0,  79, 192, 191,   1, 240,  31, 255,   5, 120,  14, 251,   1,
    241, 255, 255, 199, 127, 198, 191,   0,  26, 224,   7,   0, 240, 255,  47, 232,
    251,  15, 252, 255, 195, 196, 191,  92,  12, 240,  48, 248, 255, 227,   8,   0,
      2, 222, 111,   0, 255, 170, 223, 255, 207, 239, 220, 127, 255, 128, 207, 255,
     63, 255,   0, 240,  12, 254, 127, 127, 255, 251,  15,   0, 127, 248, 224, 255,
      8, 192, 252,   0, 128, 255, 187, 247, 159,  15,  15, 192, 252,  63,  63, 192,
     12, 128,  55, 236, 255, 191, 255, 195, 255, 129,  25,   0, 247,  47, 255, 239,
     98,  62,   5,   0,   0, 248, 255, 207, 126, 126, 126,   0, 223,  30, 248, 160,
    127,  95, 219, 255, 247, 255, 127,  15, 252, 252, 252,  28,   0,  48, 255, 183,
    135, 255, 143, 255,  15, 255,  15, 128,  63, 253, 191, 145, 191, 255,  55, 248,
    255, 143, 255, 240, 239, 254,  31, 248,   7, 255,   3,  30,   0, 254, 128,  63,
    135, 217, 127,  16, 119,   0,  63, 128,  44,  63, 127, 189, 237, 163, 158,  57,
      1, 224,   6,  90, 242,   0,   3,  79,   7,  88, 255, 215,  64,   0,  67,   0,
      7, 128,  32,   0, 255, 224, 255, 147,  95,  60,  24, 240,  35,   0, 100, 222,
    239, 255, 191, 231, 223, 223, 255, 123,  95, 252, 128,   7, 239,  15, 159, 255,
    150, 254, 247,  10, 132, 234, 150, 170, 150, 247, 247,  94, 238, 251,
};

/* Grapheme_Base: 2544 bytes. */

RE_UINT32 re_get_grapheme_base(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 15;
    code = ch ^ (f << 15);
    pos = (RE_UINT32)re_grapheme_base_stage_1[f] << 5;
    f = code >> 10;
    code ^= f << 10;
    pos = (RE_UINT32)re_grapheme_base_stage_2[pos + f] << 3;
    f = code >> 7;
    code ^= f << 7;
    pos = (RE_UINT32)re_grapheme_base_stage_3[pos + f] << 3;
    f = code >> 4;
    code ^= f << 4;
    pos = (RE_UINT32)re_grapheme_base_stage_4[pos + f] << 4;
    pos += code;
    value = (re_grapheme_base_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Grapheme_Link. */

static RE_UINT8 re_grapheme_link_stage_1[] = {
    0, 1, 2, 1, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1,
};

static RE_UINT8 re_grapheme_link_stage_2[] = {
     0,  0,  1,  2,  3,  4,  5,  0,  0,  0,  0,  6,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  7,  0,  0,  0,  0,  0,
     0,  0,  8,  0,  9, 10,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
};

static RE_UINT8 re_grapheme_link_stage_3[] = {
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  2,  3,  0,  0,  4,  5,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  6,  7,  0,  0,  0,  0,  8,  0,  9, 10,
     0,  0, 11,  0,  0,  0,  0,  0, 12,  9, 13, 14,  0, 15,  0, 16,
     0,  0,  0,  0, 17,  0,  0,  0, 18, 19, 20, 14, 21, 22,  1,  0,
     0, 23,  0, 17, 17, 24, 25,  0,
};

static RE_UINT8 re_grapheme_link_stage_4[] = {
     0,  0,  0,  0,  0,  0,  1,  0,  0,  0,  2,  0,  0,  3,  0,  0,
     4,  0,  0,  0,  0,  5,  0,  0,  6,  6,  0,  0,  0,  0,  7,  0,
     0,  0,  0,  8,  0,  0,  4,  0,  0,  9,  0, 10,  0,  0,  0, 11,
    12,  0,  0,  0,  0,  0, 13,  0,  0,  0,  8,  0,  0,  0,  0, 14,
     0,  0,  0,  1,  0, 11,  0,  0,  0,  0, 12, 11,  0, 15,  0,  0,
     0, 16,  0,  0,  0, 17,  0,  0,  0,  0,  0,  2,  0,  0, 18,  0,
     0, 14,  0,  0,  0, 19,  0,  0,
};

static RE_UINT8 re_grapheme_link_stage_5[] = {
      0,   0,   0,   0,   0,  32,   0,   0,   0,   4,   0,   0,   0,   0,   0,   4,
     16,   0,   0,   0,   0,   0,   0,   6,   0,   0,  16,   0,   0,   0,   4,   0,
      1,   0,   0,   0,   0,  12,   0,   0,   0,   0,  12,   0,   0,   0,   0, 128,
     64,   0,   0,   0,   0,   0,   8,   0,   0,   0,  64,   0,   0,   0,   0,   2,
      0,   0,  24,   0,   0,   0,  32,   0,   4,   0,   0,   0,   0,   8,   0,   0,
};

/* Grapheme_Link: 404 bytes. */

RE_UINT32 re_get_grapheme_link(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 14;
    code = ch ^ (f << 14);
    pos = (RE_UINT32)re_grapheme_link_stage_1[f] << 4;
    f = code >> 10;
    code ^= f << 10;
    pos = (RE_UINT32)re_grapheme_link_stage_2[pos + f] << 3;
    f = code >> 7;
    code ^= f << 7;
    pos = (RE_UINT32)re_grapheme_link_stage_3[pos + f] << 2;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_grapheme_link_stage_4[pos + f] << 5;
    pos += code;
    value = (re_grapheme_link_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* White_Space. */

static RE_UINT8 re_white_space_stage_1[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1,
};

static RE_UINT8 re_white_space_stage_2[] = {
    0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
};

static RE_UINT8 re_white_space_stage_3[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1,
    3, 1, 1, 1, 1, 1, 1, 1, 4, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
};

static RE_UINT8 re_white_space_stage_4[] = {
    0, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 3, 1, 1, 1, 1, 1, 4, 5, 1, 1, 1, 1, 1, 1,
    3, 1, 1, 1, 1, 1, 1, 1,
};

static RE_UINT8 re_white_space_stage_5[] = {
      0,  62,   0,   0,   1,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
     32,   0,   0,   0,   1,   0,   0,   0,   1,   0,   0,   0,   0,   0,   0,   0,
    255,   7,   0,   0,   0, 131,   0,   0,   0,   0,   0, 128,   0,   0,   0,   0,
};

/* White_Space: 169 bytes. */

RE_UINT32 re_get_white_space(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_white_space_stage_1[f] << 3;
    f = code >> 13;
    code ^= f << 13;
    pos = (RE_UINT32)re_white_space_stage_2[pos + f] << 4;
    f = code >> 9;
    code ^= f << 9;
    pos = (RE_UINT32)re_white_space_stage_3[pos + f] << 3;
    f = code >> 6;
    code ^= f << 6;
    pos = (RE_UINT32)re_white_space_stage_4[pos + f] << 6;
    pos += code;
    value = (re_white_space_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Bidi_Control. */

static RE_UINT8 re_bidi_control_stage_1[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1,
};

static RE_UINT8 re_bidi_control_stage_2[] = {
    0, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
};

static RE_UINT8 re_bidi_control_stage_3[] = {
    0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    2, 0, 0, 0, 0, 0, 0, 0,
};

static RE_UINT8 re_bidi_control_stage_4[] = {
    0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0,
    2, 3, 0, 0, 0, 0, 0, 0,
};

static RE_UINT8 re_bidi_control_stage_5[] = {
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  16,   0,   0,   0,   0,
      0, 192,   0,   0,   0, 124,   0,   0,   0,   0,   0,   0, 192,   3,   0,   0,
};

/* Bidi_Control: 129 bytes. */

RE_UINT32 re_get_bidi_control(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_bidi_control_stage_1[f] << 4;
    f = code >> 12;
    code ^= f << 12;
    pos = (RE_UINT32)re_bidi_control_stage_2[pos + f] << 3;
    f = code >> 9;
    code ^= f << 9;
    pos = (RE_UINT32)re_bidi_control_stage_3[pos + f] << 3;
    f = code >> 6;
    code ^= f << 6;
    pos = (RE_UINT32)re_bidi_control_stage_4[pos + f] << 6;
    pos += code;
    value = (re_bidi_control_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Join_Control. */

static RE_UINT8 re_join_control_stage_1[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1,
};

static RE_UINT8 re_join_control_stage_2[] = {
    0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
};

static RE_UINT8 re_join_control_stage_3[] = {
    0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0,
};

static RE_UINT8 re_join_control_stage_4[] = {
    0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0,
};

static RE_UINT8 re_join_control_stage_5[] = {
     0,  0,  0,  0,  0,  0,  0,  0,  0, 48,  0,  0,  0,  0,  0,  0,
};

/* Join_Control: 97 bytes. */

RE_UINT32 re_get_join_control(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_join_control_stage_1[f] << 4;
    f = code >> 12;
    code ^= f << 12;
    pos = (RE_UINT32)re_join_control_stage_2[pos + f] << 3;
    f = code >> 9;
    code ^= f << 9;
    pos = (RE_UINT32)re_join_control_stage_3[pos + f] << 3;
    f = code >> 6;
    code ^= f << 6;
    pos = (RE_UINT32)re_join_control_stage_4[pos + f] << 6;
    pos += code;
    value = (re_join_control_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Dash. */

static RE_UINT8 re_dash_stage_1[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1,
};

static RE_UINT8 re_dash_stage_2[] = {
    0, 1, 2, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5,
    4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
};

static RE_UINT8 re_dash_stage_3[] = {
    0, 1, 2, 1, 1, 1, 1, 1, 1, 1, 3, 1, 4, 1, 1, 1,
    5, 6, 1, 1, 1, 1, 1, 7, 8, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 9,
};

static RE_UINT8 re_dash_stage_4[] = {
     0,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  2,  1,  3,  1,  1,  1,  1,  1,  1,  1,
     4,  1,  1,  1,  1,  1,  1,  1,  5,  6,  7,  1,  1,  1,  1,  1,
     8,  1,  1,  1,  1,  1,  1,  1,  9,  3,  1,  1,  1,  1,  1,  1,
    10,  1, 11,  1,  1,  1,  1,  1, 12, 13,  1,  1, 14,  1,  1,  1,
};

static RE_UINT8 re_dash_stage_5[] = {
      0,   0,   0,   0,   0,  32,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   4,   0,   0,   0,   0,   0,  64,   1,   0,   0,   0,   0,   0,   0,   0,
     64,   0,   0,   0,   0,   0,   0,   0,   0,   0,  63,   0,   0,   0,   0,   0,
      0,   0,   8,   0,   0,   0,   0,   8,   0,   8,   0,   0,   0,   0,   0,   0,
      0,   0,   4,   0,   0,   0,   0,   0,   0,   0, 128,   4,   0,   0,   0,  12,
      0,   0,   0,  16,   0,   0,   1,   0,   0,   0,   0,   0,   1,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   6,   0,   0,   0,   0,   1,   8,   0,   0,   0,
      0,  32,   0,   0,   0,   0,   0,   0,
};

/* Dash: 297 bytes. */

RE_UINT32 re_get_dash(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_dash_stage_1[f] << 4;
    f = code >> 12;
    code ^= f << 12;
    pos = (RE_UINT32)re_dash_stage_2[pos + f] << 3;
    f = code >> 9;
    code ^= f << 9;
    pos = (RE_UINT32)re_dash_stage_3[pos + f] << 3;
    f = code >> 6;
    code ^= f << 6;
    pos = (RE_UINT32)re_dash_stage_4[pos + f] << 6;
    pos += code;
    value = (re_dash_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Hyphen. */

static RE_UINT8 re_hyphen_stage_1[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1,
};

static RE_UINT8 re_hyphen_stage_2[] = {
    0, 1, 2, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5,
    4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
};

static RE_UINT8 re_hyphen_stage_3[] = {
    0, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3, 1, 1, 1,
    4, 1, 1, 1, 1, 1, 1, 5, 6, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 7,
};

static RE_UINT8 re_hyphen_stage_4[] = {
    0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 2, 1, 3, 1, 1, 1, 1, 1, 1, 1,
    4, 1, 1, 1, 1, 1, 1, 1, 5, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 6, 1, 1, 1, 1, 1, 7, 1, 1, 8, 9, 1, 1,
};

static RE_UINT8 re_hyphen_stage_5[] = {
      0,   0,   0,   0,   0,  32,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   4,   0,   0,   0,   0,   0,   0,  64,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   3,   0,   0,   0,   0,   0,   0,   0, 128,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   8,   0,   0,   0,   0,   8,   0,   0,   0,
      0,  32,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  32,   0,   0,   0,
};

/* Hyphen: 241 bytes. */

RE_UINT32 re_get_hyphen(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_hyphen_stage_1[f] << 4;
    f = code >> 12;
    code ^= f << 12;
    pos = (RE_UINT32)re_hyphen_stage_2[pos + f] << 3;
    f = code >> 9;
    code ^= f << 9;
    pos = (RE_UINT32)re_hyphen_stage_3[pos + f] << 3;
    f = code >> 6;
    code ^= f << 6;
    pos = (RE_UINT32)re_hyphen_stage_4[pos + f] << 6;
    pos += code;
    value = (re_hyphen_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Quotation_Mark. */

static RE_UINT8 re_quotation_mark_stage_1[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1,
};

static RE_UINT8 re_quotation_mark_stage_2[] = {
    0, 1, 2, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 4,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
};

static RE_UINT8 re_quotation_mark_stage_3[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    2, 1, 1, 1, 1, 1, 1, 3, 4, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 5,
};

static RE_UINT8 re_quotation_mark_stage_4[] = {
    0, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    3, 1, 1, 1, 1, 1, 1, 1, 1, 4, 1, 1, 1, 1, 1, 1,
    5, 1, 1, 1, 1, 1, 1, 1, 1, 6, 1, 1, 7, 8, 1, 1,
};

static RE_UINT8 re_quotation_mark_stage_5[] = {
      0,   0,   0,   0, 132,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   8,   0,   8,   0,   0,   0, 255,   0,   0,   0,   6,
      4,   0,   0,   0,   0,   0,   0,   0,   0, 240,   0, 224,   0,   0,   0,   0,
     30,   0,   0,   0,   0,   0,   0,   0, 132,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,  12,   0,   0,   0,
};

/* Quotation_Mark: 209 bytes. */

RE_UINT32 re_get_quotation_mark(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_quotation_mark_stage_1[f] << 4;
    f = code >> 12;
    code ^= f << 12;
    pos = (RE_UINT32)re_quotation_mark_stage_2[pos + f] << 3;
    f = code >> 9;
    code ^= f << 9;
    pos = (RE_UINT32)re_quotation_mark_stage_3[pos + f] << 3;
    f = code >> 6;
    code ^= f << 6;
    pos = (RE_UINT32)re_quotation_mark_stage_4[pos + f] << 6;
    pos += code;
    value = (re_quotation_mark_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Terminal_Punctuation. */

static RE_UINT8 re_terminal_punctuation_stage_1[] = {
    0, 1, 2, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
    4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
    4, 4,
};

static RE_UINT8 re_terminal_punctuation_stage_2[] = {
     0,  1,  2,  3,  4,  5,  6,  7,  8,  9,  9, 10, 11,  9,  9,  9,
     9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,
     9,  9,  9,  9,  9,  9,  9,  9,  9, 12, 13,  9,  9,  9,  9,  9,
     9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9, 14,
    15,  9, 16,  9, 17, 18,  9,  9,  9, 19,  9,  9,  9,  9,  9,  9,
     9,  9,  9,  9,  9,  9,  9,  9,  9,  9, 20,  9,  9,  9,  9,  9,
     9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9, 21,
     9,  9,  9,  9,  9,  9, 22,  9,  9,  9,  9,  9,  9,  9,  9,  9,
     9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,
     9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,  9,
};

static RE_UINT8 re_terminal_punctuation_stage_3[] = {
     0,  1,  1,  1,  1,  1,  2,  3,  1,  1,  1,  4,  5,  6,  7,  8,
     9,  1, 10,  1,  1,  1,  1,  1,  1,  1,  1,  1, 11,  1, 12,  1,
    13,  1,  1,  1,  1,  1, 14,  1,  1,  1,  1,  1, 15, 16, 17, 18,
    19,  1, 20,  1,  1, 21, 22,  1, 23,  1,  1,  1,  1,  1,  1,  1,
    24,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1, 25,  1,  1,  1, 26,  1,  1,  1,  1,  1,  1,  1,
     1, 27,  1,  1, 28, 29,  1,  1, 30, 31, 32, 33, 34, 35,  1, 36,
     1,  1,  1,  1, 37,  1, 38,  1,  1,  1,  1,  1,  1,  1,  1, 39,
    40,  1, 41,  1, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51,  1,  1,
     1,  1,  1, 52, 53,  1, 54,  1, 55,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1, 56, 57, 58,  1,  1, 41,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1, 59,  1,  1,
};

static RE_UINT8 re_terminal_punctuation_stage_4[] = {
     0,  1,  0,  0,  0,  0,  0,  0,  0,  0,  0,  2,  3,  0,  0,  0,
     4,  0,  5,  0,  6,  0,  0,  0,  0,  0,  7,  0,  8,  0,  0,  0,
     0,  0,  0,  9,  0, 10,  2,  0,  0,  0,  0, 11,  0,  0, 12,  0,
    13,  0,  0,  0,  0,  0, 14,  0,  0,  0,  0, 15,  0,  0,  0, 16,
     0,  0,  0, 17,  0, 18,  0,  0,  0,  0, 19,  0, 20,  0,  0,  0,
     0,  0, 11,  0,  0, 21,  0,  0,  0,  0, 22,  0,  0, 23,  0, 24,
     0, 25, 26,  0,  0, 27, 28,  0, 29,  0,  0,  0,  0,  0,  0, 24,
    30,  0,  0,  0,  0,  0,  0, 31,  0,  0,  0, 32,  0,  0, 33,  0,
     0, 34,  0,  0,  0,  0, 26,  0,  0,  0, 35,  0,  0,  0, 36, 37,
     0,  0,  0, 38,  0,  0, 39,  0,  1,  0,  0, 40, 36,  0, 41,  0,
     0,  0, 42,  0, 36,  0,  0,  0,  0,  0, 32,  0,  0,  0,  0, 43,
     0, 44,  0,  0, 45,  0,  0,  0,  0,  0, 46,  0,  0, 24, 47,  0,
     0,  0, 48,  0,  0,  0, 49,  0,  0, 50,  0,  0,  0,  4,  0,  0,
     0,  0, 51,  0,  0,  0, 29,  0,  0, 52,  0,  0,  0,  0,  0, 53,
     0,  0,  0, 33,  0,  0,  0, 54,  0, 55, 56,  0, 57,  0,  0,  0,
};

static RE_UINT8 re_terminal_punctuation_stage_5[] = {
      0,   0,   0,   0,   2,  80,   0, 140,   0,   0,   0,  64, 128,   0,   0,   0,
      0,   2,   0,   0,   8,   0,   0,   0,   0,  16,   0, 136,   0,   0,  16,   0,
    255,  23,   0,   0,   0,   0,   0,   3,   0,   0, 255, 127,  48,   0,   0,   0,
      0,   0,   0,  12,   0, 225,   7,   0,   0,  12,   0,   0, 254,   1,   0,   0,
      0,  96,   0,   0,   0,  56,   0,   0,   0,   0,  96,   0,   0,   0, 112,   4,
     60,   3,   0,   0,   0,  15,   0,   0,   0,   0,   0, 236,   0,   0,   0, 248,
      0,   0,   0, 192,   0,   0,   0,  48, 128,   3,   0,   0,   0,  64,   0,  16,
      2,   0,   0,   0,   6,   0,   0,   0,   0, 224,   0,   0,   0,   0, 248,   0,
      0,   0, 192,   0,   0, 192,   0,   0,   0, 128,   0,   0,   0,   0,   0, 224,
      0,   0,   0, 128,   0,   0,   3,   0,   0,   8,   0,   0,   0,   0, 247,   0,
     18,   0,   0,   0,   0,   0,   1,   0,   0,   0, 128,   0,   0,   0,  63,   0,
      0,   0,   0, 252,   0,   0,   0,  30, 128,  63,   0,   0,   3,   0,   0,   0,
     14,   0,   0,   0,  96,  32,   0, 192,   0,   0,   0,  31,  60, 254, 255,   0,
      0,   0,   0, 112,   0,   0,  31,   0,   0,   0,  32,   0,   0,   0, 128,   3,
     16,   0,   0,   0, 128,   7,   0,   0,
};

/* Terminal_Punctuation: 850 bytes. */

RE_UINT32 re_get_terminal_punctuation(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 15;
    code = ch ^ (f << 15);
    pos = (RE_UINT32)re_terminal_punctuation_stage_1[f] << 5;
    f = code >> 10;
    code ^= f << 10;
    pos = (RE_UINT32)re_terminal_punctuation_stage_2[pos + f] << 3;
    f = code >> 7;
    code ^= f << 7;
    pos = (RE_UINT32)re_terminal_punctuation_stage_3[pos + f] << 2;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_terminal_punctuation_stage_4[pos + f] << 5;
    pos += code;
    value = (re_terminal_punctuation_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Other_Math. */

static RE_UINT8 re_other_math_stage_1[] = {
    0, 1, 2, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2,
};

static RE_UINT8 re_other_math_stage_2[] = {
    0, 1, 1, 1, 2, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 4,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 5, 1, 1, 6, 1, 1,
};

static RE_UINT8 re_other_math_stage_3[] = {
     0,  1,  1,  2,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     3,  4,  1,  5,  1,  6,  7,  8,  1,  9,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1, 10, 11,  1,  1,  1,  1, 12, 13, 14, 15,
     1,  1,  1,  1,  1,  1, 16,  1,
};

static RE_UINT8 re_other_math_stage_4[] = {
     0,  0,  1,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  2,  3,  4,  5,  6,  7,  8,  0,  9, 10,
    11, 12, 13,  0, 14, 15, 16, 17, 18,  0,  0,  0,  0, 19, 20, 21,
     0,  0,  0,  0,  0, 22, 23, 24, 25,  0, 26, 27,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0, 25, 28,  0,  0,  0,  0, 29,  0, 30, 31,
     0,  0,  0, 32,  0,  0,  0,  0,  0, 33,  0,  0,  0,  0,  0,  0,
    34, 34, 35, 34, 36, 37, 38, 34, 39, 40, 41, 34, 34, 34, 34, 34,
    34, 34, 34, 34, 34, 42, 43, 44, 35, 35, 45, 45, 46, 46, 47, 34,
    38, 48, 49, 50, 51, 52,  0,  0,
};

static RE_UINT8 re_other_math_stage_5[] = {
      0,   0,   0,   0,   0,   0,   0,  64,   0,   0,  39,   0,   0,   0,  51,   0,
      0,   0,  64,   0,   0,   0,  28,   0,   1,   0,   0,   0,  30,   0,   0,  96,
      0,  96,   0,   0,   0,   0, 255,  31,  98, 248,   0,   0, 132, 252,  47,  62,
     16, 179, 251, 241, 224,   3,   0,   0,   0,   0, 224, 243, 182,  62, 195, 240,
    255,  63, 235,  47,  48,   0,   0,   0,   0,  15,   0,   0,   0,   0, 176,   0,
      0,   0,   1,   0,   4,   0,   0,   0,   3, 192, 127, 240, 193, 140,  15,   0,
    148,  31,   0,   0,  96,   0,   0,   0,   5,   0,   0,   0,  15,  96,   0,   0,
    192, 255,   0,   0, 248, 255, 255,   1,   0,   0,   0,  15,   0,   0,   0,  48,
     10,   1,   0,   0,   0,   0,   0,  80, 255, 255, 255, 255, 255, 255, 223, 255,
    255, 255, 255, 223, 100, 222, 255, 235, 239, 255, 255, 255, 191, 231, 223, 223,
    255, 255, 255, 123,  95, 252, 253, 255,  63, 255, 255, 255, 253, 255, 255, 247,
    255, 255, 255, 247, 255, 127, 255, 255, 255, 253, 255, 255, 247, 207, 255, 255,
    150, 254, 247,  10, 132, 234, 150, 170, 150, 247, 247,  94, 255, 251, 255,  15,
    238, 251, 255,  15,
};

/* Other_Math: 502 bytes. */

RE_UINT32 re_get_other_math(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 15;
    code = ch ^ (f << 15);
    pos = (RE_UINT32)re_other_math_stage_1[f] << 4;
    f = code >> 11;
    code ^= f << 11;
    pos = (RE_UINT32)re_other_math_stage_2[pos + f] << 3;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_other_math_stage_3[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_other_math_stage_4[pos + f] << 5;
    pos += code;
    value = (re_other_math_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Hex_Digit. */

static RE_UINT8 re_hex_digit_stage_1[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1,
};

static RE_UINT8 re_hex_digit_stage_2[] = {
    0, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1,
};

static RE_UINT8 re_hex_digit_stage_3[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 2,
};

static RE_UINT8 re_hex_digit_stage_4[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 2, 1,
};

static RE_UINT8 re_hex_digit_stage_5[] = {
      0,   0,   0,   0,   0,   0, 255,   3, 126,   0,   0,   0, 126,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0, 255,   3, 126,   0,   0,   0, 126,   0,   0,   0,   0,   0,   0,   0,
};

/* Hex_Digit: 129 bytes. */

RE_UINT32 re_get_hex_digit(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_hex_digit_stage_1[f] << 3;
    f = code >> 13;
    code ^= f << 13;
    pos = (RE_UINT32)re_hex_digit_stage_2[pos + f] << 3;
    f = code >> 10;
    code ^= f << 10;
    pos = (RE_UINT32)re_hex_digit_stage_3[pos + f] << 3;
    f = code >> 7;
    code ^= f << 7;
    pos = (RE_UINT32)re_hex_digit_stage_4[pos + f] << 7;
    pos += code;
    value = (re_hex_digit_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* ASCII_Hex_Digit. */

static RE_UINT8 re_ascii_hex_digit_stage_1[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1,
};

static RE_UINT8 re_ascii_hex_digit_stage_2[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
};

static RE_UINT8 re_ascii_hex_digit_stage_3[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
};

static RE_UINT8 re_ascii_hex_digit_stage_4[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
};

static RE_UINT8 re_ascii_hex_digit_stage_5[] = {
      0,   0,   0,   0,   0,   0, 255,   3, 126,   0,   0,   0, 126,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
};

/* ASCII_Hex_Digit: 97 bytes. */

RE_UINT32 re_get_ascii_hex_digit(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_ascii_hex_digit_stage_1[f] << 3;
    f = code >> 13;
    code ^= f << 13;
    pos = (RE_UINT32)re_ascii_hex_digit_stage_2[pos + f] << 3;
    f = code >> 10;
    code ^= f << 10;
    pos = (RE_UINT32)re_ascii_hex_digit_stage_3[pos + f] << 3;
    f = code >> 7;
    code ^= f << 7;
    pos = (RE_UINT32)re_ascii_hex_digit_stage_4[pos + f] << 7;
    pos += code;
    value = (re_ascii_hex_digit_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Other_Alphabetic. */

static RE_UINT8 re_other_alphabetic_stage_1[] = {
    0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2,
};

static RE_UINT8 re_other_alphabetic_stage_2[] = {
     0,  1,  2,  3,  4,  5,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     6,  6,  6,  6,  7,  8,  6,  6,  6,  6,  6,  6,  6,  6,  6,  9,
    10, 11, 12,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6, 13,  6,  6,
     6,  6,  6,  6,  6,  6,  6, 14,  6,  6,  6,  6,  6,  6, 15,  6,
     6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
};

static RE_UINT8 re_other_alphabetic_stage_3[] = {
     0,  0,  0,  1,  0,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12,
    13,  0,  0, 14,  0,  0,  0, 15, 16, 17, 18, 19, 20, 21,  0,  0,
     0,  0,  0,  0, 22,  0,  0,  0,  0,  0,  0,  0,  0, 23,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 24,  0,
    25, 26, 27, 28,  0,  0,  0,  0,  0,  0,  0, 29,  0,  0,  0,  0,
     0,  0,  0, 30,  0,  0,  0,  0,  0,  0, 31,  0,  0,  0,  0,  0,
    32, 33, 34, 35, 36, 37, 38, 39,  0,  0,  0, 40,  0,  0,  0, 41,
     0,  0,  0,  0, 42,  0,  0,  0,  0, 43,  0,  0,  0,  0,  0,  0,
};

static RE_UINT8 re_other_alphabetic_stage_4[] = {
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  1,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  2,  3,  0,  4,  0,  5,  6,  0,  0,  7,  8,
     9, 10,  0,  0,  0, 11,  0,  0, 12, 13,  0,  0,  0,  0,  0, 14,
    15, 16, 17, 18, 19, 20, 21, 18, 19, 20, 22, 23, 19, 20, 24, 18,
    19, 20, 25, 18, 26, 20, 27,  0, 15, 20, 28, 18, 19, 20, 28, 18,
    19, 20, 29, 18, 18,  0, 30, 31,  0, 32, 33,  0,  0, 34, 33,  0,
     0,  0,  0, 35, 36, 37,  0,  0,  0, 38, 39, 40, 41,  0,  0,  0,
     0,  0, 42,  0,  0,  0,  0,  0, 31, 31, 31, 31,  0, 43, 44,  0,
     0,  0,  0,  0,  0, 45,  0,  0,  0, 46,  0,  0,  0,  0,  0,  0,
    47,  0, 48, 49,  0,  0,  0,  0, 50, 51, 15,  0, 52, 53,  0, 54,
     0, 55,  0,  0,  0,  0,  0, 31,  0,  0,  0,  0,  0,  0,  0, 56,
     0,  0,  0,  0,  0, 43, 57, 58,  0,  0,  0,  0,  0,  0,  0, 57,
     0,  0,  0, 59, 20,  0,  0,  0,  0, 60,  0,  0, 61, 62, 15,  0,
     0, 63, 64,  0, 15, 62,  0,  0,  0, 65, 66,  0,  0, 67,  0, 68,
     0,  0,  0,  0,  0,  0,  0, 69, 70,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0, 71,  0,  0,  0,  0, 72,  0,  0,  0,  0,  0,  0,  0,
    52, 73, 74,  0, 26, 75,  0,  0, 52, 64,  0,  0, 52, 76,  0,  0,
     0, 77,  0,  0,  0,  0, 42, 44, 15, 20, 21, 18,  0,  0,  0,  0,
     0,  0,  0,  0,  0, 10, 61,  0,  0,  0,  0,  0,  0, 78, 79,  0,
     0, 80, 81,  0,  0, 82,  0,  0, 83, 84,  0,  0,  0,  0,  0,  0,
     0, 85,  0,  0,  0,  0,  0,  0,  0,  0, 35, 86,  0,  0,  0,  0,
     0,  0,  0,  0, 70,  0,  0,  0,  0, 10, 87, 87, 58,  0,  0,  0,
};

static RE_UINT8 re_other_alphabetic_stage_5[] = {
      0,   0,   0,   0,  32,   0,   0,   0,   0,   0, 255, 191, 182,   0,   0,   0,
      0,   0, 255,   7,   0, 248, 255, 254,   0,   0,   1,   0,   0,   0, 192,  31,
    158,  33,   0,   0,   0,   0,   2,   0,   0,   0, 255, 255, 192, 255,   1,   0,
      0,   0, 192, 248, 239,  30,   0,   0, 248,   3, 255, 255,  15,   0,   0,   0,
      0,   0,   0, 204, 255, 223, 224,   0,  12,   0,   0,   0,  14,   0,   0,   0,
      0,   0,   0, 192, 159,  25, 128,   0, 135,  25,   2,   0,   0,   0,  35,   0,
    191,  27,   0,   0, 159,  25, 192,   0,   4,   0,   0,   0, 199,  29, 128,   0,
    223,  29,  96,   0, 223,  29, 128,   0,   0, 128,  95, 255,   0,   0,  12,   0,
      0,   0, 242,   7,   0,  32,   0,   0,   0,   0, 242,  27,   0,   0, 254, 255,
      3, 224, 255, 254, 255, 255, 255,  31,   0, 248, 127, 121,   0,   0, 192, 195,
    133,   1,  30,   0, 124,   0,   0,  48,   0,   0,   0, 128,   0,   0, 192, 255,
    255,   1,   0,   0,   0,   2,   0,   0, 255,  15, 255,   1,   0,   0, 128,  15,
      0,   0, 224, 127, 254, 255,  31,   0,  31,   0,   0,   0,   0,   0, 224, 255,
      7,   0,   0,   0, 254,  51,   0,   0, 128, 255,   3,   0, 240, 255,  63,   0,
    128, 255,  31,   0, 255, 255, 255, 255, 255,   3,   0,   0,   0,   0, 240,  15,
    248,   0,   0,   0,   3,   0,   0,   0,   0,   0, 240, 255, 192,   7,   0,   0,
    128, 255,   7,   0,   0, 254, 127,   0,   8,  48,   0,   0,   0,   0, 157,  65,
      0, 248,  32,   0, 248,   7,   0,   0,   0,   0,   0,  64,   0,   0, 192,   7,
    110, 240,   0,   0,   0,   0,   0, 255,  63,   0,   0,   0,   0,   0, 255,   1,
      0,   0, 248, 255,   0, 240, 159,   0,   0, 128,  63, 127,   0,   0,   0,  48,
      0,   0, 255, 127,   1,   0,   0,   0,   0, 248,  63,   0,   0,   0,   0, 224,
    255,   7,   0,   0,   0,   0, 127,   0, 255, 255, 255, 127, 255,   3, 255, 255,
};

/* Other_Alphabetic: 945 bytes. */

RE_UINT32 re_get_other_alphabetic(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_other_alphabetic_stage_1[f] << 5;
    f = code >> 11;
    code ^= f << 11;
    pos = (RE_UINT32)re_other_alphabetic_stage_2[pos + f] << 3;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_other_alphabetic_stage_3[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_other_alphabetic_stage_4[pos + f] << 5;
    pos += code;
    value = (re_other_alphabetic_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Ideographic. */

static RE_UINT8 re_ideographic_stage_1[] = {
    0, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1,
};

static RE_UINT8 re_ideographic_stage_2[] = {
     0,  0,  0,  0,  0,  0,  1,  2,  2,  3,  2,  2,  2,  2,  2,  2,
     2,  2,  2,  4,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  5,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,
     2,  2,  2,  2,  6,  2,  7,  8,  2,  9,  0,  0,  0,  0,  0, 10,
};

static RE_UINT8 re_ideographic_stage_3[] = {
     0,  0,  0,  0,  0,  0,  0,  0,  1,  0,  0,  0,  2,  2,  2,  2,
     2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  3,  2,  2,
     2,  2,  2,  2,  2,  2,  2,  4,  0,  2,  5,  0,  0,  0,  0,  0,
     2,  2,  2,  2,  2,  2,  6,  2,  2,  2,  2,  2,  2,  2,  2,  7,
     8,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  9,  0,
     2,  2, 10,  0,  0,  0,  0,  0,
};

static RE_UINT8 re_ideographic_stage_4[] = {
     0,  0,  0,  0,  0,  0,  0,  0,  1,  2,  0,  0,  0,  0,  0,  0,
     3,  3,  3,  3,  3,  3,  3,  3,  3,  3,  3,  3,  3,  4,  0,  0,
     3,  3,  3,  3,  3,  3,  4,  0,  3,  3,  3,  5,  3,  3,  6,  0,
     3,  3,  3,  3,  3,  3,  7,  0,  3,  8,  3,  3,  3,  3,  3,  3,
     9,  3,  3,  3,  3,  3,  3,  3,  3,  3,  3,  3,  3, 10,  0,  0,
     9,  0,  0,  0,  0,  0,  0,  0,
};

static RE_UINT8 re_ideographic_stage_5[] = {
      0,   0,   0,   0, 192,   0,   0,   0, 254,   3,   0,   7, 255, 255, 255, 255,
    255, 255,  63,   0, 255,  63, 255, 255, 255, 255, 255,   3, 255, 255, 127,   0,
    255, 255,  31,   0, 255, 255, 255,  63,   3,   0,   0,   0,
};

/* Ideographic: 333 bytes. */

RE_UINT32 re_get_ideographic(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_ideographic_stage_1[f] << 5;
    f = code >> 11;
    code ^= f << 11;
    pos = (RE_UINT32)re_ideographic_stage_2[pos + f] << 3;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_ideographic_stage_3[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_ideographic_stage_4[pos + f] << 5;
    pos += code;
    value = (re_ideographic_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Diacritic. */

static RE_UINT8 re_diacritic_stage_1[] = {
    0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2,
};

static RE_UINT8 re_diacritic_stage_2[] = {
     0,  1,  2,  3,  4,  5,  6,  4,  4,  4,  4,  4,  4,  4,  4,  4,
     4,  4,  4,  4,  7,  8,  4,  4,  4,  4,  4,  4,  4,  4,  4,  9,
    10, 11, 12,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4, 13,  4,  4,
     4,  4,  4,  4,  4,  4,  4,  4,  4,  4, 14,  4,  4, 15,  4,  4,
     4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,
     4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,
};

static RE_UINT8 re_diacritic_stage_3[] = {
     0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15,
    16,  1,  1,  1,  1,  1,  1, 17,  1, 18, 19, 20, 21, 22,  1, 23,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1, 24,  1, 25,  1,
    26,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1, 27, 28,
    29, 30, 31, 32,  1,  1,  1,  1,  1,  1,  1, 33,  1,  1, 34, 35,
     1,  1, 36,  1,  1,  1,  1,  1,  1,  1, 37,  1,  1,  1,  1,  1,
    38, 39, 40, 41, 42, 43, 44, 45,  1,  1, 46,  1,  1,  1,  1, 47,
     1, 48,  1,  1,  1,  1,  1,  1, 49,  1,  1,  1,  1,  1,  1,  1,
};

static RE_UINT8 re_diacritic_stage_4[] = {
     0,  0,  1,  2,  0,  3,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  4,  5,  5,  5,  5,  6,  7,  8,  0,  0,  0,
     0,  0,  0,  0,  9,  0,  0,  0,  0,  0, 10,  0, 11, 12, 13,  0,
     0,  0, 14,  0,  0,  0, 15, 16,  0,  4, 17,  0,  0, 18,  0, 19,
    20,  0,  0,  0,  0,  0,  0, 21,  0, 22, 23, 24,  0, 22, 25,  0,
     0, 22, 25,  0,  0, 22, 25,  0,  0, 22, 25,  0,  0,  0, 25,  0,
     0,  0, 25,  0,  0, 22, 25,  0,  0,  0, 25,  0,  0,  0, 26,  0,
     0,  0, 27,  0,  0,  0, 28,  0, 20, 29,  0,  0, 30,  0, 31,  0,
     0, 32,  0,  0, 33,  0,  0,  0,  0,  0,  0,  0,  0,  0, 34,  0,
     0, 35,  0,  0,  0,  0,  0,  0,  0,  0,  0, 36,  0, 37,  0,  0,
     0, 38, 39, 40,  0, 41,  0,  0,  0, 42,  0, 43,  0,  0,  4, 44,
     0, 45,  5, 17,  0,  0, 46, 47,  0,  0,  0,  0,  0, 48, 49, 50,
     0,  0,  0,  0,  0,  0,  0, 51,  0, 52,  0,  0,  0,  0,  0,  0,
     0, 53,  0,  0, 54,  0,  0, 22,  0,  0,  0, 55, 56,  0,  0, 57,
    58, 59,  0,  0, 60,  0,  0, 20,  0,  0,  0,  0,  0,  0, 39, 61,
     0, 62, 63,  0,  0, 63,  2, 64,  0,  0,  0, 65,  0, 15, 66, 67,
     0,  0, 68,  0,  0,  0,  0, 69,  1,  0,  0,  0,  0,  0,  0,  0,
     0, 70,  0,  0,  0,  0,  0,  0,  0,  1,  2, 71, 72,  0,  0, 73,
     0,  0,  0,  0,  0,  0,  0,  2,  0,  0,  0,  0,  0,  0,  0, 74,
     0,  0,  0,  0,  0, 75,  0,  0,  0, 76,  0, 63,  0,  0, 77,  0,
     0, 78,  0,  0,  0,  0,  0, 79,  0, 22, 25, 80,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0, 81,  0,  0,  0,  0,  0,  0, 15,  2,  0,
     0, 15,  0,  0,  0, 42,  0,  0,  0, 82,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0, 83,  0,  0,  0,  0, 84,  0,  0,  0,
     0,  0,  0, 85, 86, 87,  0,  0,  0,  0,  0,  0,  0,  0, 88,  0,
};

static RE_UINT8 re_diacritic_stage_5[] = {
      0,   0,   0,   0,   0,   0,   0,  64,   1,   0,   0,   0,   0, 129, 144,   1,
      0,   0, 255, 255, 255, 255, 255, 255, 255, 127, 255, 224,   7,   0,  48,   4,
     48,   0,   0,   0, 248,   0,   0,   0,   0,   0,   0,   2,   0,   0, 254, 255,
    251, 255, 255, 191,  22,   0,   0,   0,   0, 248, 135,   1,   0,   0,   0, 128,
     97,  28,   0,   0, 255,   7,   0,   0, 192, 255,   1,   0,   0, 248,  63,   0,
      0,   0,   0,   3, 248, 255, 255, 127,   0,   0,   0,  16,   0,  32,  30,   0,
      0,   0,   2,   0,   0,  32,   0,   0,   0,   4,   0,   0, 128,  95,   0,   0,
      0,  31,   0,   0,   0,   0, 160, 194, 220,   0,   0,   0,  64,   0,   0,   0,
      0,   0, 128,   6, 128, 191,   0,  12,   0, 254,  15,  32,   0,   0,   0,  14,
      0,   0, 224, 159,   0,   0, 255,  63,   0,   0,  16,   0,  16,   0,   0,   0,
      0, 248,  15,   0,   0,  12,   0,   0,   0,   0, 192,   0,   0,   0,   0,  63,
    255,  33,  16,   3,   0, 240, 255, 255, 240, 255,   0,   0,   0,   0,  32, 224,
      0,   0,   0, 160,   3, 224,   0, 224,   0, 224,   0,  96,   0, 128,   3,   0,
      0, 128,   0,   0,   0, 252,   0,   0,   0,   0,   0,  30,   0, 128,   0, 176,
      0,   0,   0,  48,   0,   0,   3,   0,   0,   0, 128, 255,   3,   0,   0,   0,
      0,   1,   0,   0, 255, 255,   3,   0,   0, 120,   0,   0,   0,   0,   8,   0,
     32,   0,   0,   0,   0,   0,   0,  56,   7,   0,   0,   0,   0,   0,  64,   0,
      0,   0,   0, 248,   0,  48,   0,   0, 255, 255,   0,   0,   0,   0,   1,   0,
      0,   0,   0, 192,   8,   0,   0,   0,  96,   0,   0,   0,   0,   0,   0,   6,
      0,   0,  24,   0,   1,  28,   0,   0,   0,   0,  96,   0,   0,   6,   0,   0,
    192,  31,  31,   0,  12,   0,   0,   0,   0,   8,   0,   0,   0,   0,  31,   0,
      0, 128, 255, 255, 128, 227,   7, 248, 231,  15,   0,   0,   0,  60,   0,   0,
      0,   0, 127,   0,
};

/* Diacritic: 997 bytes. */

RE_UINT32 re_get_diacritic(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_diacritic_stage_1[f] << 5;
    f = code >> 11;
    code ^= f << 11;
    pos = (RE_UINT32)re_diacritic_stage_2[pos + f] << 3;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_diacritic_stage_3[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_diacritic_stage_4[pos + f] << 5;
    pos += code;
    value = (re_diacritic_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Extender. */

static RE_UINT8 re_extender_stage_1[] = {
    0, 1, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
    3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
    3, 3,
};

static RE_UINT8 re_extender_stage_2[] = {
    0, 1, 2, 3, 2, 2, 4, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 5, 6, 2, 2, 2, 2, 2, 2, 2, 2, 2, 7,
    2, 2, 8, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 9, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
};

static RE_UINT8 re_extender_stage_3[] = {
     0,  1,  2,  1,  1,  1,  3,  4,  1,  1,  1,  1,  1,  1,  5,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  6,  1,  7,  1,  8,  1,  1,  1,
     9,  1,  1,  1,  1,  1,  1,  1, 10,  1,  1,  1,  1,  1, 11,  1,
     1, 12, 13,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1, 14,
     1,  1,  1, 15,  1, 16,  1,  1,  1,  1,  1, 17,  1,  1,  1,  1,
};

static RE_UINT8 re_extender_stage_4[] = {
     0,  0,  0,  0,  0,  1,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  2,  0,  0,  0,  3,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  4,  0,  0,  5,  0,  0,  0,  5,  0,
     6,  0,  7,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  8,  0,  0,
     0,  9,  0, 10,  0,  0,  0,  0, 11, 12,  0,  0, 13,  0,  0, 14,
    15,  0,  0,  0,  0,  0,  0,  0, 16,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0, 17,  5,  0,  0,  0, 18,  0,  0, 19, 20,
     0,  0,  0, 18,  0,  0,  0,  0,  0,  0, 19,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0, 21,  0,  0,  0, 22,  0,  0,  0,  0,  0,
};

static RE_UINT8 re_extender_stage_5[] = {
      0,   0,   0,   0,   0,   0, 128,   0,   0,   0,   3,   0,   1,   0,   0,   0,
      0,   0,   0,   4,  64,   0,   0,   0,   0,   4,   0,   0,   8,   0,   0,   0,
    128,   0,   0,   0,   0,   0,  64,   0,   0,   0,   0,   8,  32,   0,   0,   0,
      0,   0,  62,   0,   0,   0,   0,  96,   0,   0,   0, 112,   0,   0,  32,   0,
      0,  16,   0,   0,   0, 128,   0,   0,   0,   0,   1,   0,   0,   0,   0,  32,
      0,   0,  24,   0, 192,   1,   0,   0,  12,   0,   0,   0,
};

/* Extender: 414 bytes. */

RE_UINT32 re_get_extender(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 15;
    code = ch ^ (f << 15);
    pos = (RE_UINT32)re_extender_stage_1[f] << 4;
    f = code >> 11;
    code ^= f << 11;
    pos = (RE_UINT32)re_extender_stage_2[pos + f] << 3;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_extender_stage_3[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_extender_stage_4[pos + f] << 5;
    pos += code;
    value = (re_extender_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Other_Lowercase. */

static RE_UINT8 re_other_lowercase_stage_1[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1,
};

static RE_UINT8 re_other_lowercase_stage_2[] = {
    0, 1, 2, 3, 3, 3, 3, 3, 3, 3, 4, 3, 3, 3, 3, 3,
    3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
};

static RE_UINT8 re_other_lowercase_stage_3[] = {
    0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 2,
    4, 2, 5, 2, 2, 2, 6, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 7, 2, 8, 2, 2,
};

static RE_UINT8 re_other_lowercase_stage_4[] = {
     0,  0,  1,  0,  0,  0,  0,  0,  0,  0,  2,  3,  0,  4,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  5,  6,  7,  0,
     0,  8,  9,  0,  0, 10,  0,  0,  0,  0,  0, 11,  0,  0,  0,  0,
     0, 12,  0,  0,  0,  0,  0,  0,  0,  0, 13,  0,  0, 14,  0, 15,
     0,  0,  0,  0,  0, 16,  0,  0,
};

static RE_UINT8 re_other_lowercase_stage_5[] = {
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   4,   0,   4,
      0,   0,   0,   0,   0,   0, 255,   1,   3,   0,   0,   0,  31,   0,   0,   0,
     32,   0,   0,   0,   0,   0,   0,   4,   0,   0,   0,   0,   0, 240, 255, 255,
    255, 255, 255, 255, 255,   7,   0,   1,   0,   0,   0, 248, 255, 255, 255, 255,
      0,   0,   0,   0,   0,   0,   2, 128,   0,   0, 255,  31,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0, 255, 255,   0,   0, 255, 255, 255,   3,   0,   0,
      0,   0,   0,   0,   0,   0,   0,  48,   0,   0,   0,  48,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   1,   0,   0,   0,   0,   0,   0,   0,   0,   3,
      0,   0,   0, 240,   0,   0,   0,   0,
};

/* Other_Lowercase: 297 bytes. */

RE_UINT32 re_get_other_lowercase(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_other_lowercase_stage_1[f] << 4;
    f = code >> 12;
    code ^= f << 12;
    pos = (RE_UINT32)re_other_lowercase_stage_2[pos + f] << 3;
    f = code >> 9;
    code ^= f << 9;
    pos = (RE_UINT32)re_other_lowercase_stage_3[pos + f] << 3;
    f = code >> 6;
    code ^= f << 6;
    pos = (RE_UINT32)re_other_lowercase_stage_4[pos + f] << 6;
    pos += code;
    value = (re_other_lowercase_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Other_Uppercase. */

static RE_UINT8 re_other_uppercase_stage_1[] = {
    0, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1,
};

static RE_UINT8 re_other_uppercase_stage_2[] = {
    0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0,
};

static RE_UINT8 re_other_uppercase_stage_3[] = {
    0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 2, 0, 0, 0,
    0, 3, 0, 0, 0, 0, 0, 0,
};

static RE_UINT8 re_other_uppercase_stage_4[] = {
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 2, 1, 0, 0, 3, 4, 4, 5, 0, 0, 0,
};

static RE_UINT8 re_other_uppercase_stage_5[] = {
      0,   0,   0,   0, 255, 255,   0,   0,   0,   0, 192, 255,   0,   0, 255, 255,
    255,   3, 255, 255, 255,   3,   0,   0,
};

/* Other_Uppercase: 162 bytes. */

RE_UINT32 re_get_other_uppercase(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 15;
    code = ch ^ (f << 15);
    pos = (RE_UINT32)re_other_uppercase_stage_1[f] << 4;
    f = code >> 11;
    code ^= f << 11;
    pos = (RE_UINT32)re_other_uppercase_stage_2[pos + f] << 3;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_other_uppercase_stage_3[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_other_uppercase_stage_4[pos + f] << 5;
    pos += code;
    value = (re_other_uppercase_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Noncharacter_Code_Point. */

static RE_UINT8 re_noncharacter_code_point_stage_1[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1,
};

static RE_UINT8 re_noncharacter_code_point_stage_2[] = {
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2,
};

static RE_UINT8 re_noncharacter_code_point_stage_3[] = {
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2,
    0, 0, 0, 0, 0, 0, 0, 2,
};

static RE_UINT8 re_noncharacter_code_point_stage_4[] = {
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,
    0, 0, 0, 0, 0, 0, 0, 2,
};

static RE_UINT8 re_noncharacter_code_point_stage_5[] = {
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 255, 255, 255, 255,   0,   0,
      0,   0,   0,   0,   0,   0,   0, 192,
};

/* Noncharacter_Code_Point: 121 bytes. */

RE_UINT32 re_get_noncharacter_code_point(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_noncharacter_code_point_stage_1[f] << 4;
    f = code >> 12;
    code ^= f << 12;
    pos = (RE_UINT32)re_noncharacter_code_point_stage_2[pos + f] << 3;
    f = code >> 9;
    code ^= f << 9;
    pos = (RE_UINT32)re_noncharacter_code_point_stage_3[pos + f] << 3;
    f = code >> 6;
    code ^= f << 6;
    pos = (RE_UINT32)re_noncharacter_code_point_stage_4[pos + f] << 6;
    pos += code;
    value = (re_noncharacter_code_point_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Other_Grapheme_Extend. */

static RE_UINT8 re_other_grapheme_extend_stage_1[] = {
    0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2,
};

static RE_UINT8 re_other_grapheme_extend_stage_2[] = {
    0, 1, 2, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 4,
    1, 5, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 6, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
};

static RE_UINT8 re_other_grapheme_extend_stage_3[] = {
    0, 0, 0, 0, 1, 2, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    4, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 6, 0, 7, 8, 0, 0, 0, 0, 0,
    9, 0, 0, 0, 0, 0, 0, 0,
};

static RE_UINT8 re_other_grapheme_extend_stage_4[] = {
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  1,  2,
     0,  0,  0,  0,  1,  2,  1,  2,  0,  0,  0,  3,  1,  2,  0,  4,
     5,  0,  0,  0,  0,  0,  0,  0,  6,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  7,  0,  0,  0,  0,  0,  1,  2,  0,  0,
     0,  0,  8,  0,  0,  0,  9,  0,  0,  0,  0,  0,  0, 10,  0,  0,
};

static RE_UINT8 re_other_grapheme_extend_stage_5[] = {
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  64,
      0,   0, 128,   0,   0,   0,   0,   0,   4,   0,  96,   0,   0,   0,   0,   0,
      0, 128,   0, 128,   0,   0,   0,   0,   0,  48,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0, 192,   0,   0,   0,   0,   0, 192,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   1,  32,   0,   0,   0,   0,   0, 128,   0,   0,
      0,   0,   0,   0,  32, 192,   7,   0,
};

/* Other_Grapheme_Extend: 289 bytes. */

RE_UINT32 re_get_other_grapheme_extend(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_other_grapheme_extend_stage_1[f] << 4;
    f = code >> 12;
    code ^= f << 12;
    pos = (RE_UINT32)re_other_grapheme_extend_stage_2[pos + f] << 3;
    f = code >> 9;
    code ^= f << 9;
    pos = (RE_UINT32)re_other_grapheme_extend_stage_3[pos + f] << 3;
    f = code >> 6;
    code ^= f << 6;
    pos = (RE_UINT32)re_other_grapheme_extend_stage_4[pos + f] << 6;
    pos += code;
    value = (re_other_grapheme_extend_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* IDS_Binary_Operator. */

static RE_UINT8 re_ids_binary_operator_stage_1[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1,
};

static RE_UINT8 re_ids_binary_operator_stage_2[] = {
    0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
};

static RE_UINT8 re_ids_binary_operator_stage_3[] = {
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,
};

static RE_UINT8 re_ids_binary_operator_stage_4[] = {
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,
};

static RE_UINT8 re_ids_binary_operator_stage_5[] = {
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 243,  15,
};

/* IDS_Binary_Operator: 97 bytes. */

RE_UINT32 re_get_ids_binary_operator(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_ids_binary_operator_stage_1[f] << 4;
    f = code >> 12;
    code ^= f << 12;
    pos = (RE_UINT32)re_ids_binary_operator_stage_2[pos + f] << 3;
    f = code >> 9;
    code ^= f << 9;
    pos = (RE_UINT32)re_ids_binary_operator_stage_3[pos + f] << 3;
    f = code >> 6;
    code ^= f << 6;
    pos = (RE_UINT32)re_ids_binary_operator_stage_4[pos + f] << 6;
    pos += code;
    value = (re_ids_binary_operator_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* IDS_Trinary_Operator. */

static RE_UINT8 re_ids_trinary_operator_stage_1[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1,
};

static RE_UINT8 re_ids_trinary_operator_stage_2[] = {
    0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
};

static RE_UINT8 re_ids_trinary_operator_stage_3[] = {
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,
};

static RE_UINT8 re_ids_trinary_operator_stage_4[] = {
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,
};

static RE_UINT8 re_ids_trinary_operator_stage_5[] = {
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 12,  0,
};

/* IDS_Trinary_Operator: 97 bytes. */

RE_UINT32 re_get_ids_trinary_operator(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_ids_trinary_operator_stage_1[f] << 4;
    f = code >> 12;
    code ^= f << 12;
    pos = (RE_UINT32)re_ids_trinary_operator_stage_2[pos + f] << 3;
    f = code >> 9;
    code ^= f << 9;
    pos = (RE_UINT32)re_ids_trinary_operator_stage_3[pos + f] << 3;
    f = code >> 6;
    code ^= f << 6;
    pos = (RE_UINT32)re_ids_trinary_operator_stage_4[pos + f] << 6;
    pos += code;
    value = (re_ids_trinary_operator_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Radical. */

static RE_UINT8 re_radical_stage_1[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1,
};

static RE_UINT8 re_radical_stage_2[] = {
    0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
};

static RE_UINT8 re_radical_stage_3[] = {
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,
};

static RE_UINT8 re_radical_stage_4[] = {
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 1, 2, 2, 3, 2, 2, 2, 2, 2, 2, 4, 0,
};

static RE_UINT8 re_radical_stage_5[] = {
      0,   0,   0,   0, 255, 255, 255, 251, 255, 255, 255, 255, 255, 255,  15,   0,
    255, 255,  63,   0,
};

/* Radical: 117 bytes. */

RE_UINT32 re_get_radical(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_radical_stage_1[f] << 4;
    f = code >> 12;
    code ^= f << 12;
    pos = (RE_UINT32)re_radical_stage_2[pos + f] << 3;
    f = code >> 9;
    code ^= f << 9;
    pos = (RE_UINT32)re_radical_stage_3[pos + f] << 4;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_radical_stage_4[pos + f] << 5;
    pos += code;
    value = (re_radical_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Unified_Ideograph. */

static RE_UINT8 re_unified_ideograph_stage_1[] = {
    0, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1,
};

static RE_UINT8 re_unified_ideograph_stage_2[] = {
    0, 0, 0, 1, 2, 3, 3, 3, 3, 4, 0, 0, 0, 0, 0, 5,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 6, 7, 8, 0, 0, 0,
};

static RE_UINT8 re_unified_ideograph_stage_3[] = {
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 3, 0, 0, 0, 0, 0, 4, 0, 0,
    1, 1, 1, 5, 1, 1, 1, 1, 1, 1, 1, 6, 7, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 8,
};

static RE_UINT8 re_unified_ideograph_stage_4[] = {
    0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 2, 0, 1, 1, 1, 1, 1, 1, 1, 3,
    4, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 5, 1, 1, 1, 1,
    1, 1, 1, 1, 6, 1, 1, 1, 7, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 8, 0, 0, 0, 0, 0,
};

static RE_UINT8 re_unified_ideograph_stage_5[] = {
      0,   0,   0,   0,   0,   0,   0,   0, 255, 255, 255, 255, 255, 255, 255, 255,
    255, 255, 255, 255, 255, 255,  63,   0, 255, 255,  63,   0,   0,   0,   0,   0,
      0, 192,  26, 128, 154,   3,   0,   0, 255, 255, 127,   0,   0,   0,   0,   0,
    255, 255, 255, 255, 255, 255,  31,   0, 255, 255, 255,  63, 255, 255, 255, 255,
    255, 255, 255, 255,   3,   0,   0,   0,
};

/* Unified_Ideograph: 281 bytes. */

RE_UINT32 re_get_unified_ideograph(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_unified_ideograph_stage_1[f] << 4;
    f = code >> 12;
    code ^= f << 12;
    pos = (RE_UINT32)re_unified_ideograph_stage_2[pos + f] << 3;
    f = code >> 9;
    code ^= f << 9;
    pos = (RE_UINT32)re_unified_ideograph_stage_3[pos + f] << 3;
    f = code >> 6;
    code ^= f << 6;
    pos = (RE_UINT32)re_unified_ideograph_stage_4[pos + f] << 6;
    pos += code;
    value = (re_unified_ideograph_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Other_Default_Ignorable_Code_Point. */

static RE_UINT8 re_other_default_ignorable_code_point_stage_1[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1,
    1,
};

static RE_UINT8 re_other_default_ignorable_code_point_stage_2[] = {
    0, 1, 2, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5,
    4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
    6, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
};

static RE_UINT8 re_other_default_ignorable_code_point_stage_3[] = {
    0, 1, 0, 0, 0, 0, 0, 0, 2, 0, 0, 3, 0, 0, 0, 0,
    4, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 6,
    7, 8, 8, 8, 8, 8, 8, 8,
};

static RE_UINT8 re_other_default_ignorable_code_point_stage_4[] = {
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  1,  0,  0,
     0,  0,  0,  0,  0,  2,  0,  0,  0,  0,  0,  0,  0,  0,  3,  0,
     0,  4,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  5,  0,  0,
     0,  0,  0,  0,  0,  0,  6,  7,  8,  0,  9,  9,  0,  0,  0, 10,
     9,  9,  9,  9,  9,  9,  9,  9,
};

static RE_UINT8 re_other_default_ignorable_code_point_stage_5[] = {
      0,   0,   0,   0,   0,   0,   0,   0,   0, 128,   0,   0,   0,   0,   0,   0,
      0,   0,   0, 128,   1,   0,   0,   0,   0,   0,   0,   0,   0,   0,  48,   0,
      0,   0,   0,   0,  32,   0,   0,   0,   0,   0,   0,   0,  16,   0,   0,   0,
      0,   0,   0,   0,   1,   0,   0,   0,   0,   0,   0,   0,   0,   0, 255,   1,
    253, 255, 255, 255,   0,   0,   0,   0, 255, 255, 255, 255, 255, 255, 255, 255,
      0,   0,   0,   0,   0,   0, 255, 255,
};

/* Other_Default_Ignorable_Code_Point: 281 bytes. */

RE_UINT32 re_get_other_default_ignorable_code_point(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_other_default_ignorable_code_point_stage_1[f] << 4;
    f = code >> 12;
    code ^= f << 12;
    pos = (RE_UINT32)re_other_default_ignorable_code_point_stage_2[pos + f] << 3;
    f = code >> 9;
    code ^= f << 9;
    pos = (RE_UINT32)re_other_default_ignorable_code_point_stage_3[pos + f] << 3;
    f = code >> 6;
    code ^= f << 6;
    pos = (RE_UINT32)re_other_default_ignorable_code_point_stage_4[pos + f] << 6;
    pos += code;
    value = (re_other_default_ignorable_code_point_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Deprecated. */

static RE_UINT8 re_deprecated_stage_1[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1,
    1, 1,
};

static RE_UINT8 re_deprecated_stage_2[] = {
    0, 1, 2, 3, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
    3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
    5, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
};

static RE_UINT8 re_deprecated_stage_3[] = {
    0, 1, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 3,
    0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0,
    5, 0, 0, 6, 0, 0, 0, 0, 7, 0, 0, 0, 0, 0, 0, 0,
};

static RE_UINT8 re_deprecated_stage_4[] = {
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0,
    0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0,
    0, 6, 0, 0, 0, 0, 0, 0, 7, 0, 0, 8, 0, 0, 0, 0,
};

static RE_UINT8 re_deprecated_stage_5[] = {
      0,   0,   0,   0,   0,   2,   0,   0,   0,   0,   8,   0,   0,   0, 128,   2,
     24,   0,   0,   0,   0, 252,   0,   0,   0,   6,   0,   0,   2,   0,   0,   0,
      0,   0,   0, 128,
};

/* Deprecated: 230 bytes. */

RE_UINT32 re_get_deprecated(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 15;
    code = ch ^ (f << 15);
    pos = (RE_UINT32)re_deprecated_stage_1[f] << 4;
    f = code >> 11;
    code ^= f << 11;
    pos = (RE_UINT32)re_deprecated_stage_2[pos + f] << 3;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_deprecated_stage_3[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_deprecated_stage_4[pos + f] << 5;
    pos += code;
    value = (re_deprecated_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Soft_Dotted. */

static RE_UINT8 re_soft_dotted_stage_1[] = {
    0, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1,
};

static RE_UINT8 re_soft_dotted_stage_2[] = {
    0, 1, 1, 2, 3, 4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 5, 1, 1, 1, 1, 1,
};

static RE_UINT8 re_soft_dotted_stage_3[] = {
     0,  1,  2,  3,  4,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,
     5,  5,  5,  5,  5,  6,  7,  5,  8,  9,  5,  5,  5,  5,  5,  5,
     5,  5,  5,  5, 10,  5,  5,  5,  5,  5,  5,  5, 11, 12, 13,  5,
};

static RE_UINT8 re_soft_dotted_stage_4[] = {
     0,  0,  0,  1,  0,  0,  0,  0,  0,  2,  0,  0,  0,  0,  0,  0,
     0,  0,  3,  4,  5,  6,  0,  0,  0,  0,  0,  0,  0,  0,  0,  7,
     0,  0,  8,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  9, 10, 11,  0,  0,  0, 12,  0,  0,  0,  0, 13,  0,
     0,  0,  0, 14,  0,  0,  0,  0,  0,  0, 15,  0,  0,  0,  0,  0,
     0,  0,  0, 16,  0,  0,  0,  0,  0, 17, 18,  0, 19, 20,  0, 21,
     0, 22, 23,  0, 24,  0, 17, 18,  0, 19, 20,  0, 21,  0,  0,  0,
};

static RE_UINT8 re_soft_dotted_stage_5[] = {
      0,   0,   0,   0,   0,   6,   0,   0,   0, 128,   0,   0,   0,   2,   0,   0,
      0,   1,   0,   0,   0,   0,   0,  32,   0,   0,   4,   0,   0,   0,   8,   0,
      0,   0,  64,   1,   4,   0,   0,   0,   0,   0,  64,   0,  16,   1,   0,   0,
      0,  32,   0,   0,   0,   8,   0,   0,   0,   0,   2,   0,   0,   3,   0,   0,
      0,   0,   0,  16,  12,   0,   0,   0,   0,   0, 192,   0,   0,  12,   0,   0,
      0,   0,   0, 192,   0,   0,  12,   0, 192,   0,   0,   0,   0,   0,   0,  12,
      0, 192,   0,   0,
};

/* Soft_Dotted: 342 bytes. */

RE_UINT32 re_get_soft_dotted(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 15;
    code = ch ^ (f << 15);
    pos = (RE_UINT32)re_soft_dotted_stage_1[f] << 4;
    f = code >> 11;
    code ^= f << 11;
    pos = (RE_UINT32)re_soft_dotted_stage_2[pos + f] << 3;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_soft_dotted_stage_3[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_soft_dotted_stage_4[pos + f] << 5;
    pos += code;
    value = (re_soft_dotted_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Logical_Order_Exception. */

static RE_UINT8 re_logical_order_exception_stage_1[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1,
};

static RE_UINT8 re_logical_order_exception_stage_2[] = {
    0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 3, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
};

static RE_UINT8 re_logical_order_exception_stage_3[] = {
    0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 2, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0,
};

static RE_UINT8 re_logical_order_exception_stage_4[] = {
    0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 3, 0, 0, 0, 0, 0,
};

static RE_UINT8 re_logical_order_exception_stage_5[] = {
      0,   0,   0,   0,   0,   0,   0,   0,  31,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0, 224,   4,   0,   0,   0,   0,   0,   0,  96,  26,
};

/* Logical_Order_Exception: 145 bytes. */

RE_UINT32 re_get_logical_order_exception(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_logical_order_exception_stage_1[f] << 4;
    f = code >> 12;
    code ^= f << 12;
    pos = (RE_UINT32)re_logical_order_exception_stage_2[pos + f] << 3;
    f = code >> 9;
    code ^= f << 9;
    pos = (RE_UINT32)re_logical_order_exception_stage_3[pos + f] << 3;
    f = code >> 6;
    code ^= f << 6;
    pos = (RE_UINT32)re_logical_order_exception_stage_4[pos + f] << 6;
    pos += code;
    value = (re_logical_order_exception_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Other_ID_Start. */

static RE_UINT8 re_other_id_start_stage_1[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1,
};

static RE_UINT8 re_other_id_start_stage_2[] = {
    0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
};

static RE_UINT8 re_other_id_start_stage_3[] = {
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    1, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0,
};

static RE_UINT8 re_other_id_start_stage_4[] = {
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0,
    0, 0, 2, 0, 0, 0, 0, 0,
};

static RE_UINT8 re_other_id_start_stage_5[] = {
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  1,  0, 64,  0,  0,
     0,  0,  0, 24,  0,  0,  0,  0,
};

/* Other_ID_Start: 113 bytes. */

RE_UINT32 re_get_other_id_start(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_other_id_start_stage_1[f] << 3;
    f = code >> 13;
    code ^= f << 13;
    pos = (RE_UINT32)re_other_id_start_stage_2[pos + f] << 4;
    f = code >> 9;
    code ^= f << 9;
    pos = (RE_UINT32)re_other_id_start_stage_3[pos + f] << 3;
    f = code >> 6;
    code ^= f << 6;
    pos = (RE_UINT32)re_other_id_start_stage_4[pos + f] << 6;
    pos += code;
    value = (re_other_id_start_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Other_ID_Continue. */

static RE_UINT8 re_other_id_continue_stage_1[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1,
};

static RE_UINT8 re_other_id_continue_stage_2[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
};

static RE_UINT8 re_other_id_continue_stage_3[] = {
    0, 1, 2, 2, 2, 2, 2, 2, 2, 3, 2, 2, 4, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
};

static RE_UINT8 re_other_id_continue_stage_4[] = {
    0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 4,
};

static RE_UINT8 re_other_id_continue_stage_5[] = {
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 128,   0,
    128,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 254,   3,   0,
      0,   0,   0,   4,   0,   0,   0,   0,
};

/* Other_ID_Continue: 145 bytes. */

RE_UINT32 re_get_other_id_continue(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_other_id_continue_stage_1[f] << 3;
    f = code >> 13;
    code ^= f << 13;
    pos = (RE_UINT32)re_other_id_continue_stage_2[pos + f] << 4;
    f = code >> 9;
    code ^= f << 9;
    pos = (RE_UINT32)re_other_id_continue_stage_3[pos + f] << 3;
    f = code >> 6;
    code ^= f << 6;
    pos = (RE_UINT32)re_other_id_continue_stage_4[pos + f] << 6;
    pos += code;
    value = (re_other_id_continue_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* STerm. */

static RE_UINT8 re_sterm_stage_1[] = {
    0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2,
};

static RE_UINT8 re_sterm_stage_2[] = {
     0,  1,  2,  3,  4,  5,  6,  7,  7,  7,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  7,  8,  9,  7,  7,  7,  7,  7,  7,  7,  7,  7, 10,
     7, 11, 12,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7, 13,  7,  7,
     7,  7,  7,  7,  7,  7,  7, 14,  7,  7,  7, 15,  7,  7,  7,  7,
     7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,
};

static RE_UINT8 re_sterm_stage_3[] = {
     0,  1,  1,  1,  1,  2,  3,  4,  1,  5,  1,  1,  1,  1,  1,  1,
     6,  1,  1,  7,  1,  1,  8,  9, 10, 11, 12, 13, 14,  1,  1,  1,
    15,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1, 16,  1,
    17,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1, 18,  1, 19,  1, 20, 21, 22, 23,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1, 24, 25,  1,  1, 26,  1,  1,  1,  1,  1,
    27, 28, 29,  1,  1, 30, 31, 32,  1,  1, 33, 34,  1,  1,  1,  1,
     1,  1,  1,  1, 35,  1,  1,  1,  1,  1, 36,  1,  1,  1,  1,  1,
};

static RE_UINT8 re_sterm_stage_4[] = {
     0,  1,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  2,  0,  0,  0,  3,  0,  0,  0,  0,  0,  4,  0,
     5,  0,  0,  0,  0,  0,  0,  6,  0,  0,  0,  7,  0,  0,  0,  0,
     0,  0,  8,  0,  0,  0,  0,  0,  0,  0,  0,  9,  0,  0,  0,  0,
     0,  0,  0, 10,  0,  0,  0,  0,  0, 11,  0,  0,  0,  0,  0,  0,
    12,  0,  0,  0,  0,  0,  0,  0,  0,  0,  7,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0, 13,  0,  0,  0,  0, 14,  0,  0,  0,  0,  0,
     0, 15,  0, 16,  0,  0,  0,  0,  0, 17, 18,  0,  0,  0,  0,  0,
     0, 19,  0,  0,  0,  0,  0,  0, 20,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  3, 21,  0,  0,  0,  0,  0,  0, 22,
     0,  0,  0, 23,  0,  0, 21,  0,  0, 24,  0,  0,  0,  0, 25,  0,
     0,  0, 26,  0,  0,  0,  0, 27,  0,  0,  0,  0,  0,  0,  0, 28,
     0,  0, 29,  0,  0,  0,  0,  0,  1,  0,  0, 30,  0,  0,  0,  0,
     0,  0, 23,  0,  0,  0,  0,  0,  0,  0, 31,  0,  0, 16, 32,  0,
     0,  0, 33,  0,  0,  0, 34,  0,  0, 35,  0,  0,  0,  2,  0,  0,
     0,  0,  0,  0,  0,  0, 36,  0,  0,  0, 37,  0,  0,  0,  0,  0,
     0, 38,  0,  0,  0,  0,  0,  0,  0,  0,  0, 21,  0,  0,  0, 39,
     0, 40, 41,  0,  0,  0,  0,  0,  0,  0,  0,  0,  3,  0,  0,  0,
     0,  0,  0,  0, 42,  0,  0,  0,
};

static RE_UINT8 re_sterm_stage_5[] = {
      0,   0,   0,   0,   2,  64,   0, 128,   0,   2,   0,   0,   0,   0,   0, 128,
      0,   0,  16,   0,   7,   0,   0,   0,   0,   0,   0,   2,  48,   0,   0,   0,
      0,  12,   0,   0, 132,   1,   0,   0,   0,  64,   0,   0,   0,   0,  96,   0,
      8,   2,   0,   0,   0,  15,   0,   0,   0,   0,   0, 204,   0,   0,   0,  24,
      0,   0,   0, 192,   0,   0,   0,  48, 128,   3,   0,   0,   0,  64,   0,  16,
      4,   0,   0,   0,   0, 192,   0,   0,   0,   0, 136,   0,   0,   0, 192,   0,
      0, 128,   0,   0,   0,   3,   0,   0,   0,   0,   0, 224,   0,   0,   3,   0,
      0,   8,   0,   0,   0,   0, 196,   0,   2,   0,   0,   0, 128,   1,   0,   0,
      3,   0,   0,   0,  14,   0,   0,   0,  96,  32,   0, 192,   0,   0,   0,  27,
     12, 254, 255,   0,   6,   0,   0,   0,   0,   0,   0, 112,   0,   0,  32,   0,
      0,   0, 128,   1,  16,   0,   0,   0,   0,   1,   0,   0,
};

/* STerm: 709 bytes. */

RE_UINT32 re_get_sterm(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_sterm_stage_1[f] << 5;
    f = code >> 11;
    code ^= f << 11;
    pos = (RE_UINT32)re_sterm_stage_2[pos + f] << 3;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_sterm_stage_3[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_sterm_stage_4[pos + f] << 5;
    pos += code;
    value = (re_sterm_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Variation_Selector. */

static RE_UINT8 re_variation_selector_stage_1[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1,
    1,
};

static RE_UINT8 re_variation_selector_stage_2[] = {
    0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
};

static RE_UINT8 re_variation_selector_stage_3[] = {
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 2, 3, 0, 0, 0, 0, 0, 0, 0,
};

static RE_UINT8 re_variation_selector_stage_4[] = {
    0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0,
    2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 4,
};

static RE_UINT8 re_variation_selector_stage_5[] = {
      0,   0,   0,   0,   0,   0,   0,   0,   0,  56,   0,   0,   0,   0,   0,   0,
    255, 255,   0,   0,   0,   0,   0,   0, 255, 255, 255, 255, 255, 255, 255, 255,
    255, 255, 255, 255, 255, 255,   0,   0,
};

/* Variation_Selector: 169 bytes. */

RE_UINT32 re_get_variation_selector(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_variation_selector_stage_1[f] << 4;
    f = code >> 12;
    code ^= f << 12;
    pos = (RE_UINT32)re_variation_selector_stage_2[pos + f] << 3;
    f = code >> 9;
    code ^= f << 9;
    pos = (RE_UINT32)re_variation_selector_stage_3[pos + f] << 3;
    f = code >> 6;
    code ^= f << 6;
    pos = (RE_UINT32)re_variation_selector_stage_4[pos + f] << 6;
    pos += code;
    value = (re_variation_selector_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Pattern_White_Space. */

static RE_UINT8 re_pattern_white_space_stage_1[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1,
};

static RE_UINT8 re_pattern_white_space_stage_2[] = {
    0, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
};

static RE_UINT8 re_pattern_white_space_stage_3[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    2, 1, 1, 1, 1, 1, 1, 1,
};

static RE_UINT8 re_pattern_white_space_stage_4[] = {
    0, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    3, 1, 1, 1, 1, 1, 1, 1,
};

static RE_UINT8 re_pattern_white_space_stage_5[] = {
      0,  62,   0,   0,   1,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
     32,   0,   0,   0,   0,   0,   0,   0,   0, 192,   0,   0,   0,   3,   0,   0,
};

/* Pattern_White_Space: 129 bytes. */

RE_UINT32 re_get_pattern_white_space(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_pattern_white_space_stage_1[f] << 4;
    f = code >> 12;
    code ^= f << 12;
    pos = (RE_UINT32)re_pattern_white_space_stage_2[pos + f] << 3;
    f = code >> 9;
    code ^= f << 9;
    pos = (RE_UINT32)re_pattern_white_space_stage_3[pos + f] << 3;
    f = code >> 6;
    code ^= f << 6;
    pos = (RE_UINT32)re_pattern_white_space_stage_4[pos + f] << 6;
    pos += code;
    value = (re_pattern_white_space_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Pattern_Syntax. */

static RE_UINT8 re_pattern_syntax_stage_1[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1,
};

static RE_UINT8 re_pattern_syntax_stage_2[] = {
    0, 1, 1, 1, 2, 3, 4, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 5,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
};

static RE_UINT8 re_pattern_syntax_stage_3[] = {
     0,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     2,  3,  4,  4,  5,  4,  4,  6,  4,  4,  4,  4,  1,  1,  7,  1,
     8,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  9, 10,  1,
};

static RE_UINT8 re_pattern_syntax_stage_4[] = {
     0,  1,  2,  2,  0,  3,  4,  4,  0,  0,  0,  0,  0,  0,  0,  0,
     5,  6,  7,  0,  0,  0,  0,  0,  0,  0,  0,  0,  5,  8,  8,  8,
     8,  8,  8,  8,  8,  8,  8,  8,  8,  8,  8,  0,  0,  0,  0,  0,
     8,  8,  8,  9, 10,  8,  8,  8,  8,  8,  8,  8,  0,  0,  0,  0,
    11, 12,  0,  0,  0,  0,  0,  0,  0, 13,  0,  0,  0,  0,  0,  0,
     0,  0, 14,  0,  0,  0,  0,  0,
};

static RE_UINT8 re_pattern_syntax_stage_5[] = {
      0,   0,   0,   0, 254, 255,   0, 252,   1,   0,   0, 120, 254,  90,  67, 136,
      0,   0, 128,   0,   0,   0, 255, 255, 255,   0, 255, 127, 254, 255, 239, 127,
    255, 255, 255, 255, 255, 255,  63,   0,   0,   0, 240, 255,  14, 255, 255, 255,
      1,   0,   1,   0,   0,   0,   0, 192,  96,   0,   0,   0,
};

/* Pattern_Syntax: 277 bytes. */

RE_UINT32 re_get_pattern_syntax(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_pattern_syntax_stage_1[f] << 5;
    f = code >> 11;
    code ^= f << 11;
    pos = (RE_UINT32)re_pattern_syntax_stage_2[pos + f] << 3;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_pattern_syntax_stage_3[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_pattern_syntax_stage_4[pos + f] << 5;
    pos += code;
    value = (re_pattern_syntax_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Hangul_Syllable_Type. */

static RE_UINT8 re_hangul_syllable_type_stage_1[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1,
};

static RE_UINT8 re_hangul_syllable_type_stage_2[] = {
    0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 2, 3, 4, 5, 6, 7, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
};

static RE_UINT8 re_hangul_syllable_type_stage_3[] = {
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  1,  2,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  3,  0,  0,  0,  0,  0,  4,  5,  6,  7,  8,  9, 10,  4,
     5,  6,  7,  8,  9, 10,  4,  5,  6,  7,  8,  9, 10,  4,  5,  6,
     7,  8,  9, 10,  4,  5,  6,  7,  8,  9, 10,  4,  5,  6,  7,  8,
     9, 10,  4,  5,  6,  7,  8,  9, 10,  4,  5,  6,  7,  8,  9, 10,
     4,  5,  6,  7,  8,  9, 10,  4,  5,  6,  7,  8,  9, 10,  4,  5,
     6,  7,  8,  9, 10,  4,  5,  6,  7,  8,  9, 10,  4,  5,  6, 11,
};

static RE_UINT8 re_hangul_syllable_type_stage_4[] = {
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  2,  2,  2,  2,
     2,  2,  2,  2,  2,  3,  3,  3,  3,  3,  3,  3,  3,  3,  3,  3,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  1,  1,  1,  4,
     5,  6,  6,  7,  6,  6,  6,  5,  6,  6,  7,  6,  6,  6,  5,  6,
     6,  7,  6,  6,  6,  5,  6,  6,  7,  6,  6,  6,  5,  6,  6,  7,
     6,  6,  6,  5,  6,  6,  7,  6,  6,  6,  5,  6,  6,  7,  6,  6,
     6,  5,  6,  6,  7,  6,  6,  6,  5,  6,  6,  7,  6,  6,  6,  5,
     6,  6,  7,  6,  6,  6,  5,  6,  6,  7,  6,  6,  6,  5,  6,  6,
     7,  6,  6,  6,  5,  6,  6,  7,  6,  6,  6,  5,  6,  6,  7,  6,
     6,  6,  5,  6,  6,  7,  6,  6,  6,  5,  6,  6,  7,  6,  6,  6,
     6,  5,  6,  6,  8,  0,  2,  2,  9, 10,  3,  3,  3,  3,  3, 11,
};

static RE_UINT8 re_hangul_syllable_type_stage_5[] = {
    0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1,
    2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3,
    1, 1, 1, 1, 1, 0, 0, 0, 4, 5, 5, 5, 5, 5, 5, 5,
    5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 5, 5, 5,
    5, 5, 5, 5, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 0,
    0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0,
};

/* Hangul_Syllable_Type: 497 bytes. */

RE_UINT32 re_get_hangul_syllable_type(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_hangul_syllable_type_stage_1[f] << 5;
    f = code >> 11;
    code ^= f << 11;
    pos = (RE_UINT32)re_hangul_syllable_type_stage_2[pos + f] << 4;
    f = code >> 7;
    code ^= f << 7;
    pos = (RE_UINT32)re_hangul_syllable_type_stage_3[pos + f] << 4;
    f = code >> 3;
    code ^= f << 3;
    pos = (RE_UINT32)re_hangul_syllable_type_stage_4[pos + f] << 3;
    value = re_hangul_syllable_type_stage_5[pos + code];

    return value;
}

/* Bidi_Class. */

static RE_UINT8 re_bidi_class_stage_1[] = {
     0,  1,  2,  3,  4,  5,  5,  5,  5,  5,  6,  5,  5,  5,  5,  7,
     8,  9,  5,  5,  5,  5, 10,  5,  5,  5,  5, 11,  5, 12, 13, 14,
     5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5, 15,
     5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5, 15,
     5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5, 15,
     5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5, 15,
     5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5, 15,
     5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5, 15,
     5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5, 15,
     5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5, 15,
     5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5, 15,
     5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5, 15,
     5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5, 15,
     5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5, 15,
    16,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5, 15,
     5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5, 15,
     5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5, 15,
};

static RE_UINT8 re_bidi_class_stage_2[] = {
      0,   1,   2,   2,   2,   3,   4,   5,   2,   6,   2,   7,   8,   9,  10,  11,
     12,  13,  14,  15,  16,  17,  18,  19,  20,  21,  22,  23,  24,  25,  26,  27,
     28,  29,   2,   2,   2,   2,  30,  31,  32,   2,   2,   2,   2,  33,  34,  35,
     36,  37,  38,  39,  40,  41,  42,  43,  44,  45,   2,  46,   2,   2,   2,  47,
     48,  49,  50,  51,  52,  53,  54,  55,  56,  57,  53,  53,  53,  58,  53,  53,
      2,   2,  53,  53,  53,  53,  59,  60,   2,  61,  62,  63,  64,  65,  53,  66,
     67,  68,   2,  69,  70,  71,  72,  73,   2,   2,   2,   2,   2,   2,   2,   2,
      2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,
      2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,
      2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,  74,   2,   2,   2,   2,
      2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,
      2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,
      2,   2,   2,   2,   2,   2,   2,   2,   2,  75,   2,   2,  76,  77,  78,  79,
     80,  81,  82,  83,  84,  85,   2,  86,   2,   2,   2,   2,   2,   2,   2,   2,
      2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,
      2,   2,   2,   2,   2,   2,  87,  88,  88,  88,  89,  90,  91,  92,  93,  94,
      2,   2,  95,  96,   2,  97,  98,   2,   2,   2,   2,   2,   2,   2,   2,   2,
     99,  99, 100,  99, 101, 102, 103,  99,  99,  99,  99,  99, 104,  99,  99,  99,
    105, 106, 107, 108, 109, 110, 111,   2,   2, 112,   2, 113, 114, 115, 116,   2,
      2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,
      2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,
      2,   2,   2,   2,   2, 117, 118,   2,   2,   2,   2,   2,   2,   2,   2, 119,
      2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,
      2,   2,   2,   2,   2,   2,   2,   2,   2, 120,   2,   2,   2,   2,   2,   2,
      2,   2, 121, 122, 123,   2, 124,   2,   2,   2,   2,   2,   2, 125, 126, 127,
      2,   2,   2,   2, 128, 129,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,
      2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,
     99, 130,  99,  99,  99,  99,  99,  99,  99,  99,  99,  99,  88, 131,  99,  99,
    132, 133, 134,   2,   2,   2,  53,  53,  53,  53, 135, 136,  53, 137, 138, 139,
    140, 141, 142, 143,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2, 144,
      2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,
      2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2, 144,
    145, 145, 146, 147, 145, 145, 145, 145, 145, 145, 145, 145, 145, 145, 145, 145,
    145, 145, 145, 145, 145, 145, 145, 145, 145, 145, 145, 145, 145, 145, 145, 145,
};

static RE_UINT8 re_bidi_class_stage_3[] = {
      0,   1,   2,   3,   4,   5,   4,   6,   7,   8,   9,  10,  11,  12,  11,  12,
     11,  11,  11,  11,  11,  11,  11,  11,  11,  11,  11,  13,  14,  14,  15,  16,
     17,  17,  17,  17,  17,  17,  17,  18,  19,  11,  11,  11,  11,  11,  11,  20,
     21,  11,  11,  11,  11,  11,  11,  11,  22,  23,  17,  24,  25,  26,  26,  26,
     27,  28,  29,  29,  30,  17,  31,  32,  29,  29,  29,  29,  29,  33,  34,  35,
     29,  36,  29,  17,  28,  29,  29,  29,  29,  29,  37,  32,  26,  26,  38,  39,
     26,  40,  41,  26,  26,  42,  26,  26,  26,  26,  29,  29,  29,  29,  43,  17,
     44,  11,  11,  45,  46,  47,  48,  11,  49,  11,  11,  50,  51,  11,  48,  52,
     53,  11,  11,  50,  54,  49,  11,  55,  53,  11,  11,  50,  56,  11,  48,  57,
     49,  11,  11,  58,  51,  59,  48,  11,  60,  11,  11,  11,  61,  11,  11,  62,
     63,  11,  11,  64,  65,  66,  48,  67,  49,  11,  11,  50,  68,  11,  48,  11,
     49,  11,  11,  11,  51,  11,  48,  11,  11,  11,  11,  11,  69,  70,  11,  11,
     11,  11,  11,  71,  72,  11,  11,  11,  11,  11,  11,  73,  74,  11,  11,  11,
     11,  75,  11,  76,  11,  11,  11,  77,  78,  79,  17,  80,  59,  11,  11,  11,
     11,  11,  81,  82,  11,  83,  63,  84,  85,  86,  11,  11,  11,  11,  11,  11,
     11,  11,  11,  11,  11,  81,  11,  11,  11,  87,  11,  11,  11,  11,  11,  11,
      4,  11,  11,  11,  11,  11,  11,  11,  88,  89,  11,  11,  11,  11,  11,  11,
     11,  90,  11,  90,  11,  48,  11,  48,  11,  11,  11,  91,  92,  93,  11,  87,
     94,  11,  11,  11,  11,  11,  11,  11,  11,  11,  95,  11,  11,  11,  11,  11,
     11,  11,  96,  97,  98,  11,  11,  11,  11,  11,  11,  11,  11,  99,  16,  16,
     11, 100,  11,  11,  11, 101, 102, 103,  11,  11,  11, 104,  11,  11,  11,  11,
    105,  11,  11, 106,  60,  11, 107, 105, 108,  11, 109,  11,  11,  11, 110, 108,
     11,  11, 111, 112,  11,  11,  11,  11,  11,  11,  11,  11,  11, 113, 114, 115,
     11,  11,  11,  11,  17,  17,  17, 116,  11,  11,  11, 117, 118, 119, 119, 120,
    121,  16, 122, 123, 124, 125, 126, 127, 128,  11, 129, 129, 129,  17,  17,  63,
    130, 131, 132, 133, 134,  16,  11,  11, 135,  16,  16,  16,  16,  16,  16,  16,
     16, 136,  16,  16,  16,  16,  16,  16,  16,  16,  16,  16,  16,  16,  16,  16,
     16,  16,  16, 137,  11,  11,  11,   5,  16, 138,  16,  16,  16,  16,  16, 139,
     16,  16, 140,  11, 139,  11,  16,  16, 141, 142,  11,  11,  11,  11, 143,  16,
     16,  16, 144,  16,  16,  16,  16,  16,  16,  16,  16,  16,  16,  16,  16, 145,
     16, 146,  16, 147, 148, 149, 150,  11,  11,  11,  11,  11,  11,  11, 151, 152,
     11,  11,  11,  11,  11,  11,  11, 153,  11,  11,  11,  11,  11,  11,  17,  17,
     16,  16,  16,  16, 154,  11,  11,  11,  16, 155,  16,  16,  16,  16,  16, 156,
     16,  16,  16,  16,  16, 137,  11, 157, 158,  16, 159, 160,  11,  11,  11,  11,
     11, 161,   4,  11,  11,  11,  11, 162,  11,  11,  11,  11,  16,  16, 156,  11,
     11, 120,  11,  11,  11,  16,  11, 163,  11,  11,  11, 164, 150,  11,  11,  11,
     11,  11,  11,  11,  11,  11,  11, 165,  11,  11,  11,  11,  11,  99,  11, 166,
     11,  11,  11,  11,  16,  16,  16,  16,  11,  16,  16,  16, 140,  11,  11,  11,
    119,  11,  11,  11,  11,  11, 153, 167,  11,  64,  11,  11,  11,  11,  11, 108,
     16,  16, 149,  11,  11,  11,  11,  11, 168,  11,  11,  11,  11,  11,  11,  11,
    169,  11, 170, 171,  11,  11,  11, 172,  11,  11,  11,  11, 173,  11,  17, 108,
     11,  11, 174,  11, 175, 108,  11,  11,  44,  11,  11, 176,  11,  11, 177,  11,
     11,  11, 178, 179, 180,  11,  11,  50,  11,  11,  11, 181,  49,  11,  68,  59,
     11,  11,  11,  11,  11,  11, 182,  11,  11, 183, 184,  26,  26,  29,  29,  29,
     29,  29,  29,  29,  29,  29,  29,  29,  29,  29,  29, 185,  29,  29,  29,  29,
     29,  29,  29,  29,  29,   8,   8, 186,  17,  87,  17,  16,  16, 187, 188,  29,
     29,  29,  29,  29,  29,  29,  29, 189, 190,   3,   4,   5,   4,   5, 137,  11,
     11,  11,  11,  11,  11,  11, 191, 192, 193,  11,  11,  11,  16,  16,  16,  16,
    194, 157,   4,  11,  11,  11,  11,  86,  11,  11,  11,  11,  11,  11, 195, 142,
     11,  11,  11,  11,  11,  11,  11, 196,  26,  26,  26,  26,  26,  26,  26,  26,
     26, 197,  26,  26,  26,  26,  26,  26, 198,  26,  26, 199,  26,  26,  26,  26,
     26,  26,  26,  26,  26,  26, 200,  26,  26,  26,  26, 201,  26,  26,  26,  26,
     26,  26,  26,  26,  26,  26, 202, 203,  49,  11,  11, 204, 205,  14, 137, 153,
    108,  11,  11, 206,  11,  11,  11,  11,  44,  11, 207, 208,  11,  11,  11, 209,
    108,  11,  11, 210, 211,  11,  11,  11,  11,  11, 153, 212,  11,  11,  11,  11,
     11,  11,  11,  11,  11, 153, 213,  11, 108,  11,  11,  50,  63,  11, 214, 208,
     11,  11,  11, 215, 216,  11,  11,  11,  11,  11,  11, 217,  63,  68,  11,  11,
     11,  11,  11, 218,  63,  11,  11,  11,  11,  11, 219, 220,  11,  11,  11,  11,
     11,  81, 221,  11,  11,  11,  11,  11,  11,  11,  11,  11,  11,  11,  11, 208,
     11,  11,  11, 205,  11,  11,  11,  11, 153,  44,  11,  11,  11,  11,  11,  11,
     11, 222, 223,  11,  11,  11,  11,  11,  11,  11,  11,  11,  11,  11, 224, 225,
    226,  11, 227,  11,  11,  11,  11,  11,  16,  16,  16,  16, 228,  11,  11,  11,
     16,  16,  16,  16,  16, 140,  11,  11,  11,  11,  11,  11,  11, 162,  11,  11,
     11, 229,  11,  11, 166,  11,  11,  11, 230,  11,  11,  11, 231, 232, 232, 232,
     17,  17,  17, 233,  17,  17,  80, 177, 173, 107, 234,  11,  11,  11,  11,  11,
     26,  26,  26,  26,  26, 235,  26,  26,  29,  29,  29,  29,  29,  29,  29, 236,
     16,  16, 157,  16,  16,  16,  16,  16,  16, 156, 237, 164, 164, 164,  16, 137,
    238,  11,  11,  11,  11,  11, 133,  11,  16,  16,  16,  16,  16,  16,  16, 155,
     16,  16, 239,  16,  16,  16,  16,  16,  16,  16,  16,  16,  16,   4, 194, 156,
     16,  16,  16,  16,  16,  16,  16, 156,  16,  16,  16,  16,  16, 240,  11,  11,
    157,  16,  16,  16, 241,  87,  16,  16, 241,  16, 242,  11,  11,  11,  11,  11,
     11, 243,  11,  11,  11,  11,  11,  11, 240,  11,  11,  11,   4,  11,  11,  11,
     11,  11,  11,  11,  11,  11,  11, 244,   8,   8,   8,   8,   8,   8,   8,   8,
     17,  17,  17,  17,  17,  17,  17,  17,  17,  17,  17,  17,  17,  17,  17,   8,
};

static RE_UINT8 re_bidi_class_stage_4[] = {
      0,   0,   1,   2,   0,   0,   0,   3,   4,   5,   6,   7,   8,   8,   9,  10,
     11,  12,  12,  12,  12,  12,  13,  10,  12,  12,  13,  14,   0,  15,   0,   0,
      0,   0,   0,   0,  16,   5,  17,  18,  19,  20,  21,  10,  12,  12,  12,  12,
     12,  13,  12,  12,  12,  12,  22,  12,  23,  10,  10,  10,  12,  24,  10,  17,
     10,  10,  10,  10,  25,  25,  25,  25,  12,  26,  12,  27,  12,  17,  12,  12,
     12,  27,  12,  12,  28,  25,  29,  12,  12,  12,  27,  30,  31,  25,  25,  25,
     25,  25,  25,  32,  33,  32,  34,  34,  34,  34,  34,  34,  35,  36,  37,  38,
     25,  25,  39,  40,  40,  40,  40,  40,  40,  40,  41,  25,  35,  35,  42,  43,
     44,  40,  40,  40,  40,  45,  25,  46,  25,  47,  48,  49,   8,   8,  50,  40,
     51,  40,  40,  40,  40,  45,  25,  25,  34,  34,  52,  25,  25,  53,  54,  34,
     34,  55,  32,  25,  25,  31,  31,  56,  34,  34,  31,  34,  41,  25,  25,  25,
     57,  12,  12,  12,  12,  12,  58,  59,  60,  25,  59,  61,  60,  25,  12,  12,
     62,  12,  12,  12,  61,  12,  12,  12,  12,  12,  12,  59,  60,  59,  12,  61,
     63,  12,  64,  12,  65,  12,  12,  12,  65,  28,  66,  29,  29,  61,  12,  12,
     60,  67,  59,  61,  68,  12,  12,  12,  12,  12,  12,  66,  12,  58,  12,  12,
     58,  12,  12,  12,  59,  12,  12,  61,  13,  10,  69,  12,  59,  12,  12,  12,
     12,  12,  12,  62,  59,  62,  70,  29,  12,  65,  12,  12,  12,  12,  10,  71,
     12,  12,  12,  29,  12,  12,  58,  12,  62,  72,  12,  12,  61,  25,  57,  64,
     12,  28,  25,  57,  61,  25,  67,  59,  12,  12,  25,  29,  12,  12,  29,  12,
     12,  73,  74,  26,  60,  25,  25,  57,  25,  70,  12,  60,  25,  25,  60,  25,
     25,  25,  25,  59,  12,  12,  12,  60,  70,  25,  65,  65,  12,  12,  29,  62,
     60,  59,  12,  12,  58,  65,  12,  61,  12,  12,  12,  61,  10,  10,  26,  12,
     75,  12,  12,  12,  12,  12,  13,  11,  62,  59,  12,  12,  12,  67,  25,  29,
     12,  58,  60,  25,  25,  12,  64,  61,  10,  10,  76,  77,  12,  12,  61,  12,
     57,  28,  59,  12,  58,  12,  60,  12,  11,  26,  12,  12,  12,  12,  12,  23,
     12,  28,  66,  12,  12,  58,  25,  57,  72,  60,  25,  59,  28,  25,  25,  66,
     25,  25,  25,  57,  25,  12,  12,  12,  12,  70,  57,  59,  12,  12,  28,  25,
     29,  12,  12,  12,  62,  29,  67,  29,  12,  58,  29,  73,  12,  12,  12,  25,
     25,  62,  12,  12,  57,  25,  25,  25,  70,  25,  59,  61,  12,  59,  29,  12,
     25,  29,  12,  25,  12,  12,  12,  78,  26,  12,  12,  24,  12,  12,  12,  24,
     12,  12,  12,  22,  79,  79,  80,  81,  10,  10,  82,  83,  84,  85,  10,  10,
     10,  86,  10,  10,  10,  10,  10,  87,   0,  88,  89,   0,  90,   8,  91,  71,
      8,   8,  91,  71,  84,  84,  84,  84,  17,  71,  26,  12,  12,  20,  11,  23,
     10,  78,  92,  93,  12,  12,  23,  12,  10,  11,  23,  26,  12,  12,  24,  12,
     94,  10,  10,  10,  10,  26,  12,  12,  10,  20,  10,  10,  10,  10,  71,  12,
     10,  71,  12,  12,  10,  10,   8,   8,   8,   8,   8,  12,  12,  12,  23,  10,
     10,  10,  10,  24,  10,  23,  10,  10,  10,  26,  10,  10,  10,  10,  26,  24,
     10,  10,  20,  10,  26,  12,  12,  12,  12,  12,  12,  10,  12,  24,  71,  28,
     29,  12,  24,  10,  12,  12,  12,  28,  71,  12,  12,  12,  10,  10,  17,  10,
     10,  12,  12,  12,  10,  10,  10,  12,  95,  11,  10,  10,  11,  12,  62,  29,
     11,  23,  12,  24,  12,  12,  96,  11,  12,  12,  13,  12,  12,  12,  12,  71,
     24,  10,  10,  10,  12,  13,  71,  12,  12,  12,  12,  13,  97,  25,  25,  98,
     12,  12,  11,  12,  58,  58,  28,  12,  12,  65,  10,  12,  12,  12,  99,  12,
     12,  10,  12,  12,  12,  59,  12,  12,  12,  62,  25,  29,  12,  28,  25,  25,
     28,  62,  29,  59,  12,  61,  12,  12,  12,  12,  60,  57,  65,  65,  12,  12,
     28,  12,  12,  59,  70,  66,  59,  62,  12,  61,  59,  61,  12,  12,  12, 100,
     34,  34, 101,  34,  40,  40,  40, 102,  40,  40,  40, 103, 104, 105,  10, 106,
    107,  71, 108,  12,  40,  40,  40, 109,  30,   5,   6,   7,   5, 110,  10,  71,
      0,   0, 111, 112,  92,  12,  12,  12,  10,  10,  10,  11, 113,   8,   8,   8,
     12,  62,  57,  12,  34,  34,  34, 114,  31,  33,  34,  25,  34,  34, 115,  52,
     34,  33,  34,  34,  34,  34, 116,  10,  35,  35,  35,  35,  35,  35,  35, 117,
     12,  12,  25,  25,  25,  57,  12,  12,  28,  57,  65,  12,  12,  28,  25,  60,
     25,  59,  12,  12,  28,  12,  12,  12,  12,  62,  25,  57,  12,  12,  62,  59,
     29,  70,  12,  12,  28,  25,  57,  12,  12,  62,  25,  59,  28,  25,  72,  28,
     70,  12,  12,  12,  62,  29,  12,  67,  28,  25,  57,  73,  12,  12,  28,  61,
     25,  67,  12,  12,  62,  67,  25,  12,  12,  12,  12,  65,   0,  12,  12,  12,
     12,  28,  29,  12, 118,   0, 119,  25,  57,  60,  25,  12,  12,  12,  62,  29,
    120, 121,  12,  12,  12,  92,  12,  12,  12,  12,  92,  12,  13,  12,  12, 122,
      8,   8,   8,   8,  25,  57,  28,  25,  60,  25,  25,  25,  25, 115,  34,  34,
    123,  40,  40,  40,  10,  10,  10,  71,   8,   8, 124,  11,  10,  24,  10,  10,
     10,  11,  12,  12,  10,  10,  12,  12,  10,  10,  10,  26,  10,  10,  11,  12,
     12,  12,  12, 125,
};

static RE_UINT8 re_bidi_class_stage_5[] = {
    11, 11, 11, 11, 11,  8,  7,  8,  9,  7, 11, 11,  7,  7,  7,  8,
     9, 10, 10,  4,  4,  4, 10, 10, 10, 10, 10,  3,  6,  3,  6,  6,
     2,  2,  2,  2,  2,  2,  6, 10, 10, 10, 10, 10, 10,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0, 10, 10, 10, 10, 11, 11,  7, 11, 11,
     6, 10,  4,  4, 10, 10,  0, 10, 10, 11, 10, 10,  4,  4,  2,  2,
    10,  0, 10, 10, 10,  2,  0, 10,  0, 10, 10,  0,  0,  0, 10, 10,
     0, 10, 10, 10, 12, 12, 12, 12, 10, 10,  0,  0,  0,  0, 10,  0,
     0,  0,  0, 12, 12, 12,  0,  0,  0, 10, 10,  4,  1, 12, 12, 12,
    12, 12,  1, 12,  1, 12, 12,  1,  1,  1,  1,  1,  5,  5,  5,  5,
     5,  5, 10, 10, 13,  4,  4, 13,  6, 13, 10, 10, 12, 12, 12, 13,
    13, 13, 13, 13, 13, 13, 13, 12,  5,  5,  4,  5,  5, 13, 13, 13,
    12, 13, 13, 13, 13, 13, 12, 12, 12,  5, 10, 12, 12, 13, 13, 12,
    12, 10, 12, 12, 12, 12, 13, 13,  2,  2, 13, 13, 13, 12, 13, 13,
     1,  1,  1, 12,  1,  1, 10, 10, 10, 10,  1,  1,  1,  1, 12, 12,
    12, 12,  1,  1, 12, 12, 12,  0,  0,  0, 12,  0, 12,  0,  0,  0,
     0, 12, 12, 12,  0, 12,  0,  0,  0,  0, 12, 12,  0,  0,  4,  4,
     0,  0,  0,  4,  0, 12, 12,  0, 12,  0,  0, 12, 12, 12,  0, 12,
     0,  4,  0,  0, 10,  4, 10,  0, 12,  0, 12, 12, 10, 10, 10,  0,
    12,  0, 12,  0,  0, 12,  0, 12,  0, 12, 10, 10,  9,  0,  0,  0,
    10, 10, 10, 12, 12, 12, 11,  0,  0, 10,  0, 10,  9,  9,  9,  9,
     9,  9,  9, 11, 11, 11,  0,  1,  9,  7, 16, 17, 18, 14, 15,  6,
     4,  4,  4,  4,  4, 10, 10, 10,  6, 10, 10, 10, 10, 10, 10,  9,
    11, 11, 19, 20, 21, 22, 11, 11,  2,  0,  0,  0,  2,  2,  3,  3,
     0, 10,  0,  0,  0,  0,  4,  0, 10, 10,  3,  4,  9, 10, 10, 10,
     0, 12, 12, 10, 12, 12, 12, 10, 12, 12, 10, 10,  4,  4,  0,  0,
     0,  1, 12,  1,  1,  3,  1,  1, 13, 13, 10, 10, 13, 10, 13, 13,
     6, 10,  6,  0, 10,  6, 10, 10, 10, 10, 10,  4, 10, 10,  3,  3,
    10,  4,  4, 10, 13, 13, 13, 11, 10,  4,  4,  0, 11, 10, 10, 10,
    10, 10, 11, 11, 12,  2,  2,  2,  1,  1,  1, 10, 12, 12, 12,  1,
     1, 10, 10, 10,  5,  5,  5,  1,  0,  0,  0, 11, 11, 11, 11, 12,
    10, 10, 12, 12, 12, 10,  0,  0,  0,  0,  2,  2, 10, 10, 13, 13,
     2,  2,  2, 10,  0,  0, 11, 11,
};

/* Bidi_Class: 3484 bytes. */

RE_UINT32 re_get_bidi_class(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 12;
    code = ch ^ (f << 12);
    pos = (RE_UINT32)re_bidi_class_stage_1[f] << 5;
    f = code >> 7;
    code ^= f << 7;
    pos = (RE_UINT32)re_bidi_class_stage_2[pos + f] << 3;
    f = code >> 4;
    code ^= f << 4;
    pos = (RE_UINT32)re_bidi_class_stage_3[pos + f] << 2;
    f = code >> 2;
    code ^= f << 2;
    pos = (RE_UINT32)re_bidi_class_stage_4[pos + f] << 2;
    value = re_bidi_class_stage_5[pos + code];

    return value;
}

/* Canonical_Combining_Class. */

static RE_UINT8 re_canonical_combining_class_stage_1[] = {
    0, 1, 2, 2, 2, 3, 2, 4, 5, 2, 2, 6, 2, 7, 8, 9,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2,
};

static RE_UINT8 re_canonical_combining_class_stage_2[] = {
     0,  1,  2,  3,  4,  5,  6,  7,  8,  9,  0, 10, 11, 12, 13,  0,
    14,  0,  0,  0,  0,  0, 15,  0, 16,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0, 17, 18, 19,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 20,  0, 21,
    22, 23,  0,  0,  0, 24,  0,  0, 25, 26, 27, 28,  0,  0,  0,  0,
     0,  0,  0,  0,  0, 29,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 30,  0,
     0,  0,  0,  0,  0,  0,  0,  0, 31, 32,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0, 33,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
};

static RE_UINT8 re_canonical_combining_class_stage_3[] = {
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,   1,   2,   3,   4,   0,   0,   0,   0,
      0,   0,   0,   0,   5,   0,   0,   0,   0,   0,   0,   0,   6,   7,   8,   0,
      9,   0,  10,  11,   0,   0,  12,  13,  14,  15,  16,   0,   0,   0,   0,  17,
     18,  19,  20,   0,   0,   0,   0,  21,   0,  22,  23,   0,   0,  22,  24,   0,
      0,  22,  24,   0,   0,  22,  24,   0,   0,  22,  24,   0,   0,   0,  24,   0,
      0,   0,  25,   0,   0,  22,  24,   0,   0,   0,  24,   0,   0,   0,  26,   0,
      0,  27,  28,   0,   0,  29,  30,   0,  31,  32,   0,  33,  34,   0,  35,   0,
      0,  36,   0,   0,  37,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  38,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,  39,  39,   0,   0,   0,   0,  40,   0,
      0,   0,   0,   0,   0,  41,   0,   0,   0,  42,   0,   0,   0,   0,   0,   0,
     43,   0,   0,  44,   0,  45,   0,   0,   0,  46,  47,  48,   0,  49,   0,  50,
      0,  51,   0,   0,   0,   0,  52,  53,   0,   0,   0,   0,   0,   0,  54,  55,
      0,   0,   0,   0,   0,   0,  56,  57,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,  58,   0,   0,   0,  59,   0,   0,   0,  60,
      0,  61,   0,   0,  62,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,  63,  64,   0,   0,  65,   0,   0,   0,   0,   0,   0,   0,   0,
     66,   0,   0,   0,   0,   0,  47,  67,   0,  68,  69,   0,   0,  70,  71,   0,
      0,   0,   0,   0,   0,  72,  73,  74,   0,   0,   0,   0,   0,   0,   0,  24,
      0,   0,   0,   0,   0,   0,   0,   0,  75,   0,   0,   0,   0,   0,   0,   0,
      0,  76,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  77,
      0,   0,   0,   0,   0,   0,   0,  78,   0,   0,   0,  79,   0,   0,   0,   0,
     80,  81,   0,   0,   0,   0,   0,  82,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,  66,  59,   0,  83,   0,   0,  84,  85,   0,  70,   0,   0,  86,   0,
      0,  87,   0,   0,   0,   0,   0,  88,   0,  22,  24,  89,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,  90,   0,   0,   0,   0,   0,   0,  59,  91,   0,
      0,  59,   0,   0,   0,  92,   0,   0,   0,  93,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,  94,   0,  95,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,  96,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  97,  98,  99,   0,   0,
      0,   0, 100,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0, 101,   0,   0,   0,   0,   0,   0,   0,   0,   0,
};

static RE_UINT8 re_canonical_combining_class_stage_4[] = {
      0,   0,   0,   0,   0,   0,   0,   0,   1,   1,   1,   1,   1,   2,   3,   4,
      5,   6,   7,   4,   4,   8,   9,  10,   1,  11,  12,  13,  14,  15,  16,  17,
     18,   1,   1,   1,   0,   0,   0,   0,  19,   1,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,  20,  21,  22,   1,  23,   4,  21,  24,  25,  26,  27,  28,
     29,  30,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   1,   1,  31,   0,
      0,   0,  32,  33,  34,  35,   1,  36,   0,   0,   0,   0,  37,   0,   0,   0,
      0,   0,   0,   0,   0,  38,   1,  39,  14,  39,  40,  41,   0,   0,   0,   0,
      0,   0,   0,   0,  42,   0,   0,   0,   0,   0,   0,   0,  43,  36,  44,  45,
     21,  45,  46,   0,   0,   0,   0,   0,   0,   0,  19,   1,  21,   0,   0,   0,
      0,   0,   0,   0,   0,  38,  47,   1,   1,  48,  48,  49,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,  50,   0,  51,  21,  43,  52,  53,  21,  35,   1,
      0,   0,   0,   0,   0,   0,   0,  54,   0,   0,   0,  55,  56,  57,   0,   0,
      0,   0,   0,  55,   0,   0,   0,   0,   0,   0,   0,  55,   0,  58,   0,   0,
      0,   0,  59,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  60,   0,
      0,   0,  61,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  62,   0,
      0,   0,  63,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  64,   0,
      0,   0,   0,   0,   0,  65,  66,   0,   0,   0,   0,   0,  67,  68,  69,  70,
     71,  72,   0,   0,   0,   0,   0,   0,   0,  73,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,  74,  75,   0,   0,   0,   0,  76,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,  48,   0,   0,   0,   0,   0,  77,   0,   0,
      0,   0,   0,   0,  59,   0,   0,  78,   0,   0,  79,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,  80,   0,   0,   0,   0,   0,   0,  19,  81,   0,
     77,   0,   0,   0,   0,  48,   1,  82,   0,   0,   0,   0,   1,  52,  15,  41,
      0,   0,   0,   0,   0,  54,   0,   0,   0,  77,   0,   0,   0,   0,   0,   0,
      0,   0,  19,  10,   1,   0,   0,   0,   0,   0,  83,   0,   0,   0,   0,   0,
      0,  84,   0,   0,  83,   0,   0,   0,   0,   0,   0,   0,   0,  74,   0,   0,
      0,   0,   0,   0,  85,   9,  12,   4,  86,   8,  87,  76,   0,  57,  49,   0,
     21,   1,  21,  88,  89,   1,   1,   1,   1,   1,   1,   1,   1,  49,   0,  90,
      0,   0,   0,   0,  91,   1,  92,  57,  78,  93,  94,   4,  57,   0,   0,   0,
      0,   0,   0,  19,  49,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  95,
      1,   1,   1,   1,   1,   1,   1,   1,   0,   0,  96,  97,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,  98,   0,   0,   0,   0,  19,   0,   1,   1,  49,
      0,   0,   0,   0,   0,   0,   0,  38,   0,   0,   0,   0,  49,   0,   0,   0,
      0,  59,   0,   0,   0,   0,   0,   0,   1,   1,   1,   1,  49,   0,   0,   0,
      0,   0,  51,  64,   0,   0,   0,   0,   0,   0,   0,   0,  95,   0,   0,   0,
      0,   0,   0,   0,  74,   0,   0,   0,  77,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,  99, 100,  57,  38,  78,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,  59,   0,   0,   0,   0,   0,   0,   0,   0,   0, 101,
      1,  14,   4,  12,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  76,
     81,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  38,  85,   0,
      0,   0,   0, 102,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 103,  95,
      0, 104,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 105,   0,
     85,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  95,  77,   0,   0,
     77,   0,  84,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 105,   0,   0,
      0,   0, 106,   0,   0,   0,   0,   0,   0,  38,   1,  57,   1,  57,   0,   0,
    107,   0,   0,   0,   0,   0,   0,   0,  54,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0, 107,   0,   0,   0,   0,  95,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   8,  87,   0,   0,   0,   0,   0,   0,   1,  85,   0,   0,
      0,   0,   0,   0,   0,   0,   0, 108,   0, 109, 110, 111, 112,   0,  51,   4,
    113,  48,  23,   0,   0,   0,   0,   0,   0,   0,  38,  49,   0,   0,   0,   0,
     38,  57,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   4, 113,   0,   0,
};

static RE_UINT8 re_canonical_combining_class_stage_5[] = {
     0,  0,  0,  0, 50, 50, 50, 50, 50, 51, 45, 45, 45, 45, 51, 43,
    45, 45, 45, 45, 45, 41, 41, 45, 45, 45, 45, 41, 41, 45, 45, 45,
     1,  1,  1,  1,  1, 45, 45, 45, 45, 50, 50, 50, 50, 54, 50, 45,
    45, 45, 50, 50, 50, 45, 45,  0, 50, 50, 50, 45, 45, 45, 45, 50,
    51, 45, 45, 50, 52, 53, 53, 52, 53, 53, 52, 50,  0,  0,  0, 50,
     0, 45, 50, 50, 50, 50, 45, 50, 50, 50, 46, 45, 50, 50, 45, 45,
    50, 46, 49, 50,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 14, 15,
    16, 17,  0, 18,  0, 19, 20,  0, 50, 45,  0, 13, 25, 26, 27,  0,
     0,  0,  0, 22, 23, 24, 25, 26, 27, 28, 29, 50, 50, 45, 45, 50,
    45, 50, 50, 45, 30,  0,  0,  0,  0,  0, 50, 50, 50,  0,  0, 50,
    50,  0, 45, 50, 50, 45,  0,  0,  0, 31,  0,  0, 50, 45, 50, 50,
    45, 45, 50, 45, 45, 50, 45, 50, 45, 50, 50,  0, 50, 50,  0, 50,
     0, 50, 50, 50, 50, 50,  0,  0,  0, 45, 45, 45,  0,  0,  0, 45,
    50, 45, 45, 45, 22, 23, 24, 50,  2,  0,  0,  0,  0,  4,  0,  0,
     0, 50, 45, 50, 50,  0,  0,  0,  0, 32, 33,  0,  0,  0,  4,  0,
    34, 34,  4,  0, 35, 35, 35, 35, 36, 36,  0,  0, 37, 37, 37, 37,
    45, 45,  0,  0,  0, 45,  0, 45,  0, 43,  0,  0,  0, 38, 39,  0,
    40,  0,  0,  0,  0,  0, 39, 39, 39, 39,  0,  0, 39,  0, 50, 50,
     4,  0, 50, 50,  0,  0, 45,  0,  0,  0,  0,  2,  0,  4,  4,  0,
     0, 45,  0,  0,  4,  0,  0,  0,  0, 50,  0,  0,  0, 49,  0,  0,
     0, 46, 50, 45, 45,  0,  0,  0, 50,  0,  0, 45,  0,  0,  4,  4,
     0,  0,  2,  0, 50, 50, 50,  0, 50,  0,  1,  1,  1,  0,  0,  0,
    50, 53, 42, 45, 41, 50, 50, 50, 52, 45, 50, 45, 50, 50,  1,  1,
     1,  1,  1, 50,  0,  1,  1, 50, 45, 50,  1,  1,  0,  0,  0,  4,
     0,  0, 44, 49, 51, 46, 47, 47,  0,  3,  3,  0, 50,  0, 50, 50,
    45,  0,  0, 50,  0,  0, 21,  0,  0, 45,  0, 50, 50,  1, 45,  0,
     0, 50, 45,  0,  0,  4,  2,  0,  0,  2,  4,  0,  0,  0,  4,  2,
     0,  0,  1,  0,  0, 43, 43,  1,  1,  1,  0,  0,  0, 48, 43, 43,
    43, 43, 43,  0, 45, 45, 45,  0,
};

/* Canonical_Combining_Class: 2112 bytes. */

RE_UINT32 re_get_canonical_combining_class(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 13;
    code = ch ^ (f << 13);
    pos = (RE_UINT32)re_canonical_combining_class_stage_1[f] << 4;
    f = code >> 9;
    code ^= f << 9;
    pos = (RE_UINT32)re_canonical_combining_class_stage_2[pos + f] << 4;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_canonical_combining_class_stage_3[pos + f] << 3;
    f = code >> 2;
    code ^= f << 2;
    pos = (RE_UINT32)re_canonical_combining_class_stage_4[pos + f] << 2;
    value = re_canonical_combining_class_stage_5[pos + code];

    return value;
}

/* Decomposition_Type. */

static RE_UINT8 re_decomposition_type_stage_1[] = {
    0, 1, 2, 2, 2, 3, 4, 5, 6, 2, 2, 2, 2, 2, 7, 8,
    2, 2, 2, 2, 2, 2, 2, 9, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2,
};

static RE_UINT8 re_decomposition_type_stage_2[] = {
     0,  1,  2,  3,  4,  5,  6,  7,  7,  8,  9, 10, 11, 12, 13, 14,
    15,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7, 16,  7, 17, 18, 19,
    20, 21, 22, 23, 24,  7,  7,  7,  7,  7, 25,  7, 26, 27, 28, 29,
    30, 31, 32, 33,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  7,  7,  7, 34, 35,  7,  7,  7, 36, 37, 37, 37, 37,
    37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37,
    37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37,
    37, 37, 37, 37, 37, 37, 37, 38,  7,  7,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  7,  7,  7,  7,  7,  7, 37, 39, 40, 41, 42, 43, 44,
     7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,
    45, 46,  7, 47, 48, 49,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,
     7, 50,  7,  7, 51, 52, 53, 54,  7,  7,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7, 55,  7,
     7, 56, 57,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  7,  7,  7,  7,  7, 37, 37, 58,  7,  7,  7,  7,  7,
};

static RE_UINT8 re_decomposition_type_stage_3[] = {
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   1,   2,   3,   4,   3,   5,
      6,   7,   8,   9,  10,  11,   8,  12,   0,   0,  13,  14,  15,  16,  17,  18,
      6,  19,  20,  21,   0,   0,   0,   0,   0,   0,   0,  22,   0,  23,  24,   0,
      0,   0,   0,   0,  25,   0,   0,  26,  27,  14,  28,  14,  29,  30,   0,  31,
     32,  33,   0,  33,   0,  32,   0,  34,   0,   0,   0,   0,  35,  36,  37,  38,
      0,   0,   0,   0,   0,   0,   0,   0,  39,   0,   0,   0,   0,   0,   0,   0,
      0,   0,  40,   0,   0,   0,   0,  41,   0,   0,   0,   0,  42,  43,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,  33,  44,   0,  45,   0,   0,   0,   0,   0,   0,  46,  47,   0,   0,
      0,   0,   0,  48,   0,  49,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,  50,  51,   0,   0,   0,  52,   0,   0,  53,   0,   0,   0,
      0,   0,   0,   0,  54,   0,   0,   0,   0,   0,   0,   0,  55,   0,   0,   0,
      0,   0,   0,   0,  53,   0,   0,   0,   0,   0,   0,   0,   0,  56,   0,   0,
      0,   0,   0,  57,   0,   0,   0,   0,   0,   0,   0,  57,   0,  58,   0,   0,
     59,   0,   0,   0,  60,  61,  33,  62,  63,  60,  61,  33,   0,   0,   0,   0,
      0,   0,  64,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  65,
     66,  67,   0,  68,  69,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,  70,  71,  72,  73,  74,  75,   0,  76,  73,  73,   0,   0,   0,   0,
      6,   6,   6,   6,   6,   6,   6,   6,   6,  77,   6,   6,   6,   6,   6,  78,
      6,  79,   6,   6,  79,  80,   6,  81,   6,   6,   6,  82,  83,  84,   6,  85,
     86,  87,  88,  89,  90,  91,   0,  92,  93,  94,  95,   0,   0,   0,   0,   0,
     96,  97,  98,  99, 100, 101, 102, 102, 103, 104, 105,   0, 106,   0,   0,   0,
    107,   0, 108, 109, 110,   0, 111, 112, 112,   0, 113,   0,   0,   0, 114,   0,
      0,   0, 115,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0, 116, 117, 102, 102, 102, 118, 116, 116, 119,   0,
    120,   0,   0,   0,   0,   0,   0, 121,   0,   0,   0,   0,   0, 122,   0,   0,
      0,   0,   0,   0,   0,   0,   0, 123,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0, 124,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,   0, 125,   0,   0,   0,   0,   0,  57,
    102, 102, 102, 102, 102, 102, 102, 102, 102, 102, 102, 102, 102, 126,   0,   0,
    127,   0,   0, 128, 129, 130, 131, 132,   0, 133, 129, 130, 131, 132,   0, 134,
      0,   0,   0, 135, 102, 102, 102, 102, 136, 137,   0,   0,   0,   0,   0,   0,
    102, 136, 102, 102, 138, 139, 116, 140, 116, 116, 116, 116, 141, 116, 116, 140,
    142, 142, 142, 142, 142, 143, 102, 144, 142, 142, 142, 142, 142, 142, 102, 145,
      0,   0,   0,   0,   0,   0,   0,   0,   0, 146,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0, 147,   0,   0,   0,   0,   0,   0,   0, 148,
      0,   0,   0,   0,   0, 149,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      6,   6,   6,   6,   6,   6,   6,   6,   6,   6,   6,   6,   6,   6,   6,   6,
      6,   6,   6,   6,   6,   6,   6,   6,   6,   6,  21,   0,   0,   0,   0,   0,
     81, 150, 151,   6,   6,   6,  81,   6,   6,   6,   6,   6,   6,  78,   0,   0,
    152, 153, 154, 155, 156, 157, 158, 158, 159, 158, 160, 161,   0, 162, 163, 164,
    165, 165, 165, 165, 165, 165, 166, 167, 167, 168, 169, 169, 169, 170, 171, 172,
    165, 173, 174, 175,   0, 176, 177, 178, 179, 180, 167, 181, 182,   0,   0, 183,
      0, 184,   0, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 194, 195, 196,
    197, 198, 198, 198, 198, 198, 199, 200, 200, 200, 200, 201, 202, 203, 204,   0,
      0,   0,   0,   0,   0,   0,   0,   0,   0, 205, 206,   0,   0,   0,   0,   0,
      0,   0, 207,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,  46,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 208,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 104,   0,   0,   0,   0,
      0,   0,   0,   0,   0, 207, 209,   0,   0,   0,   0, 210,  14,   0,   0,   0,
    211, 211, 211, 211, 211, 212, 211, 211, 211, 213, 214, 215, 216, 211, 211, 211,
    217, 218, 211, 219, 220, 221, 211, 211, 211, 211, 211, 211, 211, 211, 211, 211,
    211, 211, 211, 211, 211, 211, 211, 211, 211, 211, 222, 211, 211, 211, 211, 211,
    211, 211, 211, 211, 211, 211, 211, 211, 211, 211, 211, 211, 223, 211, 211, 211,
    216, 211, 224, 225, 226, 227, 228, 229, 230, 231, 232, 231,   0,   0,   0,   0,
    233, 102, 234, 142, 142,   0, 235,   0,   0, 236,   0,   0,   0,   0,   0,   0,
    237, 142, 142, 238, 239, 240,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      6,  81,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
};

static RE_UINT8 re_decomposition_type_stage_4[] = {
      0,   0,   0,   0,   1,   0,   2,   3,   4,   5,   6,   7,   8,   9,   8,   8,
     10,  11,  10,  12,  10,  11,  10,   9,   8,   8,   8,   8,  13,   8,   8,   8,
      8,  12,   8,   8,  14,   8,  10,  15,  16,   8,  17,   8,  12,   8,   8,   8,
      8,   8,   8,  15,  12,   0,   0,  18,  19,   0,   0,   0,   0,  20,  20,  21,
      8,   8,   8,  22,   8,  13,   8,   8,  23,  12,   8,   8,   8,   8,   8,  13,
      0,  13,   8,   8,   8,   0,   0,   0,  24,  24,  25,   0,   0,   0,  20,   5,
     24,  25,   0,   0,   9,  19,   0,   0,   0,  19,  26,  27,   0,  21,  11,  22,
      0,   0,  13,   8,   0,   0,  13,  11,  28,  29,   0,   0,  30,   5,  31,   0,
      9,  18,   0,  11,   0,   0,  32,   0,   0,  13,   0,   0,  33,   0,   0,   0,
      8,  13,  13,   8,  13,   8,  13,   8,   8,  12,  12,   0,   0,   3,   0,   0,
     13,  11,   0,   0,   0,  34,  35,   0,  36,   0,   0,   0,  18,   0,   0,   0,
     32,  19,   0,   0,   0,   0,   8,   8,   0,   0,  18,  19,   0,   0,   0,   9,
     18,  27,   0,   0,   0,   0,  10,  27,   0,   0,  37,  19,   0,   0,   0,  12,
      0,  19,   0,   0,   0,   0,  13,  19,   0,   0,  19,   0,  19,  18,  22,   0,
      0,   0,  27,  11,   3,   0,   0,   0,   0,   0,   0,   5,   0,   0,   0,   1,
     18,   0,   0,  32,  27,  18,   0,  19,  18,  38,  17,   0,  32,   0,   0,   0,
      0,  27,   0,   0,   0,   0,   0,  25,   0,  27,  36,  36,  27,   0,   0,   0,
      0,   0,  18,  32,   9,   0,   0,   0,   0,   0,   0,  39,  24,  24,  39,  24,
     24,  24,  24,  40,  24,  24,  24,  24,  41,  42,  43,   0,   0,   0,  25,   0,
      0,   0,  44,  24,   8,   8,  45,   0,   8,   8,  12,   0,   8,  12,   8,  12,
      8,   8,  46,  46,   8,   8,   8,  12,   8,  22,   8,  47,  21,  22,   8,   8,
      8,  13,   8,  10,  13,  22,   8,  48,  49,  50,  30,   0,  51,   3,   0,   0,
      0,  30,   0,  52,   3,  53,   0,  54,   0,   3,   5,   0,   0,   3,   0,   3,
     55,  24,  24,  24,  42,  42,  42,  43,  42,  42,  42,  56,   0,   0,  35,   0,
     57,  34,  58,  59,  59,  60,  61,  62,  63,  64,  65,  66,  66,  67,  68,  59,
     69,  61,  62,   0,  70,  70,  70,  70,  20,  20,  20,  20,   0,   0,  71,   0,
      0,   0,  13,   0,   0,   0,   0,  27,   0,   0,   0,  10,   0,  19,  32,  19,
      0,  36,   0,  72,  35,   0,   0,   0,  32,  37,  32,   0,  36,   0,   0,  10,
     12,  12,  12,   0,   0,   0,   0,   8,   8,   0,  13,  12,   0,   0,  33,   0,
     73,  73,  73,  73,  73,  20,  20,  20,  20,  74,  73,  73,  73,  73,  75,   0,
      0,   0,   0,  35,   0,  30,   0,   0,   0,   0,   0,  19,   0,   0,   0,  76,
      0,   0,   0,  44,   0,   0,   0,   3,  20,   5,   0,   0,  77,   0,   0,   0,
      0,  26,  30,   0,   0,   0,   0,  36,  36,  36,  36,  36,  36,  46,  32,   0,
      9,  22,  33,  12,   0,  19,   3,  78,   0,  37,  11,  79,  34,  20,  20,  20,
     20,  20,  20,  30,   4,  24,  24,  24,  20,  73,   0,   0,  80,  73,  73,  73,
     73,  73,  73,  75,  20,  20,  20,  81,  81,  81,  81,  81,  81,  81,  20,  20,
     82,  81,  81,  81,  20,  20,  20,  83,   0,   0,   0,  55,  25,   0,   0,   0,
      0,   0,  55,   0,   0,   0,   0,  24,  36,  10,   8,  11,  36,  33,  13,   8,
     20,  30,   0,   0,   3,  20,   0,  46,  59,  59,  84,   8,   8,  11,   8,  36,
      9,  22,   8,  15,  85,  86,  86,  86,  86,  86,  86,  86,  86,  85,  85,  85,
     87,  85,  86,  86,  88,   0,   0,   0,  89,  90,  91,  92,  85,  87,  86,  85,
     85,  85,  93,  87,  94,  94,  94,  94,  94,  95,  95,  95,  95,  95,  95,  95,
     95,  96,  97,  97,  97,  97,  97,  97,  97,  97,  97,  98,  99,  99,  99,  99,
     99, 100,  94,  94, 101,  95,  95,  95,  95,  95,  95, 102,  97,  99,  99, 103,
    104,  97, 105, 106, 107, 105, 108, 105, 104,  96,  95, 105,  96, 109, 110,  97,
    111, 106, 112, 105,  95, 106, 113,  95,  96, 106,   0,   0,  94,  94,  94, 114,
    115, 115, 116,   0, 115, 115, 115, 115, 115, 117, 118,  20, 119, 120, 120, 120,
    120, 119, 120,   0, 121, 122, 123, 123, 124,  91, 125, 126,  90, 125, 127, 127,
    127, 127, 126,  91, 125, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 126,
    125, 126,  91, 128, 129, 130, 130, 130, 130, 130, 130, 130, 131, 132, 132, 132,
    132, 132, 132, 132, 132, 132, 132, 133, 134, 132, 134, 132, 134, 132, 134, 135,
    130, 136, 132, 133,   0,   0,  27,  19,   0,   0,  18,   0,   0,   0,   0,  13,
      0,   0,  18,  36,   8,  19,   0,   0,   0,   0,  18,   8,  59,  59,  59,  59,
     59, 137,  59,  59,  59,  59,  59, 137, 138, 139,  61, 137,  59,  59,  66,  61,
     59,  61,  59,  59,  59,  66, 140,  61,  59, 137,  59, 137,  59,  59,  66, 140,
     59, 141, 142,  59, 137,  59,  59,  59,  59,  62,  59,  59,  59,  59,  59, 142,
    139, 143,  61,  59, 140,  59, 144,   0, 138, 145, 144,  61, 139, 143, 144, 144,
    139, 143, 140,  59, 140,  59,  61, 141,  59,  59,  66,  59,  59,  59,  59,   0,
     61,  61,  66,  59,  20,  20,  30,   0,  20,  20, 146,  75,   0,   0,   4,   0,
    147,   0,   0,   0, 148,   0,   0,   0,  81,  81, 148,   0,  20,  20,  35,   0,
    149,   0,   0,   0,
};

static RE_UINT8 re_decomposition_type_stage_5[] = {
     0,  0,  0,  0,  4,  0,  0,  0,  2,  0, 10,  0,  0,  0,  0,  2,
     0,  0, 10, 10,  2,  2,  0,  0,  2, 10, 10,  0, 17, 17, 17,  0,
     1,  1,  1,  1,  1,  1,  0,  1,  0,  1,  1,  1,  1,  1,  1,  0,
     1,  1,  0,  0,  0,  0,  1,  1,  1,  0,  2,  2,  1,  1,  1,  2,
     2,  0,  0,  1,  1,  2,  0,  0,  0,  0,  0,  1,  1,  0,  0,  0,
     2,  2,  2,  2,  2,  1,  1,  1,  1,  0,  1,  1,  1,  2,  2,  2,
    10, 10, 10, 10, 10,  0,  0,  0,  0,  0,  2,  0,  0,  0,  1,  0,
     2,  2,  2,  1,  1,  2,  2,  0,  2,  2,  2,  0,  0,  2,  0,  0,
     0,  1,  0,  0,  0,  1,  1,  0,  0,  2,  2,  2,  2,  0,  0,  0,
     1,  0,  1,  0,  1,  0,  0,  1,  0,  1,  1,  2, 10, 10, 10,  0,
    10, 10,  0, 10, 10, 10, 11, 11, 11, 11, 11, 11, 11, 11, 11,  0,
     0,  0,  0, 10,  1,  1,  2,  1,  0,  1,  0,  1,  1,  2,  1,  2,
     1,  1,  2,  0,  1,  1,  2,  2,  2,  2,  2,  4,  0,  4,  0,  0,
     0,  0,  0,  4,  2,  0,  2,  2,  2,  0,  2,  0, 10, 10,  0,  0,
    11,  0,  0,  0,  2,  2,  3,  2,  0,  2,  3,  3,  3,  3,  3,  3,
     0,  3,  2,  0,  0,  3,  3,  3,  3,  3,  0,  0, 10,  2, 10,  0,
     3,  0,  1,  0,  3,  0,  1,  1,  3,  3,  0,  3,  3,  2,  2,  2,
     2,  3,  0,  2,  3,  0,  0,  0, 17, 17, 17, 17,  0, 17,  0,  0,
     2,  2,  0,  2,  9,  9,  9,  9,  2,  2,  9,  9,  9,  9,  9,  0,
    11, 10,  0,  0, 13,  0,  0,  0,  2,  0,  1, 12,  0,  0,  1, 12,
    16,  9,  9,  9, 16, 16, 16, 16,  2, 16, 16, 16,  2,  2,  2, 16,
     3,  3,  1,  1,  8,  7,  8,  7,  5,  6,  8,  7,  8,  7,  5,  6,
     8,  7,  0,  0,  0,  0,  0,  8,  7,  5,  6,  8,  7,  8,  7,  8,
     7,  8,  8,  7,  5,  8,  7,  5,  8,  8,  8,  8,  7,  7,  7,  7,
     7,  7,  7,  5,  5,  5,  5,  5,  5,  5,  5,  6,  6,  6,  6,  6,
     6,  8,  8,  8,  8,  7,  7,  7,  7,  5,  5,  5,  7,  8,  0,  0,
     5,  7,  5,  5,  7,  5,  7,  7,  5,  5,  7,  7,  5,  5,  7,  5,
     5,  7,  7,  5,  7,  7,  5,  7,  5,  5,  5,  7,  0,  0,  5,  5,
     5,  7,  7,  7,  5,  7,  5,  7,  8,  0,  0,  0, 12, 12, 12, 12,
    12, 12,  0,  0, 12,  0,  0, 12, 12,  2,  2,  2, 15, 15, 15,  0,
    15, 15, 15, 15,  8,  6,  8,  0,  8,  0,  8,  6,  8,  6,  8,  6,
     8,  8,  7,  8,  7,  8,  7,  5,  6,  8,  7,  8,  6,  8,  7,  5,
     7,  0,  0,  0,  0, 13, 13, 13, 13, 13, 13, 13, 13, 14, 14, 14,
    14, 14, 14, 14, 14, 14, 14,  0,  0,  0, 14, 14, 14,  0,  0,  0,
    13, 13, 13,  0,  3,  0,  3,  3,  0,  0,  3,  0,  0,  3,  3,  0,
     3,  3,  3,  0,  3,  0,  3,  0,  0,  0,  3,  3,  3,  0,  0,  3,
     0,  3,  0,  3,  0,  0,  0,  3,  2,  2,  2,  9, 16,  0,  0,  0,
    16, 16, 16,  0,  9,  9,  0,  0,
};

/* Decomposition_Type: 2964 bytes. */

RE_UINT32 re_get_decomposition_type(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 13;
    code = ch ^ (f << 13);
    pos = (RE_UINT32)re_decomposition_type_stage_1[f] << 5;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_decomposition_type_stage_2[pos + f] << 4;
    f = code >> 4;
    code ^= f << 4;
    pos = (RE_UINT32)re_decomposition_type_stage_3[pos + f] << 2;
    f = code >> 2;
    code ^= f << 2;
    pos = (RE_UINT32)re_decomposition_type_stage_4[pos + f] << 2;
    value = re_decomposition_type_stage_5[pos + code];

    return value;
}

/* East_Asian_Width. */

static RE_UINT8 re_east_asian_width_stage_1[] = {
     0,  1,  2,  3,  4,  5,  5,  5,  5,  5,  6,  5,  5,  7,  8,  9,
    10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 11, 10, 10, 10, 12,
     5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5, 13,
     5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5, 13,
    10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
    10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
    10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
    10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
    10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
    10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
    10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
    10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
    10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
    10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
    14, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
     8,  8,  8,  8,  8,  8,  8,  8,  8,  8,  8,  8,  8,  8,  8, 15,
     8,  8,  8,  8,  8,  8,  8,  8,  8,  8,  8,  8,  8,  8,  8, 15,
};

static RE_UINT8 re_east_asian_width_stage_2[] = {
     0,  1,  2,  3,  4,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,
     5,  6,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,
     7,  8,  9, 10, 11, 12, 13, 14,  5, 15,  5, 16,  5,  5, 17, 18,
    19, 20, 21, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22,
    22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 23, 22, 22,
    22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22,
    22, 22, 22, 22, 24,  5,  5,  5,  5, 25,  5,  5, 22, 22, 22, 22,
    22, 22, 22, 22, 22, 22, 22, 26,  5,  5,  5,  5,  5,  5,  5,  5,
    27, 27, 27, 27, 27, 27, 27, 27, 27, 27, 27, 27, 27, 27, 27, 27,
    27, 27, 27, 27, 27, 27, 27, 27, 27, 22, 22,  5,  5,  5, 28, 29,
     5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,
    30,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,
     5, 31, 32,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,
    22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 33,
     5, 34,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,
    27, 27, 27, 27, 27, 27, 27, 27, 27, 27, 27, 27, 27, 27, 27, 35,
};

static RE_UINT8 re_east_asian_width_stage_3[] = {
     0,  0,  1,  1,  1,  1,  1,  2,  0,  0,  3,  4,  5,  6,  7,  8,
     9, 10, 11, 12, 13, 14, 11,  0,  0,  0,  0,  0, 15, 16,  0,  0,
     0,  0,  0,  0,  0,  9,  9,  0,  0,  0,  0,  0, 17, 18,  0,  0,
    19, 19, 19, 19, 19, 19, 19,  0,  0, 20, 21, 20, 21,  0,  0,  0,
     9, 19, 19, 19, 19,  9,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
    22, 22, 22, 22, 22, 22,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0, 23, 24, 25,  0,  0,  0, 26, 27,  0, 28,  0,  0,  0,  0,  0,
    29, 30, 31,  0,  0, 32, 33, 34, 35, 34,  0, 36,  0, 37, 38,  0,
    39, 40, 41, 42, 43, 44, 45,  0, 46, 47, 48, 49,  0,  0,  0,  0,
     0, 44, 50,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0, 19, 19, 19, 19, 19, 19, 19, 19, 51, 19,
    19, 19, 19, 19, 33, 19, 19, 52, 19, 53, 21, 54, 55, 56, 57,  0,
    58, 59,  0,  0, 60,  0, 61,  0,  0, 62,  0, 62, 63, 19, 64, 19,
     0,  0,  0, 65,  0, 38,  0, 66,  0,  0,  0,  0,  0,  0, 67,  0,
     0,  0,  0,  0,  0,  0,  0,  0, 68,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0, 69,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0, 22, 70, 22, 22, 22, 22, 22, 71,
    22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 72,  0, 73,
    74, 22, 22, 75, 76, 22, 22, 22, 22, 77, 22, 22, 22, 22, 22, 22,
    78, 22, 79, 76, 22, 22, 22, 22, 75, 22, 22, 80, 22, 22, 71, 22,
    22, 75, 22, 22, 81, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 75,
    22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22,
    22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22,  0,  0,  0,  0,
    22, 22, 22, 22, 22, 22, 22, 22, 82, 22, 22, 22, 83,  0,  0,  0,
     0,  0,  0,  0,  0,  0, 22, 82,  0,  0,  0,  0,  0,  0,  0,  0,
    22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 71,  0,  0,  0,  0,  0,
    19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19,
    19, 84,  0, 22, 22, 85, 86,  0,  0,  0,  0,  0,  0,  0,  0,  0,
    87, 88, 88, 88, 88, 88, 89, 90, 90, 90, 90, 91, 92, 93, 94, 65,
    95,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
    96, 19, 97, 19, 19, 19, 34, 19, 19, 96,  0,  0,  0,  0,  0,  0,
    98, 22, 22, 80, 99, 95,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
    22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 79,
    19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19,  0,
    19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 97,
};

static RE_UINT8 re_east_asian_width_stage_4[] = {
     0,  0,  0,  0,  1,  1,  1,  1,  1,  1,  1,  2,  3,  4,  5,  6,
     7,  8,  9,  7,  0, 10,  0,  0, 11, 12, 11, 13, 14, 10,  9, 14,
     8, 12,  9,  5, 15,  0,  0,  0, 16,  0, 12,  0,  0, 13, 12,  0,
    17,  0, 11, 12,  9, 11,  7, 15, 13,  0,  0,  0,  0,  0,  0, 10,
     5,  5,  5, 11,  0, 18, 17, 15, 11,  0,  7, 16,  7,  7,  7,  7,
    17,  7,  7,  7, 19,  7, 14,  0, 20, 20, 20, 20, 18,  9, 14, 14,
     9,  7,  0,  0,  8, 15, 12, 10,  0, 11,  0, 12, 17, 11,  0,  0,
     0,  0, 21, 11, 12, 15, 15,  0, 12, 10,  0,  0, 22, 10, 12,  0,
    12, 11, 12,  9,  7,  7,  7,  0,  7,  7, 14,  0,  0,  0, 15,  0,
     0,  0, 14,  0, 10, 11,  0,  0,  0, 12,  0,  0,  8, 12, 18, 12,
    15, 15, 10, 17, 18, 16,  7,  5,  0,  7,  0, 14,  0,  0, 11, 11,
    10,  0,  0,  0, 14,  7, 13, 13, 13, 13,  0,  0,  0, 15, 15,  0,
     0, 15,  0,  0,  0,  0,  0, 12,  0,  0, 23,  0,  7,  7, 19,  7,
     7,  0,  0,  0, 13, 14,  0,  0, 13, 13,  0, 14, 14, 13, 18, 13,
    14,  0,  0,  0, 13, 14,  0, 12,  0, 22, 15, 13,  0, 14,  0,  5,
     5,  0,  0,  0, 19, 19,  9, 19,  0,  0,  0, 13,  0,  7,  7, 19,
    19,  0,  7,  7,  0,  0,  0, 15,  0, 13,  7,  7,  0, 24,  1, 25,
     0, 26,  0,  0,  0, 17, 14,  0, 20, 20, 27, 20, 20,  0,  0,  0,
    20, 28,  0,  0, 20, 20, 20,  0, 29, 20, 20, 20, 20, 20, 20, 30,
    31, 20, 20, 20, 20, 30, 31, 20,  0, 31, 20, 20, 20, 20, 20, 28,
    20, 20, 30,  0, 20, 20,  7,  7, 20, 20, 20, 32, 20, 30,  0,  0,
    20, 20, 28,  0, 30, 20, 20, 20, 20, 30, 20,  0, 33, 34, 34, 34,
    34, 34, 34, 34, 35, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 37,
    38, 36, 38, 36, 38, 36, 38, 39, 34, 40, 36, 37, 28,  0,  0,  0,
     7,  7,  9,  0,  7,  7,  7, 14, 30,  0,  0,  0, 20, 20, 32,  0,
};

static RE_UINT8 re_east_asian_width_stage_5[] = {
    0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 0, 0, 1, 5, 5,
    1, 5, 5, 1, 1, 0, 1, 0, 5, 1, 1, 5, 1, 1, 1, 1,
    1, 0, 1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0,
    0, 0, 0, 1, 0, 0, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0,
    0, 1, 0, 1, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 0, 1,
    3, 3, 3, 3, 0, 2, 0, 0, 0, 1, 1, 0, 0, 3, 3, 0,
    0, 0, 5, 5, 5, 5, 0, 0, 0, 5, 5, 0, 3, 3, 0, 3,
    3, 3, 0, 0, 4, 3, 3, 3, 3, 3, 3, 0, 0, 3, 3, 3,
    3, 0, 0, 0, 0, 4, 4, 4, 4, 4, 4, 4, 4, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 2, 2, 2, 0, 0, 0,
    4, 4, 4, 0,
};

/* East_Asian_Width: 1668 bytes. */

RE_UINT32 re_get_east_asian_width(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 12;
    code = ch ^ (f << 12);
    pos = (RE_UINT32)re_east_asian_width_stage_1[f] << 4;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_east_asian_width_stage_2[pos + f] << 4;
    f = code >> 4;
    code ^= f << 4;
    pos = (RE_UINT32)re_east_asian_width_stage_3[pos + f] << 2;
    f = code >> 2;
    code ^= f << 2;
    pos = (RE_UINT32)re_east_asian_width_stage_4[pos + f] << 2;
    value = re_east_asian_width_stage_5[pos + code];

    return value;
}

/* Joining_Group. */

static RE_UINT8 re_joining_group_stage_1[] = {
    0, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1,
};

static RE_UINT8 re_joining_group_stage_2[] = {
    0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
};

static RE_UINT8 re_joining_group_stage_3[] = {
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 0,
    0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
};

static RE_UINT8 re_joining_group_stage_4[] = {
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  1,  2,  3,  4,  5,  6,  0,  0,  0,  7,  8,  9,
    10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,  0,  0, 21,  0, 22,
     0,  0, 23, 24, 25, 26,  0,  0,  0, 27, 28, 29, 30, 31, 32, 33,
     0,  0,  0,  0, 34, 35, 36,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0, 37, 38, 39, 40, 41, 42,  0,  0,
};

static RE_UINT8 re_joining_group_stage_5[] = {
     0,  0,  0,  0,  0,  0,  0,  0, 45,  0,  3,  3, 43,  3, 45,  3,
     4, 41,  4,  4, 13, 13, 13,  6,  6, 31, 31, 35, 35, 33, 33, 39,
    39,  1,  1, 11, 11, 55, 55, 55,  0,  9, 29, 19, 22, 24, 26, 16,
    43, 45, 45,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  4, 29,
     0,  3,  3,  3,  0,  3, 43, 43, 45,  4,  4,  4,  4,  4,  4,  4,
     4, 13, 13, 13, 13, 13, 13, 13,  6,  6,  6,  6,  6,  6,  6,  6,
     6, 31, 31, 31, 31, 31, 31, 31, 31, 31, 35, 35, 35, 33, 33, 39,
     1,  9,  9,  9,  9,  9,  9, 29, 29, 11, 38, 11, 19, 19, 19, 11,
    11, 11, 11, 11, 11, 22, 22, 22, 22, 26, 26, 26, 26, 56, 21, 13,
    41, 17, 17, 14, 43, 43, 43, 43, 43, 43, 43, 43, 55, 47, 55, 43,
    45, 45, 46, 46,  0, 41,  0,  0,  0,  0,  0,  0,  0,  0,  6, 31,
     0,  0, 35, 33,  1,  0,  0, 21,  2,  0,  5, 12, 12,  7,  7, 15,
    44, 50, 18, 42, 42, 48, 49, 20, 23, 25, 27, 36, 10,  8, 28, 32,
    34, 30,  7, 37, 40,  5, 12,  7,  0,  0,  0,  0,  0, 51, 52, 53,
     4,  4,  4,  4,  4,  4,  4, 13, 13,  6,  6, 31, 35,  1,  1,  1,
     9,  9, 11, 11, 11, 24, 24, 26, 26, 26, 22, 31, 31, 35, 13, 13,
    35, 31, 13,  3,  3, 55, 55, 45, 43, 43, 54, 54, 13, 35, 35, 19,
     4,  4, 13, 39,  9, 29, 22, 24, 45, 45, 31, 43, 57,  0,  6, 33,
    11, 58, 31,  1, 19,  0,  0,  0, 59, 61, 61, 65, 65, 62,  0, 83,
     0, 85, 85,  0,  0, 66, 80, 84, 68, 68, 68, 69, 63, 81, 70, 71,
    77, 60, 60, 73, 73, 76, 74, 74, 74, 75,  0,  0, 78,  0,  0,  0,
     0,  0,  0, 72, 64, 79, 82, 67,
};

/* Joining_Group: 586 bytes. */

RE_UINT32 re_get_joining_group(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 15;
    code = ch ^ (f << 15);
    pos = (RE_UINT32)re_joining_group_stage_1[f] << 4;
    f = code >> 11;
    code ^= f << 11;
    pos = (RE_UINT32)re_joining_group_stage_2[pos + f] << 4;
    f = code >> 7;
    code ^= f << 7;
    pos = (RE_UINT32)re_joining_group_stage_3[pos + f] << 4;
    f = code >> 3;
    code ^= f << 3;
    pos = (RE_UINT32)re_joining_group_stage_4[pos + f] << 3;
    value = re_joining_group_stage_5[pos + code];

    return value;
}

/* Joining_Type. */

static RE_UINT8 re_joining_type_stage_1[] = {
     0,  1,  2,  3,  4,  4,  4,  4,  4,  4,  5,  4,  4,  4,  4,  6,
     7,  8,  4,  4,  4,  4,  9,  4,  4,  4,  4, 10,  4, 11, 12,  4,
     4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,
     4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,
     4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,
     4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,
     4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,
     4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,
     4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,
     4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,
     4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,
     4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,
     4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,
     4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,
    13,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,
     4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,
     4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,
};

static RE_UINT8 re_joining_type_stage_2[] = {
     0,  1,  0,  0,  0,  0,  2,  0,  0,  3,  0,  4,  5,  6,  7,  8,
     9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24,
    25, 26,  0,  0,  0,  0, 27,  0,  0,  0,  0,  0,  0,  0, 28, 29,
    30, 31, 32,  0, 33, 34, 35, 36, 37, 38,  0, 39,  0,  0,  0,  0,
    40, 41,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0, 42, 43, 44,  0,  0,  0,  0,
    45, 46,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 47, 48,  0,  0,
    49, 50, 51, 52, 53, 54,  0, 55,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0, 56,  0,  0,  0,  0,  0, 57, 43,  0, 58,
     0,  0,  0, 59,  0, 60, 61,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0, 62, 63,  0, 64,  0,  0,  0,  0,  0,  0,  0,  0,
    65, 66, 67, 68, 69, 70, 71,  0,  0, 72,  0, 73, 74, 75, 76,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0, 77, 78,  0,  0,  0,  0,  0,  0,  0,  0, 79,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0, 80,  0,  0,  0,  0,  0,  0,
     0,  0, 81, 82, 83,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0, 84, 85,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0, 86,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
    87,  0, 88,  2,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
};

static RE_UINT8 re_joining_type_stage_3[] = {
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   1,   0,   0,   0,   0,   0,
      2,   2,   2,   2,   2,   2,   2,   0,   3,   0,   0,   0,   0,   0,   0,   0,
      0,   4,   2,   5,   6,   0,   0,   0,   0,   7,   8,   9,  10,   2,  11,  12,
     13,  14,  15,  15,  16,  17,  18,  19,  20,  21,  22,   2,  23,  24,  25,  26,
      0,   0,  27,  28,  29,  15,  30,  31,   0,  32,  33,   0,  34,  35,   0,   0,
      0,   0,  36,  37,   0,   0,  38,   2,  39,   0,   0,  40,  41,  42,  43,   0,
     44,   0,   0,  45,  46,   0,  43,   0,  47,   0,   0,  45,  48,  44,   0,  49,
     47,   0,   0,  45,  50,   0,  43,   0,  44,   0,   0,  51,  46,  52,  43,   0,
     53,   0,   0,   0,  54,   0,   0,   0,  28,   0,   0,  55,  56,  57,  43,   0,
     44,   0,   0,  51,  58,   0,  43,   0,  44,   0,   0,   0,  46,   0,  43,   0,
      0,   0,   0,   0,  59,  60,   0,   0,   0,   0,   0,  61,  62,   0,   0,   0,
      0,   0,   0,  63,  64,   0,   0,   0,   0,  65,   0,  66,   0,   0,   0,  67,
     68,  69,   2,  70,  52,   0,   0,   0,   0,   0,  71,  72,   0,  73,  28,  74,
     75,   1,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  71,   0,   0,
      0,  76,   0,  76,   0,  43,   0,  43,   0,   0,   0,  77,  78,  79,   0,   0,
     80,   0,  15,  15,  15,  15,  15,  81,  82,  15,  83,   0,   0,   0,   0,   0,
      0,   0,  84,  85,   0,   0,   0,   0,   0,  86,   0,   0,   0,  87,  88,  89,
      0,   0,   0,  90,   0,   0,   0,   0,  91,   0,   0,  92,  53,   0,  93,  91,
     94,   0,  95,   0,   0,   0,  96,  94,   0,   0,  97,  98,   0,   0,   0,   0,
      0,   0,   0,   0,   0,  99, 100, 101,   0,   0,   0,   0,   2,   2,   2, 102,
    103,   0, 104,   0,   0,   0, 105,   0,   0,   0,   0,   0,   0,   2,   2,  28,
      0,   0,   0,   0,   0,   0,  20,  94,   0,   0,   0,   0,   0,   0,   0,  20,
      0,   0,   0,   0,   0,   0,   2,   2,   0,   0, 106,   0,   0,   0,   0,   0,
      0, 107,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  20, 108,
      0,  55,   0,   0,   0,   0,   0,  94, 109,   0,  57,   0,  15,  15,  15, 110,
      0,   0,   0,   0, 111,   0,   2,  94,   0,   0, 112,   0, 113,  94,   0,   0,
     39,   0,   0, 114,   0,   0, 115,   0,   0,   0, 116, 117, 118,   0,   0,  45,
      0,   0,   0, 119,  44,   0, 120,  52,   0,   0,   0,   0,   0,   0, 121,   0,
      0, 122,   0,   0,   0,   0,   0,   0,   2,   0,   2,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0, 123,   0,   0,   0,   0,   0,   0,   0,   1,
      0,   0,   0,   0,   0,   0,  28,   0,   0,   0,   0,   0,   0,   0,   0, 124,
    125,   0,   0, 126,   0,   0,   0,   0,   0,   0,   0,   0, 127, 128, 129,   0,
    130, 131, 132,   0,   0,   0,   0,   0,  44,   0,   0, 133, 134,   0,   0,  20,
     94,   0,   0, 135,   0,   0,   0,   0,  39,   0, 136, 137,   0,   0,   0, 138,
     94,   0,   0, 139, 140,   0,   0,   0,   0,   0,  20, 141,   0,   0,   0,   0,
      0,   0,   0,   0,   0,  20, 142,   0,  94,   0,   0,  45,  28,   0, 143, 137,
      0,   0,   0, 144, 145,   0,   0,   0,   0,   0,   0, 146,  28, 120,   0,   0,
      0,   0,   0, 147,  28,   0,   0,   0,   0,   0, 148, 149,   0,   0,   0,   0,
      0,  71, 150,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 137,
      0,   0,   0, 134,   0,   0,   0,   0,  20,  39,   0,   0,   0,   0,   0,   0,
      0, 151,  91,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 152,  38,
    153,   0, 106,   0,   0,   0,   0,   0,   0,   0,   0,   0,  76,   0,   0,   0,
      2,   2,   2, 154,   2,   2,  70, 115, 111,  93,   4,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0, 134,   0,   0,  44,   0,   2,   2,   2,   2,   2,   2,
      2,   2,   2,   2,   2,   2,   2,   2,
};

static RE_UINT8 re_joining_type_stage_4[] = {
     0,  0,  0,  0,  0,  0,  0,  1,  2,  2,  2,  2,  3,  2,  4,  0,
     5,  2,  2,  2,  2,  2,  2,  6,  7,  6,  0,  0,  2,  2,  8,  9,
    10, 11, 12, 13, 14, 15, 15, 15, 16, 15, 17,  2,  0,  0,  0, 18,
    19, 20, 15, 15, 15, 15, 21, 21, 21, 21, 22, 15, 15, 15, 15, 15,
    23, 21, 21, 24, 25, 26,  2, 27,  2, 27, 28, 29,  0,  0, 18, 30,
     0,  0,  0,  3, 31, 32, 22, 33, 15, 15, 34, 23,  2,  2,  8, 35,
    15, 15, 32, 15, 15, 15, 13, 36, 24, 36, 22, 15,  0, 37,  2,  2,
     9,  0,  0,  0,  0,  0, 18, 15, 15, 15, 38,  2,  2,  0, 39,  0,
     0, 37,  6,  2,  2,  5,  5,  4, 36, 25, 12, 15, 15, 40,  5,  0,
    15, 15, 25, 41, 42, 43,  0,  0,  3,  2,  2,  2,  8,  0,  0,  0,
     0,  0, 44,  9,  5,  2,  9,  1,  5,  2,  0,  0, 37,  0,  0,  0,
     1,  0,  0,  0,  0,  0,  0,  9,  5,  9,  0,  1,  7,  0,  0,  0,
     7,  3, 27,  4,  4,  1,  0,  0,  5,  6,  9,  1,  0,  0,  0, 27,
     0, 44,  0,  0, 44,  0,  0,  0,  9,  0,  0,  1,  0,  0,  0, 37,
     9, 37, 28,  4,  0,  7,  0,  0,  0, 44,  0,  4,  0,  0, 44,  0,
    37, 45,  0,  0,  1,  2,  8,  0,  0,  3,  2,  8,  1,  2,  6,  9,
     0,  0,  2,  4,  0,  0,  4,  0,  0, 46,  1,  0,  5,  2,  2,  8,
     2, 28,  0,  5,  2,  2,  5,  2,  2,  2,  2,  9,  0,  0,  0,  5,
    28,  2,  7,  7,  0,  0,  4, 37,  5,  9,  0,  0, 44,  7,  0,  1,
    37,  9,  0,  0,  0,  6,  2,  4,  0, 44,  5,  2,  2,  0,  0,  1,
     0, 47, 48,  4, 15, 15,  0,  0,  0, 47, 15, 15, 15, 15, 49,  0,
     8,  3,  9,  0, 44,  0,  5,  0,  0,  3, 27,  0,  0, 44,  2,  8,
    45,  5,  2,  9,  3,  2,  2, 27,  2,  2,  2,  8,  2,  0,  0,  0,
     0, 28,  8,  9,  0,  0,  3,  2,  4,  0,  0,  0, 37,  4,  6,  4,
     0, 44,  4, 46,  0,  0,  0,  2,  2, 37,  0,  0,  8,  2,  2,  2,
    28,  2,  9,  1,  0,  9,  4,  0,  2,  4,  0,  2,  0,  0,  3, 50,
     0,  0, 37,  8,  2,  9, 37,  2,  0,  0, 37,  4,  0,  0,  7,  0,
     8,  2,  2,  4, 44, 44,  3,  0, 51,  0,  0,  0,  0,  9,  0,  0,
     0, 37,  2,  4,  0,  3,  2,  2,  3, 37,  4,  9,  0,  1,  0,  0,
     0,  0,  5,  8,  7,  7,  0,  0,  3,  0,  0,  9, 28, 27,  9, 37,
     0,  0,  0,  4,  0,  1,  9,  1,  0,  0,  0, 44,  0,  0,  5,  0,
     0, 37,  8,  0,  5,  7,  0,  2,  0,  0,  8,  3, 15, 52, 53, 54,
    14, 55, 15, 12, 56, 57, 47, 13, 24, 22, 12, 58, 56,  0,  0,  0,
     0,  0, 20, 59,  0,  0,  2,  2,  2,  8,  0,  0,  3,  8,  7,  1,
     0,  3,  2,  5,  2,  9,  0,  0,  3,  0,  0,  0,  0, 37,  2,  8,
     0,  0, 37,  9,  4, 28,  0,  0,  3,  2,  8,  0,  0, 37,  2,  9,
     3,  2, 45,  3, 28,  0,  0,  0, 37,  4,  0,  6,  3,  2,  8, 46,
     0,  0,  3,  1,  2,  6,  0,  0, 37,  6,  2,  0,  0,  0,  0,  7,
     0,  3,  4,  0,  8,  5,  2,  0,  2,  8,  3,  2,
};

static RE_UINT8 re_joining_type_stage_5[] = {
    0, 0, 0, 0, 0, 5, 0, 0, 5, 5, 5, 5, 0, 0, 0, 5,
    5, 5, 0, 0, 0, 5, 5, 5, 5, 5, 0, 5, 0, 5, 5, 0,
    5, 5, 5, 0, 5, 0, 0, 0, 2, 0, 3, 3, 3, 3, 2, 3,
    2, 3, 2, 2, 2, 2, 2, 3, 3, 3, 3, 2, 2, 2, 2, 2,
    1, 2, 2, 2, 3, 2, 2, 5, 0, 0, 2, 2, 5, 3, 3, 3,
    0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 2, 3, 2, 2, 3,
    2, 3, 2, 3, 2, 2, 3, 3, 0, 3, 5, 5, 5, 0, 0, 5,
    5, 0, 5, 5, 5, 5, 3, 3, 2, 0, 0, 2, 3, 5, 2, 2,
    2, 3, 3, 3, 2, 2, 3, 2, 3, 2, 3, 2, 0, 3, 2, 2,
    3, 2, 2, 2, 0, 0, 5, 5, 2, 2, 2, 5, 0, 0, 1, 0,
    3, 2, 0, 0, 3, 0, 3, 2, 2, 3, 3, 2, 2, 0, 0, 0,
    0, 0, 5, 0, 5, 0, 5, 0, 0, 5, 0, 5, 0, 0, 0, 2,
    0, 0, 1, 5, 2, 5, 2, 0, 0, 1, 5, 5, 2, 2, 4, 0,
    2, 3, 0, 3, 0, 3, 3, 0, 0, 4, 3, 3, 2, 2, 2, 4,
    2, 3, 0, 0, 3, 5, 5, 0, 3, 2, 3, 3, 3, 2, 2, 0,
};

/* Joining_Type: 2292 bytes. */

RE_UINT32 re_get_joining_type(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 12;
    code = ch ^ (f << 12);
    pos = (RE_UINT32)re_joining_type_stage_1[f] << 5;
    f = code >> 7;
    code ^= f << 7;
    pos = (RE_UINT32)re_joining_type_stage_2[pos + f] << 3;
    f = code >> 4;
    code ^= f << 4;
    pos = (RE_UINT32)re_joining_type_stage_3[pos + f] << 2;
    f = code >> 2;
    code ^= f << 2;
    pos = (RE_UINT32)re_joining_type_stage_4[pos + f] << 2;
    value = re_joining_type_stage_5[pos + code];

    return value;
}

/* Line_Break. */

static RE_UINT8 re_line_break_stage_1[] = {
     0,  1,  2,  3,  4,  5,  5,  5,  5,  5,  6,  7,  8,  9, 10, 11,
    12, 13, 14, 15, 16, 10, 17, 10, 10, 10, 10, 18, 10, 19, 20, 21,
     5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5, 22,
     5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5,  5, 22,
    10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
    10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
    10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
    10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
    10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
    10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
    10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
    10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
    10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
    10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
    23, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
    10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
    10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
};

static RE_UINT8 re_line_break_stage_2[] = {
      0,   1,   2,   2,   2,   3,   4,   5,   2,   6,   7,   8,   9,  10,  11,  12,
     13,  14,  15,  16,  17,  18,  19,  20,  21,  22,  23,  24,  25,  26,  27,  28,
     29,  30,  31,  32,  33,  34,  35,  36,  37,   2,   2,   2,   2,  38,  39,  40,
     41,  42,  43,  44,  45,  46,  47,  48,  49,  50,   2,  51,   2,   2,  52,  53,
     54,  55,  56,  57,  58,  59,  60,  61,  62,  63,  64,  65,  66,  67,  68,  69,
      2,   2,   2,  70,   2,   2,  71,  72,  73,  74,  75,  76,  77,  78,  79,  80,
     81,  82,  83,  84,  85,  86,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,
     79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,
     79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,
     79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  87,  79,  79,  79,  79,
     79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,
     79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,
     88,  79,  79,  79,  79,  79,  79,  79,  79,  89,   2,   2,  90,  91,   2,  92,
     93,  94,  95,  96,  97,  98,  99, 100, 101, 102, 103, 104, 105, 106, 107, 101,
    102, 103, 104, 105, 106, 107, 101, 102, 103, 104, 105, 106, 107, 101, 102, 103,
    104, 105, 106, 107, 101, 102, 103, 104, 105, 106, 107, 101, 102, 103, 104, 105,
    106, 107, 101, 102, 103, 104, 105, 106, 107, 101, 102, 103, 104, 105, 106, 107,
    101, 102, 103, 104, 105, 106, 107, 101, 102, 103, 104, 105, 106, 107, 101, 102,
    103, 104, 105, 106, 107, 101, 102, 103, 104, 105, 106, 107, 101, 102, 103, 108,
    109, 109, 109, 109, 109, 109, 109, 109, 109, 109, 109, 109, 109, 109, 109, 109,
    110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110,
    110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110,
    110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110,
    110, 110,  79,  79,  79,  79, 111, 112,   2,   2, 113, 114, 115, 116, 117, 118,
    119, 120, 121, 122, 110, 123, 124, 125,   2, 126, 127, 110,   2,   2, 128, 110,
    129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 110, 110, 139, 110, 110, 110,
    140, 141, 142, 143, 144, 145, 146, 110, 110, 147, 110, 148, 149, 150, 151, 110,
    110, 152, 110, 110, 110, 153, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110,
      2,   2,   2,   2,   2,   2,   2, 154, 155,   2, 156, 110, 110, 110, 110, 110,
    110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110,
      2,   2,   2,   2, 157, 158, 159,   2, 160, 110, 110, 110, 110, 110, 110, 110,
    110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110,
    110, 110, 110, 110, 110, 110, 110, 110,   2,   2,   2, 161, 162, 110, 110, 110,
    110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110,
    110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110,
      2,   2,   2,   2, 163, 164, 165, 166, 110, 110, 110, 110, 110, 110, 167, 168,
    169, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110,
    110, 110, 110, 110, 110, 110, 110, 110, 170, 171, 110, 110, 110, 110, 110, 110,
      2, 172, 173, 174, 175, 110, 176, 110, 177, 178, 179,   2,   2, 180,   2, 181,
      2,   2,   2,   2, 182, 183, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110,
    110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110,
      2, 184, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 185, 186, 110, 110,
    187, 188, 189, 190, 191, 110,  79, 192,  79, 193, 194, 195, 196, 197, 198, 199,
    200, 201, 202, 203, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110,
     79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,
     79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79,  79, 204,
    205, 110, 206, 207, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110,
    110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110,
};

static RE_UINT16 re_line_break_stage_3[] = {
      0,   1,   2,   3,   4,   5,   4,   6,   7,   1,   8,   9,   4,  10,   4,  10,
      4,   4,   4,   4,   4,   4,   4,   4,   4,   4,   4,   4,  11,  12,   4,   4,
      1,   1,   1,   1,  13,  14,  15,  16,  17,   4,  18,   4,   4,   4,   4,   4,
     19,   4,   4,   4,   4,   4,   4,   4,   4,   4,   4,  20,   4,  21,  20,   4,
     22,  23,   1,  24,  25,  26,  27,  28,  29,  30,   4,   4,  31,   1,  32,  33,
      4,   4,   4,   4,   4,  34,  35,  36,  37,  38,   4,   1,  39,   4,   4,   4,
      4,   4,  40,  41,  36,   4,  31,  42,   4,  43,  44,  45,   4,  46,  47,  47,
     47,  47,   4,  48,  47,  47,  49,   1,  50,   4,   4,  51,   1,  52,  53,   4,
     54,  55,  56,  57,  58,  59,  60,  61,  62,  55,  56,  63,  64,  65,  66,  67,
     68,  18,  56,  69,  70,  71,  60,  72,  73,  55,  56,  69,  74,  75,  60,  76,
     77,  78,  79,  80,  81,  82,  66,  83,  84,  85,  56,  86,  87,  88,  60,  89,
     90,  85,  56,  91,  87,  92,  60,  93,  90,  85,   4,  94,  95,  96,  60,  97,
     98,  99,   4, 100, 101, 102,  66, 103, 104, 105, 105, 106, 107, 108,  47,  47,
    109, 110, 111, 112, 113, 114,  47,  47, 115, 116,  36, 117, 118,   4, 119, 120,
    121, 122,   1, 123, 124, 125,  47,  47, 105, 105, 105, 105, 126, 105, 105, 105,
    105, 127,   4,   4, 128,   4,   4,   4, 129, 129, 129, 129, 129, 129, 130, 130,
    130, 130, 131, 132, 132, 132, 132, 132,   4,   4,   4,   4, 133, 134,   4,   4,
    133,   4,   4, 135, 136, 137,   4,   4,   4, 136,   4,   4,   4, 138, 139, 119,
      4, 140,   4,   4,   4,   4,   4, 141, 142,   4,   4,   4,   4,   4,   4,   4,
    142, 143,   4,   4,   4,   4, 144, 145, 146, 147,   4, 148,   4, 149, 146, 150,
    105, 105, 105, 105, 105, 151, 152, 140, 153, 152,   4,   4,   4,   4,   4,  76,
      4,   4, 154,   4,   4,   4,   4, 155,   4,  45, 156, 156, 157, 105, 158, 159,
    105, 105, 160, 105, 161, 162,   4,   4,   4, 163, 105, 105, 105, 164, 105, 165,
    152, 152, 158, 166,  47,  47,  47,  47, 167,   4,   4, 168, 169, 170, 171, 172,
    173,   4, 174,  36,   4,   4,  40, 175,   4,   4, 168, 176, 177,  36,   4, 178,
     47,  47,  47,  47,  76, 179, 180, 181,   4,   4,   4,   4,   1,   1,   1, 182,
      4, 141,   4,   4, 141, 183,   4, 184,   4,   4,   4, 185, 185, 186,   4, 187,
    188, 189, 190, 191, 192, 193, 194, 195, 196, 119, 197, 198, 199,   1,   1, 200,
    201, 202, 203,   4,   4, 204, 205, 206, 207, 206,   4,   4,   4, 208,   4,   4,
    209, 210, 211, 212, 213, 214, 215,   4, 216, 217, 218, 219,   4,   4, 220,   4,
    221, 222, 223,   4,   4,   4,   4,   4,   4,   4,   4,   4,   4,   4,   4, 224,
      4,   4, 225,  47, 226,  47, 227, 227, 227, 227, 227, 227, 227, 227, 227, 228,
    227, 227, 227, 227, 205, 227, 227, 229, 227, 230, 231, 232, 233, 234, 235,   4,
    236, 237,   4, 238, 239,   4, 240, 241,   4, 242,   4, 243, 244, 245, 246, 247,
    248,   4,   4,   4,   4, 249, 250, 251, 227, 252,   4,   4, 253,   4, 254,   4,
    255, 256,   4,   4,   4, 221,   4, 257,   4,   4,   4,   4,   4, 258,   4, 259,
      4, 260,   4, 261,  56, 262, 263,  47,   4,   4,  45,   4,   4,  45,   4,   4,
      4,   4,   4,   4,   4,   4, 264, 265,   4,   4, 128,   4,   4,   4, 266, 267,
      4, 225, 268, 268, 268, 268,   1,   1, 269, 270, 271, 272, 273,  47,  47,  47,
    274, 275, 274, 274, 274, 274, 274, 276, 274, 274, 274, 274, 274, 274, 274, 274,
    274, 274, 274, 274, 274, 277,  47, 278, 279, 280, 281, 282, 283, 274, 284, 274,
    285, 286, 287, 274, 284, 274, 285, 288, 289, 274, 290, 291, 274, 274, 274, 274,
    292, 274, 274, 293, 274, 274, 276, 294, 274, 292, 274, 274, 295, 274, 274, 274,
    274, 274, 274, 274, 274, 274, 274, 292, 274, 274, 274, 274,   4,   4,   4,   4,
    274, 296, 274, 274, 274, 274, 274, 274, 297, 274, 274, 274, 298,   4,   4, 178,
    299,   4, 300,  47,   4,   4, 264, 301,   4, 302,   4,   4,   4,   4,   4, 303,
      4,   4, 184,  76,  47,  47,  47, 304, 305,   4, 306, 307,   4,   4,   4, 308,
    309,   4,   4, 168, 310, 152,   1, 311,  36,   4, 312,   4, 313, 314, 129, 315,
     50,   4,   4, 316, 317, 318, 105, 319,   4,   4, 320, 321, 322, 323, 105, 105,
    105, 105, 105, 105, 324, 325,  31, 326, 327, 328, 268,   4,   4,   4, 155,   4,
      4,   4,   4,   4,   4,   4, 329, 152, 330, 331, 332, 333, 332, 334, 332, 330,
    331, 332, 333, 332, 334, 332, 330, 331, 332, 333, 332, 334, 332, 330, 331, 332,
    333, 332, 334, 332, 330, 331, 332, 333, 332, 334, 332, 330, 331, 332, 333, 332,
    334, 332, 330, 331, 332, 333, 332, 334, 332, 330, 331, 332, 333, 332, 334, 332,
    333, 332, 335, 130, 336, 132, 132, 337, 338, 338, 338, 338, 338, 338, 338, 338,
     47,  47,  47,  47,  47,  47,  47,  47, 225, 339, 340, 341, 342,   4,   4,   4,
      4,   4,   4,   4, 262, 343,   4,   4,   4,   4,   4, 344,  47,   4,   4,   4,
      4, 345,   4,   4,  76,  47,  47, 346,   1, 347,   1, 348, 349, 350, 351, 185,
      4,   4,   4,   4,   4,   4,   4, 352, 353, 354, 274, 355, 274, 356, 357, 358,
      4, 359,   4,  45, 360, 361, 362, 363, 364,   4, 137, 365, 184, 184,  47,  47,
      4,   4,   4,   4,   4,   4,   4, 226, 366,   4,   4, 367,   4,   4,   4,   4,
    119, 368,  71,  47,  47,   4,   4, 369,   4, 119,   4,   4,   4,  71,  33, 368,
      4,   4, 370,   4, 226,   4,   4, 371,   4, 372,   4,   4, 373, 374,  47,  47,
      4, 184, 152,  47,  47,  47,  47,  47,   4,   4,  76,   4,   4,   4, 375,  47,
      4,   4,   4, 225,   4, 155,  76,  47, 376,   4,   4, 377,   4, 378,   4,   4,
      4,  45, 304,  47,  47,  47,   4, 379,   4, 380,   4, 381,  47,  47,  47,  47,
      4,   4,   4, 382,   4, 345,   4,   4, 383, 384,   4, 385,  76, 386,   4,   4,
      4,   4,  47,  47,   4,   4, 387, 388,   4,   4,   4, 389,   4, 260,   4, 390,
      4, 391, 392,  47,  47,  47,  47,  47,   4,   4,   4,   4, 145,  47,  47,  47,
      4,   4,   4, 393,   4,   4,   4, 394,  47,  47,  47,  47,  47,  47,   4,  45,
    173,   4,   4, 395, 396, 345, 397, 398, 173,   4,   4, 399, 400,   4, 145, 152,
    173,   4, 313, 401, 402,   4,   4, 403, 173,   4,   4, 316, 404, 405,  20,  48,
      4,  18, 406, 407,  47,  47,  47,  47, 408,  37, 409,   4,   4, 264, 410, 152,
    411,  55,  56,  69,  74, 412, 413, 414,   4,   4,   4,   1, 415, 152,  47,  47,
      4,   4, 264, 416, 417, 418,  47,  47,   4,   4,   4,   1, 419, 152,  47,  47,
      4,   4,  31, 420, 152,  47,  47,  47, 105, 421, 160, 422,  47,  47,  47,  47,
     47,  47,   4,   4,   4,   4,  36, 423,  47,  47,  47,  47,   4,   4,   4, 145,
      4, 140,  47,  47,  47,  47,  47,  47,   4,   4,   4,   4,   4,   4,  45, 424,
      4,   4,   4,   4, 370,  47,  47,  47,   4,   4,   4,   4,   4, 425,   4,   4,
    426,   4,   4,   4,   4,   4,   4,   4,   4,   4,   4,   4,   4,   4,   4, 427,
      4,   4,  45,  47,  47,  47,  47,  47,   4,   4,   4,   4, 428,   4,   4,   4,
      4,   4,   4,   4, 225,  47,  47,  47,   4,   4,   4, 145,   4,  45, 429,  47,
     47,  47,  47,  47,  47,   4, 184, 430,   4,   4,   4, 431, 432, 433,  18, 434,
      4,  47,  47,  47,  47,  47,  47,  47,   4,   4,   4,   4,  48, 435,   1, 166,
    398, 173,  47,  47,  47,  47,  47,  47, 436,  47,  47,  47,  47,  47,  47,  47,
      4,   4,   4,   4,   4,   4, 226, 119, 145, 437, 438,  47,  47,  47,  47,  47,
      4,   4,   4,   4,   4,   4,   4, 155,   4,   4,  21,   4,   4,   4, 439,   1,
    440,   4, 441,   4,   4,   4, 145,  47,   4,   4,   4,   4, 442,  47,  47,  47,
      4,   4,   4,   4,   4, 225,   4, 262,   4,   4,   4,   4,   4, 185,   4,   4,
      4, 146, 443, 444, 445,   4,   4,   4, 446, 447,   4, 448, 449,  85,   4,   4,
      4,   4, 260,   4,   4,   4,   4,   4,   4,   4,   4,   4, 450, 451, 451, 451,
      1,   1,   1, 452,   1,   1, 453, 454, 455, 456,  23,  47,  47,  47,  47,  47,
      4,   4,   4,   4, 457, 321,  47,  47, 445,   4, 458, 459, 460, 461, 462, 463,
    464, 368, 465, 368,  47,  47,  47, 262, 274, 274, 278, 274, 274, 274, 274, 274,
    274, 276, 292, 291, 291, 291, 274, 277, 466, 227, 467, 227, 227, 227, 468, 227,
    227, 469,  47,  47,  47,  47, 470, 471, 472, 274, 274, 293, 473, 436,  47,  47,
    274, 474, 274, 475, 274, 274, 274, 476, 274, 274, 477, 478, 274, 274, 274, 274,
    479, 480, 481, 482, 483, 274, 274, 275, 274, 274, 484, 274, 274, 485, 274, 486,
    274, 274, 274, 274, 274,   4,   4, 487, 274, 274, 274, 274, 274, 488, 297, 276,
      4,   4,   4,   4,   4,   4,   4, 370,   4,   4,   4,   4,   4,  48,  47,  47,
    368,   4,   4,   4,  76, 140,   4,   4,  76,   4, 184,  47,  47,  47,  47,  47,
     47, 473,  47,  47,  47,  47,  47,  47, 489,  47,  47,  47, 488,  47,  47,  47,
    274, 274, 274, 274, 274, 274, 274, 290, 490,  47,   1,   1,   1,   1,   1,   1,
      1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,  47,
};

static RE_UINT8 re_line_break_stage_4[] = {
      0,   0,   0,   0,   1,   2,   3,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      4,   5,   6,   7,   8,   9,  10,  11,  12,  12,  12,  12,  12,  13,  14,  15,
     14,  14,  14,  14,  14,  14,  14,  14,  14,  14,  14,  14,  14,  16,  17,  14,
     14,  14,  14,  14,  14,  16,  18,  19,   0,   0,  20,   0,   0,   0,   0,   0,
     21,  22,  23,  24,  25,  26,  27,  14,  22,  28,  29,  28,  28,  26,  28,  30,
     14,  14,  14,  24,  14,  14,  14,  14,  14,  14,  14,  24,  31,  28,  31,  14,
     25,  14,  14,  14,  28,  28,  24,  32,   0,   0,   0,   0,   0,   0,   0,  33,
      0,   0,   0,   0,   0,   0,  34,  34,  34,  35,   0,   0,   0,   0,   0,   0,
     14,  14,  14,  14,  36,  14,  14,  37,  36,  36,  14,  14,  14,  38,  38,  14,
     14,  39,  14,  14,  14,  14,  14,  14,  14,  19,   0,   0,   0,  14,  14,  14,
     39,  14,  14,  14,  14,  14,  14,  14,  14,  14,  14,  38,  39,  14,  14,  14,
     14,  14,  14,  14,  40,  41,  39,   9,  42,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,  43,  19,  44,   0,  45,  36,  36,  36,  36,
     46,  46,  46,  46,  46,  46,  46,  46,  46,  46,  46,  46,  46,  47,  36,  36,
     46,  48,  38,  36,  36,  36,  36,  36,  14,  14,  14,  14,  49,  50,  13,  14,
      0,   0,   0,   0,   0,  51,  52,  53,  14,  14,  14,  14,  14,  19,   0,   0,
     12,  12,  12,  12,  12,  54,  55,  14,  44,  14,  14,  14,  14,  14,  14,  14,
     14,  14,  56,   0,   0,   0,  44,  19,   0,   0,  44,  19,  44,   0,   0,  14,
     12,  12,  12,  12,  12,  14,  14,  14,  14,  14,  14,  14,  14,  14,  14,  39,
     19,  14,  14,  14,  14,  14,  14,  14,   0,   0,   0,   0,   0,  52,  39,  14,
     14,  14,  14,   0,   0,   0,   0,   0,  44,  36,  36,  36,  36,  36,  36,  36,
      0,   0,  14,  14,  57,  38,  36,  36,  14,  14,  14,   0,   0,  19,   0,   0,
      0,   0,  19,   0,  19,   0,   0,  36,  14,  14,  14,  14,  14,  14,  14,  38,
     14,  14,  14,  14,  19,   0,  36,  38,  36,  36,  36,  36,  36,  36,  36,  36,
     14,  14,  38,  36,  36,  36,  36,  36,  36,  42,   0,   0,   0,   0,   0,   0,
      0,   0,  14,  14,  14,  14,  14,  14,  14,  14,  14,  14,  14,   0,  44,   0,
     19,   0,   0,   0,  14,  14,  14,  14,  14,   0,  58,  12,  12,  12,  12,  12,
     19,   0,  39,  14,  14,  14,  38,  39,  38,  39,  14,  14,  14,  14,  14,  14,
     14,  14,  14,  14,  38,  14,  14,  14,  38,  38,  36,  14,  14,  36,  44,   0,
      0,   0,  52,  42,  52,  42,   0,  38,  36,  36,  36,  42,  36,  36,  14,  39,
     14,   0,  36,  12,  12,  12,  12,  12,  14,  50,  14,  14,  49,   9,  36,  36,
     42,   0,  39,  14,  14,  38,  36,  39,  38,  14,  39,  38,  14,  36,  52,   0,
      0,  52,  36,  42,  52,  42,   0,  36,  42,  36,  36,  36,  39,  14,  38,  38,
     36,  36,  36,  12,  12,  12,  12,  12,   0,  14,  19,  36,  36,  36,  36,  36,
     42,   0,  39,  14,  14,  14,  14,  39,  38,  14,  39,  14,  14,  36,  44,   0,
      0,   0,   0,  42,   0,  42,   0,  36,  38,  36,  36,  36,  36,  36,  36,  36,
      9,  36,  36,  36,  39,  36,  36,  36,  42,   0,  39,  14,  14,  14,  38,  39,
      0,   0,  52,  42,  52,  42,   0,  36,  36,  36,  36,   0,  36,  36,  14,  39,
     14,  14,  14,  14,  36,  36,  36,  36,  36,  44,  39,  14,  14,  38,  36,  14,
     38,  14,  14,  36,  39,  38,  38,  14,  36,  39,  38,  36,  14,  38,  36,  14,
     14,  14,  14,  14,  14,  36,  36,   0,   0,  52,  36,   0,  52,   0,   0,  36,
     38,  36,  36,  42,  36,  36,  36,  36,  14,  14,  14,  14,   9,  38,  36,  36,
      0,   0,  39,  14,  14,  14,  38,  14,  38,  14,  14,  14,  14,  14,  14,  14,
     14,  14,  14,  14,  14,  36,  39,   0,   0,   0,  52,   0,  52,   0,   0,  36,
     36,  36,  42,  52,  14,  38,  36,  36,  36,  36,  36,  36,  14,  14,  14,  14,
     42,   0,  39,  14,  14,  14,  38,  14,  14,  14,  39,  14,  14,  36,  44,   0,
     36,  36,  42,  52,  36,  36,  36,  38,  39,  38,  36,  36,  36,  36,  36,  36,
     14,  14,  14,  14,  14,  38,  39,   0,   0,   0,  52,   0,  52,   0,   0,  38,
     36,  36,  36,  42,  36,  36,  36,  39,  14,  14,  14,  36,  59,  14,  14,  14,
     36,   0,  39,  14,  14,  14,  14,  14,  14,  14,  14,  38,  36,  14,  14,  14,
     14,  39,  14,  14,  14,  14,  39,  36,  14,  14,  14,  38,  36,  52,  36,  42,
      0,   0,  52,  52,   0,   0,   0,   0,  36,   0,  38,  36,  36,  36,  36,  36,
     60,  61,  61,  61,  61,  61,  61,  61,  61,  61,  61,  61,  61,  61,  61,  61,
     61,  61,  61,  61,  61,  62,  36,  63,  61,  61,  61,  61,  61,  61,  61,  64,
     12,  12,  12,  12,  12,  58,  36,  36,  60,  62,  62,  60,  62,  62,  60,  36,
     36,  36,  61,  61,  60,  61,  61,  61,  60,  61,  60,  60,  36,  61,  60,  61,
     61,  61,  61,  61,  61,  60,  61,  36,  61,  61,  62,  62,  61,  61,  61,  36,
     12,  12,  12,  12,  12,  36,  61,  61,  32,  65,  29,  65,  66,  67,  68,  53,
     53,  69,  56,  14,   0,  14,  14,  14,  14,  14,  43,  19,  19,  70,  70,   0,
     14,  14,  14,  14,  39,  14,  14,  14,  14,  14,  14,  14,  14,  14,  38,  36,
     42,   0,   0,   0,   0,   0,   0,   1,   0,   0,   1,   0,  14,  14,  19,   0,
      0,   0,   0,   0,  42,   0,   0,   0,   0,   0,   0,   0,   0,   0,  52,  58,
     14,  14,  14,  44,  14,  14,  38,  14,  65,  71,  14,  14,  72,  73,  36,  36,
     12,  12,  12,  12,  12,  58,  14,  14,  12,  12,  12,  12,  12,  61,  61,  61,
     14,  14,  14,  39,  36,  36,  39,  36,  74,  74,  74,  74,  74,  74,  74,  74,
     75,  75,  75,  75,  75,  75,  75,  75,  75,  75,  75,  75,  76,  76,  76,  76,
     76,  76,  76,  76,  76,  76,  76,  76,  14,  14,  14,  14,  38,  14,  14,  36,
     14,  14,  14,  38,  38,  14,  14,  36,  38,  14,  14,  36,  14,  14,  14,  38,
     38,  14,  14,  36,  14,  14,  14,  14,  14,  14,  14,  38,  14,  14,  14,  14,
     14,  14,  14,  14,  14,  38,  42,   0,  27,  14,  14,  14,  14,  14,  14,  14,
     14,  14,  14,  14,  14,  36,  36,  36,  14,  14,  14,  36,  14,  14,  14,  36,
     77,  14,  14,  14,  14,  14,  14,  14,  14,  14,  14,  14,  14,  16,  78,  36,
     14,  14,  14,  14,  14,  27,  58,  14,  14,  14,  14,  14,  38,  36,  36,  36,
     14,  14,  14,  14,  14,  14,  38,  14,  14,   0,  52,  36,  36,  36,  36,  36,
     14,   0,   1,  41,  36,  36,  36,  36,  14,   0,  36,  36,  36,  36,  36,  36,
     38,   0,  36,  36,  36,  36,  36,  36,  61,  61,  58,  79,  77,  80,  61,  36,
     12,  12,  12,  12,  12,  36,  36,  36,  14,  53,  58,  29,  53,  19,   0,  73,
     14,  14,  14,  14,  19,  38,  36,  36,  14,  14,  14,  36,  36,  36,  36,  36,
      0,   0,   0,   0,   0,   0,  36,  36,  38,  36,  53,  12,  12,  12,  12,  12,
     61,  61,  61,  61,  61,  61,  61,  36,  61,  61,  62,  36,  36,  36,  36,  36,
     61,  61,  61,  61,  61,  61,  36,  36,  61,  61,  61,  61,  61,  36,  36,  36,
     12,  12,  12,  12,  12,  62,  36,  61,  14,  14,  14,  19,   0,   0,  36,  14,
     61,  61,  61,  61,  61,  61,  61,  62,  61,  61,  61,  61,  61,  61,  62,  42,
      0,   0,   0,   0,   0,   0,   0,  52,   0,   0,  44,  14,  14,  14,  14,  14,
     14,  14,   0,   0,   0,   0,   0,   0,   0,   0,  44,  14,  14,  14,  36,  36,
     12,  12,  12,  12,  12,  58,  27,  58,  77,  14,  14,  14,  14,  19,   0,   0,
      0,   0,  14,  14,  14,  14,  38,  36,   0,  44,  14,  14,  14,  14,  14,  14,
     19,   0,   0,   0,   0,   0,   0,  14,   0,   0,  36,  36,  36,  36,  14,  14,
      0,   0,   0,   0,  36,  81,  58,  58,  12,  12,  12,  12,  12,  36,  39,  14,
     14,  14,  14,  14,  14,  14,  14,  58,   0,  44,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,  44,  14,  19,  14,  14,   0,  44,  38,   0,  36,  36,  36,
      0,   0,   0,  36,  36,  36,   0,   0,  14,  14,  14,  14,  39,  39,  39,  39,
     14,  14,  14,  14,  14,  14,  14,  36,  14,  14,  38,  14,  14,  14,  14,  14,
     14,  14,  36,  14,  14,  14,  39,  14,  36,  14,  38,  14,  14,  14,  32,  38,
     58,  58,  58,  82,  58,  83,   0,   0,  82,  58,  84,  25,  85,  86,  85,  86,
     28,  14,  87,  88,  89,   0,   0,  33,  50,  50,  50,  50,   7,  90,  91,  14,
     14,  14,  92,  93,  91,  14,  14,  14,  14,  14,  14,  77,  58,  58,  27,  58,
     94,  14,  38,   0,   0,   0,   0,   0,  14,  36,  25,  14,  14,  14,  16,  95,
     24,  28,  25,  14,  14,  14,  16,  78,  23,  23,  23,   6,  23,  23,  23,  23,
     23,  23,  23,  22,  23,   6,  23,  22,  23,  23,  23,  23,  23,  23,  23,  23,
     52,  36,  36,  36,  36,  36,  36,  36,  14,  49,  24,  14,  49,  14,  14,  14,
     14,  24,  14,  96,  14,  14,  14,  14,  24,  25,  14,  14,  14,  24,  14,  14,
     14,  14,  28,  14,  14,  24,  14,  25,  28,  28,  28,  28,  28,  28,  14,  14,
     28,  28,  28,  28,  28,  14,  14,  14,  14,  14,  14,  14,  24,  14,  36,  36,
     14,  25,  25,  14,  14,  14,  14,  14,  25,  28,  14,  24,  25,  24,  14,  24,
     24,  23,  24,  14,  14,  25,  24,  28,  25,  24,  24,  24,  28,  28,  25,  25,
     14,  14,  28,  28,  14,  14,  28,  14,  14,  14,  14,  14,  25,  14,  25,  14,
     14,  25,  14,  14,  14,  14,  14,  14,  28,  14,  28,  28,  14,  28,  14,  28,
     14,  28,  14,  28,  14,  14,  14,  14,  14,  14,  24,  14,  24,  14,  14,  14,
     14,  14,  24,  14,  14,  14,  14,  14,  14,  14,  14,  14,  14,  14,  14,  24,
     14,  14,  14,  14,  14,  14,  14,  97,  14,  14,  14,  14,  70,  70,  14,  14,
     14,  25,  14,  14,  14,  98,  14,  14,  14,  14,  14,  14,  16,  99,  14,  14,
     98,  98,  14,  14,  14,  38,  36,  36,  14,  14,  14,  38,  36,  36,  36,  36,
     14,  14,  14,  14,  14,  38,  36,  36,  28,  28,  28,  28,  28,  28,  28,  28,
     28,  28,  28,  28,  28,  28,  28,  25,  28,  28,  25,  14,  14,  14,  14,  14,
     14,  28,  28,  14,  14,  14,  14,  14,  28,  24,  28,  28,  28,  14,  14,  14,
     14,  28,  14,  28,  14,  14,  28,  14,  28,  14,  14,  28,  25,  24,  14,  28,
     28,  14,  14,  14,  14,  14,  14,  14,  14,  28,  28,  14,  14,  14,  14,  24,
     98,  98,  24,  25,  24,  14,  14,  28,  14,  14,  98,  28, 100,  98,  98,  98,
     14,  14,  14,  14, 101,  98,  14,  14,  25,  25,  14,  14,  14,  14,  14,  14,
     28,  24,  28,  24, 102,  25,  28,  24,  14,  14,  14,  14,  14,  14,  14, 101,
     14,  14,  14,  14,  14,  14,  14,  28,  14,  14,  14,  14,  14,  14, 101,  98,
     98,  98,  98,  98, 102,  28, 103, 101,  98, 103, 102,  28,  98,  28, 102, 103,
     98,  24,  14,  14,  28, 102,  28,  28, 103,  98,  98, 103,  98, 102, 103,  98,
     98,  98, 100,  14,  98,  98,  98,  14,  14,  14,  14,  24,  14,   7,  85,  85,
      5,  53,  14,  14,  70,  70,  70,  70,  70,  70,  70,  28,  28,  28,  28,  28,
     28,  28,  14,  14,  14,  14,  14,  14,  14,  14,  16,  99,  14,  14,  14,  14,
     14,  14,  14,  70,  70,  70,  70,  70,  14,  16, 104, 104, 104, 104, 104, 104,
    104, 104, 104, 104,  99,  14,  14,  14,  14,  14,  14,  14,  14,  14,  70,  14,
     14,  14,  24,  28,  28,  14,  14,  14,  14,  14,  36,  14,  14,  14,  14,  14,
     14,  14,  14,  36,  14,  14,  14,  14,  14,  14,  14,  14,  14,  36,  39,  14,
     14,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  14,  14,
     14,  14,  14,  14,  14,  14,  14,  19,   0,  14,  36,  36, 105,  58,  77, 106,
     14,  14,  14,  14,  36,  36,  36,  39,  41,  36,  36,  36,  36,  36,  36,  42,
     14,  14,  14,  38,  14,  14,  14,  38,  85,  85,  85,  85,  85,  85,  85,  58,
     58,  58,  58,  27, 107,  14,  85,  14,  85,  70,  70,  70,  70,  58,  58,  56,
     58,  27,  77,  14,  14, 108,  58,  77,  58, 109,  36,  36,  36,  36,  36,  36,
     98,  98,  98,  98,  98,  98,  98,  98,  98,  98,  98,  98,  98, 110,  98,  98,
     98,  98,  36,  36,  36,  36,  36,  36,  98,  98,  98,  36,  36,  36,  36,  36,
     98,  98,  98,  98,  98,  98,  36,  36,  18, 111, 112,  98,  70,  70,  70,  70,
     70,  98,  70,  70,  70,  70, 113, 114,  98,  98,  98,  98,  98,   0,   0,   0,
     98,  98, 115,  98,  98, 112, 116,  98, 117, 118, 118, 118, 118,  98,  98,  98,
     98, 118,  98,  98,  98,  98,  98,  98,  98, 118, 118, 118,  98,  98,  98, 119,
     98,  98, 118, 120,  42, 121,  91, 116, 122, 118, 118, 118, 118,  98,  98,  98,
     98,  98, 118, 119,  98, 112, 123, 116,  36,  36, 110,  98,  98,  98,  98,  98,
     98,  98,  98,  98,  98,  98,  98,  36, 110,  98,  98,  98,  98,  98,  98,  98,
     98,  98,  98,  98,  98,  98,  98, 124,  98,  98,  98,  98,  98, 124,  36,  36,
    125, 125, 125, 125, 125, 125, 125, 125,  98,  98,  98,  98,  28,  28,  28,  28,
     98,  98, 112,  98,  98,  98,  98,  98,  98,  98,  98,  98,  98,  98, 124,  36,
     98,  98,  98, 124,  36,  36,  36,  36,  14,  14,  14,  14,  14,  14,  27, 106,
     12,  12,  12,  12,  12,  14,  36,  36,   0,  44,   0,   0,   0,   0,   0,  14,
     14,  14,  14,  14,  14,  14,  14,   0,   0,  27,  58,  58,  36,  36,  36,  36,
     36,  36,  36,  39,  14,  14,  14,  14,  14,  44,  14,  44,  14,  19,  14,  14,
     14,  19,   0,   0,  14,  14,  36,  36,  14,  14,  14,  14, 126,  36,  36,  36,
     14,  14,  65,  53,  36,  36,  36,  36,   0,  14,  14,  14,  14,  14,  14,  14,
      0,   0,  52,  36,  36,  36,  36,  58,   0,  14,  14,  14,  14,  14,  29,  36,
     14,  14,  14,   0,   0,   0,   0,  58,  14,  14,  14,  19,   0,   0,   0,   0,
      0,   0,  36,  36,  36,  36,  36,  39,  74,  74,  74,  74,  74,  74, 127,  36,
     14,  19,   0,   0,   0,   0,   0,   0,  44,  14,  14,  27,  58,  14,  14,  39,
     12,  12,  12,  12,  12,  36,  36,  14,  12,  12,  12,  12,  12,  61,  61,  62,
     14,  14,  14,  14,  19,   0,   0,   0,   0,   0,   0,  52,  36,  36,  36,  36,
     14,  19,  14,  14,  14,  14,   0,  36,  12,  12,  12,  12,  12,  36,  27,  58,
     61,  62,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  36,  60,  61,  61,
     58,  14,  19,  52,  36,  36,  36,  36,  39,  14,  14,  38,  39,  14,  14,  38,
     39,  14,  14,  38,  36,  36,  36,  36,  14,  19,   0,   0,   0,   1,   0,  36,
    128, 129, 129, 129, 129, 129, 129, 129, 129, 129, 129, 129, 129, 129, 128, 129,
    129, 129, 129, 129, 129, 129, 129, 129, 129, 129, 129, 129, 128, 129, 129, 129,
    129, 129, 128, 129, 129, 129, 129, 129, 129, 129,  36,  36,  36,  36,  36,  36,
     75,  75,  75, 130,  36, 131,  76,  76,  76,  76,  76,  76,  76,  76,  36,  36,
    132, 132, 132, 132, 132, 132, 132, 132,  36,  39,  14,  14,  36,  36, 133, 134,
     46,  46,  46,  46,  48,  46,  46,  46,  46,  46,  46,  47,  46,  46,  47,  47,
     46, 133,  47,  46,  46,  46,  46,  46,  36,  39,  14,  14,  14,  14,  14,  14,
     14,  14,  14,  14,  14,  14,  14, 104,  36,  14,  14,  14,  14,  14,  14,  14,
     14,  14,  14,  14,  14,  14, 126,  36, 135, 136,  57, 137, 138,  36,  36,  36,
     98,  98, 139, 104, 104, 104, 104, 104, 104, 104, 111, 139, 111,  98,  98,  98,
    111,  78,  91,  53, 139, 104, 104, 111,  98,  98,  98, 124, 140, 141,  36,  36,
     14,  14,  14,  14,  14,  14,  38, 142, 105,  98,   6,  98,  70,  98, 111, 111,
     98,  98,  98,  98,  98,  91,  98, 143,  98,  98,  98,  98,  98, 139, 144,  98,
     98,  98,  98,  98,  98, 139, 144, 139, 114,  70,  93, 145, 125, 125, 125, 125,
    146,  14,  14,  14,  14,  14,  14,  14,  14,  14,  14,  14,  14,  14,  14,  91,
     36,  14,  14,  14,  36,  14,  14,  14,  36,  14,  14,  14,  36,  14,  38,  36,
     22,  98, 140, 147,  14,  14,  14,  38,  36,  36,  36,  36,  42,   0, 148,  36,
     14,  14,  14,  14,  14,  14,  39,  14,  14,  14,  14,  14,  14,  38,  14,  39,
     58,  41,  36,  39,  14,  14,  14,  14,  14,  14,  36,  39,  14,  14,  14,  14,
     14,  14,  14,  14,  14,  14,  36,  36,  14,  14,  14,  14,  14,  14,  19,  36,
     14,  14,  36,  36,  36,  36,  36,  36,  14,  14,  14,   0,   0,  52,  36,  36,
     14,  14,  14,  14,  14,  14,  14,  81,  14,  14,  36,  36,  14,  14,  14,  14,
     77,  14,  14,  36,  36,  36,  36,  36,  14,  14,  36,  36,  36,  36,  36,  39,
     14,  14,  14,  36,  38,  14,  14,  14,  14,  14,  14,  39,  38,  36,  38,  39,
     14,  14,  14,  81,  14,  14,  14,  14,  14,  38,  14,  36,  36,  39,  14,  14,
     14,  14,  14,  14,  14,  14,  36,  81,  14,  14,  14,  14,  14,  36,  36,  39,
     14,  14,  14,  14,  36,  36,  14,  14,  19,   0,  42,  52,  36,  36,   0,   0,
     14,  14,  39,  14,  39,  14,  14,  14,  14,  14,  36,  36,   0,  52,  36,  42,
     58,  58,  58,  58,  38,  36,  36,  36,  14,  14,  19,  52,  36,  39,  14,  14,
     58,  58,  58, 149,  36,  36,  36,  36,  14,  14,  14,  36,  81,  58,  58,  58,
     14,  38,  36,  36,  14,  14,  14,  14,  14,  36,  36,  36,  39,  14,  38,  36,
     36,  36,  36,  36,  39,  14,  14,  14,  14,  38,  36,  36,  36,  36,  36,  36,
     14,  38,  36,  36,  36,  14,  14,  14,  14,  14,  14,  14,   0,   0,   0,   0,
      0,   0,   0,   1,  77,  14,  14,  36,  14,  14,  14,  12,  12,  12,  12,  12,
     36,  36,  36,  36,  36,  36,  36,  42,   0,   0,   0,   0,   0,  44,  14,  58,
     58,  36,  36,  36,  36,  36,  36,  36,   0,   0,  52,  12,  12,  12,  12,  12,
     58,  58,  36,  36,  36,  36,  36,  36,  14,  19,  32,  38,  36,  36,  36,  36,
     44,  14,  27,  77,  77,   0,  44,  36,  12,  12,  12,  12,  12,  32,  27,  58,
     14,  14,  14,  14,  14,  14,   0,   0,   0,   0,   0,   0,  58,  27,  77,  36,
     14,  14,  14,  38,  38,  14,  14,  39,  14,  14,  14,  14,  27,  36,  36,  36,
      0,   0,   0,   0,   0,  52,  36,  36,   0,   0,  39,  14,  14,  14,  38,  39,
     38,  36,  36,  42,  36,  36,  39,  14,  14,   0,  36,   0,   0,   0,  52,  36,
      0,   0,  52,  36,  36,  36,  36,  36,   0,   0,  14,  14,  36,  36,  36,  36,
      0,   0,   0,  36,   0,   0,   0,   0, 150,  58,  53,  14,  27,  58,  58,  58,
     58,  58,  58,  58,  14,  14,   0,  36,   1,  77,  38,  36,  36,  36,  36,  36,
      0,   0,   0,   0,  36,  36,  36,  36,  61,  61,  61,  61,  61,  36,  60,  61,
     12,  12,  12,  12,  12,  61,  58, 151,  14,  38,  36,  36,  36,  36,  36,  39,
     58,  58,  41,  36,  36,  36,  36,  36,  14,  14,  14,  14, 152,  70, 114,  14,
     14,  99,  14,  70,  70,  14,  14,  14,  14,  14,  14,  14,  16, 114,  14,  14,
     14,  14,  14,  14,  14,  14,  14,  70,  12,  12,  12,  12,  12,  36,  36,  58,
      0,   0,   1,  36,  36,  36,  36,  36,   0,   0,   0,   1,  58,  14,  14,  14,
     14,  14,  77,  36,  36,  36,  36,  36,  12,  12,  12,  12,  12,  39,  14,  14,
     14,  14,  14,  14,  36,  36,  39,  14,  19,   0,   0,   0,   0,   0,   0,   0,
     98,  36,  36,  36,  36,  36,  36,  36,  14,  14,  14,  14,  14,  36,  19,   1,
      0,   0,  36,  36,  36,  36,  36,  36,  14,  14,  19,   0,   0,  14,  19,   0,
      0,  44,  19,   0,   0,   0,  14,  14,  14,  14,  14,  14,  14,   0,   0,  14,
     14,   0,  44,  36,  36,  36,  36,  36,  36,  38,  39,  38,  39,  14,  38,  14,
     14,  14,  14,  14,  14,  39,  39,  14,  14,  14,  39,  14,  14,  14,  14,  14,
     14,  14,  14,  39,  14,  38,  39,  14,  14,  14,  38,  14,  14,  14,  38,  14,
     14,  14,  14,  14,  14,  39,  14,  38,  14,  14,  38,  38,  36,  14,  14,  14,
     14,  14,  14,  14,  14,  14,  36,  12,  12,  12,  12,  12,  12,  12,  12,  12,
      0,   0,   0,  44,  14,  19,   0,   0,   0,   0,   0,   0,   0,   0,  44,  14,
     14,  14,  19,  14,  14,  14,  14,  14,  14,  14,  44,  27,  58,  77,  36,  36,
     36,  36,  36,  36,  36,  42,   0,   0,  14,  14,  38,  39,  14,  14,  14,  14,
     39,  38,  38,  39,  39,  14,  14,  14,  14,  38,  14,  14,  39,  39,  36,  36,
     36,  38,  36,  39,  39,  39,  39,  14,  39,  38,  38,  39,  39,  39,  39,  39,
     39,  38,  38,  39,  14,  38,  14,  14,  14,  38,  14,  14,  39,  14,  38,  38,
     14,  14,  14,  14,  14,  39,  14,  14,  39,  14,  39,  14,  14,  39,  14,  14,
     28,  28,  28,  28,  28,  28, 153,  36,  28,  28,  28,  28,  28,  28,  28,  38,
     28,  28,  28,  28,  28,  14,  36,  36,  28,  28,  28,  28,  28, 153,  36,  36,
     36,  36,  36, 154, 154, 154, 154, 154, 154, 154, 154, 154, 154, 154, 154, 154,
     98, 124,  36,  36,  36,  36,  36,  36,  98,  98,  98,  98, 124,  36,  36,  36,
     98,  98,  98,  98,  98,  98,  14,  98,  98,  98, 100, 101,  98,  98, 101,  98,
     98,  98,  98,  98,  98, 100,  14,  14, 101, 101, 101,  98,  98,  98,  98, 100,
    100, 101,  98,  98,  98,  98,  98,  98,  14,  14,  14, 101,  98,  98,  98,  98,
     98,  98,  98, 100,  14,  14,  14,  14,  14,  14, 101,  98,  98,  98,  98,  98,
     98,  14,  14,  14,  14,  14,  14,  14,  14,  14,  14,  14,  14,  98,  98,  98,
     98,  98, 110,  98,  98,  98,  98,  98,  98,  98,  14,  14,  14,  14,  98,  98,
     98,  98,  14,  14,  14,  98,  98,  98,  14,  14,  14,  85, 155,  91,  14,  14,
    124,  36,  36,  36,  36,  36,  36,  36,  98,  98, 124,  36,  36,  36,  36,  36,
     42,  36,  36,  36,  36,  36,  36,  36,
};

static RE_UINT8 re_line_break_stage_5[] = {
    16, 16, 16, 18, 22, 20, 20, 21, 19,  6,  3, 12,  9, 10, 12,  3,
     1, 36, 12,  9,  8, 15,  8,  7, 11, 11,  8,  8, 12, 12, 12,  6,
    12,  1,  9, 36, 18,  2, 12, 16, 16, 29,  4,  1, 10,  9,  9,  9,
    12, 25, 25, 12, 25,  3, 12, 18, 25, 25, 17, 12, 25,  1, 17, 25,
    12, 17, 16,  4,  4,  4,  4, 16,  0,  0,  8, 12, 12,  0,  0, 12,
     0,  8, 18,  0,  0, 16, 18, 16, 16, 12,  6, 16, 37, 37, 37,  0,
    37, 12, 12, 10, 10, 10, 16,  6, 16,  0,  6,  6, 10, 11, 11, 12,
     6, 12,  8,  6, 18, 18,  0, 10,  0, 24, 24, 24, 24,  0,  0,  9,
    24, 12, 17, 17,  4, 17, 17, 18,  4,  6,  4, 12,  1,  2, 18, 17,
    12,  4,  4,  0, 31, 31, 32, 32, 33, 33, 18, 12,  2,  0,  5, 24,
    18,  9,  0, 18, 18,  4, 18, 28, 26, 25,  3,  3,  1,  3, 14, 14,
    14, 18, 20, 20,  3, 25,  5,  5,  8,  1,  2,  5, 30, 12,  2, 25,
     9, 12, 12, 14, 13, 13,  2, 12, 13, 12, 12, 13, 13, 25, 25, 13,
     2,  1,  0,  6,  6, 18,  1, 18, 26, 26,  1,  0,  0, 13,  2, 13,
    13,  5,  5,  1,  2,  2, 13, 16,  5, 13,  0, 38, 13, 38, 38, 13,
    38,  0, 16,  5,  5, 38, 38,  5, 13,  0, 38, 38, 10, 12, 31,  0,
    34, 35, 35, 35, 32,  0,  0, 33, 27, 27,  0, 37, 16, 37,  8,  2,
     2,  8,  6,  1,  2, 14, 13,  1, 13,  9, 10, 13,  0, 30, 13,  6,
    13,  2, 12, 38, 38, 12,  9,  0, 23, 25, 14,  0, 16, 17, 18, 24,
     1,  1, 25,  0, 39, 39,  3,  5,
};

/* Line_Break: 8608 bytes. */

RE_UINT32 re_get_line_break(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 12;
    code = ch ^ (f << 12);
    pos = (RE_UINT32)re_line_break_stage_1[f] << 5;
    f = code >> 7;
    code ^= f << 7;
    pos = (RE_UINT32)re_line_break_stage_2[pos + f] << 3;
    f = code >> 4;
    code ^= f << 4;
    pos = (RE_UINT32)re_line_break_stage_3[pos + f] << 3;
    f = code >> 1;
    code ^= f << 1;
    pos = (RE_UINT32)re_line_break_stage_4[pos + f] << 1;
    value = re_line_break_stage_5[pos + code];

    return value;
}

/* Numeric_Type. */

static RE_UINT8 re_numeric_type_stage_1[] = {
     0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 11, 11, 11, 12,
    13, 14, 15, 11, 11, 11, 16, 11, 11, 11, 11, 11, 11, 17, 18, 19,
    20, 11, 21, 22, 11, 11, 23, 11, 11, 11, 11, 11, 11, 11, 11, 24,
    11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
    11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
    11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
    11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
    11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
    11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
    11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
    11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
    11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
    11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
    11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
    11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
    11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
    11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
};

static RE_UINT8 re_numeric_type_stage_2[] = {
     0,  1,  1,  1,  1,  1,  2,  3,  1,  4,  5,  6,  7,  8,  9, 10,
    11,  1,  1, 12,  1,  1, 13, 14, 15, 16, 17, 18, 19,  1,  1,  1,
    20, 21,  1,  1, 22,  1,  1, 23,  1,  1,  1,  1, 24,  1,  1,  1,
    25, 26, 27,  1, 28,  1,  1,  1, 29,  1,  1, 30,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1, 31, 32,
     1, 33,  1, 34,  1,  1, 35,  1, 36,  1,  1,  1,  1,  1, 37, 38,
     1,  1, 39, 40,  1,  1,  1, 41,  1,  1,  1,  1,  1,  1,  1, 42,
     1,  1,  1, 43,  1,  1, 44,  1,  1,  1,  1,  1,  1,  1,  1,  1,
    45,  1,  1,  1, 46,  1,  1,  1,  1,  1,  1,  1, 47, 48,  1,  1,
     1,  1,  1,  1,  1,  1, 49,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1, 50,  1, 51, 52, 53, 54,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  1, 55,  1,  1,  1,  1,  1, 15,
     1, 56, 57, 58, 59,  1,  1,  1, 60, 61, 62, 63, 64,  1, 65,  1,
    66, 67, 54,  1, 68,  1, 69, 70, 71,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1, 72,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1, 73, 74,  1,  1,  1,  1,
     1,  1,  1, 75,  1,  1,  1, 76,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1, 77,  1,  1,  1,  1,  1,  1,  1,
     1, 78,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
    79, 80,  1,  1,  1,  1,  1,  1,  1, 81, 82, 83,  1,  1,  1,  1,
     1,  1,  1, 84,  1,  1,  1,  1,  1, 85,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1, 86,  1,  1,  1,  1,
     1,  1, 87,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1, 84,  1,  1,  1,  1,  1,  1,  1,
};

static RE_UINT8 re_numeric_type_stage_3[] = {
      0,   1,   0,   0,   0,   2,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   3,   0,   0,   0,   1,   0,   0,   0,   0,   0,   0,   3,   0,
      0,   0,   0,   4,   0,   0,   0,   5,   0,   0,   0,   4,   0,   0,   0,   4,
      0,   0,   0,   6,   0,   0,   0,   7,   0,   0,   0,   8,   0,   0,   0,   4,
      0,   0,   0,   9,   0,   0,   0,   4,   0,   0,   1,   0,   0,   0,   1,   0,
      0,  10,   0,   0,   0,   0,   0,   0,   0,   0,   3,   0,   1,   0,   0,   0,
      0,   0,   0,  11,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  12,
      0,   0,   0,   0,   0,   0,   0,  13,   1,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   4,   0,   0,   0,  14,   0,   0,   0,   0,   0,  15,   0,   0,   0,
      0,   0,   1,   0,   0,   1,   0,   0,   0,   0,  15,   0,   0,   0,   0,   0,
      0,   0,   0,  16,  17,   0,   0,   0,   0,   0,  18,  19,  20,   0,   0,   0,
      0,   0,   0,  21,  22,   0,   0,  23,   0,   0,   0,  24,  25,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,  26,  27,  28,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,  29,   0,   0,   0,   0,  30,  31,   0,  30,  32,   0,   0,
     33,   0,   0,   0,  34,   0,   0,   0,   0,  35,   0,   0,   0,   0,   0,   0,
      0,   0,  36,   0,   0,   0,   0,   0,  37,   0,  26,   0,  38,  39,  40,  41,
     36,   0,   0,  42,   0,   0,   0,   0,  43,   0,  44,  45,   0,   0,   0,   0,
      0,   0,  46,   0,   0,   0,  47,   0,   0,   0,   0,   0,   0,   0,  48,   0,
      0,   0,   0,   0,   0,   0,   0,  49,   0,   0,   0,  50,   0,   0,   0,  51,
     52,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  53,
      0,   0,  54,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  55,   0,
     44,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  56,   0,   0,   0,
      0,   0,   0,  53,   0,   0,   0,   0,   0,   0,   0,   0,  44,   0,   0,   0,
      0,  54,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  57,   0,   0,
      0,  42,   0,   0,   0,   0,   0,   0,   0,  58,  59,  60,   0,   0,   0,  56,
      0,   3,   0,   0,   0,   0,   0,  61,   0,  62,   0,   0,   0,   0,   1,   0,
      3,   0,   0,   0,   0,   0,   1,   1,   0,   0,   1,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   1,   0,   0,   0,  63,   0,  55,  64,  26,
     65,  66,  19,  67,  68,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  69,
      0,  70,  71,   0,   0,   0,  72,   0,   0,   0,   0,   0,   0,   3,   0,   0,
      0,   0,  73,  74,   0,  75,   0,  76,  77,   0,   0,   0,   0,  78,  79,  19,
      0,   0,  80,  81,  82,   0,   0,  83,   0,   0,  73,  73,   0,  84,   0,   0,
      0,   0,   0,   0,   0,   0,   0,  85,   0,   0,   0,  86,   0,   0,   0,   0,
      0,   0,  87,  88,   0,   0,   0,   1,   0,  89,   0,   0,   0,   0,   1,  90,
      0,   0,   0,   0,   0,   0,   1,   0,   0,   0,   1,   0,   0,   0,   3,   0,
      0,  91,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  92,
     19,  19,  19,  93,   0,   0,   0,   0,   0,   0,   0,   3,   0,   0,   0,   0,
      0,   0,  94,  95,   0,   0,   0,   0,   0,   0,   0,  96,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,  97,  98,   0,   0,   0,   0,   0,   0,  75,   0,
     99,   0,   0,   0,   0,   0,   0,   0,  58,   0,   0,  43,   0,   0,   0, 100,
      0,  58,   0,   0,   0,   0,   0,   0,   0,  35,   0,   0, 101,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0, 102, 103,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,  42,   0,   0,   0,   0,   0,   0,   0,  60,   0,   0,   0,
     48,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  36,   0,   0,   0,   0,
};

static RE_UINT8 re_numeric_type_stage_4[] = {
     0,  0,  0,  0,  0,  0,  1,  2,  0,  0,  3,  4,  1,  2,  0,  0,
     5,  1,  0,  0,  5,  1,  6,  7,  5,  1,  8,  0,  5,  1,  9,  0,
     5,  1,  0, 10,  5,  1, 11,  0,  1, 12, 13,  0,  0, 14, 15, 16,
     0, 17, 18,  0,  1,  2, 19,  7,  0,  0,  1, 20,  1,  2,  1,  2,
     0,  0, 21, 22, 23, 22,  0,  0,  0,  0, 19, 19, 19, 19, 19, 19,
    24,  7,  0,  0, 23, 25, 26, 27, 19, 23, 25, 13,  0, 28, 29, 30,
     0,  0, 31, 32, 23, 33, 34,  0,  0,  0,  0, 35, 36,  0,  0,  0,
    37,  7,  0,  9,  0,  0, 38,  0, 19,  7,  0,  0,  0, 19, 37, 19,
     0,  0, 37, 19, 35,  0,  0,  0, 39,  0,  0,  0,  0, 40,  0,  0,
     0, 35,  0,  0, 41, 42,  0,  0,  0, 43, 44,  0,  0,  0,  0, 36,
    18,  0,  0, 36,  0, 18,  0,  0,  0,  0, 18,  0, 43,  0,  0,  0,
    45,  0,  0,  0,  0, 46,  0,  0, 47, 43,  0,  0, 48,  0,  0,  0,
     0,  0,  0, 39,  0,  0, 42, 42,  0,  0,  0, 40,  0,  0,  0, 17,
     0, 49, 18,  0,  0,  0,  0, 45,  0, 43,  0,  0,  0,  0, 40,  0,
     0,  0, 45,  0,  0, 45, 39,  0, 42,  0,  0,  0, 45, 43,  0,  0,
     0,  0,  0, 18, 17, 19,  0,  0,  0,  0, 11,  0,  0, 39, 39, 18,
     0,  0, 50,  0, 36, 19, 19, 19, 19, 19, 13,  0, 19, 19, 19, 18,
     0, 51,  0,  0, 37, 19, 19, 13, 13,  0,  0,  0, 42, 40,  0,  0,
     0,  0, 52,  0,  0,  0,  0, 19,  0,  0,  0, 37, 36, 19,  0,  0,
     0,  0,  0, 53,  0,  0, 17, 13,  0,  0,  0, 54, 19, 19,  8, 19,
    55,  0,  0,  0,  0,  0,  0, 56,  0,  0,  0, 57,  0, 53,  0,  0,
     0, 37,  0,  0,  0,  0,  0,  8, 23, 25, 19, 10,  0,  0, 58, 59,
    60,  1,  0,  0,  0,  0,  5,  1, 37, 19, 16,  0,  0,  0,  1, 61,
     1, 12,  9,  0, 19, 10,  0,  0,  0,  0,  1, 62,  7,  0,  0,  0,
    19, 19,  7,  0,  0,  5,  1,  1,  1,  1,  1,  1, 23, 63,  0,  0,
    40,  0,  0,  0, 39, 43,  0, 43,  0, 40,  0, 35,  0,  0,  0, 42,
};

static RE_UINT8 re_numeric_type_stage_5[] = {
    0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3,
    3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 0, 0, 0, 0,
    0, 2, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 3, 3,
    0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0,
    0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0,
    1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0,
    3, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0,
    0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1,
    1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1,
    3, 3, 2, 0, 0, 0, 0, 0, 2, 0, 0, 0, 2, 2, 2, 2,
    2, 2, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 2,
    1, 1, 1, 0, 0, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1,
    0, 0, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 1, 2, 0, 0, 0, 0, 0, 0, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 1, 2, 1, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1,
    0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0,
    0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1,
    0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0,
    0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0,
    0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 1, 1, 0, 0,
    0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0,
    0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0,
    0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1,
    0, 0, 0, 0, 1, 1, 0, 0, 2, 2, 2, 2, 1, 1, 1, 1,
    0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1,
    0, 0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 3, 3, 3, 3, 1, 1, 0, 0, 0, 0,
    3, 3, 0, 1, 1, 1, 1, 1, 2, 2, 2, 1, 1, 0, 0, 0,
};

/* Numeric_Type: 2304 bytes. */

RE_UINT32 re_get_numeric_type(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 12;
    code = ch ^ (f << 12);
    pos = (RE_UINT32)re_numeric_type_stage_1[f] << 4;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_numeric_type_stage_2[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_numeric_type_stage_3[pos + f] << 2;
    f = code >> 3;
    code ^= f << 3;
    pos = (RE_UINT32)re_numeric_type_stage_4[pos + f] << 3;
    value = re_numeric_type_stage_5[pos + code];

    return value;
}

/* Numeric_Value. */

static RE_UINT8 re_numeric_value_stage_1[] = {
     0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 11, 11, 11, 12,
    13, 14, 15, 11, 11, 11, 16, 11, 11, 11, 11, 11, 11, 17, 18, 19,
    20, 11, 21, 22, 11, 11, 23, 11, 11, 11, 11, 11, 11, 11, 11, 24,
    11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
    11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
    11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
    11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
    11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
    11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
    11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
    11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
    11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
    11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
    11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
    11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
    11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
    11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
};

static RE_UINT8 re_numeric_value_stage_2[] = {
     0,  1,  1,  1,  1,  1,  2,  3,  1,  4,  5,  6,  7,  8,  9, 10,
    11,  1,  1, 12,  1,  1, 13, 14, 15, 16, 17, 18, 19,  1,  1,  1,
    20, 21,  1,  1, 22,  1,  1, 23,  1,  1,  1,  1, 24,  1,  1,  1,
    25, 26, 27,  1, 28,  1,  1,  1, 29,  1,  1, 30,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1, 31, 32,
     1, 33,  1, 34,  1,  1, 35,  1, 36,  1,  1,  1,  1,  1, 37, 38,
     1,  1, 39, 40,  1,  1,  1, 41,  1,  1,  1,  1,  1,  1,  1, 42,
     1,  1,  1, 43,  1,  1, 44,  1,  1,  1,  1,  1,  1,  1,  1,  1,
    45,  1,  1,  1, 46,  1,  1,  1,  1,  1,  1,  1, 47, 48,  1,  1,
     1,  1,  1,  1,  1,  1, 49,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1, 50,  1, 51, 52, 53, 54,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  1, 55,  1,  1,  1,  1,  1, 15,
     1, 56, 57, 58, 59,  1,  1,  1, 60, 61, 62, 63, 64,  1, 65,  1,
    66, 67, 54,  1, 68,  1, 69, 70, 71,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1, 72,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1, 73, 74,  1,  1,  1,  1,
     1,  1,  1, 75,  1,  1,  1, 76,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1, 77,  1,  1,  1,  1,  1,  1,  1,
     1, 78,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
    79, 80,  1,  1,  1,  1,  1,  1,  1, 81, 82, 83,  1,  1,  1,  1,
     1,  1,  1, 84,  1,  1,  1,  1,  1, 85,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1, 86,  1,  1,  1,  1,
     1,  1, 87,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1, 88,  1,  1,  1,  1,  1,  1,  1,
};

static RE_UINT8 re_numeric_value_stage_3[] = {
      0,   1,   0,   0,   0,   2,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   3,   0,   0,   0,   1,   0,   0,   0,   0,   0,   0,   3,   0,
      0,   0,   0,   4,   0,   0,   0,   5,   0,   0,   0,   4,   0,   0,   0,   4,
      0,   0,   0,   6,   0,   0,   0,   7,   0,   0,   0,   8,   0,   0,   0,   4,
      0,   0,   0,   9,   0,   0,   0,   4,   0,   0,   1,   0,   0,   0,   1,   0,
      0,  10,   0,   0,   0,   0,   0,   0,   0,   0,   3,   0,   1,   0,   0,   0,
      0,   0,   0,  11,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  12,
      0,   0,   0,   0,   0,   0,   0,  13,   1,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   4,   0,   0,   0,  14,   0,   0,   0,   0,   0,  13,   0,   0,   0,
      0,   0,   1,   0,   0,   1,   0,   0,   0,   0,  13,   0,   0,   0,   0,   0,
      0,   0,   0,  15,   3,   0,   0,   0,   0,   0,  16,  17,  18,   0,   0,   0,
      0,   0,   0,  19,  20,   0,   0,  21,   0,   0,   0,  22,  23,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,  24,  25,  26,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,  27,   0,   0,   0,   0,  28,  29,   0,  28,  30,   0,   0,
     31,   0,   0,   0,  32,   0,   0,   0,   0,  33,   0,   0,   0,   0,   0,   0,
      0,   0,  34,   0,   0,   0,   0,   0,  35,   0,  36,   0,  37,  38,  39,  40,
     41,   0,   0,  42,   0,   0,   0,   0,  43,   0,  44,  45,   0,   0,   0,   0,
      0,   0,  46,   0,   0,   0,  47,   0,   0,   0,   0,   0,   0,   0,  48,   0,
      0,   0,   0,   0,   0,   0,   0,  49,   0,   0,   0,  50,   0,   0,   0,  51,
     52,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  53,
      0,   0,  54,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  55,   0,
     56,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  57,   0,   0,   0,
      0,   0,   0,  58,   0,   0,   0,   0,   0,   0,   0,   0,  59,   0,   0,   0,
      0,  60,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  61,   0,   0,
      0,  62,   0,   0,   0,   0,   0,   0,   0,  63,  64,  65,   0,   0,   0,  66,
      0,   3,   0,   0,   0,   0,   0,  67,   0,  68,   0,   0,   0,   0,   1,   0,
      3,   0,   0,   0,   0,   0,   1,   1,   0,   0,   1,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   1,   0,   0,   0,  69,   0,  70,  71,  72,
     73,  74,  75,  76,  77,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  78,
      0,  79,  80,   0,   0,   0,  81,   0,   0,   0,   0,   0,   0,   3,   0,   0,
      0,   0,  82,  83,   0,  84,   0,  85,  86,   0,   0,   0,   0,  87,  88,  89,
      0,   0,  90,  91,  92,   0,   0,  93,   0,   0,  94,  94,   0,  95,   0,   0,
      0,   0,   0,   0,   0,   0,   0,  96,   0,   0,   0,  97,   0,   0,   0,   0,
      0,   0,  98,  99,   0,   0,   0,   1,   0, 100,   0,   0,   0,   0,   1, 101,
      0,   0,   0,   0,   0,   0,   1,   0,   0,   0,   1,   0,   0,   0,   3,   0,
      0, 102,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 103,
    104, 105, 106, 107,   0,   0,   0,   0,   0,   0,   0,   3,   0,   0,   0,   0,
      0,   0, 108, 109,   0,   0,   0,   0,   0,   0,   0, 110,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0, 111, 112,   0,   0,   0,   0,   0,   0, 113,   0,
    114,   0,   0,   0,   0,   0,   0,   0, 115,   0,   0, 116,   0,   0,   0, 117,
      0, 118,   0,   0,   0,   0,   0,   0,   0, 119,   0,   0, 120,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0, 121, 122,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,  62,   0,   0,   0,   0,   0,   0,   0, 123,   0,   0,   0,
    124,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 125,   0,   0,   0,   0,
      0,   0,   0,   0, 126,   0,   0,   0,
};

static RE_UINT8 re_numeric_value_stage_4[] = {
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   1,   2,   3,   0,
      0,   0,   0,   0,   4,   0,   5,   6,   1,   2,   3,   0,   0,   0,   0,   0,
      0,   7,   8,   9,   0,   0,   0,   0,   0,   7,   8,   9,   0,  10,  11,   0,
      0,   7,   8,   9,  12,  13,   0,   0,   0,   7,   8,   9,  14,   0,   0,   0,
      0,   7,   8,   9,   0,   0,   1,  15,   0,   7,   8,   9,  16,  17,   0,   0,
      1,   2,  18,  19,  20,   0,   0,   0,   0,   0,  21,   2,  22,  23,  24,  25,
      0,   0,   0,  26,  27,   0,   0,   0,   1,   2,   3,   0,   1,   2,   3,   0,
      0,   0,   0,   0,   1,   2,  28,   0,   0,   0,   0,   0,  29,   2,   3,   0,
      0,   0,   0,   0,  30,  31,  32,  33,  34,  35,  36,  37,  34,  35,  36,  37,
     38,  39,  40,   0,   0,   0,   0,   0,  34,  35,  36,  41,  42,  34,  35,  36,
     41,  42,  34,  35,  36,  41,  42,   0,   0,   0,  43,  44,  45,  46,   2,  47,
      0,   0,   0,   0,   0,  48,  49,  50,  34,  35,  51,  49,  50,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,  52,   0,  53,   0,   0,   0,   0,   0,   0,
     21,   2,   3,   0,   0,   0,  54,   0,   0,   0,   0,   0,  48,  55,   0,   0,
     34,  35,  56,   0,   0,   0,   0,   0,   0,   0,  57,  58,  59,  60,  61,  62,
      0,   0,   0,   0,  63,  64,  65,  66,   0,  67,   0,   0,   0,   0,   0,   0,
     68,   0,   0,   0,   0,   0,   0,   0,   0,   0,  69,   0,   0,   0,   0,   0,
      0,   0,   0,  70,   0,   0,   0,   0,  71,  72,  73,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,  74,   0,   0,   0,  75,   0,  76,   0,   0,
      0,   0,   0,   0,   0,   0,   0,  77,  78,   0,   0,   0,   0,   0,   0,  79,
      0,   0,  80,   0,   0,   0,   0,   0,   0,   0,   0,  67,   0,   0,   0,   0,
      0,   0,   0,   0,  81,   0,   0,   0,   0,  82,   0,   0,   0,   0,   0,   0,
      0,  83,   0,   0,   0,   0,   0,   0,   0,   0,  84,  85,   0,   0,   0,   0,
     86,  87,   0,  88,   0,   0,   0,   0,  89,  80,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,  90,   0,   0,   0,   0,   0,   5,   0,   5,   0,
      0,   0,   0,   0,   0,   0,  91,   0,   0,   0,   0,   0,   0,   0,   0,  92,
      0,   0,   0,  15,  75,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  93,
      0,   0,   0,  94,   0,   0,   0,   0,   0,   0,   0,   0,  95,   0,   0,   0,
      0,  95,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  96,   0,   0,
      0,   0,   0,   0,   0,   0,   0,  97,   0,  98,   0,   0,   0,   0,   0,   0,
      0,   0,   0,  25,   0,   0,   0,   0,   0,   0,   0,  99,  68,   0,   0,   0,
      0,   0,   0,   0,  75,   0,   0,   0, 100,   0,   0,   0,   0,   0,   0,   0,
      0, 101,   0,  81,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 102,   0,
      0,   0,   0,   0,   0, 103,   0,   0,   0,  48,  49, 104,   0,   0,   0,   0,
      0,   0,   0,   0, 105, 106,   0,   0,   0,   0, 107,   0, 108,   0,  75,   0,
      0,   0,   0,   0, 103,   0,   0,   0,   0,   0,   0,   0, 109,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0, 110,   0, 111,   8,   9,  57,  58, 112, 113,
    114, 115, 116, 117, 118,   0,   0,   0, 119, 120, 121, 122, 123, 124, 125, 126,
    127, 128, 129, 130, 122, 131, 132,   0,   0,   0, 133,   0,   0,   0,   0,   0,
     21,   2,  22,  23,  24, 134, 135,   0, 136,   0,   0,   0,   0,   0,   0,   0,
    137,   0, 138,   0,   0,   0,   0,   0,   0,   0,   0,   0, 139, 140,   0,   0,
      0,   0,   0,   0,   0,   0, 141, 142,   0,   0,   0,   0,   0,   0,  21, 143,
      0, 111, 144, 145,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 111, 145,
      0,   0,   0,   0,   0, 146, 147,   0,   0,   0,   0,   0,   0,   0,   0, 148,
     34,  35, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162,
     34, 163,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 164,
      0,   0,   0,   0,   0,   0,   0, 165,   0,   0, 111, 145,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,  34, 163,   0,   0,  21, 166,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0, 167, 168,  34,  35, 149, 150, 169, 152, 170, 171,
      0,   0,   0,   0,  48,  49,  50, 172, 173, 174,   8,   9,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   7,   8,   9,  21,   2,  22,  23,  24, 175,   0,   0,
      0,   0,   0,   0,   1,   2,  22,   0,   1,   2,  22,  23, 176,   0,   0,   0,
      8,   9,  49, 177,  35, 178,   2, 179, 180, 181,   9, 182, 183, 182, 184, 185,
    186, 187, 188, 189, 144, 190, 191, 192, 193, 194, 195, 196,   0,   0,   0,   0,
      0,   0,   0,   0,   1,   2, 197, 198, 199,   0,   0,   0,   0,   0,   0,   0,
     34,  35, 149, 150, 200,   0,   0,   0,   0,   0,   0,   7,   8,   9,   1,   2,
    201,   8,   9,   1,   2, 201,   8,   9,   0, 111,   8,   9,   0,   0,   0,   0,
    202,  49, 104,  29,   0,   0,   0,   0,  70,   0,   0,   0,   0,   0,   0,   0,
      0, 203,   0,   0,   0,   0,   0,   0,  98,   0,   0,   0,   0,   0,   0,   0,
     67,   0,   0,   0,   0,   0,   0,   0,   0,   0,  91,   0,   0,   0,   0,   0,
    204,   0,   0,  88,   0,   0,   0,  88,   0,   0, 101,   0,   0,   0,   0,  73,
      0,   0,   0,   0,   0,   0,  73,   0,   0,   0,   0,   0,   0,   0,  80,   0,
      0,   0,   0,   0,   0,   0, 107,   0,   0,   0,   0, 205,   0,   0,   0,   0,
      0,   0,   0,   0, 206,   0,   0,   0,
};

static RE_UINT8 re_numeric_value_stage_5[] = {
      0,   0,   0,   0,   2,  27,  29,  31,  33,  35,  37,  39,  41,  43,   0,   0,
      0,   0,  29,  31,   0,  27,   0,   0,  12,  17,  22,   0,   0,   0,   2,  27,
     29,  31,  33,  35,  37,  39,  41,  43,   3,   7,  10,  12,  22,  50,   0,   0,
      0,   0,  12,  17,  22,   3,   7,  10,  44,  89,  98,   0,  27,  29,  31,   0,
     44,  89,  98,  12,  17,  22,   0,   0,  41,  43,  17,  28,  30,  32,  34,  36,
     38,  40,  42,   1,   0,  27,  29,  31,  41,  43,  44,  54,  64,  74,  84,  85,
     86,  87,  88,  89, 107,   0,   0,   0,   0,   0,  51,  52,  53,   0,   0,   0,
     41,  43,  27,   0,   2,   0,   0,   0,   8,   6,   5,  13,  21,  11,  15,  19,
     23,   9,  24,   7,  14,  20,  25,  27,  27,  29,  31,  33,  35,  37,  39,  41,
     43,  44,  45,  46,  84,  89,  93,  98,  98, 102, 107,   0,   0,  37,  84, 111,
    116,   2,   0,   0,  47,  48,  49,  50,  51,  52,  53,  54,   0,   0,   2,  45,
     46,  47,  48,  49,  50,  51,  52,  53,  54,  27,  29,  31,  41,  43,  44,   2,
      0,   0,  27,  29,  31,  33,  35,  37,  39,  41,  43,  44,  43,  44,  27,  29,
      0,  17,   0,   0,   0,   0,   0,   2,  44,  54,  64,   0,  31,  33,   0,   0,
     43,  44,   0,   0,  44,  54,  64,  74,  84,  85,  86,  87,   0,  55,  56,  57,
     58,  59,  60,  61,  62,  63,  64,  65,  66,  67,  68,  69,   0,  70,  71,  72,
     73,  74,  75,  76,  77,  78,  79,  80,  81,  82,  83,  84,   0,  35,   0,   0,
      0,   0,   0,  29,   0,   0,  35,   0,   0,  39,   0,   0,  27,   0,   0,  39,
      0,   0,   0, 107,   0,  31,   0,   0,   0,  43,   0,   0,  29,   0,   0,   0,
     35,   0,  33,   0,   0,   0,   0, 128,  44,   0,   0,   0,   0,   0,   0,  98,
     31,   0,   0,   0,  89,   0,   0,   0, 128,   0,   0,   0,   0,   0, 130,   0,
      0,  29,   0,  41,   0,  37,   0,   0,   0,  44,   0,  98,  54,  64,   0,   0,
     74,   0,   0,   0,   0,  31,  31,  31,   0,   0,   0,  33,   0,   0,  27,   0,
      0,   0,  43,  54,   0,   0,  44,   0,  41,   0,   0,   0,   0,   0,  39,   0,
      0,   0,  43,   0,   0,   0,  89,   0,   0,   0,  33,   0,   0,   0,  29,   0,
      0,  98,   0,   0,   0,   0,  37,   0,  37,   0,   0,   0,   0,   0,   2,   0,
     39,  41,  43,   2,  12,  17,  22,   3,   7,  10,   0,   0,   0,   0,   0,  31,
      0,   0,   0,  44,   0,  37,   0,  37,   0,  44,   0,   0,   0,   0,   0,  27,
     88,  89,  90,  91,  92,  93,  94,  95,  96,  97,  98,  99, 100, 101, 102, 103,
    104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115,  12,  17,  27,  35,
     84,  93, 102, 111,  35,  44,  84,  89,  93,  98, 102,  35,  44,  84,  89,  93,
     98, 107, 111,  44,  27,  27,  27,  29,  29,  29,  29,  35,  44,  44,  44,  44,
     44,  64,  84,  84,  84,  84,  89,  91,  93,  93,  93,  93,  84,  17,  17,  21,
     22,   0,   0,   0,   0,   0,   2,  12,  90,  91,  92,  93,  94,  95,  96,  97,
     27,  35,  44,  84,   0,  88,   0,   0,   0,   0,  97,   0,   0,  27,  29,  44,
     54,  89,   0,   0,  27,  29,  31,  44,  54,  89,  98, 107,  33,  35,  44,  54,
     29,  31,  33,  33,  35,  44,  54,  89,   0,   0,  27,  44,  54,  89,  29,  31,
     26,  17,   0,   0,  43,  44,  54,  64,  74,  84,  85,  86,   0,   0,  89,  90,
     91,  92,  93,  94,  95,  96,  97,  98,  99, 100, 101, 102, 103, 104, 105, 106,
    107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 119, 120, 122, 123, 124,
    125, 126,   4,   9,  12,  13,  16,  17,  18,  21,  22,  24,  44,  54,  89,  98,
      0,  27,  84,   0,   0,  27,  44,  54,  33,  44,  54,  89,   0,   0,  27,  35,
     44,  84,  89,  98,  87,  88,  89,  90,  95,  96,  97,  17,  12,  13,  21,   0,
     54,  64,  74,  84,  85,  86,  87,  88,  89,  98,   2,  27,  98,   0,   0,   0,
     86,  87,  88,   0,  39,  41,  43,  33,  43,  27,  29,  31,  41,  43,  27,  29,
     31,  33,  35,  29,  31,  31,  33,  35,  27,  29,  31,  31,  33,  35, 118, 121,
     33,  35,  31,  31,  33,  33,  33,  33,  37,  39,  39,  39,  41,  41,  43,  43,
     43,  43,  29,  31,  33,  35,  37,  27,  35,  35,  29,  31,  27,  29,  13,  21,
     24,  13,  21,   7,  12,   9,  12,  12,  17,  13,  21,  74,  84,  33,  35,  37,
     39,  41,  43,   0,  41,  43,   0,  44,  89, 107, 127, 128, 129, 130,   0,   0,
     87,  88,   0,   0,  41,  43,   2,  27,   2,   2,  27,  29,  33,   0,   0,   0,
      0,   0,   0,  64,   0,  33,   0,   0,  43,   0,   0,   0,
};

/* Numeric_Value: 3228 bytes. */

RE_UINT32 re_get_numeric_value(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 12;
    code = ch ^ (f << 12);
    pos = (RE_UINT32)re_numeric_value_stage_1[f] << 4;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_numeric_value_stage_2[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_numeric_value_stage_3[pos + f] << 3;
    f = code >> 2;
    code ^= f << 2;
    pos = (RE_UINT32)re_numeric_value_stage_4[pos + f] << 2;
    value = re_numeric_value_stage_5[pos + code];

    return value;
}

/* Bidi_Mirrored. */

static RE_UINT8 re_bidi_mirrored_stage_1[] = {
    0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2,
};

static RE_UINT8 re_bidi_mirrored_stage_2[] = {
    0, 1, 2, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5,
    4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 6, 4, 4,
    4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
};

static RE_UINT8 re_bidi_mirrored_stage_3[] = {
     0,  1,  1,  1,  1,  1,  1,  2,  1,  1,  1,  3,  1,  1,  1,  1,
     4,  5,  1,  6,  7,  8,  1,  9, 10,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1, 11,
     1,  1,  1, 12,  1,  1,  1,  1,
};

static RE_UINT8 re_bidi_mirrored_stage_4[] = {
     0,  1,  2,  3,  3,  3,  3,  3,  3,  3,  3,  3,  3,  3,  3,  3,
     3,  3,  3,  3,  4,  3,  3,  3,  3,  3,  5,  3,  3,  3,  3,  3,
     6,  7,  8,  3,  3,  9,  3,  3, 10, 11, 12, 13, 14,  3,  3,  3,
     3,  3,  3,  3,  3, 15,  3, 16,  3,  3,  3,  3,  3,  3, 17, 18,
    19, 20, 21, 22,  3,  3,  3,  3, 23,  3,  3,  3,  3,  3,  3,  3,
    24,  3,  3,  3,  3,  3,  3,  3,  3, 25,  3,  3, 26, 27,  3,  3,
     3,  3,  3, 28, 29, 30, 31, 32,
};

static RE_UINT8 re_bidi_mirrored_stage_5[] = {
      0,   0,   0,   0,   0,   3,   0,  80,   0,   0,   0,  40,   0,   0,   0,  40,
      0,   0,   0,   0,   0,   8,   0,   8,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,  60,   0,   0,   0,  24,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   6,  96,   0,   0,   0,   0,   0,   0,  96,
      0,  96,   0,   0,   0,   0,   0,   0,   1,   0,   0,   0,   0,   0,   0,   0,
     30,  63,  98, 188,  87, 248,  15, 250, 255,  31,  60, 128, 245, 207, 255, 255,
    255, 159,   7,   1, 204, 255, 255, 193,   0,  62, 195, 255, 255,  63, 255, 255,
      0,  15,   0,   0,   3,   6,   0,   0,   0,   0,   0,   0,   0, 255,  63,   0,
    121,  59, 120, 112, 252, 255,   0,   0, 248, 255, 255, 249, 255, 255,   0,   1,
     63, 194,  55,  31,  58,   3, 240,  51,   0, 252, 255, 223,  83, 122,  48, 112,
      0,   0, 128,   1,  48, 188,  25, 254, 255, 255, 255, 255, 207, 191, 255, 255,
    255, 255, 127,  80, 124, 112, 136,  47,  60,  54,   0,  48, 255,   3,   0,   0,
      0, 255, 243,  15,   0,   0,   0,   0,   0,   0,   0, 126,  48,   0,   0,   0,
      0,   3,   0,  80,   0,   0,   0,  40,   0,   0,   0, 168,  13,   0,   0,   0,
      0,   0,   0,   8,   0,   0,   0,   0,   0,   0,  32,   0,   0,   0,   0,   0,
      0, 128,   0,   0,   0,   0,   0,   0,   0,   2,   0,   0,   0,   0,   0,   0,
      8,   0,   0,   0,   0,   0,   0,   0,
};

/* Bidi_Mirrored: 489 bytes. */

RE_UINT32 re_get_bidi_mirrored(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_bidi_mirrored_stage_1[f] << 4;
    f = code >> 12;
    code ^= f << 12;
    pos = (RE_UINT32)re_bidi_mirrored_stage_2[pos + f] << 3;
    f = code >> 9;
    code ^= f << 9;
    pos = (RE_UINT32)re_bidi_mirrored_stage_3[pos + f] << 3;
    f = code >> 6;
    code ^= f << 6;
    pos = (RE_UINT32)re_bidi_mirrored_stage_4[pos + f] << 6;
    pos += code;
    value = (re_bidi_mirrored_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Indic_Positional_Category. */

static RE_UINT8 re_indic_positional_category_stage_1[] = {
    0, 1, 1, 1, 1, 2, 1, 1, 3, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1,
};

static RE_UINT8 re_indic_positional_category_stage_2[] = {
     0,  0,  0,  0,  0,  0,  0,  0,  0,  1,  2,  3,  4,  5,  6,  7,
     8,  0,  0,  0,  0,  0,  0,  9,  0, 10, 11, 12, 13,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0, 14, 15, 16, 17,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 18,  0,  0,  0,  0,  0,
    19, 20, 21, 22, 23, 24, 25, 26,  0,  0,  0,  0,  0,  0,  0,  0,
};

static RE_UINT8 re_indic_positional_category_stage_3[] = {
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      1,   0,   0,   2,   3,   4,   5,   0,   6,   0,   0,   7,   8,   9,   5,   0,
     10,   0,   0,   7,  11,   0,   0,  12,  10,   0,   0,   7,  13,   0,   5,   0,
      6,   0,   0,  14,  15,  16,   5,   0,  17,   0,   0,  18,  19,   9,   0,   0,
     20,   0,   0,  21,  22,  23,   5,   0,   6,   0,   0,  14,  24,  25,   5,   0,
      6,   0,   0,  18,  26,   9,   5,   0,  27,   0,   0,   0,  28,  29,   0,  27,
      0,   0,   0,  30,  31,   0,   0,   0,   0,   0,   0,  32,  33,   0,   0,   0,
      0,  34,   0,  35,   0,   0,   0,  36,  37,  38,  39,  40,  41,   0,   0,   0,
      0,   0,  42,  43,   0,  44,  45,  46,  47,  48,   0,   0,   0,   0,   0,   0,
      0,  49,   0,  49,   0,  50,   0,  50,   0,   0,   0,  51,  52,  53,   0,   0,
      0,   0,  54,  55,   0,   0,   0,   0,   0,   0,   0,  56,  57,   0,   0,   0,
      0,  58,   0,   0,   0,  59,  60,  61,   0,   0,   0,   0,   0,   0,   0,   0,
     62,   0,   0,  63,  64,   0,  65,  66,  67,   0,  68,   0,   0,   0,  69,  70,
      0,   0,  71,  72,   0,   0,   0,   0,   0,   0,   0,   0,   0,  73,  74,  75,
     76,   0,  77,   0,   0,   0,   0,   0,  78,   0,   0,  79,  80,   0,  81,  82,
      0,   0,  83,   0,  84,  70,   0,   0,   1,   0,   0,  85,  86,   0,  87,   0,
      0,   0,  88,  89,  90,   0,   0,  91,   0,   0,   0,  92,  93,   0,  94,  95,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  96,   0,
     97,   0,   0,  98,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
     99,   0,   0, 100, 101,   0,   0,   0,  67,   0,   0, 102,   0,   0,   0,   0,
    103,   0, 104, 105,   0,   0,   0, 106,  67,   0,   0, 107, 108,   0,   0,   0,
      0,   0, 109, 110,   0,   0,   0,   0,   0,   0,   0,   0,   0, 111, 112,   0,
      6,   0,   0,  18, 113,   9, 114, 115,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 116, 117,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 118, 119, 120, 121,   0,   0,
      0,   0,   0, 122, 123,   0,   0,   0,   0,   0, 124, 125,   0,   0,   0,   0,
      0, 126, 127,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
};

static RE_UINT8 re_indic_positional_category_stage_4[] = {
     0,  0,  0,  0,  0,  0,  0,  0,  1,  2,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  2,  3,  4,  5,  6,  7,  1,  2,  8,  5,  9,
    10,  7,  1,  6,  0,  0,  0,  0,  0,  6,  0,  0,  0,  0,  0,  0,
    10,  8,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  3,  4,
     5,  6,  3, 11, 12, 13, 14,  0,  0,  0,  0, 15,  0,  0,  0,  0,
    10,  2,  0,  0,  0,  0,  0,  0,  5,  3,  0, 10, 16, 10, 17,  0,
     1,  0, 18,  0,  0,  0,  0,  0,  5,  6,  7, 10, 19, 15,  5,  0,
     0,  0,  0,  0,  0,  0,  3, 20,  5,  6,  3, 11, 21, 13, 22,  0,
     0,  0,  0, 19,  0,  0,  0,  0,  0, 16,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  8,  2, 23,  0, 24, 12, 25, 26,  0,
     2,  8,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  1,
     2,  8, 23,  1, 27,  1,  1,  0,  0,  0, 10,  3,  0,  0,  0,  0,
    28,  8, 23, 19, 29, 30,  1,  0,  0,  0, 15, 23,  0,  0,  0,  0,
     8,  5,  3, 24, 12, 25, 26,  0,  0,  8,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0, 16,  0, 15,  8,  1,  3,  3,  4, 31, 32, 33,
    20,  8,  1,  1,  6,  3,  0,  0, 34, 34, 35, 10,  1,  1,  1, 16,
    20,  8,  1,  1,  6, 10,  3,  0, 34, 34, 36,  0,  1,  1,  1,  0,
     0,  0,  0,  0,  6,  0,  0,  0,  0,  0, 18, 18, 10,  0,  0,  4,
    18, 37,  6, 38, 38,  1,  1,  2, 37,  1,  3,  1,  0,  0, 18,  6,
     6,  6,  6,  6, 18,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     6,  6,  6,  6,  6,  6,  3,  0,  0,  0,  0,  3,  0,  0,  0,  0,
     0,  0,  0,  0,  0, 15, 20, 17, 39,  1,  1, 17, 23,  2, 18,  3,
     0,  0,  0,  8,  6,  0,  0,  6,  3,  8, 23, 15,  8,  8,  8,  0,
    10,  1, 16,  0,  0,  0,  0,  0,  0, 40, 41,  2,  8,  8,  5, 15,
     0,  0,  0,  0,  0,  8, 20,  0,  0, 17,  3,  0,  0,  0,  0,  0,
     0, 17,  0,  0,  0,  0,  0,  0,  0,  0,  0, 20,  1, 17,  6, 42,
    43, 24, 25,  2, 20,  1,  1,  1,  1, 10,  0,  0,  0,  0, 10,  0,
     1, 40, 44, 45,  2,  8,  0,  0,  8, 40,  8,  8,  5, 17,  0,  0,
     8,  8, 46, 34,  8, 35,  8,  8, 23,  0,  0,  0,  8,  0,  0,  0,
     0,  0,  0, 10, 39, 20,  0,  0,  0,  0, 11, 40,  1, 17,  6,  3,
    15,  2, 20,  1, 17,  7, 40, 24, 24, 41,  1,  1,  1,  1, 16, 18,
     1,  1, 23,  0,  0,  0,  0,  0,  0,  0,  2,  1,  6, 47, 48, 24,
    25, 19, 23,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 10,  7,  1,
     1,  1,  0,  0,  0,  0,  0,  0,  1, 23,  0,  0,  0,  0,  0,  0,
    15,  6, 17,  9,  1, 23,  6,  0,  0,  0,  0,  2,  1,  8, 20, 20,
     1,  8,  0,  0,  0,  0,  0,  0,  0,  0,  8,  4, 49,  8,  7,  1,
     1,  1, 24, 17,  0,  0,  0,  0,  1, 16, 50,  6,  6,  1,  6,  6,
     2, 51, 51, 51, 52,  0, 18,  0,  0,  0, 16,  0,  0,  0,  0,  0,
     0,  0,  0, 16,  0, 10,  0,  0,  0, 15,  5,  2,  0,  0,  0,  0,
     8,  0,  0,  0,  0,  0,  0,  0,  0,  0,  8,  8,  8,  8,  8,  8,
     8,  8,  3,  0,  0,  0,  0,  0,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 18,  6,  0,
     0,  0,  0, 18,  6, 17,  6,  7,  0, 10,  8,  1,  6, 24,  2,  8,
    53,  0,  0,  0,  0,  0,  0,  0,  0,  0, 10,  0,  0,  0,  0,  0,
     0,  0,  0,  0, 10,  1, 17, 54, 41, 40, 55,  3,  0,  0,  0,  0,
     0, 10,  0,  0,  0,  0,  2,  0,  0,  0,  0,  0,  0, 15,  2,  0,
     2,  1, 56, 57, 58, 46, 35,  1, 10,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0, 11,  7,  9,  0,  0, 15,  0,  0,  0,  0,  0,
     0, 15, 20,  8, 40, 23,  5,  0, 59,  6, 10, 52,  0,  0,  6,  7,
     0,  0,  0,  0, 17,  3,  0,  0, 20, 23,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  1,  1,  6,  6,  6,  1,  1, 16,  0,  0,  0,  0,
     4,  5,  7,  2,  5,  3,  0,  0,  1, 16,  0,  0,  0,  0,  0,  0,
     0,  0,  0, 10,  1,  6, 41, 38, 17,  3, 16,  0,  0,  0,  0,  0,
     0, 18,  0,  0,  0,  0,  0,  0,  0, 15,  9,  6,  6,  6,  1, 19,
    23,  0,  0,  0,  0, 10,  3,  0,  0,  0,  0,  0,  0,  0,  8,  5,
     1, 30,  2,  1,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 10,
     4,  5,  7,  1, 17,  3,  0,  0,  2,  8, 23, 11, 12, 13, 33,  0,
     0,  8,  0,  1,  1,  1, 16,  0,  1,  1, 16,  0,  0,  0,  0,  0,
     4,  5,  6,  6, 39, 60, 33, 26,  2,  6,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0, 15,  9,  6,  6,  0, 49, 32,  1,  5,
     3,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  6,  0,
     8,  5,  6,  6,  7,  2, 20,  5, 16,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0, 10, 20,  9,  6,  1,  1,  5,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0, 18, 10,  8,  1,  6, 41,  7,  1,  0,  0,
};

static RE_UINT8 re_indic_positional_category_stage_5[] = {
     0,  0,  5,  5,  5,  1,  6,  0,  1,  2,  1,  6,  6,  6,  6,  5,
     1,  1,  2,  1,  0,  5,  0,  2,  2,  0,  0,  4,  4,  6,  0,  1,
     5,  0,  5,  6,  0,  6,  5,  8,  1,  5,  9,  0, 10,  6,  1,  0,
     2,  2,  4,  4,  4,  5,  7,  0,  8,  1,  8,  0,  8,  8,  9,  2,
     4, 10,  4,  1,  3,  3,  3,  1,  3,  0,  5,  7,  7,  7,  6,  2,
     6,  1,  2,  5,  9, 10,  4,  2,  1,  8,  8,  5,  1,  3,  6, 11,
     7, 12,  2,  9, 13,  6, 13, 13, 13,  0, 11,  0,  5,  2,  2,  6,
     6,  3,  3,  5,  5,  3,  0, 13,  5,  9,
};

/* Indic_Positional_Category: 1842 bytes. */

RE_UINT32 re_get_indic_positional_category(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 13;
    code = ch ^ (f << 13);
    pos = (RE_UINT32)re_indic_positional_category_stage_1[f] << 5;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_indic_positional_category_stage_2[pos + f] << 4;
    f = code >> 4;
    code ^= f << 4;
    pos = (RE_UINT32)re_indic_positional_category_stage_3[pos + f] << 3;
    f = code >> 1;
    code ^= f << 1;
    pos = (RE_UINT32)re_indic_positional_category_stage_4[pos + f] << 1;
    value = re_indic_positional_category_stage_5[pos + code];

    return value;
}

/* Indic_Syllabic_Category. */

static RE_UINT8 re_indic_syllabic_category_stage_1[] = {
    0, 1, 2, 2, 2, 3, 2, 2, 4, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2,
};

static RE_UINT8 re_indic_syllabic_category_stage_2[] = {
     0,  1,  1,  1,  1,  1,  1,  1,  1,  2,  3,  4,  5,  6,  7,  8,
     9,  1,  1,  1,  1,  1,  1, 10,  1, 11, 12, 13, 14,  1,  1,  1,
    15,  1,  1,  1,  1, 16,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1, 17, 18, 19, 20,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1, 21,  1,  1,  1,  1,  1,
    22, 23, 24, 25, 26, 27, 28, 29,  1,  1,  1,  1,  1,  1,  1,  1,
};

static RE_UINT8 re_indic_syllabic_category_stage_3[] = {
      0,   0,   1,   2,   0,   0,   0,   0,   0,   0,   3,   4,   0,   5,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      6,   7,   8,   9,  10,  11,  12,  13,  14,  15,  16,  17,  18,  19,  12,  20,
     21,  15,  16,  22,  23,  24,  25,  26,  27,  28,  16,  29,  30,   0,  12,  31,
     14,  15,  16,  29,  32,  33,  12,  34,  35,  36,  37,  38,  39,  40,  25,   0,
     41,  42,  16,  43,  44,  45,  12,   0,  46,  42,  16,  47,  44,  48,  12,  49,
     46,  42,   8,  50,  51,  52,  12,  53,  54,  55,   8,  56,  57,  58,  25,  59,
     60,   8,  61,  62,  63,   2,   0,   0,  64,  65,  66,  67,  68,  69,   0,   0,
      0,   0,  70,  71,  72,   8,  73,  74,  75,  76,  77,  78,  79,   0,   0,   0,
      8,   8,  80,  81,  82,  83,  84,  85,  86,  87,   0,   0,   0,   0,   0,   0,
     88,  89,  90,  89,  90,  91,  88,  92,   8,   8,  93,  94,  95,  96,   2,   0,
     97,  61,  98,  99,  25,   8, 100, 101,   8,   8, 102, 103, 104,   2,   0,   0,
      8, 105,   8,   8, 106, 107, 108, 109,   2,   2,   0,   0,   0,   0,   0,   0,
    110,  90,   8, 111, 112,   2,   0,   0, 113,   8, 114, 115,   8,   8, 116, 117,
      8,   8, 118, 119, 120,   0,   0,   0,   0,   0,   0,   0,   0, 121, 122, 123,
    124, 125,   0,   0,   0,   0,   0, 126, 127,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 128,   0,   0,   0,
    129,   8, 130,   0,   8, 131, 132, 133, 134, 135,   8, 136, 137,   2, 138, 122,
    139,   8, 140,   8, 141, 142,   0,   0, 143,   8,   8, 144, 145,   2, 146, 147,
    148,   8, 149, 150, 151,   2,   8, 152,   8,   8,   8, 153, 154,   0, 155, 156,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 157, 158, 159,   2,
    160, 161,   8, 162, 163,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
    164,  90,   8, 165, 166, 167, 168, 169, 170,   8,   8, 171,   0,   0,   0,   0,
    172,   8, 173, 174,   0, 175,   8, 176, 177, 178,   8, 179, 180,   2, 181, 182,
    183, 184, 185, 186,   0,   0,   0,   0, 187, 188, 189, 190,   8, 191, 192,   2,
    193,  15,  16,  29,  32,  40, 194, 195,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0, 196,   8,   8, 197, 198,   2,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0, 199,   8, 200, 201, 202, 203,   0,   0,
    199,   8,   8, 204, 205,   2,   0,   0, 190,   8, 206, 207,   2,   0,   0,   0,
      8, 208, 209, 210,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
};

static RE_UINT8 re_indic_syllabic_category_stage_4[] = {
      0,   0,   0,   0,   0,   0,   0,   1,   2,   2,   3,   0,   4,   0,   0,   0,
      5,   0,   0,   0,   0,   6,   0,   0,   7,   8,   8,   8,   8,   9,  10,  10,
     10,  10,  10,  10,  10,  10,  11,  12,  13,  13,  13,  14,  15,  16,  10,  10,
     17,  18,   2,   2,  19,   8,  10,  10,  20,  21,   8,  22,  22,   9,  10,  10,
     10,  10,  23,  10,  24,  25,  26,  12,  13,  27,  27,  28,   0,  29,   0,  30,
     26,   0,   0,   0,  20,  21,  31,  32,  23,  33,  26,  34,  35,  29,  27,  36,
      0,   0,  37,  24,   0,  18,   2,   2,  38,  39,   0,   0,  20,  21,   8,  40,
     40,   9,  10,  10,  23,  37,  26,  12,  13,  41,  41,  36,   0,   0,  42,   0,
     13,  27,  27,  36,   0,  43,   0,  30,  42,   0,   0,   0,  44,  21,  31,  19,
     45,  46,  33,  23,  47,  48,  49,  25,  10,  10,  26,  43,  35,  43,  50,  36,
      0,  29,   0,   0,   7,  21,   8,  45,  45,   9,  10,  10,  10,  10,  26,  51,
     13,  50,  50,  36,   0,  52,  49,   0,  20,  21,   8,  45,  10,  37,  26,  12,
      0,  52,   0,  53,  54,   0,   0,   0,  10,  10,  49,  51,  13,  50,  50,  55,
      0,  29,   0,  32,   0,   0,  56,  57,  58,  21,   8,   8,   8,  31,  25,  10,
     30,  10,  10,  42,  10,  49,  59,  29,  13,  60,  13,  13,  43,   0,   0,   0,
     37,  10,  10,  10,  10,  10,  10,  49,  13,  13,  61,   0,  13,  41,  62,  63,
     33,  64,  24,  42,   0,  10,  37,  10,  37,  65,  25,  33,  13,  13,  41,  66,
     13,  67,  62,  68,   2,   2,   3,  10,   2,   2,   2,   2,   2,  69,  70,   0,
     10,  10,  37,  10,  10,  10,  10,  48,  16,  13,  13,  71,  72,  73,  74,  75,
     76,  76,  77,  76,  76,  76,  76,  76,  76,  76,  76,  78,   0,  79,   0,   0,
     80,   8,  81,  13,  13,  82,  83,  84,   2,   2,   3,  85,  86,  17,  87,  88,
     89,  90,  91,  92,  93,  94,  10,  10,  95,  96,  62,  97,   2,   2,  98,  99,
    100,  10,  10,  23,  11, 101,   0,   0, 100,  10,  10,  10,  11,   0,   0,   0,
    102,   0,   0,   0, 103,   8,   8,   8,   8,  43,  13,  13,  13,  71, 104, 105,
    106,   0,   0, 107, 108,  10,  10,  10,  13,  13, 109,   0, 110, 111, 112,   0,
    113, 114, 114, 115, 116, 117,   0,   0,  10,  10,  10,   0,  13,  13,  13,  13,
    118, 111, 119,   0,  10, 120,  13,   0,  10,  10,  10,  80, 100, 121, 111, 122,
    123,  13,  13,  13,  13,  91, 124, 125, 126, 127,   8,   8,  10, 128,  13,  13,
     13, 129,  10,   0, 130,   8, 131,  10, 132,  13, 133, 134,   2,   2, 135, 136,
     10, 137,  13,  13, 138,   0,   0,   0,  10, 139,  13, 118, 111, 140,   0,   0,
      2,   2,   3,  37, 141, 142, 142, 142, 143,   0,   0,   0, 144, 145, 143,   0,
      0,   0,   0, 146, 147,   4,   0,   0,   0, 148,   0,   0,   5, 148,   0,   0,
      0,   0,   0,   4,  40, 149, 150,  10, 120,  13,   0,   0,  10,  10,  10, 151,
    152, 153, 154,  10, 155,   0,   0,   0, 156,   8,   8,   8, 131,  10,  10,  10,
     10, 157,  13,  13,  13, 158,   0,   0, 142, 142, 142, 142,   2,   2, 159,  10,
    151, 114, 160, 119,  10, 120,  13, 161, 162,   0,   0,   0, 163,   8,   9, 100,
    164,  13,  13, 165, 158,   0,   0,   0,  10, 166,  10,  10,   2,   2, 159,  49,
      8, 131,  10,  10,  10,  10,  93,  13, 167, 168,   0,   0, 111, 111, 111, 169,
     37,   0, 170,  92,  13,  13,  13,  96, 171,   0,   0,   0, 131,  10, 120,  13,
      0, 172,   0,   0,  10,  10,  10,  86, 173,  10, 174, 111, 175,  13,  35, 176,
     93,  52,   0,  71,  10,  37,  37,  10,  10,   0, 177, 178,   2,   2,   0,   0,
    179, 180,   8,   8,  10,  10,  13,  13,  13, 181,   0,   0, 182, 183, 183, 183,
    183, 184,   2,   2,   0,   0,   0, 185, 186,   8,   8,   9,  13,  13, 187,   0,
    186, 100,  10,  10,  10, 120,  13,  13, 188, 189,   2,   2, 114, 190,  10,  10,
    164,   0,   0,   0, 186,   8,   8,   8,   9,  10,  10,  10, 120,  13,  13,  13,
    191,   0, 192,  67, 193,   2,   2,   2,   2, 194,   0,   0,   8,   8,  10,  10,
     30,  10,  10,  10,  10,  10,  10,  13,  13, 195,   0,   0,   8,  49,  23,  30,
     10,  10,  10,  30,  10,  10,  48,   0,   8,   8, 131,  10,  10,  10,  10, 150,
     13,  13, 196,   0,   7,  21,   8,  22,  17, 197, 142, 145, 142, 145,   0,   0,
     21,   8,   8, 100,  13,  13,  13, 198, 199, 107,   0,   0,   8,   8,   8, 131,
     10,  10,  10, 120,  13,  99,  13, 200, 201,   0,   0,   0,   0,   0,   8,  99,
     13,  13,  13, 202,  67,   0,   0,   0,  10,  10, 150, 203,  13, 204,   0,   0,
     10,  10,  26, 205,  13,  13, 206,   0,   2,   2,   2,   0,
};

static RE_UINT8 re_indic_syllabic_category_stage_5[] = {
     0,  0,  0,  0,  0, 11,  0,  0, 33, 33, 33, 33, 33, 33,  0,  0,
    11,  0,  0,  0,  0,  0, 28, 28,  0,  0,  0, 11,  1,  1,  1,  2,
     8,  8,  8,  8,  8, 12, 12, 12, 12, 12, 12, 12, 12, 12,  9,  9,
     4,  3,  9,  9,  9,  9,  9,  9,  9,  5,  9,  9,  0, 26, 26,  0,
     0,  9,  9,  9,  8,  8,  9,  9,  0,  0, 33, 33,  0,  0,  8,  8,
     0,  1,  1,  2,  0,  8,  8,  8,  8,  0,  0,  8, 12,  0, 12, 12,
    12,  0, 12,  0,  0,  0, 12, 12, 12, 12,  0,  0,  9,  0,  0,  9,
     9,  5, 13,  0,  0,  0,  0,  9, 12, 12,  0, 12,  8,  8,  8,  0,
     0,  0,  0,  8,  0, 12, 12,  0,  4,  0,  9,  9,  9,  9,  9,  0,
     9,  5,  0,  0,  0, 12, 12, 12,  1, 25, 11, 11,  0, 19,  0,  0,
     8,  8,  0,  8,  9,  9,  0,  9,  0, 12,  0,  0,  0,  0,  9,  9,
     0,  0,  1, 22,  8,  0,  8,  8,  8, 12,  0,  0,  0,  0,  0, 12,
    12,  0,  0,  0, 12, 12, 12,  0,  9,  0,  9,  9,  0,  3,  9,  9,
     0,  9,  9,  0,  0,  0, 12,  0,  0, 14, 14,  0,  9,  5, 16,  0,
     0,  0, 13, 13, 13, 13, 13, 13,  0,  0,  1,  2,  0,  0,  5,  0,
     9,  0,  9,  0,  9,  9,  6,  0, 24, 24, 24, 24, 29,  1,  6,  0,
    12,  0,  0, 12,  0, 12,  0, 12, 19, 19,  0,  0,  9,  0,  0,  0,
     0,  1,  0,  0,  0, 28,  0, 28,  0,  4,  0,  0,  9,  9,  1,  2,
     9,  9,  1,  1,  6,  3,  0,  0, 21, 21, 21, 21, 21, 18, 18, 18,
    18, 18, 18, 18,  0, 18, 18, 18, 18,  0,  0,  0,  0,  0, 28,  0,
    12,  8,  8,  8,  8,  8,  8,  9,  9,  9,  1, 24,  2,  7,  6, 19,
    19, 19, 19, 12,  0,  0, 11,  0, 12, 12,  8,  8,  9,  9, 12, 12,
    12, 12, 19, 19, 19, 12,  9, 24, 24, 12, 12,  9,  9, 24, 24, 24,
    24, 24, 12, 12, 12,  9,  9,  9,  9, 12, 12, 12, 12, 12, 19,  9,
     9,  9,  9, 24, 24, 24, 12, 24, 33, 33, 24, 24,  9,  9,  0,  0,
     8,  8,  8, 12,  6,  0,  0,  0, 12,  0,  9,  9, 12, 12, 12,  8,
     9, 27, 27, 28, 17, 29, 28, 28, 28,  6,  7, 28,  3,  0,  0,  0,
    11, 12, 12, 12,  9, 18, 18, 18, 20, 20,  1, 20, 20, 20, 20, 20,
    20, 20,  9, 28, 12, 12, 12, 10, 10, 10, 10, 10, 10, 10,  0,  0,
    23, 23, 23, 23, 23,  0,  0,  0,  9, 20, 20, 20, 24, 24,  0,  0,
    12, 12, 12,  9, 12, 19, 19, 20, 20, 20, 20,  0,  7,  9,  9,  9,
    24, 24, 28, 28, 28,  0,  0, 28,  1,  1,  1, 17,  2,  8,  8,  8,
     4,  9,  9,  9,  5, 12, 12, 12,  1, 17,  2,  8,  8,  8, 12, 12,
    12, 18, 18, 18,  9,  9,  6,  7, 18, 18, 12, 12, 33, 33,  3, 12,
    12, 12, 20, 20,  8,  8,  4,  9, 20, 20,  6,  6, 18, 18,  9,  9,
     1,  1, 28,  4, 26, 26, 26,  0, 26, 26, 26, 26, 26, 26,  0,  0,
     0,  0,  2,  2, 26,  0,  0,  0, 30, 31,  0,  0, 11, 11, 11, 11,
    28,  0,  0,  0,  8,  8,  6, 12, 12, 12, 12,  1, 12, 12, 10, 10,
    10, 10, 12, 12, 12, 12, 10, 18, 18, 12, 12, 12, 12, 18, 12,  1,
     1,  2,  8,  8, 20,  9,  9,  9,  5,  0,  0,  0, 33, 33, 12, 12,
    10, 10, 10, 24,  9,  9,  9, 20, 20, 20, 20,  6,  1,  1, 17,  2,
    12, 12, 12,  4,  9, 18, 19, 19, 12,  9,  0, 12,  9,  9,  9, 19,
    19, 19, 19,  0, 20, 20,  0,  0,  0,  0, 12, 24, 23, 24, 23,  0,
     0,  2,  7,  0, 12,  8, 12, 12, 12, 12, 12, 20, 20, 20, 20,  9,
    24,  6,  0,  0,  4,  4,  4,  0,  0,  0,  0,  7,  1,  1,  2, 14,
    14,  8,  8,  8,  9,  9,  5,  0,  0,  0, 34, 34, 34, 34, 34, 34,
    34, 34, 33, 33,  0,  0,  0, 32,  1,  1,  2,  8,  9,  5,  4,  0,
     9,  9,  9,  7,  6,  0, 33, 33, 10, 12, 12, 12,  5,  3, 15, 15,
     0,  0,  4,  9,  0, 33, 33, 33, 33,  0,  0,  0,  1,  5,  4, 25,
     9,  4,  6,  0,  0,  0, 26, 26,  9,  9,  9,  1,  1,  2,  5,  4,
     1,  1,  2,  5,  4,  0,  0,  0,  9,  1,  2,  5,  2,  9,  9,  9,
     9,  9,  5,  4,  0, 19, 19, 19,  9,  9,  9,  6,
};

/* Indic_Syllabic_Category: 2448 bytes. */

RE_UINT32 re_get_indic_syllabic_category(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 13;
    code = ch ^ (f << 13);
    pos = (RE_UINT32)re_indic_syllabic_category_stage_1[f] << 5;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_indic_syllabic_category_stage_2[pos + f] << 4;
    f = code >> 4;
    code ^= f << 4;
    pos = (RE_UINT32)re_indic_syllabic_category_stage_3[pos + f] << 2;
    f = code >> 2;
    code ^= f << 2;
    pos = (RE_UINT32)re_indic_syllabic_category_stage_4[pos + f] << 2;
    value = re_indic_syllabic_category_stage_5[pos + code];

    return value;
}

/* Alphanumeric. */

static RE_UINT8 re_alphanumeric_stage_1[] = {
    0, 1, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
    3,
};

static RE_UINT8 re_alphanumeric_stage_2[] = {
     0,  1,  2,  3,  4,  5,  6,  7,  7,  8,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  9, 10, 11,  7,  7,  7,  7, 12, 13, 13, 13, 13, 14,
    15, 16, 17, 18, 19, 13, 20, 13, 21, 13, 13, 13, 13, 22, 13, 13,
    13, 13, 13, 13, 13, 13, 23, 24, 13, 13, 25, 13, 13, 26, 27, 13,
     7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  7, 28,  7, 29, 30,  7, 31, 13, 13, 13, 13, 13, 32,
    13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13,
    13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13,
};

static RE_UINT8 re_alphanumeric_stage_3[] = {
     0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15,
    16,  1, 17, 18, 19,  1, 20, 21, 22, 23, 24, 25, 26, 27,  1, 28,
    29, 30, 31, 31, 32, 31, 31, 31, 31, 31, 31, 31, 33, 34, 35, 31,
    36, 37, 31, 31,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1, 38,  1,  1,  1,  1,  1,  1,  1,  1,  1, 39,
     1,  1,  1,  1, 40,  1, 41, 42, 43, 44, 45, 46,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1, 47, 31, 31, 31, 31, 31, 31, 31, 31,
    31,  1, 48, 49,  1, 50, 51, 52, 53, 54, 55, 56, 57, 58,  1, 59,
    60, 61, 62, 63, 64, 31, 31, 31, 65, 66, 67, 68, 69, 70, 71, 72,
    73, 31, 74, 31, 31, 31, 31, 31,  1,  1,  1, 75, 76, 77, 31, 31,
     1,  1,  1,  1, 78, 31, 31, 31, 31, 31, 31, 31,  1,  1, 79, 31,
     1,  1, 80, 81, 31, 31, 31, 82, 83, 31, 31, 31, 31, 31, 31, 31,
    31, 31, 31, 31, 84, 31, 31, 31, 31, 31, 31, 31, 85, 86, 87, 88,
    89, 31, 31, 31, 31, 31, 90, 31, 31, 91, 31, 31, 31, 31, 31, 31,
     1,  1,  1,  1,  1,  1, 92,  1,  1,  1,  1,  1,  1,  1,  1, 93,
    94,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1, 95, 31,
     1,  1, 96, 31, 31, 31, 31, 31,
};

static RE_UINT8 re_alphanumeric_stage_4[] = {
      0,   1,   2,   2,   0,   3,   4,   4,   5,   5,   5,   5,   5,   5,   5,   5,
      5,   5,   5,   5,   5,   5,   6,   7,   0,   0,   8,   9,  10,  11,   5,  12,
      5,   5,   5,   5,  13,   5,   5,   5,   5,  14,  15,  16,  17,  18,  19,  20,
     21,   5,  22,  23,   5,   5,  24,  25,  26,   5,  27,   5,   5,  28,   5,  29,
     30,  31,  32,   0,   0,  33,   0,  34,   5,  35,  36,  37,  38,  39,  40,  41,
     42,  43,  44,  45,  46,  47,  48,  49,  50,  47,  51,  52,  53,  54,  55,  56,
     57,  58,  59,  60,  61,  62,  63,  64,  61,  65,  66,  67,  68,  69,  70,  71,
     16,  72,  73,   0,  74,  75,  76,   0,  77,  78,  79,  80,  81,  82,   0,   0,
      5,  83,  84,  85,  86,   5,  87,  88,   5,   5,  89,   5,  90,  91,  92,   5,
     93,   5,  94,   0,  95,   5,   5,  96,  16,   5,   5,   5,   5,   5,   5,   5,
      5,   5,   5,  97,   2,   5,   5,  98,  99, 100, 100, 101,   5, 102, 103,  78,
      1,   5,   5, 104,   5, 105,   5, 106, 107, 108, 109, 110,   5, 111, 112,   0,
    113,   5, 107, 114, 112, 115,   0,   0,   5, 116, 117,   0,   5, 118,   5, 119,
      5, 106, 120, 121,   0,   0,   0, 122,   5,   5,   5,   5,   5,   5,   0, 123,
     96,   5, 124, 121,   5, 125, 126, 127,   0,   0,   0, 128, 129,   0,   0,   0,
    130, 131, 132,   5, 133,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0, 134,   5,  78,   5, 135, 107,   5,   5,   5,   5, 136,
      5,  87,   5, 137, 138, 139, 139,   5,   0, 140,   0,   0,   0,   0,   0,   0,
    141, 142,  16,   5, 143,  16,   5,  88, 144, 145,   5,   5, 146,  72,   0,  26,
      5,   5,   5,   5,   5, 106,   0,   0,   5,   5,   5,   5,   5,   5, 106,   0,
      5,   5,   5,   5,  31,   0,  26, 121, 147, 148,   5, 149,   5,   5,   5,  95,
    150, 151,   5,   5, 152, 153,   0, 150, 154,  17,   5, 100,   5,   5, 155, 156,
      5, 105, 157,  82,   5, 158, 159, 160,   5, 138, 161, 162,   5, 107, 163, 164,
    165, 166,  88, 167,   5,   5,   5, 168,   5,   5,   5,   5,   5, 169, 170, 113,
      5,   5,   5, 171,   5,   5, 172,   0, 173, 174, 175,   5,   5,  28, 176,   5,
      5, 121,  26,   5, 177,   5,  17, 178,   0,   0,   0, 179,   5,   5,   5,  82,
      1,   2,   2, 109,   5, 107, 180,   0, 181, 182, 183,   0,   5,   5,   5,  72,
      0,   0,   5,  33,   0,   0,   0,   0,   0,   0,   0,   0,  82,   5, 184,   0,
      5,  26, 105,  72, 121,   5, 185,   0,   5,   5,   5,   5, 121,  78,   0,   0,
      5, 186,   5, 187,   0,   0,   0,   0,   5, 138, 106,  17,   0,   0,   0,   0,
    188, 189, 106, 138, 107,   0,   0, 190, 106, 172,   0,   0,   5, 191,   0,   0,
    192, 100,   0,  82,  82,   0,  79, 193,   5, 106, 106, 157,  28,   0,   0,   0,
      5,   5, 133,   0,   5, 157,   5, 157,   5,   5, 194,  56, 151,  32,  26, 195,
      5, 196,  26, 197,   5,   5, 198,   0, 199, 200,   0,   0, 201, 202,   5, 195,
     38,  47, 203, 187,   0,   0,   0,   0,   0,   0,   0,   0,   5,   5, 204,   0,
      0,   0,   0,   0,   5, 205, 206,   0,   5, 107, 207,   0,   5, 106,  78,   0,
    208, 168,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   5,   5, 209,
      0,   0,   0,   0,   0,   0,   5,  32,   5,   5,   5,   5, 172,   0,   0,   0,
      5,   5,   5, 146,   5,   5,   5,   5,   5,   5, 187,   0,   0,   0,   0,   0,
      5, 146,   0,   0,   0,   0,   0,   0,   5,   5, 210,   0,   0,   0,   0,   0,
      5,  32, 107,  78,   0,   0,  26, 211,   5, 138, 155, 212,  95,   0,   0,   0,
      5,   5, 213, 107, 176,   0,   0,   0, 214,   0,   0,   0,   0,   0,   0,   0,
      5,   5,   5, 215, 216,   0,   0,   0,   5,   5, 217,   5, 218, 219, 220,   5,
    221, 222, 223,   5,   5,   5,   5,   5,   5,   5,   5,   5,   5, 224, 225,  88,
    217, 217, 135, 135, 226, 226, 227,   5,   5,   5,   5,   5,   5,   5, 193,   0,
    220, 228, 229, 230, 231, 232,   0,   0,   0,  26,  84,  84,  78,   0,   0,   0,
      5,   5,   5,   5,   5,   5, 138,   0,   5,  33,   5,   5,   5,   5,   5,   5,
    121,   5,   5,   5,   5,   5,   5,   5,   5,   5,   5,   5,   5, 214,   0,   0,
    121,   0,   0,   0,   0,   0,   0,   0,
};

static RE_UINT8 re_alphanumeric_stage_5[] = {
      0,   0,   0,   0,   0,   0, 255,   3, 254, 255, 255,   7,   0,   4,  32,   4,
    255, 255, 127, 255, 255, 255, 255, 255, 195, 255,   3,   0,  31,  80,   0,   0,
     32,   0,   0,   0,   0,   0, 223, 188,  64, 215, 255, 255, 251, 255, 255, 255,
    255, 255, 191, 255,   3, 252, 255, 255, 255, 255, 254, 255, 255, 255, 127,   2,
    254, 255, 255, 255, 255,   0,   0,   0,   0,   0, 255, 191, 182,   0, 255, 255,
    255,   7,   7,   0,   0,   0, 255,   7, 255, 255, 255, 254, 255, 195, 255, 255,
    255, 255, 239,  31, 254, 225, 255, 159,   0,   0, 255, 255,   0, 224, 255, 255,
    255, 255,   3,   0, 255,   7,  48,   4, 255, 255, 255, 252, 255,  31,   0,   0,
    255, 255, 255,   1, 255, 255,  31,   0, 248,   3, 255, 255, 255, 255, 255, 239,
    255, 223, 225, 255, 207, 255, 254, 255, 239, 159, 249, 255, 255, 253, 197, 227,
    159,  89, 128, 176, 207, 255,   3,   0, 238, 135, 249, 255, 255, 253, 109, 195,
    135,  25,   2,  94, 192, 255,  63,   0, 238, 191, 251, 255, 255, 253, 237, 227,
    191,  27,   1,   0, 207, 255,   0,   2, 238, 159, 249, 255, 159,  25, 192, 176,
    207, 255,   2,   0, 236, 199,  61, 214,  24, 199, 255, 195, 199,  29, 129,   0,
    192, 255,   0,   0, 239, 223, 253, 255, 255, 253, 255, 227, 223,  29,  96,   7,
    207, 255,   0,   0, 238, 223, 253, 255, 255, 253, 239, 227, 223,  29,  96,  64,
    207, 255,   6,   0, 255, 255, 255, 231, 223,  93, 128, 128, 207, 255,   0, 252,
    236, 255, 127, 252, 255, 255, 251,  47, 127, 128,  95, 255, 192, 255,  12,   0,
    255, 255, 255,   7, 127,  32, 255,   3, 150,  37, 240, 254, 174, 236, 255,  59,
     95,  32, 255, 243,   1,   0,   0,   0, 255,   3,   0,   0, 255, 254, 255, 255,
    255,  31, 254, 255,   3, 255, 255, 254, 255, 255, 255,  31, 255, 255, 127, 249,
    255,   3, 255, 255, 231, 193, 255, 255, 127,  64, 255,  51, 191,  32, 255, 255,
    255, 255, 255, 247, 255,  61, 127,  61, 255,  61, 255, 255, 255, 255,  61, 127,
     61, 255, 127, 255, 255, 255,  61, 255, 255, 255, 255, 135, 255, 255,   0,   0,
    255, 255,  63,  63, 255, 159, 255, 255, 255, 199, 255,   1, 255, 223,  15,   0,
    255, 255,  15,   0, 255, 223,  13,   0, 255, 255, 207, 255, 255,   1, 128,  16,
    255, 255, 255,   0, 255,   7, 255, 255, 255, 255,  63,   0, 255, 255, 255, 127,
    255,  15, 255,   1, 192, 255, 255, 255, 255,  63,  31,   0, 255,  15, 255, 255,
    255,   3, 255,   3, 255, 255, 255,  15, 254, 255,  31,   0, 128,   0,   0,   0,
    255, 255, 239, 255, 239,  15, 255,   3, 255, 243, 255, 255, 191, 255,   3,   0,
    255, 227, 255, 255, 255, 255, 255,  63,   0, 222, 111,   0, 128, 255,  31,   0,
     63,  63, 255, 170, 255, 255, 223,  95, 220,  31, 207,  15, 255,  31, 220,  31,
      0,   0,   2, 128,   0,   0, 255,  31, 132, 252,  47,  62,  80, 189, 255, 243,
    224,  67,   0,   0, 255,   1,   0,   0,   0,   0, 192, 255, 255, 127, 255, 255,
     31, 120,  12,   0, 255, 128,   0,   0, 255, 255, 127,   0, 127, 127, 127, 127,
      0, 128,   0,   0, 224,   0,   0,   0, 254,   3,  62,  31, 255, 255, 127, 224,
    224, 255, 255, 255, 255,  63, 254, 255, 255, 127,   0,   0, 255,  31, 255, 255,
    255,  15,   0,   0, 255, 127, 240, 143,   0,   0, 128, 255, 252, 255, 255, 255,
    255, 249, 255, 255, 255,  63, 255,   0, 187, 247, 255, 255,  15,   0, 255,   3,
      0,   0, 252,  40, 255, 255,   7,   0, 255, 255, 247, 255,   0, 128, 255,   3,
    223, 255, 255, 127, 255,  63, 255,   3, 255, 255, 127, 196,   5,   0,   0,  56,
    255, 255,  60,   0, 126, 126, 126,   0, 127, 127, 255, 255,  63,   0, 255, 255,
    255,   7, 255,   3,  15,   0, 255, 255, 127, 248, 255, 255, 255,  63, 255, 255,
    255, 255, 255,   3, 127,   0, 248, 224, 255, 253, 127,  95, 219, 255, 255, 255,
      0,   0, 248, 255, 255, 255, 252, 255,   0,   0, 255,  15,   0,   0, 223, 255,
    252, 252, 252,  28, 255, 239, 255, 255, 127, 255, 255, 183, 255,  63, 255,  63,
    255, 255,   1,   0,  15, 255,  62,   0, 255,   0, 255, 255,  15,   0,   0,   0,
     63, 253, 255, 255, 255, 255, 191, 145, 255, 255,  55,   0, 255, 255, 255, 192,
    111, 240, 239, 254,  31,   0,   0,   0,  63,   0,   0,   0, 255,   1, 255,   3,
    255, 255, 199, 255, 255, 255,  71,   0,  30,   0, 255,  23, 255, 255, 251, 255,
    255, 255, 159,   0, 127, 189, 255, 191, 255,   1, 255, 255, 159,  25, 129, 224,
    179,   0, 255,   3, 255, 255,  63, 127,   0,   0,   0,  63,  17,   0, 255,   3,
    255, 255, 255, 227, 255,   3,   0, 128, 127,   0,   0,   0, 255,  63,   0,   0,
    248, 255, 255, 224,  31,   0, 255, 255,   3,   0,   0,   0, 255,   7, 255,  31,
    255,   1, 255,  67, 255, 255, 223, 255, 255, 255, 255, 223, 100, 222, 255, 235,
    239, 255, 255, 255, 191, 231, 223, 223, 255, 255, 255, 123,  95, 252, 253, 255,
     63, 255, 255, 255, 253, 255, 255, 247, 255, 253, 255, 255, 247, 207, 255, 255,
    150, 254, 247,  10, 132, 234, 150, 170, 150, 247, 247,  94, 255, 251, 255,  15,
    238, 251, 255,  15,
};

/* Alphanumeric: 2117 bytes. */

RE_UINT32 re_get_alphanumeric(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_alphanumeric_stage_1[f] << 5;
    f = code >> 11;
    code ^= f << 11;
    pos = (RE_UINT32)re_alphanumeric_stage_2[pos + f] << 3;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_alphanumeric_stage_3[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_alphanumeric_stage_4[pos + f] << 5;
    pos += code;
    value = (re_alphanumeric_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Any. */

RE_UINT32 re_get_any(RE_UINT32 ch) {
    return 1;
}

/* Blank. */

static RE_UINT8 re_blank_stage_1[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1,
};

static RE_UINT8 re_blank_stage_2[] = {
    0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
};

static RE_UINT8 re_blank_stage_3[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1,
    3, 1, 1, 1, 1, 1, 1, 1, 4, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
};

static RE_UINT8 re_blank_stage_4[] = {
    0, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 3, 1, 1, 1, 1, 1, 4, 5, 1, 1, 1, 1, 1, 1,
    3, 1, 1, 1, 1, 1, 1, 1,
};

static RE_UINT8 re_blank_stage_5[] = {
      0,   2,   0,   0,   1,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   1,   0,   0,   0,   1,   0,   0,   0,   0,   0,   0,   0,
    255,   7,   0,   0,   0, 128,   0,   0,   0,   0,   0, 128,   0,   0,   0,   0,
};

/* Blank: 169 bytes. */

RE_UINT32 re_get_blank(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_blank_stage_1[f] << 3;
    f = code >> 13;
    code ^= f << 13;
    pos = (RE_UINT32)re_blank_stage_2[pos + f] << 4;
    f = code >> 9;
    code ^= f << 9;
    pos = (RE_UINT32)re_blank_stage_3[pos + f] << 3;
    f = code >> 6;
    code ^= f << 6;
    pos = (RE_UINT32)re_blank_stage_4[pos + f] << 6;
    pos += code;
    value = (re_blank_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Graph. */

static RE_UINT8 re_graph_stage_1[] = {
    0, 1, 2, 3, 4, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6,
    6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 7, 6, 4, 8,
    4, 8,
};

static RE_UINT8 re_graph_stage_2[] = {
     0,  1,  2,  3,  4,  5,  6,  7,  7,  8,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  9, 10, 11,  7,  7,  7,  7, 12, 13,  7,  7,  7, 14,
    15, 16, 17, 18, 19, 13, 20, 13, 21, 13, 13, 13, 13, 22, 13, 13,
    13, 13, 13, 13, 13, 13, 23, 24, 13, 13, 25, 26, 13, 27, 28, 29,
     7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  7, 30,  7, 31, 32,  7, 33, 13, 13, 13, 13, 13, 34,
    13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13,
    35, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13,
     7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7, 36,
};

static RE_UINT8 re_graph_stage_3[] = {
      0,   1,   1,   2,   1,   3,   4,   5,   6,   7,   8,   9,  10,  11,  12,  13,
     14,   1,  15,  16,   1,   1,  17,  18,  19,  20,  21,  22,  23,  24,   1,  25,
     26,  27,   1,  28,  29,   1,   1,   1,   1,   1,   1,  30,  31,  32,  33,  34,
     35,  36,  37,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,
      1,   1,   1,   1,   1,  38,   1,   1,   1,   1,   1,   1,   1,   1,   1,  39,
      1,   1,   1,   1,  40,   1,  41,  42,  43,  44,  45,  46,   1,   1,   1,   1,
      1,   1,   1,   1,   1,   1,   1,  47,  48,  48,  48,  48,  48,  48,  48,  48,
      1,   1,  49,  50,   1,  51,  52,  53,  54,  55,  56,  57,  58,  59,   1,  60,
     61,  62,  63,  64,  65,  48,  66,  48,  67,  68,  69,  70,  71,  72,  73,  74,
     75,  48,  76,  48,  48,  48,  48,  48,   1,   1,   1,  77,  78,  79,  48,  48,
      1,   1,   1,   1,  80,  48,  48,  48,  48,  48,  48,  48,   1,   1,  81,  48,
      1,   1,  82,  83,  48,  48,  48,  84,  85,  48,  48,  48,  48,  48,  48,  48,
     48,  48,  48,  48,  86,  48,  48,  48,  87,  88,  89,  90,  91,  92,  93,  94,
      1,   1,  95,  48,  48,  48,  48,  48,  96,  48,  48,  48,  48,  48,  97,  48,
     98,  99, 100,   1,   1, 101, 102, 103, 104, 105,  48,  48,  48,  48,  48,  48,
      1,   1,   1,   1,   1,   1, 106,   1,   1,   1,   1,   1,   1,   1,   1, 107,
    108,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1, 109,  48,
      1,   1, 110,  48,  48,  48,  48,  48, 111, 112,  48,  48,  48,  48,  48,  48,
      1,   1,   1,   1,   1,   1,   1, 113,
};

static RE_UINT8 re_graph_stage_4[] = {
      0,   1,   2,   3,   0,   1,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,
      2,   2,   2,   4,   5,   6,   2,   2,   2,   7,   8,   1,   9,   2,  10,  11,
     12,   2,   2,   2,   2,   2,   2,   2,  13,   2,  14,   2,   2,  15,   2,  16,
      2,  17,  18,   0,   0,  19,   0,  20,   2,   2,   2,   2,  21,  22,  23,  24,
     25,  26,  27,  28,  29,  30,  31,  32,  33,  30,  34,  35,  36,  37,  38,  39,
     40,  41,  42,  43,  44,  45,  46,  47,  44,  48,  49,  50,  51,  52,  53,  54,
      1,  55,  56,   0,  57,  58,  59,   0,   2,   2,  60,  61,  62,  12,  63,   0,
      2,   2,   2,   2,   2,   2,  64,   2,   2,   2,  65,   2,  66,  67,  68,   2,
     69,   2,  48,  70,  71,   2,   2,  72,   2,   2,   2,   2,  73,   2,   2,  74,
     75,  76,  77,  78,   2,   2,  79,  80,  81,   2,   2,  82,   2,  83,   2,  84,
      3,  85,  86,  87,   2,  88,  89,   2,  90,   2,   3,  91,  80,  17,   0,   0,
      2,   2,  88,  70,   2,   2,   2,  92,   2,  93,  94,   2,   0,   0,  10,  95,
      2,   2,   2,   2,   2,   2,   2,  96,  72,   2,  97,  79,   2,  98,  99, 100,
    101, 102,   3, 103, 104,   3, 105, 106,   2,   2,   2,   2,  88,   2,   2,   2,
      2,   2,   2,   2,   2,   2,   2,  16,   2, 107, 108,   2,   2,   2,   2,   2,
      2,   2,   2, 109, 110, 111, 112, 113,   2, 114,   3,   2,   2,   2,   2, 115,
      2,  64,   2, 116,  76, 117, 117,   2,   2,   2, 118,   0, 119,   2,   2,  77,
      2,   2,   2,   2,   2,   2,  84, 120,   1,   2,   1,   2,   8,   2,   2,   2,
    121, 122,   2,   2, 114,  16,   2, 123,   3,   2,   2,   2,   2,   2,   2,   3,
      2,   2,   2,   2,   2,  84,   2,   2,   2,   2,   2,   2,   2,   2,  84,   0,
      2,   2,   2,   2, 124,   2, 125,   2,   2, 126,   2,   2,   2,   2,   2,  82,
      2,   2,   2,   2,   2, 127,   0, 128,   2, 129,   2,  82,   2,   2, 130,  79,
      2,   2, 131,  70,   2,   2, 132,   3,   2,  76, 133,   2,   2,   2, 134,  76,
    135, 136,   2, 137,   2,   2,   2, 138,   2,   2,   2,   2,   2, 123, 139,  56,
      0,   0,   0,   0,   0,   0,   0,   0,   2,   2,   2, 140,   2,   2,  71,   0,
    141, 142, 143,   2,   2,   2, 144,   2,   2,   2, 105,   2, 145,   2, 146, 147,
     71,   2, 148, 149,   2,   2,   2,  91,   1,   2,   2,   2,   2,   3, 150, 151,
    152, 153, 154,   0,   2,   2,   2,  16, 155, 156,   2,   2, 157, 158, 105,  79,
      0,   0,   0,   0,  70,   2, 106,  56,   2, 123,  83,  16, 159,   2, 160,   0,
      2,   2,   2,   2,  79, 161,   0,   0,   2,  10,   2, 162,   0,   0,   0,   0,
      2,  76,  84, 146,   0,   0,   0,   0, 163, 164, 165,   2,   3, 166,   0, 167,
    168, 169,   0,   0,   2, 170, 145,   2, 171, 172, 173,   2,   2,   0,   2, 174,
      2, 175, 110, 176, 177, 178,   0,   0,   2,   2, 179,   0,   2, 180,   2, 181,
      0,   0,   0,   3,   0,   0,   0,   0,   2,   2, 182, 183,   2,   2, 184, 185,
      2,  98, 123,  76,   2,   2, 140, 186, 187,  79,   0,   0, 188, 189,   2, 190,
     21,  30, 191, 192,   0,   0,   0,   0,   0,   0,   0,   0,   2,   2, 193,   0,
      0,   0,   0,   0,   2, 110,  79,   0,   2,   2, 194,   0,   2,  82, 161,   0,
    111,  88,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   2,   2, 195,
      0,   0,   0,   0,   0,   0,   2,  74,   2,   2,   2,   2,  71,   0,   0,   0,
      2,   2,   2, 196,   2,   2,   2,   2,   2,   2, 197,   0,   0,   0,   0,   0,
      2, 198,   0,   0,   0,   0,   0,   0,   2,   2, 107,   0,   0,   0,   0,   0,
      2,  74,   3, 199,   0,   0, 105, 200,   2,   2, 201, 202, 203,   0,   0,   0,
      2,   2, 204,   3, 205,   0,   0,   0, 206,   0,   0,   0,   0,   0,   0,   0,
      2,   2,   2, 207, 208, 197,   0,   0,   2,   2,   2,   2,   2,   2,   2,  84,
      2, 209,   2,   2,   2,   2,   2, 179,   2,   2, 210,   0,   0,   0,   0,   0,
      2,   2,  76,  15,   0,   0,   0,   0,   2,   2,  98,   2,  12, 211, 212,   2,
    213, 214, 215,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2, 216,   2,   2,
      2,   2,   2,   2,   2,   2, 217,   2,   2,   2,   2,   2, 218, 219,   0,   0,
      2,   2,   2,   2,   2,   2, 220,   0, 212, 221, 222, 223, 224, 225,   0, 226,
      2,  88,   2,   2,  77, 227, 228,  84, 124, 114,   2,  88,  16,   0,   0, 229,
    230,  16, 231,   0,   0,   0,   0,   0,   2,   2,   2, 119,   2, 212,   2,   2,
      2,   2,   2,   2,   2,   2, 106, 232,   2,   2,   2,  77,   2,   2,  19,   0,
     88,   2, 193,   2,  10, 233,   0,   0, 234,   0,   0,   0, 235,   0, 158,   0,
      2,   2,   2,   2,   2,   2,  76,   0,   2,  19,   2,   2,   2,   2,   2,   2,
     79,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2,   2, 206,   0,   0,
     79,   0,   0,   0,   0,   0,   0,   0, 236,   2,   2,   2,   0,   0,   0,   0,
      2,   2,   2,   2,   2,   2,   2, 203,   2,   2,   2,   2,   2,   2,   2,  79,
};

static RE_UINT8 re_graph_stage_5[] = {
      0,   0,   0,   0, 254, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 127,
    255, 255, 255, 252, 240, 215, 255, 255, 251, 255, 255, 255, 255, 255, 254, 255,
    255, 255, 127, 254, 255, 230, 254, 255, 255,   0, 255, 255, 255,   7,  31,   0,
    255, 255, 255, 223, 255, 191, 255, 255, 255, 231, 255, 255, 255, 255,   3,   0,
    255, 255, 255,   7, 255,  63, 255, 127, 255, 255, 255,  79, 255, 255,  31,   0,
    248, 255, 255, 255, 239, 159, 249, 255, 255, 253, 197, 243, 159, 121, 128, 176,
    207, 255, 255,  15, 238, 135, 249, 255, 255, 253, 109, 211, 135,  57,   2,  94,
    192, 255,  63,   0, 238, 191, 251, 255, 255, 253, 237, 243, 191,  59,   1,   0,
    207, 255,   3,   2, 238, 159, 249, 255, 159,  57, 192, 176, 207, 255, 255,   0,
    236, 199,  61, 214,  24, 199, 255, 195, 199,  61, 129,   0, 192, 255, 255,   7,
    239, 223, 253, 255, 255, 253, 255, 227, 223,  61,  96,   7, 207, 255,   0, 255,
    238, 223, 253, 255, 255, 253, 239, 243, 223,  61,  96,  64, 207, 255,   6,   0,
    255, 255, 255, 231, 223, 125, 128, 128, 207, 255,  63, 254, 236, 255, 127, 252,
    255, 255, 251,  47, 127, 132,  95, 255, 192, 255,  28,   0, 255, 255, 255, 135,
    255, 255, 255,  15, 150,  37, 240, 254, 174, 236, 255,  59,  95,  63, 255, 243,
    255, 254, 255, 255, 255,  31, 254, 255, 255, 255, 255, 254, 255, 223, 255,   7,
    191,  32, 255, 255, 255,  61, 127,  61, 255,  61, 255, 255, 255, 255,  61, 127,
     61, 255, 127, 255, 255, 255,  61, 255, 255, 255, 255,  31, 255, 255, 255,   3,
    255, 255,  63,  63, 254, 255, 255,  31, 255, 255, 255,   1, 255, 223,  31,   0,
    255, 255, 127,   0, 255, 255,  15,   0, 255, 223,  13,   0, 255, 255, 255,  63,
    255,   3, 255,   3, 255, 127, 255,   3, 255, 255, 255,   0, 255,   7, 255, 255,
    255, 255,  63,   0, 255,  15, 255,  15, 241, 255, 255, 255, 255,  63,  31,   0,
    255,  15, 255, 255, 255,   3, 255, 199, 255, 255, 255, 207, 255, 255, 255, 159,
    255, 255,  15, 240, 255, 255, 255, 248, 255, 227, 255, 255, 255, 255, 127,   3,
    255, 255,  63, 240,  63,  63, 255, 170, 255, 255, 223, 255, 223, 255, 207, 239,
    255, 255, 220, 127,   0, 248, 255, 255, 255, 124, 255, 255, 223, 255, 243, 255,
    255, 127, 255,  31,   0,   0, 255, 255, 255, 255,   1,   0, 127,   0,   0,   0,
    255,   7,   0,   0, 255, 255, 207, 255, 255, 255,  63, 255, 255, 255, 255, 227,
    255, 253,   3,   0,   0, 240,   0,   0, 255, 127, 255, 255, 255, 255,  15, 254,
    255, 128,   1, 128, 127, 127, 127, 127,   7,   0,   0,   0, 255, 255, 255, 251,
      0,   0, 255,  15, 224, 255, 255, 255, 255,  63, 254, 255,  15,   0, 255, 255,
    255,  31, 255, 255, 127,   0, 255, 255, 255,  15,   0,   0, 255,  63, 255,   0,
      0,   0, 128, 255, 255,  15, 255,   3,  31, 192, 255,   3, 255, 255,  15, 128,
    255, 191, 255, 195, 255,  63, 255, 243,   7,   0,   0, 248, 126, 126, 126,   0,
    127, 127, 255, 255,  63,   0, 255, 255, 255,  63, 255,   3, 127, 248, 255, 255,
    255,  63, 255, 255, 127,   0, 248, 224, 255, 255, 127,  95, 219, 255, 255, 255,
      3,   0, 248, 255, 255, 255, 252, 255, 255,   0,   0,   0,   0,   0, 255,  63,
    255, 255, 247, 255, 127,  15, 223, 255, 252, 252, 252,  28, 127, 127,   0,  62,
    255, 239, 255, 255, 127, 255, 255, 183, 255,  63, 255,  63, 135, 255, 255, 255,
    255, 255, 143, 255, 255,  31, 255,  15,   1,   0,   0,   0, 255, 255, 255, 191,
     15, 255,  63,   0, 255,   3,   0,   0,  15, 128,   0,   0,  63, 253, 255, 255,
    255, 255, 191, 145, 255, 255, 191, 255, 128, 255,   0,   0, 255, 255,  55, 248,
    255, 255, 255, 143, 255, 255, 255, 131, 255, 255, 255, 240, 111, 240, 239, 254,
    255, 255,  15, 135, 255,   0, 255,   1, 127, 248, 127,   0, 255, 255,  63, 254,
    255, 255,   7, 255, 255, 255,   3,  30,   0, 254,   0,   0, 255,   1,   0,   0,
    255, 255,   7,   0, 255, 255,   7, 252, 255,  63, 252, 255, 255, 255,   0, 128,
      3,   0, 255, 255, 255,   1, 255,   3, 254, 255,  31,   0, 255, 255, 251, 255,
    127, 189, 255, 191, 255,   3, 255, 255, 255,   7, 255,   3, 159,  57, 129, 224,
    207,  31,  31,   0, 255,   0, 255,   3,  31,   0, 255,   3, 255, 255,   7, 128,
    255, 127,  31,   0,  15,   0,   0,   0, 255, 127,   0,   0, 255, 195,   0,   0,
    255,  63,  63,   0,  63,   0, 255, 251, 251, 255, 255, 224, 255, 255,   0,   0,
     31,   0, 255, 255,   0, 128, 255, 255,   3,   0,   0,   0, 255,   7, 255,  31,
    255,   1, 255, 243, 127, 254, 255, 255,  63,   0,   0,   0, 100, 222, 255, 235,
    239, 255, 255, 255, 191, 231, 223, 223, 255, 255, 255, 123,  95, 252, 253, 255,
     63, 255, 255, 255, 255, 207, 255, 255, 255,  15,   0, 248, 254, 255,   0,   0,
    159, 255, 127,   0, 150, 254, 247,  10, 132, 234, 150, 170, 150, 247, 247,  94,
    255, 251, 255,  15, 238, 251, 255,  15,   0,   0,   3,   0, 255, 127, 254, 255,
    254, 255, 254, 255, 192, 255, 255, 255,   7,   0, 255, 255, 255,   1,   3,   0,
    255,  31,  15,   0, 255,  63,   0,   0,   0,   0, 255,   1,  31,   0,   0,   0,
      2,   0,   0,   0,
};

/* Graph: 2334 bytes. */

RE_UINT32 re_get_graph(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 15;
    code = ch ^ (f << 15);
    pos = (RE_UINT32)re_graph_stage_1[f] << 4;
    f = code >> 11;
    code ^= f << 11;
    pos = (RE_UINT32)re_graph_stage_2[pos + f] << 3;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_graph_stage_3[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_graph_stage_4[pos + f] << 5;
    pos += code;
    value = (re_graph_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Print. */

static RE_UINT8 re_print_stage_1[] = {
    0, 1, 2, 3, 4, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6,
    6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 7, 6, 4, 8,
    4, 8,
};

static RE_UINT8 re_print_stage_2[] = {
     0,  1,  2,  3,  4,  5,  6,  7,  7,  8,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  9, 10, 11,  7,  7,  7,  7, 12, 13,  7,  7,  7, 14,
    15, 16, 17, 18, 19, 13, 20, 13, 21, 13, 13, 13, 13, 22, 13, 13,
    13, 13, 13, 13, 13, 13, 23, 24, 13, 13, 25, 26, 13, 27, 28, 29,
     7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  7, 30,  7, 31, 32,  7, 33, 13, 13, 13, 13, 13, 34,
    13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13,
    35, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13,
     7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7, 36,
};

static RE_UINT8 re_print_stage_3[] = {
      0,   1,   1,   2,   1,   3,   4,   5,   6,   7,   8,   9,  10,  11,  12,  13,
     14,   1,  15,  16,   1,   1,  17,  18,  19,  20,  21,  22,  23,  24,   1,  25,
     26,  27,   1,  28,  29,   1,   1,   1,   1,   1,   1,  30,  31,  32,  33,  34,
     35,  36,  37,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,
      1,   1,   1,   1,   1,  38,   1,   1,   1,   1,   1,   1,   1,   1,   1,  39,
      1,   1,   1,   1,  40,   1,  41,  42,  43,  44,  45,  46,   1,   1,   1,   1,
      1,   1,   1,   1,   1,   1,   1,  47,  48,  48,  48,  48,  48,  48,  48,  48,
      1,   1,  49,  50,   1,  51,  52,  53,  54,  55,  56,  57,  58,  59,   1,  60,
     61,  62,  63,  64,  65,  48,  66,  48,  67,  68,  69,  70,  71,  72,  73,  74,
     75,  48,  76,  48,  48,  48,  48,  48,   1,   1,   1,  77,  78,  79,  48,  48,
      1,   1,   1,   1,  80,  48,  48,  48,  48,  48,  48,  48,   1,   1,  81,  48,
      1,   1,  82,  83,  48,  48,  48,  84,  85,  48,  48,  48,  48,  48,  48,  48,
     48,  48,  48,  48,  86,  48,  48,  48,  87,  88,  89,  90,  91,  92,  93,  94,
      1,   1,  95,  48,  48,  48,  48,  48,  96,  48,  48,  48,  48,  48,  97,  48,
     98,  99, 100,   1,   1, 101, 102, 103, 104, 105,  48,  48,  48,  48,  48,  48,
      1,   1,   1,   1,   1,   1, 106,   1,   1,   1,   1,   1,   1,   1,   1, 107,
    108,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1, 109,  48,
      1,   1, 110,  48,  48,  48,  48,  48, 111, 112,  48,  48,  48,  48,  48,  48,
      1,   1,   1,   1,   1,   1,   1, 113,
};

static RE_UINT8 re_print_stage_4[] = {
      0,   1,   1,   2,   0,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,
      1,   1,   1,   3,   4,   5,   1,   1,   1,   6,   7,   8,   9,   1,  10,  11,
     12,   1,   1,   1,   1,   1,   1,   1,  13,   1,  14,   1,   1,  15,   1,  16,
      1,  17,  18,   0,   0,  19,   0,  20,   1,   1,   1,   1,  21,  22,  23,  24,
     25,  26,  27,  28,  29,  30,  31,  32,  33,  30,  34,  35,  36,  37,  38,  39,
     40,  41,  42,  43,  44,  45,  46,  47,  44,  48,  49,  50,  51,  52,  53,  54,
      8,  55,  56,   0,  57,  58,  59,   0,   1,   1,  60,  61,  62,  12,  63,   0,
      1,   1,   1,   1,   1,   1,  64,   1,   1,   1,  65,   1,  66,  67,  68,   1,
     69,   1,  48,  70,  71,   1,   1,  72,   1,   1,   1,   1,  70,   1,   1,  73,
     74,  75,  76,  77,   1,   1,  78,  79,  80,   1,   1,  81,   1,  82,   1,  83,
      2,  84,  85,  86,   1,  87,  88,   1,  89,   1,   2,  90,  79,  17,   0,   0,
      1,   1,  87,  70,   1,   1,   1,  91,   1,  92,  93,   1,   0,   0,  10,  94,
      1,   1,   1,   1,   1,   1,   1,  95,  72,   1,  96,  78,   1,  97,  98,  99,
      1, 100,   1, 101, 102,   2, 103, 104,   1,   1,   1,   1,  87,   1,   1,   1,
      1,   1,   1,   1,   1,   1,   1,  16,   1, 105, 106,   1,   1,   1,   1,   1,
      1,   1,   1, 107, 108, 109, 110, 111,   1, 112,   2,   1,   1,   1,   1, 113,
      1,  64,   1, 114,  75, 115, 115,   1,   1,   1, 116,   0, 117,   1,   1,  76,
      1,   1,   1,   1,   1,   1,  83, 118,   1,   1,   8,   1,   7,   1,   1,   1,
    119, 120,   1,   1, 112,  16,   1, 121,   2,   1,   1,   1,   1,   1,   1,   2,
      1,   1,   1,   1,   1,  83,   1,   1,   1,   1,   1,   1,   1,   1,  83,   0,
      1,   1,   1,   1, 122,   1, 123,   1,   1, 124,   1,   1,   1,   1,   1,  81,
      1,   1,   1,   1,   1, 125,   0, 126,   1, 127,   1,  81,   1,   1, 128,  78,
      1,   1, 129,  70,   1,   1, 130,   2,   1,  75, 131,   1,   1,   1, 132,  75,
    133, 134,   1, 135,   1,   1,   1, 136,   1,   1,   1,   1,   1, 121, 137,  56,
      0,   0,   0,   0,   0,   0,   0,   0,   1,   1,   1, 138,   1,   1,  71,   0,
    139, 140, 141,   1,   1,   1, 142,   1,   1,   1, 103,   1, 143,   1, 144, 145,
     71,   1, 146, 147,   1,   1,   1,  90,   8,   1,   1,   1,   1,   2, 148, 149,
    150, 151, 152,   0,   1,   1,   1,  16, 153, 154,   1,   1, 155, 156, 103,  78,
      0,   0,   0,   0,  70,   1, 104,  56,   1, 121,  82,  16, 157,   1, 158,   0,
      1,   1,   1,   1,  78, 159,   0,   0,   1,  10,   1, 160,   0,   0,   0,   0,
      1,  75,  83, 144,   0,   0,   0,   0, 161, 162, 163,   1,   2, 164,   0, 165,
    166, 167,   0,   0,   1, 168, 143,   1, 169, 170, 171,   1,   1,   0,   1, 172,
      1, 173, 108, 174, 175, 176,   0,   0,   1,   1, 177,   0,   1, 178,   1, 179,
      0,   0,   0,   2,   0,   0,   0,   0,   1,   1, 180, 181,   1,   1, 182, 183,
      1,  97, 121,  75,   1,   1, 138, 184, 185,  78,   0,   0, 186, 187,   1, 188,
     21,  30, 189, 190,   0,   0,   0,   0,   0,   0,   0,   0,   1,   1, 191,   0,
      0,   0,   0,   0,   1, 108,  78,   0,   1,   1, 192,   0,   1,  81, 159,   0,
    109,  87,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   1,   1, 193,
      0,   0,   0,   0,   0,   0,   1,  73,   1,   1,   1,   1,  71,   0,   0,   0,
      1,   1,   1, 194,   1,   1,   1,   1,   1,   1, 195,   0,   0,   0,   0,   0,
      1, 196,   0,   0,   0,   0,   0,   0,   1,   1, 105,   0,   0,   0,   0,   0,
      1,  73,   2, 197,   0,   0, 103, 198,   1,   1, 199, 200, 201,   0,   0,   0,
      1,   1, 202,   2, 203,   0,   0,   0, 204,   0,   0,   0,   0,   0,   0,   0,
      1,   1,   1, 205, 206, 195,   0,   0,   1,   1,   1,   1,   1,   1,   1,  83,
      1, 207,   1,   1,   1,   1,   1, 177,   1,   1, 208,   0,   0,   0,   0,   0,
      1,   1,  75,  15,   0,   0,   0,   0,   1,   1,  97,   1,  12, 209, 210,   1,
    211, 212, 213,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1, 214,   1,   1,
      1,   1,   1,   1,   1,   1, 215,   1,   1,   1,   1,   1, 216, 217,   0,   0,
      1,   1,   1,   1,   1,   1, 218,   0, 210, 219, 220, 221, 222, 223,   0, 224,
      1,  87,   1,   1,  76, 225, 226,  83, 122, 112,   1,  87,  16,   0,   0, 227,
    228,  16, 229,   0,   0,   0,   0,   0,   1,   1,   1, 117,   1, 210,   1,   1,
      1,   1,   1,   1,   1,   1, 104, 230,   1,   1,   1,  76,   1,   1,  19,   0,
     87,   1, 191,   1,  10, 231,   0,   0, 232,   0,   0,   0, 233,   0, 156,   0,
      1,   1,   1,   1,   1,   1,  75,   0,   1,  19,   1,   1,   1,   1,   1,   1,
     78,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1, 204,   0,   0,
     78,   0,   0,   0,   0,   0,   0,   0, 234,   1,   1,   1,   0,   0,   0,   0,
      1,   1,   1,   1,   1,   1,   1, 201,   1,   1,   1,   1,   1,   1,   1,  78,
};

static RE_UINT8 re_print_stage_5[] = {
      0,   0,   0,   0, 255, 255, 255, 255, 255, 255, 255, 127, 255, 255, 255, 252,
    240, 215, 255, 255, 251, 255, 255, 255, 255, 255, 254, 255, 255, 255, 127, 254,
    254, 255, 255, 255, 255, 230, 254, 255, 255,   0, 255, 255, 255,   7,  31,   0,
    255, 255, 255, 223, 255, 191, 255, 255, 255, 231, 255, 255, 255, 255,   3,   0,
    255, 255, 255,   7, 255,  63, 255, 127, 255, 255, 255,  79, 255, 255,  31,   0,
    248, 255, 255, 255, 239, 159, 249, 255, 255, 253, 197, 243, 159, 121, 128, 176,
    207, 255, 255,  15, 238, 135, 249, 255, 255, 253, 109, 211, 135,  57,   2,  94,
    192, 255,  63,   0, 238, 191, 251, 255, 255, 253, 237, 243, 191,  59,   1,   0,
    207, 255,   3,   2, 238, 159, 249, 255, 159,  57, 192, 176, 207, 255, 255,   0,
    236, 199,  61, 214,  24, 199, 255, 195, 199,  61, 129,   0, 192, 255, 255,   7,
    239, 223, 253, 255, 255, 253, 255, 227, 223,  61,  96,   7, 207, 255,   0, 255,
    238, 223, 253, 255, 255, 253, 239, 243, 223,  61,  96,  64, 207, 255,   6,   0,
    255, 255, 255, 231, 223, 125, 128, 128, 207, 255,  63, 254, 236, 255, 127, 252,
    255, 255, 251,  47, 127, 132,  95, 255, 192, 255,  28,   0, 255, 255, 255, 135,
    255, 255, 255,  15, 150,  37, 240, 254, 174, 236, 255,  59,  95,  63, 255, 243,
    255, 254, 255, 255, 255,  31, 254, 255, 255, 255, 255, 254, 255, 223, 255,   7,
    191,  32, 255, 255, 255,  61, 127,  61, 255,  61, 255, 255, 255, 255,  61, 127,
     61, 255, 127, 255, 255, 255,  61, 255, 255, 255, 255,  31, 255, 255, 255,   3,
    255, 255,  63,  63, 255, 255, 255,   1, 255, 223,  31,   0, 255, 255, 127,   0,
    255, 255,  15,   0, 255, 223,  13,   0, 255, 255, 255,  63, 255,   3, 255,   3,
    255, 127, 255,   3, 255, 255, 255,   0, 255,   7, 255, 255, 255, 255,  63,   0,
    255,  15, 255,  15, 241, 255, 255, 255, 255,  63,  31,   0, 255,  15, 255, 255,
    255,   3, 255, 199, 255, 255, 255, 207, 255, 255, 255, 159, 255, 255,  15, 240,
    255, 255, 255, 248, 255, 227, 255, 255, 255, 255, 127,   3, 255, 255,  63, 240,
     63,  63, 255, 170, 255, 255, 223, 255, 223, 255, 207, 239, 255, 255, 220, 127,
    255, 252, 255, 255, 223, 255, 243, 255, 255, 127, 255,  31,   0,   0, 255, 255,
    255, 255,   1,   0, 127,   0,   0,   0, 255,   7,   0,   0, 255, 255, 207, 255,
    255, 255,  63, 255, 255, 255, 255, 227, 255, 253,   3,   0,   0, 240,   0,   0,
    255, 127, 255, 255, 255, 255,  15, 254, 255, 128,   1, 128, 127, 127, 127, 127,
      7,   0,   0,   0, 255, 255, 255, 251,   0,   0, 255,  15, 224, 255, 255, 255,
    255,  63, 254, 255,  15,   0, 255, 255, 255,  31, 255, 255, 127,   0, 255, 255,
    255,  15,   0,   0, 255,  63, 255,   0,   0,   0, 128, 255, 255,  15, 255,   3,
     31, 192, 255,   3, 255, 255,  15, 128, 255, 191, 255, 195, 255,  63, 255, 243,
      7,   0,   0, 248, 126, 126, 126,   0, 127, 127, 255, 255,  63,   0, 255, 255,
    255,  63, 255,   3, 127, 248, 255, 255, 255,  63, 255, 255, 127,   0, 248, 224,
    255, 255, 127,  95, 219, 255, 255, 255,   3,   0, 248, 255, 255, 255, 252, 255,
    255,   0,   0,   0,   0,   0, 255,  63, 255, 255, 247, 255, 127,  15, 223, 255,
    252, 252, 252,  28, 127, 127,   0,  62, 255, 239, 255, 255, 127, 255, 255, 183,
    255,  63, 255,  63, 135, 255, 255, 255, 255, 255, 143, 255, 255,  31, 255,  15,
      1,   0,   0,   0, 255, 255, 255, 191,  15, 255,  63,   0, 255,   3,   0,   0,
     15, 128,   0,   0,  63, 253, 255, 255, 255, 255, 191, 145, 255, 255, 191, 255,
    128, 255,   0,   0, 255, 255,  55, 248, 255, 255, 255, 143, 255, 255, 255, 131,
    255, 255, 255, 240, 111, 240, 239, 254, 255, 255,  15, 135, 255,   0, 255,   1,
    127, 248, 127,   0, 255, 255,  63, 254, 255, 255,   7, 255, 255, 255,   3,  30,
      0, 254,   0,   0, 255,   1,   0,   0, 255, 255,   7,   0, 255, 255,   7, 252,
    255,  63, 252, 255, 255, 255,   0, 128,   3,   0, 255, 255, 255,   1, 255,   3,
    254, 255,  31,   0, 255, 255, 251, 255, 127, 189, 255, 191, 255,   3, 255, 255,
    255,   7, 255,   3, 159,  57, 129, 224, 207,  31,  31,   0, 255,   0, 255,   3,
     31,   0, 255,   3, 255, 255,   7, 128, 255, 127,  31,   0,  15,   0,   0,   0,
    255, 127,   0,   0, 255, 195,   0,   0, 255,  63,  63,   0,  63,   0, 255, 251,
    251, 255, 255, 224, 255, 255,   0,   0,  31,   0, 255, 255,   0, 128, 255, 255,
      3,   0,   0,   0, 255,   7, 255,  31, 255,   1, 255, 243, 127, 254, 255, 255,
     63,   0,   0,   0, 100, 222, 255, 235, 239, 255, 255, 255, 191, 231, 223, 223,
    255, 255, 255, 123,  95, 252, 253, 255,  63, 255, 255, 255, 255, 207, 255, 255,
    255,  15,   0, 248, 254, 255,   0,   0, 159, 255, 127,   0, 150, 254, 247,  10,
    132, 234, 150, 170, 150, 247, 247,  94, 255, 251, 255,  15, 238, 251, 255,  15,
      0,   0,   3,   0, 255, 127, 254, 255, 254, 255, 254, 255, 192, 255, 255, 255,
      7,   0, 255, 255, 255,   1,   3,   0, 255,  31,  15,   0, 255,  63,   0,   0,
      0,   0, 255,   1,  31,   0,   0,   0,   2,   0,   0,   0,
};

/* Print: 2326 bytes. */

RE_UINT32 re_get_print(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 15;
    code = ch ^ (f << 15);
    pos = (RE_UINT32)re_print_stage_1[f] << 4;
    f = code >> 11;
    code ^= f << 11;
    pos = (RE_UINT32)re_print_stage_2[pos + f] << 3;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_print_stage_3[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_print_stage_4[pos + f] << 5;
    pos += code;
    value = (re_print_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Word. */

static RE_UINT8 re_word_stage_1[] = {
    0, 1, 2, 3, 4, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6,
    6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 7, 6, 6, 6,
    6, 6,
};

static RE_UINT8 re_word_stage_2[] = {
     0,  1,  2,  3,  4,  5,  6,  7,  7,  8,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  9, 10, 11,  7,  7,  7,  7, 12, 13, 13, 13, 13, 14,
    15, 16, 17, 18, 19, 13, 20, 13, 21, 13, 13, 13, 13, 22, 13, 13,
    13, 13, 13, 13, 13, 13, 23, 24, 13, 13, 25, 26, 13, 27, 28, 13,
     7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  7, 29,  7, 30, 31,  7, 32, 13, 13, 13, 13, 13, 33,
    13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13,
    34, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13,
};

static RE_UINT8 re_word_stage_3[] = {
      0,   1,   2,   3,   4,   5,   6,   7,   8,   9,  10,  11,  12,  13,  14,  15,
     16,   1,  17,  18,  19,   1,  20,  21,  22,  23,  24,  25,  26,  27,   1,  28,
     29,  30,  31,  31,  32,  31,  31,  31,  31,  31,  31,  31,  33,  34,  35,  31,
     36,  37,  31,  31,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,
      1,   1,   1,   1,   1,  38,   1,   1,   1,   1,   1,   1,   1,   1,   1,  39,
      1,   1,   1,   1,  40,   1,  41,  42,  43,  44,  45,  46,   1,   1,   1,   1,
      1,   1,   1,   1,   1,   1,   1,  47,  31,  31,  31,  31,  31,  31,  31,  31,
     31,   1,  48,  49,   1,  50,  51,  52,  53,  54,  55,  56,  57,  58,   1,  59,
     60,  61,  62,  63,  64,  31,  31,  31,  65,  66,  67,  68,  69,  70,  71,  72,
     73,  31,  74,  31,  31,  31,  31,  31,   1,   1,   1,  75,  76,  77,  31,  31,
      1,   1,   1,   1,  78,  31,  31,  31,  31,  31,  31,  31,   1,   1,  79,  31,
      1,   1,  80,  81,  31,  31,  31,  82,  83,  31,  31,  31,  31,  31,  31,  31,
     31,  31,  31,  31,  84,  31,  31,  31,  31,  85,  86,  31,  87,  88,  89,  90,
     31,  31,  91,  31,  31,  31,  31,  31,  92,  31,  31,  31,  31,  31,  93,  31,
     31,  94,  31,  31,  31,  31,  31,  31,   1,   1,   1,   1,   1,   1,  95,   1,
      1,   1,   1,   1,   1,   1,   1,  96,  97,   1,   1,   1,   1,   1,   1,   1,
      1,   1,   1,   1,   1,   1,  98,  31,   1,   1,  99,  31,  31,  31,  31,  31,
     31, 100,  31,  31,  31,  31,  31,  31,
};

static RE_UINT8 re_word_stage_4[] = {
      0,   1,   2,   3,   0,   4,   5,   5,   6,   6,   6,   6,   6,   6,   6,   6,
      6,   6,   6,   6,   6,   6,   7,   8,   6,   6,   6,   9,  10,  11,   6,  12,
      6,   6,   6,   6,  11,   6,   6,   6,   6,  13,  14,  15,  16,  17,  18,  19,
     20,   6,   6,  21,   6,   6,  22,  23,  24,   6,  25,   6,   6,  26,   6,  27,
      6,  28,  29,   0,   0,  30,   0,  31,   6,   6,   6,  32,  33,  34,  35,  36,
     37,  38,  39,  40,  41,  42,  43,  44,  45,  42,  46,  47,  48,  49,  50,  51,
     52,  53,  54,  55,  56,  57,  58,  59,  56,  60,  61,  62,  63,  64,  65,  66,
     15,  67,  68,   0,  69,  70,  71,   0,  72,  73,  74,  75,  76,  77,  78,   0,
      6,   6,  79,   6,  80,   6,  81,  82,   6,   6,  83,   6,  84,  85,  86,   6,
     87,   6,  60,   0,  88,   6,   6,  89,  15,   6,   6,   6,   6,   6,   6,   6,
      6,   6,   6,  90,   3,   6,   6,  91,  92,  30,  93,  94,   6,   6,  95,  96,
     97,   6,   6,  98,   6,  99,   6, 100, 101, 102, 103, 104,   6, 105, 106,   0,
     29,   6, 101, 107, 106, 108,   0,   0,   6,   6, 109, 110,   6,   6,   6,  93,
      6,  98, 111,  80,   0,   0, 112, 113,   6,   6,   6,   6,   6,   6,   6, 114,
     89,   6, 115,  80,   6, 116, 117, 118, 119, 120, 121, 122, 123,   0,  24, 124,
    125, 126, 127,   6, 128,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0, 129,   6,  96,   6, 130, 101,   6,   6,   6,   6, 131,
      6,  81,   6, 132, 133, 134, 134,   6,   0, 135,   0,   0,   0,   0,   0,   0,
    136, 137,  15,   6, 138,  15,   6,  82, 139, 140,   6,   6, 141,  67,   0,  24,
      6,   6,   6,   6,   6, 100,   0,   0,   6,   6,   6,   6,   6,   6, 100,   0,
      6,   6,   6,   6, 142,   0,  24,  80, 143, 144,   6, 145,   6,   6,   6,  26,
    146, 147,   6,   6, 148, 149,   0, 146,   6, 150,   6,  93,   6,   6, 151, 152,
      6, 153,  93,  77,   6,   6, 154, 101,   6, 133, 155, 156,   6,   6, 157, 158,
    159, 160,  82, 161,   6,   6,   6, 162,   6,   6,   6,   6,   6, 163, 164,  29,
      6,   6,   6, 153,   6,   6, 165,   0, 166, 167, 168,   6,   6,  26, 169,   6,
      6,  80,  24,   6, 170,   6, 150, 171,  88, 172, 173, 174,   6,   6,   6,  77,
      1,   2,   3, 103,   6, 101, 175,   0, 176, 177, 178,   0,   6,   6,   6,  67,
      0,   0,   6,  30,   0,   0,   0, 179,   0,   0,   0,   0,  77,   6, 124, 180,
      6,  24,  99,  67,  80,   6, 181,   0,   6,   6,   6,   6,  80,  96,   0,   0,
      6, 182,   6, 183,   0,   0,   0,   0,   6, 133, 100, 150,   0,   0,   0,   0,
    184, 185, 100, 133, 101,   0,   0, 186, 100, 165,   0,   0,   6, 187,   0,   0,
    188, 189,   0,  77,  77,   0,  74, 190,   6, 100, 100, 191,  26,   0,   0,   0,
      6,   6, 128,   0,   6, 191,   6, 191,   6,   6, 190, 192,   6,  67,  24, 193,
      6, 194,  24, 195,   6,   6, 196,   0, 197,  98,   0,   0, 198, 199,   6, 200,
     33,  42, 201, 202,   0,   0,   0,   0,   0,   0,   0,   0,   6,   6, 203,   0,
      0,   0,   0,   0,   6, 204, 205,   0,   6,   6, 206,   0,   6,  98,  96,   0,
    207, 109,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   6,   6, 208,
      0,   0,   0,   0,   0,   0,   6, 209,   6,   6,   6,   6, 165,   0,   0,   0,
      6,   6,   6, 141,   6,   6,   6,   6,   6,   6, 183,   0,   0,   0,   0,   0,
      6, 141,   0,   0,   0,   0,   0,   0,   6,   6, 190,   0,   0,   0,   0,   0,
      6, 209, 101,  96,   0,   0,  24, 104,   6, 133, 210, 211,  88,   0,   0,   0,
      6,   6, 212, 101, 213,   0,   0,   0, 214,   0,   0,   0,   0,   0,   0,   0,
      6,   6,   6, 215, 216,   0,   0,   0,   0,   0,   0, 217, 218, 219,   0,   0,
      0,   0, 220,   0,   0,   0,   0,   0,   6,   6, 194,   6, 221, 222, 223,   6,
    224, 225, 226,   6,   6,   6,   6,   6,   6,   6,   6,   6,   6, 227, 228,  82,
    194, 194, 130, 130, 229, 229, 230,   6,   6, 231,   6, 232, 233, 234,   0,   0,
      6,   6,   6,   6,   6,   6, 235,   0, 223, 236, 237, 238, 239, 240,   0,   0,
      0,  24,  79,  79,  96,   0,   0,   0,   6,   6,   6,   6,   6,   6, 133,   0,
      6,  30,   6,   6,   6,   6,   6,   6,  80,   6,   6,   6,   6,   6,   6,   6,
      6,   6,   6,   6,   6, 214,   0,   0,  80,   0,   0,   0,   0,   0,   0,   0,
      6,   6,   6,   6,   6,   6,   6,  88,
};

static RE_UINT8 re_word_stage_5[] = {
      0,   0,   0,   0,   0,   0, 255,   3, 254, 255, 255, 135, 254, 255, 255,   7,
      0,   4,  32,   4, 255, 255, 127, 255, 255, 255, 255, 255, 195, 255,   3,   0,
     31,  80,   0,   0, 255, 255, 223, 188,  64, 215, 255, 255, 251, 255, 255, 255,
    255, 255, 191, 255, 255, 255, 254, 255, 255, 255, 127,   2, 254, 255, 255, 255,
    255,   0, 254, 255, 255, 255, 255, 191, 182,   0, 255, 255, 255,   7,   7,   0,
      0,   0, 255,   7, 255, 195, 255, 255, 255, 255, 239, 159, 255, 253, 255, 159,
      0,   0, 255, 255, 255, 231, 255, 255, 255, 255,   3,   0, 255, 255,  63,   4,
    255,  63,   0,   0, 255, 255, 255,  15, 255, 255,  31,   0, 248, 255, 255, 255,
    207, 255, 254, 255, 239, 159, 249, 255, 255, 253, 197, 243, 159, 121, 128, 176,
    207, 255,   3,   0, 238, 135, 249, 255, 255, 253, 109, 211, 135,  57,   2,  94,
    192, 255,  63,   0, 238, 191, 251, 255, 255, 253, 237, 243, 191,  59,   1,   0,
    207, 255,   0,   2, 238, 159, 249, 255, 159,  57, 192, 176, 207, 255,   2,   0,
    236, 199,  61, 214,  24, 199, 255, 195, 199,  61, 129,   0, 192, 255,   0,   0,
    239, 223, 253, 255, 255, 253, 255, 227, 223,  61,  96,   7, 207, 255,   0,   0,
    238, 223, 253, 255, 255, 253, 239, 243, 223,  61,  96,  64, 207, 255,   6,   0,
    255, 255, 255, 231, 223, 125, 128, 128, 207, 255,   0, 252, 236, 255, 127, 252,
    255, 255, 251,  47, 127, 132,  95, 255, 192, 255,  12,   0, 255, 255, 255,   7,
    255, 127, 255,   3, 150,  37, 240, 254, 174, 236, 255,  59,  95,  63, 255, 243,
      1,   0,   0,   3, 255,   3, 160, 194, 255, 254, 255, 255, 255,  31, 254, 255,
    223, 255, 255, 254, 255, 255, 255,  31,  64,   0,   0,   0, 255,   3, 255, 255,
    255, 255, 255,  63, 191,  32, 255, 255, 255, 255, 255, 247, 255,  61, 127,  61,
    255,  61, 255, 255, 255, 255,  61, 127,  61, 255, 127, 255, 255, 255,  61, 255,
    255, 255,   0,   0, 255, 255,  63,  63, 255, 159, 255, 255, 255, 199, 255,   1,
    255, 223,  31,   0, 255, 255,  15,   0, 255, 223,  13,   0, 255, 255, 143,  48,
    255,   3,   0,   0,   0,  56, 255,   3, 255, 255, 255,   0, 255,   7, 255, 255,
    255, 255,  63,   0, 255, 255, 255, 127, 255,  15, 255,  15, 192, 255, 255, 255,
    255,  63,  31,   0, 255,  15, 255, 255, 255,   3, 255,   3, 255, 255, 255, 159,
    128,   0, 255, 127, 255,  15, 255,   3,   0, 248,  15,   0, 255, 227, 255, 255,
      0,   0, 247, 255, 255, 255, 127,   3, 255, 255,  63, 240,  63,  63, 255, 170,
    255, 255, 223,  95, 220,  31, 207,  15, 255,  31, 220,  31,   0,  48,   0,   0,
      0,   0,   0, 128,   1,   0,  16,   0,   0,   0,   2, 128,   0,   0, 255,  31,
    255, 255,   1,   0, 132, 252,  47,  62,  80, 189, 255, 243, 224,  67,   0,   0,
    255,   1,   0,   0,   0,   0, 192, 255, 255, 127, 255, 255,  31, 248,  15,   0,
    255, 128,   0, 128, 255, 255, 127,   0, 127, 127, 127, 127,   0, 128,   0,   0,
    224,   0,   0,   0, 254, 255,  62,  31, 255, 255, 127, 230, 224, 255, 255, 255,
    255,  63, 254, 255, 255, 127,   0,   0, 255,  31,   0,   0, 255,  31, 255, 255,
    255,  15,   0,   0, 255, 255, 247, 191,   0,   0, 128, 255, 252, 255, 255, 255,
    255, 249, 255, 255, 255,  63, 255,   0, 255,   0,   0,   0,  31,   0, 255,   3,
    255, 255, 255,  40, 255,  63, 255, 255,   1, 128, 255,   3, 255,  63, 255,   3,
    255, 255, 127, 252,   7,   0,   0,  56, 255, 255, 124,   0, 126, 126, 126,   0,
    127, 127, 255, 255,  63,   0, 255, 255, 255,  55, 255,   3,  15,   0, 255, 255,
    127, 248, 255, 255, 255, 255, 255,   3, 127,   0, 248, 224, 255, 253, 127,  95,
    219, 255, 255, 255,   0,   0, 248, 255, 255, 255, 252, 255,   0,   0, 255,  15,
    255, 255,  24,   0,   0, 224,   0,   0,   0,   0, 223, 255, 252, 252, 252,  28,
    255, 239, 255, 255, 127, 255, 255, 183, 255,  63, 255,  63,   0,   0,   0,  32,
      1,   0,   0,   0,  15, 255,  62,   0, 255,   0, 255, 255,  15,   0,   0,   0,
     63, 253, 255, 255, 255, 255, 191, 145, 255, 255,  55,   0, 255, 255, 255, 192,
    111, 240, 239, 254, 255, 255,  15, 135, 127,   0,   0,   0, 255, 255,   7,   0,
    192, 255,   0, 128, 255,   1, 255,   3, 255, 255, 223, 255, 255, 255,  79,   0,
     31,  28, 255,  23, 255, 255, 251, 255, 127, 189, 255, 191, 255,   1, 255, 255,
    255,   7, 255,   3, 159,  57, 129, 224, 207,  31,  31,   0, 191,   0, 255,   3,
    255, 255,  63, 255,   1,   0,   0,  63,  17,   0, 255,   3, 255, 255, 255, 227,
    255,   3,   0, 128, 255, 255, 255,   1,  15,   0, 255,   3, 248, 255, 255, 224,
     31,   0, 255, 255,   0, 128, 255, 255,   3,   0,   0,   0, 255,   7, 255,  31,
    255,   1, 255,  99, 224, 227,   7, 248, 231,  15,   0,   0,   0,  60,   0,   0,
     28,   0,   0,   0, 255, 255, 255, 223, 100, 222, 255, 235, 239, 255, 255, 255,
    191, 231, 223, 223, 255, 255, 255, 123,  95, 252, 253, 255,  63, 255, 255, 255,
    253, 255, 255, 247, 255, 253, 255, 255, 247, 207, 255, 255, 255, 255, 127, 248,
    255,  31,  32,   0,  16,   0,   0, 248, 254, 255,   0,   0,  31,   0, 127,   0,
    150, 254, 247,  10, 132, 234, 150, 170, 150, 247, 247,  94, 255, 251, 255,  15,
    238, 251, 255,  15,
};

/* Word: 2214 bytes. */

RE_UINT32 re_get_word(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 15;
    code = ch ^ (f << 15);
    pos = (RE_UINT32)re_word_stage_1[f] << 4;
    f = code >> 11;
    code ^= f << 11;
    pos = (RE_UINT32)re_word_stage_2[pos + f] << 3;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_word_stage_3[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_word_stage_4[pos + f] << 5;
    pos += code;
    value = (re_word_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* XDigit. */

static RE_UINT8 re_xdigit_stage_1[] = {
    0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2,
};

static RE_UINT8 re_xdigit_stage_2[] = {
    0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 3, 2, 2, 2, 2, 4,
    5, 6, 2, 2, 2, 2, 7, 2, 2, 2, 2, 2, 2, 8, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
};

static RE_UINT8 re_xdigit_stage_3[] = {
     0,  1,  1,  1,  1,  1,  2,  3,  1,  4,  4,  4,  4,  4,  5,  6,
     7,  1,  1,  1,  1,  1,  1,  8,  9, 10, 11, 12, 13,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  6,  1, 14, 15, 16, 17,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1, 18,
     1,  1,  1,  1, 19,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
    20, 21, 17,  1, 14,  1, 22, 23,  8,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1, 24, 16,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1, 25,  1,  1,  1,  1,  1,  1,  1,  1,
};

static RE_UINT8 re_xdigit_stage_4[] = {
     0,  1,  2,  2,  2,  2,  2,  2,  2,  3,  2,  0,  2,  2,  2,  4,
     2,  5,  2,  5,  2,  6,  2,  6,  3,  2,  2,  2,  2,  4,  6,  2,
     2,  2,  2,  3,  6,  2,  2,  2,  2,  7,  2,  6,  2,  2,  8,  2,
     2,  6,  0,  2,  2,  8,  2,  2,  2,  2,  2,  6,  4,  2,  2,  9,
     2,  6,  2,  2,  2,  2,  2,  0, 10, 11,  2,  2,  2,  2,  3,  2,
     2,  5,  2,  0, 12,  2,  2,  6,  2,  6,  2,  4,  0,  2,  2,  2,
     2,  3,  2,  2,  2,  2,  2, 13,
};

static RE_UINT8 re_xdigit_stage_5[] = {
      0,   0,   0,   0,   0,   0, 255,   3, 126,   0,   0,   0, 126,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 255,   3,   0,   0,
    255,   3,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 192, 255,   0,   0,
      0,   0, 255,   3,   0,   0,   0,   0, 192, 255,   0,   0,   0,   0,   0,   0,
    255,   3, 255,   3,   0,   0,   0,   0,   0,   0, 255,   3,   0,   0, 255,   3,
      0,   0, 255,   3, 126,   0,   0,   0, 126,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0, 192, 255,   0, 192, 255, 255, 255, 255, 255, 255,
};

/* XDigit: 425 bytes. */

RE_UINT32 re_get_xdigit(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_xdigit_stage_1[f] << 4;
    f = code >> 12;
    code ^= f << 12;
    pos = (RE_UINT32)re_xdigit_stage_2[pos + f] << 4;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_xdigit_stage_3[pos + f] << 2;
    f = code >> 6;
    code ^= f << 6;
    pos = (RE_UINT32)re_xdigit_stage_4[pos + f] << 6;
    pos += code;
    value = (re_xdigit_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Posix_Digit. */

static RE_UINT8 re_posix_digit_stage_1[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1,
};

static RE_UINT8 re_posix_digit_stage_2[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
};

static RE_UINT8 re_posix_digit_stage_3[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
};

static RE_UINT8 re_posix_digit_stage_4[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
};

static RE_UINT8 re_posix_digit_stage_5[] = {
      0,   0,   0,   0,   0,   0, 255,   3,   0,   0,   0,   0,   0,   0,   0,   0,
};

/* Posix_Digit: 97 bytes. */

RE_UINT32 re_get_posix_digit(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_posix_digit_stage_1[f] << 4;
    f = code >> 12;
    code ^= f << 12;
    pos = (RE_UINT32)re_posix_digit_stage_2[pos + f] << 3;
    f = code >> 9;
    code ^= f << 9;
    pos = (RE_UINT32)re_posix_digit_stage_3[pos + f] << 3;
    f = code >> 6;
    code ^= f << 6;
    pos = (RE_UINT32)re_posix_digit_stage_4[pos + f] << 6;
    pos += code;
    value = (re_posix_digit_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Posix_AlNum. */

static RE_UINT8 re_posix_alnum_stage_1[] = {
    0, 1, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
    3,
};

static RE_UINT8 re_posix_alnum_stage_2[] = {
     0,  1,  2,  3,  4,  5,  6,  7,  7,  8,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  9, 10, 11,  7,  7,  7,  7, 12, 13, 13, 13, 13, 14,
    15, 16, 17, 18, 19, 13, 20, 13, 21, 13, 13, 13, 13, 22, 13, 13,
    13, 13, 13, 13, 13, 13, 23, 24, 13, 13, 25, 13, 13, 26, 27, 13,
     7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  7, 28,  7, 29, 30,  7, 31, 13, 13, 13, 13, 13, 32,
    13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13,
    13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13,
};

static RE_UINT8 re_posix_alnum_stage_3[] = {
     0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15,
    16,  1, 17, 18, 19,  1, 20, 21, 22, 23, 24, 25, 26, 27,  1, 28,
    29, 30, 31, 31, 32, 31, 31, 31, 31, 31, 31, 31, 33, 34, 35, 31,
    36, 37, 31, 31,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1, 38,  1,  1,  1,  1,  1,  1,  1,  1,  1, 39,
     1,  1,  1,  1, 40,  1, 41, 42, 43, 44, 45, 46,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1, 47, 31, 31, 31, 31, 31, 31, 31, 31,
    31,  1, 48, 49,  1, 50, 51, 52, 53, 54, 55, 56, 57, 58,  1, 59,
    60, 61, 62, 63, 64, 31, 31, 31, 65, 66, 67, 68, 69, 70, 71, 72,
    73, 31, 74, 31, 31, 31, 31, 31,  1,  1,  1, 75, 76, 77, 31, 31,
     1,  1,  1,  1, 78, 31, 31, 31, 31, 31, 31, 31,  1,  1, 79, 31,
     1,  1, 80, 81, 31, 31, 31, 82, 83, 31, 31, 31, 31, 31, 31, 31,
    31, 31, 31, 31, 84, 31, 31, 31, 31, 31, 31, 31, 85, 86, 87, 88,
    89, 31, 31, 31, 31, 31, 90, 31, 31, 91, 31, 31, 31, 31, 31, 31,
     1,  1,  1,  1,  1,  1, 92,  1,  1,  1,  1,  1,  1,  1,  1, 93,
    94,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1, 95, 31,
     1,  1, 96, 31, 31, 31, 31, 31,
};

static RE_UINT8 re_posix_alnum_stage_4[] = {
      0,   1,   2,   2,   0,   3,   4,   4,   5,   5,   5,   5,   5,   5,   5,   5,
      5,   5,   5,   5,   5,   5,   6,   7,   0,   0,   8,   9,  10,  11,   5,  12,
      5,   5,   5,   5,  13,   5,   5,   5,   5,  14,  15,  16,  17,  18,  19,  20,
     21,   5,  22,  23,   5,   5,  24,  25,  26,   5,  27,   5,   5,  28,  29,  30,
     31,  32,  33,   0,   0,  34,   0,  35,   5,  36,  37,  38,  39,  40,  41,  42,
     43,  44,  45,  46,  47,  48,  49,  50,  51,  48,  52,  53,  54,  55,  56,   0,
     57,  58,  59,  60,  61,  62,  63,  64,  61,  65,  66,  67,  68,  69,  70,  71,
     16,  72,  73,   0,  74,  75,  76,   0,  77,   0,  78,  79,  80,  81,   0,   0,
      5,  82,  26,  83,  84,   5,  85,  86,   5,   5,  87,   5,  88,  89,  90,   5,
     91,   5,  92,   0,  93,   5,   5,  94,  16,   5,   5,   5,   5,   5,   5,   5,
      5,   5,   5,  95,   2,   5,   5,  96,  97,  98,  98,  99,   5, 100, 101,   0,
      0,   5,   5, 102,   5, 103,   5, 104, 105, 106,  26, 107,   5, 108, 109,   0,
    110,   5, 105, 111,   0, 112,   0,   0,   5, 113, 114,   0,   5, 115,   5, 116,
      5, 104, 117, 118,   0,   0,   0, 119,   5,   5,   5,   5,   5,   5,   0, 120,
     94,   5, 121, 118,   5, 122, 123, 124,   0,   0,   0, 125, 126,   0,   0,   0,
    127, 128, 129,   5, 130,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0, 131,   5, 109,   5, 132, 105,   5,   5,   5,   5, 133,
      5,  85,   5, 134, 135, 136, 136,   5,   0, 137,   0,   0,   0,   0,   0,   0,
    138, 139,  16,   5, 140,  16,   5,  86, 141, 142,   5,   5, 143,  72,   0,  26,
      5,   5,   5,   5,   5, 104,   0,   0,   5,   5,   5,   5,   5,   5, 104,   0,
      5,   5,   5,   5,  32,   0,  26, 118, 144, 145,   5, 146,   5,   5,   5,  93,
    147, 148,   5,   5, 149, 150,   0, 147, 151,  17,   5,  98,   5,   5,  60, 152,
     29, 103, 153,  81,   5, 154, 137, 155,   5, 135, 156, 157,   5, 105, 158, 159,
    160, 161,  86, 162,   5,   5,   5, 163,   5,   5,   5,   5,   5, 164, 165, 110,
      5,   5,   5, 166,   5,   5, 167,   0, 168, 169, 170,   5,   5,  28, 171,   5,
      5, 118,  26,   5, 172,   5,  17, 173,   0,   0,   0, 174,   5,   5,   5,  81,
      0,   2,   2, 175,   5, 105, 176,   0, 177, 178, 179,   0,   5,   5,   5,  72,
      0,   0,   5,  34,   0,   0,   0,   0,   0,   0,   0,   0,  81,   5, 180,   0,
      5,  26, 103,  72, 118,   5, 181,   0,   5,   5,   5,   5, 118,   0,   0,   0,
      5, 182,   5,  60,   0,   0,   0,   0,   5, 135, 104,  17,   0,   0,   0,   0,
    183, 184, 104, 135, 105,   0,   0, 185, 104, 167,   0,   0,   5, 186,   0,   0,
    187,  98,   0,  81,  81,   0,  78, 188,   5, 104, 104, 153,  28,   0,   0,   0,
      5,   5, 130,   0,   5, 153,   5, 153,   5,   5, 189,   0, 148,  33,  26, 130,
      5, 153,  26, 190,   5,   5, 191,   0, 192, 193,   0,   0, 194, 195,   5, 130,
     39,  48, 196,  60,   0,   0,   0,   0,   0,   0,   0,   0,   5,   5, 197,   0,
      0,   0,   0,   0,   5, 198, 199,   0,   5, 105, 200,   0,   5, 104,   0,   0,
    201, 163,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   5,   5, 202,
      0,   0,   0,   0,   0,   0,   5,  33,   5,   5,   5,   5, 167,   0,   0,   0,
      5,   5,   5, 143,   5,   5,   5,   5,   5,   5,  60,   0,   0,   0,   0,   0,
      5, 143,   0,   0,   0,   0,   0,   0,   5,   5, 203,   0,   0,   0,   0,   0,
      5,  33, 105,   0,   0,   0,  26, 156,   5, 135,  60, 204,  93,   0,   0,   0,
      5,   5, 205, 105, 171,   0,   0,   0, 206,   0,   0,   0,   0,   0,   0,   0,
      5,   5,   5, 207, 208,   0,   0,   0,   5,   5, 209,   5, 210, 211, 212,   5,
    213, 214, 215,   5,   5,   5,   5,   5,   5,   5,   5,   5,   5, 216, 217,  86,
    209, 209, 132, 132, 218, 218, 219,   0,   5,   5,   5,   5,   5,   5, 188,   0,
    212, 220, 221, 222, 223, 224,   0,   0,   0,  26, 225, 225, 109,   0,   0,   0,
      5,   5,   5,   5,   5,   5, 135,   0,   5,  34,   5,   5,   5,   5,   5,   5,
    118,   5,   5,   5,   5,   5,   5,   5,   5,   5,   5,   5,   5, 206,   0,   0,
    118,   0,   0,   0,   0,   0,   0,   0,
};

static RE_UINT8 re_posix_alnum_stage_5[] = {
      0,   0,   0,   0,   0,   0, 255,   3, 254, 255, 255,   7,   0,   4,  32,   4,
    255, 255, 127, 255, 255, 255, 255, 255, 195, 255,   3,   0,  31,  80,   0,   0,
     32,   0,   0,   0,   0,   0, 223, 188,  64, 215, 255, 255, 251, 255, 255, 255,
    255, 255, 191, 255,   3, 252, 255, 255, 255, 255, 254, 255, 255, 255, 127,   2,
    254, 255, 255, 255, 255,   0,   0,   0,   0,   0, 255, 191, 182,   0, 255, 255,
    255,   7,   7,   0,   0,   0, 255,   7, 255, 255, 255, 254,   0, 192, 255, 255,
    255, 255, 239,  31, 254, 225,   0, 156,   0,   0, 255, 255,   0, 224, 255, 255,
    255, 255,   3,   0,   0, 252, 255, 255, 255,   7,  48,   4, 255, 255, 255, 252,
    255,  31,   0,   0, 255, 255, 255,   1, 255, 255,  31,   0, 248,   3, 255, 255,
    255, 255, 255, 239, 255, 223, 225, 255,  15,   0, 254, 255, 239, 159, 249, 255,
    255, 253, 197, 227, 159,  89, 128, 176,  15,   0,   3,   0, 238, 135, 249, 255,
    255, 253, 109, 195, 135,  25,   2,  94,   0,   0,  63,   0, 238, 191, 251, 255,
    255, 253, 237, 227, 191,  27,   1,   0,  15,   0,   0,   2, 238, 159, 249, 255,
    159,  25, 192, 176,  15,   0,   2,   0, 236, 199,  61, 214,  24, 199, 255, 195,
    199,  29, 129,   0, 239, 223, 253, 255, 255, 253, 255, 227, 223,  29,  96,   7,
     15,   0,   0,   0, 238, 223, 253, 255, 255, 253, 239, 227, 223,  29,  96,  64,
     15,   0,   6,   0, 255, 255, 255, 231, 223,  93, 128, 128,  15,   0,   0, 252,
    236, 255, 127, 252, 255, 255, 251,  47, 127, 128,  95, 255,   0,   0,  12,   0,
    255, 255, 255,   7, 127,  32,   0,   0, 150,  37, 240, 254, 174, 236, 255,  59,
     95,  32,   0, 240,   1,   0,   0,   0, 255, 254, 255, 255, 255,  31, 254, 255,
      3, 255, 255, 254, 255, 255, 255,  31, 255, 255, 127, 249, 231, 193, 255, 255,
    127,  64,   0,  48, 191,  32, 255, 255, 255, 255, 255, 247, 255,  61, 127,  61,
    255,  61, 255, 255, 255, 255,  61, 127,  61, 255, 127, 255, 255, 255,  61, 255,
    255, 255, 255, 135, 255, 255,   0,   0, 255, 255,  63,  63, 255, 159, 255, 255,
    255, 199, 255,   1, 255, 223,  15,   0, 255, 255,  15,   0, 255, 223,  13,   0,
    255, 255, 207, 255, 255,   1, 128,  16, 255, 255, 255,   0, 255,   7, 255, 255,
    255, 255,  63,   0, 255, 255, 255, 127, 255,  15, 255,   1, 255,  63,  31,   0,
    255,  15, 255, 255, 255,   3,   0,   0, 255, 255, 255,  15, 254, 255,  31,   0,
    128,   0,   0,   0, 255, 255, 239, 255, 239,  15,   0,   0, 255, 243,   0, 252,
    191, 255,   3,   0,   0, 224,   0, 252, 255, 255, 255,  63,   0, 222, 111,   0,
    128, 255,  31,   0,  63,  63, 255, 170, 255, 255, 223,  95, 220,  31, 207,  15,
    255,  31, 220,  31,   0,   0,   2, 128,   0,   0, 255,  31, 132, 252,  47,  62,
     80, 189, 255, 243, 224,  67,   0,   0, 255,   1,   0,   0,   0,   0, 192, 255,
    255, 127, 255, 255,  31, 120,  12,   0, 255, 128,   0,   0, 255, 255, 127,   0,
    127, 127, 127, 127,   0, 128,   0,   0, 224,   0,   0,   0, 254,   3,  62,  31,
    255, 255, 127, 224, 224, 255, 255, 255, 255,  63, 254, 255, 255, 127,   0,   0,
    255,  31, 255, 255,   0,  12,   0,   0, 255, 127, 240, 143,   0,   0, 128, 255,
    252, 255, 255, 255, 255, 249, 255, 255, 255,  63, 255,   0, 187, 247, 255, 255,
      0,   0, 252,  40, 255, 255,   7,   0, 255, 255, 247, 255, 223, 255,   0, 124,
    255,  63,   0,   0, 255, 255, 127, 196,   5,   0,   0,  56, 255, 255,  60,   0,
    126, 126, 126,   0, 127, 127, 255, 255,  63,   0, 255, 255, 255,   7,   0,   0,
     15,   0, 255, 255, 127, 248, 255, 255, 255,  63, 255, 255, 255, 255, 255,   3,
    127,   0, 248, 224, 255, 253, 127,  95, 219, 255, 255, 255,   0,   0, 248, 255,
    255, 255, 252, 255,   0,   0, 255,  15,   0,   0, 223, 255, 192, 255, 255, 255,
    252, 252, 252,  28, 255, 239, 255, 255, 127, 255, 255, 183, 255,  63, 255,  63,
    255, 255,   1,   0,  15, 255,  62,   0, 255,   0, 255, 255,  63, 253, 255, 255,
    255, 255, 191, 145, 255, 255,  55,   0, 255, 255, 255, 192, 111, 240, 239, 254,
     31,   0,   0,   0,  63,   0,   0,   0, 255, 255,  71,   0,  30,   0,   0,  20,
    255, 255, 251, 255, 255, 255, 159,   0, 127, 189, 255, 191, 255,   1, 255, 255,
    159,  25, 129, 224, 179,   0,   0,   0, 255, 255,  63, 127,   0,   0,   0,  63,
     17,   0,   0,   0, 255, 255, 255, 227,   0,   0,   0, 128, 127,   0,   0,   0,
    248, 255, 255, 224,  31,   0, 255, 255,   3,   0,   0,   0, 255,   7, 255,  31,
    255,   1, 255,  67, 255, 255, 223, 255, 255, 255, 255, 223, 100, 222, 255, 235,
    239, 255, 255, 255, 191, 231, 223, 223, 255, 255, 255, 123,  95, 252, 253, 255,
     63, 255, 255, 255, 253, 255, 255, 247, 255, 253, 255, 255, 247,  15,   0,   0,
    150, 254, 247,  10, 132, 234, 150, 170, 150, 247, 247,  94, 255, 251, 255,  15,
    238, 251, 255,  15, 255,   3, 255, 255,
};

/* Posix_AlNum: 2089 bytes. */

RE_UINT32 re_get_posix_alnum(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_posix_alnum_stage_1[f] << 5;
    f = code >> 11;
    code ^= f << 11;
    pos = (RE_UINT32)re_posix_alnum_stage_2[pos + f] << 3;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_posix_alnum_stage_3[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_posix_alnum_stage_4[pos + f] << 5;
    pos += code;
    value = (re_posix_alnum_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Posix_Punct. */

static RE_UINT8 re_posix_punct_stage_1[] = {
    0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2,
};

static RE_UINT8 re_posix_punct_stage_2[] = {
     0,  1,  2,  3,  4,  5,  6,  7,  7,  8,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  7,  9, 10,  7,  7,  7,  7,  7,  7,  7,  7,  7, 11,
    12, 13, 14,  7, 15,  7,  7,  7,  7,  7,  7,  7,  7, 16,  7,  7,
     7,  7,  7,  7,  7,  7,  7, 17,  7,  7, 18, 19,  7, 20, 21, 22,
     7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,
};

static RE_UINT8 re_posix_punct_stage_3[] = {
     0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15,
    16,  1,  1, 17, 18,  1, 19, 20, 21, 22, 23, 24, 25,  1,  1, 26,
    27, 28, 29, 30, 31, 29, 29, 32, 29, 29, 29, 33, 34, 35, 36, 37,
    38, 39, 40, 29,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1, 41,  1,  1,  1,  1,  1,  1, 42,  1, 43, 44,
    45, 46, 47, 48,  1,  1,  1,  1,  1,  1,  1, 49,  1, 50, 51, 52,
     1, 53,  1, 54,  1, 55,  1,  1, 56, 57, 58, 59,  1,  1,  1,  1,
    60, 61, 62,  1, 63, 64, 65, 66,  1,  1,  1,  1, 67,  1,  1,  1,
     1,  1, 68, 69,  1,  1,  1,  1,  1,  1,  1,  1, 70,  1,  1,  1,
    71, 72, 73, 74,  1,  1, 75, 76, 29, 29, 77,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1, 10,  1, 78, 79, 80, 29, 29, 81, 82, 83,
    84, 85,  1,  1,  1,  1,  1,  1,
};

static RE_UINT8 re_posix_punct_stage_4[] = {
      0,   1,   2,   3,   0,   4,   5,   5,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   6,   7,   0,   0,   0,   8,   9,   0,   0,  10,
      0,   0,   0,   0,  11,   0,   0,   0,   0,   0,  12,   0,  13,  14,  15,  16,
     17,   0,   0,  18,   0,   0,  19,  20,  21,   0,   0,   0,   0,   0,   0,  22,
      0,  23,  14,   0,   0,   0,   0,   0,   0,   0,   0,  24,   0,   0,   0,  25,
      0,   0,   0,   0,   0,   0,   0,  26,   0,   0,   0,  27,   0,   0,   0,  28,
      0,   0,   0,  29,   0,   0,   0,   0,   0,   0,   0,  30,   0,   0,   0,  31,
      0,  29,  32,   0,   0,   0,   0,   0,  33,  34,   0,   0,  35,  36,  37,   0,
      0,   0,  38,   0,  36,   0,   0,  39,   0,   0,   0,  40,  41,   0,   0,   0,
     42,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  43,  44,   0,   0,  45,
      0,  46,   0,   0,   0,   0,  47,   0,  48,   0,   0,   0,   0,   0,   0,   0,
      0,   0,  49,   0,   0,   0,  36,  50,  36,   0,   0,   0,   0,  51,   0,   0,
      0,   0,  12,  52,   0,   0,   0,  53,   0,  54,   0,  36,   0,   0,  55,   0,
      0,   0,   0,   0,   0,  56,  57,  58,  59,  60,  61,  62,  63,  61,   0,   0,
     64,  65,  66,   0,  67,  50,  50,  50,  50,  50,  50,  50,  50,  50,  50,  50,
     50,  50,  50,  50,  50,  50,  50,  68,  50,  69,  48,   0,  53,  70,   0,   0,
     50,  50,  50,  70,  71,  50,  50,  50,  50,  50,  50,  72,  73,  74,  75,  76,
      0,   0,   0,   0,   0,   0,   0,  77,   0,   0,   0,  27,   0,   0,   0,   0,
     50,  78,  79,   0,  80,  50,  50,  81,  50,  50,  50,  50,  50,  50,  70,  82,
     83,  84,   0,   0,  44,  42,   0,  39,   0,   0,   0,   0,  85,   0,  50,  86,
     61,  87,  88,  50,  87,  89,  50,  61,   0,   0,   0,   0,   0,   0,  50,  50,
      0,   0,   0,   0,  59,  50,  69,  36,  90,   0,   0,  91,   0,   0,   0,  92,
     93,  94,   0,   0,  95,   0,   0,   0,   0,  96,   0,  97,   0,   0,  98,  99,
      0,  98,  29,   0,   0,   0, 100,   0,   0,   0,  53, 101,   0,   0,  36,  26,
      0,   0,  39,   0,   0,   0,   0, 102,   0, 103,   0,   0,   0, 104,  94,   0,
      0,  36,   0,   0,   0,   0,   0, 105,  41,  59, 106, 107,   0,   0,   0,   0,
      1,   2,   2, 108,   0,   0,   0, 109,  79, 110,   0, 111, 112,  42,  59, 113,
      0,   0,   0,   0,  29,   0,  27,   0,   0,   0,   0, 114,   0,   0,   0,   0,
      0,   0,   5, 115,   0,   0,   0,   0,  29,  29,   0,   0,   0,   0,   0,   0,
      0,   0, 116,  29,   0,   0, 117, 118,   0, 111,   0,   0, 119,   0,   0,   0,
      0,   0, 120,   0,   0, 121,  94,   0,   0,   0,  86, 122,   0,   0, 123,   0,
      0, 124,   0,   0,   0, 103,   0,   0,   0,   0,   0,   0,   0,   0, 125,   0,
      0,   0,   0,   0,   0,   0, 126,   0,   0,   0, 127,   0,   0,   0,   0,   0,
      0,  53,   0,   0,   0,   0,   0,   0,   0,   0,   0, 128,   0,   0,   0,   0,
      0,   0,   0,  98,   0,   0,   0, 129,   0, 110, 130,   0,   0,   0,   0,   0,
      0,   0,   0,   0, 131,   0,   0,   0,  50,  50,  50,  50,  50,  50,  50,  70,
     50, 132,  50, 133, 134, 135,  50,  40,  50,  50, 136,   0,   0,   0,   0,   0,
     50,  50,  93,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 137,  39,
    129, 129, 114, 114, 103, 103, 138,   0,   0, 139,   0, 140, 141,   0,   0,   0,
     50, 142,  50,  50,  81, 143, 144,  70,  59, 145,  38, 146, 147,   0,   0, 148,
    149,  68, 150,   0,   0,   0,   0,   0,  50,  50,  50,  80,  50, 151,  50,  50,
     50,  50,  50,  50,  50,  50,  89, 152,  50,  50,  50,  81,  50,  50, 153,   0,
    142,  50, 154,  50,  60,  21,   0,   0, 116,   0,   0,   0, 155,   0,  42,   0,
};

static RE_UINT8 re_posix_punct_stage_5[] = {
      0,   0,   0,   0, 254, 255,   0, 252,   1,   0,   0, 248,   1,   0,   0, 120,
    254, 219, 211, 137,   0,   0, 128,   0,  60,   0, 252, 255, 224, 175, 255, 255,
      0,   0,  32,  64, 176,   0,   0,   0,   0,   0,  64,   0,   4,   0,   0,   0,
      0,   0,   0, 252,   0, 230,   0,   0,   0,   0,   0,  64,  73,   0,   0,   0,
      0,   0,  24,   0, 192, 255,   0, 200,   0,  60,   0,   0,   0,   0,  16,  64,
      0,   2,   0,  96, 255,  63,   0,   0,   0,   0, 192,   3,   0,   0, 255, 127,
     48,   0,   1,   0,   0,   0,  12,  12,   0,   0,   3,   0,   0,   0,   1,   0,
      0,   0, 248,   7,   0,   0,   0, 128,   0,   0,   0,   2,   0,   0,  16,   0,
      0, 128,   0,  12, 254, 255, 255, 252,   0,   0,  80,  61,  32,   0,   0,   0,
      0,   0,   0, 192, 191, 223, 255,   7,   0, 252,   0,   0,   0,   0,   0,   8,
    255,   1,   0,   0,   0,   0, 255,   3,   1,   0,   0,   0,   0,  96,   0,   0,
      0,   0,   0,  24,   0,  56,   0,   0,   0,   0,  96,   0,   0,   0, 112,  15,
    255,   7,   0,   0,  49,   0,   0,   0, 255, 255, 255, 255, 127,  63,   0,   0,
    255,   7, 240,  31,   0,   0,   0, 240,   0,   0,   0, 248, 255,   0,   8,   0,
      0,   0,   0, 160,   3, 224,   0, 224,   0, 224,   0,  96,   0,   0, 255, 255,
    255,   0, 255, 255, 255, 255, 255, 127,   0,   0,   0, 124,   0, 124,   0,   0,
    123,   3, 208, 193, 175,  66,   0,  12,  31, 188,   0,   0,   0,  12, 255, 255,
    255, 255, 255,   7, 127,   0,   0,   0, 255, 255,  63,   0,   0,   0, 240, 255,
    255, 255, 207, 255, 255, 255,  63, 255, 255, 255, 255, 227, 255, 253,   3,   0,
      0, 240,   0,   0, 224,   7,   0, 222, 255, 127, 255, 255,   7,   0,   0,   0,
    255, 255, 255, 251, 255, 255,  15,   0,   0,   0, 255,  15,  30, 255, 255, 255,
      1,   0, 193, 224,   0,   0, 195, 255,  15,   0,   0,   0,   0, 252, 255, 255,
    255,   0,   1,   0, 255, 255,   1,   0,   0, 224,   0,   0,   0,   0,   8,  64,
      0,   0, 252,   0, 255, 255, 127,   0,   3,   0,   0,   0,   0,   6,   0,   0,
      0,  15, 192,   3,   0,   0, 240,   0,   0, 192,   0,   0,   0,   0,   0,  23,
    254,  63,   0, 192,   0,   0, 128,   3,   0,   8,   0,   0,   0,   2,   0,   0,
      0,   0, 252, 255,   0,   0,   0,  48, 255, 255, 247, 255, 127,  15,   0,   0,
     63,   0,   0,   0, 127, 127,   0,  48,   0,   0, 128, 255,   0,   0,   0, 254,
    255,  19, 255,  15, 255, 255, 255,  31,   0, 128,   0,   0,   0,   0, 128,   1,
      0,   0, 255,   1,   0,   1,   0,   0,   0,   0, 127,   0,   0,   0,   0,  30,
    128,  63,   0,   0,   0,   0,   0, 216,   0,   0,  48,   0, 224,  35,   0, 232,
      0,   0,   0,  63,  64,   0,   0,   0, 254, 255, 255,   0,  14,   0,   0,   0,
      0,   0,  31,   0,   0,   0,  32,   0,  48,   0,   0,   0,   0,   0,   0, 144,
    127, 254, 255, 255,  31,  28,   0,   0,  24, 240, 255, 255, 255, 195, 255, 255,
     35,   0,   0,   0,   2,   0,   0,   8,   8,   0,   0,   0,   0,   0, 128,   7,
      0, 224, 223, 255, 239,  15,   0,   0, 255,  15, 255, 255, 255, 127, 254, 255,
    254, 255, 254, 255, 255, 127,   0,   0,   0,  12,   0,   0,   0, 252, 255,   7,
    192, 255, 255, 255,   7,   0, 255, 255, 255,   1,   3,   0, 239, 255, 255, 255,
    255,  31,  15,   0, 255, 255,  31,   0, 255,   0, 255,   3,  31,   0,   0,   0,
};

/* Posix_Punct: 1609 bytes. */

RE_UINT32 re_get_posix_punct(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_posix_punct_stage_1[f] << 5;
    f = code >> 11;
    code ^= f << 11;
    pos = (RE_UINT32)re_posix_punct_stage_2[pos + f] << 3;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_posix_punct_stage_3[pos + f] << 3;
    f = code >> 5;
    code ^= f << 5;
    pos = (RE_UINT32)re_posix_punct_stage_4[pos + f] << 5;
    pos += code;
    value = (re_posix_punct_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* Posix_XDigit. */

static RE_UINT8 re_posix_xdigit_stage_1[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1,
};

static RE_UINT8 re_posix_xdigit_stage_2[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
};

static RE_UINT8 re_posix_xdigit_stage_3[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
};

static RE_UINT8 re_posix_xdigit_stage_4[] = {
    0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
};

static RE_UINT8 re_posix_xdigit_stage_5[] = {
      0,   0,   0,   0,   0,   0, 255,   3, 126,   0,   0,   0, 126,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
};

/* Posix_XDigit: 97 bytes. */

RE_UINT32 re_get_posix_xdigit(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;

    f = ch >> 16;
    code = ch ^ (f << 16);
    pos = (RE_UINT32)re_posix_xdigit_stage_1[f] << 3;
    f = code >> 13;
    code ^= f << 13;
    pos = (RE_UINT32)re_posix_xdigit_stage_2[pos + f] << 3;
    f = code >> 10;
    code ^= f << 10;
    pos = (RE_UINT32)re_posix_xdigit_stage_3[pos + f] << 3;
    f = code >> 7;
    code ^= f << 7;
    pos = (RE_UINT32)re_posix_xdigit_stage_4[pos + f] << 7;
    pos += code;
    value = (re_posix_xdigit_stage_5[pos >> 3] >> (pos & 0x7)) & 0x1;

    return value;
}

/* All_Cases. */

static RE_UINT8 re_all_cases_stage_1[] = {
    0, 1, 2, 2, 2, 3, 2, 4, 5, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2,
};

static RE_UINT8 re_all_cases_stage_2[] = {
     0,  1,  2,  3,  4,  5,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     7,  6,  6,  8,  6,  6,  6,  6,  6,  6,  6,  6,  6,  9, 10, 11,
     6, 12,  6,  6, 13,  6,  6,  6,  6,  6,  6,  6, 14, 15,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     6,  6,  6,  6,  6,  6, 16, 17,  6,  6,  6, 18,  6,  6,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6, 19,  6,  6,  6, 20,
     6,  6,  6,  6, 21,  6,  6,  6,  6,  6,  6,  6, 22,  6,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6, 23,  6,  6,  6,  6,  6,  6,  6,
};

static RE_UINT8 re_all_cases_stage_3[] = {
      0,   0,   0,   0,   0,   0,   0,   0,   1,   2,   3,   4,   5,   6,   7,   8,
      0,   0,   0,   0,   0,   0,   9,   0,  10,  11,  12,  13,  14,  15,  16,  17,
     18,  18,  18,  18,  18,  18,  19,  20,  21,  22,  18,  18,  18,  18,  18,  23,
     24,  25,  26,  27,  28,  29,  30,  31,  32,  33,  21,  34,  18,  18,  35,  18,
     18,  18,  18,  18,  36,  18,  37,  38,  39,  18,  40,  41,  42,  43,  44,  45,
     46,  47,  48,  49,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,  50,   0,   0,   0,   0,   0,  51,  52,
     53,  54,  55,  56,  57,  58,  59,  60,  61,  62,  63,  18,  18,  18,  64,  65,
     66,  66,  11,  11,  11,  11,  15,  15,  15,  15,  67,  67,  18,  18,  18,  18,
     68,  69,  18,  18,  18,  18,  18,  18,  70,  71,  18,  18,  18,  18,  18,  18,
     18,  18,  18,  18,  18,  18,  72,  73,  73,  73,  74,   0,  75,  76,  76,  76,
     77,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,  78,  78,  78,  78,  79,  80,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,  81,  81,  81,  81,  81,  81,  81,  81,  81,  81,  82,  83,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  84,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
     18,  18,  18,  18,  18,  18,  18,  18,  18,  18,  18,  18,  85,  18,  18,  18,
     18,  18,  86,  87,  18,  18,  18,  18,  18,  18,  18,  18,  18,  18,  18,  18,
     88,  89,  82,  83,  88,  89,  88,  89,  82,  83,  90,  91,  88,  89,  92,  93,
     88,  89,  88,  89,  88,  89,  94,  95,  96,  97,  98,  99, 100, 101,  96, 102,
      0,   0,   0,   0, 103, 104, 105,   0,   0, 106,   0,   0, 107, 107, 108, 108,
    109,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0, 110, 111, 111, 111, 112, 112, 112, 113,   0,   0,
     73,  73,  73,  73,  73,  74,  76,  76,  76,  76,  76,  77, 114, 115, 116, 117,
     18,  18,  18,  18,  18,  18,  18,  18,  18,  18,  18,  18,  37, 118, 119,   0,
    120, 120, 120, 120, 121, 122,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,  18,  18,  18,  18,  18,  86,   0,   0,
     18,  18,  18,  37,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,  69,  18,  69,  18,  18,  18,  18,  18,  18,  18,   0, 123,
     18, 124,  51,  18,  18, 125, 126,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 127,   0,   0,   0, 128, 128,
    128, 128, 128, 128, 128, 128, 128, 128,   0,   0,   0,   0,   0,   0,   0,   0,
    129,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   1,  11,  11,   4,   5,  15,  15,   8,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
    130, 130, 130, 130, 130, 131, 131, 131, 131, 131,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
    132, 132, 132, 132, 132, 132, 133,   0, 134, 134, 134, 134, 134, 134, 135,   0,
      0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,  11,  11,  11,  11,  15,  15,  15,  15,   0,   0,   0,   0,
};

static RE_UINT8 re_all_cases_stage_4[] = {
      0,   0,   0,   0,   0,   0,   0,   0,   0,   1,   1,   1,   1,   1,   1,   1,
      1,   2,   1,   3,   1,   1,   1,   1,   1,   1,   1,   4,   1,   1,   1,   1,
      1,   1,   1,   0,   0,   0,   0,   0,   0,   5,   5,   5,   5,   5,   5,   5,
      5,   6,   5,   7,   5,   5,   5,   5,   5,   5,   5,   8,   5,   5,   5,   5,
      5,   5,   5,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   9,   0,   0,
      1,   1,   1,   1,   1,  10,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,
      1,   1,   1,   1,   1,   1,   1,   0,   1,   1,   1,   1,   1,   1,   1,  11,
      5,   5,   5,   5,   5,  12,   5,   5,   5,   5,   5,   5,   5,   5,   5,   5,
      5,   5,   5,   5,   5,   5,   5,   0,   5,   5,   5,   5,   5,   5,   5,  13,
     14,  15,  14,  15,  14,  15,  14,  15,  16,  17,  14,  15,  14,  15,  14,  15,
      0,  14,  15,  14,  15,  14,  15,  14,  15,  14,  15,  14,  15,  14,  15,  14,
     15,   0,  14,  15,  14,  15,  14,  15,  18,  14,  15,  14,  15,  14,  15,  19,
     20,  21,  14,  15,  14,  15,  22,  14,  15,  23,  23,  14,  15,   0,  24,  25,
     26,  14,  15,  23,  27,  28,  29,  30,  14,  15,  31,   0,  29,  32,  33,  34,
     14,  15,  14,  15,  14,  15,  35,  14,  15,  35,   0,   0,  14,  15,  35,  14,
     15,  36,  36,  14,  15,  14,  15,  37,  14,  15,   0,   0,  14,  15,   0,  38,
      0,   0,   0,   0,  39,  40,  41,  39,  40,  41,  39,  40,  41,  14,  15,  14,
     15,  14,  15,  14,  15,  42,  14,  15,   0,  39,  40,  41,  14,  15,  43,  44,
     45,   0,  14,  15,  14,  15,  14,  15,  14,  15,  14,  15,   0,   0,   0,   0,
      0,   0,  46,  14,  15,  47,  48,  49,  49,  14,  15,  50,  51,  52,  14,  15,
     53,  54,  55,  56,  57,   0,  58,  58,   0,  59,   0,  60,  61,   0,   0,   0,
     58,  62,   0,  63,   0,  64,  65,   0,  66,  67,   0,  68,  69,   0,   0,  67,
      0,  70,  71,   0,   0,  72,   0,   0,   0,   0,   0,   0,   0,  73,   0,   0,
     74,   0,   0,  74,   0,   0,   0,  75,  74,  76,  77,  77,  78,   0,   0,   0,
      0,   0,  79,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  80,  81,   0,
      0,   0,   0,   0,   0,  82,   0,   0,  14,  15,  14,  15,   0,   0,  14,  15,
      0,   0,   0,  33,  33,  33,   0,  83,   0,   0,   0,   0,   0,   0,  84,   0,
     85,  85,  85,   0,  86,   0,  87,  87,  88,   1,  89,   1,   1,  90,   1,   1,
     91,  92,  93,   1,  94,   1,   1,   1,  95,  96,   0,  97,   1,   1,  98,   1,
      1,  99,   1,   1, 100, 101, 101, 101, 102,   5, 103,   5,   5, 104,   5,   5,
    105, 106, 107,   5, 108,   5,   5,   5, 109, 110, 111, 112,   5,   5, 113,   5,
      5, 114,   5,   5, 115, 116, 116, 117, 118, 119,   0,   0,   0, 120, 121, 122,
    123, 124, 125, 126, 127, 128,   0,  14,  15, 129,  14,  15,   0,  45,  45,  45,
    130, 130, 130, 130, 130, 130, 130, 130, 131, 131, 131, 131, 131, 131, 131, 131,
     14,  15,   0,   0,   0,   0,   0,   0,   0,   0,  14,  15,  14,  15,  14,  15,
    132,  14,  15,  14,  15,  14,  15,  14,  15,  14,  15,  14,  15,  14,  15, 133,
      0, 134, 134, 134, 134, 134, 134, 134, 134, 134, 134, 134, 134, 134, 134, 134,
    134, 134, 134, 134, 134, 134, 134,   0,   0, 135, 135, 135, 135, 135, 135, 135,
    135, 135, 135, 135, 135, 135, 135, 135, 135, 135, 135, 135, 135, 135, 135,   0,
    136, 136, 136, 136, 136, 136, 136, 136, 136, 136, 136, 136, 136, 136,   0, 136,
      0,   0,   0,   0,   0, 136,   0,   0, 137, 137, 137, 137, 137, 137, 137, 137,
    117, 117, 117, 117, 117, 117,   0,   0, 122, 122, 122, 122, 122, 122,   0,   0,
      0, 138,   0,   0,   0, 139,   0,   0, 140, 141,  14,  15,  14,  15,  14,  15,
     14,  15,  14,  15,  14,  15,   0,   0,   0,   0,   0, 142,   0,   0, 143,   0,
    117, 117, 117, 117, 117, 117, 117, 117, 122, 122, 122, 122, 122, 122, 122, 122,
      0, 117,   0, 117,   0, 117,   0, 117,   0, 122,   0, 122,   0, 122,   0, 122,
    144, 144, 145, 145, 145, 145, 146, 146, 147, 147, 148, 148, 149, 149,   0,   0,
    117, 117,   0, 150,   0,   0,   0,   0, 122, 122, 151, 151, 152,   0, 153,   0,
      0,   0,   0, 150,   0,   0,   0,   0, 154, 154, 154, 154, 152,   0,   0,   0,
    117, 117,   0, 155,   0,   0,   0,   0, 122, 122, 156, 156,   0,   0,   0,   0,
    117, 117,   0, 157,   0, 125,   0,   0, 122, 122, 158, 158, 129,   0,   0,   0,
    159, 159, 160, 160, 152,   0,   0,   0,   0,   0,   0,   0,   0,   0, 161,   0,
      0,   0, 162, 163,   0,   0,   0,   0,   0,   0, 164,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0, 165,   0, 166, 166, 166, 166, 166, 166, 166, 166,
    167, 167, 167, 167, 167, 167, 167, 167,   0,   0,   0,  14,  15,   0,   0,   0,
      0,   0,   0,   0,   0,   0, 168, 168, 168, 168, 168, 168, 168, 168, 168, 168,
    169, 169, 169, 169, 169, 169, 169, 169, 169, 169,   0,   0,   0,   0,   0,   0,
     14,  15, 170, 171, 172, 173, 174,  14,  15,  14,  15,  14,  15, 175, 176, 177,
    178,   0,  14,  15,   0,  14,  15,   0,   0,   0,   0,   0,   0,   0, 179, 179,
      0,   0,   0,  14,  15,  14,  15,   0,   0,   0,  14,  15,   0,   0,   0,   0,
    180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180,   0, 180,
      0,   0,   0,   0,   0, 180,   0,   0,   0,  14,  15,  14,  15, 181,  14,  15,
      0,   0,   0,  14,  15, 182,   0,   0,  14,  15, 183, 184, 185, 186,   0,   0,
    187, 188, 189, 190,  14,  15,  14,  15,   0,   0,   0, 191,   0,   0,   0,   0,
    192, 192, 192, 192, 192, 192, 192, 192,   0,   0,   0,   0,   0,  14,  15,   0,
    193, 193, 193, 193, 193, 193, 193, 193, 194, 194, 194, 194, 194, 194, 194, 194,
     86,  86,  86,  86,  86,  86,  86,  86,  86,  86,  86,   0,   0,   0,   0,   0,
    115, 115, 115, 115, 115, 115, 115, 115, 115, 115, 115,   0,   0,   0,   0,   0,
};

/* All_Cases: 2184 bytes. */

static RE_AllCases re_all_cases_table[] = {
    {{     0,     0,     0}},
    {{    32,     0,     0}},
    {{    32,   232,     0}},
    {{    32,  8415,     0}},
    {{    32,   300,     0}},
    {{   -32,     0,     0}},
    {{   -32,   199,     0}},
    {{   -32,  8383,     0}},
    {{   -32,   268,     0}},
    {{   743,   775,     0}},
    {{    32,  8294,     0}},
    {{  7615,     0,     0}},
    {{   -32,  8262,     0}},
    {{   121,     0,     0}},
    {{     1,     0,     0}},
    {{    -1,     0,     0}},
    {{  -199,     0,     0}},
    {{  -232,     0,     0}},
    {{  -121,     0,     0}},
    {{  -300,  -268,     0}},
    {{   195,     0,     0}},
    {{   210,     0,     0}},
    {{   206,     0,     0}},
    {{   205,     0,     0}},
    {{    79,     0,     0}},
    {{   202,     0,     0}},
    {{   203,     0,     0}},
    {{   207,     0,     0}},
    {{    97,     0,     0}},
    {{   211,     0,     0}},
    {{   209,     0,     0}},
    {{   163,     0,     0}},
    {{   213,     0,     0}},
    {{   130,     0,     0}},
    {{   214,     0,     0}},
    {{   218,     0,     0}},
    {{   217,     0,     0}},
    {{   219,     0,     0}},
    {{    56,     0,     0}},
    {{     1,     2,     0}},
    {{    -1,     1,     0}},
    {{    -2,    -1,     0}},
    {{   -79,     0,     0}},
    {{   -97,     0,     0}},
    {{   -56,     0,     0}},
    {{  -130,     0,     0}},
    {{ 10795,     0,     0}},
    {{  -163,     0,     0}},
    {{ 10792,     0,     0}},
    {{ 10815,     0,     0}},
    {{  -195,     0,     0}},
    {{    69,     0,     0}},
    {{    71,     0,     0}},
    {{ 10783,     0,     0}},
    {{ 10780,     0,     0}},
    {{ 10782,     0,     0}},
    {{  -210,     0,     0}},
    {{  -206,     0,     0}},
    {{  -205,     0,     0}},
    {{  -202,     0,     0}},
    {{  -203,     0,     0}},
    {{ 42319,     0,     0}},
    {{ 42315,     0,     0}},
    {{  -207,     0,     0}},
    {{ 42280,     0,     0}},
    {{ 42308,     0,     0}},
    {{  -209,     0,     0}},
    {{  -211,     0,     0}},
    {{ 10743,     0,     0}},
    {{ 42305,     0,     0}},
    {{ 10749,     0,     0}},
    {{  -213,     0,     0}},
    {{  -214,     0,     0}},
    {{ 10727,     0,     0}},
    {{  -218,     0,     0}},
    {{ 42282,     0,     0}},
    {{   -69,     0,     0}},
    {{  -217,     0,     0}},
    {{   -71,     0,     0}},
    {{  -219,     0,     0}},
    {{ 42261,     0,     0}},
    {{ 42258,     0,     0}},
    {{    84,   116,  7289}},
    {{   116,     0,     0}},
    {{    38,     0,     0}},
    {{    37,     0,     0}},
    {{    64,     0,     0}},
    {{    63,     0,     0}},
    {{  7235,     0,     0}},
    {{    32,    62,     0}},
    {{    32,    96,     0}},
    {{    32,    57,    92}},
    {{   -84,    32,  7205}},
    {{    32,    86,     0}},
    {{  -743,    32,     0}},
    {{    32,    54,     0}},
    {{    32,    80,     0}},
    {{    31,    32,     0}},
    {{    32,    47,     0}},
    {{    32,  7549,     0}},
    {{   -38,     0,     0}},
    {{   -37,     0,     0}},
    {{  7219,     0,     0}},
    {{   -32,    30,     0}},
    {{   -32,    64,     0}},
    {{   -32,    25,    60}},
    {{  -116,   -32,  7173}},
    {{   -32,    54,     0}},
    {{  -775,   -32,     0}},
    {{   -32,    22,     0}},
    {{   -32,    48,     0}},
    {{   -31,     1,     0}},
    {{   -32,    -1,     0}},
    {{   -32,    15,     0}},
    {{   -32,  7517,     0}},
    {{   -64,     0,     0}},
    {{   -63,     0,     0}},
    {{     8,     0,     0}},
    {{   -62,   -30,     0}},
    {{   -57,   -25,    35}},
    {{   -47,   -15,     0}},
    {{   -54,   -22,     0}},
    {{    -8,     0,     0}},
    {{   -86,   -54,     0}},
    {{   -80,   -48,     0}},
    {{     7,     0,     0}},
    {{  -116,     0,     0}},
    {{   -92,   -60,   -35}},
    {{   -96,   -64,     0}},
    {{    -7,     0,     0}},
    {{    80,     0,     0}},
    {{   -80,     0,     0}},
    {{    15,     0,     0}},
    {{   -15,     0,     0}},
    {{    48,     0,     0}},
    {{   -48,     0,     0}},
    {{  7264,     0,     0}},
    {{ 38864,     0,     0}},
    {{ 35332,     0,     0}},
    {{  3814,     0,     0}},
    {{     1,    59,     0}},
    {{    -1,    58,     0}},
    {{   -59,   -58,     0}},
    {{ -7615,     0,     0}},
    {{    74,     0,     0}},
    {{    86,     0,     0}},
    {{   100,     0,     0}},
    {{   128,     0,     0}},
    {{   112,     0,     0}},
    {{   126,     0,     0}},
    {{     9,     0,     0}},
    {{   -74,     0,     0}},
    {{    -9,     0,     0}},
    {{ -7289, -7205, -7173}},
    {{   -86,     0,     0}},
    {{ -7235,     0,     0}},
    {{  -100,     0,     0}},
    {{ -7219,     0,     0}},
    {{  -112,     0,     0}},
    {{  -128,     0,     0}},
    {{  -126,     0,     0}},
    {{ -7549, -7517,     0}},
    {{ -8415, -8383,     0}},
    {{ -8294, -8262,     0}},
    {{    28,     0,     0}},
    {{   -28,     0,     0}},
    {{    16,     0,     0}},
    {{   -16,     0,     0}},
    {{    26,     0,     0}},
    {{   -26,     0,     0}},
    {{-10743,     0,     0}},
    {{ -3814,     0,     0}},
    {{-10727,     0,     0}},
    {{-10795,     0,     0}},
    {{-10792,     0,     0}},
    {{-10780,     0,     0}},
    {{-10749,     0,     0}},
    {{-10783,     0,     0}},
    {{-10782,     0,     0}},
    {{-10815,     0,     0}},
    {{ -7264,     0,     0}},
    {{-35332,     0,     0}},
    {{-42280,     0,     0}},
    {{-42308,     0,     0}},
    {{-42319,     0,     0}},
    {{-42315,     0,     0}},
    {{-42305,     0,     0}},
    {{-42258,     0,     0}},
    {{-42282,     0,     0}},
    {{-42261,     0,     0}},
    {{   928,     0,     0}},
    {{  -928,     0,     0}},
    {{-38864,     0,     0}},
    {{    40,     0,     0}},
    {{   -40,     0,     0}},
};

/* All_Cases: 2340 bytes. */

int re_get_all_cases(RE_UINT32 ch, RE_UINT32* codepoints) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;
    RE_AllCases* all_cases;
    int count;

    f = ch >> 13;
    code = ch ^ (f << 13);
    pos = (RE_UINT32)re_all_cases_stage_1[f] << 5;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_all_cases_stage_2[pos + f] << 5;
    f = code >> 3;
    code ^= f << 3;
    pos = (RE_UINT32)re_all_cases_stage_3[pos + f] << 3;
    value = re_all_cases_stage_4[pos + code];

    all_cases = &re_all_cases_table[value];

    codepoints[0] = ch;
    count = 1;

    while (count < RE_MAX_CASES && all_cases->diffs[count - 1] != 0) {
        codepoints[count] = (RE_UINT32)((RE_INT32)ch + all_cases->diffs[count -
          1]);
        ++count;
    }

    return count;
}

/* Simple_Case_Folding. */

static RE_UINT8 re_simple_case_folding_stage_1[] = {
    0, 1, 2, 2, 2, 3, 2, 4, 5, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2,
};

static RE_UINT8 re_simple_case_folding_stage_2[] = {
     0,  1,  2,  3,  4,  5,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     7,  6,  6,  8,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  9, 10,
     6, 11,  6,  6, 12,  6,  6,  6,  6,  6,  6,  6, 13,  6,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     6,  6,  6,  6,  6,  6, 14, 15,  6,  6,  6, 16,  6,  6,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6, 17,
     6,  6,  6,  6, 18,  6,  6,  6,  6,  6,  6,  6, 19,  6,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6, 20,  6,  6,  6,  6,  6,  6,  6,
};

static RE_UINT8 re_simple_case_folding_stage_3[] = {
     0,  0,  0,  0,  0,  0,  0,  0,  1,  2,  2,  3,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  4,  0,  2,  2,  5,  5,  0,  0,  0,  0,
     6,  6,  6,  6,  6,  6,  7,  8,  8,  7,  6,  6,  6,  6,  6,  9,
    10, 11, 12, 13, 14, 15, 16, 17, 18, 19,  8, 20,  6,  6, 21,  6,
     6,  6,  6,  6, 22,  6, 23, 24, 25,  6,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0, 26,  0,  0,  0,  0,  0, 27, 28,
    29, 30,  1,  2, 31, 32,  0,  0, 33, 34, 35,  6,  6,  6, 36, 37,
    38, 38,  2,  2,  2,  2,  0,  0,  0,  0,  0,  0,  6,  6,  6,  6,
    39,  7,  6,  6,  6,  6,  6,  6, 40, 41,  6,  6,  6,  6,  6,  6,
     6,  6,  6,  6,  6,  6, 42, 43, 43, 43, 44,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0, 45, 45, 45, 45, 46, 47,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 48,
     6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     6,  6, 49, 50,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     0, 51,  0, 48,  0, 51,  0, 51,  0, 48,  0, 52,  0, 51,  0,  0,
     0, 51,  0, 51,  0, 51,  0, 53,  0, 54,  0, 55,  0, 56,  0, 57,
     0,  0,  0,  0, 58, 59, 60,  0,  0,  0,  0,  0, 61, 61,  0,  0,
    62,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0, 63, 64, 64, 64,  0,  0,  0,  0,  0,  0,
    43, 43, 43, 43, 43, 44,  0,  0,  0,  0,  0,  0, 65, 66, 67, 68,
     6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6, 23, 69, 33,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  6,  6,  6,  6,  6, 49,  0,  0,
     6,  6,  6, 23,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  7,  6,  7,  6,  6,  6,  6,  6,  6,  6,  0, 70,
     6, 71, 27,  6,  6, 72, 73,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 74, 74,
    74, 74, 74, 74, 74, 74, 74, 74,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  1,  2,  2,  3,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
    75, 75, 75, 75, 75,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
    76, 76, 76, 76, 76, 76, 77,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  2,  2,  2,  2,  0,  0,  0,  0,  0,  0,  0,  0,
};

static RE_UINT8 re_simple_case_folding_stage_4[] = {
     0,  0,  0,  0,  0,  0,  0,  0,  0,  1,  1,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  2,  0,  0,  1,  1,  1,  1,  1,  1,  1,  0,
     3,  0,  3,  0,  3,  0,  3,  0,  0,  0,  3,  0,  3,  0,  3,  0,
     0,  3,  0,  3,  0,  3,  0,  3,  4,  3,  0,  3,  0,  3,  0,  5,
     0,  6,  3,  0,  3,  0,  7,  3,  0,  8,  8,  3,  0,  0,  9, 10,
    11,  3,  0,  8, 12,  0, 13, 14,  3,  0,  0,  0, 13, 15,  0, 16,
     3,  0,  3,  0,  3,  0, 17,  3,  0, 17,  0,  0,  3,  0, 17,  3,
     0, 18, 18,  3,  0,  3,  0, 19,  3,  0,  0,  0,  3,  0,  0,  0,
     0,  0,  0,  0, 20,  3,  0, 20,  3,  0, 20,  3,  0,  3,  0,  3,
     0,  3,  0,  3,  0,  0,  3,  0,  0, 20,  3,  0,  3,  0, 21, 22,
    23,  0,  3,  0,  3,  0,  3,  0,  3,  0,  3,  0,  0,  0,  0,  0,
     0,  0, 24,  3,  0, 25, 26,  0,  0,  3,  0, 27, 28, 29,  3,  0,
     0,  0,  0,  0,  0, 30,  0,  0,  3,  0,  3,  0,  0,  0,  3,  0,
     0,  0,  0,  0,  0,  0,  0, 30,  0,  0,  0,  0,  0,  0, 31,  0,
    32, 32, 32,  0, 33,  0, 34, 34,  1,  1,  0,  1,  1,  1,  1,  1,
     1,  1,  1,  1,  0,  0,  0,  0,  0,  0,  3,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0, 35, 36, 37,  0,  0,  0, 38, 39,  0,
    40, 41,  0,  0, 42, 43,  0,  3,  0, 44,  3,  0,  0, 23, 23, 23,
    45, 45, 45, 45, 45, 45, 45, 45,  3,  0,  0,  0,  0,  0,  0,  0,
    46,  3,  0,  3,  0,  3,  0,  3,  0,  3,  0,  3,  0,  3,  0,  0,
     0, 47, 47, 47, 47, 47, 47, 47, 47, 47, 47, 47, 47, 47, 47, 47,
    47, 47, 47, 47, 47, 47, 47,  0, 48, 48, 48, 48, 48, 48, 48, 48,
    48, 48, 48, 48, 48, 48,  0, 48,  0,  0,  0,  0,  0, 48,  0,  0,
    49, 49, 49, 49, 49, 49,  0,  0,  3,  0,  3,  0,  3,  0,  0,  0,
     0,  0,  0, 50,  0,  0, 51,  0, 49, 49, 49, 49, 49, 49, 49, 49,
     0, 49,  0, 49,  0, 49,  0, 49, 49, 49, 52, 52, 53,  0, 54,  0,
    55, 55, 55, 55, 53,  0,  0,  0, 49, 49, 56, 56,  0,  0,  0,  0,
    49, 49, 57, 57, 44,  0,  0,  0, 58, 58, 59, 59, 53,  0,  0,  0,
     0,  0,  0,  0,  0,  0, 60,  0,  0,  0, 61, 62,  0,  0,  0,  0,
     0,  0, 63,  0,  0,  0,  0,  0, 64, 64, 64, 64, 64, 64, 64, 64,
     0,  0,  0,  3,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 65, 65,
    65, 65, 65, 65, 65, 65, 65, 65,  3,  0, 66, 67, 68,  0,  0,  3,
     0,  3,  0,  3,  0, 69, 70, 71, 72,  0,  3,  0,  0,  3,  0,  0,
     0,  0,  0,  0,  0,  0, 73, 73,  0,  0,  0,  3,  0,  3,  0,  0,
     0,  3,  0,  3,  0, 74,  3,  0,  0,  0,  0,  3,  0, 75,  0,  0,
     3,  0, 76, 77, 78, 79,  0,  0, 80, 81, 82, 83,  3,  0,  3,  0,
    84, 84, 84, 84, 84, 84, 84, 84, 85, 85, 85, 85, 85, 85, 85, 85,
    33, 33, 33, 33, 33, 33, 33, 33, 33, 33, 33,  0,  0,  0,  0,  0,
};

/* Simple_Case_Folding: 1624 bytes. */

static RE_INT32 re_simple_case_folding_table[] = {
         0,
        32,
       775,
         1,
      -121,
      -268,
       210,
       206,
       205,
        79,
       202,
       203,
       207,
       211,
       209,
       213,
       214,
       218,
       217,
       219,
         2,
       -97,
       -56,
      -130,
     10795,
      -163,
     10792,
      -195,
        69,
        71,
       116,
        38,
        37,
        64,
        63,
         8,
       -30,
       -25,
       -15,
       -22,
       -54,
       -48,
       -60,
       -64,
        -7,
        80,
        15,
        48,
      7264,
        -8,
       -58,
     -7615,
       -74,
        -9,
     -7173,
       -86,
      -100,
      -112,
      -128,
      -126,
     -7517,
     -8383,
     -8262,
        28,
        16,
        26,
    -10743,
     -3814,
    -10727,
    -10780,
    -10749,
    -10783,
    -10782,
    -10815,
    -35332,
    -42280,
    -42308,
    -42319,
    -42315,
    -42305,
    -42258,
    -42282,
    -42261,
       928,
    -38864,
        40,
};

/* Simple_Case_Folding: 344 bytes. */

RE_UINT32 re_get_simple_case_folding(RE_UINT32 ch) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;
    RE_INT32 diff;

    f = ch >> 13;
    code = ch ^ (f << 13);
    pos = (RE_UINT32)re_simple_case_folding_stage_1[f] << 5;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_simple_case_folding_stage_2[pos + f] << 5;
    f = code >> 3;
    code ^= f << 3;
    pos = (RE_UINT32)re_simple_case_folding_stage_3[pos + f] << 3;
    value = re_simple_case_folding_stage_4[pos + code];

    diff = re_simple_case_folding_table[value];

    return (RE_UINT32)((RE_INT32)ch + diff);
}

/* Full_Case_Folding. */

static RE_UINT8 re_full_case_folding_stage_1[] = {
    0, 1, 2, 2, 2, 3, 2, 4, 5, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2,
};

static RE_UINT8 re_full_case_folding_stage_2[] = {
     0,  1,  2,  3,  4,  5,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     7,  6,  6,  8,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  9, 10,
     6, 11,  6,  6, 12,  6,  6,  6,  6,  6,  6,  6, 13,  6,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     6,  6,  6,  6,  6,  6, 14, 15,  6,  6,  6, 16,  6,  6,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6, 17,  6,  6,  6, 18,
     6,  6,  6,  6, 19,  6,  6,  6,  6,  6,  6,  6, 20,  6,  6,  6,
     6,  6,  6,  6,  6,  6,  6,  6, 21,  6,  6,  6,  6,  6,  6,  6,
};

static RE_UINT8 re_full_case_folding_stage_3[] = {
     0,  0,  0,  0,  0,  0,  0,  0,  1,  2,  2,  3,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  4,  0,  2,  2,  5,  6,  0,  0,  0,  0,
     7,  7,  7,  7,  7,  7,  8,  9,  9, 10,  7,  7,  7,  7,  7, 11,
    12, 13, 14, 15, 16, 17, 18, 19, 20, 21,  9, 22,  7,  7, 23,  7,
     7,  7,  7,  7, 24,  7, 25, 26, 27,  7,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0, 28,  0,  0,  0,  0,  0, 29, 30,
    31, 32, 33,  2, 34, 35, 36,  0, 37, 38, 39,  7,  7,  7, 40, 41,
    42, 42,  2,  2,  2,  2,  0,  0,  0,  0,  0,  0,  7,  7,  7,  7,
    43, 44,  7,  7,  7,  7,  7,  7, 45, 46,  7,  7,  7,  7,  7,  7,
     7,  7,  7,  7,  7,  7, 47, 48, 48, 48, 49,  0,  0,  0,  0,  0,
    50,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0, 51, 51, 51, 51, 52, 53,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 54,
     7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,
     7,  7, 55, 56,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,
     0, 57,  0, 54,  0, 57,  0, 57,  0, 54, 58, 59,  0, 57,  0,  0,
    60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75,
     0,  0,  0,  0, 76, 77, 78,  0,  0,  0,  0,  0, 79, 79,  0,  0,
    80,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0, 81, 82, 82, 82,  0,  0,  0,  0,  0,  0,
    48, 48, 48, 48, 48, 49,  0,  0,  0,  0,  0,  0, 83, 84, 85, 86,
     7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7, 25, 87, 37,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  7,  7,  7,  7,  7, 88,  0,  0,
     7,  7,  7, 25,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0, 44,  7, 44,  7,  7,  7,  7,  7,  7,  7,  0, 89,
     7, 90, 29,  7,  7, 91, 92,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 93, 93,
    93, 93, 93, 93, 93, 93, 93, 93,  0,  0,  0,  0,  0,  0,  0,  0,
    94,  0, 95,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  1,  2,  2,  3,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
    96, 96, 96, 96, 96,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
    97, 97, 97, 97, 97, 97, 98,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  2,  2,  2,  2,  0,  0,  0,  0,  0,  0,  0,  0,
};

static RE_UINT8 re_full_case_folding_stage_4[] = {
      0,   0,   0,   0,   0,   0,   0,   0,   0,   1,   1,   1,   1,   1,   1,   1,
      1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   2,   0,   0,   1,   1,   1,   1,   1,   1,   1,   0,
      1,   1,   1,   1,   1,   1,   1,   3,   4,   0,   4,   0,   4,   0,   4,   0,
      5,   0,   4,   0,   4,   0,   4,   0,   0,   4,   0,   4,   0,   4,   0,   4,
      0,   6,   4,   0,   4,   0,   4,   0,   7,   4,   0,   4,   0,   4,   0,   8,
      0,   9,   4,   0,   4,   0,  10,   4,   0,  11,  11,   4,   0,   0,  12,  13,
     14,   4,   0,  11,  15,   0,  16,  17,   4,   0,   0,   0,  16,  18,   0,  19,
      4,   0,   4,   0,   4,   0,  20,   4,   0,  20,   0,   0,   4,   0,  20,   4,
      0,  21,  21,   4,   0,   4,   0,  22,   4,   0,   0,   0,   4,   0,   0,   0,
      0,   0,   0,   0,  23,   4,   0,  23,   4,   0,  23,   4,   0,   4,   0,   4,
      0,   4,   0,   4,   0,   0,   4,   0,  24,  23,   4,   0,   4,   0,  25,  26,
     27,   0,   4,   0,   4,   0,   4,   0,   4,   0,   4,   0,   0,   0,   0,   0,
      0,   0,  28,   4,   0,  29,  30,   0,   0,   4,   0,  31,  32,  33,   4,   0,
      0,   0,   0,   0,   0,  34,   0,   0,   4,   0,   4,   0,   0,   0,   4,   0,
      0,   0,   0,   0,   0,   0,   0,  34,   0,   0,   0,   0,   0,   0,  35,   0,
     36,  36,  36,   0,  37,   0,  38,  38,  39,   1,   1,   1,   1,   1,   1,   1,
      1,   1,   0,   1,   1,   1,   1,   1,   1,   1,   1,   1,   0,   0,   0,   0,
     40,   0,   0,   0,   0,   0,   0,   0,   0,   0,   4,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,  41,  42,  43,   0,   0,   0,  44,  45,   0,
     46,  47,   0,   0,  48,  49,   0,   4,   0,  50,   4,   0,   0,  27,  27,  27,
     51,  51,  51,  51,  51,  51,  51,  51,   4,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   4,   0,   4,   0,   4,   0,  52,   4,   0,   4,   0,   4,   0,   4,
      0,   4,   0,   4,   0,   4,   0,   0,   0,  53,  53,  53,  53,  53,  53,  53,
     53,  53,  53,  53,  53,  53,  53,  53,  53,  53,  53,  53,  53,  53,  53,   0,
      0,   0,   0,   0,   0,   0,   0,  54,  55,  55,  55,  55,  55,  55,  55,  55,
     55,  55,  55,  55,  55,  55,   0,  55,   0,   0,   0,   0,   0,  55,   0,   0,
     56,  56,  56,  56,  56,  56,   0,   0,   4,   0,   4,   0,   4,   0,  57,  58,
     59,  60,  61,  62,   0,   0,  63,   0,  56,  56,  56,  56,  56,  56,  56,  56,
     64,   0,  65,   0,  66,   0,  67,   0,   0,  56,   0,  56,   0,  56,   0,  56,
     68,  68,  68,  68,  68,  68,  68,  68,  69,  69,  69,  69,  69,  69,  69,  69,
     70,  70,  70,  70,  70,  70,  70,  70,  71,  71,  71,  71,  71,  71,  71,  71,
     72,  72,  72,  72,  72,  72,  72,  72,  73,  73,  73,  73,  73,  73,  73,  73,
      0,   0,  74,  75,  76,   0,  77,  78,  56,  56,  79,  79,  80,   0,  81,   0,
      0,   0,  82,  83,  84,   0,  85,  86,  87,  87,  87,  87,  88,   0,   0,   0,
      0,   0,  89,  90,   0,   0,  91,  92,  56,  56,  93,  93,   0,   0,   0,   0,
      0,   0,  94,  95,  96,   0,  97,  98,  56,  56,  99,  99,  50,   0,   0,   0,
      0,   0, 100, 101, 102,   0, 103, 104, 105, 105, 106, 106, 107,   0,   0,   0,
      0,   0,   0,   0,   0,   0, 108,   0,   0,   0, 109, 110,   0,   0,   0,   0,
      0,   0, 111,   0,   0,   0,   0,   0, 112, 112, 112, 112, 112, 112, 112, 112,
      0,   0,   0,   4,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 113, 113,
    113, 113, 113, 113, 113, 113, 113, 113,   4,   0, 114, 115, 116,   0,   0,   4,
      0,   4,   0,   4,   0, 117, 118, 119, 120,   0,   4,   0,   0,   4,   0,   0,
      0,   0,   0,   0,   0,   0, 121, 121,   0,   0,   0,   4,   0,   4,   0,   0,
      4,   0,   4,   0,   4,   0,   0,   0,   0,   4,   0,   4,   0, 122,   4,   0,
      0,   0,   0,   4,   0, 123,   0,   0,   4,   0, 124, 125, 126, 127,   0,   0,
    128, 129, 130, 131,   4,   0,   4,   0, 132, 132, 132, 132, 132, 132, 132, 132,
    133, 134, 135, 136, 137, 138, 139,   0,   0,   0,   0, 140, 141, 142, 143, 144,
    145, 145, 145, 145, 145, 145, 145, 145,  37,  37,  37,  37,  37,  37,  37,  37,
     37,  37,  37,   0,   0,   0,   0,   0,
};

/* Full_Case_Folding: 1824 bytes. */

static RE_FullCaseFolding re_full_case_folding_table[] = {
    {     0, {   0,   0}},
    {    32, {   0,   0}},
    {   775, {   0,   0}},
    {  -108, { 115,   0}},
    {     1, {   0,   0}},
    {  -199, { 775,   0}},
    {   371, { 110,   0}},
    {  -121, {   0,   0}},
    {  -268, {   0,   0}},
    {   210, {   0,   0}},
    {   206, {   0,   0}},
    {   205, {   0,   0}},
    {    79, {   0,   0}},
    {   202, {   0,   0}},
    {   203, {   0,   0}},
    {   207, {   0,   0}},
    {   211, {   0,   0}},
    {   209, {   0,   0}},
    {   213, {   0,   0}},
    {   214, {   0,   0}},
    {   218, {   0,   0}},
    {   217, {   0,   0}},
    {   219, {   0,   0}},
    {     2, {   0,   0}},
    {  -390, { 780,   0}},
    {   -97, {   0,   0}},
    {   -56, {   0,   0}},
    {  -130, {   0,   0}},
    { 10795, {   0,   0}},
    {  -163, {   0,   0}},
    { 10792, {   0,   0}},
    {  -195, {   0,   0}},
    {    69, {   0,   0}},
    {    71, {   0,   0}},
    {   116, {   0,   0}},
    {    38, {   0,   0}},
    {    37, {   0,   0}},
    {    64, {   0,   0}},
    {    63, {   0,   0}},
    {    41, { 776, 769}},
    {    21, { 776, 769}},
    {     8, {   0,   0}},
    {   -30, {   0,   0}},
    {   -25, {   0,   0}},
    {   -15, {   0,   0}},
    {   -22, {   0,   0}},
    {   -54, {   0,   0}},
    {   -48, {   0,   0}},
    {   -60, {   0,   0}},
    {   -64, {   0,   0}},
    {    -7, {   0,   0}},
    {    80, {   0,   0}},
    {    15, {   0,   0}},
    {    48, {   0,   0}},
    {   -34, {1410,   0}},
    {  7264, {   0,   0}},
    {    -8, {   0,   0}},
    { -7726, { 817,   0}},
    { -7715, { 776,   0}},
    { -7713, { 778,   0}},
    { -7712, { 778,   0}},
    { -7737, { 702,   0}},
    {   -58, {   0,   0}},
    { -7723, { 115,   0}},
    { -7051, { 787,   0}},
    { -7053, { 787, 768}},
    { -7055, { 787, 769}},
    { -7057, { 787, 834}},
    {  -128, { 953,   0}},
    {  -136, { 953,   0}},
    {  -112, { 953,   0}},
    {  -120, { 953,   0}},
    {   -64, { 953,   0}},
    {   -72, { 953,   0}},
    {   -66, { 953,   0}},
    { -7170, { 953,   0}},
    { -7176, { 953,   0}},
    { -7173, { 834,   0}},
    { -7174, { 834, 953}},
    {   -74, {   0,   0}},
    { -7179, { 953,   0}},
    { -7173, {   0,   0}},
    {   -78, { 953,   0}},
    { -7180, { 953,   0}},
    { -7190, { 953,   0}},
    { -7183, { 834,   0}},
    { -7184, { 834, 953}},
    {   -86, {   0,   0}},
    { -7189, { 953,   0}},
    { -7193, { 776, 768}},
    { -7194, { 776, 769}},
    { -7197, { 834,   0}},
    { -7198, { 776, 834}},
    {  -100, {   0,   0}},
    { -7197, { 776, 768}},
    { -7198, { 776, 769}},
    { -7203, { 787,   0}},
    { -7201, { 834,   0}},
    { -7202, { 776, 834}},
    {  -112, {   0,   0}},
    {  -118, { 953,   0}},
    { -7210, { 953,   0}},
    { -7206, { 953,   0}},
    { -7213, { 834,   0}},
    { -7214, { 834, 953}},
    {  -128, {   0,   0}},
    {  -126, {   0,   0}},
    { -7219, { 953,   0}},
    { -7517, {   0,   0}},
    { -8383, {   0,   0}},
    { -8262, {   0,   0}},
    {    28, {   0,   0}},
    {    16, {   0,   0}},
    {    26, {   0,   0}},
    {-10743, {   0,   0}},
    { -3814, {   0,   0}},
    {-10727, {   0,   0}},
    {-10780, {   0,   0}},
    {-10749, {   0,   0}},
    {-10783, {   0,   0}},
    {-10782, {   0,   0}},
    {-10815, {   0,   0}},
    {-35332, {   0,   0}},
    {-42280, {   0,   0}},
    {-42308, {   0,   0}},
    {-42319, {   0,   0}},
    {-42315, {   0,   0}},
    {-42305, {   0,   0}},
    {-42258, {   0,   0}},
    {-42282, {   0,   0}},
    {-42261, {   0,   0}},
    {   928, {   0,   0}},
    {-38864, {   0,   0}},
    {-64154, { 102,   0}},
    {-64155, { 105,   0}},
    {-64156, { 108,   0}},
    {-64157, { 102, 105}},
    {-64158, { 102, 108}},
    {-64146, { 116,   0}},
    {-64147, { 116,   0}},
    {-62879, {1398,   0}},
    {-62880, {1381,   0}},
    {-62881, {1387,   0}},
    {-62872, {1398,   0}},
    {-62883, {1389,   0}},
    {    40, {   0,   0}},
};

/* Full_Case_Folding: 1168 bytes. */

int re_get_full_case_folding(RE_UINT32 ch, RE_UINT32* codepoints) {
    RE_UINT32 code;
    RE_UINT32 f;
    RE_UINT32 pos;
    RE_UINT32 value;
    RE_FullCaseFolding* case_folding;
    int count;

    f = ch >> 13;
    code = ch ^ (f << 13);
    pos = (RE_UINT32)re_full_case_folding_stage_1[f] << 5;
    f = code >> 8;
    code ^= f << 8;
    pos = (RE_UINT32)re_full_case_folding_stage_2[pos + f] << 5;
    f = code >> 3;
    code ^= f << 3;
    pos = (RE_UINT32)re_full_case_folding_stage_3[pos + f] << 3;
    value = re_full_case_folding_stage_4[pos + code];

    case_folding = &re_full_case_folding_table[value];

    codepoints[0] = (RE_UINT32)((RE_INT32)ch + case_folding->diff);
    count = 1;

    while (count < RE_MAX_FOLDED && case_folding->codepoints[count - 1] != 0) {
        codepoints[count] = case_folding->codepoints[count - 1];
        ++count;
    }

    return count;
}

/* Property function table. */

RE_GetPropertyFunc re_get_property[] = {
    re_get_general_category,
    re_get_block,
    re_get_script,
    re_get_word_break,
    re_get_grapheme_cluster_break,
    re_get_sentence_break,
    re_get_math,
    re_get_alphabetic,
    re_get_lowercase,
    re_get_uppercase,
    re_get_cased,
    re_get_case_ignorable,
    re_get_changes_when_lowercased,
    re_get_changes_when_uppercased,
    re_get_changes_when_titlecased,
    re_get_changes_when_casefolded,
    re_get_changes_when_casemapped,
    re_get_id_start,
    re_get_id_continue,
    re_get_xid_start,
    re_get_xid_continue,
    re_get_default_ignorable_code_point,
    re_get_grapheme_extend,
    re_get_grapheme_base,
    re_get_grapheme_link,
    re_get_white_space,
    re_get_bidi_control,
    re_get_join_control,
    re_get_dash,
    re_get_hyphen,
    re_get_quotation_mark,
    re_get_terminal_punctuation,
    re_get_other_math,
    re_get_hex_digit,
    re_get_ascii_hex_digit,
    re_get_other_alphabetic,
    re_get_ideographic,
    re_get_diacritic,
    re_get_extender,
    re_get_other_lowercase,
    re_get_other_uppercase,
    re_get_noncharacter_code_point,
    re_get_other_grapheme_extend,
    re_get_ids_binary_operator,
    re_get_ids_trinary_operator,
    re_get_radical,
    re_get_unified_ideograph,
    re_get_other_default_ignorable_code_point,
    re_get_deprecated,
    re_get_soft_dotted,
    re_get_logical_order_exception,
    re_get_other_id_start,
    re_get_other_id_continue,
    re_get_sterm,
    re_get_variation_selector,
    re_get_pattern_white_space,
    re_get_pattern_syntax,
    re_get_hangul_syllable_type,
    re_get_bidi_class,
    re_get_canonical_combining_class,
    re_get_decomposition_type,
    re_get_east_asian_width,
    re_get_joining_group,
    re_get_joining_type,
    re_get_line_break,
    re_get_numeric_type,
    re_get_numeric_value,
    re_get_bidi_mirrored,
    re_get_indic_positional_category,
    re_get_indic_syllabic_category,
    re_get_alphanumeric,
    re_get_any,
    re_get_blank,
    re_get_graph,
    re_get_print,
    re_get_word,
    re_get_xdigit,
    re_get_posix_digit,
    re_get_posix_alnum,
    re_get_posix_punct,
    re_get_posix_xdigit,
};
