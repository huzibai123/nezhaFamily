"""
统一密码强度校验。
"""

import re


COMMON_WEAK_PASSWORDS = {
    "123456",
    "12345678",
    "123456789",
    "password",
    "password1",
    "qwerty123",
    "admin123",
    "admin123456",
    "user123456",
}


def validate_password_strength(
    password: str,
    *,
    username: str | None = None,
    email: str | None = None,
) -> str:
    """校验家庭成员账号密码强度，返回原密码便于 Pydantic validator 使用。"""
    if len(password) < 10:
        raise ValueError("密码至少 10 位")

    normalized = password.lower()
    if normalized in COMMON_WEAK_PASSWORDS:
        raise ValueError("密码过于常见，请更换更安全的密码")

    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise ValueError("密码必须同时包含字母和数字")

    identifiers = []
    if username:
        identifiers.append(username)
    if email and "@" in email:
        identifiers.append(email.split("@", 1)[0])

    for identifier in identifiers:
        identifier = identifier.strip().lower()
        if len(identifier) >= 3 and identifier in normalized:
            raise ValueError("密码不能包含用户名或邮箱")

    return password
