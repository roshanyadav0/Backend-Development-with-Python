# The new file: routers/loans.py
router = APIRouter(tags=["Loans"])

class LoanRequest(BaseModel):
    book_id: UUID
    member_id: UUID

@router.post("/borrow", response_model=LoanResponse, ...)
async def borrow_book(
    request: LoanRequest,
    books: dict = Depends(get_db),
    members: dict = Depends(get_members_db),
    loans: dict = Depends(get_loans_db),
):
    book = _require_book(books, request.book_id)
    _require_member(members, request.member_id)

    if request.book_id in loans:
        raise BookUnavailableError(request.book_id)

    loans[request.book_id] = request.member_id
    book["available"] = False
    return LoanResponse(book_id=request.book_id, member_id=request.member_id, status="borrowed")

# The validation rules, and why each is its own exception
class BookUnavailableError(Exception):        # can't borrow — book's already out
class NotBorrowedByMemberError(Exception):     # can't return — you're not the holder

