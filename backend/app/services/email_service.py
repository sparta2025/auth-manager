"""
Email service — SMTP transport with console fallback.

If SMTP_ENABLED=False (default), all emails are printed to stdout.
This lets the project run without a mail server during development
while making it trivial to switch to real sending in production.
"""
import logging
import smtplib
import textwrap
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

log = logging.getLogger(__name__)


def _send_smtp(to: str, subject: str, html: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = settings.SMTP_FROM
    msg["To"]      = to
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
        server.ehlo()
        server.starttls()
        if settings.SMTP_USER:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_FROM, [to], msg.as_string())
    log.info("Email sent to %s: %s", to, subject)


def send_email(to: str, subject: str, html: str) -> None:
    """Send an HTML email. Falls back to console log if SMTP is disabled."""
    if not to:
        return
    if settings.SMTP_ENABLED:
        try:
            _send_smtp(to, subject, html)
        except Exception as exc:
            log.error("Failed to send email to %s: %s", to, exc)
    else:
        plain = html.replace("<br>", "\n").replace("</p>", "\n")
        log.info(
            "\n%s\n📧 EMAIL (console mode)\nTo: %s\nSubject: %s\n%s\n%s",
            "─" * 60, to, subject, "─" * 60,
            textwrap.fill(plain, width=80),
        )


# ── Template helpers ──────────────────────────────────────────────────────────

def _wrap(title: str, body: str) -> str:
    return f"""
<div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:24px;border:1px solid #e5e7eb;border-radius:12px">
  <h2 style="color:#1d4ed8;margin-bottom:16px">{title}</h2>
  {body}
  <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0">
  <p style="color:#9ca3af;font-size:12px">Auth Manager &mdash; автоматическое уведомление</p>
</div>"""


def send_admin_notification(
    event: str, user_email: str, user_id: str, detail: str
) -> None:
    link = f"{settings.FRONTEND_URL}/admin/users/{user_id}"
    body = f"""
<p>Событие: <strong>{event}</strong></p>
<p>Пользователь: <strong>{user_email}</strong></p>
<p>{detail}</p>
<p><a href="{link}" style="background:#1d4ed8;color:white;padding:10px 20px;border-radius:8px;text-decoration:none;display:inline-block">
  Открыть профиль пользователя →
</a></p>"""
    send_email(
        to=settings.ADMIN_EMAIL,
        subject=f"[Auth Manager] {event}: {user_email}",
        html=_wrap(f"Событие: {event}", body),
    )


def send_password_reset(to: str, token: str, is_admin: bool = False) -> None:
    link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    title = "Восстановление пароля администратора" if is_admin else "Восстановление пароля"
    body = f"""
<p>Получен запрос на сброс пароля.</p>
<p>Нажмите кнопку ниже. Ссылка действует <strong>60 минут</strong>.</p>
<p><a href="{link}" style="background:#1d4ed8;color:white;padding:10px 20px;border-radius:8px;text-decoration:none;display:inline-block">
  Сбросить пароль →
</a></p>
<p style="color:#6b7280;font-size:12px">Если вы не запрашивали сброс, проигнорируйте это письмо.</p>"""
    send_email(to=to, subject=title, html=_wrap(title, body))


def send_password_changed(to: str) -> None:
    body = "<p>Пароль вашего аккаунта был успешно изменён.</p><p>Если это были не вы — срочно обратитесь к администратору.</p>"
    send_email(to=to, subject="Пароль изменён — Auth Manager", html=_wrap("Пароль изменён", body))
