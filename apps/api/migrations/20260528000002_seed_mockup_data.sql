-- Mockup de categorias e oportunidades para camada gold

-- ============================================
-- 1. CATEGORIAS DE CNAES (10 categorias)
-- ============================================

INSERT INTO categories (id, name, description, parent_id, slug) VALUES
-- Categorias raiz
('550e8400-e29b-41d4-a716-446655440001', 'Comércio', 'Atividades comerciais e de varejo', NULL, 'comercio'),
('550e8400-e29b-41d4-a716-446655440002', 'Construção Civil', 'Obras, reformas e serviços de construção', NULL, 'construcao-civil'),
('550e8400-e29b-41d4-a716-446655440003', 'Serviços Profissionais', 'Consultoria, assessoria e serviços técnicos', NULL, 'servicos-profissionais'),
('550e8400-e29b-41d4-a716-446655440004', 'Alimentação', 'Fornecimento de alimentos e refeições', NULL, 'alimentacao'),
('550e8400-e29b-41d4-a716-446655440005', 'Transporte', 'Serviços de transporte e logística', NULL, 'transporte'),

-- Subcategorias
('550e8400-e29b-41d4-a716-446655440006', 'Varejo de Material de Escritório', 'Venda de papelaria e suprimentos', '550e8400-e29b-41d4-a716-446655440001', 'varejo-material-escritorio'),
('550e8400-e29b-41d4-a716-446655440007', 'Obras de Alvenaria', 'Construção e reforma de estruturas', '550e8400-e29b-41d4-a716-446655440002', 'obras-alvenaria'),
('550e8400-e29b-41d4-a716-446655440008', 'Consultoria em TI', 'Serviços de tecnologia da informação', '550e8400-e29b-41d4-a716-446655440003', 'consultoria-ti'),
('550e8400-e29b-41d4-a716-446655440009', 'Fornecimento de Refeições', 'Catering e refeições coletivas', '550e8400-e29b-41d4-a716-446655440004', 'fornecimento-refeicoes'),
('550e8400-e29b-41d4-a716-446655440010', 'Transporte de Passageiros', 'Serviço de transporte urbano/intermunicipal', '550e8400-e29b-41d4-a716-446655440005', 'transporte-passageiros')
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 2. CNAES MOCKADOS (alguns exemplos realistas)
-- ============================================

-- Inserir CNAEs de exemplo se não existirem
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

-- Vincular CNAEs às categorias
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

-- ============================================
-- 3. OPORTUNIDADES (10 editais mockados)
-- ============================================

INSERT INTO opportunities (
    id, pncp_id, pncp_url, title, description, object_full,
    modality, judgement_criterion, estimated_value,
    opening_date, closing_date, proposals_opening_date,
    status, agency_name, agency_cnpj, agency_unit,
    location_city, location_state
) VALUES
-- Edital 1
(
    '660e8400-e29b-41d4-a716-446655440001',
    'PNCP-2026-001234',
    'https://pncp.gov.br/edital/PNCP-2026-001234',
    'Aquisição de Material de Escritório - Prefeitura',
    'Fornecimento de papelaria e material de escritório para o exercício de 2026',
    'Contratação de empresa especializada para fornecimento de material de escritório (canetas, papéis, pastas, grampeadores, etc.) em regime de entrega parcelada para atender às necessidades das secretarias municipais durante o ano de 2026.',
    'Pregão Eletrônico',
    'Menor preço',
    45000.00,
    '2026-05-20 08:00:00-03',
    '2026-06-05 18:00:00-03',
    '2026-06-06 10:00:00-03',
    'aberto',
    'Prefeitura Municipal de Recife',
    '11222333000145',
    'Secretaria de Administração',
    'Recife',
    'PE'
),

