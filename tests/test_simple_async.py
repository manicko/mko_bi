"""Simple test to debug async connection."""



async def test_simple_async(async_db_session):
    """Simple test to verify async session works."""
    from sqlalchemy import text
    
    result = await async_db_session.execute(text("SELECT 1"))
    row = result.scalar()
    assert row == 1
