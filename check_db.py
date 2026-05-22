import sqlite3
import os

conn = sqlite3.connect('backend/auth.db')
cur = conn.cursor()

print("=== Columns in auth_users ===")
cur.execute("PRAGMA table_info(auth_users)")
for c in cur.fetchall():
    print(f"  {c[1]:30s} {c[2]}")

print("\n=== Driver rows ===")
cur.execute("SELECT username, role, license_number, or_renewal_date, cr_plate_number, face_image_b64_db, license_image_b64_db, or_image_b64_db, cr_image_b64_db FROM auth_users WHERE role='driver' LIMIT 5")
rows = cur.fetchall()
if not rows:
    print("  No driver rows found.")
for r in rows:
    print(f"  user={r[0]}, role={r[1]}")
    print(f"    license_number  = {r[2]}")
    print(f"    or_renewal_date = {r[3]}")
    print(f"    cr_plate_number = {r[4]}")
    print(f"    face_image_b64  = {bool(r[5])} (len={len(r[5]) if r[5] else 0})")
    print(f"    license_image_b64 = {bool(r[6])} (len={len(r[6]) if r[6] else 0})")
    print(f"    or_image_b64      = {bool(r[7])} (len={len(r[7]) if r[7] else 0})")
    print(f"    cr_image_b64      = {bool(r[8])} (len={len(r[8]) if r[8] else 0})")

print("\n=== driver_docs/ folder contents ===")
driver_docs = os.path.join("backend", "driver_docs")
if os.path.exists(driver_docs):
    files = os.listdir(driver_docs)
    for f in files[:10]:
        size = os.path.getsize(os.path.join(driver_docs, f))
        print(f"  {f}  ({size} bytes)")
else:
    print("  (folder not found)")

conn.close()
print("\n[OK] Done.")
