"""
Demo Data Seeding Script for Procurement Intelligence Platform.
Seeds initial organization, administrative users, suppliers, delivery/quality records,
and sample purchase requests into PostgreSQL databases.
"""
import os
import sys
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
import bcrypt
from sqlalchemy import create_engine, text

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEMO_ORG_ID = "00000000-0000-0000-0000-000000000001"
DEMO_OFFICER_ID = "00000000-0000-0000-0000-000000000002"
DEMO_MANAGER_ID = "00000000-0000-0000-0000-000000000003"

ROLE_OFFICER_ID = "00000000-0000-0000-0000-000000000011"
ROLE_MANAGER_ID = "00000000-0000-0000-0000-000000000012"

SUPPLIER_1_ID = "11111111-1111-1111-1111-111111110001"
SUPPLIER_2_ID = "11111111-1111-1111-1111-111111110002"
SUPPLIER_3_ID = "11111111-1111-1111-1111-111111110003"

PR_1_ID = "22222222-2222-2222-2222-222222220001"


def hash_pw(plain: str) -> str:
    pwd_bytes = plain.encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def seed_demo_data():
    print("==================================================================")
    print("  Ceylon Industrial Manufacturing — Demo Data Seeding Script     ")
    print("==================================================================")
    print(f"Target Organization: Ceylon Industrial Manufacturing Ltd (ID: {DEMO_ORG_ID})")
    print("")
    print("Authorized Demonstration Accounts:")
    print("  1. Procurement Officer: officer@ceylonindustrial.lk / Officer@12345")
    print("     Roles: [PROCUREMENT_OFFICER]")
    print("  2. Procurement Manager: manager@ceylonindustrial.lk / Manager@12345")
    print("     Roles: [PROCUREMENT_OFFICER, MANAGER]")
    print("")

    postgres_host = os.environ.get("POSTGRES_HOST", "localhost")
    postgres_port = os.environ.get("POSTGRES_PORT", "5432")
    user = os.environ.get("POSTGRES_USER", "postgres")
    pwd = os.environ.get("POSTGRES_PASSWORD", "postgres")

    print(f"Connecting to database host: {postgres_host}:{postgres_port}...")

    # 1. Seed Identity Service Database
    try:
        id_db_url = f"postgresql+psycopg2://{user}:{pwd}@{postgres_host}:{postgres_port}/identity_db"
        engine = create_engine(id_db_url, connect_args={"connect_timeout": 3})
        with engine.begin() as conn:
            # Check if tables exist
            conn.execute(text("SELECT 1 FROM organizations LIMIT 1;"))
            
            # Organization
            conn.execute(text("""
                INSERT INTO organizations (id, name, registration_number, industry, is_active, created_at, updated_at)
                VALUES (:id, :name, :reg, :ind, true, NOW(), NOW())
                ON CONFLICT (id) DO NOTHING;
            """), {
                "id": DEMO_ORG_ID,
                "name": "Ceylon Industrial Manufacturing Ltd",
                "reg": "PV-102934",
                "ind": "Industrial Manufacturing"
            })

            # Roles
            conn.execute(text("""
                INSERT INTO roles (id, name, description)
                VALUES (:id, :name, :desc)
                ON CONFLICT (name) DO NOTHING;
            """), {"id": ROLE_OFFICER_ID, "name": "PROCUREMENT_OFFICER", "desc": "Procurement Officer"})
            
            conn.execute(text("""
                INSERT INTO roles (id, name, description)
                VALUES (:id, :name, :desc)
                ON CONFLICT (name) DO NOTHING;
            """), {"id": ROLE_MANAGER_ID, "name": "MANAGER", "desc": "Procurement Manager"})

            # Users
            pw_officer = hash_pw("Officer@12345")
            pw_manager = hash_pw("Manager@12345")

            conn.execute(text("""
                INSERT INTO users (id, email, hashed_password, full_name, organization_id, is_active, is_verified, created_at, updated_at)
                VALUES (:id, :email, :pw, :name, :org_id, true, true, NOW(), NOW())
                ON CONFLICT (email) DO UPDATE SET hashed_password = EXCLUDED.hashed_password;
            """), {
                "id": DEMO_OFFICER_ID,
                "email": "officer@ceylonindustrial.lk",
                "pw": pw_officer,
                "name": "Kamal Perera",
                "org_id": DEMO_ORG_ID
            })

            conn.execute(text("""
                INSERT INTO users (id, email, hashed_password, full_name, organization_id, is_active, is_verified, created_at, updated_at)
                VALUES (:id, :email, :pw, :name, :org_id, true, true, NOW(), NOW())
                ON CONFLICT (email) DO UPDATE SET hashed_password = EXCLUDED.hashed_password;
            """), {
                "id": DEMO_MANAGER_ID,
                "email": "manager@ceylonindustrial.lk",
                "pw": pw_manager,
                "name": "Anura Silva",
                "org_id": DEMO_ORG_ID
            })

            # Map user roles
            conn.execute(text("""
                INSERT INTO user_roles (user_id, role_id)
                VALUES (:user_id, :role_id)
                ON CONFLICT DO NOTHING;
            """), {"user_id": DEMO_OFFICER_ID, "role_id": ROLE_OFFICER_ID})

            conn.execute(text("""
                INSERT INTO user_roles (user_id, role_id)
                VALUES (:user_id, :role_id)
                ON CONFLICT DO NOTHING;
            """), {"user_id": DEMO_MANAGER_ID, "role_id": ROLE_OFFICER_ID})

            conn.execute(text("""
                INSERT INTO user_roles (user_id, role_id)
                VALUES (:user_id, :role_id)
                ON CONFLICT DO NOTHING;
            """), {"user_id": DEMO_MANAGER_ID, "role_id": ROLE_MANAGER_ID})

            print("✓ Identity Database seeded: Organization, Roles, Users (Kamal & Anura)")
    except Exception as exc:
        print(f"ℹ Identity DB seeding notice: {exc}")

    # 2. Seed Supplier Service Database
    try:
        supp_db_url = f"postgresql+psycopg2://{user}:{pwd}@{postgres_host}:{postgres_port}/supplier_db"
        engine_supp = create_engine(supp_db_url, connect_args={"connect_timeout": 3})
        with engine_supp.begin() as conn:
            conn.execute(text("SELECT 1 FROM suppliers LIMIT 1;"))

            suppliers_data = [
                (SUPPLIER_1_ID, "Lanka Steel Fabricators PLC", "info@lankasteel.lk", "+94 11 2345678", "Raw Materials", 4.8, "TIER_1", "Colombo"),
                (SUPPLIER_2_ID, "Colombo Tool Works Ltd", "sales@colombotool.lk", "+94 11 8765432", "Tooling & Hardware", 4.2, "TIER_2", "Kelaniya"),
                (SUPPLIER_3_ID, "Apex Precision Components", "support@apexprecision.lk", "+94 33 2211445", "Components", 3.5, "TIER_3", "Gampaha"),
            ]
            for sid, sname, semail, sphone, scat, srating, stier, scity in suppliers_data:
                conn.execute(text("""
                    INSERT INTO suppliers (id, organization_id, company_name, contact_email, contact_phone, category, rating, tier, city, country, compliance_status, is_active, created_at, updated_at)
                    VALUES (:id, :org_id, :name, :email, :phone, :cat, :rating, :tier, :city, 'Sri Lanka', 'VERIFIED', true, NOW(), NOW())
                    ON CONFLICT (id) DO NOTHING;
                """), {
                    "id": sid, "org_id": DEMO_ORG_ID, "name": sname, "email": semail, "phone": sphone,
                    "cat": scat, "rating": srating, "tier": stier, "city": scity
                })

            # Historical delivery records for Supplier 1 (Reliable)
            now = datetime.now(timezone.utc)
            for i in range(1, 5):
                conn.execute(text("""
                    INSERT INTO supplier_delivery_records (id, organization_id, supplier_id, po_reference, promised_delivery_date, actual_delivery_date, on_time, delay_days, source_system, recorded_by, created_at)
                    VALUES (:id, :org_id, :supp_id, :po, :p_date, :a_date, :on_time, :delay, 'ERP_EXPORT', :rec_by, NOW())
                    ON CONFLICT (id) DO NOTHING;
                """), {
                    "id": str(uuid.uuid4()), "org_id": DEMO_ORG_ID, "supp_id": SUPPLIER_1_ID,
                    "po": f"PO-2025-0{i}",
                    "p_date": now - timedelta(days=90 - i * 20),
                    "a_date": now - timedelta(days=90 - i * 20) if i != 2 else now - timedelta(days=88 - i * 20),
                    "on_time": i != 2,
                    "delay": 0 if i != 2 else 2,
                    "rec_by": DEMO_OFFICER_ID
                })

            # Historical quality records for Supplier 1
            for i in range(1, 5):
                conn.execute(text("""
                    INSERT INTO supplier_quality_records (id, organization_id, supplier_id, batch_reference, defect_rate, incident_severity, passed, source_system, recorded_by, created_at)
                    VALUES (:id, :org_id, :supp_id, :batch, :rate, 'NONE', true, 'QA_LAB_LOG', :rec_by, NOW())
                    ON CONFLICT (id) DO NOTHING;
                """), {
                    "id": str(uuid.uuid4()), "org_id": DEMO_ORG_ID, "supp_id": SUPPLIER_1_ID,
                    "batch": f"BATCH-ST-0{i}",
                    "rate": 0.012,
                    "rec_by": DEMO_OFFICER_ID
                })

            print("✓ Supplier Database seeded: Suppliers (Lanka Steel, Colombo Tool, Apex Precision) & History")
    except Exception as exc:
        print(f"ℹ Supplier DB seeding notice: {exc}")

    # 3. Seed Procurement Service Database
    try:
        proc_db_url = f"postgresql+psycopg2://{user}:{pwd}@{postgres_host}:{postgres_port}/procurement_db"
        engine_proc = create_engine(proc_db_url, connect_args={"connect_timeout": 3})
        with engine_proc.begin() as conn:
            conn.execute(text("SELECT 1 FROM purchase_requests LIMIT 1;"))

            conn.execute(text("""
                INSERT INTO purchase_requests (id, organization_id, created_by_user_id, request_number, title, description, category, priority, budget_limit, currency, status, created_at, updated_at)
                VALUES (:id, :org_id, :user_id, :req_num, :title, :desc, :cat, 'HIGH', 5500000.0, 'LKR', 'UNDER_EVALUATION', NOW(), NOW())
                ON CONFLICT (id) DO NOTHING;
            """), {
                "id": PR_1_ID, "org_id": DEMO_ORG_ID, "user_id": DEMO_OFFICER_ID,
                "req_num": "PR-2026-001",
                "title": "Industrial Steel Sheets Grade A-36 (Q1 Batch)",
                "desc": "Procurement of 120 tons of structural steel sheets for the Colombo central manufacturing line.",
                "cat": "Raw Materials"
            })

            conn.execute(text("""
                INSERT INTO purchase_request_items (id, organization_id, purchase_request_id, item_name, specification, quantity, unit_of_measure, target_unit_price, created_at)
                VALUES (:id, :org_id, :pr_id, :item, :spec, :qty, 'TONS', :price, NOW())
                ON CONFLICT (id) DO NOTHING;
            """), {
                "id": str(uuid.uuid4()), "org_id": DEMO_ORG_ID, "pr_id": PR_1_ID,
                "item": "Cold Rolled Steel Sheet 2.0mm",
                "spec": "Grade A-36 structural standard, JIS G3101",
                "qty": 80.0,
                "price": 40000.0
            })

            conn.execute(text("""
                INSERT INTO purchase_request_items (id, organization_id, purchase_request_id, item_name, specification, quantity, unit_of_measure, target_unit_price, created_at)
                VALUES (:id, :org_id, :pr_id, :item, :spec, :qty, 'TONS', :price, NOW())
                ON CONFLICT (id) DO NOTHING;
            """), {
                "id": str(uuid.uuid4()), "org_id": DEMO_ORG_ID, "pr_id": PR_1_ID,
                "item": "Galvanized High-Tensile Strip Coil 1.5mm",
                "spec": "Hot dip zinc coated, 275g/m2 coating weight",
                "qty": 40.0,
                "price": 57500.0
            })

            print("✓ Procurement Database seeded: PR-2026-001 with Line Items")
    except Exception as exc:
        print(f"ℹ Procurement DB seeding notice: {exc}")

    print("")
    print("==================================================================")
    print("  Seed completed. Ready for evaluation and demonstration!         ")
    print("==================================================================")


if __name__ == "__main__":
    seed_demo_data()
