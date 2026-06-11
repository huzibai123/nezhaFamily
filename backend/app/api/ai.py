"""
AI 家庭管家 API
"""
import base64
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_admin
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.ai import (
    AIAlbumSuggestion,
    AIJob,
    AIPersona,
    AIProfile,
    AIProviderConfig,
    AIReportDraft,
)
from app.models.album import Album, album_media
from app.models.media import MediaFile
from app.models.post import Post
from app.models.user import User
from app.schemas.ai import (
    AIAlbumSuggestionResponse,
    AIAlbumSuggestionReview,
    AIJobCreate,
    AIJobResponse,
    AIPersonaCreate,
    AIPersonaResponse,
    AIPersonaUpdate,
    AIProfileResponse,
    AIProfileUpdate,
    AIProviderResponse,
    AIProviderTestResponse,
    AIProviderUpdate,
    AIPostCaptionResponse,
    AIReportDraftResponse,
    AIReportGenerateRequest,
    AIReportUpdate,
    AISearchResponse,
    AISearchResponseItem,
    AIStatusResponse,
)
from app.services.ai_housekeeper import (
    AI_DISABLED_MESSAGE,
    AIPostCaptionMediaInput,
    create_album_suggestion_job,
    create_history_learning_job,
    create_system_user_for_persona,
    encrypt_ai_api_key,
    ensure_default_personas,
    generate_report_draft,
    get_or_create_provider,
    get_provider,
    generate_post_caption,
    mark_ai_job_failed,
    now_utc,
    provider_api_key_source,
    provider_disable_response_storage,
    provider_has_key,
    provider_is_active,
    provider_model_reasoning_effort,
    provider_settings,
    provider_wire_api,
    search_ai_memory,
    test_provider_connection,
)
from app.services.ai_client import AIProviderError
from app.tasks.ai_housekeeper import run_ai_album_suggestions, run_ai_history_learning

admin_router = APIRouter(prefix="/admin/ai")
router = APIRouter(prefix="/ai")
MAX_POST_CAPTION_FILES = 4
MAX_POST_CAPTION_IMAGE_BYTES = 8 * 1024 * 1024
POST_CAPTION_ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def provider_response(provider: AIProviderConfig) -> AIProviderResponse:
    return AIProviderResponse(
        id=provider.id,
        name=provider.name,
        base_url=provider.base_url,
        text_model=provider.text_model,
        vision_model=provider.vision_model,
        timeout_seconds=provider.timeout_seconds,
        enabled=provider.enabled,
        status=provider.status,
        has_api_key=provider_has_key(provider),
        api_key_source=provider_api_key_source(provider),
        wire_api=provider_wire_api(provider),
        model_reasoning_effort=provider_model_reasoning_effort(provider),
        disable_response_storage=provider_disable_response_storage(provider),
        failure_count=provider.failure_count,
        last_error=provider.last_error,
        paused_reason=provider.paused_reason,
        last_checked_at=provider.last_checked_at,
        notified_pause_at=provider.notified_pause_at,
        created_at=provider.created_at,
        updated_at=provider.updated_at,
    )


async def _post_caption_media_input(file: UploadFile) -> AIPostCaptionMediaInput | None:
    content_type = (file.content_type or "").lower()
    filename = file.filename or "media"
    if content_type.startswith("image/"):
        if content_type not in POST_CAPTION_ALLOWED_IMAGE_TYPES:
            raise HTTPException(status_code=400, detail=f"不支持的图片类型: {content_type}")
        data = await file.read(MAX_POST_CAPTION_IMAGE_BYTES + 1)
        if len(data) > MAX_POST_CAPTION_IMAGE_BYTES:
            raise HTTPException(status_code=400, detail="用于 AI 文案的图片不能超过 8MB")
        if not data:
            return None
        return AIPostCaptionMediaInput(
            filename=filename,
            content_type=content_type,
            media_type="image",
            data_url=f"data:{content_type};base64,{base64.b64encode(data).decode('ascii')}",
        )
    if content_type.startswith("video/"):
        return AIPostCaptionMediaInput(
            filename=filename,
            content_type=content_type,
            media_type="video",
        )
    raise HTTPException(status_code=400, detail=f"不支持的媒体类型: {content_type or filename}")


