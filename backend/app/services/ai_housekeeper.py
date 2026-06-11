"""
AI 家庭管家业务服务
"""
from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import mimetypes
import random
import secrets
from pathlib import Path
from typing import Iterable, Literal, Optional
from uuid import UUID

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import String, desc, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.media_utils import media_path_from_url, media_storage_path
from app.core.security import get_password_hash
from app.models.ai import (
    AIAlbumSuggestion,
    AIContentInsight,
    AIJob,
    AIPersona,
    AIProfile,
    AIProviderConfig,
    AIReportDraft,
)
from app.models.comment import Comment
from app.models.like import Like
from app.models.media import MediaFile
from app.models.notification import Notification
from app.models.post import Post
from app.models.user import User
from app.services.ai_client import AIProviderError, OpenAICompatibleClient

AI_DISABLED_MESSAGE = "AI 管家尚未启用"
SAFE_COMMENT = "看到这条新的家庭记忆，心里也跟着亮了一下。愿这些温柔的小瞬间被好好收藏。"
POSITIVE_WORDS = ("温暖", "可爱", "开心", "幸福", "珍贵", "美好", "喜欢", "收藏", "陪伴", "快乐")
UNSAFE_WORDS = ("讨厌", "糟糕", "丑", "笨", "病", "死亡", "吓人", "隐私", "诊断")
OFF_CONTEXT_FOOD_WORDS = ("烤肉", "烧烤", "肉香", "好香", "想吃", "开吃", "馋")
TOKEN_CONTEXT_WORDS = ("token", "Token", "TOKEN", "烧token", "烧 token", "烧Token", "烧 Token")
ENCRYPTED_KEY_PREFIX = "fernet:"
ENCRYPTED_KEY_V2_PREFIX = "fernet:v2:"
DEFAULT_WIRE_API = "chat_completions"
SUPPORTED_WIRE_APIS = {"chat_completions", "responses"}
POST_CAPTION_MAX_LENGTH = 180
AI_COMMENT_MAX_IMAGES = 2
AI_COMMENT_MAX_IMAGE_BYTES = 2 * 1024 * 1024


@dataclass(frozen=True)
class AIPostCaptionMediaInput:
    filename: str
    content_type: str
    media_type: Literal["image", "video"]
    data_url: Optional[str] = None


@dataclass(frozen=True)
class AICommentMediaContext:
    media_type: str
    url: str
    filename: str
    content_type: str
    data_url: Optional[str] = None


@dataclass(frozen=True)
class AICommentContext:
    author_label: str
    text: str
    media: list[AICommentMediaContext]
    profile_text: str

    @property
    def has_images(self) -> bool:
        return any(item.media_type == "image" for item in self.media)

    @property
    def has_visual_inputs(self) -> bool:
        return any(item.data_url for item in self.media)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


async def get_provider(db: AsyncSession) -> Optional[AIProviderConfig]:
    result = await db.execute(select(AIProviderConfig).order_by(desc(AIProviderConfig.created_at)).limit(1))
    return result.scalar_one_or_none()


async def get_or_create_provider(db: AsyncSession) -> AIProviderConfig:
    provider = await get_provider(db)
    if provider:
        return provider

    provider = AIProviderConfig(
        name="默认模型",
        base_url=settings.AI_DEFAULT_BASE_URL,
        api_key_encrypted=None,
        text_model=settings.AI_DEFAULT_TEXT_MODEL,
        vision_model=settings.AI_DEFAULT_VISION_MODEL,
        timeout_seconds=settings.AI_REQUEST_TIMEOUT_SECONDS,
        enabled=settings.AI_ENABLED,
        status="active" if settings.AI_ENABLED and settings.AI_API_KEY else "disabled",
    )
    db.add(provider)
    await db.flush()
    return provider


def provider_has_key(provider: AIProviderConfig) -> bool:
    return bool(provider.api_key_encrypted or settings.AI_API_KEY)


def provider_api_key_source(provider: AIProviderConfig) -> str:
    if provider.api_key_encrypted:
        return "database"
    if settings.AI_API_KEY:
        return "environment"
    return "none"


def provider_settings(provider: AIProviderConfig) -> dict:
    if isinstance(provider.settings, dict):
        return dict(provider.settings)
    return {}


def provider_wire_api(provider: AIProviderConfig) -> str:
    wire_api = provider_settings(provider).get("wire_api")
    if wire_api in SUPPORTED_WIRE_APIS:
        return wire_api
    return DEFAULT_WIRE_API


def provider_model_reasoning_effort(provider: AIProviderConfig) -> Optional[str]:
    value = provider_settings(provider).get("model_reasoning_effort")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def provider_disable_response_storage(provider: AIProviderConfig) -> bool:
    return bool(provider_settings(provider).get("disable_response_storage", False))


