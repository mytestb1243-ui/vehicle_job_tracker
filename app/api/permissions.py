"""
What an external API client is allowed to do with user accounts.

API keys are held by another team's systems, so they deliberately can't
create or manage administrators — that stays in the Admin Panel, where a
human Super Admin / Admin is logged in.
"""
from app.choices import ROLE_FIELD_SUPPORT, ROLE_USER, ROLE_VIEWER

API_ASSIGNABLE_ROLES = [ROLE_USER, ROLE_FIELD_SUPPORT, ROLE_VIEWER]
