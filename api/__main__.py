from time import ctime, perf_counter

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.exceptions.common import CommonException, InternalServerError
from api.utils.logger import Log
from starlette.middleware.cors import CORSMiddleware
from api.endpoints.events import event_router


app = FastAPI(title="Na-slet creator API")
origins = ["*"]


@app.on_event("startup")
async def startup() -> None:
    await Log.initialise_logger()


@app.on_event("shutdown")
async def shutdown() -> None:
    await Log.shutdown_logger()


@app.exception_handler(CommonException)
async def common_exception_handler(request: Request, exception: CommonException):
    await Log.log_exception(exception)
    return JSONResponse(
        status_code=exception.code,
        content={"code": exception.code, "message": exception.message},
    )


@app.exception_handler(Exception)
async def unknown_exception(request: Request, exception: Exception):
    return await common_exception_handler(request, InternalServerError(exception))


@app.middleware("http")
async def log_requst(request: Request, call_next):
    await Log.log_request_start(
        request.method, request.url.path, ctime(), request.client.host
    )
    start_time = perf_counter()
    response = await call_next(request)
    process_time = perf_counter() - start_time
    formatted_process_time = "{0:.5f}".format(process_time)
    await Log.log_request_end(
        request.method,
        request.url.path,
        ctime(),
        formatted_process_time,
        request.client.host,
    )
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
app.include_router(event_router)