def provider_is_active(provider: Optional[AIProviderConfig]) -> bool:
    return bool(
        provider
        and provider.enabled
        and provider.status == "active"
        and provider_has_key(provider)
    )


async def ensure_default_personas(db: AsyncSession) -> list[AIPersona]:
    await db.execute(select(func.pg_advisory_xact_lock(0x4E455A484149)))
    existing_result = await db.execute(select(AIPersona).order_by(AIPersona.sort_order))
    existing = list(existing_result.scalars().all())
    if existing:
        for persona in existing:
            if not isinstance(persona.persona_metadata, dict) or "auto_like_enabled" not in persona.persona_metadata:
                persona.auto_like_enabled = True
        return existing

    defaults = [
        {
            "name": "哪吒总管",
            "persona_type": "steward",
            "tone": "温暖、稳重、像家里的记忆管家。",
            "bio": "负责守护家庭记忆、生成回顾和温柔提醒。",
            "sort_order": 10,
        },
        {
            "name": "记忆嬷嬷",
            "persona_type": "nanny",
            "tone": "亲切、细腻、会夸人，像照看一家人的长辈。",
            "bio": "喜欢给照片和日常留下暖心评论。",
            "sort_order": 20,
        },
        {
            "name": "小金毛",
            "persona_type": "pet_dog",
            "tone": "活泼、真诚、短句、像陪在家里的小伙伴。",
            "bio": "负责把家庭动态夸得开心一点。",
            "sort_order": 30,
        },
    ]
    personas = []
    for item in defaults:
        user = await create_system_user_for_persona(db, item["name"], item["persona_type"])
        persona = AIPersona(user_id=user.id, enabled=True, auto_comment_enabled=True, **item)
        persona.auto_like_enabled = True
        db.add(persona)
        personas.append(persona)
    await db.flush()
    return personas


async def create_system_user_for_persona(db: AsyncSession, name: str, persona_type: str) -> User:
    base_username = _slugify_persona_name(name)
    index = 1
    while True:
        username = base_username if index == 1 else f"{base_username}_{index}"
        email = f"{username}@ai.nezha.local"
        existing_user = await _find_user_by_username_or_email(db, username, email)
        if not existing_user:
            break
        if existing_user.is_system and existing_user.system_type == "ai_persona":
            if not await _system_user_has_persona(db, existing_user.id):
                return existing_user
        index += 1

    user = User(
        username=username,
        email=email,
        password_hash=get_password_hash(secrets.token_urlsafe(32)),
        role="member",
        is_system=True,
        system_type="ai_persona",
        avatar_url=None,
        bio=f"AI 家庭角色：{name}",
        role_in_family=persona_type,
    )
    db.add(user)
    await db.flush()
    return user


async def _find_user_by_username_or_email(db: AsyncSession, username: str, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(or_(User.username == username, User.email == email)))
    return result.scalar_one_or_none()


async def _system_user_has_persona(db: AsyncSession, user_id: UUID) -> bool:
    result = await db.execute(select(AIPersona.id).where(AIPersona.user_id == user_id).limit(1))
    return result.scalar_one_or_none() is not None


def _slugify_persona_name(name: str) -> str:
    suffix = int(hashlib.sha1(name.encode("utf-8")).hexdigest()[:8], 16) % 100000
    return f"ai_{suffix}"


async def pick_auto_comment_persona(db: AsyncSession) -> Optional[AIPersona]:
    await ensure_default_personas(db)
    result = await db.execute(
        select(AIPersona).where(
            AIPersona.enabled.is_(True),
            AIPersona.auto_comment_enabled.is_(True),
            AIPersona.user_id.is_not(None),
        )
    )
    personas = list(result.scalars().all())
    if not personas:
        return None
    return random.choice(personas)


async def pick_auto_like_persona(db: AsyncSession) -> Optional[AIPersona]:
    await ensure_default_personas(db)
    result = await db.execute(
        select(AIPersona).where(
            AIPersona.enabled.is_(True),
            AIPersona.user_id.is_not(None),
        )
    )
    personas = [persona for persona in result.scalars().all() if persona.auto_like_enabled]
    if not personas:
        return None
    return random.choice(personas)


def build_client(
    provider: AIProviderConfig,
    *,
    model: Optional[str] = None,
) -> OpenAICompatibleClient:
    api_key = resolve_provider_api_key(provider)
    return OpenAICompatibleClient(
        base_url=provider.base_url,
        api_key=api_key,
        model=model or provider.text_model,
        timeout_seconds=provider.timeout_seconds or settings.AI_REQUEST_TIMEOUT_SECONDS,
        wire_api=provider_wire_api(provider),
        reasoning_effort=provider_model_reasoning_effort(provider),
        disable_response_storage=provider_disable_response_storage(provider),
    )