async def _post_caption_media_inputs(files: list[UploadFile]) -> list[AIPostCaptionMediaInput]:
    media: list[AIPostCaptionMediaInput] = []
    for file in files[:MAX_POST_CAPTION_FILES]:
        item = await _post_caption_media_input(file)
        if item:
            media.append(item)
    return media


@router.post("/post-caption", response_model=AIPostCaptionResponse)
async def create_ai_post_caption(
    mode: Literal["polish", "generate"] = Form(...),
    content: str = Form(""),
    files: list[UploadFile] = File(default=[]),
    files_bracket: list[UploadFile] = File(default=[], alias="files[]"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    media = await _post_caption_media_inputs([*(files or []), *(files_bracket or [])])
    try:
        caption = await generate_post_caption(
            db,
            mode=mode,
            content=content,
            media=media,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except AIProviderError as exc:
        await db.commit()
        raise HTTPException(status_code=503, detail=f"AI 文案暂时不可用：{exc}") from exc
    await db.commit()
    return AIPostCaptionResponse(content=caption, mode=mode, used_media_count=len(media))


@admin_router.get("/status", response_model=AIStatusResponse)
async def get_ai_status(
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
):
    provider = await get_or_create_provider(db)
    await ensure_default_personas(db)
    personas_result = await db.execute(select(AIPersona))
    personas = list(personas_result.scalars().all())
    await db.commit()
    return AIStatusResponse(
        enabled=provider_is_active(provider),
        status=provider.status,
        provider=provider_response(provider),
        personas_enabled=len([p for p in personas if p.enabled]),
        auto_comment_personas=len([p for p in personas if p.enabled and p.auto_comment_enabled]),
    )


@admin_router.get("/providers", response_model=list[AIProviderResponse])
async def get_ai_providers(
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
):
    provider = await get_or_create_provider(db)
    await db.commit()
    return [provider_response(provider)]


@admin_router.put("/providers/default", response_model=AIProviderResponse)
async def update_ai_provider(
    payload: AIProviderUpdate,
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
):
    provider = await get_or_create_provider(db)
    provider.name = payload.name
    provider.base_url = payload.base_url
    provider.text_model = payload.text_model
    provider.vision_model = payload.vision_model
    provider.timeout_seconds = payload.timeout_seconds
    provider.enabled = payload.enabled
    api_key = payload.api_key.strip() if payload.api_key is not None else None
    if api_key:
        provider.api_key_encrypted = encrypt_ai_api_key(api_key)
    elif payload.clear_api_key:
        provider.api_key_encrypted = None
    settings = provider_settings(provider)
    settings["wire_api"] = payload.wire_api
    if payload.model_reasoning_effort and payload.model_reasoning_effort.strip():
        settings["model_reasoning_effort"] = payload.model_reasoning_effort.strip()
    else:
        settings.pop("model_reasoning_effort", None)
    settings["disable_response_storage"] = payload.disable_response_storage
    provider.settings = settings
    provider.status = "active" if provider.enabled and provider_has_key(provider) else "disabled"
    provider.failure_count = 0
    provider.last_error = None
    provider.paused_reason = None
    provider.notified_pause_at = None
    await db.commit()
    await db.refresh(provider)
    return provider_response(provider)


@admin_router.post("/providers/default/test", response_model=AIProviderTestResponse)
async def test_ai_provider(
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
):
    provider = await get_or_create_provider(db)
    ok, message = await test_provider_connection(db, provider)
    await db.commit()
    return AIProviderTestResponse(ok=ok, status=provider.status, message=message)


@admin_router.get("/personas", response_model=list[AIPersonaResponse])
async def get_ai_personas(
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
):
    personas = await ensure_default_personas(db)
    await db.commit()
    return personas


@admin_router.post("/personas", response_model=AIPersonaResponse, status_code=status.HTTP_201_CREATED)
async def create_ai_persona(
    payload: AIPersonaCreate,
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
):
    user = await create_system_user_for_persona(db, payload.name, payload.persona_type)
    persona = AIPersona(user_id=user.id, **payload.model_dump())
    db.add(persona)
    await db.commit()
    await db.refresh(persona)
    return persona


@admin_router.patch("/personas/{persona_id}", response_model=AIPersonaResponse)
async def update_ai_persona(
    persona_id: UUID,
    payload: AIPersonaUpdate,
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
):
    persona = await db.get(AIPersona, persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="AI 角色不存在")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(persona, field, value)
    if persona.user_id:
        user = await db.get(User, persona.user_id)
        if user:
            user.bio = persona.bio
            user.avatar_url = persona.avatar_url
            user.role_in_family = persona.persona_type
    await db.commit()
    await db.refresh(persona)
    return persona


@admin_router.delete("/personas/{persona_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ai_persona(
    persona_id: UUID,
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
):
    persona = await db.get(AIPersona, persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="AI 角色不存在")
    persona.enabled = False
    persona.auto_comment_enabled = False
    await db.commit()
    return None


@admin_router.get("/jobs", response_model=list[AIJobResponse])
async def get_ai_jobs(
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AIJob).order_by(desc(AIJob.created_at)).limit(30))
    return list(result.scalars().all())


@admin_router.post("/jobs", response_model=AIJobResponse, status_code=status.HTTP_201_CREATED)
async def create_ai_job(
    payload: AIJobCreate,
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        if payload.job_type == "album_suggestions":
            job = await create_album_suggestion_job(db, current_user.id)
            task = run_ai_album_suggestions
        else:
            job = await create_history_learning_job(db, current_user.id)
            task = run_ai_history_learning
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await db.commit()
    try:
        task.delay(str(job.id))
    except Exception as exc:
        await mark_ai_job_failed(db, job.id, "任务队列不可用，请检查 Redis/Celery")
        await db.commit()
        raise HTTPException(status_code=503, detail="任务队列不可用，请检查 Redis/Celery") from exc
    await db.refresh(job)
    return job


@admin_router.get("/album-suggestions", response_model=list[AIAlbumSuggestionResponse])
async def get_ai_album_suggestions(
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AIAlbumSuggestion).order_by(desc(AIAlbumSuggestion.created_at)).limit(50)
    )
    return list(result.scalars().all())


@admin_router.post(
    "/album-suggestions/{suggestion_id}/review",
    response_model=AIAlbumSuggestionResponse,
)
async def review_ai_album_suggestion(
    suggestion_id: UUID,
    payload: AIAlbumSuggestionReview,
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
):
    suggestion = await db.get(AIAlbumSuggestion, suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="AI 相册建议不存在")
    if suggestion.status != "pending":
        return suggestion

    if payload.action == "reject":
        suggestion.reviewed_by = current_user.id
        suggestion.reviewed_at = now_utc()
        suggestion.status = "rejected"
        await db.commit()
        await db.refresh(suggestion)
        return suggestion

    media = await db.get(MediaFile, suggestion.target_id)
    if suggestion.target_type != "media" or not media or media.deleted_at is not None:
        raise HTTPException(status_code=404, detail="建议关联的媒体不存在")

    album = await db.get(Album, payload.album_id) if payload.album_id else None
    if payload.album_id and not album:
        raise HTTPException(status_code=404, detail="相册不存在")
    if not album:
        album_name = payload.album_name or suggestion.suggested_album_name or "AI 整理相册"
        album = Album(
            name=album_name,
            description=suggestion.reason,
            cover_image_url=media.file_path,
            created_by=current_user.id,
        )
        db.add(album)
        await db.flush()

    exists_result = await db.execute(
        select(album_media.c.media_id).where(
            album_media.c.album_id == album.id,
            album_media.c.media_id == media.id,
        )
    )
    if not exists_result.scalar_one_or_none():
        await db.execute(album_media.insert().values(album_id=album.id, media_id=media.id))

    suggestion.reviewed_by = current_user.id
    suggestion.reviewed_at = now_utc()
    suggestion.album_id = album.id
    suggestion.status = "approved"
    await db.commit()
    await db.refresh(suggestion)
    return suggestion


@admin_router.get("/profiles", response_model=list[AIProfileResponse])
async def get_ai_profiles(
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AIProfile).order_by(desc(AIProfile.updated_at)))
    return list(result.scalars().all())


@admin_router.patch("/profiles/{profile_id}", response_model=AIProfileResponse)
async def update_ai_profile(
    profile_id: UUID,
    payload: AIProfileUpdate,
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
):
    profile = await db.get(AIProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="AI 画像不存在")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    profile.updated_by = current_user.id
    await db.commit()
    await db.refresh(profile)
    return profile


@admin_router.get("/reports", response_model=list[AIReportDraftResponse])
async def get_ai_reports(
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AIReportDraft).order_by(desc(AIReportDraft.created_at)).limit(30))
    return list(result.scalars().all())


