# 🏗️ DATABASE REDESIGN V2 - Arquitetura Normalizada

**Data:** 2026-01-04  
**Estratégia:** Reset Completo (Opção B)  
**Target Performance:** <1 hora para 974k registros  
**Prioridade:** Alta integração BrasilAPI (CNPJ + CEP)

---

## 🎯 OBJETIVOS

1. ✅ Schema normalizado (3NF)
2. ✅ Tipos de dados corretos (CNPJ com 14 dígitos)
3. ✅ Relacionamentos com FKs
4. ✅ Performance <1h para carga completa
5. ✅ Integração BrasilAPI embutida
6. ✅ Escalabilidade para milhões de registros

---

## 📊 NOVA ARQUITETURA

### **Modelo Entidade-Relacionamento**

```
vehicles (1) ────── (N) registrations (N) ────── (1) empresas
    │                                                    │
    │                                                    ├─── (1) enderecos
    │                                                    ├─── (1) contatos
    ├─── (1) marcas                                      └─── (N:1) cnae_lookup
    └─── (1) modelos
```

### **Tabelas e Campos**

#### 1. **marcas** (Tabela de domínio)
```sql
CREATE TABLE marcas (
    id SERIAL PRIMARY KEY,
    nome TEXT UNIQUE NOT NULL,
    nome_normalizado TEXT GENERATED ALWAYS AS (UPPER(TRIM(nome))) STORED,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 2. **modelos** (Tabela de domínio)
```sql
CREATE TABLE modelos (
    id SERIAL PRIMARY KEY,
    marca_id INT NOT NULL REFERENCES marcas(id),
    nome TEXT NOT NULL,
    segmento TEXT,
    subsegmento TEXT,
    tracao TEXT,
    cilindrada TEXT,
    UNIQUE(marca_id, nome),
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 3. **vehicles** (Dados do veículo - imutáveis)
```sql
CREATE TABLE vehicles (
    id SERIAL PRIMARY KEY,
    chassi CHAR(17) UNIQUE NOT NULL,
    placa CHAR(7),
    marca_id INT REFERENCES marcas(id),
    modelo_id INT REFERENCES modelos(id),
    ano_fabricacao INT,
    ano_modelo INT,
    cor TEXT,
    categoria TEXT,
    
    -- Peso para evitar JOINs desnecessários
    marca_nome TEXT, -- denormalized
    modelo_nome TEXT, -- denormalized
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### 4. **empresas** (CNPJ + BrasilAPI)
```sql
CREATE TABLE empresas (
    id SERIAL PRIMARY KEY,
    cnpj CHAR(14) UNIQUE NOT NULL,
    
    -- Dados básicos
    razao_social TEXT,
    nome_fantasia TEXT,
    tipo_proprietario TEXT, -- PJ/PF
    
    -- Classificação
    cnae_id INT REFERENCES cnae_lookup(id),
    porte TEXT,
    natureza_juridica TEXT,
    codigo_natureza_juridica INT,
    
    -- Status
    situacao_cadastral TEXT,
    data_abertura DATE,
    idade_empresa_dias INT,
    faixa_idade_empresa TEXT,
    
    -- Segmentação
    segmento_cliente TEXT,
    grupo_locadora TEXT,
    
    -- Enriquecimento BrasilAPI
    brasilapi_qsa JSONB, -- Quadro societário
    brasilapi_cnaes_sec JSONB, -- CNAEs secundários
    brasilapi_raw JSONB, -- Response completo
    brasilapi_status TEXT, -- pending|success|error
    brasilapi_updated_at TIMESTAMP,
    brasilapi_error TEXT,
    
    -- Metadata
    source TEXT DEFAULT 'excel',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_empresas_cnpj ON empresas(cnpj);
CREATE INDEX idx_empresas_cnae ON empresas(cnae_id);
CREATE INDEX idx_empresas_brasilapi_status ON empresas(brasilapi_status);
```

#### 5. **enderecos** (CEP + BrasilAPI)
```sql
CREATE TABLE enderecos (
    id SERIAL PRIMARY KEY,
    empresa_id INT UNIQUE NOT NULL REFERENCES empresas(id), -- 1:1
    
    -- Endereço
    cep CHAR(8),
    logradouro TEXT,
    numero TEXT,
    complemento TEXT,
    bairro TEXT,
    cidade TEXT,
    uf CHAR(2),
    codigo_municipio_ibge INT,
    
    -- Geolocalização (BrasilAPI CEP V2)
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    
    -- Enriquecimento BrasilAPI
    brasilapi_raw JSONB,
    brasilapi_status TEXT, -- pending|success|error
    brasilapi_updated_at TIMESTAMP,
    brasilapi_error TEXT,
    
    -- Metadata
    source TEXT DEFAULT 'excel',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_enderecos_empresa ON enderecos(empresa_id);
CREATE INDEX idx_enderecos_cep ON enderecos(cep);
CREATE INDEX idx_enderecos_cidade_uf ON enderecos(cidade, uf);
CREATE INDEX idx_enderecos_brasilapi_status ON enderecos(brasilapi_status);
```

#### 6. **contatos** (Telefones e emails)
```sql
CREATE TABLE contatos (
    id SERIAL PRIMARY KEY,
    empresa_id INT UNIQUE NOT NULL REFERENCES empresas(id), -- 1:1
    
    telefones TEXT[], -- Array de telefones
    celulares TEXT[], -- Array de celulares
    email TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_contatos_empresa ON contatos(empresa_id);
```

#### 7. **registrations** (Núcleo - apenas dados variáveis)
```sql
CREATE TABLE registrations (
    id SERIAL PRIMARY KEY,
    external_id TEXT UNIQUE NOT NULL,
    
    -- Relacionamentos (FKs)
    vehicle_id INT NOT NULL REFERENCES vehicles(id),
    empresa_id INT NOT NULL REFERENCES empresas(id),
    
    -- Dados do emplacamento
    data_emplacamento DATE NOT NULL,
    municipio_emplacamento TEXT,
    uf_emplacamento CHAR(2),
    regiao_emplacamento TEXT,
    
    -- Concessionária
    cnpj_concessionario CHAR(14),
    concessionario TEXT,
    area_operacional TEXT,
    
    -- Comercial
    preco DECIMAL(12,2),
    preco_validado BOOLEAN,
    
    -- Metadata
    fonte TEXT DEFAULT 'excel_inicial',
    versao_carga INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Chave composta para UPSERT
    UNIQUE(vehicle_id, data_emplacamento)
);

CREATE INDEX idx_registrations_vehicle ON registrations(vehicle_id);
CREATE INDEX idx_registrations_empresa ON registrations(empresa_id);
CREATE INDEX idx_registrations_data_emplac ON registrations(data_emplacamento);
CREATE INDEX idx_registrations_external_id ON registrations(external_id);
```

---

## 🔧 CORREÇÕES DE TIPOS DE DADOS

### **Função para corrigir documentos**
```sql
CREATE OR REPLACE FUNCTION fix_documento(doc TEXT, tamanho INT) 
RETURNS TEXT AS $$
BEGIN
    IF doc IS NULL OR doc = '' THEN
        RETURN NULL;
    END IF;
    
    -- Remove tudo que não é dígito
    doc := regexp_replace(doc, '\D', '', 'g');
    
    -- Se vazio após limpeza, retorna NULL
    IF doc = '' THEN
        RETURN NULL;
    END IF;
    
    -- Preenche zeros à esquerda
    RETURN lpad(doc, tamanho, '0');
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Exemplos:
-- fix_documento('2916265009116', 14) → '02916265009116' ✅
-- fix_documento('4744099', 7) → '0474409' ✅
-- fix_documento('89010025', 8) → '89010025' ✅
```

---

## 📈 ESTIMATIVA DE PERFORMANCE

### **Target: <1 hora para 974k registros**

#### Estratégia:
1. **COPY bulk insert** (mais rápido que INSERT)
2. **Desabilitar índices** durante carga
3. **Batches de 10k** com commits parciais
4. **Parallel processing** onde possível

#### Cálculo:
```
974,122 registros / 3600 segundos = 270 reg/s mínimo
Com batches de 10k:
  - 97 batches
  - ~37 segundos/batch
  - Total: ~60 minutos ✅
```

---

## 🔄 INTEGRAÇÃO BRASILAPI

### **Job de Enriquecimento Assíncrono**

```python
# jobs/enrich_brasilapi.py

async def enrich_empresas_job():
    """
    Enriquece empresas pendentes com dados BrasilAPI
    Rate limit: 100 req/min (conservador)
    """
    empresas = await db.fetch("""
        SELECT id, cnpj 
        FROM empresas 
        WHERE brasilapi_status IS NULL 
           OR brasilapi_status = 'pending'
        LIMIT 100
    """)
    
    for empresa in empresas:
        try:
            # Chamar BrasilAPI CNPJ
            data = await brasilapi_cnpj(empresa['cnpj'])
            
            await db.execute("""
                UPDATE empresas SET
                    razao_social = COALESCE(razao_social, $1),
                    nome_fantasia = $2,
                    situacao_cadastral = $3,
                    brasilapi_qsa = $4,
                    brasilapi_cnaes_sec = $5,
                    brasilapi_raw = $6,
                    brasilapi_status = 'success',
                    brasilapi_ at = NOW()
                WHERE id = $7
            """, data['razao_social'], data['nome_fantasia'], 
                 data['descricao_situacao_cadastral'], 
                 data['qsa'], data['cnaes_secundarios'],
                 data, empresa['id'])
            
            await asyncio.sleep(0.6)  # Rate limit
            
        except Exception as e:
            await mark_as_error(empresa['id'], str(e))

async def enrich_enderecos_job():
    """Enriquece CEPs com dados + geolocalização"""
    enderecos = await db.fetch("""
        SELECT id, cep 
        FROM enderecos 
        WHERE cep IS NOT NULL
          AND brasilapi_status IS NULL
        LIMIT 100
    """)
    
    for endereco in enderecos:
        try:
            # BrasilAPI CEP V2 (com lat/long)
            data = await brasilapi_cep_v2(endereco['cep'])
            
            await db.execute("""
                UPDATE enderecos SET
                    logradouro = COALESCE(logradouro, $1),
                    bairro = COALESCE(bairro, $2),
                    cidade = COALESCE(cidade, $3),
                    uf = COALESCE(uf, $4),
                    latitude = $5,
                    longitude = $6,
                    brasilapi_raw = $7,
                    brasilapi_status = 'success',
                    brasilapi_updated_at = NOW()
                WHERE id = $8
            """, data['street'], data['neighborhood'],
                 data['city'], data['state'],
                 data['location']['coordinates']['latitude'],
                 data['location']['coordinates']['longitude'],
                 data, endereco['id'])
            
            await asyncio.sleep(0.6)
            
        except Exception as e:
            await mark_endereco_error(endereco['id'], str(e))
```

---

## 📋 PRÓXIMOS PASSOS

1. ✅ Criar migrations de DROP + novo schema
2. ✅ Criar scripts ETL otimizados
3. ✅ Implementar BrasilAPI integration
4. ✅ Testar com 10k registros
5. ✅ Executar carga completa 974k
6. ✅ Iniciar jobs de enriquecimento

---

**Pronto para iniciar implementação!**
