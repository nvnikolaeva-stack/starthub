import re

import pytest


def test_all_keys_present():
    from translations import TRANSLATIONS

    ru_keys = set(TRANSLATIONS["ru"].keys())
    en_keys = set(TRANSLATIONS["en"].keys())

    missing_in_en = ru_keys - en_keys
    missing_in_ru = en_keys - ru_keys

    assert not missing_in_en, f"Ключи есть в RU, но нет в EN: {missing_in_en}"
    assert not missing_in_ru, f"Ключи есть в EN, но нет в RU: {missing_in_ru}"


def test_no_empty_values():
    from translations import TRANSLATIONS

    for lang in ("ru", "en"):
        for key, value in TRANSLATIONS[lang].items():
            assert str(value).strip() != "", f"Пустое значение: [{lang}][{key}]"


def test_translations_differ():
    from translations import TRANSLATIONS

    same_count = 0
    total = len(TRANSLATIONS["ru"])
    for key in TRANSLATIONS["ru"]:
        if key in TRANSLATIONS["en"]:
            if TRANSLATIONS["ru"][key] == TRANSLATIONS["en"][key]:
                same_count += 1

    assert same_count < total * 0.3, (
        f"Слишком много совпадений ({same_count}/{total}). Забыли перевести?"
    )


def test_supported_languages():
    from translations import TRANSLATIONS

    assert "ru" in TRANSLATIONS
    assert "en" in TRANSLATIONS


def test_placeholders_match():
    from translations import TRANSLATIONS

    placeholder_re = re.compile(r"\{(\w+)\}")

    for key in TRANSLATIONS["ru"]:
        if key not in TRANSLATIONS["en"]:
            continue
        ru_raw = TRANSLATIONS["ru"][key]
        en_raw = TRANSLATIONS["en"][key]
        ru_placeholders = set(placeholder_re.findall(ru_raw))
        en_placeholders = set(placeholder_re.findall(en_raw))

        assert ru_placeholders == en_placeholders, (
            f"Плейсхолдеры не совпадают для [{key}]: "
            f"RU={ru_placeholders}, EN={en_placeholders}"
        )
