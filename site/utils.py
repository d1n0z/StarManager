from fastapi import Request


async def get_current_user(request: Request):
    if not request or not request.session:
        return None
    user = request.session.get("user")
    return user
