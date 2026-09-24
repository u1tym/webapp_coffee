from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
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
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(exc.code, exc.message),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(
        _request: Request, _exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content=error_body("VALIDATION_ERROR", "入力が正しくありません。"),
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(_request: Request, exc: Exception) -> JSONResponse:
        if isinstance(exc, (AppError, StarletteHTTPException, RequestValidationError)):
            raise exc
        return JSONResponse(
            status_code=500,
            content=error_body("INTERNAL_ERROR", "処理に失敗しました。"),
        )
