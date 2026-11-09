"""
Multi-tenancy: every company (organization) only ever sees its own data.

How it works
------------
* Tenant-owned models inherit :class:`TenantScoped`, which adds an
  ``organization_id`` column.
* After authentication, :func:`bind_tenant` stores the user's organization on
  the request's database session (``session.info``).
* A ``do_orm_execute`` hook then adds ``organization_id = <tenant>`` to every
  ORM SELECT, UPDATE and DELETE touching a tenant-owned model, including joins
  and relationship loads.
* A ``before_flush`` hook stamps new rows with the session's organization.

Because the filter is applied centrally, a new query cannot forget it.
Code that must look across tenants (for example, checking that a login email
is globally unique) opts out explicitly with ``unscoped(...)``.
"""

from sqlalchemy import Column, ForeignKey, Integer, event
from sqlalchemy.orm import Session, declared_attr, with_loader_criteria

TENANT_KEY = "organization_id"
SKIP_OPTION = "skip_tenant_filter"


class TenantScoped:
    """Mixin for models owned by an organization."""

    @declared_attr
    def organization_id(cls):  # noqa: N805 - SQLAlchemy declared_attr signature
        return Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)


def bind_tenant(session: Session, organization_id: int) -> None:
    """Scope all further ORM queries on this session to one organization."""
    session.info[TENANT_KEY] = organization_id


def current_tenant(session: Session):
    return session.info.get(TENANT_KEY)


def unscoped(query):
    """Run a query across all organizations (use sparingly)."""
    return query.execution_options(**{SKIP_OPTION: True})


@event.listens_for(Session, "do_orm_execute")
def _apply_tenant_filter(state):
    organization_id = state.session.info.get(TENANT_KEY)
    if organization_id is None or state.execution_options.get(SKIP_OPTION):
        return
    if state.is_select or state.is_update or state.is_delete:
        state.statement = state.statement.options(
            with_loader_criteria(
                TenantScoped,
                lambda cls: cls.organization_id == organization_id,
                include_aliases=True,
            )
        )


@event.listens_for(Session, "before_flush")
def _stamp_new_rows(session, flush_context, instances):
    organization_id = session.info.get(TENANT_KEY)
    for obj in session.new:
        if isinstance(obj, TenantScoped) and getattr(obj, "organization_id", None) is None:
            if organization_id is None:
                raise ValueError(f"Cannot save {type(obj).__name__} without an organization")
            obj.organization_id = organization_id
