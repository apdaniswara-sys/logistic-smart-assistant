import pandas as pd
import re
from rapidfuzz import fuzz, process

# ==============================
# Konfigurasi
# ==============================
API_URL = "http://10.64.6.27/legion/limit_5_dock43.php"
CSV_FALLBACK = "data/master_parts.csv"

# ==============================
# Konteks percakapan
# ==============================
conversation_context = {
    "last_kanban": None
}

# ==============================
# Fungsi bantu
# ==============================
def normalize_columns(df):
    """Buat semua nama kolom huruf kecil agar konsisten"""
    df.columns = [c.strip().lower() for c in df.columns]
    return df

def load_data():
    """Ambil data dari API atau CSV fallback"""
    import requests
    try:
        resp = requests.get(API_URL, timeout=5)
        resp.raise_for_status()
        df = pd.DataFrame(resp.json()["data"])
        return normalize_columns(df)
    except Exception:
        try:
            df = pd.read_csv(CSV_FALLBACK, sep=";")
            return normalize_columns(df)
        except Exception:
            return pd.DataFrame()

def extract_kanban(text: str):
    """Ambil kemungkinan kode Kanban dari teks"""
    tokens = text.replace(",", "").split()
    for token in tokens:
        if any(char.isdigit() for char in token):  # ada angka
            return token.upper()
    return None

def find_kanban(df, code):
    """Cari data berdasarkan KanbanNo"""
    if "kanbanno" not in df.columns:
        return None
    row = df[df["kanbanno"].astype(str).str.upper().str.contains(code.upper(), na=False)]
    if row.empty:
        return None
    return row.iloc[0].to_dict()

# ==============================
# Mapping pertanyaan → kolom
# ==============================
COLUMN_KEYWORDS = {
    "stock": ["stockoverall", "stock_overall", "stock"],
    "pcs per kanban": ["pcsperkanban", "qtyperkanban", "qty", "pcs"],
    "supplier": ["suppliername", "supplier_name", "supplier"],
    "part": ["partname", "part_name", "part"],
    "part no": ["partno", "part_no", "partnumber"],
    "dock": ["dockcode", "dock_code"],
    "plant": ["plantcode", "plant_code"],
    "kanban address": ["kanbanaddress", "kanban_address"],
    "last received": ["lastreceiveddate", "last_received_date"],
    "category": ["category"]
}

def match_column(user_input, columns):
    """Cari kolom yang relevan dengan pertanyaan user"""
    best_match = None
    highest_score = 0
    for key, col_list in COLUMN_KEYWORDS.items():
        score = fuzz.partial_ratio(user_input.lower(), key.lower())
        if score > highest_score and score > 60:
            for col in col_list:
                if col in columns:
                    best_match = col
                    highest_score = score
                    break
    return best_match

# ==============================
# Fungsi utama
# ==============================
def process_query(user_input, df):
    global conversation_context
    user_input = user_input.strip().lower()

    if df.empty:
        return "Data part tidak dapat dimuat saat ini.", None

    # Ambil kode Kanban dari input atau dari konteks
    kanban_code = extract_kanban(user_input) or conversation_context.get("last_kanban")
    if not kanban_code:
        if any(word in user_input for word in COLUMN_KEYWORDS):
            return "Silakan sebutkan kode Kanban terlebih dahulu.", None
        return "Saya belum memahami maksud pertanyaan Anda.", None

    record = find_kanban(df, kanban_code)
    if record is None:
        return f"Saya tidak menemukan Kanban {kanban_code} pada sistem.", None

    # Update konteks
    conversation_context["last_kanban"] = kanban_code

    # Tentukan kolom relevan
    col = match_column(user_input, record.keys())

    # Jika cocok kolom
    if col:
        value = record.get(col, "(tidak tersedia)")
        # Bentuk jawaban kontekstual
        if col in COLUMN_KEYWORDS["stock"]:
            return f"Stok Kanban {kanban_code} ({record.get('partname','')}) saat ini {value} pcs dari supplier {record.get('suppliername','')}.", kanban_code
        elif col in COLUMN_KEYWORDS["pcs per kanban"]:
            return f"Jumlah per Kanban {kanban_code} adalah {value} pcs.", kanban_code
        elif col in COLUMN_KEYWORDS["supplier"]:
            return f"Supplier untuk Kanban {kanban_code} adalah {value}.", kanban_code
        elif col in COLUMN_KEYWORDS["part"]:
            return f"Nama part Kanban {kanban_code} adalah {value}.", kanban_code
        elif col in COLUMN_KEYWORDS["part no"]:
            return f"Part number Kanban {kanban_code} adalah {value}.", kanban_code
        else:
            return f"{col} untuk Kanban {kanban_code} adalah {value}.", kanban_code

    # Jika tidak ada kolom spesifik → tampilkan ringkasan penting
    summary_cols = ["partname", "suppliername", "stockoverall", "pcsperkanban", "partno"]
    summary_text = ", ".join([f"{c}: {record.get(c,'(tidak tersedia)')}" for c in summary_cols if c in record])
    return f"Kanban {kanban_code} - {summary_text}", kanban_code
