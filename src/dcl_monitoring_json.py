# src/dcl_monitoring_json.py

import requests
import time

DCL_URL = "http://10.64.6.27/legion/dcl_monitoring_dock43.php"
DCL_CACHE_TTL = 30  # seconds

_dcl_cache = {"rows": None, "ts": 0}


# LOAD DCL JSON (with caching)
def load_dcl_json():
    global _dcl_cache
    now = time.time()

    if _dcl_cache["rows"] is not None and (now - _dcl_cache["ts"]) < DCL_CACHE_TTL:
        return {"rows": _dcl_cache["rows"]}

    try:
        r = requests.get(DCL_URL, timeout=5)
        r.raise_for_status()
        payload = r.json()

        rows = payload.get("data", [])
        _dcl_cache["rows"] = rows
        _dcl_cache["ts"] = now
        return {"rows": rows}

    except Exception:
        return None


# STATUS MAPPING (FINAL)
def normalize_status(st):
    if not st:
        return ""

    st = st.strip().lower()

    if st == "arrived":
        return "arrived"
    if st == "advanced":
        return "advanced"
    if st == "late":
        return "late"
    if st == "delay":
        return "delay"
    if st == "waiting":
        return "waiting"

    return st


# COUNTERS
def count_arrived(rows):
    return sum(1 for r in rows if normalize_status(r[8]) == "arrived")


def count_advanced(rows):
    return sum(1 for r in rows if normalize_status(r[8]) == "advanced")


def count_late(rows):
    return sum(1 for r in rows if normalize_status(r[8]) == "late")


def count_delay(rows):
    return sum(1 for r in rows if normalize_status(r[8]) == "delay")


def count_waiting(rows):
    return sum(1 for r in rows if normalize_status(r[8]) == "waiting")


def count_not_arrived(rows):
    return count_delay(rows) + count_waiting(rows)


def count_on_time(rows):
    return count_arrived(rows)

# DOCK COUNTER
def count_by_dock(rows, dock):
    return sum(1 for r in rows if str(r[0]).strip() == str(dock).strip())

# LIST ROUTES BY STATUS
def get_routes_by_status(rows, status):
    status = normalize_status(status)
    result = []

    for r in rows:
        st = normalize_status(r[8])
        if st == status:
            result.append(str(r[2]))

    return result


# FIND SINGLE ROUTE ROW (for detail query)

def find_route_row(rows, route_name):
    route_name = route_name.strip().lower()

    for r in rows:
        if str(r[2]).strip().lower() == route_name:
            return r

    return None


# SUMMARY (OTIF)
def summarize_dcl(rows):
    total = len(rows)
    advanced = count_advanced(rows)
    arrived = count_arrived(rows)
    late = count_late(rows)
    delay = count_delay(rows)
    waiting = count_waiting(rows)
    not_arrived = delay + waiting

    on_time_ratio = 0
    if total > 0:
        on_time_ratio = round(arrived / total * 100, 2)

    return {
        "total": total,
        "advanced": advanced,
        "arrived": arrived,
        "late": late,
        "delay": delay,
        "waiting": waiting,
        "not_arrived": not_arrived,
        "on_time_ratio": on_time_ratio,
    }
