-- =============================================================================
-- Migration: 20260525000001_create_users
-- Description: Tabela de contas de usuário com autenticação JWT própria.
--              NÃO usa Supabase Auth — credenciais ficam no schema public.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Tabela principal
-- ---------------------------------------------------------------------------
CREATE TABLE public.users (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name          TEXT        NOT NULL,
    -- email normalizado em lowercase pela camada de aplicação (Pydantic EmailStr)
    email         TEXT        UNIQUE NOT NULL,
    password_hash TEXT        NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  public.users                IS 'Contas de usuário da plataforma LicitaFácil.';
COMMENT ON COLUMN public.users.password_hash  IS 'Hash bcrypt — nunca armazene a senha em texto plano.';

-- ---------------------------------------------------------------------------
-- Índice auxiliar: busca case-insensitive de e-mail (segurança extra)
-- ---------------------------------------------------------------------------
CREATE INDEX idx_users_email_lower ON public.users (lower(email));

-- ---------------------------------------------------------------------------
-- Trigger: mantém updated_at sincronizado automaticamente
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();

-- ---------------------------------------------------------------------------
-- Grants explícitos para service_role (Postgres 15+ não herda por padrão)
-- anon / authenticated: sem grants — bloqueados pelo RLS sem policies
-- ---------------------------------------------------------------------------
GRANT USAGE ON SCHEMA public TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.users TO service_role;

-- ---------------------------------------------------------------------------
-- Row Level Security
-- Habilitado sem policies: apenas a service role key do backend tem acesso.
-- Clientes anônimos ou autenticados via Supabase são bloqueados pelo Postgres.
-- ---------------------------------------------------------------------------
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- ---------------------------------------------------------------------------
-- Rollback (execute manualmente se precisar reverter):
--   DROP TRIGGER  IF EXISTS trg_users_updated_at ON public.users;
--   DROP FUNCTION IF EXISTS public.set_updated_at();
--   DROP TABLE    IF EXISTS public.users;
-- ---------------------------------------------------------------------------
