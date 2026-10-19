#!/usr/bin/env python3

"""
RU-ZH parallel JSONL datasetni tozalash va filtrlash.

Kutiladigan input format:

{"ru": "Привет, мир!", "zh": "你好，世界！"}
{"ru": "Как дела?", "zh": "你好吗？"}

Ishlatish:

    python clean_ru_zh.py input.jsonl output.jsonl

Masalan:

    python clean_ru_zh.py \
        mohina/test_ru_zh/multiun_ru_zh.jsonl \
        mohina/test_ru_zh/multiun_ru_zh_clean.jsonl

Reject qilingan qatorlarni alohida saqlash:

    python clean_ru_zh.py \
        input.jsonl \
        output.jsonl \
        --rejects rejected.jsonl

Script quyidagilarni qiladi:

1. UTF-8 ni tekshiradi
2. JSON formatni tekshiradi
3. ru va zh maydonlarini oladi
4. Unicode matnni normalize qiladi
5. Ko'rinmas/buzuq belgilarni olib tashlaydi
6. Bo'shliqlarni normalize qiladi
7. Russian matnda Cyrillic ulushini tekshiradi
8. Chinese matnda Han belgilar ulushini tekshiradi
9. Begona yozuvlarni tekshiradi
10. Juda uzun/qisqa juftliklarni olib tashlaydi
11. RU/ZH uzunlik nisbatini tekshiradi
12. Dublikatlarni olib tashlaydi
13. Toza JSONL fayl yaratadi
14. Statistikani chiqaradi
"""

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter


# ---------------------------------------------------------
# Konsol encoding
# ---------------------------------------------------------

# Windows kabi muhitlarda stdout UTF-8 bo'lmasa,
# Unicode belgilarni print qilishda xato chiqmasligi uchun.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(
        encoding="utf-8",
        errors="replace",
    )


# ---------------------------------------------------------
# Asosiy konstantalar
# ---------------------------------------------------------

# UTF-8 BOM:
# ayrim fayllarning birinchi qatori shundan boshlanishi mumkin.
UTF8_BOM = b"\xef\xbb\xbf"

# Unicode replacement character:
#
#     �
#
# Bu odatda matn noto'g'ri decode qilinganini bildiradi.
REPLACEMENT_CHAR = "\ufffd"


# ---------------------------------------------------------
# Regexlar
# ---------------------------------------------------------

# Vertical tab, form feed, next line,
# Unicode line separator va paragraph separator.
#
# Ularni o'chirib yubormaymiz, probelga aylantiramiz.
# Aks holda ikkita so'z bir-biriga yopishib qolishi mumkin.
LINE_SEPARATOR_RE = re.compile(
    r"[\x0b\x0c\x85\u2028\u2029]"
)


# Ko'rinmas belgilar:
#
# \u200b       zero-width space
# \u200c       zero-width non-joiner
# \u200d       zero-width joiner
# \u200e...    direction belgilar
# \ufeff       BOM
# \u00ad       soft hyphen
INVISIBLE_RE = re.compile(
    r"[\u200b-\u200f\u202a-\u202e\u2060\ufeff\u00ad]"
)


# Control characterlar.
#
# \t, \n va \r bu regexga kiritilmagan.
CONTROL_RE = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]"
)


# Yolg'iz UTF-16 surrogate belgilar.
#
# Bularni UTF-8 ga to'g'ri yozib bo'lmaydi.
SURROGATE_RE = re.compile(
    r"[\ud800-\udfff]"
)


# Unicode noncharacterlar.
NONCHARACTER_RE = re.compile(
    r"[\ufdd0-\ufdef\ufffe\uffff]"
)


# Har qanday whitespace:
#
# oddiy space
# tab
# newline
# NBSP
# Unicode whitespace
#
# Hammasini bitta oddiy space ga aylantiramiz.
WHITESPACE_RE = re.compile(r"\s+")


# ---------------------------------------------------------
# Apostroflar
# ---------------------------------------------------------

