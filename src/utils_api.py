import requests

# Contoh struktur API — silakan sesuaikan dengan endpoint kamu
API_URL = "https://yourserver.com/api/stock"  # ganti ke URL sebenarnya

def get_realtime_stock(part_no_or_kanban: str):
    """
    Memanggil API real-time untuk mendapatkan stok part tertentu.
    Ganti parameter dan struktur JSON sesuai dengan sistem kamu.
    """
    try:
        params = {"query": part_no_or_kanban}
        response = requests.get(API_URL, params=params, timeout=5)

        if response.status_code == 200:
            data = response.json()
            # contoh hasil JSON: {"part": "105D", "stock": 25, "uom": "PCS"}
            if "stock" in data:
                return f"Stok terkini untuk {data.get('part', part_no_or_kanban)} adalah {data['stock']} {data.get('uom', '')}."
            else:
                return "Data stok tidak ditemukan dalam respon API."
        else:
            return f"Gagal mengambil data stok. (status {response.status_code})"
    except Exception as e:
        return f"Terjadi kesalahan saat memanggil API stok: {e}"
