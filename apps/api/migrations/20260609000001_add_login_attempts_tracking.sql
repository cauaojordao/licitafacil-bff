-- =============================================================================
-- Migration: 20260609000001_add_login_attempts_tracking
-- Description: Adiciona controle de tentativas de login para proteção brute force
-- =============================================================================

ALTER TABLE public.users 
ADD COLUMN failed_login_attempts INTEGER NOT NULL DEFAULT 0,
ADD COLUMN locked_until TIMESTAMPTZ NULL;

COMMENT ON COLUMN public.users.failed_login_attempts IS 
'Contador de tentativas de login falhadas consecutivas.';

COMMENT ON COLUMN public.users.locked_until IS 
'Data/hora até quando a conta está bloqueada por excesso de tentativas. NULL = não bloqueada.';

CREATE INDEX idx_users_locked_until ON public.users (locked_until) WHERE locked_until IS NOT NULL;

COMMENT ON INDEX idx_users_locked_until IS 
'Índice parcial para verificação de contas bloqueadas.';
