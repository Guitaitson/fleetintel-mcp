# Guardrails de Consulta - FleetIntel MCP

## Filtros Obrigatórios
- **UF (estado)**: Sempre obrigatório
- **Período**: Máximo de 90 dias por consulta
- **Tipo de veículo**: Opcional mas recomendado
- **Status**: Opcional (ativo/inativo/manutenção)

## Limites de Volume
- Máximo de registros por consulta: 100
- Máximo de consultas por usuário/hora: 20
- Máximo de consultas por usuário/dia: 200
- Timeout de query: 30 segundos

## Regras de Validação
1. Validação de filtros obrigatórios via schema Pydantic
2. Truncamento automático de resultados acima do limite
3. Notificação ao usuário: "Resultados truncados em 100 registros"

## Queries Proibidas
- "Liste todos os veículos" (sem filtro de UF)
- Períodos maiores que 90 dias
- Tentativas de bypass de limites (ex: múltiplas consultas consecutivas)

## Schema de Validação (Exemplo Pydantic)
```python
from pydantic import BaseModel, Field
from datetime import date

class BaseQueryParams(BaseModel):
    uf: str = Field(..., description="UF obrigatória (ex: SP, RJ)")
    start_date: date = Field(..., description="Data inicial (YYYY-MM-DD)")
    end_date: date = Field(..., description="Data final (YYYY-MM-DD)")
    vehicle_type: str | None = Field(None, description="Tipo de veículo (opcional)")
    status: str | None = Field(None, description="Status do veículo (opcional)")
    limit: int = Field(100, le=100, description="Máximo 100 registros")
```

## Exemplos
- **Válido**: 
  "Veículos em SP entre 2026-01-01 e 2026-01-07, tipo caminhão"
- **Inválido**: 
  "Todos os veículos ativos"
