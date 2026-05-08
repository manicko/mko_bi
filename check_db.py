import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def check_db():
    engine = create_async_engine("postgresql+asyncpg://postgres:1234@localhost:5432/bidb_test")
    async with engine.connect() as conn:
        # Check if config column exists
        result = await conn.execute(
            text(
                "SELECT column_name, data_type FROM information_schema.columns "
                "WHERE table_name='dashboards' ORDER BY ordinal_position"
            )
        )
        columns = list(result.fetchall())
        print("Columns in dashboards table:")
        for col in columns:
            print(f"  {col[0]}: {col[1]}")
        
        if not columns:
            print("Table dashboards does not exist or has no columns!")
        else:
            column_names = [col[0] for col in columns]
            if "config" not in column_names:
                print("\nERROR: config column does NOT exist!")
            else:
                print("\nSUCCESS: config column exists!")
    
    await engine.dispose()

asyncio.run(check_db())