# Turli ko'rinishdagi apostroflar.
#
# Bu RU-ZH dataset uchun juda muhim emas,
# lekin dataset ichida Latin text uchrasa foydali.
APOSTROPHES = "ʻʼ‘’`´′‵ʹ՚＇'"

APOSTROPHE_RE = re.compile(
    rf"(?<=[A-Za-z])[{re.escape(APOSTROPHES)}](?=[A-Za-z]|\b)"
)


# ---------------------------------------------------------
# Fullwidth belgilar
# ---------------------------------------------------------

# Masalan:
#
#   １２３ -> 123
#   ＡＢＣ -> ABC
#   ａｂｃ -> abc
#
# Unicode code pointdan ASCII code pointga o'tkazamiz.
FULLWIDTH_TABLE = {
    c: c - 0xFEE0
    for c in range(0xFF10, 0xFF1A)
}

FULLWIDTH_TABLE.update({
    c: c - 0xFEE0
    for c in range(0xFF21, 0xFF3B)
})

FULLWIDTH_TABLE.update({
    c: c - 0xFEE0
    for c in range(0xFF41, 0xFF5B)
})


# ---------------------------------------------------------
# Chinese / CJK
# ---------------------------------------------------------

# Han ideographlar.
HAN_RANGE = (
    r"\u3400-\u4dbf"
    r"\u4e00-\u9fff"
    r"\uf900-\ufaff"
    r"\U00020000-\U0002fa1f"
)


# Chinese belgilar orasidagi space:
#
#     你 好 世 界
#
# ->
#
#     你好世界
#
CJK_SPACE_RE = re.compile(
    rf"(?<=[{HAN_RANGE}])\s+(?=[{HAN_RANGE}])"
)


# ---------------------------------------------------------
# Tinish belgilar
# ---------------------------------------------------------

# Tinish belgisidan oldingi noto'g'ri probelni olib tashlaydi.
#
#   "Привет , мир !"
#
# ->
#
#   "Привет, мир!"
#
# % bu yerda ataylab yo'q:
#
#   "5 %"
#
# rus tilida normal yozuv bo'lishi mumkin.
SPACE_BEFORE_PUNCT_RE = re.compile(
    r"\s+([,.;:!?…)\]\}»])"
)


# ---------------------------------------------------------
# Script detector
# ---------------------------------------------------------

# Unicode letter.
#
# \W  -> word bo'lmagan
# \d  -> raqam
# _   -> underscore
#
# Natijada harflarni taxminan ajratamiz.
LETTER_RE = re.compile(
    r"[^\W\d_]",
    flags=re.UNICODE,
)


# Cyrillic:
CYRILLIC_RE = re.compile(
    r"[\u0400-\u052f]"
)


# Chinese Han:
HAN_RE = re.compile(
    rf"[{HAN_RANGE}]"
)


# Japanese Hiragana + Katakana.
#
# Chinese datasetga yapon matni aralashib qolganini
# aniqlash uchun ishlatiladi.
KANA_RE = re.compile(
    r"[\u3040-\u30ff]"
)


# =========================================================
# Matnni tozalash
# =========================================================

