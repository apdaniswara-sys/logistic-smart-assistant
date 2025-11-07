import requests

API_URL = "https://api.yourcompany.com/stock"  # Ganti sesuai API internal

def get_stock_available(part_no):
    """
    Memanggil API untuk mendapatkan stock.
    Dipanggil sekali per query agar efisien.
    """
    try:
        response = requests.get(f"{API_URL}?part_no={part_no}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("stock_available", "Unknown")
        else:
            return f"API Error: {response.status_code}"
    except Exception as e:
        return f"API Error: {str(e)}"
