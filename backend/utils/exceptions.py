from fastapi import HTTPException, status


def raise_404(detail: str = "Not found"):
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def raise_400(detail: str = "Bad request"):
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def raise_401(detail: str = "Unauthorized"):
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


def raise_403(detail: str = "Forbidden"):
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def raise_409(detail: str = "Conflict"):
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


def raise_422(detail: str = "Unprocessable entity"):
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


def raise_insufficient_stock(available: int, requested: int):
    detail = f"Insufficient stock: {available} available, {requested} requested"
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