def encrypt_ai_api_key(api_key: str) -> str:
    if settings.AI_KEY_ENCRYPTION_SECRET:
        token = _ai_key_cipher(settings.AI_KEY_ENCRYPTION_SECRET).encrypt(
            api_key.encode("utf-8")
        ).decode("utf-8")
        return f"{ENCRYPTED_KEY_V2_PREFIX}{token}"

    token = _ai_key_cipher(settings.SECRET_KEY).encrypt(api_key.encode("utf-8")).decode("utf-8")
    return f"{ENCRYPTED_KEY_PREFIX}{token}"


def resolve_provider_api_key(provider: AIProviderConfig) -> str:
    if not provider.api_key_encrypted:
        return settings.AI_API_KEY
    if provider.api_key_encrypted.startswith(ENCRYPTED_KEY_V2_PREFIX):
        token = provider.api_key_encrypted.removeprefix(ENCRYPTED_KEY_V2_PREFIX)
        try:
            return _ai_key_cipher(settings.AI_KEY_ENCRYPTION_SECRET).decrypt(
                token.encode("utf-8")
            ).decode("utf-8")
        except InvalidToken as exc:
            raise AIProviderError("模型 API Key 解密失败，请重新保存配置", status_code=401) from exc
    if not provider.api_key_encrypted.startswith(ENCRYPTED_KEY_PREFIX):
        return provider.api_key_encrypted
    token = provider.api_key_encrypted.removeprefix(ENCRYPTED_KEY_PREFIX)
    try:
        return _ai_key_cipher(settings.SECRET_KEY).decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise AIProviderError("模型 API Key 解密失败，请重新保存配置", status_code=401) from exc


def _ai_key_cipher(secret: str) -> Fernet:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


async def pause_provider_for_error(
    db: AsyncSession,
    provider: AIProviderConfig,
    error: AIProviderError,
) -> None:
    provider.failure_count = (provider.failure_count or 0) + 1
    provider.last_error = str(error)[:1000]
    provider.last_checked_at = now_utc()

    status = _status_for_error(error)
    if status in {"paused_billing_or_auth", "paused_rate_limit"} or provider.failure_count >= settings.AI_FAILURE_THRESHOLD:
        provider.enabled = False
        provider.status = status if status != "active" else "paused_error"
        provider.paused_reason = _reason_for_status(provider.status)
        await notify_admins_ai_paused(db, provider)
    await db.flush()


def _status_for_error(error: AIProviderError) -> str:
    if error.status_code in {401, 402, 403}:
        return "paused_billing_or_auth"
    if error.status_code == 429:
        return "paused_rate_limit"
    return "paused_error"


def _reason_for_status(status: str) -> str:
    if status == "paused_billing_or_auth":
        return "模型 API 鉴权失败、欠费或余额不足"
    if status == "paused_rate_limit":
        return "模型 API 被限流"
    return "模型 API 连续调用失败"


async def notify_admins_ai_paused(db: AsyncSession, provider: AIProviderConfig) -> None:
    if provider.notified_pause_at:
        return

    admins_result = await db.execute(select(User.id).where(User.role == "admin", User.is_system.is_(False)))
    admin_ids = list(admins_result.scalars().all())
    if not admin_ids:
        return

    actor = await ensure_ai_notification_actor(db)
    message = (
        f"AI 管家已暂停：{provider.paused_reason or '模型服务不可用'}。"
        f"请检查 {provider.name} / {provider.text_model} 的 API 配置。"
    )
    for admin_id in set(admin_ids):
        if admin_id == actor.id:
            continue
        existing_result = await db.execute(
            select(Notification.id).where(
                Notification.recipient_id == admin_id,
                Notification.actor_id == actor.id,
                Notification.type == "ai_paused",
                Notification.target_type == "ai_provider",
                Notification.target_id == provider.id,
            )
        )
        if existing_result.scalar_one_or_none():
            continue
        db.add(
            Notification(
                recipient_id=admin_id,
                actor_id=actor.id,
                type="ai_paused",
                target_type="ai_provider",
                target_id=provider.id,
                message=message,
                is_read=False,
            )
        )
    provider.notified_pause_at = now_utc()


async def ensure_ai_notification_actor(db: AsyncSession) -> User:
    result = await db.execute(
        select(User).where(User.is_system.is_(True), User.system_type == "ai_system").limit(1)
    )
    actor = result.scalar_one_or_none()
    if actor:
        return actor

    actor = User(
        username="ai_system",
        email="ai_system@ai.nezha.local",
        password_hash=get_password_hash(secrets.token_urlsafe(32)),
        role="member",
        is_system=True,
        system_type="ai_system",
        bio="AI 管家系统通知账号",
        role_in_family="AI 管家",
    )
    db.add(actor)
    await db.flush()
    return actor


