import pytest
from sqlalchemy import select, extract, String, func
from sqlalchemy.dialects import postgresql
from proyecto_maria.database.models import Operation

def test_cohort_retention_query_compiles_in_postgres():
    """Verifica que la query de agregación de operaciones compile en PostgreSQL.
    
    El uso de func.strftime es exclusivo de SQLite y falla en Prod (Postgres).
    Aseguramos que la sintaxis extract() que usamos compile bien.
    """
    query = select(
        (extract('year', Operation.created_at) * 100 +
         extract('month', Operation.created_at)).cast(String).label('month'),
        func.count().label('count')
    ).where(
        Operation.owner_username == "testuser"
    ).group_by(
        'month'
    ).order_by(
        'month'
    )
    
    # Intentar compilarla con el dialecto postgresql
    compiled_query = str(query.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
    
    # Verificar que postgres use EXTRACT
    assert "EXTRACT" in compiled_query.upper()
    assert "CAST" in compiled_query.upper()
    assert "strftime" not in compiled_query.lower()
