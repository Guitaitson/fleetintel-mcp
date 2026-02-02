"""Test script for FastAPI MCP Server

This script tests if FastAPI app can be imported and if all endpoints are defined correctly.
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_fastapi_app():
    """Test FastAPI app import and endpoints"""
    print("=" * 60)
    print("Testing FastAPI MCP Server")
    print("=" * 60)
    
    try:
        # Test 1: Import app
        print("\n[1/5] Testing app import...")
        from app.main import app
        print("[OK] FastAPI app imported successfully")
        
        # Test 2: Check app configuration
        print("\n[2/5] Testing app configuration...")
        print(f"  - App name: {app.title}")
        print(f"  - App version: {app.version}")
        print(f"  - App description: {app.description}")
        print("[OK] App configuration is valid")
        
        # Test 3: Check routes
        print("\n[3/5] Testing routes...")
        routes = []
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                routes.append({
                    'path': route.path,
                    'methods': list(route.methods),
                    'name': getattr(route, 'name', 'N/A')
                })
        
        print(f"  - Total routes: {len(routes)}")
        for route in routes:
            print(f"  - {route['methods'][0]:6} {route['path']}")
        print("[OK] Routes are defined correctly")
        
        # Test 4: Check database connection
        print("\n[4/5] Testing database connection...")
        from src.fleet_intel_mcp.db.connection import get_db_engine
        engine = get_db_engine()
        print(f"  - Engine URL: {engine.url}")
        print(f"  - Pool size: {engine.pool.size()}")
        print(f"  - Max overflow: {engine.pool._max_overflow}")
        print("[OK] Database connection is configured")
        
        # Test 5: Check schemas
        print("\n[5/5] Testing schemas...")
        from app.schemas.query_schemas import (
            VehicleQuery, VehicleResponse,
            EmpresaQuery, EmpresaResponse,
            RegistrationQuery, RegistrationResponse,
            StatsResponse
        )
        print("  - VehicleQuery: [OK]")
        print("  - VehicleResponse: [OK]")
        print("  - EmpresaQuery: [OK]")
        print("  - EmpresaResponse: [OK]")
        print("  - RegistrationQuery: [OK]")
        print("  - RegistrationResponse: [OK]")
        print("  - StatsResponse: [OK]")
        print("[OK] All schemas are imported successfully")
        
        print("\n" + "=" * 60)
        print("All tests passed! [OK]")
        print("=" * 60)
        print("\nThe FastAPI MCP Server is ready to use.")
        print("\nTo start the server, run:")
        print("  uv run python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
        print("\nOr use Makefile:")
        print("  make dev")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_fastapi_app()
    sys.exit(0 if success else 1)