async def test_provider_connection(db: AsyncSession, provider: AIProviderConfig) -> tuple[bool, str]:
    if not provider_has_key(provider):
        return False, "未配置 API Key"

    was_enabled = bool(provider.enabled)
    try:
        client = build_client(provider)
        await client.chat(
            [
                {"role": "system", "content": "你是一个连接测试助手，只回复 OK。"},
                {"role": "user", "content": "请回复 OK"},
            ],
            temperature=0,
            max_tokens=20,
        )
    except AIProviderError as error:
        if was_enabled and error.status_code in {401, 402, 403, 429}:
            await pause_provider_for_error(db, provider, error)
        else:
            provider.last_error = str(error)[:1000]
            provider.last_checked_at = now_utc()
            await db.flush()
        return False, str(error)

    provider.status = "active" if was_enabled else "disabled"
    provider.failure_count = 0
    provider.last_error = None
    provider.paused_reason = None
    provider.notified_pause_at = None
    provider.last_checked_at = now_utc()
    await db.flush()
    if was_enabled:
        return True, "连接测试成功"
    return True, "连接可用，当前未启用"


async def generate_ai_comment_for_post(db: AsyncSession, post_id: UUID) -> Optional[Comment]:
    provider = await get_provider(db)
    if not provider_is_active(provider):
        return None

    post_result = await db.execute(select(Post).where(Post.id == post_id).with_for_update())
    post = post_result.scalar_one_or_none()
    if not post:
        return None

    await create_ai_like_for_post(db, post)

    existing = await db.execute(
        select(Comment.id).where(
            Comment.post_id == post_id,
            Comment.is_ai_generated.is_(True),
        ).limit(1)
    )
    if existing.scalar_one_or_none():
        return None

    persona = await pick_auto_comment_persona(db)
    if not persona or not persona.user_id:
        return None

    author = await db.get(User, post.author_id)
    context = await build_post_context(db, post, author, include_image_data=bool(provider.vision_model))
    comment_model = provider.vision_model if context.has_visual_inputs else provider.text_model
    try:
        client = build_client(provider, model=comment_model)
    except AIProviderError as error:
        await pause_provider_for_error(db, provider, error)
        return None
    comment_text = SAFE_COMMENT
    attempts: list[dict[str, str | int | bool]] = []

    for attempt in range(1, 4):
        try:
            result = await client.chat(
                build_comment_prompt(persona, context, previous_comment=None if attempt == 1 else comment_text),
                temperature=0.7,
                max_tokens=180,
            )
        except AIProviderError as error:
            await pause_provider_for_error(db, provider, error)
            return None

        candidate = normalize_comment(result.content)
        ok, reason = validate_positive_comment(candidate, context)
        attempts.append({"attempt": attempt, "ok": ok, "reason": reason, "content": candidate})
        if ok:
            comment_text = candidate
            break
        comment_text = candidate or SAFE_COMMENT
    else:
        comment_text = SAFE_COMMENT

    comment = Comment(
        post_id=post.id,
        author_id=persona.user_id,
        content=comment_text,
        is_ai_generated=True,
        ai_persona_id=persona.id,
        ai_generation_metadata={
            "provider_id": str(provider.id),
            "model": comment_model,
            "attempts": attempts,
            "fallback": comment_text == SAFE_COMMENT,
            "used_visual_inputs": context.has_visual_inputs,
        },
    )
    db.add(comment)
    await db.execute(update(Post).where(Post.id == post.id).values(comment_count=Post.comment_count + 1))
    provider.failure_count = 0
    provider.last_error = None
    await db.flush()
    return comment


async def create_ai_like_for_post(db: AsyncSession, post: Post) -> Optional[Like]:
    from app.api.notifications import build_like_post_message, create_notification

    existing_ai_like = await db.execute(
        select(Like.id)
        .join(User, Like.user_id == User.id)
        .where(
            Like.target_type == "post",
            Like.target_id == post.id,
            User.is_system.is_(True),
            User.system_type.in_(("ai_persona", "ai_system")),
        )
        .limit(1)
    )
    if existing_ai_like.scalar_one_or_none():
        return None

    persona = await pick_auto_like_persona(db)
    if not persona or not persona.user_id:
        return None

    actor = await db.get(User, persona.user_id)
    if not actor or not actor.is_system:
        return None

    like = Like(user_id=actor.id, target_type="post", target_id=post.id)
    db.add(like)
    await create_notification(
        db,
        recipient_id=post.author_id,
        actor=actor,
        notification_type="like_post",
        target_type="post",
        target_id=post.id,
        post_id=post.id,
        message=build_like_post_message(actor),
        dedupe=True,
    )
    await db.flush()
    return like


