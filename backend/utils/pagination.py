class PaginationParams:
    def __init__(self, skip: int = 0, limit: int = 50):
        self.skip = skip
        self.limit = min(limit, 200)  # cap at 200
