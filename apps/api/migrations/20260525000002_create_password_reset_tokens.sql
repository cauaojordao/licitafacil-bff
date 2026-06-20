-- =============================================================================
-- Migration: 20260525000002_create_password_reset_tokens
-- Description: Tokens de uso único para o fluxo de redefinição de senha.
--
-- Decisão arquitetural — PK = user_id (não um UUID separado):
--   A rota /forgot-password faz `upsert` sem especificar `on_conflict`.
--   O Supabase resolve o conflito pela PK por padrão. Com user_id como PK,
--   cada novo pedido de reset substitui o token anterior automaticamente,
--   garantindo que exista no máximo 1 token ativo por usuário.
--   Se usássemos um UUID separado como PK, o upsert sempre INSERT-aria
--   (nunca UPDATE-aria) — acumulando tokens órfãos na tabela.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Tabela principal
-- ---------------------------------------------------------------------------
CREATE TABLE public.password_reset_tokens (
    -- PK = user_id → garante 1 token ativo por usuário; upsert funciona sem on_conflict
    user_id    UUID        PRIMARY KEY REFERENCES public.users(id) ON DELETE CASCADE,
    token      TEXT        UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  public.password_reset_tokens          IS 'Tokens de uso único para redefinição de senha (TTL = 1 h).';
COMMENT ON COLUMN public.password_reset_tokens.user_id  IS 'FK para users. PK intencional: 1 token ativo por usuário.';
COMMENT ON COLUMN public.password_reset_tokens.token    IS 'Token URL-safe gerado com secrets.token_urlsafe(32).';

-- ---------------------------------------------------------------------------
-- Índice: a rota /reset-password busca pelo token, não pelo user_id
-- ---------------------------------------------------------------------------
CREATE INDEX idx_prt_token ON public.password_reset_tokens (token);

-- ---------------------------------------------------------------------------
-- Grants explícitos para service_role
-- ---------------------------------------------------------------------------
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.password_reset_tokens TO service_role;

-- ---------------------------------------------------------------------------
-- Row Level Security (mesma política de users: apenas service role acessa)
-- ---------------------------------------------------------------------------
ALTER TABLE public.password_reset_tokens ENABLE ROW LEVEL SECURITY;

-- ---------------------------------------------------------------------------
-- Rollback (execute manualmente se precisar reverter):
--   DROP TABLE IF EXISTS public.password_reset_tokens;
-- ---------------------------------------------------------------------------