def clean_text(text: str) -> str:
    """
    Bitta matnni Unicode va formatting nuqtai nazaridan tozalaydi.

    Matnning tilini o'zgartirmaydi.
    Faqat texnik iflosliklarni olib tashlaydi.
    """

    # 1.
    # Yolg'iz surrogate belgilarni olib tashlaymiz.
    text = SURROGATE_RE.sub("", text)

    # 2.
    # Unicode NFC normalization.
    #
    # Masalan ayrim belgilar:
    #
    #   harf + combining mark
    #
    # ko'rinishida bo'lishi mumkin.
    # NFC imkon qadar ularni bitta standart belgiga birlashtiradi.
    text = unicodedata.normalize("NFC", text)

    # 3.
    # Qator/sahifa separatorlarini space ga aylantiramiz.
    text = LINE_SEPARATOR_RE.sub(" ", text)

    # 4.
    # Ko'rinmas belgilarni olib tashlaymiz.
    text = INVISIBLE_RE.sub("", text)

    # 5.
    # Control characterlarni olib tashlaymiz.
    text = CONTROL_RE.sub("", text)

    # 6.
    # Unicode noncharacterlarni olib tashlaymiz.
    text = NONCHARACTER_RE.sub("", text)

    # 7.
    # Fullwidth Latin va raqamlarni ASCII ga o'tkazamiz.
    text = text.translate(FULLWIDTH_TABLE)

    # 8.
    # Latin harflari orasidagi turli apostroflarni
    # oddiy ASCII apostrofga o'tkazamiz.
    #
    # masalan:
    #
    #   ma’lumot -> ma'lumot
    text = APOSTROPHE_RE.sub("'", text)

    # 9.
    # Barcha whitespace'larni bitta space ga aylantiramiz.
    #
    # MUHIM:
    #
    # oldingi scriptdagi:
    #
    #     WHITESPACE_RE.sub("", text)
    #
    # noto'g'ri edi, chunki barcha so'zlarni yopishtirib yuborardi.
    text = WHITESPACE_RE.sub(" ", text)

    # 10.
    # Chinese Han belgilar orasidagi ortiqcha space'ni olib tashlaymiz.
    #
    #   中 国 -> 中国
    text = CJK_SPACE_RE.sub("", text)

    # 11.
    # Tinish belgilaridan oldingi space'ni olib tashlaymiz.
    text = SPACE_BEFORE_PUNCT_RE.sub(r"\1", text)

    # 12.
    # Boshi va oxiridagi space'larni olib tashlaymiz.
    return text.strip()


# =========================================================
# Til statistikasi
# =========================================================

def language_stats(text: str) -> tuple[int, int, int, int]:
    """
    Matndagi yozuv turlarining sonini qaytaradi.

    Return:

        (
            total_letters,
            cyrillic_letters,
            han_letters,
            kana_letters,
        )
    """

    total_letters = len(LETTER_RE.findall(text))
    cyrillic = len(CYRILLIC_RE.findall(text))
    han = len(HAN_RE.findall(text))
    kana = len(KANA_RE.findall(text))

    return (
        total_letters,
        cyrillic,
        han,
        kana,
    )


# =========================================================
# Parallel pair validation
# =========================================================