async def generate_post_caption(
    db: AsyncSession,
    *,
    mode: Literal["polish", "generate"],
    content: str,
    media: list[AIPostCaptionMediaInput],
) -> str:
    provider = await get_provider(db)
    if not provider_is_active(provider):
        raise ValueError(AI_DISABLED_MESSAGE)

    normalized_content = content.strip()
    if not normalized_content and not media:
        raise ValueError("请先写一点内容，或添加图片/视频")

    model = provider.vision_model if media and provider.vision_model else provider.text_model
    try:
        client = build_client(provider, model=model)
    except AIProviderError as error:
        await pause_provider_for_error(db, provider, error)
        raise

    messages = build_post_caption_prompt(mode, normalized_content, media)
    try:
        result = await client.chat(messages, temperature=0.55, max_tokens=220)
    except AIProviderError as error:
        if _can_fallback_post_caption_to_text(media, error):
            try:
                fallback_client = build_client(provider, model=provider.text_model)
                result = await fallback_client.chat(
                    build_post_caption_prompt(
                        mode,
                        normalized_content,
                        strip_post_caption_media_data(media),
                    ),
                    temperature=0.55,
                    max_tokens=220,
                )
            except AIProviderError as fallback_error:
                await pause_provider_for_error(db, provider, fallback_error)
                raise fallback_error from error
        else:
            await pause_provider_for_error(db, provider, error)
            raise

    provider.failure_count = 0
    provider.last_error = None
    await db.flush()
    return normalize_post_caption(result.content)


def _can_fallback_post_caption_to_text(
    media: list[AIPostCaptionMediaInput],
    error: AIProviderError,
) -> bool:
    return bool(
        media
        and any(item.data_url for item in media)
        and error.status_code not in {401, 402, 403, 429}
    )


def strip_post_caption_media_data(
    media: list[AIPostCaptionMediaInput],
) -> list[AIPostCaptionMediaInput]:
    return [
        AIPostCaptionMediaInput(
            filename=item.filename,
            content_type=item.content_type,
            media_type=item.media_type,
        )
        for item in media
    ]


def build_post_caption_prompt(
    mode: Literal["polish", "generate"],
    content: str,
    media: list[AIPostCaptionMediaInput],
) -> list[dict[str, object]]:
    system_prompt = (
        "你是哪吒家庭私有时间线里的文案助手。"
        "只为家庭成员生成中文文案，语气自然、温暖、像真实家人记录日常。"
        "不要自称 AI 或大模型，不要写标签、Markdown、标题或解释。"
        "不要凭空编造人物身份、地点、病情、隐私事实；看不确定的内容就用更稳妥的描述。"
        f"只输出一段 {POST_CAPTION_MAX_LENGTH} 字以内的文案。"
    )
    media_lines = [
        f"- {item.media_type}: {item.filename or '未命名媒体'} ({item.content_type or 'unknown'})"
        for item in media
    ]
    if mode == "polish" and content:
        task = (
            "请润色下面这段家庭动态文案，保留原意和事实，让它更顺口、更温暖，"
            "不要添加原文和媒体里没有的信息。"
        )
    else:
        task = (
            "请根据已选择的图片/视频，为这条家庭动态写一段可直接发布的文案。"
            "如果只有视频元信息或看不清具体内容，就写得通用但真诚。"
        )

    text_prompt = "\n".join(
        [
            task,
            "",
            f"原文：{content or '无'}",
            "媒体：",
            "\n".join(media_lines) or "- 无",
        ]
    )
    if not media:
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text_prompt},
        ]

    user_content: list[dict[str, object]] = [{"type": "text", "text": text_prompt}]
    for item in media:
        if item.media_type == "image" and item.data_url:
            user_content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": item.data_url},
                }
            )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]


def normalize_post_caption(content: str) -> str:
    cleaned = " ".join(content.strip().strip('"“”`').split())
    if len(cleaned) > POST_CAPTION_MAX_LENGTH:
        cleaned = cleaned[:POST_CAPTION_MAX_LENGTH].rstrip("，。,. ")
    if not cleaned:
        raise AIProviderError("模型返回了空内容")
    return cleaned


async def build_post_context(
    db: AsyncSession,
    post: Post,
    author: Optional[User],
    *,
    include_image_data: bool = True,
) -> AICommentContext:
    media_items = post.media_urls or []
    media_context = [
        item for item in build_comment_media_context(media_items, include_image_data=include_image_data) if item
    ]
    recent_profiles = await db.execute(select(AIProfile).order_by(desc(AIProfile.updated_at)).limit(5))
    profile_text = "\n".join(
        f"- {profile.title}: {profile.summary or profile.editable_notes or ''}"
        for profile in recent_profiles.scalars().all()
    )
    return AICommentContext(
        author_label=author.role_in_family or author.username if author else "家人",
        text=post.content or "",
        media=media_context,
        profile_text=profile_text,
    )


