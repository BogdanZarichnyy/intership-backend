from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="unknown")
current_user_id_var: ContextVar[str | None] = ContextVar("current_user_id", default=None)
