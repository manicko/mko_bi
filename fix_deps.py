with open("src/mko_bi/api/deps.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace the exception handling
old = """    except Exception as e:
        logger.warning("Ошибка аутентификации: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не удалось аутентифицировать пользователя",
            headers={"WWW-Authenticate": "Bearer"},
        )"""

new = """    except AuthenticationError:
        # AuthenticationError уже залогирована в get_current_user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не удалось аутентифицировать пользователя",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error("Неожиданная ошибка аутентификации: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера",
        )"""

content = content.replace(old, new)

with open("src/mko_bi/api/deps.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed exception handling")
