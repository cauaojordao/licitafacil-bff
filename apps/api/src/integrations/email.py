"""Integração com serviço de e-mail via SMTP."""

from email.message import EmailMessage

import aiosmtplib

from src.core.config import settings


async def send_reset_code_email(to_email: str, code: str) -> None:
    """
    Envia e-mail com código de 4 dígitos para redefinição de senha.

    Args:
        to_email: Endereço de e-mail do destinatário
        code: Código de 4 dígitos gerado para o usuário

    Raises:
        SMTPException: Se houver erro no envio do e-mail
    """
    message = EmailMessage()
    message["From"] = settings.EMAIL_FROM
    message["To"] = to_email
    message["Subject"] = "Código de redefinição de senha - LicitaFácil"
    message.set_content(
        f"Olá!\n\n"
        f"Recebemos uma solicitação para redefinir a senha da sua conta.\n\n"
        f"Seu código de verificação é:\n\n"
        f"    {code}\n\n"
        f"Este código expira em {settings.RESET_CODE_EXPIRE_MINUTES} minutos.\n\n"
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
