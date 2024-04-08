import asyncio
import logging
from enum import StrEnum

import socketio
from engineio.async_server import task_reference_holder
from fastapi import Header, HTTPException
from pydantic import BaseModel

from rchat.views.auth.helpers import check_access_token

logger = logging.getLogger(__name__)


class SocketioEventsEnum(StrEnum):
    new_message = "_new_message_"
    update_message = "_update_message_"
    delete_message = "_delete_message_"
    read_message = "_read_message_"
    error = "_error_"


class SocketIOClient(socketio.AsyncServer):
    def __init__(self):
        super().__init__(
            async_mode="asgi",
            cors_allowed_origins="*",
        )
        self.users = {}

    # async def _handle_event(self, sid, namespace, id, data):
    #     logger.info("Data received: %s", data)
    #     logger.info("Namespace: %s", namespace)
    #     namespace = namespace or "/"
    #     res = self._get_event_handler(data[0], namespace, sid)
    #     # self._validate_arguments(res[0], data)
    #     # logger.info("Result: %s", res[0].__annotations__["data"](sender_id=3213))
    #
    #     await super()._handle_event(sid, namespace, id, data)

    # async def _trigger_event(self, event, *args, **kwargs):
    #     """Invoke an event handler."""
    #     run_async = kwargs.pop('run_async', False)
    #     logger.info("Triggered")
    #     ret = None
    #     if event in self.handlers:
    #         logger.info("AS: %s", type(args[0]))
    #         if asyncio.iscoroutinefunction(self.handlers[event]):
    #             async def run_async_handler():
    #                 try:
    #                     if args and isinstance(args[0], dict):
    #                         body = self.handlers[event].__annotations__.values()[0]
    #                         return await self.handlers[event](body(**args[0]))
    #                     else:
    #                         return await self.handlers[event](*args)
    #                 except asyncio.CancelledError:  # pragma: no cover
    #                     pass
    #                 except Exception:
    #                     self.logger.exception(event + ' async handler error')
    #                     if event == 'connect':
    #                         # if connect handler raised error we reject the
    #                         # connection
    #                         return False
    #
    #             if run_async:
    #                 ret = self.start_background_task(run_async_handler)
    #                 task_reference_holder.add(ret)
    #                 ret.add_done_callback(task_reference_holder.discard)
    #             else:
    #                 ret = await run_async_handler()
    #         else:
    #             async def run_sync_handler():
    #                 try:
    #                     return self.handlers[event](*args)
    #                 except Exception:
    #                     self.logger.exception(event + ' handler error')
    #                     if event == 'connect':
    #                         # if connect handler raised error we reject the
    #                         # connection
    #                         return False
    #
    #             if run_async:
    #                 ret = self.start_background_task(run_sync_handler)
    #                 task_reference_holder.add(ret)
    #                 ret.add_done_callback(task_reference_holder.discard)
    #             else:
    #                 ret = await run_sync_handler()
    #     return ret
    #
    # def _validate_arguments(self, handler, data):
    #     params = handler.__annotations__
    #     for key in params:
    #         if isinstance(params[key], BaseModel):
    #             if isinstance(data, dict):
    #                 params[key](**data)


sio = SocketIOClient()
asio_app = socketio.ASGIApp(socketio_server=sio, socketio_path="socks")


@sio.event
async def connect(sid, environ, auth):
    try:
        session = await check_access_token(auth_data=environ["HTTP_AUTHORIZATION"])
    except HTTPException:
        logger.error("Invalid token.")
        await sio.disconnect(sid)
        return
    with sio.session(sid) as io_session:
        io_session["user_id"] = session.user_id
    logger.info("Socketio connected. params=%s", {"sid": sid, "user_id": session.user_id})


@sio.event
async def disconnect(sid):
    sio.users.pop(sid, None)
    logger.info("Socketio disconnected. params=%s", {"sid": sid})
