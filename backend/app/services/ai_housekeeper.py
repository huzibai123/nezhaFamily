"""
AI 家庭管家业务服务
"""
from __future__ import annotations

import base64
from datetime import datetime, timezone
import hashlib
import random
import secrets
from typing import Iterable, Optional
from uuid import UUID

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import String, desc, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
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
from app.models.media import MediaFile
from app.models.notification import Notification
from app.models.post import Post
from app.models.user import User
from app.services.ai_client import AIProviderError, OpenAICompatibleClient

AI_DISABLED_MESSAGE = "AI 管家尚未启用"
SAFE_COMMENT = "看到这条新的家庭记忆，心里也跟着亮了一下。愿这些温柔的小瞬间被好好收藏。"
POSITIVE_WORDS = ("温暖", "可爱", "开心", "幸福", "珍贵", "美好", "喜欢", "收藏", "陪伴", "快乐")
UNSAFE_WORDS = ("讨厌", "糟糕", "丑", "笨", "病", "死亡", "吓人", "隐私", "诊断")
ENCRYPTED_KEY_PREFIX = "fernet:"


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


def provider_is_active(provider: Optional[AIProviderConfig]) -> bool:
    return bool(
        provider
        and provider.enabled
        and provider.status == "active"
        and provider_has_key(provider)
    )


async def ensure_default_personas(db: AsyncSession) -> list[AIPersona]:
    existing_result = await db.execute(select(AIPersona).order_by(AIPersona.sort_order))
    existing = list(existing_result.scalars().all())
    if existing:
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


def build_client(provider: AIProviderConfig) -> OpenAICompatibleClient:
    api_key = resolve_provider_api_key(provider)
    return OpenAICompatibleClient(
        base_url=provider.base_url,
        api_key=api_key,
        model=provider.text_model,
        timeout_seconds=provider.timeout_seconds or settings.AI_REQUEST_TIMEOUT_SECONDS,
    )


def encrypt_ai_api_key(api_key: str) -> str:
    token = _ai_key_cipher().encrypt(api_key.encode("utf-8")).decode("utf-8")
    return f"{ENCRYPTED_KEY_PREFIX}{token}"


def resolve_provider_api_key(provider: AIProviderConfig) -> str:
    if not provider.api_key_encrypted:
        return settings.AI_API_KEY
    if not provider.api_key_encrypted.startswith(ENCRYPTED_KEY_PREFIX):
        return provider.api_key_encrypted
    token = provider.api_key_encrypted.removeprefix(ENCRYPTED_KEY_PREFIX)
    try:
        return _ai_key_cipher().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise AIProviderError("模型 API Key 解密失败，请重新保存配置", status_code=401) from exc


def _ai_key_cipher() -> Fernet:
    digest = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
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
        await pause_provider_for_error(db, provider, error)
        return False, str(error)

    provider.status = "active" if provider.enabled else "disabled"
    provider.failure_count = 0
    provider.last_error = None
    provider.paused_reason = None
    provider.notified_pause_at = None
    provider.last_checked_at = now_utc()
    await db.flush()
    return True, "连接测试成功"


async def generate_ai_comment_for_post(db: AsyncSession, post_id: UUID) -> Optional[Comment]:
    provider = await get_provider(db)
    if not provider_is_active(provider):
        return None

    post_result = await db.execute(select(Post).where(Post.id == post_id).with_for_update())
    post = post_result.scalar_one_or_none()
    if not post:
        return None

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
    try:
        client = build_client(provider)
    except AIProviderError as error:
        await pause_provider_for_error(db, provider, error)
        return None
    context = await build_post_context(db, post, author)
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
        ok, reason = validate_positive_comment(candidate)
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
            "model": provider.text_model,
            "attempts": attempts,
            "fallback": comment_text == SAFE_COMMENT,
        },
    )
    db.add(comment)
    await db.execute(update(Post).where(Post.id == post.id).values(comment_count=Post.comment_count + 1))
    provider.failure_count = 0
    provider.last_error = None
    await db.flush()
    return comment


async def build_post_context(db: AsyncSession, post: Post, author: Optional[User]) -> str:
    media_lines = []
    media_items = post.media_urls or []
    for item in media_items[:5]:
        if isinstance(item, dict):
            media_lines.append(f"- {item.get('type', 'media')}: {item.get('url', '')}")

    recent_profiles = await db.execute(select(AIProfile).order_by(desc(AIProfile.updated_at)).limit(5))
    profile_text = "\n".join(
        f"- {profile.title}: {profile.summary or profile.editable_notes or ''}"
        for profile in recent_profiles.scalars().all()
    )
    return "\n".join(
        [
            f"作者：{author.role_in_family or author.username if author else '家人'}",
            f"帖子文字：{post.content or '无文字说明'}",
            "媒体：",
            "\n".join(media_lines) or "- 无媒体",
            "已有家庭画像摘要：",
            profile_text or "- 暂无",
        ]
    )


def build_comment_prompt(
    persona: AIPersona,
    context: str,
    previous_comment: Optional[str],
) -> list[dict[str, str]]:
    system_prompt = (
        f"你是家庭私有平台里的 AI 角色「{persona.name}」。"
        f"你的性格/语气：{persona.tone or '温暖、真诚、简短'}。"
        "你要为家人的新帖子写一条正向评论。"
        "要求：中文，30字以内，真诚、具体、积极，不要批评、诊断、吓人、泄露隐私，不要自称大模型。"
    )
    user_prompt = f"帖子上下文：\n{context}\n\n请写一条评论。"
    if previous_comment:
        user_prompt += f"\n上一版不够合适：{previous_comment}\n请重新写得更自然、更正向。"
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def normalize_comment(content: str) -> str:
    content = content.strip().strip('"“”')
    return " ".join(content.split())[:120]


def validate_positive_comment(content: str) -> tuple[bool, str]:
    if not content:
        return False, "empty"
    if len(content) > 80:
        return False, "too_long"
    if any(word in content for word in UNSAFE_WORDS):
        return False, "unsafe_word"
    if not any(word in content for word in POSITIVE_WORDS) and not content.endswith(("呀", "呢", "～", "！", "!")):
        return False, "not_positive_enough"
    return True, "ok"


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
