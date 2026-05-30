-- Migration para estrutura de editais (opportunities) e categorias de CNAEs

-- 1. Tabela de categorias (hierárquica, suporta árvore)
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    parent_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    slug VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices para categorias
CREATE INDEX idx_categories_parent_id ON categories(parent_id);
CREATE INDEX idx_categories_slug ON categories(slug);

-- 2. Relacionamento CNAEs → Categorias (N:M)
CREATE TABLE cnae_categories (
    cnae_id VARCHAR(10) REFERENCES cnaes(id) ON DELETE CASCADE,
    category_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (cnae_id, category_id)
);

CREATE INDEX idx_cnae_categories_cnae ON cnae_categories(cnae_id);
CREATE INDEX idx_cnae_categories_category ON cnae_categories(category_id);

-- 3. Tabela principal de oportunidades (editais)
CREATE TABLE opportunities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Identificação PNCP
    pncp_id VARCHAR(50) UNIQUE NOT NULL,
    pncp_url TEXT,
    
    -- Informações básicas
    title TEXT NOT NULL,
    description TEXT, -- resumo curto (1-2 linhas)
    object_full TEXT, -- descrição completa do objeto
    
    -- Modalidade e critério
    modality VARCHAR(100) NOT NULL, -- "Pregão eletrônico", "Dispensa", etc
    judgement_criterion VARCHAR(100), -- "Menor preço", "Melhor técnica"
    
    -- Valores
    estimated_value DECIMAL(15, 2) NOT NULL,
    
    -- Datas
    opening_date TIMESTAMP WITH TIME ZONE NOT NULL,
    closing_date TIMESTAMP WITH TIME ZONE NOT NULL,
    proposals_opening_date TIMESTAMP WITH TIME ZONE,
    
    -- Status
    status VARCHAR(20) NOT NULL CHECK (status IN ('aberto', 'encerrado', 'suspenso', 'cancelado')),
    
    -- Órgão responsável
    agency_name TEXT NOT NULL,
    agency_cnpj VARCHAR(14) NOT NULL, -- alfanumérico
    agency_unit TEXT,
    
    -- Localização
    location_city VARCHAR(255),
    location_state VARCHAR(2) NOT NULL, -- UF
    
    -- Metadados
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices para opportunities
CREATE INDEX idx_opportunities_status ON opportunities(status);
CREATE INDEX idx_opportunities_closing_date ON opportunities(closing_date);
CREATE INDEX idx_opportunities_location_state ON opportunities(location_state);
CREATE INDEX idx_opportunities_pncp_id ON opportunities(pncp_id);
CREATE INDEX idx_opportunities_estimated_value ON opportunities(estimated_value);

-- 4. Relacionamento Opportunities → Categories (N:M)
-- Editais já vêm categorizados da camada Silver (Spark)
CREATE TABLE opportunity_categories (
    opportunity_id UUID REFERENCES opportunities(id) ON DELETE CASCADE,
    category_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    is_primary BOOLEAN DEFAULT FALSE, -- Categoria principal do edital
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (opportunity_id, category_id)
);

CREATE INDEX idx_opportunity_categories_opportunity ON opportunity_categories(opportunity_id);
CREATE INDEX idx_opportunity_categories_category ON opportunity_categories(category_id);

-- 5. Favoritos dos usuários
CREATE TABLE user_favorite_opportunities (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    opportunity_id UUID REFERENCES opportunities(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, opportunity_id)
);

CREATE INDEX idx_user_favorite_opportunities_user ON user_favorite_opportunities(user_id);
CREATE INDEX idx_user_favorite_opportunities_opportunity ON user_favorite_opportunities(opportunity_id);

-- 6. Anexos dos editais
CREATE TABLE opportunity_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID REFERENCES opportunities(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    size_bytes BIGINT,
    mime_type VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_opportunity_attachments_opportunity ON opportunity_attachments(opportunity_id);

-- Trigger para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_opportunities_updated_at BEFORE UPDATE ON opportunities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_categories_updated_at BEFORE UPDATE ON categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
