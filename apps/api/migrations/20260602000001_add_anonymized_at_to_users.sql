-- =============================================================================
-- Migration: 20260602000001_add_anonymized_at_to_users
-- Description: Adiciona campo de anonimização para compliance LGPD (Art. 18)
--              Permite soft delete mantendo integridade de auditoria
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Adiciona coluna anonymized_at
-- ---------------------------------------------------------------------------
ALTER TABLE public.users 
ADD COLUMN anonymized_at TIMESTAMPTZ NULL;

COMMENT ON COLUMN public.users.anonymized_at IS 
'Data de anonimização do usuário (LGPD Art. 18). Quando preenchida, indica que os dados pessoais foram substituídos por valores irreversíveis.';

-- ---------------------------------------------------------------------------
-- Índice para filtrar usuários ativos (não anonimizados)
-- ---------------------------------------------------------------------------
CREATE INDEX idx_users_active ON public.users (id) WHERE anonymized_at IS NULL;

COMMENT ON INDEX idx_users_active IS 
'Índice parcial para consultas de usuários ativos (não anonimizados).';

-- ---------------------------------------------------------------------------
-- Rollback (execute manualmente se precisar reverter):
--   DROP INDEX IF EXISTS idx_users_active;
--   ALTER TABLE public.users DROP COLUMN IF EXISTS anonymized_at;
-- ---------------------------------------------------------------------------
