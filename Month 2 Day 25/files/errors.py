from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from uuid import UUID


def error_body(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


class ResourceNotFoundError(Exception):
    def __init__(self, resource: str, resource_id: UUID):
        self.resource = resource
        self.resource_id = resource_id


def register_error_handlers(app):
    @app.exception_handler(ResourceNotFoundError)
    async def handle_not_found(request: Request, exc: ResourceNotFoundError):
        return JSONResponse(
            status_code=404,
            content=error_body(f"{exc.resource.upper()}_NOT_FOUND", f"{exc.resource} {exc.resource_id} not found"),
        )

    @app.exception_handler(HTTPException)
    async def handle_http_exception(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(f"HTTP_{exc.status_code}", str(exc.detail)),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        first = exc.errors()[0]
        field = ".".join(str(p) for p in first["loc"][1:]) if len(first["loc"]) > 1 else str(first["loc"][0])
        message = f"{field}: {first['msg']}" if field else first["msg"]
        return JSONResponse(status_code=422, content=error_body("VALIDATION_ERROR", message))

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception):
        return JSONResponse(status_code=500, content=error_body("INTERNAL_ERROR", "Something went wrong on our end"))
