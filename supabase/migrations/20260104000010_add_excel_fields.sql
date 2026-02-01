-- ============================================
-- MIGRAÇÃO 10: Adicionar campos do Excel histórico
-- Data: 2026-01-04
-- Objetivo: Expandir tabela registrations para suportar todos os 56 campos do Excel
-- ============================================

BEGIN;

-- Adicionar campos do Veículo (que estavam faltando)
ALTER TABLE registrations 
  ADD COLUMN IF NOT EXISTS cod_modelo TEXT,
  ADD COLUMN IF NOT EXISTS tracao TEXT,
  ADD COLUMN IF NOT EXISTS cilindrada TEXT,
  ADD COLUMN IF NOT EXISTS grupo_modelo TEXT,
  ADD COLUMN IF NOT EXISTS segmento TEXT,
  ADD COLUMN IF NOT EXISTS subsegmento TEXT;

-- Adicionar campos da Concessionária
ALTER TABLE registrations 
  ADD COLUMN IF NOT EXISTS cnpj_concessionario TEXT,
  ADD COLUMN IF NOT EXISTS concessionario TEXT,
  ADD COLUMN IF NOT EXISTS area_operacional TEXT,
  ADD COLUMN IF NOT EXISTS regiao_emplacamento TEXT;

-- Adicionar campos de Preço
ALTER TABLE registrations 
  ADD COLUMN IF NOT EXISTS preco DECIMAL(12,2),
  ADD COLUMN IF NOT EXISTS preco_validado BOOLEAN;

-- Adicionar campos do Proprietário
ALTER TABLE registrations 
  ADD COLUMN IF NOT EXISTS tipo_proprietario TEXT,
  ADD COLUMN IF NOT EXISTS cpf_cnpj_proprietario TEXT,
  ADD COLUMN IF NOT EXISTS nome_proprietario TEXT,
  ADD COLUMN IF NOT EXISTS data_abertura DATE,
  ADD COLUMN IF NOT EXISTS idade_empresa INTEGER,
  ADD COLUMN IF NOT EXISTS faixa_idade_empresa TEXT,
  ADD COLUMN IF NOT EXISTS segmento_cliente TEXT,
  ADD COLUMN IF NOT EXISTS porte TEXT;

-- Adicionar campos de Atividade Econômica
ALTER TABLE registrations 
  ADD COLUMN IF NOT EXISTS cod_atividade_economica TEXT,
  ADD COLUMN IF NOT EXISTS atividade_economica TEXT,
  ADD COLUMN IF NOT EXISTS cnae_agrupado TEXT,
  ADD COLUMN IF NOT EXISTS codigo_natureza_juridica TEXT,
  ADD COLUMN IF NOT EXISTS natureza_juridica TEXT,
  ADD COLUMN IF NOT EXISTS grupo_locadora TEXT;

-- Adicionar campos de Endereço do Proprietário
ALTER TABLE registrations 
  ADD COLUMN IF NOT EXISTS logradouro TEXT,
  ADD COLUMN IF NOT EXISTS numero TEXT,
  ADD COLUMN IF NOT EXISTS complemento TEXT,
  ADD COLUMN IF NOT EXISTS bairro TEXT,
  ADD COLUMN IF NOT EXISTS cep TEXT,
  ADD COLUMN IF NOT EXISTS cidade_proprietario TEXT,
  ADD COLUMN IF NOT EXISTS uf_proprietario CHAR(2);

-- Adicionar campo de Contatos (JSONB para armazenar telefones/celulares)
ALTER TABLE registrations 
  ADD COLUMN IF NOT EXISTS contatos JSONB;

-- Adicionar campos da API Real Hub-Quest (futuro)
ALTER TABLE registrations 
  ADD COLUMN IF NOT EXISTS cod_municipio TEXT,
  ADD COLUMN IF NOT EXISTS combustivel TEXT,
  ADD COLUMN IF NOT EXISTS potencia TEXT,
  ADD COLUMN IF NOT EXISTS data_emplacamento DATE,
  ADD COLUMN IF NOT EXISTS data_atualizacao TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  ADD COLUMN IF NOT EXISTS email TEXT;

-- ============================================
-- ÍNDICES PARA NOVOS CAMPOS
-- ============================================

-- Índices para busca de proprietário
CREATE INDEX IF NOT EXISTS idx_registrations_cpf_cnpj 
  ON registrations(cpf_cnpj_proprietario);

CREATE INDEX IF NOT EXISTS idx_registrations_nome_proprietario 
  ON registrations USING gin(to_tsvector('portuguese', nome_proprietario));

-- Índices para concessionária
CREATE INDEX IF NOT EXISTS idx_registrations_cnpj_concessionario 
  ON registrations(cnpj_concessionario);

CREATE INDEX IF NOT EXISTS idx_registrations_concessionario 
  ON registrations(concessionario);

-- Índices para data de emplacamento (importante para UPSERT)
CREATE INDEX IF NOT EXISTS idx_registrations_data_emplacamento 
  ON registrations(data_emplacamento);

-- Índice composto para UPSERT (chassi + data_emplacamento)
CREATE UNIQUE INDEX IF NOT EXISTS idx_registrations_chassi_data_upsert 
  ON registrations(chassi, data_emplacamento) 
  WHERE chassi IS NOT NULL AND data_emplacamento IS NOT NULL;

-- Índices para atividade econômica
CREATE INDEX IF NOT EXISTS idx_registrations_cod_atividade 
  ON registrations(cod_atividade_economica);

