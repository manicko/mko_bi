import pytest
from datetime import datetime, timedelta
from mko_bi.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
)
from jose.exceptions import JWTError


def test_hash_password():
    """Test password hashing function."""
    password = "secure_password_123"
    hashed = hash_password(password)

    # Check that hashed password is a string
    assert isinstance(hashed, str)
    # Check that it's not the original password
    assert hashed != password
    # Check that it follows bcrypt format
    assert hashed.startswith("$2b$")
    # Check that verification works
    assert verify_password(password, hashed) is True


def test_verify_password():
    """Test password verification function."""
    password = "another_password"
    wrong_password = "wrong_password"

    hashed = hash_password(password)

    # Correct password should verify
    assert verify_password(password, hashed) is True
    # Wrong password should not verify
    assert verify_password(wrong_password, hashed) is False


def test_hash_different_salts():
    """Test that same password produces different hashes due to salt."""
    password = "same_password"

    hash1 = hash_password(password)
    hash2 = hash_password(password)
    hash3 = hash_password(password)

    # All hashes should be different
    assert hash1 != hash2
    assert hash2 != hash3
    assert hash1 != hash3

    # But all should verify correctly
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True
    assert verify_password(password, hash3) is True


def test_edge_cases():
    """Test edge cases for password hashing."""
    # Empty password
    empty_hash = hash_password("")
    assert verify_password("", empty_hash) is True
    assert verify_password("not_empty", empty_hash) is False

    # Very long password (bcrypt truncates at 72 bytes)
    long_password = "x" * 1000
    long_hash = hash_password(long_password)
    assert verify_password(long_password, long_hash) is True
    # Changing a character within the first 72 bytes should fail verification
    assert (
        verify_password(long_password[:71] + "y" + long_password[72:], long_hash)
        is False
    )

    # Password with special characters
    special_password = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    special_hash = hash_password(special_password)
    assert verify_password(special_password, special_hash) is True
    assert verify_password(special_password + "x", special_hash) is False


def test_create_access_token():
    """Test JWT access token creation."""
    # Test data to encode
    test_data = {"user_id": 1, "email": "test@example.com"}

    # Create token
    token = create_access_token(test_data)

    # Verify token is a string
    assert isinstance(token, str)
    assert len(token) > 0

    # Decode token to verify contents
    decoded = decode_token(token)
    assert decoded["user_id"] == test_data["user_id"]
    assert decoded["email"] == test_data["email"]
    # Check that expiration is set
    assert "exp" in decoded


def test_decode_token():
    """Test JWT token decoding."""
    # Test data
    test_data = {"user_id": 2, "role": "admin"}

    # Create and decode token
    token = create_access_token(test_data)
    decoded = decode_token(token)

    # Verify decoded data matches original
    assert decoded["user_id"] == test_data["user_id"]
    assert decoded["role"] == test_data["role"]
    assert "exp" in decoded


def test_token_expiration():
    """Test token expiration handling."""
    # Test with negative expiration time to ensure token is expired
    from mko_bi.core.security import ACCESS_TOKEN_EXPIRE_MINUTES

    original_expire = ACCESS_TOKEN_EXPIRE_MINUTES

    # Temporarily set negative expiration
    import mko_bi.core.security as security_module

    security_module.ACCESS_TOKEN_EXPIRE_MINUTES = -5  # Expired 5 minutes ago

    try:
        test_data = {"user_id": 3}
        token = create_access_token(test_data)

        # Token should be invalid (expired)
        try:
            decode_token(token)
            assert False, "Token should have expired"
        except JWTError:
            # Expected - token is expired
            pass
    finally:
        # Restore original value
        security_module.ACCESS_TOKEN_EXPIRE_MINUTES = original_expire


def test_invalid_token():
    """Test handling of invalid tokens."""
    # Test with malformed token
    try:
        decode_token("invalid.token.string")
        assert False, "Should have raised JWTError"
    except JWTError:
        # Expected
        pass

    # Test with wrong secret key
    test_data = {"user_id": 4}

    # Create token with original secret
    token = create_access_token(test_data)

    # Try to decode with wrong key by temporarily patching the SECRET_KEY in security module
    import mko_bi.core.security as security_module
    import mko_bi.config as config_module

    # Save original values
    original_secret = security_module.SECRET_KEY

    # Temporarily change the secret key in the security module
    security_module.SECRET_KEY = "wrong-secret-key"

    try:
        try:
            decode_token(token)
            assert False, "Should have raised JWTError with wrong key"
        except JWTError:
            # Expected - token is invalid with wrong key
            pass
    finally:
        # Restore original secret key
        security_module.SECRET_KEY = original_secret
