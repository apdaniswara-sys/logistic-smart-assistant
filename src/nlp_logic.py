# src/nlp_logic.py
import pandas as pd
import re
from typing import Optional, Callable

# ------------- Configuration -------------
MASTER_FILE = "data/master_parts.csv"   # path ke master CSV
CSV_SEP = ";"                           # separator file CSV Anda
# Jika Anda punya fungsi API untuk stock realtime, set ini dengan function(part_key)->str
get_realtime_stock_fn: Optional[Callable[[str], str]] = None

# ------------- Internal state -------------
last_part = None   # simpan konteks (row dict) dari part terakhir yang diproses

# ------------- Utilities: load + normalize -------------
def load_master_data(path: str = MASTER_FILE, sep: str = CSV_SEP):
    """
    Load master CSV, normalize header, build two DataFrames:
     - df_raw: as-is (but header stripped)
     - df_search: all string values uppercased & stripped for matching
    """
    try:
        df_raw = pd.read_csv(path, sep=sep, dtype=str, keep_default_na=False)
    except Exception as e:
        print(f"❌ Gagal memuat master file '{path}': {e}")
        return None, None

    # strip column names
    df_raw.columns = [c.strip() for c in df_raw.columns]

    # create searchable df (uppercased values)
    df_search = df_raw.copy()
    for col in df_search.columns:
        df_search[col] = df_search[col].astype(str).str.strip().str.upper()

    return df_raw, df_search


# Load at module import (can be reloaded if needed)
_df_raw, _df_search = load_master_data()


def reload_master_data(path: str = MASTER_FILE, sep: str = CSV_SEP):
    global _df_raw, _df_search
    _df_raw, _df_search = load_master_data(path, sep)


# ------------- NLU helpers -------------
def detect_intents(text: str):
    """
    Return list of intents detected. Orders: more specific -> general
    intents: stock, supplier, lot, part_name, list_by_supplier, search_all
    """
    t = text.lower()
    intents = []

    # stock intent
    if any(k in t for k in ["stok", "stock", "jumlah", "qty", "berapa stok", "cek stok", "cek stock", "cek unit"]):
        intents.append("stock")

    # supplier intent
    if any(k in t for k in ["supplier", "vendor", "pemasok", "supplier name", "siapa supplier", "siapa vendor"]):
        intents.append("supplier")

    # lot/order size
    if any(k in t for k in ["lot", "order", "order lot", "lot size", "order lot size", "order lot size", "order_lot_size"]):
        intents.append("lot")

    # part name intent
    if any(k in t for k in ["nama part", "part name", "apa part", "part apa", "what is the part", "nama komponen"]):
        intents.append("part_name")

    # list by supplier
    if any(k in t for k in ["dari", "oleh", "dikeluarkan oleh", "produksi oleh", "dari supplier", "dari vendor"]) and "part" in t:
        intents.append("list_by_supplier")

    # fallback search intent (general query)
    if not intents:
        intents.append("search")

    return intents


_part_code_pattern = re.compile(r'\b[A-Z0-9\-]{2,20}\b', flags=re.IGNORECASE)


def extract_candidates(text: str):
    """
    Extract candidate tokens that might be part codes (alphanumeric short tokens).
    Also return raw text uppercased for searching substrings (e.g. part name)
    """
    candidates = re.findall(_part_code_pattern, text)
    candidates = [c.strip().upper() for c in candidates if c.strip()]
    return candidates


# ------------- Search helpers -------------
def find_best_match(candidates, df_search):
    """
    Try to find the best matching row in df_search based on candidates.
    Matching strategy:
     1) exact match in columns that likely contain codes (Part No, Kanban No)
     2) exact match in Part Name
     3) substring match in Part Name or Supplier
    Return the first matching raw-row index (int) or None
    """
    if df_search is None:
        return None

    cols = df_search.columns.tolist()
    # identify likely code columns
    code_cols = [c for c in cols if any(k in c.lower() for k in ["part no", "partno", "part_no", "kanban", "kanban no", "kanban_no"])]
    name_cols = [c for c in cols if "part" in c.lower() and "name" in c.lower()]
    supplier_cols = [c for c in cols if "supplier" in c.lower() or "exporter" in c.lower() or "vendor" in c.lower()]

    # 1) exact code match
    for cand in candidates:
        for col in code_cols:
            matches = df_search[df_search[col] == cand]
            if not matches.empty:
                return matches.index[0]

    # 2) exact match in part name
    for cand in candidates:
        for col in name_cols:
            matches = df_search[df_search[col] == cand]
            if not matches.empty:
                return matches.index[0]

    # 3) substring match (part name / supplier)
    text_upper = " ".join(candidates) if candidates else ""
    if text_upper:
        for col in name_cols + supplier_cols:
            matches = df_search[df_search[col].str.contains(text_upper, na=False)]
            if not matches.empty:
                return matches.index[0]

    # 4) fallback: try any candidate as substring across part name
    for cand in candidates:
        for col in name_cols + supplier_cols + code_cols:
            matches = df_search[df_search[col].str.contains(cand, na=False)]
            if not matches.empty:
                return matches.index[0]

    return None