def validate_pair(
    ru: str,
    zh: str,
    args: argparse.Namespace,
) -> str | None:
    """
    RU-ZH juftlik sifatini tekshiradi.

    Hammasi yaxshi bo'lsa:
        None

    Muammo bo'lsa:
        sabab string qaytaradi.
    """

    # -----------------------------------------------------
    # 1. Bo'sh matn
    # -----------------------------------------------------

    if not ru:
        return "ru bo'sh"

    if not zh:
        return "zh bo'sh"

    # -----------------------------------------------------
    # 2. Minimal uzunlik
    # -----------------------------------------------------

    if len(ru) < args.min_len:
        return "ru juda qisqa"

    if len(zh) < args.min_len:
        return "zh juda qisqa"

    # -----------------------------------------------------
    # 3. Maksimal uzunlik
    # -----------------------------------------------------

    if len(ru) > args.max_len:
        return "ru juda uzun"

    if len(zh) > args.max_len:
        return "zh juda uzun"

    # -----------------------------------------------------
    # 4. Yozuv statistikasi
    # -----------------------------------------------------

    (
        ru_letters,
        ru_cyrillic,
        ru_han,
        ru_kana,
    ) = language_stats(ru)

    (
        zh_letters,
        zh_cyrillic,
        zh_han,
        zh_kana,
    ) = language_stats(zh)

    # Umuman harf yo'q bo'lsa:
    if ru_letters == 0:
        return "ru da harf yo'q"

    if zh_letters == 0:
        return "zh da harf yo'q"

    # -----------------------------------------------------
    # 5. Russian matnda Cyrillic ulushi
    # -----------------------------------------------------

    ru_cyrillic_ratio = ru_cyrillic / ru_letters

    if ru_cyrillic_ratio < args.min_cyrillic:
        return (
            "ru da kirill ulushi kam "
            f"({ru_cyrillic_ratio:.3f})"
        )

    # -----------------------------------------------------
    # 6. Chinese matnda Han ulushi
    # -----------------------------------------------------

    zh_han_ratio = zh_han / zh_letters

    if zh_han_ratio < args.min_han:
        return (
            "zh da Han belgilar ulushi kam "
            f"({zh_han_ratio:.3f})"
        )

    # -----------------------------------------------------
    # 7. Russian ichidagi begona yozuv
    # -----------------------------------------------------

    # Russian matnda Chinese yoki Japanese belgilar juda ko'p
    # bo'lmasligi kerak.
    ru_foreign = ru_han + ru_kana
    ru_foreign_ratio = ru_foreign / ru_letters

    if ru_foreign_ratio > args.max_foreign:
        return (
            "ru da begona yozuv ko'p "
            f"({ru_foreign_ratio:.3f})"
        )

    # -----------------------------------------------------
    # 8. Chinese ichidagi begona yozuv
    # -----------------------------------------------------

    # Chinese matnda Cyrillic yoki Japanese Kana
    # juda ko'p bo'lmasligi kerak.
    zh_foreign = zh_cyrillic + zh_kana
    zh_foreign_ratio = zh_foreign / zh_letters

    if zh_foreign_ratio > args.max_foreign:
        return (
            "zh da begona yozuv ko'p "
            f"({zh_foreign_ratio:.3f})"
        )

    # -----------------------------------------------------
    # 9. RU/ZH uzunlik nisbati
    # -----------------------------------------------------

    # Juda qisqa gaplarda ratio noto'g'ri signal berishi mumkin.
    #
    # Masalan:
    #
    #   Да
    #   是
    #
    # shuning uchun ratio faqat yetarlicha uzun pairlarda tekshiriladi.
    if max(len(ru), len(zh)) >= args.ratio_min_len:

        ratio = len(ru) / len(zh)

        if ratio < args.min_ratio:
            return (
                "ru/zh uzunlik nisbati juda kichik "
                f"({ratio:.3f})"
            )

        if ratio > args.max_ratio:
            return (
                "ru/zh uzunlik nisbati juda katta "
                f"({ratio:.3f})"
            )

    return None


