#!/usr/bin/env python3
"""
Test script to verify logging functionality.
Run this to check if logging is working properly.
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_logging():
    """Test the logging system."""
    print("Testing logging system...")
    
    try:
        # Test 1: Import logger
        print("✓ Testing logger import...")
        from utils.logger import logger, setup_logging
        
        # Test 2: Setup logging
        print("✓ Testing logging setup...")
        setup_logging()
        
        # Test 3: Test different log levels
        print("✓ Testing log levels...")
        logger.debug("This is a debug message")
        logger.info("This is an info message")
        logger.warning("This is a warning message")
        logger.error("This is an error message")
        
        # Test 4: Test structured logging
        print("✓ Testing structured logging...")
        logger.info("Test message", extra={"test": True, "data": {"key": "value"}})
        
        print("\n🎉 All logging tests passed!")
        print("Logging system is working correctly.")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        return False

def test_settings():
    """Test the settings configuration."""
    print("\nTesting settings configuration...")
    
    try:
        from config.settings import get_settings
        
        settings = get_settings()
        print(f"✓ Environment: {settings.environment}")
        print(f"✓ Debug mode: {settings.debug}")
        print(f"✓ Log level: {settings.log_level}")
        print(f"✓ Log format: {settings.log_format}")
        print(f"✓ OpenAI API key configured: {bool(settings.openai_api_key)}")
        print(f"✓ ElevenLabs API key configured: {bool(settings.elevenlabs_api_key)}")
        print(f"✓ Secret key configured: {bool(settings.secret_key)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Settings test failed: {e}")
        return False

def main():
    """Main test function."""
    print("🔍 Healthcare Voice AI - System Test")
    print("=" * 50)
    
    # Test logging
    logging_ok = test_logging()
    
    # Test settings
    settings_ok = test_settings()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"Logging System: {'✅ PASS' if logging_ok else '❌ FAIL'}")
    print(f"Settings Config: {'✅ PASS' if settings_ok else '❌ FAIL'}")
    
    if logging_ok and settings_ok:
        print("\n🎉 All systems are working correctly!")
        print("You can now run the main application: python main.py")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        print("Make sure your .env file is configured correctly.")

if __name__ == "__main__":
    main()
