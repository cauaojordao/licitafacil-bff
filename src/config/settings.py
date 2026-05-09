import os
from dotenv import load_dotenv


load_dotenv()


class Settings:
    """
    Classe responsável por centralizar as configurações da aplicação.
    As variáveis são carregadas a partir do arquivo .env.
    """

    PNCP_BASE_URL = os.getenv("PNCP_BASE_URL", "")
    MONGO_URI = os.getenv("MONGO_URI", "")
    MONGO_DATABASE = os.getenv("MONGO_DATABASE", "")
    MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

    @classmethod
    def validate(cls) -> None:
        """
        Valida se as configurações obrigatórias foram definidas.

        Raises:
            ValueError: Caso alguma configuração obrigatória esteja ausente.
        """
        required_fields = {
            "PNCP_BASE_URL": cls.PNCP_BASE_URL,
            "MONGO_URI": cls.MONGO_URI,
            "MONGO_DATABASE": cls.MONGO_DATABASE,
            "MONGO_COLLECTION": cls.MONGO_COLLECTION,
        }

        missing = [key for key, value in required_fields.items() if not value]

        if missing:
            raise ValueError(
                f"As seguintes variáveis de ambiente não foram definidas: {', '.join(missing)}"
            )