def build_comment_media_context(
    media_items: list[object],
    *,
    include_image_data: bool = True,
) -> list[AICommentMediaContext]:
    contexts: list[AICommentMediaContext] = []
    image_data_count = 0
    for item in media_items[:5]:
        if not isinstance(item, dict):
            continue
        media_type = str(item.get("type") or "media")
        url = str(item.get("url") or "")
        filename = Path(media_path_from_url(url)).name if url else ""
        content_type = guess_media_content_type(url, media_type)
        data_url: Optional[str] = None
        if include_image_data and media_type == "image" and image_data_count < AI_COMMENT_MAX_IMAGES:
            data_url = load_comment_image_data_url(url, content_type)
            if data_url:
                image_data_count += 1
        contexts.append(
            AICommentMediaContext(
                media_type=media_type,
                url=url,
                filename=filename or "未命名媒体",
                content_type=content_type,
                data_url=data_url,
            )
        )
    return contexts


def guess_media_content_type(url: str, media_type: str) -> str:
    guessed_type, _ = mimetypes.guess_type(media_path_from_url(url))
    if guessed_type:
        return guessed_type
    if media_type == "image":
        return "image/jpeg"
    if media_type == "video":
        return "video/mp4"
    return "application/octet-stream"


def load_comment_image_data_url(url: str, content_type: str) -> Optional[str]:
    if not url:
        return None
    try:
        image_path = media_storage_path(media_path_from_url(url))
        if not image_path.is_file() or image_path.stat().st_size > AI_COMMENT_MAX_IMAGE_BYTES:
            return None
        data = image_path.read_bytes()
    except (OSError, ValueError):
        return None
    return f"data:{content_type};base64,{base64.b64encode(data).decode('ascii')}"


def comment_context_text(context: AICommentContext) -> str:
    media_lines = [
        f"- {item.media_type}: {item.filename} ({item.content_type})"
        for item in context.media
    ]
    visual_note = (
        "已附带图片视觉输入，请只评论你能从图片和文案中确认的内容。"
        if context.has_visual_inputs
        else (
            "未提供可看的图片内容；不要猜测图片里有什么，只能依据文字和媒体类型做通用正向回应。"
            if context.has_images
            else "无图片视觉输入。"
        )
    )
    return "\n".join(
        [
            f"作者：{context.author_label}",
            f"帖子文字：{context.text.strip() or '无文字说明'}",
            "媒体：",
            "\n".join(media_lines) or "- 无媒体",
            f"视觉说明：{visual_note}",
            "已有家庭画像摘要：",
            context.profile_text or "- 暂无",
        ]
    )


def build_comment_prompt(
    persona: AIPersona,
    context: AICommentContext,
    previous_comment: Optional[str],
) -> list[dict[str, object]]:
    system_prompt = (
        f"你是家庭私有平台里的 AI 角色「{persona.name}」。"
        f"你的性格/语气：{persona.tone or '温暖、真诚、简短'}。"
        "你要为家人的新帖子写一条正向评论。必须贴合事实，宁可朴素也不要脑补。"
        "如果帖子没有图片，只能根据帖子文字评论；如果有图片且提供视觉输入，可以结合图片中明确可见的内容评论；"
        "如果只有视频或图片不可见，只能写通用正向回应，不描述具体画面。"
        "不要把网络梗、技术词或比喻当成真实事件，例如“烧 token/烧钱/烧卡”不能解读成烧烤、烤肉或食物。"
        "要求：中文，30字以内，真诚、具体、积极，不要批评、诊断、吓人、泄露隐私，不要自称大模型。"
    )
    user_prompt = f"帖子上下文：\n{comment_context_text(context)}\n\n请写一条评论。"
    if previous_comment:
        user_prompt += f"\n上一版不够合适：{previous_comment}\n请重新写得更自然、更正向。"
    if not context.has_visual_inputs:
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    user_content: list[dict[str, object]] = [{"type": "text", "text": user_prompt}]
    for item in context.media:
        if item.data_url:
            user_content.append({"type": "image_url", "image_url": {"url": item.data_url}})
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]


def normalize_comment(content: str) -> str:
    content = content.strip().strip('"“”')
    return " ".join(content.split())[:120]


def validate_positive_comment(
    content: str,
    context: Optional[AICommentContext] = None,
) -> tuple[bool, str]:
    if not content:
        return False, "empty"
    if len(content) > 80:
        return False, "too_long"
    if any(word in content for word in UNSAFE_WORDS):
        return False, "unsafe_word"
    if context and is_comment_off_context(content, context):
        return False, "off_context"
    if not any(word in content for word in POSITIVE_WORDS) and not content.endswith(("呀", "呢", "～", "！", "!")):
        return False, "not_positive_enough"
    return True, "ok"


def is_comment_off_context(content: str, context: AICommentContext) -> bool:
    post_text = context.text or ""
    if any(word in post_text for word in TOKEN_CONTEXT_WORDS) and any(
        word in content for word in OFF_CONTEXT_FOOD_WORDS
    ):
        return True
    if not context.has_visual_inputs and any(word in content for word in OFF_CONTEXT_FOOD_WORDS):
        food_cues = ("饭", "菜", "吃", "餐", "肉", "烤", "烧烤", "美食", "香")
        if not any(word in post_text for word in food_cues):
            return True
    return False


