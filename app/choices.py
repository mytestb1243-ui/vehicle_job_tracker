"""
Central place for every dropdown / checkbox list used across the app.
Keeping these in one module means the input form, the search filters and
the Excel export always stay in sync.
"""

# ---------------------------------------------------------------------------
# Column order — this is the exact order requested for the input form,
# the search results table and the Excel export. Do not add columns that
# are not in this list.
# ---------------------------------------------------------------------------
COLUMN_ORDER = [
    "Vehicle No.",
    "Device ID",
    "Company Name",
    "Date",
    "Location",
    "Before Images",
    "After Images",
    "Service Form",
    "PO Number",
    "Device type",
    "Service Type",
    "Tempering",
    "Tempering Evidence",
    "Service checklist",
    "Notes",
]

# ---------------------------------------------------------------------------
# Company Name
# ---------------------------------------------------------------------------
COMPANY_NAME_OPTIONS = [
    "Unilever Trucks",
    "Unilever Pool Cars",
    "UPFL Pool Cars",
    "Magnum Primary",
    "Magnum Secondary",
    "Wall's Pool Cars",
    "Emirates Logistics",
    "Allied Logistics",
    "KKC Pvt Ltd",
    "Nestle Dedicated",
    "Nestle NON Dedicated",
    "Go Petroleum",
    "DHL Global",
    "Shaheen Fright",
    "Engro Polymer",
    "DHL PAK",
]

# ---------------------------------------------------------------------------
# Device type
# ---------------------------------------------------------------------------
DEVICE_TYPE_OPTIONS = [
    "CNo1-KG",
    "CN01-KGP",
    "CN02-QN",
    "8204",
    "SP5D",
    "SP5IP",
]

# ---------------------------------------------------------------------------
# Service Type — hierarchy: New Installation / Servicing / Inspection, and
# Inspection itself branches into Tempering / Redo.
# ---------------------------------------------------------------------------
SERVICE_TYPE_TOP_OPTIONS = ["New Installation", "Re-Installation", "Servicing", "Inspection", "Uninstallation"]
SERVICE_TYPE_INSPECTION_SUBOPTIONS = ["Tempering", "Redo"]

# Full flattened list of valid stored values for Service Type.
SERVICE_TYPE_OPTIONS = ["New Installation", "Re-Installation", "Servicing", "Uninstallation"] + [
    f"Inspection - {sub}" for sub in SERVICE_TYPE_INSPECTION_SUBOPTIONS
]

# ---------------------------------------------------------------------------
# Tempering (evidence type found during inspection) — multi-select.
# Stored as a comma-separated string on the job record.
# ---------------------------------------------------------------------------
TEMPERING_OPTIONS = [
    "Water Damage",
    "DSM Cam",
    "ADAS",
    "GPS",
    "Rear View Camera",
    "Sim",
    "SD Card",
    "Main Wiring",
    "Back Camera Wiring",
]

# ---------------------------------------------------------------------------
# Service checklist — multi-select, stored as individual boolean columns.
# (field_name, label) in exact spreadsheet order.
# ---------------------------------------------------------------------------
CHECKLIST_FIELDS = [
    ("verify_camera_angles", "Verify Camera Angles"),
    ("memory_card", "Memory Card"),
    ("sim", "Sim"),
    ("network_connection", "Network Connection"),
    ("gps_connection", "GPS Connection"),
    ("wire_piping", "Wire Piping"),
    ("dsm_wire_check", "DSM Wire Check"),
    ("power_wire_check", "Power Wire Check"),
    ("configuration", "Configuration"),
    ("replace_dsm", "Replace DSM"),
    ("replace_device", "Replace Device"),
    ("change_sim", "Change Sim"),
    ("check_back_camera", "Check Back Camera"),
    ("replace_back_camera", "Replace Back Camera"),
    ("temperature_sensor", "Temperature Sensor"),
    ("probe", "Probe"),
    ("seal_all_connections", "Seal All Connections"),
]

# ---------------------------------------------------------------------------
# Roles — see user_roles.txt
# ---------------------------------------------------------------------------
ROLE_SUPER_ADMIN = "super_admin"
ROLE_ADMIN = "admin"
ROLE_USER = "user"
ROLE_FIELD_SUPPORT = "field_support"
ROLE_VIEWER = "viewer"

ROLE_LABELS = {
    ROLE_SUPER_ADMIN: "Super Admin",
    ROLE_ADMIN: "Admin",
    ROLE_USER: "User",
    ROLE_FIELD_SUPPORT: "Field Support",
    ROLE_VIEWER: "Viewer",
}

ALL_ROLES = [ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_USER, ROLE_FIELD_SUPPORT, ROLE_VIEWER]

# Roles that can see the Admin Panel and manage records/users freely.
ADMIN_LEVEL_ROLES = {ROLE_SUPER_ADMIN, ROLE_ADMIN}

# Roles allowed to delete job records (Admin-level roles + Field Support).
CAN_DELETE_JOB_ROLES = ADMIN_LEVEL_ROLES | {ROLE_FIELD_SUPPORT}
