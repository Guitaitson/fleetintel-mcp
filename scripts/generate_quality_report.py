#!/usr/bin/env python3
"""
GT-30: Quality Report
Gera relatório de qualidade dos dados
"""
import asyncio
import os
import json
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from datetime import datetime
from pathlib import Path

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "").replace("postgresql://", "postgresql+asyncpg://", 1)
engine = create_async_engine(DATABASE_URL, echo=False)

async def generate_quality_report():
    """Gera relatório de qualidade"""
    print("=" * 60)
    print("📊 GT-30: QUALITY REPORT")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    report = {"timestamp": datetime.now().isoformat(), "metrics": {}}
    
    async with engine.connect() as conn:
        # Total de registros
        result = await conn.execute(text("SELECT COUNT(*) FROM registrations"))
        total = result.scalar()
        report["metrics"]["total_records"] = total
        print(f"\n📊 Total registros: {total:,}")
        
        # % NULL por coluna principal
        columns = ["chassi", "placa", "marca", "modelo", "data_emplacamento", 
                  "cpf_cnpj_proprietario", "nome_proprietario"]
        
        null_pcts = {}
        for col in columns:
            result = await conn.execute(text(f"""
                SELECT 
                    COUNT(*) FILTER (WHERE {col} IS NULL) * 100.0 / COUNT(*) as null_pct
                FROM registrations
            """))
            null_pct = result.scalar() or 0
            null_pcts[col] = round(null_pct, 2)
        
        report["metrics"]["null_percentages"] = null_pcts
        print(f"\n📉 % NULL por coluna:")
        for col, pct in null_pcts.items():
            print(f"   - {col}: {pct}%")
        
        # Distribuição por ano
        result = await conn.execute(text("""
            SELECT ano_modelo, COUNT(*) 
            FROM registrations 
            WHERE ano_modelo IS NOT NULL
            GROUP BY ano_modelo
            ORDER BY ano_modelo DESC
            LIMIT 10
        """))
        year_dist = {row[0]: row[1] for row in result}
        report["metrics"]["year_distribution"] = year_dist
        
        # Quality Score (0-100)
        avg_null = sum(null_pcts.values()) / len(null_pcts)
        quality_score = max(0, 100 - avg_null)
        report["quality_score"] = round(quality_score, 2)
        
        print(f"\n✨ Quality Score: {quality_score:.2f}/100")
    
    # Salvar relatórios
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    # JSON
    json_file = reports_dir / "quality_report.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n💾 JSON salvo: {json_file}")
    
    # Markdown
    md_file = reports_dir / "quality_report.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(f"# Quality Report\n\n")
        f.write(f"**Data:** {report['timestamp']}\n\n")
        f.write(f"## Quality Score: {report['quality_score']}/100\n\n")
        f.write(f"**Total de Registros:** {report['metrics']['total_records']:,}\n\n")
        f.write(f"## % NULL por Coluna\n\n")
        for col, pct in report['metrics']['null_percentages'].items():
            f.write(f"- **{col}**: {pct}%\n")
    print(f"💾 Markdown salvo: {md_file}")
    
    print(f"\n🎉 Relatório gerado com sucesso!")

if __name__ == "__main__":
    asyncio.run(generate_quality_report())