async def create_history_learning_job(db: AsyncSession, created_by: UUID) -> AIJob:
    provider = await get_provider(db)
    if not provider_is_active(provider):
        raise ValueError(AI_DISABLED_MESSAGE)

    total_posts = await _count_targets(db, Post)
    total_media = await _count_targets(db, MediaFile)
    job = AIJob(
        job_type="history_learning",
        status="pending",
        progress_total=total_posts + total_media,
        created_by=created_by,
    )
    db.add(job)
    await db.flush()
    return job


async def create_album_suggestion_job(db: AsyncSession, created_by: UUID) -> AIJob:
    provider = await get_provider(db)
    if not provider_is_active(provider):
        raise ValueError(AI_DISABLED_MESSAGE)

    total_media = await _count_targets(db, MediaFile)
    job = AIJob(
        job_type="album_suggestions",
        status="pending",
        progress_total=min(total_media, 50),
        created_by=created_by,
    )
    db.add(job)
    await db.flush()
    return job


async def _count_targets(db: AsyncSession, model) -> int:
    result = await db.execute(select(model.id))
    return len(result.scalars().all())


async def run_history_learning(db: AsyncSession, job_id: UUID) -> None:
    job = await db.get(AIJob, job_id)
    if not job:
        return
    provider = await get_provider(db)
    if not provider_is_active(provider):
        job.status = "skipped"
        job.error_message = AI_DISABLED_MESSAGE
        return

    job.status = "running"
    job.started_at = now_utc()
    posts_result = await db.execute(select(Post).order_by(Post.created_at).limit(200))
    media_result = await db.execute(select(MediaFile).order_by(MediaFile.created_at).limit(200))
    processed = 0

    for post in posts_result.scalars().all():
        await upsert_simple_insight(
            db,
            target_type="post",
            target_id=post.id,
            summary=(post.content or "家庭影像帖子")[:300],
            tags=["家庭动态"] + (["有媒体"] if post.media_urls else ["文字"]),
            scenes=[],
            people=[],
        )
        processed += 1

    for media in media_result.scalars().all():
        await upsert_simple_insight(
            db,
            target_type="media",
            target_id=media.id,
            summary=media.caption or media.original_name or f"{media.file_type} 媒体",
            tags=[media.file_type],
            scenes=[],
            people=[],
        )
        processed += 1

    await ensure_family_profile(db)
    job.progress_current = processed
    job.status = "completed"
    job.completed_at = now_utc()


async def run_album_suggestions(db: AsyncSession, job_id: UUID) -> None:
    job = await db.get(AIJob, job_id)
    if not job:
        return
    provider = await get_provider(db)
    if not provider_is_active(provider):
        job.status = "skipped"
        job.error_message = AI_DISABLED_MESSAGE
        return

    job.status = "running"
    job.started_at = now_utc()
    persona = await pick_album_suggestion_persona(db)
    existing_result = await db.execute(
        select(AIAlbumSuggestion.target_id).where(AIAlbumSuggestion.target_type == "media")
    )
    existing_target_ids = set(existing_result.scalars().all())

    media_result = await db.execute(
        select(MediaFile)
        .where(MediaFile.deleted_at.is_(None))
        .order_by(desc(MediaFile.captured_at), desc(MediaFile.created_at))
        .limit(50)
    )
    processed = 0
    created = 0
    for media in media_result.scalars().all():
        processed += 1
        if media.id in existing_target_ids:
            continue
        suggestion = AIAlbumSuggestion(
            target_type="media",
            target_id=media.id,
            suggested_album_name=suggest_album_name(media),
            reason=suggest_album_reason(media),
            status="pending",
            created_by_persona_id=persona.id if persona else None,
        )
        db.add(suggestion)
        created += 1

    job.progress_current = processed
    job.status = "completed"
    job.result = {"suggestions_created": created}
    job.completed_at = now_utc()


async def mark_ai_job_failed(db: AsyncSession, job_id: UUID, error: Exception | str) -> None:
    job = await db.get(AIJob, job_id)
    if not job:
        return
    job.status = "failed"
    job.error_message = str(error)[:1000]
    job.completed_at = now_utc()
    if not job.started_at:
        job.started_at = job.completed_at
    await db.flush()


async def pick_album_suggestion_persona(db: AsyncSession) -> Optional[AIPersona]:
    await ensure_default_personas(db)
    result = await db.execute(
        select(AIPersona)
        .where(
            AIPersona.enabled.is_(True),
            AIPersona.album_suggestion_enabled.is_(True),
        )
        .order_by(AIPersona.sort_order, AIPersona.created_at)
        .limit(1)
    )
    return result.scalar_one_or_none()