def find_by_supplier_name(supplier_query: str, df_search):
    """
    Return all indices where supplier contains the supplier_query (case-insensitive)
    """
    if df_search is None:
        return []
    supplier_cols = [c for c in df_search.columns if "supplier" in c.lower() or "exporter" in c.lower() or "vendor" in c.lower()]
    results = pd.Index([])
    for col in supplier_cols:
        matches = df_search[df_search[col].str.contains(supplier_query.upper(), na=False)]
        results = results.union(matches.index)
    return list(results)


# ------------- Response generator -------------
def build_response_from_row(row_raw, intent_list):
    """
    Given a raw row (Series from _df_raw) and list of intents, build natural response.
    """
    if row_raw is None:
        return "Data part tidak ditemukan."

    # map common column names; use safe get with various aliases
    def get_col(*candidates, default="Tidak tersedia"):
        for c in candidates:
            if c in row_raw.index:
                val = row_raw.get(c)
                if val is None or str(val).strip() == "":
                    continue
                return str(val)
        return default

    part_name = get_col("Part Name", "PartName", "part_name")
    part_no = get_col("Part No", "PartNo", "part_no", "PartNo ")
    kanban_no = get_col("Kanban No", "KanbanNo", "kanban_no", "Kanban No ")
    supplier = get_col("Supplier / Exporter Name", "Supplier / Exporter Name ", "Supplier", "supplier")
    lot = get_col("Order Lot Size", "Order Lot Size ", "OrderLotSize", "Order_Lot_Size", "order lot size")

    texts = []
    for intent in intent_list:
        if intent == "stock":
            # Use real-time API hook if available
            key_for_stock = part_no if part_no != "Tidak tersedia" else kanban_no
            if get_realtime_stock_fn:
                try:
                    stock_txt = get_realtime_stock_fn(key_for_stock)
                except Exception as e:
                    stock_txt = f"Gagal ambil stok realtime: {e}"
                texts.append(stock_txt)
            else:
                texts.append(f"Stok part {part_name} ({kanban_no or part_no}) sedang dicek (API belum terhubung).")
        elif intent == "supplier":
            texts.append(f"Supplier untuk part {part_name} ({kanban_no or part_no}) adalah {supplier}.")
        elif intent == "lot":
            texts.append(f"Lot size (Order Lot Size) untuk part {part_name} ({kanban_no or part_no}) adalah {lot}.")
        elif intent == "part_name":
            texts.append(f"Nama part dengan kode {kanban_no or part_no} adalah {part_name}.")
        else:
            # fallback: brief summary
            texts.append(f"Part {part_name} ({kanban_no or part_no}): supplier {supplier}, lot size {lot}.")

    return " ".join(texts)


# ------------- Public API: process_query -------------
def process_query(user_text: str) -> str:
    """
    Main entry point. Given user_text (string), return a natural language response.
    Keeps context in module variable `last_part`.
    """
    global last_part, _df_raw, _df_search

    if _df_raw is None or _df_search is None:
        return "Data master parts belum dimuat. Pastikan file CSV tersedia."

    if not user_text or not isinstance(user_text, str):
        return "Saya tidak mendengar dengan jelas."

    text = user_text.strip()
    intents = detect_intents(text)
    candidates = extract_candidates(text)  # tokens like 105D etc.

    # If user asks without explicit part code but context exists, use last_part
    if not candidates and last_part is not None:
        # use last_part index
        row_raw = last_part
        return build_response_from_row(row_raw, intents)

    # find best match index
    idx = find_best_match(candidates, _df_search)

    if idx is None:
        # maybe user asked to list by supplier: try to detect supplier name token in full text
        # naive supplier detection: take words longer than 3 chars and try match
        words = [w.upper() for w in re.findall(r'\w+', text) if len(w) > 3]
        for w in words:
            supplier_matches = find_by_supplier_name(w, _df_search)
            if supplier_matches:
                # build a list response
                rows = [_df_raw.loc[i] for i in supplier_matches[:10]]  # top 10
                names = [r.get(next((c for c in r.index if "Part Name" in c), r.index[0])) for r in rows]
                supplier_sample = _df_raw.loc[supplier_matches[0]].get(next((c for c in _df_raw.columns if "Supplier" in c or "Exporter" in c), supplier_matches[0]))
                return f"Ditemukan {len(supplier_matches)} part untuk supplier {supplier_sample}. Contoh: " + ", ".join(str(n) for n in names)

        return "Saya tidak menemukan kode part yang kamu maksud."

    # found a match
    row_raw = _df_raw.loc[idx]
    # update context
    last_part = row_raw

    # build answer
    response = build_response_from_row(row_raw, intents)
    return response


# ------------- Helper to set realtime stock function from outside -------------
def set_realtime_stock_function(fn: Callable[[str], str]):
    """
    Set a function that will be called for stock lookups.
    Example signature:
        def my_stock_api(part_key: str) -> str: return "Stok ..."

    Then in your app: from src import nlp_logic; nlp_logic.set_realtime_stock_function(my_stock_api)
    """
    global get_realtime_stock_fn
    get_realtime_stock_fn = fn
