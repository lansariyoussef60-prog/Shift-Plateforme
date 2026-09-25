"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-09-10

Hand-written to exactly match app/models/*. Autogeneration was not used because
no live PostgreSQL instance is available in this environment — when you first
connect a real database, run `alembic check` (or diff against `alembic upgrade head`
then `alembic revision --autogenerate`) to confirm there is no drift before adding
further migrations.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Enum types. Each postgresql.ENUM object below issues its own
    # CREATE TYPE the first time it's attached to a table column (via
    # SQLAlchemy's DDL event, not a manual .create() call — calling both
    # raises "type already exists"). Enums reused on a second table
    # (task_priority_enum, contact_method_enum) use a second ENUM object
    # with create_type=False so it's only ever created once.
    # ------------------------------------------------------------------
    role_enum = postgresql.ENUM("ADMIN", "PM", "OCP", "OCVP", "OC", name="role_enum")
    partner_type_enum = postgresql.ENUM(
        "SPONSORING", "FOOD", "DRINKS", "FINANCIAL", "MEDIA", "STRATEGIC", "EVENT", "SPEAKER", "OTHER",
        name="partner_type_enum",
    )
    partner_status_enum = postgresql.ENUM(
        "NEW", "CONTACTED", "FOLLOW_UP", "NEGOTIATION", "SIGNED", "REJECTED", "NOT_INTERESTED",
        name="partner_status_enum",
    )
    target_list_item_status_enum = postgresql.ENUM(
        "PROSPECT", "CONTACTED", "RESPONDED", "FOLLOW_UP", "NEGOTIATION", "SIGNED", "REJECTED", "NOT_INTERESTED",
        name="target_list_item_status_enum",
    )
    contact_method_enum = postgresql.ENUM("EMAIL", "CALL", "MEETING", "SOCIAL", "OTHER", name="contact_method_enum")
    speaker_status_enum = postgresql.ENUM(
        "PROSPECT", "CONTACTED", "INTERESTED", "CONFIRMED", "DECLINED", "FOLLOW_UP", name="speaker_status_enum"
    )
    task_status_enum = postgresql.ENUM(
        "TODO", "IN_PROGRESS", "COMPLETED", "OVERDUE", "CANCELLED", name="task_status_enum"
    )
    task_priority_enum = postgresql.ENUM("LOW", "MEDIUM", "HIGH", "URGENT", name="task_priority_enum")
    goal_scope_enum = postgresql.ENUM("PROJECT", "DEPARTMENT", "INDIVIDUAL", name="goal_scope_enum")
    goal_status_enum = postgresql.ENUM("ON_TRACK", "AT_RISK", "ACHIEVED", "MISSED", name="goal_status_enum")
    mkt_status_enum = postgresql.ENUM("PLANNED", "IN_PROGRESS", "DONE", "DELAYED", name="mkt_status_enum")
    import_batch_status_enum = postgresql.ENUM(
        "PENDING", "VALIDATED", "COMMITTED", "FAILED", name="import_batch_status_enum"
    )
    import_row_status_enum = postgresql.ENUM("NEW", "DUPLICATE", "ERROR", name="import_row_status_enum")

    # Reused types must not attempt to CREATE TYPE a second time.
    task_priority_enum_reuse = postgresql.ENUM(
        "LOW", "MEDIUM", "HIGH", "URGENT", name="task_priority_enum", create_type=False
    )
    contact_method_enum_reuse = postgresql.ENUM(
        "EMAIL", "CALL", "MEETING", "SOCIAL", "OTHER", name="contact_method_enum", create_type=False
    )

    # ------------------------------------------------------------------
    # Tables, in FK dependency order
    # ------------------------------------------------------------------

    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "departments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("project_id", "name", name="uq_department_project_name"),
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", role_enum, nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("manager_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_department_id", "users", ["department_id"])
    op.create_index("ix_users_manager_id", "users", ["manager_id"])

    op.create_table(
        "partners",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("normalized_name", sa.String(255), nullable=False, unique=True),
        sa.Column("industry", sa.String(150), nullable=True),
        sa.Column("contact_person", sa.String(150), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("address", sa.String(255), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("website", sa.String(255), nullable=True),
        sa.Column("social_media", sa.Text(), nullable=True),
        sa.Column("partner_type", partner_type_enum, nullable=False, server_default="OTHER"),
        sa.Column("status", partner_status_enum, nullable=False, server_default="NEW"),
        sa.Column("last_contact_date", sa.Date(), nullable=True),
        sa.Column("last_contacted_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_partners_normalized_name", "partners", ["normalized_name"])

    op.create_table(
        "partner_contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("partners.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="SET NULL"), nullable=True),
        sa.Column("contact_method", contact_method_enum, nullable=False),
        sa.Column("result", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("follow_up_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_partner_contacts_partner_id", "partner_contacts", ["partner_id"])

    op.create_table(
        "partner_collaborations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("partners.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("amount_value", sa.Numeric(12, 2), nullable=True),
        sa.Column("currency", sa.String(10), nullable=True, server_default="TND"),
        sa.Column("confirmed_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_partner_collaborations_partner_id", "partner_collaborations", ["partner_id"])

    op.create_table(
        "target_lists",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_target_lists_owner_id", "target_lists", ["owner_id"])

    op.create_table(
        "target_list_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("target_list_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("target_lists.id", ondelete="CASCADE"), nullable=False),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("partners.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", target_list_item_status_enum, nullable=False, server_default="PROSPECT"),
        sa.Column("added_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("target_list_id", "partner_id", name="uq_target_list_partner"),
    )
    op.create_index("ix_target_list_items_partner_id", "target_list_items", ["partner_id"])

    op.create_table(
        "speakers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("normalized_name", sa.String(150), nullable=False, unique=True),
        sa.Column("organization", sa.String(150), nullable=True),
        sa.Column("position", sa.String(150), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("linkedin", sa.String(255), nullable=True),
        sa.Column("topic", sa.String(255), nullable=True),
        sa.Column("status", speaker_status_enum, nullable=False, server_default="PROSPECT"),
        sa.Column("contacted_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("contact_date", sa.Date(), nullable=True),
        sa.Column("confirmation_status", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_speakers_normalized_name", "speakers", ["normalized_name"])

    op.create_table(
        "speaker_contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("speaker_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("speakers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("contact_method", contact_method_enum_reuse, nullable=False),
        sa.Column("result", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_speaker_contacts_speaker_id", "speaker_contacts", ["speaker_id"])

    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("assigned_to_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("priority", task_priority_enum, nullable=False, server_default="MEDIUM"),
        sa.Column("status", task_status_enum, nullable=False, server_default="TODO"),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_tasks_assigned_to_id", "tasks", ["assigned_to_id"])

    op.create_table(
        "goals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("target_value", sa.Numeric(12, 2), nullable=False),
        sa.Column("current_value", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("unit", sa.String(50), nullable=True),
        sa.Column("scope", goal_scope_enum, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("responsible_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column("status", goal_status_enum, nullable=False, server_default="ON_TRACK"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "mkt_timeline_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("responsible_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", mkt_status_enum, nullable=False, server_default="PLANNED"),
        sa.Column("priority", task_priority_enum_reuse, nullable=False, server_default="MEDIUM"),
        sa.Column("related_task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(100), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("related_entity_type", sa.String(100), nullable=True),
        sa.Column("related_entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])

    op.create_table(
        "activity_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_activity_logs_actor_id", "activity_logs", ["actor_id"])

    op.create_table(
        "import_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("uploaded_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("status", import_batch_status_enum, nullable=False, server_default="PENDING"),
        sa.Column("total_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("new_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duplicate_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "import_rows",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("import_batch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("import_batches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("raw_data", postgresql.JSONB(), nullable=False),
        sa.Column("row_status", import_row_status_enum, nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("resolved_partner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("partners.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_import_rows_batch_id", "import_rows", ["import_batch_id"])


def downgrade() -> None:
    op.drop_table("import_rows")
    op.drop_table("import_batches")
    op.drop_table("activity_logs")
    op.drop_table("notifications")
    op.drop_table("mkt_timeline_items")
    op.drop_table("goals")
    op.drop_table("tasks")
    op.drop_table("speaker_contacts")
    op.drop_table("speakers")
    op.drop_table("target_list_items")
    op.drop_table("target_lists")
    op.drop_table("partner_collaborations")
    op.drop_table("partner_contacts")
    op.drop_table("partners")
    op.drop_table("users")
    op.drop_table("departments")
    op.drop_table("projects")

    bind = op.get_bind()
    for enum_name in (
        "import_row_status_enum", "import_batch_status_enum", "mkt_status_enum", "goal_status_enum",
        "goal_scope_enum", "task_priority_enum", "task_status_enum", "speaker_status_enum",
        "contact_method_enum", "target_list_item_status_enum", "partner_status_enum",
        "partner_type_enum", "role_enum",
    ):
        postgresql.ENUM(name=enum_name).drop(bind, checkfirst=True)
