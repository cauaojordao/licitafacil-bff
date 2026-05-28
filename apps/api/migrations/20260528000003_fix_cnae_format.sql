-- Migration para corrigir formato dos CNAEs (remover barras e hífens)
-- Executar apenas se a seed anterior já foi aplicada

-- 1. Remover relacionamentos antigos (com formato antigo)
DELETE FROM cnae_categories WHERE cnae_id LIKE '%-%' OR cnae_id LIKE '%/%';

-- 2. Remover user_cnaes com formato antigo (se existirem)
DELETE FROM user_cnaes WHERE cnae_id LIKE '%-%' OR cnae_id LIKE '%/%';

-- 3. Remover CNAEs com formato antigo
DELETE FROM cnaes WHERE id LIKE '%-%' OR id LIKE '%/%';

-- 4. Inserir CNAEs com formato correto (apenas números)
INSERT INTO cnaes (id, description) VALUES
('4761000', 'Comércio varejista de livros, jornais, revistas e papelaria'),
('4330401', 'Obras de alvenaria'),
('6202300', 'Desenvolvimento e licenciamento de programas de computador customizáveis'),
('5620101', 'Fornecimento de alimentos preparados preponderantemente para empresas'),
('4923002', 'Serviço de transporte de passageiros - locação de automóveis com motorista'),
('4742300', 'Comércio varejista de material elétrico'),
('4330405', 'Instalações elétricas'),
('6311900', 'Tratamento de dados, provedores de serviços de aplicação e serviços de hospedagem na internet'),
('4329101', 'Instalação de painéis publicitários'),
('5611201', 'Restaurantes e similares'),
('6201501', 'Desenvolvimento de programas de computador sob encomenda'),
('6203100', 'Desenvolvimento e licenciamento de programas de computador não-customizáveis'),
('6204000', 'Consultoria em tecnologia da informação'),
('6209100', 'Suporte técnico, manutenção e outros serviços em tecnologia da informação')
ON CONFLICT (id) DO NOTHING;

-- 5. Recriar relacionamentos cnae_categories com formato correto
INSERT INTO cnae_categories (cnae_id, category_id) VALUES
('4761000', '550e8400-e29b-41d4-a716-446655440006'),
('4330401', '550e8400-e29b-41d4-a716-446655440007'),
('6202300', '550e8400-e29b-41d4-a716-446655440008'),
('6201501', '550e8400-e29b-41d4-a716-446655440008'),
('6203100', '550e8400-e29b-41d4-a716-446655440008'),
('6204000', '550e8400-e29b-41d4-a716-446655440008'),
('6209100', '550e8400-e29b-41d4-a716-446655440008'),
('5620101', '550e8400-e29b-41d4-a716-446655440009'),
('4923002', '550e8400-e29b-41d4-a716-446655440010'),
('4742300', '550e8400-e29b-41d4-a716-446655440001'),
('4330405', '550e8400-e29b-41d4-a716-446655440002'),
('6311900', '550e8400-e29b-41d4-a716-446655440008'),
('4329101', '550e8400-e29b-41d4-a716-446655440002'),
('5611201', '550e8400-e29b-41d4-a716-446655440004')
ON CONFLICT (cnae_id, category_id) DO NOTHING;
