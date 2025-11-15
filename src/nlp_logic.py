import pandas as pd
import requests

API_URL = "http://10.64.6.27/legion/limit_5_dock43.php"
CSV_FALLBACK = "data/master_parts.csv"

conversation_context = {
    "last_kanban": None,
}

# ===========================
# Fungsi bantu
# ===========================
def normalize_columns(df):
    df.columns = [c.strip().lower() for c in df.columns]
    return df

def safe_get(mapping, *possible_keys):
    mapping_lower = {k.lower(): v for k, v in mapping.items()}
    for k in possible_keys:
        key = k.lower()
        if key in mapping_lower and str(mapping_lower[key]).strip() != "":
            return mapping_lower[key]
    return None

def extract_kanban(text: str):
    tokens = text.replace(",", "").split()
    for token in tokens:
        if any(char.isdigit() for char in token):
            return token.upper()
    return None

def find_part(df, code):
    if "kanbanno" not in df.columns:
        return None
    result = df[df["kanbanno"].astype(str).str.upper().str.contains(code.upper(), na=False)]
    if result.empty:
        return None
    return result.iloc[0].to_dict()

def load_data():
    try:
        response = requests.get(API_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data["data"])
        return normalize_columns(df)
    except:
        try:
            df = pd.read_csv(CSV_FALLBACK, sep=";")
            return normalize_columns(df)
        except:
            return pd.DataFrame()

# ===========================
# Fungsi utama pemrosesan query
# ===========================
def process_query(user_input: str):
    global conversation_context
    df = load_data()
    if df.empty:
        return "Data part tidak dapat dimuat saat ini."

    user_input_lower = user_input.strip().lower()
    last_kanban = conversation_context.get("last_kanban")
    code = extract_kanban(user_input_lower) or last_kanban
    if not code:
        return "Silakan sebutkan kode Kanban terlebih dahulu."

    part_data = find_part(df, code)
    if not part_data:
        return f"Saya tidak menemukan Kanban {code} pada sistem."

    conversation_context["last_kanban"] = code

    # Ambil semua field penting
    part_name = safe_get(part_data, "partname", "part_name")
    part_no = safe_get(part_data, "partno", "part_no")
    supplier = safe_get(part_data, "suppliername", "supplier_name")
    supplier_code = safe_get(part_data, "suppliercode", "supplier_code")
    plant_code = safe_get(part_data, "plantcode", "plant_code")
    dock_code = safe_get(part_data, "dockcode", "dock_code")
    address = safe_get(part_data, "kanbanaddress", "kanban_address")
    stock_pcs = safe_get(part_data, "stockoverall", "stock_overall", "stock")
    stock_sps = safe_get(part_data, "stocksps", "stock_sps")
    stock_receiving = safe_get(part_data, "stockreceiving", "stock_receiving")
    stock_minutes = safe_get(part_data, "stockspsminutes", "stock_sps_minutes", "stockoverallminutes", "stock_overall_minutes")
    pcs_per_kanban = safe_get(part_data, "pcsperkanban", "qtyperkanban", "pcs")
    last_received = safe_get(part_data, "lastreceiveddate", "last_received_date")

    # ===========================
    # Deteksi intent stock
    # ===========================
    if any(word in user_input_lower for word in ["stock", "stok", "jumlah stock", "berapa stock"]):
        if "menit" in user_input_lower or "minute" in user_input_lower:
            if stock_minutes is not None:
                return f"Stok Kanban {code} saat ini {stock_minutes} menit."
            else:
                return f"Informasi stock dalam menit tidak tersedia untuk Kanban {code}."
        elif "jam" in user_input_lower:
            if stock_minutes is not None:
                stock_hours = round(float(stock_minutes) / 60, 2)
                return f"Stok Kanban {code} saat ini setara {stock_hours} jam."
            else:
                return f"Informasi stock dalam jam tidak tersedia untuk Kanban {code}."
        elif "sps" in user_input_lower:
            if stock_sps is not None:
                return f"Stock SPS Kanban {code} saat ini {stock_sps} pcs."
            else:
                return f"Informasi Stock SPS tidak tersedia untuk Kanban {code}."
        elif "receiving" in user_input_lower:
            if stock_receiving is not None:
                return f"Stock Receiving Kanban {code} saat ini {stock_receiving} pcs."
            else:
                return f"Informasi Stock Receiving tidak tersedia untuk Kanban {code}."
        else:
            if stock_pcs is not None:
                return f"Stok Kanban {code} saat ini {stock_pcs} pcs."
            else:
                return f"Informasi stock tidak tersedia untuk Kanban {code}."

    # ===========================
    # Intent lainnya
    # ===========================
    if any(k in user_input_lower for k in ["supplier code"]):
        return f"Supplier code Kanban {code} adalah {supplier_code}."
    if any(k in user_input_lower for k in ["supplier", "supplier name", "nama supplier", "suppliernya"]):
        return f"Supplier Kanban {code} adalah {supplier}."
    if any(k in user_input_lower for k in ["plant", "plan"]):
        msg = f"Plant code Kanban {code} adalah {plant_code}" if plant_code else ""
        if dock_code:
            msg += f" dengan dock {dock_code}"
        return msg if msg else f"Informasi plant/dock tidak tersedia untuk Kanban {code}."
    if any(k in user_input_lower for k in ["dock"]):
        return f"Dock Kanban {code} berada di {dock_code}." if dock_code else f"Informasi dock tidak tersedia untuk Kanban {code}."
    if any(k in user_input_lower for k in ["address", "alamat"]):
        return f"Alamat Kanban {code} berada di {address}." if address else f"Informasi alamat tidak tersedia untuk Kanban {code}."
    if any(k in user_input_lower for k in ["part no", "part no.", "partnumber", "nomor part"]):
        return f"Nomor part Kanban {code} adalah {part_no}." if part_no else f"Informasi part no tidak tersedia untuk Kanban {code}."
    if any(k in user_input_lower for k in ["nama part", "partname", "part name"]):
        return f"Kanban {code} adalah part {part_name}." if part_name else f"Informasi nama part tidak tersedia untuk Kanban {code}."
    if any(k in user_input_lower for k in ["pcs per kanban", "pcs perkanban", "qty perkanban", "qty per kanban", "jumlah per kanban", "isi kanban"]):
        return f"Jumlah per Kanban {code} adalah {pcs_per_kanban} pcs." if pcs_per_kanban else f"Informasi pcs per kanban tidak tersedia untuk Kanban {code}."
    if any(k in user_input_lower for k in ["last received", "tanggal kirim", "tanggal datang", "tanggal terima", "tanggal terakhir", "terakhir"]):
        return f"Part Kanban {code} terakhir diterima pada {last_received}." if last_received else f"Informasi tanggal last received tidak tersedia untuk Kanban {code}."

    # Default fallback
    return f"Kanban {code} ditemukan. Silakan tanyakan informasi spesifik seperti stok, supplier, alamat, dock, plant, part no, pcs per kanban, atau last received."
