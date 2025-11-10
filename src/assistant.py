import re
from src.utils import load_master_parts, get_part_info
from src.stock_api import get_stock_available

# Load master parts saat modul diimport
master_df = load_master_parts()

def get_intent(user_text):
    """
    Tentukan intent berdasarkan keyword.
    Bisa dikembangkan dengan NLP lebih lanjut.
    """
    text = user_text.lower()

    if "detail" in text:
        return "detail"
    elif "supplier" in text:
        return "supplier"
    elif "qty" in text or "per box" in text:
        return "qty"
    elif "line" in text:
        return "line"
    elif "stock" in text or "tersedia" in text or "berapa" in text:
        return "stock"
    else:
        return "stock"  # default intent

def extract_part_no(user_text):
    """
    Extract Part No dari teks user (format alfanumerik seperti 105D, 106E)
    """
    match = re.search(r'\b[A-Z0-9]+\b', user_text.upper())
    return match.group(0) if match else None

def answer_query_contextual(user_text):
    """
    Jawaban kontekstual sesuai intent.
    Stock API dipanggil hanya sekali per query.
    """
    intent = get_intent(user_text)
    part_no = extract_part_no(user_text)

    if not part_no:
        return "Maaf, saya tidak menemukan Part No di perintah Anda."

    part_info = get_part_info(master_df, part_no)
    if not part_info:
        return f"Part {part_no} tidak ditemukan."

    # Panggil stock API sekali per query
    stock_available = get_stock_available(part_no)

    if intent == "stock":
        return f"Stock tersedia untuk Part {part_no}: {stock_available}"
    elif intent == "detail":
        return f"""
Part Name      : {part_info['Part Name']}
Part No        : {part_info['Part No']}
Supplier Name  : {part_info['Supplier Name']}
Qty/Box        : {part_info['Qty/Box']}
Line Address   : {part_info['Line Address']}
Stock Available: {stock_available}
""".strip()
    elif intent == "supplier":
        return f"Supplier untuk Part {part_no}: {part_info['Supplier Name']}"
    elif intent == "qty":
        return f"Qty per Box untuk Part {part_no}: {part_info['Qty/Box']}"
    elif intent == "line":
        return f"Line Address untuk Part {part_no}: {part_info['Line Address']}"
    else:
        # Default fallback
        return f"Stock tersedia untuk Part {part_no}: {stock_available}"

# Contoh test mandiri
if __name__ == "__main__":
    user_inputs = [
        "Berikan stock 105D",
        "Detail part 105D",
        "Supplier 105D",
        "Qty per box 105D",
        "Line address 105D"
    ]

    for text in user_inputs:
        print(f"> User: {text}")
        print(answer_query_contextual(text))
        print("-" * 40)
