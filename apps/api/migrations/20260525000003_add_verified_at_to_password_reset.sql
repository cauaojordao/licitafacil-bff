-- Adicionar campo verified_at para controle de código verificado
ALTER TABLE password_reset_tokens 
ADD COLUMN verified_at TIMESTAMP WITH TIME ZONE;

-- Criar índice para busca por código e email
CREATE INDEX idx_password_reset_tokens_token ON password_reset_tokens(token);
