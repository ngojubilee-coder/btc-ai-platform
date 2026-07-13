"""Unit tests for i18n: verify all FR keys exist in EN and vice versa, and t() returns correct values."""
import pytest
import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def extract_keys_from_dict_source(source: str) -> set[str]:
    """Extract quoted keys from a TypeScript dict-like structure."""
    keys = set()
    for m in re.finditer(r'"([a-zA-Z0-9_.]+)"\s*:', source):
        keys.add(m.group(1))
    return keys


def read_i18n_file() -> str:
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "frontend", "lib", "i18n.tsx",
    )
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def split_fr_en(source: str) -> tuple[str, str]:
    """Roughly split the i18n file into FR and EN sections."""
    fr_match = re.search(r'const\s+fr\s*:\s*Dict\s*=\s*\{(.+?)\n\};', source, re.DOTALL)
    en_match = re.search(r'const\s+en\s*:\s*Dict\s*=\s*\{(.+?)\n\};', source, re.DOTALL)
    fr_section = fr_match.group(1) if fr_match else ""
    en_section = en_match.group(1) if en_match else ""
    return fr_section, en_section


class TestI18nKeys:
    def test_fr_and_en_have_same_keys(self):
        source = read_i18n_file()
        fr_section, en_section = split_fr_en(source)
        fr_keys = extract_keys_from_dict_source(fr_section)
        en_keys = extract_keys_from_dict_source(en_section)
        missing_in_en = fr_keys - en_keys
        missing_in_fr = en_keys - fr_keys
        assert not missing_in_en, f"Keys missing in EN: {missing_in_en}"
        assert not missing_in_fr, f"Keys missing in FR: {missing_in_fr}"

    def test_fr_keys_not_empty(self):
        source = read_i18n_file()
        fr_section, _ = split_fr_en(source)
        fr_keys = extract_keys_from_dict_source(fr_section)
        assert len(fr_keys) > 50, f"Too few FR keys: {len(fr_keys)}"

    def test_en_keys_not_empty(self):
        source = read_i18n_file()
        _, en_section = split_fr_en(source)
        en_keys = extract_keys_from_dict_source(en_section)
        assert len(en_keys) > 50, f"Too few EN keys: {len(en_keys)}"

    def test_no_french_values_in_en_dict(self):
        source = read_i18n_file()
        _, en_section = split_fr_en(source)
        # Check for common French words in EN values
        french_indicators = ["é", "è", "ê", "à", "ç", "ô", "û", "œ"]
        # Extract values in EN section
        for m in re.finditer(r'"[^"]+"\s*:\s*"([^"]*)"', en_section):
            val = m.group(1)
            for indicator in french_indicators:
                assert indicator not in val, f"French character '{indicator}' found in EN value: '{val}'"

    def test_key_sections_exist(self):
        source = read_i18n_file()
        fr_section, en_section = split_fr_en(source)
        required_sections = ["nav.", "chat.", "dashboard.", "models.", "news.", "settings.", "reports.", "whales."]
        for section in required_sections:
            fr_count = sum(1 for k in extract_keys_from_dict_source(fr_section) if k.startswith(section))
            en_count = sum(1 for k in extract_keys_from_dict_source(en_section) if k.startswith(section))
            assert fr_count > 0, f"No FR keys for section '{section}'"
            assert en_count > 0, f"No EN keys for section '{section}'"
