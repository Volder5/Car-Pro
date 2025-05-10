from .callbacks import router as callbacks_router
from .commands import router as commands_router
from .states import router as states_router

routers = [callbacks_router, commands_router, states_router]