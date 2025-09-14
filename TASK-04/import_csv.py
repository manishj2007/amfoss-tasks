
import csv
import os
from pathlib import Path
import mysql.connector as mysql

# ---------- CONFIG ----------
DB = dict(
    host="localhost",
    user="cine",        # set to your MySQL user
    password="cinepass",# set to your MySQL password
    database="cinescope"
)
TABLE = "movies"
CSV_FILENAME = "movies.csv"
TRUNCATE_FIRST = True   # set False if you want to append instead of clearing
BATCH_SIZE = 1000       # insert in batches for speed
# ----------------------------

# Expected CSV headers -> DB column names (left = CSV header)
# Adjust these if your CSV uses different header names.
HEADER_MAP = {
    "Series_Title": "Series_Title",
    "Released_Year": "Released_Year",
    "Genre": "Genre",
    "IMDB_Rating": "IMDB_Rating",
    "Director": "Director",
    "Star1": "Star1",
    "Star2": "Star2",
    "Star3": "Star3",
}

# Table schema (id auto-increments)
SCHEMA_SQL = f"""
CREATE TABLE IF NOT EXISTS {TABLE} (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Series_Title   VARCHAR(255),
    Released_Year  INT,
    Genre          VARCHAR(255),
    IMDB_Rating    DECIMAL(3,1),
    Director       VARCHAR(255),
    Star1          VARCHAR(255),
    Star2          VARCHAR(255),
    Star3          VARCHAR(255)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

def to_int(x):
    if x is None: return None
    s = str(x).strip()
    if s == "": return None
    # Remove non-digits like quotes or extra spaces
    s = "".join(ch for ch in s if (ch.isdigit() or ch == "-"))
    try:
        return int(s) if s != "" else None
    except:
        return None

def to_float(x):
    if x is None: return None
    s = str(x).strip()
    if s == "": return None
    # Allow values like "9.0", "8", etc.
    try:
        return float(s)
    except:
        return None

def normalize_str(x):
    if x is None: return None
    s = str(x).strip()
    return s if s != "" else None

def open_connection():
    return mysql.connect(**DB)

def ensure_table(cur):
    cur.execute(SCHEMA_SQL)

def truncate_table(cur):
    cur.execute(f"TRUNCATE TABLE {TABLE}")

def read_csv_rows(csv_path):
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # verify headers
        missing = [h for h in HEADER_MAP.keys() if h not in reader.fieldnames]
        if missing:
            raise SystemExit(
                f"❌ CSV is missing expected headers: {missing}\n"
                f"   Found headers: {reader.fieldnames}\n"
                f"   Update HEADER_MAP in this script to match your CSV."
            )
        for row in reader:
            yield row

def prepare_record(csv_row):
    # Build a dict that matches DB column order from HEADER_MAP values
    record = {}
    for csv_key, db_col in HEADER_MAP.items():
        val = csv_row.get(csv_key)

        # Cast by column
        if db_col == "Released_Year":
            record[db_col] = to_int(val)
        elif db_col == "IMDB_Rating":
            record[db_col] = to_float(val)
        else:
            record[db_col] = normalize_str(val)
    return record

def insert_batch(cur, rows, cols):
    if not rows:
        return
    placeholders = ", ".join(["%s"] * len(cols))
    col_sql = ", ".join(cols)
    sql = f"INSERT INTO {TABLE} ({col_sql}) VALUES ({placeholders})"
    data = [tuple(r[c] for c in cols) for r in rows]
    cur.executemany(sql, data)

def main():
    csv_path = Path(__file__).with_name(CSV_FILENAME)
    if not csv_path.exists():
        raise SystemExit(f"❌ Cannot find {CSV_FILENAME} next to this script at: {csv_path}")

    conn = open_connection()
    cur = conn.cursor()

    # Ensure table exists
    ensure_table(cur)
    conn.commit()

    # Optionally clear existing data
    if TRUNCATE_FIRST:
        truncate_table(cur)
        conn.commit()

    # Column order we will insert into
    cols = list(HEADER_MAP.values())

    total = 0
    batch = []

    print(f"📥 Reading {CSV_FILENAME} and inserting into `{DB['database']}.{TABLE}` ...")

    for csv_row in read_csv_rows(csv_path):
        rec = prepare_record(csv_row)
        batch.append(rec)
        if len(batch) >= BATCH_SIZE:
            insert_batch(cur, batch, cols)
            conn.commit()
            total += len(batch)
            print(f"  -> inserted {total} rows...")
            batch.clear()

    # Insert trailing batch
    if batch:
        insert_batch(cur, batch, cols)
        conn.commit()
        total += len(batch)

    cur.close()
    conn.close()
    print(f"✅ Done. Inserted {total} rows into `{TABLE}`.")

if __name__ == "__main__":
    main()