CREATE INDEX IF NOT EXISTS idx_registrations_segmento_cliente 
  ON registrations(segmento_cliente);

-- Índices para localização do proprietário
CREATE INDEX IF NOT EXISTS idx_registrations_cidade_proprietario 
  ON registrations(cidade_proprietario);

CREATE INDEX IF NOT EXISTS idx_registrations_uf_proprietario 
  ON registrations(uf_proprietario);

-- Índice para busca em contatos (JSONB)
CREATE INDEX IF NOT EXISTS idx_registrations_contatos_gin 
  ON registrations USING gin(contatos);

-- Índice para data de atualização (sync incremental)
CREATE INDEX IF NOT EXISTS idx_registrations_data_atualizacao 
  ON registrations(data_atualizacao);

-- Índice para preço
CREATE INDEX IF NOT EXISTS idx_registrations_preco 
  ON registrations(preco) 
  WHERE preco IS NOT NULL;

-- ============================================
-- COMENTÁRIOS
-- ============================================

COMMENT ON COLUMN registrations.cod_modelo IS 'Código do modelo do veículo';
COMMENT ON COLUMN registrations.tracao IS 'Tipo de tração (4X2, 6X4, etc)';
COMMENT ON COLUMN registrations.cilindrada IS 'Cilindrada do motor';
COMMENT ON COLUMN registrations.grupo_modelo IS 'Grupo/família do modelo';
COMMENT ON COLUMN registrations.segmento IS 'Segmento do veículo (Caminhão, Van, etc)';
COMMENT ON COLUMN registrations.subsegmento IS 'Subsegmento (CA - PESADO, etc)';

COMMENT ON COLUMN registrations.cnpj_concessionario IS 'CNPJ da concessionária';
COMMENT ON COLUMN registrations.concessionario IS 'Nome da concessionária';
COMMENT ON COLUMN registrations.area_operacional IS 'Área operacional da concessionária';
COMMENT ON COLUMN registrations.regiao_emplacamento IS 'Região de emplacamento';

COMMENT ON COLUMN registrations.preco IS 'Preço do veículo';
COMMENT ON COLUMN registrations.preco_validado IS 'Se o preço foi validado';

COMMENT ON COLUMN registrations.tipo_proprietario IS 'Tipo do proprietário (JURIDICA/FISICA)';
COMMENT ON COLUMN registrations.cpf_cnpj_proprietario IS 'CPF/CNPJ do proprietário (apenas dígitos)';
COMMENT ON COLUMN registrations.nome_proprietario IS 'Nome/Razão social do proprietário';
COMMENT ON COLUMN registrations.data_abertura IS 'Data de abertura da empresa';
COMMENT ON COLUMN registrations.idade_empresa IS 'Idade da empresa em dias';
COMMENT ON COLUMN registrations.faixa_idade_empresa IS 'Faixa etária da empresa';
COMMENT ON COLUMN registrations.segmento_cliente IS 'Segmento do cliente';
COMMENT ON COLUMN registrations.porte IS 'Porte da empresa';

COMMENT ON COLUMN registrations.cod_atividade_economica IS 'Código CNAE da atividade';
COMMENT ON COLUMN registrations.atividade_economica IS 'Descrição da atividade econômica';
COMMENT ON COLUMN registrations.cnae_agrupado IS 'CNAE agrupado';
COMMENT ON COLUMN registrations.codigo_natureza_juridica IS 'Código da natureza jurídica';
COMMENT ON COLUMN registrations.natureza_juridica IS 'Natureza jurídica';
COMMENT ON COLUMN registrations.grupo_locadora IS 'Se pertence a grupo locadora';

COMMENT ON COLUMN registrations.logradouro IS 'Logradouro do proprietário';
COMMENT ON COLUMN registrations.numero IS 'Número do endereço';
COMMENT ON COLUMN registrations.complemento IS 'Complemento do endereço';
COMMENT ON COLUMN registrations.bairro IS 'Bairro';
COMMENT ON COLUMN registrations.cep IS 'CEP (apenas dígitos)';
COMMENT ON COLUMN registrations.cidade_proprietario IS 'Cidade do proprietário';
COMMENT ON COLUMN registrations.uf_proprietario IS 'UF do proprietário';

COMMENT ON COLUMN registrations.contatos IS 'Contatos (telefones e celulares) em formato JSONB';

COMMENT ON COLUMN registrations.cod_municipio IS 'Código SERPRO do município';
COMMENT ON COLUMN registrations.combustivel IS 'Tipo de combustível';
COMMENT ON COLUMN registrations.potencia IS 'Potência do motor';
COMMENT ON COLUMN registrations.data_emplacamento IS 'Data de emplacamento';
COMMENT ON COLUMN registrations.data_atualizacao IS 'Data da última atualização';
COMMENT ON COLUMN registrations.email IS 'Email de contato';

COMMIT;

-- ============================================
-- VALIDAÇÃO
-- ============================================

-- Verificar se todos os campos foram criados
DO $$
DECLARE
    campo_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO campo_count
    FROM information_schema.columns
    WHERE table_name = 'registrations'
    AND table_schema = 'public';
    
    RAISE NOTICE 'Total de campos na tabela registrations: %', campo_count;
    
    IF campo_count < 50 THEN
        RAISE EXCEPTION 'Migração falhou: esperado pelo menos 50 campos, encontrado %', campo_count;
    END IF;
END $$;
