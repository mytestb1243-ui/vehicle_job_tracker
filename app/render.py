from fastapi.templating import Jinja2Templates
from markupsafe import Markup, escape

from app.config import settings
from app.choices import ROLE_LABELS

templates = Jinja2Templates(directory="app/templates")
templates.env.globals["app_name"] = settings.APP_NAME
templates.env.globals["role_labels"] = ROLE_LABELS


def evidence_link(url, label: str = "View"):
    """
    Turn a stored image/OneDrive URL into a clickable link.
    Used in templates as: {{ job.before_images | evidence_link }}
    """
    if not url:
        return ""
    url = str(url).strip()
    if not url:
        return ""
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url
    return Markup(
        f'<a href="{escape(url)}" target="_blank" rel="noopener noreferrer" '
        f'class="evidence-link">{escape(label)} \u2197</a>'
    )


def role_label(role: str) -> str:
    return ROLE_LABELS.get(role, role)


def split_comma(value):
    if not value:
        return []
    return [v.strip() for v in str(value).split(",") if v.strip()]


templates.env.filters["evidence_link"] = evidence_link
templates.env.filters["role_label"] = role_label
templates.env.filters["split_comma"] = split_comma
