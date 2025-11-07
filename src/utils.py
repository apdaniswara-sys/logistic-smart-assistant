import pandas as pd

def load_master_parts(csv_path="data/master_parts.csv"):
    """
    Load CSV master parts.
    """
    try:
        df = pd.read_csv(csv_path)
        return df
    except FileNotFoundError:
        print(f"File {csv_path} tidak ditemukan.")
        return pd.DataFrame()

def get_part_info(master_df, part_no):
    """
    Mengambil informasi part dari master_df berdasarkan Part No.
    """
    part_row = master_df[master_df['Part No'] == part_no]
    if part_row.empty:
        return None
    return part_row.to_dict(orient='records')[0]
