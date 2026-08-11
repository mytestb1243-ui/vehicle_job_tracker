import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Date,
    Boolean,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.choices import (
    CHECKLIST_FIELDS,
    ROLE_USER,
    ROLE_SUPER_ADMIN,
    ADMIN_LEVEL_ROLES,
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, index=True, nullable=False)
    full_name = Column(String(150), nullable=False, default="")
    password_hash = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False, default=ROLE_USER)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    jobs_created = relationship("Job", back_populates="creator")

    @property
    def is_admin_level(self) -> bool:
        """Super Admin & Admin: full access, incl. Admin Panel."""
        return self.role in ADMIN_LEVEL_ROLES

    # kept for backwards-compatible template usage
    @property
    def is_admin(self) -> bool:
        return self.is_admin_level

    @property
    def is_super_admin(self) -> bool:
        return self.role == ROLE_SUPER_ADMIN


# ---------------------------------------------------------------------------
# Job — one inspection / service record. Column order matches
# column_information.txt exactly:
#   Vehicle No. / Device ID / Company Name / Date / Location /
#   Before Images / After Images / Service Form / PO Number / Device type /
#   Service Type / Tempering / Tempering Evidence / Service checklist / Notes
# ---------------------------------------------------------------------------
class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)

    vehicle_no = Column(String(60), nullable=False, index=True)
    device_id = Column(String(60), nullable=True, index=True)
    company_name = Column(String(120), nullable=True)
    job_date = Column(Date, nullable=False, index=True)
    location = Column(String(200), nullable=False)
    before_images = Column(Text, nullable=True)   # OneDrive folder/file link
    after_images = Column(Text, nullable=True)    # OneDrive folder/file link
    service_form = Column(Text, nullable=True)    # OneDrive folder link
    po_number = Column(String(120), nullable=True)
    device_type = Column(String(60), nullable=True)
    service_type = Column(String(60), nullable=True)
    tempering = Column(String(300), nullable=True)          # comma separated
    tempering_evidence = Column(Text, nullable=True)        # folder link

    # --- Service checklist checkboxes, spreadsheet order ---
    verify_camera_angles = Column(Boolean, nullable=False, default=False)
    memory_card = Column(Boolean, nullable=False, default=False)
    sim = Column(Boolean, nullable=False, default=False)
    network_connection = Column(Boolean, nullable=False, default=False)
    gps_connection = Column(Boolean, nullable=False, default=False)
    wire_piping = Column(Boolean, nullable=False, default=False)
    dsm_wire_check = Column(Boolean, nullable=False, default=False)
    power_wire_check = Column(Boolean, nullable=False, default=False)
    configuration = Column(Boolean, nullable=False, default=False)
    replace_dsm = Column(Boolean, nullable=False, default=False)
    replace_device = Column(Boolean, nullable=False, default=False)
    change_sim = Column(Boolean, nullable=False, default=False)
    check_back_camera = Column(Boolean, nullable=False, default=False)
    replace_back_camera = Column(Boolean, nullable=False, default=False)
    seal_all_connections = Column(Boolean, nullable=False, default=False)

    notes = Column(Text, nullable=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    creator = relationship("User", back_populates="jobs_created")

    @property
    def checklist_done_count(self) -> int:
        return sum(1 for name, _label in CHECKLIST_FIELDS if getattr(self, name))
