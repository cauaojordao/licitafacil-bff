-- Adicionar razão social da empresa ao perfil do usuário
ALTER TABLE users
ADD COLUMN company_name TEXT;
