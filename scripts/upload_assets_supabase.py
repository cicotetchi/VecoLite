#!/usr/bin/env python3
"""
Upload des assets statiques VecoLite vers Supabase Storage.
Utilise uniquement la bibliothèque standard Python (pas de dépendances).

Usage :
    SUPABASE_SERVICE_KEY="votre-service-role-key" python3 scripts/upload_assets_supabase.py

Où trouver la clé :
    Supabase Dashboard → Project → Settings → API → service_role (secret)
"""

import os, sys, json
import urllib.request, urllib.error

SUPABASE_URL = "https://xlpypozfpuemuanhnoxh.supabase.co"
BUCKET       = "assets"
PUBLIC_DIR   = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public")
CDN_BASE     = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}"

ASSETS = [
    ("logo.jpeg",            "image/jpeg"),
    ("favicon.ico",          "image/x-icon"),
    ("favicon-32.png",       "image/png"),
    ("apple-touch-icon.png", "image/png"),
]


def request(url, method="GET", data=None, extra_headers=None, key=""):
    h = {"Authorization": f"Bearer {key}", "apikey": key, **(extra_headers or {})}
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def main():
    key = os.environ.get("SUPABASE_SERVICE_KEY", "").strip()
    if not key:
        print("❌  Variable SUPABASE_SERVICE_KEY manquante.")
        print('   SUPABASE_SERVICE_KEY="ta-clé" python3 scripts/upload_assets_supabase.py')
        sys.exit(1)

    # Créer bucket public
    body = json.dumps({"id": BUCKET, "name": BUCKET, "public": True}).encode()
    status, resp = request(
        f"{SUPABASE_URL}/storage/v1/bucket", "POST", body,
        {"Content-Type": "application/json"}, key
    )
    if status in (200, 201):
        print(f"✅  Bucket « {BUCKET} » créé (public)")
    elif status == 409:
        print(f"ℹ️   Bucket « {BUCKET} » existe déjà")
    else:
        print(f"⚠️   Bucket : {status} — {resp}")

    # Uploader les fichiers
    print()
    uploaded = []
    for filename, ctype in ASSETS:
        path = os.path.join(PUBLIC_DIR, filename)
        if not os.path.exists(path):
            print(f"⚠️   Introuvable : {path}")
            continue
        with open(path, "rb") as f:
            data = f.read()
        status, resp = request(
            f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{filename}",
            "POST", data, {"Content-Type": ctype, "x-upsert": "true"}, key
        )
        if status in (200, 201):
            print(f"✅  {filename:<30}  →  {CDN_BASE}/{filename}")
            uploaded.append(filename)
        else:
            print(f"❌  {filename} : {status} — {resp}")

    print()
    print(f"🏁  {len(uploaded)}/{len(ASSETS)} fichiers uploadés sur Supabase Storage")


if __name__ == "__main__":
    main()
