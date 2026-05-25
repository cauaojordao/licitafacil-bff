import aiosmtplib
from email.message import EmailMessage

from api.core.config import settings


async def send_reset_email(to_email: str, reset_token: str) -> None:
    """Envia o e-mail com o link de redefinição de senha."""
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

    message = EmailMessage()
    message["From"] = settings.EMAIL_FROM
    message["To"] = to_email
    message["Subject"] = "Redefinição de senha - LicitaFácil"
    message.set_content(
        f"Olá!\n\n"
        f"Recebemos uma solicitação para redefinir a senha da sua conta.\n\n"
        f"Clique no link abaixo para criar uma nova senha:\n{reset_url}\n\n"
        f"Este link expira em 1 hora.\n\n"
        f"Se você não solicitou isso, ignore este e-mail."
    )

    await aiosmtplib.send(
        message,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        start_tls=True,
    )