# =========================================================
# Main
# =========================================================

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Russian-Chinese parallel JSONL datasetni "
            "tozalash va filtrlash"
        )
    )

    # -----------------------------------------------------
    # Input / Output
    # -----------------------------------------------------

    parser.add_argument(
        "input",
        help="Kirish JSONL fayli",
    )

    parser.add_argument(
        "output",
        help="Tozalangan JSONL fayli",
    )

    # -----------------------------------------------------
    # JSON field nomlari
    # -----------------------------------------------------

    parser.add_argument(
        "--ru-key",
        default="ru",
        help="Russian text field nomi (default: ru)",
    )

    parser.add_argument(
        "--zh-key",
        default="zh",
        help="Chinese text field nomi (default: zh)",
    )

    # -----------------------------------------------------
    # Duplicate
    # -----------------------------------------------------

    parser.add_argument(
        "--keep-duplicates",
        action="store_true",
        help="Dublikat juftliklarni saqlab qolish",
    )

    # -----------------------------------------------------
    # Replacement character
    # -----------------------------------------------------

    parser.add_argument(
        "--keep-replacement",
        action="store_true",
        help="U+FFFD (�) mavjud qatorlarni saqlab qolish",
    )

    # -----------------------------------------------------
    # Reject log
    # -----------------------------------------------------

    parser.add_argument(
        "--rejects",
        default=None,
        help=(
            "O'chirilgan qatorlarni sabab bilan "
            "JSONL faylga yozish"
        ),
    )

    # -----------------------------------------------------
    # Length filtering
    # -----------------------------------------------------

    parser.add_argument(
        "--min-len",
        type=int,
        default=1,
        help="Har bir tomon minimal uzunligi (default: 1)",
    )

    parser.add_argument(
        "--max-len",
        type=int,
        default=1000,
        help="Har bir tomon maksimal uzunligi (default: 1000)",
    )

    # -----------------------------------------------------
    # Language filtering
    # -----------------------------------------------------

    parser.add_argument(
        "--min-cyrillic",
        type=float,
        default=0.5,
        help=(
            "Russian matndagi Cyrillic harflarning "
            "minimal ulushi (default: 0.5)"
        ),
    )

    parser.add_argument(
        "--min-han",
        type=float,
        default=0.3,
        help=(
            "Chinese matndagi Han harflarning "
            "minimal ulushi (default: 0.3)"
        ),
    )

    parser.add_argument(
        "--max-foreign",
        type=float,
        default=0.1,
        help=(
            "Begona yozuvning maksimal ulushi "
            "(default: 0.1)"
        ),
    )

    # -----------------------------------------------------
    # Length ratio filtering
    # -----------------------------------------------------

    parser.add_argument(
        "--min-ratio",
        type=float,
        default=0.8,
        help=(
            "len(ru) / len(zh) minimal nisbat "
            "(default: 0.8)"
        ),
    )

    parser.add_argument(
        "--max-ratio",
        type=float,
        default=10.0,
        help=(
            "len(ru) / len(zh) maksimal nisbat "
            "(default: 10.0)"
        ),
    )

    parser.add_argument(
        "--ratio-min-len",
        type=int,
        default=15,
        help=(
            "Ratio tekshiruvi boshlanadigan minimal "
            "pair uzunligi (default: 15)"
        ),
    )

    args = parser.parse_args()

    # -----------------------------------------------------
    # Statistikalar
    # -----------------------------------------------------

    stats = Counter()

    # Duplicate aniqlash uchun hashlar.
    seen = set()

    # Reject file.
    reject_file = None

    if args.rejects:
        reject_file = open(
            args.rejects,
            "w",
            encoding="utf-8",
            newline="\n",
        )

    # -----------------------------------------------------
    # Reject helper
    # -----------------------------------------------------

    def reject(reason, line_no, payload):
        """
        Reject statistikasini oshiradi va kerak bo'lsa
        rejects JSONL fayliga yozadi.
        """

        stats[f"{reason} (o'chirildi)"] += 1

        if reject_file:
            reject_file.write(
                json.dumps(
                    {
                        "qator": line_no,
                        "sabab": reason,
                        "data": payload,
                    },
                    ensure_ascii=True,
                )
                + "\n"
            )

    # -----------------------------------------------------
    # Faylni o'qish
    # -----------------------------------------------------

    try:
        # Inputni binary mode'da o'qiymiz.
        #
        # Sababi:
        #
        # har bir qatorni alohida strict UTF-8 bilan decode
        # qila olamiz. Bitta buzuq qator butun jarayonni
        # to'xtatmaydi.
        with (
            open(args.input, "rb") as fin,
            open(
                args.output,
                "w",
                encoding="utf-8",
                newline="\n",
            ) as fout,
        ):

            for line_no, raw in enumerate(fin, 1):

                # -----------------------------------------
                # BOM
                # -----------------------------------------

                if line_no == 1 and raw.startswith(UTF8_BOM):
                    raw = raw[len(UTF8_BOM):]

                # -----------------------------------------
                # UTF-8 decode
                # -----------------------------------------

                try:
                    line = raw.decode("utf-8")

                except UnicodeDecodeError:

                    print(
                        f"[!] {line_no}-qator yaroqsiz UTF-8, "
                        "o'tkazib yuborildi"
                    )

                    reject(
                        "yaroqsiz UTF-8",
                        line_no,
                        raw.decode(
                            "utf-8",
                            errors="replace",
                        ),
                    )

                    continue

                # -----------------------------------------
                # Empty line
                # -----------------------------------------

                line = line.strip()

                if not line:
                    stats["bo'sh qator"] += 1
                    continue

                # -----------------------------------------
                # JSON parse
                # -----------------------------------------

                try:
                    obj = json.loads(line)

                except json.JSONDecodeError:

                    print(
                        f"[!] {line_no}-qator JSON emas, "
                        "o'tkazib yuborildi"
                    )

                    reject(
                        "buzuq JSON",
                        line_no,
                        line,
                    )

                    continue

                # JSON object bo'lishi kerak.
                if not isinstance(obj, dict):
                    reject(
                        "JSON obyekt emas",
                        line_no,
                        obj,
                    )
                    continue

                stats["jami"] += 1

                # Birinchi valid row fieldlarini ko'rsatamiz.
                if stats["jami"] == 1:
                    print(
                        "Topilgan maydonlar:",
                        list(obj.keys()),
                    )

                # -----------------------------------------
                # RU / ZH olish
                # -----------------------------------------

                ru = obj.get(args.ru_key)
                zh = obj.get(args.zh_key)

                if (
                    not isinstance(ru, str)
                    or not isinstance(zh, str)
                ):
                    reject(
                        (
                            f"'{args.ru_key}' yoki "
                            f"'{args.zh_key}' maydoni "
                            "yo'q yoki string emas"
                        ),
                        line_no,
                        obj,
                    )
                    continue

                # -----------------------------------------
                # Text cleaning
                # -----------------------------------------

                ru = clean_text(ru)
                zh = clean_text(zh)

                # -----------------------------------------
                # Replacement char
                # -----------------------------------------

                if (
                    not args.keep_replacement
                    and (
                        REPLACEMENT_CHAR in ru
                        or REPLACEMENT_CHAR in zh
                    )
                ):
                    reject(
                        "buzilgan belgi �",
                        line_no,
                        {
                            args.ru_key: ru,
                            args.zh_key: zh,
                        },
                    )

                    continue

                # -----------------------------------------
                # Pair validation
                # -----------------------------------------

                reason = validate_pair(
                    ru,
                    zh,
                    args,
                )

                if reason:
                    reject(
                        reason,
                        line_no,
                        {
                            args.ru_key: ru,
                            args.zh_key: zh,
                        },
                    )
                    continue

                # -----------------------------------------
                # Duplicate
                # -----------------------------------------

                if not args.keep_duplicates:

                    # To'liq matnni RAM'da saqlamaslik uchun
                    # 16-byte BLAKE2 hash saqlaymiz.
                    duplicate_source = (
                        ru.casefold()
                        + "\t"
                        + zh.casefold()
                    )

                    key = hashlib.blake2b(
                        duplicate_source.encode("utf-8"),
                        digest_size=16,
                    ).digest()

                    if key in seen:
                        reject(
                            "dublikat",
                            line_no,
                            {
                                args.ru_key: ru,
                                args.zh_key: zh,
                            },
                        )
                        continue

                    seen.add(key)

                # -----------------------------------------
                # Tozalangan qiymatlarni qaytarish
                # -----------------------------------------

                # Faqat ru va zh fieldlar o'zgaradi.
                #
                # Datasetdagi boshqa metadata fieldlariga
                # tegilmaydi.
                obj[args.ru_key] = ru
                obj[args.zh_key] = zh

                # -----------------------------------------
                # JSON serialization
                # -----------------------------------------

                try:
                    out_line = json.dumps(
                        obj,
                        ensure_ascii=False,
                    )

                    # UTF-8 ga encode bo'lishini tekshiramiz.
                    out_line.encode("utf-8")

                except UnicodeEncodeError:

                    reject(
                        "UTF-8 ga yozib bo'lmadi",
                        line_no,
                        obj,
                    )

                    continue

                # -----------------------------------------
                # Output
                # -----------------------------------------

                fout.write(out_line + "\n")

                stats["saqlandi"] += 1

    finally:
        if reject_file:
            reject_file.close()

    # -----------------------------------------------------
    # Natija
    # -----------------------------------------------------

    print()
    print("--- Natija ---")

    for key, value in stats.items():
        print(f"{key}: {value}")

    # Qo'shimcha umumiy statistika.
    total = stats["jami"]
    saved = stats["saqlandi"]

    if total:
        removed = total - saved

        print()
        print(f"Jami valid JSON obyektlar : {total}")
        print(f"Saqlandi                  : {saved}")
        print(f"O'chirildi                : {removed}")
        print(
            "Saqlanish foizi           : "
            f"{saved / total * 100:.2f}%"
        )


# =========================================================
# Entry point
# =========================================================

if __name__ == "__main__":
    main()