def suggest_album_name(media: MediaFile) -> str:
    text = " ".join([media.caption or "", media.original_name or ""])
    if any(keyword in text for keyword in ("生日", "蛋糕", "周岁")):
        return "生日时光"
    if any(keyword in text for keyword in ("旅行", "出游", "公园", "海边", "露营")):
        return "一起出门的日子"
    if any(keyword in text for keyword in ("吃饭", "早餐", "午餐", "晚餐", "美食")):
        return "餐桌小记"
    captured_at = media.captured_at or media.created_at
    if captured_at:
        return f"{captured_at.year}年{captured_at.month}月家庭影像"
    return "家庭影像整理"


def suggest_album_reason(media: MediaFile) -> str:
    name = media.original_name or ("视频" if media.file_type == "video" else "照片")
    caption = f"「{media.caption}」" if media.caption else name
    return f"根据媒体说明和拍摄时间，建议把 {caption} 收入这个相册，方便之后按主题回看。"


async def upsert_simple_insight(
    db: AsyncSession,
    *,
    target_type: str,
    target_id: UUID,
    summary: str,
    tags: list[str],
    scenes: list[str],
    people: list[str],
) -> AIContentInsight:
    result = await db.execute(
        select(AIContentInsight).where(
            AIContentInsight.target_type == target_type,
            AIContentInsight.target_id == target_id,
        )
    )
    insight = result.scalar_one_or_none()
    if not insight:
        insight = AIContentInsight(target_type=target_type, target_id=target_id)
        db.add(insight)
    insight.summary = summary
    insight.tags = tags
    insight.scenes = scenes
    insight.people = people
    insight.sentiment = "positive"
    insight.model_metadata = {"source": "history_learning_v1"}
    return insight


async def ensure_family_profile(db: AsyncSession) -> AIProfile:
    result = await db.execute(
        select(AIProfile).where(AIProfile.subject_type == "family", AIProfile.subject_id.is_(None))
    )
    profile = result.scalar_one_or_none()
    if profile:
        return profile
    profile = AIProfile(
        subject_type="family",
        subject_id=None,
        title="家庭画像",
        summary="这个家庭正在用哪吒家庭记录日常、照片、视频和互动。",
        traits=["重视家庭记忆", "喜欢私有化保存"],
        preferences=[],
        memories=[],
    )
    db.add(profile)
    await db.flush()
    return profile


async def generate_report_draft(
    db: AsyncSession,
    *,
    period_type: str,
    period_start: datetime,
    period_end: datetime,
    created_by: UUID,
    persona_id: Optional[UUID] = None,
) -> AIReportDraft:
    provider = await get_provider(db)
    if not provider_is_active(provider):
        raise ValueError(AI_DISABLED_MESSAGE)

    persona = await db.get(AIPersona, persona_id) if persona_id else await pick_auto_comment_persona(db)
    posts_result = await db.execute(
        select(Post).where(
            Post.created_at >= period_start,
            Post.created_at <= period_end,
        ).order_by(Post.created_at)
    )
    posts = list(posts_result.scalars().all())
    title = f"家庭{_period_label(period_type)}回忆"
    content = build_report_content(posts)
    draft = AIReportDraft(
        persona_id=persona.id if persona else None,
        period_type=period_type,
        period_start=period_start,
        period_end=period_end,
        title=title,
        content=content,
        status="draft",
        source_metadata={"post_count": len(posts), "generated_by": "v1_template"},
        created_by=created_by,
    )
    db.add(draft)
    await db.flush()
    return draft


def build_report_content(posts: Iterable[Post]) -> str:
    posts = list(posts)
    if not posts:
        return "这段时间还没有新的家庭动态。等下一张照片、下一句话出现时，我会帮你们好好收进回忆里。"
    lines = ["这段时间，家里又多了一些值得收藏的小片段："]
    for post in posts[:8]:
        snippet = (post.content or "一组家庭影像").strip()
        lines.append(f"- {snippet[:80]}")
    lines.append("愿这些日常被慢慢保存，之后回头看时依然觉得温暖。")
    return "\n".join(lines)


def _period_label(period_type: str) -> str:
    if period_type == "month":
        return "月度"
    if period_type == "week":
        return "每周"
    return "阶段"


async def search_ai_memory(db: AsyncSession, query: str) -> list[AIContentInsight]:
    keyword = f"%{query.strip()}%"
    if not query.strip():
        return []
    result = await db.execute(
        select(AIContentInsight)
        .where(
            or_(
                AIContentInsight.summary.ilike(keyword),
                AIContentInsight.tags.cast(String).ilike(keyword),
                AIContentInsight.scenes.cast(String).ilike(keyword),
                AIContentInsight.people.cast(String).ilike(keyword),
            )
        )
        .order_by(desc(AIContentInsight.updated_at))
        .limit(50)
    )
    return list(result.scalars().all())
