"""Acquire the two prespecified hourly price days and the public SimBench MV archive."""
import argparse
from datetime import date, datetime, time, timedelta, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import sys
from urllib.parse import urlencode
import subprocess
from zipfile import ZipFile
from zoneinfo import ZoneInfo


PRICE_DAYS = (date(2024, 1, 17), date(2024, 7, 17))
GRID_URL = "https://daks.uni-kassel.de/bitstreams/84ac49bc-fa58-4480-b5ae-2962bf287a70/download"
PRICE_API = "https://api.energidataservice.dk/dataset/Elspotprices"


def fetch(url, max_bytes, timeout):
    # Use the host HTTPS trust configuration. TLS verification stays enabled
    # for the original connection and for any explicitly HTTPS-only redirect.
    reply = subprocess.run(
        ["/usr/bin/curl", "--disable", "--fail-with-body", "--show-error", "--silent", "--location",
         "--proto", "=https", "--proto-redir", "=https", "--max-redirs", "4",
         "--connect-timeout", "15", "--max-time", str(timeout), "--max-filesize", str(max_bytes),
         "--write-out", "%{stderr}\nstatus=%{http_code} retry_after=%header{retry-after}", url],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if reply.returncode:
        error = reply.stderr.decode(errors="replace").strip()
        if "status=429" in error:
            error += " " + reply.stdout[:500].decode(errors="replace").strip()
        raise OSError(f"curl {reply.returncode}: {error}")
    buffer = reply.stdout
    if len(buffer) > max_bytes:
        raise ValueError("source exceeds frozen size limit")
    return buffer


def price_url(day):
    return PRICE_API + "?" + urlencode({
        "start": day.isoformat(), "end": (day + timedelta(days=1)).isoformat(),
        "filter": '{"PriceArea":["DE"]}', "columns": "HourUTC,PriceArea,SpotPriceEUR",
        "sort": "HourUTC", "limit": 100,
    })


def check_day(buffer, day):
    payload = json.loads(buffer)
    local = ZoneInfo("Europe/Berlin")
    start = datetime.combine(day, time(), local).astimezone(timezone.utc)
    end = datetime.combine(day + timedelta(days=1), time(), local).astimezone(timezone.utc)
    rows = payload["records"]
    hours = int((end - start) / timedelta(hours=1))
    if payload["total"] != hours or len(rows) != hours:
        raise ValueError("incomplete local day")
    for i, row in enumerate(rows):
        stamp = datetime.fromisoformat(row["HourUTC"])
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=timezone.utc)
        if (row["PriceArea"] != "DE" or stamp != start + timedelta(hours=i)
                or not math.isfinite(row["SpotPriceEUR"])):
            raise ValueError("invalid zone, hour sequence or price")
    return {"validated_hours": hours, "observed_price_areas": sorted({row["PriceArea"] for row in rows}),
            "first_utc": start.isoformat(),
            "end_utc_exclusive": end.isoformat(), "units": "EUR/MWh"}


def main():
    sources = [(f"DE-{day}.json", price_url(day), 1_000_000, day) for day in PRICE_DAYS]
    sources.append(("1-MV-rural--0-sw.zip", GRID_URL, 100_000_000, None))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out", type=Path)
    parser.add_argument("--only", action="append", choices=[s[0] for s in sources],
                        help="Fetch only the named inputs. Already admitted inputs can be reused.")
    args = parser.parse_args()
    out = args.out
    out.mkdir(exist_ok=False)
    entries = []
    for name, url, limit, day in sources:
        if args.only and name not in args.only:
            continue
        entry = {"file": name, "url": url, "status": "pending"}
        entries.append(entry)
        try:
            buffer = fetch(url, limit, 180 if day is None else 30)
            (out / name).write_bytes(buffer)
            entry.update(bytes=len(buffer), sha256=hashlib.sha256(buffer).hexdigest())
            if day is not None:
                entry.update(check_day(buffer, day))
            else:
                with ZipFile(io.BytesIO(buffer)) as archive:
                    names = {Path(item).name for item in archive.namelist()}
                    required = {"Node.csv", "Line.csv", "Transformer.csv", "Switch.csv",
                                "Load.csv", "LoadProfile.csv", "RESProfile.csv"}
                    if not required <= names:
                        raise ValueError(f"missing grid/profile tables: {sorted(required - names)}")
                    entry["present_tables"] = sorted(names & required)
            entry["status"] = "received"
        except Exception as exc:
            entry.update(status="failed", error=f"{type(exc).__name__}: {exc}")
    receipt = {"sources": entries, "note": "Archive structure and hourly coverage only. No case evaluation."}
    print(json.dumps(receipt, indent=2))
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return int(any(entry["status"] != "received" for entry in entries))


if __name__ == "__main__":
    raise SystemExit(main())
