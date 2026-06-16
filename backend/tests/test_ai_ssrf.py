"""AI Provider base_url 的 SSRF 防护测试。

独立成文件，不引入 test_ai_housekeeper_api.py 里放行 host 检查的 autouse fixture，
确保这里用的是真实的 SSRF 校验逻辑。只断言"内网/环回/元数据 IP 被拒"——
用字面量 IP，不依赖外部 DNS，CI 无网络也能稳定运行。
"""
import pytest

from app.schemas.ai import AIProviderBase


@pytest.mark.parametrize(
    "url",
    [
        "http://169.254.169.254/v1",  # 云元数据地址
        "http://127.0.0.1:6379",  # 本地环回（如 Redis）
        "http://10.0.0.5/v1",  # 私网 10/8
        "http://192.168.1.10/v1",  # 私网 192.168/16
        "http://172.16.0.1/v1",  # 私网 172.16/12
    ],
)
def test_base_url_rejects_internal_addresses(url: str):
    """内网 / 环回 / 元数据地址必须被 SSRF 校验拒绝（抛 ValueError）。"""
    with pytest.raises(ValueError):
        AIProviderBase(base_url=url, name="测试", text_model="gpt-4o-mini")
