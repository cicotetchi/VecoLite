#!/usr/bin/env python3
"""
Upload des assets statiques VecoLite vers Supabase Storage.

Usage :
    SUPABASE_SERVICE_KEY="votre-service-role-key" python3 scripts/upload_assets_supabase.py

Où trouver la clé :
    Supabase Dashboard → Project → Settings → API → service_role (secret)

Les fichiers uploadés seront accessibles publiquement via :
    https://xlpypozfpuemuanhnoxh.supabase.co/storage/v1/object/public/assets/<fichier>
"""

import os
import sys
import requests

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


def main():
    key = os.environ.get("SUPABASE_SERVICE_KEY", "").strip()
    if not key:
        print("❌  Variable SUPABASE_SERVICE_KEY manquante.")
        print()
        print("   Exécute :")
        print('   SUPABASE_SERVICE_KEY="ta-clé" python3 scripts/upload_assets_supabase.py')
        print()
        print("   Clé disponible sur :")
        print("   Supabase → Settings → API → service_role")
        sys.exit(1)

    headers = {"Authorization": f"Bearer {key}", "apikey": key}

    # ── Création du bucket public ──────────────────────────────────────────
    r = requests.post(
        f"{SUPABASE_URL}/storage/v1/bucket",
        headers=headers,
        json={"id": BUCKET, "name": BUCKET, "public": True},
    )
    if r.status_code in (200, 201):
        print(f"✅  Bucket « {BUCKET} » créé (public)")
    elif r.status_code == 409:
        print(f"ℹ️   Bucket « {BUCKET} » existe déjà")
    else:
        print(f"⚠️   Bucket : {r.status_code} — {r.text}")

    # ── Upload des fichiers ────────────────────────────────────────────────
    print()
    uploaded = []
    for filename, content_type in ASSETS:
        path = os.path.join(PUBLIC_DIR, filename)
        if not os.path.exists(path):
            print(f"⚠️   Introuvable localement : {path}")
            continue

        with open(path, "rb") as f:
            data = f.read()

        r = requests.post(
            f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{filename}",
            headers={**headers, "Content-Type": content_type, "x-upsert": "true"},
            data=data,
        )
        if r.status_code in (200, 201):
            url = f"{CDN_BASE}/{filename}"
            print(f"✅  {filename:<30} → {url}")
            uploaded.append(filename)
        else:
            print(f"❌  {filename} : {r.status_code} — {r.text}")

    # ── Résumé ────────────────────────────────────────────────────────────
    print()
    print(f"🏁  {len(uploaded)}/{len(ASSETS)} fichiers uploadés")
    if uploaded:
        print()
        print("   URLs Supabase CDN :")
        for f in uploaded:
            print(f"   {CDN_BASE}/{f}")


if __name__ == "__main__":
    main()
