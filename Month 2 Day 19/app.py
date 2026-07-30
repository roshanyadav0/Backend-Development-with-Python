# The timing middleware

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)   # the ENTIRE rest of the stack + route runs here
        duration = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{duration:.4f}"
        return response

# The request-id middleware
class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

# app.add_middleware() — and why order genuinely surprised the test
app.add_middleware(PrintMiddlewareA)
app.add_middleware(PrintMiddlewareB)
app.add_middleware(TimingMiddleware)
app.add_middleware(RequestIDMiddleware)

# B: before call_next
A: before call_next
ROUTE: handling request
A: after call_next
B: after call_next


