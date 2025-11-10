import pandas as pd
import requests

# ==============================
# Konfigurasi dasar
# ==============================
API_URL = "http://10.64.6.27/legion/limit_5_dock43.php"
CSV_FALLBACK = "data/master_parts.csv"

# Menyimpan konteks percakapan
conversation_context = {
    "last_kanban": None,
    "last_part": None,
    "last_supplier": None,
    "last_stock": None,
    "last_qty_kanban": None,
    "last_partno": None
}


# ==============================
# Fungsi bantu
# ==============================
def normalize_columns(df):
    """Ubah semua nama kolom ke huruf kecil agar konsisten"""
    df.columns = [c.strip().lower() for c in df.columns]
    return df


def safe_get(mapping, *possible_keys):
    """Ambil nilai dengan aman (abaikan huruf besar kecil)"""
    mapping_lower = {k.lower(): v for k, v in mapping.items()}
    for k in possible_keys:
        key = k.lower()
        if key in mapping_lower and str(mapping_lower[key]).strip() != "":
            return mapping_lower[key]
    return ""


def extract_kanban(text: str):
    """Ambil kemungkinan kode Kanban dari teks"""
    tokens = text.replace(",", "").split()
    for token in tokens:
        if any(char.isdigit() for char in token):  # mengandung angka
            return token.upper()
    return None


def find_part(df, code):
    """Cari data berdasarkan KanbanNo"""
    if "kanbanno" not in df.columns:
        return None
    result = df[df["kanbanno"].astype(str).str.upper().str.contains(code.upper(), na=False)]
    if result.empty:
        return None
    return result.iloc[0].to_dict()


# ==============================
# Fungsi ambil data
# ==============================
def load_data():
    """Ambil data dari API, fallback ke CSV, atau dummy"""
    try:
        response = requests.get(API_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        print("[✅] Data berhasil diambil dari API.")
        df = pd.DataFrame(data["data"])
        return normalize_columns(df)

    except Exception as e:
        print(f"[⚠️] Gagal ambil data dari API: {e}")
        print("[ℹ️] Mencoba memuat data dari file lokal...")

        try:
            df = pd.read_csv(CSV_FALLBACK, sep=";")
            print(f"[✅] Data berhasil dimuat dari file lokal: {CSV_FALLBACK}")
            return normalize_columns(df)
        except Exception as e2:
            print(f"[❌] Gagal load data lokal: {e2}")
            print("[⚠️] Menggunakan data dummy karena file tidak ditemukan.")
            dummy_data = pd.DataFrame([
                {"KanbanNo": "105D", "PartName": "COVER RR BUMPER", "SupplierName": "SUGITY CREATIVES", "StockOverall": 248, "QtyPerKanban": 12, "PartNo": "52159-BZ230"},
                {"KanbanNo": "106A", "PartName": "FR BUMPER", "SupplierName": "SUMMIT ADYAWINSA", "StockOverall": 310, "QtyPerKanban": 10, "PartNo": "52021-BZ230"},
                {"KanbanNo": "107C", "PartName": "DOOR PANEL LH", "SupplierName": "INDOJAYA", "StockOverall": 150, "QtyPerKanban": 8, "PartNo": "67011-BZ230"},
            ])
            return normalize_columns(dummy_data)


# ==============================
# Fungsi utama pemrosesan pertanyaan user
# ==============================
def process_query(user_input: str):
    global conversation_context
    user_input = user_input.strip().lower()
    df = load_data()

    if df.empty:
        return "Data part tidak dapat dimuat saat ini."

    last_kanban = conversation_context.get("last_kanban")

    # Ambil kode dari input atau dari konteks
    code = extract_kanban(user_input)
    if not code and last_kanban:
        code = last_kanban
    if not code:
        if any(k in user_input for k in ["stok", "stock", "supplier", "part", "kanban", "pcs"]):
            return "Silakan sebutkan kode Kanban terlebih dahulu."
        return "Saya belum memahami maksud pertanyaan kamu."

    match = find_part(df, code)
    if match is None:
        return f"Saya tidak menemukan Kanban {code} pada sistem."

    # Ambil data dengan aman
    kanban = safe_get(match, "kanbanno", "kanban", "kanban_no")
    part = safe_get(match, "partname", "part_name", "name")
    supplier = safe_get(match, "suppliername", "supplier_name", "supplier")
    stock = safe_get(match, "stockoverall", "stock_overall", "stock")
    qty = safe_get(match, "pcsperkanban", "qtyperkanban", "qty", "pcs")
    partno = safe_get(match, "partno", "part_no", "partnumber")

    # Update konteks percakapan
    conversation_context.update({
        "last_kanban": kanban,
        "last_part": part,
        "last_supplier": supplier,
        "last_stock": stock,
        "last_qty_kanban": qty,
        "last_partno": partno
    })

    # =========================
    # Deteksi intent pengguna
    # =========================
    intents = []

    if "supplier" in user_input:
        intents.append(f"suppliernya {supplier}")
    if "stok" in user_input or "stock" in user_input:
        intents.append(f"stoknya {stock} pcs")
    if "pcs per kanban" in user_input or "isi kanban" in user_input or "per kanban" in user_input:
        intents.append(f"jumlah per kanban {qty} pcs")
    if "part no" in user_input or "part number" in user_input or "nomor part" in user_input:
        intents.append(f"part number-nya {partno}")
    if "nama part" in user_input or (("part" in user_input or "partname" in user_input) and "no" not in user_input):
        intents.append(f"nama part-nya {part}")

    # =========================
    # Bentuk respon akhir
    # =========================
    if len(intents) > 1:
        return f"Untuk Kanban {kanban}, " + ", ".join(intents) + "."

    if "supplier" in user_input:
        return f"Supplier untuk Kanban {kanban} adalah {supplier}."

    elif "part no" in user_input or "part number" in user_input or "nomor part" in user_input:
        return f"Part number Kanban {kanban} adalah {partno}."

    elif "pcs per kanban" in user_input or "isi kanban" in user_input or "per kanban" in user_input:
        return f"Jumlah per Kanban {kanban} adalah {qty} pcs."

    elif "stok" in user_input or "stock" in user_input:
        return f"Stok Kanban {kanban} ({part}) saat ini adalah {stock} pcs dari supplier {supplier}."

    elif "nama part" in user_input or ("part" in user_input and "name" in user_input):
        return f"Kanban {kanban} adalah part {part}."

    elif "berapa" in user_input and "stok" not in user_input:
        return f"Stok Kanban {kanban} ({part}) saat ini {stock} pcs dari supplier {supplier}."

    else:
        return f"Untuk Kanban {kanban}, stok {stock} pcs dari supplier {supplier}."
