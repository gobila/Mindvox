from fastapi import HTTPException, UploadFile, status

from settings import Settings


UPLOAD_READ_CHUNK_SIZE = 1024 * 1024


async def read_upload_with_limit(
    upload_file: UploadFile,
    *,
    settings: Settings,
    detail: str,
) -> bytes:
    max_size_bytes = settings.max_upload_mb * 1024 * 1024
    total_size = 0
    chunks: list[bytes] = []

    while True:
        chunk = await upload_file.read(UPLOAD_READ_CHUNK_SIZE)
        if not chunk:
            break

        total_size += len(chunk)
        if total_size > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=detail,
            )

        chunks.append(chunk)

    return b"".join(chunks)
