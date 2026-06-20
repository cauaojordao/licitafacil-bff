-- Adicionar campos específicos do MEI na tabela users
ALTER TABLE users 
ADD COLUMN cnpj VARCHAR(14) UNIQUE,
ADD COLUMN registration_complete BOOLEAN DEFAULT FALSE,
ADD COLUMN onboarding_completed_at TIMESTAMP WITH TIME ZONE;

-- Criar tabela de CNAEs (Classificação Nacional de Atividades Econômicas)
CREATE TABLE cnaes (
    id VARCHAR(10) PRIMARY KEY,  -- Código CNAE (ex: "4781400")
    title TEXT NOT NULL,          -- Descrição da atividade
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Criar índice para busca por título
CREATE INDEX idx_cnaes_title ON cnaes(title);

-- Criar tabela de relacionamento usuário-CNAEs
CREATE TABLE user_cnaes (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    cnae_id VARCHAR(10) REFERENCES cnaes(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, cnae_id)
);

-- Criar tabela de estados de interesse do usuário
CREATE TABLE user_interested_states (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    state_id VARCHAR(2) NOT NULL,  -- Código IBGE da UF (ex: "35" para SP)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, state_id)
);

-- Criar índices para melhorar performance de queries
CREATE INDEX idx_user_cnaes_user_id ON user_cnaes(user_id);
CREATE INDEX idx_user_interested_states_user_id ON user_interested_states(user_id);
