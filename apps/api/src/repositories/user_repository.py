"""Repository para gerenciamento de usuários."""


from supabase import Client


class UserRepository:
    """Repository para operações de CRUD de usuários."""

    def __init__(self, db: Client):
        """
        Inicializa o repository com a conexão do banco.

        Args:
            db: Cliente Supabase para acesso ao banco de dados
        """
        self.db = db
        self.table = "users"

    def find_by_email(self, email: str) -> dict | None:
        """
        Busca um usuário pelo e-mail.

        Args:
            email: E-mail do usuário

        Returns:
            Dados do usuário ou None se não encontrado
        """
        result = (
            self.db.table(self.table)
            .select("*")
            .eq("email", email)
            .maybe_single()
            .execute()
        )
        return result.data

    def find_by_id(self, user_id: str) -> dict | None:
        """
        Busca um usuário pelo ID.

        Args:
            user_id: ID do usuário

        Returns:
            Dados do usuário ou None se não encontrado
        """
        result = (
            self.db.table(self.table)
            .select("*")
            .eq("id", user_id)
            .maybe_single()
            .execute()
        )
        return result.data

    def create(self, name: str, email: str, password_hash: str) -> dict:
        """
        Cria um novo usuário.

        Args:
            name: Nome do usuário
            email: E-mail do usuário
            password_hash: Hash da senha

        Returns:
            Dados do usuário criado
        """
        result = (
            self.db.table(self.table)
            .insert({
                "name": name,
                "email": email,
                "password_hash": password_hash,
            })
            .execute()
        )
        return result.data[0]

    def update_password(self, user_id: str, password_hash: str) -> None:
        """
        Atualiza a senha de um usuário.

        Args:
            user_id: ID do usuário
            password_hash: Novo hash da senha
        """
        self.db.table(self.table).update(
            {"password_hash": password_hash}
        ).eq("id", user_id).execute()
