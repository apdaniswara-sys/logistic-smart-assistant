# src/nlp_logic.py

from typing import Optional, Dict, Any
import re
import time
import pandas as pd
import requests

# DCL JSON loader
from src.dcl_monitoring_json import (
    load_dcl_json,
    summarize_dcl,
    count_by_dock,
    count_arrived,
    count_advanced,
    count_late,
    count_delay,
    count_waiting,
    count_not_arrived,
    count_on_time,
    get_routes_by_status,
    find_route_row,
)

# ============================================================
# CONFIGURATION
# ============================================================
API_URL = "http://10.64.6.27/legion/all_data_dock43.php"  # STOCK only
CSV_FALLBACK = "data/master_parts.csv"
DATA_CACHE_TTL = 30

_data_cache = {"df": None, "ts": 0}

conversation_context: Dict[str, Optional[str]] = {
    "last_kanban": None,
    "last_status_query": None,   # misal: "advanced", "late"
}


# ============================================================
# HELPERS
# ============================================================
def _now_ts() -> float:
    return time.time()


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    return df


def safe_get(mapping: Dict[str, Any], *possible_keys: str) -> Optional[Any]:
    if not isinstance(mapping, dict):
        return None
    ml = {k.lower(): v for k, v in mapping.items()}
    for k in possible_keys:
        v = ml.get(k.lower())
        if v is not None and str(v).strip() != "":
            return v
    return None


# ============================================================
# FIXED — ROUTE DETECTOR (SAFE VERSION)
# ============================================================
def extract_route(text: str) -> Optional[str]:
    if not text:
        return None

    banned = {
        "apa", "siapa", "berapa", "bagaimana", "gimana",
        "mengapa", "kapan", "dimana", "kemana", "darimana"
    }

    tokens = re.split(r"[\s,.;]+", text.lower())

    for token in tokens:
        t = token.strip()
        if not t:
            continue

        if t in banned:
            continue

        if "-" not in t:
            continue

        parts = t.split("-")
        if len(parts) != 2:
            continue

        prefix, suffix = parts[0], parts[1]

        if not prefix.isalpha():
            continue

        if not suffix.isdigit():
            continue

        if len(t) < 4 or len(t) > 20:
            continue

        return t.upper()

    return None

# ============================================================
# KANBAN DETECTOR — 4 DIGIT & DIAWALI ANGKA
# ============================================================
def extract_kanban(text: str) -> Optional[str]:
    tokens = re.split(r"[\s,;:]+", text)
    for t in tokens:
        tok = t.strip().upper()
        if len(tok) == 4 and tok[0].isdigit():
            return tok
    return None

# ============================================================
# FIND PART
# ============================================================
def find_part(df: pd.DataFrame, code: str) -> Optional[Dict[str, Any]]:
    if df is None or df.empty:
        return None
    if "kanbanno" not in df.columns:
        return None
    try:
        mask = df["kanbanno"].astype(str).str.upper().str.contains(code)
        res = df[mask]
        if res.empty:
            return None
        return res.iloc[0].to_dict()
    except Exception:
        return None

# ============================================================
# LOAD STOCK DATA
# ============================================================
def load_data(force_refresh: bool = False) -> pd.DataFrame:
    global _data_cache

    if (
        not force_refresh
        and _data_cache["df"] is not None
        and (_now_ts() - _data_cache["ts"]) < DATA_CACHE_TTL
    ):
        return _data_cache["df"]

    try:
        resp = requests.get(API_URL, timeout=5)
        payload = resp.json()
        if isinstance(payload, dict) and "data" in payload:
            df = pd.DataFrame(payload["data"])
            df = normalize_columns(df)
            _data_cache["df"] = df
            _data_cache["ts"] = _now_ts()
            return df
    except Exception:
        pass

    try:
        df = pd.read_csv(CSV_FALLBACK, sep=";")
        df = normalize_columns(df)
        _data_cache["df"] = df
        _data_cache["ts"] = _now_ts()
        return df
    except Exception:
        return pd.DataFrame()

