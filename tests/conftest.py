from bs4 import BeautifulSoup
import os
import tomllib
from typing import Any, Tuple

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
RECORD_TESTDATA_DIR = os.path.join(CURR_DIR, "testdata_records")


def load_toml(filename: str) -> dict[str, Any]:
    with open(filename, "rb") as f:
        return tomllib.load(f)


def load_soup(filename: str) -> BeautifulSoup:
    with open(filename, "r") as f:
        return BeautifulSoup(f, "html.parser")


def load_record_test(record_id: str) -> Tuple[BeautifulSoup, dict[str, Any]]:
    path_stub = os.path.join(RECORD_TESTDATA_DIR, record_id)
    return load_soup(f"{path_stub}.html"), load_toml(f"{path_stub}.toml")
