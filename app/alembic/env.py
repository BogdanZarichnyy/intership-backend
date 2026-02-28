import asyncio
import os
import re
import uuid

from logging.config import fileConfig
# from sqlalchemy import pool, Column, String, DateTime, Boolean, text
from sqlalchemy import pool, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy.dialects.postgresql import UUID
from alembic import context
# from alembic.autogenerate import renderers

from app.config import settings
from app.db.postgres import Base
from app.models.user import User
from app.models.company import Company
from app.models.company_member import CompanyMember
from app.models.company_invitation import CompanyInvitation
from app.models.quiz import Quiz, QuizAnswerOption, QuizQuestion
from app.models.quiz_result import QuizResult

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
  fileConfig(config.config_file_name)

target_metadata = Base.metadata

# --- Auto-increment revision id ---
def get_next_revision_id() -> str:
  versions_dir = os.path.join(os.path.dirname(__file__), "versions")
  if not os.path.exists(versions_dir):
    return "0001"
  revisions = [
    int(re.match(r"^(\d{4})_", f).group(1))
    for f in os.listdir(versions_dir)
    if re.match(r"^(\d{4})_", f)
  ]
  next_rev = max(revisions, default=0) + 1
  return f"{next_rev:04d}"

def process_revision_directives(context, revision, directives):
  if getattr(config.cmd_opts, "autogenerate", False):
    script = directives[0]
    script.rev_id = get_next_revision_id()

# @renderers.dispatch_for(Column, replace=True) #--- UUID renderer for Alembic ---
# def render_column(autogen_context, sa_column, autogen_kw):
#     rendered = autogen_context.impl.render_column(
#       autogen_context, sa_column, autogen_kw
#     )
#     if isinstance(sa_column.type, UUID):
#       rendered = rendered.replace("sa.UUID()", "sa.UUID(as_uuid=True)")
#       if sa_column.default is not None:
#         # додати default uuid.uuid4() у рядку створення колонки
#         rendered = rendered.replace(
#           f"{sa_column.name}", 
#           f"{sa_column.name}, default=uuid.uuid4"
#         )
#     return rendered

# @renderers.dispatch_for(UUID) # у моделях обов'язково прописуємо default=uuid.uuid4
# def render_uuid(type_, autogen_context):
#   return "sa.UUID(as_uuid=True)"

# --- Offline migrations ---
def run_migrations_offline():
  context.configure(
    url=settings.database_url,
    target_metadata=target_metadata,
    literal_binds=True,
    dialect_opts={"paramstyle": "named"},
    process_revision_directives=process_revision_directives,
    compare_type=True,
  )
  with context.begin_transaction():
    context.run_migrations()

# --- Online migrations ---
def do_run_migrations(connection: Connection):
  context.configure(
    connection=connection,
    target_metadata=target_metadata,
    compare_type=True,
    render_as_batch=True,
    process_revision_directives=process_revision_directives,
  )
  with context.begin_transaction():
    context.run_migrations()

async def run_migrations_online():
  connectable = async_engine_from_config(
    config.get_section(config.config_ini_section),
    prefix="sqlalchemy.",
    poolclass=pool.NullPool,
  )
  async with connectable.connect() as connection:
    await connection.run_sync(do_run_migrations)
  await connectable.dispose()

if context.is_offline_mode():
  run_migrations_offline()
else:
  asyncio.run(run_migrations_online())