-- Edital 2
(
    '660e8400-e29b-41d4-a716-446655440002',
    'PNCP-2026-005678',
    'https://pncp.gov.br/edital/PNCP-2026-005678',
    'Reforma e Ampliação de Escola Municipal',
    'Obras de alvenaria, instalações elétricas e pintura',
    'Execução de reforma completa da Escola Municipal João da Silva, incluindo: ampliação de 2 salas de aula, reforma de banheiros, instalações elétricas completas, pintura interna e externa, e adequação de acessibilidade conforme ABNT NBR 9050.',
    'Concorrência Pública',
    'Menor preço',
    850000.00,
    '2026-05-15 09:00:00-03',
    '2026-06-10 17:00:00-03',
    '2026-06-12 14:00:00-03',
    'aberto',
    'Secretaria de Educação do Estado de São Paulo',
    '44556677000188',
    'Diretoria Regional de Ensino Norte',
    'São Paulo',
    'SP'
),

-- Edital 3
(
    '660e8400-e29b-41d4-a716-446655440003',
    'PNCP-2026-008912',
    'https://pncp.gov.br/edital/PNCP-2026-008912',
    'Desenvolvimento de Sistema de Gestão Escolar',
    'Software customizado para controle acadêmico',
    'Contratação de empresa de TI para desenvolvimento de sistema web de gestão escolar, incluindo módulos de matrícula, notas, frequência, boletim online, comunicação com pais, e integração com sistema de RH. Prazo de entrega: 6 meses.',
    'Tomada de Preços',
    'Melhor técnica e preço',
    320000.00,
    '2026-05-10 08:30:00-03',
    '2026-05-28 16:00:00-03',
    '2026-05-29 09:00:00-03',
    'aberto',
    'Universidade Federal do Rio de Janeiro',
    '33778899000166',
    'Pró-Reitoria de Graduação',
    'Rio de Janeiro',
    'RJ'
),

-- Edital 4
(
    '660e8400-e29b-41d4-a716-446655440004',
    'PNCP-2026-012345',
    'https://pncp.gov.br/edital/PNCP-2026-012345',
    'Fornecimento de Refeições para Hospital Público',
    'Catering com 1.200 refeições/dia por 12 meses',
    'Contratação de empresa de alimentação coletiva para fornecimento de café da manhã, almoço e jantar para pacientes, acompanhantes e funcionários do Hospital Regional, totalizando aproximadamente 1.200 refeições/dia. Contrato de 12 meses com possibilidade de renovação.',
    'Pregão Eletrônico',
    'Menor preço',
    1800000.00,
    '2026-05-18 09:00:00-03',
    '2026-06-08 18:00:00-03',
    '2026-06-10 10:00:00-03',
    'aberto',
    'Secretaria de Saúde do Estado do Paraná',
    '55667788000199',
    'Hospital Regional do Litoral',
    'Paranaguá',
    'PR'
),

-- Edital 5
(
    '660e8400-e29b-41d4-a716-446655440005',
    'PNCP-2026-016789',
    'https://pncp.gov.br/edital/PNCP-2026-016789',
    'Transporte Escolar Rural - Zona Norte',
    'Locação de veículos com motorista para transporte de alunos',
    'Prestação de serviço de transporte escolar rural para atender alunos da rede municipal na zona norte, compreendendo 8 rotas diárias (ida e volta), com veículos apropriados e motoristas habilitados. Período: 200 dias letivos.',
    'Pregão Presencial',
    'Menor preço',
    280000.00,
    '2026-05-12 10:00:00-03',
    '2026-05-30 14:00:00-03',
    '2026-06-01 09:00:00-03',
    'aberto',
    'Prefeitura Municipal de Belém',
    '66778899000177',
    'Secretaria de Educação',
    'Belém',
    'PA'
),

-- Edital 6
(
    '660e8400-e29b-41d4-a716-446655440006',
    'PNCP-2026-020123',
    'https://pncp.gov.br/edital/PNCP-2026-020123',
    'Material Elétrico para Iluminação Pública',
    'Lâmpadas LED, luminárias e acessórios',
    'Aquisição de material elétrico para manutenção e expansão da iluminação pública, incluindo: 2.000 lâmpadas LED 100W, 500 luminárias, 1.000m de cabos, disjuntores, e demais acessórios. Entrega parcelada conforme cronograma.',
    'Pregão Eletrônico',
    'Menor preço',
    195000.00,
    '2026-05-22 08:00:00-03',
    '2026-06-12 17:00:00-03',
    '2026-06-13 11:00:00-03',
    'aberto',
    'Prefeitura Municipal de Curitiba',
    '77889900000155',
    'Secretaria de Obras Públicas',
    'Curitiba',
    'PR'
),

