from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.logging_setup import get_logger

log = get_logger()


class AppError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def validation_error(message: str = "入力が正しくありません。") -> AppError:
    return AppError(400, "VALIDATION_ERROR", message)


def not_found(message: str = "対象が見つかりません。") -> AppError:
    return AppError(404, "NOT_FOUND", message)


def conflict(code: str, message: str) -> AppError:
    return AppError(409, code, message)


def error_body(code: str, message: str) -> dict[str, dict[str, str]]:
    return {"error": {"code": code, "message": message}}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        log.warning(
            "要求拒否 %s %s status=%s code=%s 理由=%s",
            request.method,
            request.url.path,
            exc.status_code,
            exc.code,
            exc.message,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(exc.code, exc.message),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        fields = [".".join(str(part) for part in err.get("loc", ())) for err in exc.errors()]
        log.warning(
            "入力不正 %s %s 項目=%s",
            request.method,
            request.url.path,
            ",".join(fields),
        )
        return JSONResponse(
            status_code=400,
            content=error_body("VALIDATION_ERROR", "入力が正しくありません。"),
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        if isinstance(exc, (AppError, StarletteHTTPException, RequestValidationError)):
            raise exc
        log.error(
            "想定外の失敗 %s %s 理由=%s",
            request.method,
            request.url.path,
            type(exc).__name__,
            exc_info=exc,
        )
        return JSONResponse(
            status_code=500,
            content=error_body("INTERNAL_ERROR", "処理に失敗しました。"),
        )
