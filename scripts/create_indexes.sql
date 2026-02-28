-- =============================================================================
-- FLEETINTEL MCP - INDICES POS-CARGA
-- Execute APOS a carga ETL completa para maxima performance de insercao
--
-- Uso:
--   docker exec -i fleetintel-postgres psql -U fleetintel -d fleetintel < scripts/create_indexes.sql
-- =============================================================================

-- marcas
CREATE INDEX IF NOT EXISTS idx_marcas_nome ON marcas(nome);

-- modelos
CREATE INDEX IF NOT EXISTS idx_modelos_marca ON modelos(marca_id);
CREATE INDEX IF NOT EXISTS idx_modelos_nome ON modelos(nome);

-- vehicles
CREATE INDEX IF NOT EXISTS idx_vehicles_chassi ON vehicles(chassi);
CREATE INDEX IF NOT EXISTS idx_vehicles_placa ON vehicles(placa);
CREATE INDEX IF NOT EXISTS idx_vehicles_marca_id ON vehicles(marca_id);
CREATE INDEX IF NOT EXISTS idx_vehicles_modelo_id ON vehicles(modelo_id);
CREATE INDEX IF NOT EXISTS idx_vehicles_marca_nome ON vehicles(marca_nome);
CREATE INDEX IF NOT EXISTS idx_vehicles_modelo_nome ON vehicles(modelo_nome);
CREATE INDEX IF NOT EXISTS idx_vehicles_ano_fabricacao ON vehicles(ano_fabricacao);

-- empresas
CREATE INDEX IF NOT EXISTS idx_empresas_cnpj ON empresas(cnpj);
CREATE INDEX IF NOT EXISTS idx_empresas_razao_social ON empresas(razao_social);
CREATE INDEX IF NOT EXISTS idx_empresas_segmento ON empresas(segmento_cliente);
CREATE INDEX IF NOT EXISTS idx_empresas_grupo_locadora ON empresas(grupo_locadora);
CREATE INDEX IF NOT EXISTS idx_empresas_cnae ON empresas(cnae_id);
CREATE INDEX IF NOT EXISTS idx_empresas_brasilapi_status ON empresas(brasilapi_status);

-- enderecos
CREATE INDEX IF NOT EXISTS idx_enderecos_empresa ON enderecos(empresa_id);
CREATE INDEX IF NOT EXISTS idx_enderecos_cep ON enderecos(cep);
CREATE INDEX IF NOT EXISTS idx_enderecos_cidade_uf ON enderecos(cidade, uf);
CREATE INDEX IF NOT EXISTS idx_enderecos_brasilapi_status ON enderecos(brasilapi_status);

-- contatos
CREATE INDEX IF NOT EXISTS idx_contatos_empresa ON contatos(empresa_id);

-- registrations (tabela mais consultada)
CREATE INDEX IF NOT EXISTS idx_registrations_vehicle ON registrations(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_registrations_empresa ON registrations(empresa_id);
CREATE INDEX IF NOT EXISTS idx_registrations_external_id ON registrations(external_id);
CREATE INDEX IF NOT EXISTS idx_registrations_data ON registrations(data_emplacamento);
CREATE INDEX IF NOT EXISTS idx_registrations_uf ON registrations(uf_emplacamento);
CREATE INDEX IF NOT EXISTS idx_registrations_ano ON registrations(EXTRACT(YEAR FROM data_emplacamento));
CREATE INDEX IF NOT EXISTS idx_registrations_preco ON registrations(preco) WHERE preco IS NOT NULL;

\echo 'Indices criados com sucesso!'
SELECT schemaname, tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
