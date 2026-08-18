-- ============================================================================
-- Vehicle Job Tracker — Database Schema (PostgreSQL)
-- Matches app/models.py exactly. Generated for reference / manual setup.
-- Normally you never need to run this by hand — `python scripts/init_db.py`
-- creates these tables automatically from the SQLAlchemy models. Use this
-- file only if you want to inspect the schema, set it up on a server without
-- running Python first, or recreate it manually.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Table: users
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    username        VARCHAR(80)  NOT NULL,
    full_name       VARCHAR(150) NOT NULL DEFAULT '',
    password_hash   VARCHAR(255) NOT NULL,
    role            VARCHAR(30)  NOT NULL DEFAULT 'user',   -- super_admin | admin | user | field_support
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_users_username UNIQUE (username)
);

CREATE INDEX IF NOT EXISTS ix_users_username ON users (username);


-- ----------------------------------------------------------------------------
-- Table: jobs
-- Column order matches column_information.txt:
--   Vehicle No. / Device ID / Company Name / Date / Location /
--   Before Images / After Images / Service Form / PO Number / Device type /
--   Service Type / Tempering / Tempering Evidence / Service checklist / Notes
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS jobs (
    id                      SERIAL PRIMARY KEY,

    vehicle_no              VARCHAR(60)  NOT NULL,
    device_id               VARCHAR(60),
    company_name            VARCHAR(120),
    job_date                DATE         NOT NULL,
    location                VARCHAR(200) NOT NULL,
    before_images           TEXT,                     -- OneDrive folder/file link
    after_images            TEXT,                     -- OneDrive folder/file link
    service_form            TEXT,                     -- OneDrive folder link
    po_number                VARCHAR(120),
    device_type             VARCHAR(60),
    service_type            VARCHAR(60),               -- e.g. "Inspection - Tempering"
    tempering                VARCHAR(300),              -- comma-separated evidence types
    tempering_evidence       TEXT,                     -- OneDrive folder link

    -- ---- Service checklist (15 items, spreadsheet order) ----
    verify_camera_angles    BOOLEAN NOT NULL DEFAULT FALSE,
    memory_card              BOOLEAN NOT NULL DEFAULT FALSE,
    sim                      BOOLEAN NOT NULL DEFAULT FALSE,
    network_connection       BOOLEAN NOT NULL DEFAULT FALSE,
    gps_connection            BOOLEAN NOT NULL DEFAULT FALSE,
    wire_piping               BOOLEAN NOT NULL DEFAULT FALSE,
    dsm_wire_check            BOOLEAN NOT NULL DEFAULT FALSE,
    power_wire_check          BOOLEAN NOT NULL DEFAULT FALSE,
    configuration             BOOLEAN NOT NULL DEFAULT FALSE,
    replace_dsm               BOOLEAN NOT NULL DEFAULT FALSE,
    replace_device            BOOLEAN NOT NULL DEFAULT FALSE,
    change_sim                BOOLEAN NOT NULL DEFAULT FALSE,
    check_back_camera         BOOLEAN NOT NULL DEFAULT FALSE,
    replace_back_camera       BOOLEAN NOT NULL DEFAULT FALSE,
    temperature_sensor        BOOLEAN NOT NULL DEFAULT FALSE,
    probe                     BOOLEAN NOT NULL DEFAULT FALSE,
    seal_all_connections      BOOLEAN NOT NULL DEFAULT FALSE,

    notes                    TEXT,

    created_by               INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at                TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at                TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_jobs_vehicle_no ON jobs (vehicle_no);
CREATE INDEX IF NOT EXISTS ix_jobs_device_id  ON jobs (device_id);
CREATE INDEX IF NOT EXISTS ix_jobs_job_date   ON jobs (job_date);


-- ----------------------------------------------------------------------------
-- Optional: auto-update `updated_at` on every row change
-- (the Python app already does this via SQLAlchemy's onupdate, so this
-- trigger is only needed if you plan to update rows directly in SQL too)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_jobs_updated_at ON jobs;
CREATE TRIGGER trg_jobs_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();


-- ----------------------------------------------------------------------------
-- Reference only — valid values for `role` and `service_type`.
-- Not enforced as DB-level CHECK constraints so the app's dropdown lists
-- (app/choices.py) remain the single source of truth and can be edited
-- without a migration.
-- ----------------------------------------------------------------------------
-- role:          super_admin | admin | user | field_support
-- service_type:  New Installation | Servicing | Inspection - Tempering | Inspection - Rede
-- device_type:   CNo1-KG | CN01-KGP | CN02-QN | 8204 | SP5D | SP5IP