-- Edital 7
(
    '660e8400-e29b-41d4-a716-446655440007',
    'PNCP-2026-024567',
    'https://pncp.gov.br/edital/PNCP-2026-024567',
    'Instalação de Rede Elétrica em Prédio Novo',
    'Instalações elétricas completas para edifício de 4 andares',
    'Execução de projeto elétrico completo para novo edifício administrativo de 4 andares, incluindo: cabeamento estruturado, quadros de distribuição, tomadas, interruptores, iluminação, aterramento, SPDA (para-raios), e sistema de emergência com nobreak.',
    'Tomada de Preços',
    'Menor preço',
    420000.00,
    '2026-05-08 09:30:00-03',
    '2026-05-26 16:00:00-03',
    '2026-05-27 10:00:00-03',
    'aberto',
    'Tribunal de Justiça do Estado da Bahia',
    '88990011000133',
    'Diretoria de Infraestrutura',
    'Salvador',
    'BA'
),

-- Edital 8
(
    '660e8400-e29b-41d4-a716-446655440008',
    'PNCP-2026-028901',
    'https://pncp.gov.br/edital/PNCP-2026-028901',
    'Hospedagem e Infraestrutura Cloud',
    'Serviços de cloud computing por 24 meses',
    'Contratação de serviços de hospedagem em nuvem (IaaS e PaaS) para sistemas institucionais, incluindo: servidores virtuais, banco de dados gerenciado, storage, backup automatizado, CDN, e suporte técnico 24x7. Contrato de 24 meses.',
    'Pregão Eletrônico',
    'Menor preço',
    680000.00,
    '2026-05-25 08:00:00-03',
    '2026-06-15 18:00:00-03',
    '2026-06-17 14:00:00-03',
    'aberto',
    'Ministério da Ciência, Tecnologia e Inovação',
    '99001122000111',
    'Secretaria de Tecnologia da Informação',
    'Brasília',
    'DF'
),

-- Edital 9
(
    '660e8400-e29b-41d4-a716-446655440009',
    'PNCP-2026-032345',
    'https://pncp.gov.br/edital/PNCP-2026-032345',
    'Instalação de Painéis Publicitários em Rodovia',
    'Fabricação, instalação e manutenção de 20 painéis',
    'Prestação de serviços de fabricação, instalação e manutenção de 20 painéis publicitários digitais (LED) ao longo da BR-101, trecho Sul, com estrutura metálica, fundação, cabeamento e sistema de controle remoto. Manutenção inclusa por 36 meses.',
    'Concorrência Pública',
    'Melhor técnica e preço',
    1200000.00,
    '2026-05-05 10:00:00-03',
    '2026-05-23 17:00:00-03',
    '2026-05-25 09:00:00-03',
    'aberto',
    'Departamento Nacional de Infraestrutura de Transportes',
    '00112233000144',
    'Superintendência Regional Sul',
    'Florianópolis',
    'SC'
),

-- Edital 10
(
    '660e8400-e29b-41d4-a716-446655440010',
    'PNCP-2026-036789',
    'https://pncp.gov.br/edital/PNCP-2026-036789',
    'Restaurante Comunitário - Gestão e Operação',
    'Operação de restaurante popular com 800 refeições/dia',
    'Concessão de uso de espaço público para operação de restaurante comunitário, com fornecimento de 800 refeições/dia (almoço) a preço subsidiado (R$ 2,00 por refeição). Empresa responsável por equipe, insumos, equipamentos e manutenção. Prazo: 60 meses.',
    'Concorrência Pública',
    'Melhor técnica e preço',
    3600000.00,
    '2026-05-01 09:00:00-03',
    '2026-05-20 16:00:00-03',
    '2026-05-22 10:00:00-03',
    'aberto',
    'Prefeitura Municipal de Fortaleza',
    '11223344000122',
    'Secretaria de Assistência Social',
    'Fortaleza',
    'CE'
)
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 4. RELACIONAMENTO: OPPORTUNITIES <-> CATEGORIES
-- Spark já classificou os editais em categorias (Silver → Gold)
-- ============================================

