-- ============================================
-- FUNÇÕES DE UPSERT PARA REGISTRATIONS
-- ============================================

-- Função para UPSERT de um único registro
CREATE OR REPLACE FUNCTION upsert_registration(
    p_external_id TEXT,
    p_placa TEXT,
    p_renavam TEXT DEFAULT NULL,
    p_chassi TEXT DEFAULT NULL,
    p_marca TEXT DEFAULT NULL,
    p_modelo TEXT DEFAULT NULL,
    p_ano_fabricacao INTEGER DEFAULT NULL,
    p_ano_modelo INTEGER DEFAULT NULL,
    p_cor TEXT DEFAULT NULL,
    p_categoria TEXT DEFAULT NULL,
    p_municipio TEXT DEFAULT NULL,
    p_uf CHAR(2) DEFAULT NULL,
    p_situacao TEXT DEFAULT NULL,
    p_restricao TEXT DEFAULT NULL,
    p_data_registro TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    p_fonte TEXT DEFAULT 'api',
    p_versao_carga INTEGER DEFAULT 1,
    p_raw_data JSONB DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_id UUID;
BEGIN
    INSERT INTO registrations (
        external_id, placa, renavam, chassi, marca, modelo,
        ano_fabricacao, ano_modelo, cor, categoria, municipio, uf,
        situacao, restricao, data_registro, fonte, versao_carga, raw_data
    ) VALUES (
        p_external_id, p_placa, p_renavam, p_chassi, p_marca, p_modelo,
        p_ano_fabricacao, p_ano_modelo, p_cor, p_categoria, p_municipio, p_uf,
        p_situacao, p_restricao, p_data_registro, p_fonte, p_versao_carga, p_raw_data
    )
    ON CONFLICT (external_id) DO UPDATE SET
        placa = EXCLUDED.placa,
        renavam = COALESCE(EXCLUDED.renavam, registrations.renavam),
        chassi = COALESCE(EXCLUDED.chassi, registrations.chassi),
        marca = COALESCE(EXCLUDED.marca, registrations.marca),
        modelo = COALESCE(EXCLUDED.modelo, registrations.modelo),
        ano_fabricacao = COALESCE(EXCLUDED.ano_fabricacao, registrations.ano_fabricacao),
        ano_modelo = COALESCE(EXCLUDED.ano_modelo, registrations.ano_modelo),
        cor = COALESCE(EXCLUDED.cor, registrations.cor),
        categoria = COALESCE(EXCLUDED.categoria, registrations.categoria),
        municipio = COALESCE(EXCLUDED.municipio, registrations.municipio),
        uf = COALESCE(EXCLUDED.uf, registrations.uf),
        situacao = COALESCE(EXCLUDED.situacao, registrations.situacao),
        restricao = COALESCE(EXCLUDED.restricao, registrations.restricao),
        data_registro = COALESCE(EXCLUDED.data_registro, registrations.data_registro),
        versao_carga = EXCLUDED.versao_carga,
        raw_data = COALESCE(EXCLUDED.raw_data, registrations.raw_data),
        updated_at = NOW()
    RETURNING id INTO v_id;
    
    RETURN v_id;
END;
$$ LANGUAGE plpgsql;

-- Comentário
COMMENT ON FUNCTION upsert_registration IS 
'Insere ou atualiza um registro de veículo. Usa COALESCE para preservar dados existentes quando novos valores são NULL.';

-- ============================================

-- Função para UPSERT em batch (array de registros)
CREATE OR REPLACE FUNCTION upsert_registrations_batch(
    p_registrations JSONB
)
RETURNS TABLE (
    external_id TEXT,
    id UUID,
    action TEXT
) AS $$
DECLARE
    v_record JSONB;
    v_id UUID;
    v_action TEXT;
BEGIN
    -- Iterar sobre cada registro no array JSON
    FOR v_record IN SELECT * FROM jsonb_array_elements(p_registrations)
    LOOP
        -- Verificar se registro já existe
        SELECT registrations.id INTO v_id
        FROM registrations
        WHERE registrations.external_id = v_record->>'external_id';
        
        IF v_id IS NOT NULL THEN
            v_action := 'updated';
        ELSE
            v_action := 'inserted';
        END IF;
        
        -- Executar UPSERT
        SELECT upsert_registration(
            v_record->>'external_id',
            v_record->>'placa',
            v_record->>'renavam',
            v_record->>'chassi',
            v_record->>'marca',
            v_record->>'modelo',
            (v_record->>'ano_fabricacao')::INTEGER,
            (v_record->>'ano_modelo')::INTEGER,
            v_record->>'cor',
            v_record->>'categoria',
            v_record->>'municipio',
            v_record->>'uf',
            v_record->>'situacao',
            v_record->>'restricao',
            (v_record->>'data_registro')::TIMESTAMP WITH TIME ZONE,
            COALESCE(v_record->>'fonte', 'batch_import'),
            COALESCE((v_record->>'versao_carga')::INTEGER, 1),
            v_record->'raw_data'
        ) INTO v_id;
        
        -- Retornar resultado
        RETURN QUERY SELECT 
            v_record->>'external_id',
            v_id,
            v_action;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Comentário
COMMENT ON FUNCTION upsert_registrations_batch IS 
'Insere ou atualiza múltiplos registros de veículos a partir de um array JSONB. Retorna o ID e ação (inserted/updated) para cada registro.';

-- ============================================

-- Exemplo de uso:
-- 
-- -- UPSERT single:
-- SELECT upsert_registration(
--     'EXT-001',
--     'ABC1234',
--     '12345678901',
--     NULL,
--     'FIAT',
--     'UNO',
--     2020,
--     2021,
--     'BRANCO',
--     'PASSEIO',
--     'SÃO PAULO',
--     'SP',
--     'ATIVO',
--     NULL,
--     NOW(),
--     'api',
--     1,
--     '{"source": "detran"}'::jsonb
-- );
--
-- -- UPSERT batch:
-- SELECT * FROM upsert_registrations_batch('[
--     {
--         "external_id": "EXT-001",
--         "placa": "ABC1234",
--         "marca": "FIAT",
--         "modelo": "UNO",
--         "ano_fabricacao": 2020,
--         "uf": "SP"
--     },
--     {
--         "external_id": "EXT-002",
--         "placa": "XYZ5678",
--         "marca": "VW",
--         "modelo": "GOL",
--         "ano_fabricacao": 2019,
--         "uf": "RJ"
--     }
-- ]'::jsonb);
