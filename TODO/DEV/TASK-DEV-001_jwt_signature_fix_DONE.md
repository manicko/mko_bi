TASK: Fix JWT signature verification in dash_app.py

FILE: src/mko_bi/dash_app.py

GOAL: Remove security risk from disabled JWT signature verification

IMPLEMENT:

func: remove_or_fix_decode_token_payload()

LOGIC:

проверить использование функции decode_token_payload() во всем коде
если функция используется - заменить на validate_jwt_token() с проверкой подписи
если функция не используется - удалить её полностью
оставить только validate_jwt_token() которая использует decode_token() из core/security.py

CONSTRAINTS:

функция decode_token_payload() с verify_signature: False является security risk
использовать только проверенные функции: validate_jwt_token() или decode_token() из core/security

DONE:

 функция decode_token_payload() удалена или исправлена
 все JWT проверки используют валидную подпись
 тест на проверку JWT аутентификации