INSERT INTO opportunity_categories (opportunity_id, category_id, is_primary) VALUES
-- Edital 1: Material de escritório → Varejo de Material de Escritório
('660e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440006', TRUE),
('660e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', FALSE),

-- Edital 2: Reforma escola → Obras de Alvenaria + Construção Civil
('660e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440007', TRUE),
('660e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440002', FALSE),

-- Edital 3: Sistema TI → Consultoria em TI + Serviços Profissionais
('660e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440008', TRUE),
('660e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440003', FALSE),

-- Edital 4: Refeições hospital → Fornecimento de Refeições + Alimentação
('660e8400-e29b-41d4-a716-446655440004', '550e8400-e29b-41d4-a716-446655440009', TRUE),
('660e8400-e29b-41d4-a716-446655440004', '550e8400-e29b-41d4-a716-446655440004', FALSE),

-- Edital 5: Transporte escolar → Transporte de Passageiros + Transporte
('660e8400-e29b-41d4-a716-446655440005', '550e8400-e29b-41d4-a716-446655440010', TRUE),
('660e8400-e29b-41d4-a716-446655440005', '550e8400-e29b-41d4-a716-446655440005', FALSE),

-- Edital 6: Material elétrico → Comércio
('660e8400-e29b-41d4-a716-446655440006', '550e8400-e29b-41d4-a716-446655440001', TRUE),

-- Edital 7: Instalações elétricas → Construção Civil
('660e8400-e29b-41d4-a716-446655440007', '550e8400-e29b-41d4-a716-446655440002', TRUE),

-- Edital 8: Cloud → Consultoria em TI + Serviços Profissionais
('660e8400-e29b-41d4-a716-446655440008', '550e8400-e29b-41d4-a716-446655440008', TRUE),
('660e8400-e29b-41d4-a716-446655440008', '550e8400-e29b-41d4-a716-446655440003', FALSE),

-- Edital 9: Painéis publicitários → Construção Civil
('660e8400-e29b-41d4-a716-446655440009', '550e8400-e29b-41d4-a716-446655440002', TRUE),

-- Edital 10: Restaurante → Alimentação
('660e8400-e29b-41d4-a716-446655440010', '550e8400-e29b-41d4-a716-446655440004', TRUE)
ON CONFLICT (opportunity_id, category_id) DO NOTHING;

-- ============================================
-- 5. ANEXOS MOCKADOS (alguns exemplos)
-- ============================================

INSERT INTO opportunity_attachments (id, opportunity_id, name, url, size_bytes, mime_type) VALUES
('770e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440001', 'Edital Completo.pdf', 'https://pncp.gov.br/anexos/edital-001234.pdf', 524288, 'application/pdf'),
('770e8400-e29b-41d4-a716-446655440002', '660e8400-e29b-41d4-a716-446655440002', 'Projeto Arquitetônico.pdf', 'https://pncp.gov.br/anexos/projeto-005678.pdf', 2097152, 'application/pdf'),
('770e8400-e29b-41d4-a716-446655440003', '660e8400-e29b-41d4-a716-446655440003', 'Termo de Referência.pdf', 'https://pncp.gov.br/anexos/termo-008912.pdf', 1048576, 'application/pdf'),
('770e8400-e29b-41d4-a716-446655440004', '660e8400-e29b-41d4-a716-446655440004', 'Cardápio Referência.pdf', 'https://pncp.gov.br/anexos/cardapio-012345.pdf', 327680, 'application/pdf')
ON CONFLICT (id) DO NOTHING;
