from vkbottle import VKAPIError


async def exception_handle(e: VKAPIError):
    print(e.__class__)
