# import pandas as pd

# def load_master_parts(filepath="data/master_parts.csv"):
#     try:
#         df = pd.read_csv(filepath, delimiter=';')
#         df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
#         return df
#     except Exception as e:
#         print(f"⚠️ Gagal memuat master_parts.csv: {e}")
#         return pd.DataFrame()

# def get_part_info(part_no, df):
#     if df.empty:
#         return None

#     part_no = str(part_no).strip().lower()
#     df["kanban_no"] = df["kanban_no"].astype(str).str.lower()

#     match = df[df["kanban_no"].str.contains(part_no, case=False, na=False)]

#     if match.empty:
#         return None

#     info = match.iloc[0].to_dict()

#     return {
#         "Part Name": info.get("part_name", "-"),
#         "Part No": info.get("part_no", "-"),
#         "Supplier Name": info.get("supplier_/_exporter_name", "-"),
#         "Qty/Box": info.get("order_lot_size", "-"),
#         "Line Address": info.get("kanban_no", "-"),
#     }