@admin_router.post("/reports", response_model=AIReportDraftResponse, status_code=status.HTTP_201_CREATED)
async def create_ai_report(
    payload: AIReportGenerateRequest,
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        draft = await generate_report_draft(
            db,
            period_type=payload.period_type,
            period_start=payload.period_start,
            period_end=payload.period_end,
            persona_id=payload.persona_id,
            created_by=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await db.commit()
    await db.refresh(draft)
    return draft


@admin_router.patch("/reports/{report_id}", response_model=AIReportDraftResponse)
async def update_ai_report(
    report_id: UUID,
    payload: AIReportUpdate,
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
):
    draft = await db.get(AIReportDraft, report_id)
    if not draft:
        raise HTTPException(status_code=404, detail="AI 报告草稿不存在")
    if payload.title is not None:
        draft.title = payload.title
    if payload.content is not None:
        draft.content = payload.content
    await db.commit()
    await db.refresh(draft)
    return draft


@admin_router.post("/reports/{report_id}/publish", response_model=AIReportDraftResponse)
async def publish_ai_report(
    report_id: UUID,
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
):
    draft = await db.get(AIReportDraft, report_id)
    if not draft:
        raise HTTPException(status_code=404, detail="AI 报告草稿不存在")
    if draft.published_post_id:
        return draft

    persona = await db.get(AIPersona, draft.persona_id) if draft.persona_id else None
    author_id = persona.user_id if persona and persona.user_id else current_user.id
    post = Post(author_id=author_id, content=f"{draft.title}\n\n{draft.content}", media_urls=[])
    db.add(post)
    await db.flush()
    draft.status = "published"
    draft.published_post_id = post.id
    await db.commit()
    await db.refresh(draft)
    return draft


@router.get("/search", response_model=AISearchResponse)
async def search_ai(
    q: str = Query(..., min_length=1, max_length=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    provider = await get_provider(db)
    if not provider_is_active(provider):
        raise HTTPException(status_code=400, detail=AI_DISABLED_MESSAGE)
    insights = await search_ai_memory(db, q)
    results = [
        AISearchResponseItem(
            target_type=insight.target_type,
            target_id=insight.target_id,
            summary=insight.summary,
            tags=insight.tags or [],
            scenes=insight.scenes or [],
            people=insight.people or [],
            score=1,
        )
        for insight in insights
    ]
    return AISearchResponse(query=q, results=results, total=len(results))
