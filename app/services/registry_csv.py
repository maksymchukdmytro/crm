"""Реєстр виплат перевізника (CSV): ТТН і сума — для звірки накладених платежів."""
import csv
import io

TTN_HEADERS = ("ттн", "ен", "ен ", "номер", "number", "ttn", "декларац", "відправлення", "barcode", "штрихкод")
SUM_HEADERS = ("сума", "sum", "amount", "переказ", "післяплат", "наложен", "накладен", "до виплати")


class _Semicolon(csv.excel):
    delimiter = ";"


def _detect_columns(header: list[str]) -> tuple[int | None, int | None]:
    low = [h.strip().lower() for h in header]
    ttn_col = next((i for i, h in enumerate(low) if any(k in h for k in TTN_HEADERS)), None)
    sum_col = next((i for i, h in enumerate(low) if any(k in h for k in SUM_HEADERS) and i != ttn_col), None)
    return ttn_col, sum_col


def parse_registry(content: bytes) -> tuple[list[dict], str]:
    for enc in ("utf-8-sig", "cp1251"):
        try:
            text = content.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        return [], "Не вдалося прочитати файл (очікується CSV у UTF-8 або Windows-1251)"
    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,\t")
    except csv.Error:
        dialect = _Semicolon
    rows = list(csv.reader(io.StringIO(text), dialect))
    if not rows:
        return [], "Файл порожній"
    ttn_col, sum_col = _detect_columns(rows[0])
    start = 1
    if ttn_col is None:
        # без заголовка: перша колонка — ТТН, друга — сума
        ttn_col, sum_col, start = 0, 1, 0
    result = []
    for r in rows[start:]:
        if len(r) <= ttn_col:
            continue
        result.append({"ttn": r[ttn_col], "amount": r[sum_col] if sum_col is not None and len(r) > sum_col else ""})
    return result, ""
