-- Remove restrição de unicidade do CNPJ para permitir múltiplos usuários
-- colaboradores em um mesmo CNPJ (empresa com vários usuários na plataforma).
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_cnpj_key;
