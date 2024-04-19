import logging
from enum import StrEnum

import socketio
from fastapi import HTTPException
from pydantic import ValidationError
from socketio import packet

from rchat.views.auth.helpers import check_access_token

logger = logging.getLogger(__name__)


class SocketioEventsEnum(StrEnum):
    new_message = "_new_message_"
    update_message = "_update_message_"
    delete_message = "_delete_message_"
    read_message = "_read_message_"
    error = "_error_"


class SocketioErrorStatusEnum(StrEnum):
    invalid_data = "invalid_data"
    server_error = "server_error"


class SocketIOClient(socketio.AsyncServer):
    def __init__(self):
        super().__init__(
            async_mode="asgi",
            cors_allowed_origins="*",
        )
        self.users = {}

    async def emit_error_event(
        self,
        to_sid,
        status: SocketioErrorStatusEnum,
        event_name: str,
        error_msg: str,
        data,
    ):
        await self.emit(
            event=SocketioEventsEnum.error,
            to=to_sid,
            data={
                "status": status,
                "event_name": event_name,
                "error": error_msg,
                "event_data": data,
            },
        )

    async def _handle_event_internal(
        self, server, sid, eio_sid, data, namespace, id
    ):
        try:
            cls = self._get_handler_params_type(data[0], namespace, sid)
            if len(data) > 2:
                raise ValidationError
            cls(**data[1]
        except ValidationError as err:
            logger.error("Validation error. data=%s, err=%s", data, err)
            await self.emit_error_event(
                status=SocketioErrorStatusEnum.invalid_data,
                to_sid=sid,
                event_name=data[0],
                error_msg=str(err),
                data=data,
            )
            return
        try:
            r = await server._trigger_event(
                data[0], namespace, sid, cls(**data[1])
            )
        except Exception:
            await self.emit_error_event(
                status=SocketioErrorStatusEnum.server_error,
                to_sid=sid,
                event_name=data[0],
                error_msg=str("Server error occured."),
                data=data,
            )
            raise

        if r != self.not_handled and id is not None:
            # send ACK packet with the response returned by the handler
            # tuples are expanded as multiple arguments
            if r is None:
                data = []
            elif isinstance(r, tuple):
                data = list(r)
            else:
                data = [r]
            await server._send_packet(
                eio_sid,
                self.packet_class(
                    packet.ACK, namespace=namespace, id=id, data=data
                ),
            )

    def _get_handler_params_type(self, event_name, namespace, sid):
        """
        Возвращает класс параметра функции обработчика события с event_name.
        """
        handler = self._get_event_handler(event_name, namespace, sid)[0]
        params = handler.__annotations__
        return list(params.values())[0]


sio = SocketIOClient()
asio_app = socketio.ASGIApp(socketio_server=sio, socketio_path="socks")


@sio.event
async def connect(sid, environ, _):
    try:
        session = await check_access_token(
            auth_data=environ["HTTP_AUTHORIZATION"]
        )
    except HTTPException:
        logger.error("Invalid token.")
        await sio.disconnect(sid)
        return
    async with sio.session(sid) as io_session:
        io_session["user_id"] = session.user_id
    sio.users[session.user_id] = sid
    logger.info(
        "Socketio connected. params=%s",
        {"sid": sid, "user_id": session.user_id},
    )


@sio.event
async def disconnect(sid):
    sio.users.pop(sid, None)
    logger.info("Socketio disconnected. params=%s", {"sid": sid})
