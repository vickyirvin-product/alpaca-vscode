"""
Simple test script to verify authentication setup.
Run this after setting up your .env file to check for configuration issues.
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    try:
        from config import settings
        print("✓ Config imported successfully")
        
        from database import Database, get_db
        print("✓ Database module imported successfully")
        
        from models.user import User, UserCreate, Token, TokenData
        print("✓ User models imported successfully")
        
        from auth.security import (
            create_access_token,
            create_refresh_token,
            decode_token,
            verify_token
        )
        print("✓ Security module imported successfully")
        
        from routes.auth import router
        print("✓ Auth routes imported successfully")
        
        from main import app
        print("✓ Main app imported successfully")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_config():
    """Test configuration settings."""
    print("\nTesting configuration...")
    try:
        from config import settings
        
        # Check required settings
        required = [
            'mongo_uri',
            'database_name',
            'google_client_id',
            'google_client_secret',
            'jwt_secret_key'
        ]
        
        missing = []
        for setting in required:
            value = getattr(settings, setting, None)
            if not value or value.startswith('your_'):
                missing.append(setting)
        
        if missing:
            print(f"✗ Missing or placeholder values for: {', '.join(missing)}")
            print("  Please update your .env file with actual values")
            return False
        else:
            print("✓ All required configuration values are set")
            return True
            
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False


def test_jwt_creation():
    """Test JWT token creation."""
    print("\nTesting JWT token creation...")
    try:
        from auth.security import create_access_token, create_refresh_token, decode_token
        
        # Create test tokens
        test_data = {"sub": "test@example.com"}
        access_token = create_access_token(test_data)
        refresh_token = create_refresh_token(test_data)
        
        print(f"✓ Access token created: {access_token[:50]}...")
        print(f"✓ Refresh token created: {refresh_token[:50]}...")
        
        # Verify token can be decoded
        payload = decode_token(access_token)
        if payload.sub == "test@example.com" and payload.type == "access":
            print("✓ Token decoded successfully")
            return True
        else:
            print("✗ Token payload incorrect")
            return False
            
    except Exception as e:
        print(f"✗ JWT test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Authentication Setup Verification")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Configuration", test_config()))
    results.append(("JWT Creation", test_jwt_creation()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n✓ All tests passed! Your authentication setup is ready.")
        print("\nNext steps:")
        print("1. Start MongoDB: mongod")
        print("2. Run the server: uvicorn backend.main:app --reload")
        print("3. Visit: http://localhost:8000/docs")
        print("4. Test OAuth: http://localhost:8000/auth/login/google")
    else:
        print("\n✗ Some tests failed. Please fix the issues above.")
        print("\nCommon issues:")
        print("- Missing .env file (copy from .env.example)")
        print("- Placeholder values in .env (update with real credentials)")
        print("- Missing dependencies (run: pip install -r requirements.txt)")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())