# ============================================================
# MAIN NLP PROCESSOR
# ============================================================
def process_query(user_input: str) -> str:
    if not user_input or not user_input.strip():
        return "Silakan masukkan pertanyaan."

    txt = user_input.lower().strip()

    # Load DCL
    dcl = load_dcl_json()
    dcl_rows = dcl.get("rows", []) if dcl else []

    # Detect route
    route = extract_route(txt)

    # ===================================================
    # 1) FOLLOW-UP: “rute apa saja?” (mengacu ke last_status_query)
    # ===================================================
    if route is None and ("route" in txt or txt in "rute"):
        last_status = conversation_context.get("last_status_query")
        if last_status:
            routes = get_routes_by_status(dcl_rows, last_status)
            if not routes:
                return f"Tidak ada route yang berstatus {last_status}."
            return "Berikut route yang " + last_status + ":\n- " + "\n- ".join(routes)
        else:
            return "Status apa yang ingin ditampilkan? (advanced, late, arrived, delay, waiting)"

    # ===================================================
    # 2) ROUTE DETAIL (contoh: “kapan kedatangan route RC16-02”)
    # ===================================================
    if route:
        row = find_route_row(dcl_rows, route)
        if row:
            return (
                f"Informasi Route {route}:\n"
                f"- Status: {row.get('raw_status')}\n"
                f"- Scheduled Arrival: {row.get('scheduled_arrival')}\n"
                f"- Actual Arrival: {row.get('actual_arrival')}"
            )
        return f"Saya tidak menemukan informasi route {route}."

    # ===================================================
    # 3) DCL INTENTS (lebih natural + handle 0 result)
    # ===================================================

    def natural_count_response(label: str, count_value: int) -> str:
        """
        Membuat respon natural.
        Jika 0 -> "Tidak ada <label> saat ini."
        Jika >0 -> "Ada <count> <label>."
        """
        if count_value == 0:
            return f"Tidak ada {label} saat ini."
        return f"Ada {count_value} {label}."

    # ----- Arrived -----
    if any(x in txt for x in ["arrived", "sudah tiba", "sudah datang", "sampai"]):
        conversation_context["last_status_query"] = "arrived"
        c = count_arrived(dcl_rows)
        return natural_count_response("delivery yang sudah tiba", c)

    # ----- Advanced -----
    if any(x in txt for x in ["advanced", "lebih cepat", "lebih awal", "advance"]):
        conversation_context["last_status_query"] = "advanced"
        c = count_advanced(dcl_rows)
        return natural_count_response("delivery yang lebih cepat (advanced)", c)

    # ----- Late -----
    if any(x in txt for x in ["late", "terlambat"]):
        conversation_context["last_status_query"] = "late"
        c = count_late(dcl_rows)
        return natural_count_response("delivery yang Late (sudah datang lewat jadwal)", c)

    # ----- Delay -----
    if "delay" in txt:
        conversation_context["last_status_query"] = "delay"
        c = count_delay(dcl_rows)
        return natural_count_response("delivery yang Delay (belum datang tapi lewat jadwal)", c)

    # ----- Waiting -----
    if "waiting" in txt:
        conversation_context["last_status_query"] = "waiting"
        c = count_waiting(dcl_rows)
        return natural_count_response("delivery yang Waiting (belum saatnya datang)", c)

    # ----- Belum datang / Not Arrived -----
    if any(x in txt for x in ["belum datang", "belum tiba", "not arrived"]):
        conversation_context["last_status_query"] = "not_arrived"
        c = count_not_arrived(dcl_rows)
        return natural_count_response("delivery yang belum tiba", c)

    # ----- On-time -----
    if "on time" in txt or "ontime" in txt:
        conversation_context["last_status_query"] = "ontime"
        c = count_on_time(dcl_rows)
        return natural_count_response("delivery yang On-Time", c)


    # Performance / summary
    if any(x in txt for x in ["performance", "summary", "ringkas", "ringkasan", "kondisi"]):
        s = summarize_dcl(dcl_rows)
        return (
            "Ringkasan Delivery Performance hari ini:\n"
            f"- Total Delivery: {s['total']}\n"
            f"- Advanced: {s['advanced']}\n"
            f"- Arrived: {s['arrived']}\n"
            f"- Late: {s['late']}\n"
            f"- Delay: {s['delay']}\n"
            f"- Waiting: {s['waiting']}\n"
            f"- Belum Tiba: {s['not_arrived']}\n"
            f"- On-Time: {s['on_time']}\n"
            f"- On-Time Ratio: {s['on_time_ratio']}%"
        )

    # Dock-based
    if "dock" in txt:
        m = re.search(r"dock\s*(\d+)", txt)
        if m:
            dock = m.group(1)
            return f"Dock {dock} memiliki {count_by_dock(dcl_rows, dock)} delivery hari ini."

    # =======================================================
    # 4) STOCK (KANBAN)
    # =======================================================

    df = load_data()
    last_kanban = conversation_context.get("last_kanban")
    code = extract_kanban(txt) or last_kanban

    if not code:
        if any(k in txt for k in ["kanban", "part", "stok", "stock", "supplier"]):
            return "Silakan sebutkan kode Kanban atau nomor part."
        return "Permintaan tidak dikenali. Anda bisa menanyakan delivery atau stock parts."

    part = find_part(df, code)
    if not part:
        conversation_context["last_kanban"] = code
        return f"Saya tidak menemukan Kanban {code}."

    conversation_context["last_kanban"] = code

    # extract values
    part_name = safe_get(part, "partname")
    part_no = safe_get(part, "partno")
    supplier = safe_get(part, "suppliername")
    supplier_code = safe_get(part, "suppliercode")
    plant_code = safe_get(part, "plantcode")
    dock_code = safe_get(part, "dockcode")
    address = safe_get(part, "kanbanaddress")
    stock_pcs = safe_get(part, "stockoverall")
    stock_sps = safe_get(part, "stocksps")
    stock_receiving = safe_get(part, "stockreceiving")
    stock_minutes = safe_get(part, "stockspsminutes")
    pcs_per_kanban = safe_get(part, "pcsperkanban")
    last_received = safe_get(part, "lastreceiveddate")
    stock_overflow = safe_get(part, "stockoverflow")

    # STOCK INTENTS
    if "stock" in txt or "stok" in txt or "total stok" in txt:
        if "menit" in txt:
            return f"Total Stok Kanban {code} = {stock_minutes} menit."
        if "jam" in txt:
            if stock_minutes:
                return f"Total Stok Kanban {code} = {round(float(stock_minutes)/60, 2)} jam."
        if "sps" in txt or "line" in txt:
            return f"Stock SPS (line side) Kanban {code} = {stock_sps} pcs."
        if "receiving" in txt:
            return f"Stock Receiving Kanban {code} = {stock_receiving} pcs."
        if "over flow" in txt or "overflow" in txt or "over" in txt:
            return f"Stock overflow kanban {code} = {stock_overflow}."
        return f"Stok Kanban {code} = {stock_pcs} pcs."

    if "supplier code" in txt or "supp. code" in txt or "supp code" in txt:
        return f"Supplier code Kanban {code} = {supplier_code}."
    if "supplier" in txt:
        return f"Supplier Kanban {code} = {supplier}."

    if "plant" in txt:
        return f"Plant {plant_code}, Dock {dock_code}."
    if "dock" in txt:
        return f"Dock Kanban {code} = {dock_code}."

    if "alamat" in txt or "address" in txt:
        return f"Alamat Kanban {code} = {address}."

    if "part no" in txt or "part number" in txt or "part no." in txt or "no. part" in txt or "no part" in txt:
        return f"Part number Kanban {code} = {part_no}."
    if "nama part" in txt or "part name" in txt:
        return f"Nama part Kanban {code} = {part_name}."

    if "pcs per kanban" in txt or "isi kanban" in txt or "pcs perkanban" in txt or "qty perkanban" in txt or "qty per kanban" in txt:
        return f"Isi per Kanban {code} = {pcs_per_kanban} pcs."

    if "last received" in txt or "terakhir" in txt:
        return f"Terakhir diterima: {last_received}"

    return f"Kanban {code} ditemukan. Silakan tanya stok, supplier, part no, atau informasi lainnya."
