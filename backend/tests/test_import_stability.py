"""
模块导入稳定性测试。

这些导入路径常被脚本、迁移校验和交互式排障直接使用，需要避免包级循环导入。
"""
import importlib
import subprocess
import sys


def test_direct_schema_and_model_imports_are_stable():
    module_names = [
        "app.schemas.post",
        "app.schemas.user",
        "app.schemas.event",
        "app.models.user",
        "app.models.event",
        "app.db.base",
        "app.db.session",
        "app.core.config",
    ]

    for module_name in module_names:
        importlib.import_module(module_name)


def test_database_imports_are_stable_in_fresh_process():
    """Alembic 会从 app.db.base 入口导入，需防止包级循环导入。"""
    subprocess.run(
        [
            sys.executable,
            "-c",
            "import app.db.base; import app.db.session; import app.core.config",
        ],
        check=True,
    )
