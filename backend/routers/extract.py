from fastapi import APIRouter, File, HTTPException, UploadFile

from services.vision import GeminiQuotaExceeded, extract_drugs

router = APIRouter()

MAX_IMAGES = 4
MAX_SIZE_BYTES = 8 * 1024 * 1024


@router.post("/extract")
async def extract(images: list[UploadFile] = File(...)) -> dict:
    if not images or len(images) > MAX_IMAGES:
        raise HTTPException(
            status_code=400,
            detail={
                "error": True,
                "code": "BAD_IMAGE_COUNT",
                "message": f"Send 1-{MAX_IMAGES} images",
                "details": {},
            },
        )

    image_bytes_list = []
    image_mime_types = []
    for image in images:
        content = await image.read()
        if len(content) > MAX_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": True,
                    "code": "IMAGE_TOO_LARGE",
                    "message": f"{image.filename} exceeds 8MB",
                    "details": {},
                },
            )
        image_bytes_list.append(content)
        image_mime_types.append(image.content_type or "image/jpeg")

    try:
        return extract_drugs(image_bytes_list, image_mime_types)
    except GeminiQuotaExceeded as exc:
        raise HTTPException(
            status_code=429,
            detail={
                "error": True,
                "code": "GEMINI_QUOTA_EXCEEDED",
                "message": str(exc),
                "details": {},
            },
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "error": True,
                "code": "GEMINI_UNAVAILABLE",
                "message": str(exc),
                "details": {},
            },
        ) from exc
