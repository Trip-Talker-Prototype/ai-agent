from sqlalchemy import Column, String, DateTime, func

def get_audit_columns():
    """
    Returns a list of audit columns for use in table definitions.
    """
    return [
        Column("created_by", String, nullable=False),
        Column("updated_by", String, nullable=True),
        Column("deleted_by", String, nullable=True),
        Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
        Column("updated_at", DateTime(timezone=True), nullable=True),
        Column("deleted_at", DateTime(timezone=True), nullable=True),
    ]