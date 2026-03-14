def success(data, message: str = "Success") -> dict:
    return {"success": True, "message": message, "data": data}


def paginated(data, total: int, skip: int, limit: int) -> dict:
    return {
        "success": True,
        "data": data,
        "pagination": {"total": total, "skip": skip, "limit": limit}
    }
