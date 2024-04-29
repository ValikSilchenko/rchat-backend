import logging
from datetime import datetime

import geocoder
from asyncpg import Pool
from requests import RequestException

from rchat.repository.helpers import build_model
from rchat.schemas.geoip import GeoIPData

logger = logging.getLogger(__name__)


class GeoIPRepository:
    def __init__(self, db: Pool):
        self._db = db

    async def get_data_by_ip(self, ip: str) -> GeoIPData:
        """
        Получает информацию о геолокации по IP адресу,
        обновляет информацию если нужно.
        """
        sql = """
            select * from "geoip"
            where "ip" = $1
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, ip)

        if not row:
            return await self._save_geocoder_data(ip)

        return GeoIPData(**dict(row))

    async def _save_geocoder_data(self, ip: str) -> GeoIPData:
        """
        Получает информацию о геолокации по IP через geocoder и сохраняет ёё.
        """
        try:
            geocoder_data = geocoder.ip(ip)
            if not geocoder_data.ok:
                logger.error("IP not found in geocoder. ip=%s", ip)
                return GeoIPData(ip=ip, updated_timestamp=datetime.now())

            data = GeoIPData(
                ip=ip,
                state=geocoder_data.state,
                country=geocoder_data.country,
                city=geocoder_data.city,
                updated_timestamp=datetime.now(),
            )

            await self._save_geoip_data(data)
            return data
        except RequestException:
            logger.error("Request exception on get geoip. ip=%s", ip)
            return GeoIPData(ip=ip, updated_timestamp=datetime.now())
        except Exception as unexpected_exception:
            logger.error(
                "Unexpected exception on get geoi. ip=%s, exception=%s",
                ip,
                unexpected_exception,
            )
            return GeoIPData(ip=ip, updated_timestamp=datetime.now())

    async def _save_geoip_data(self, data: GeoIPData):
        """
        Сохраняет информацию о геолокации по IP.
        Для существующего IP информация обновляется.
        """
        sql_build = build_model(data)
        sql = f"""
            insert into "geoip" ({sql_build.field_names})
            values ({sql_build.placeholders})
            on conflict (ip) do update
            set ({sql_build.field_names}) = ({sql_build.placeholders})
        """

        async with self._db.acquire() as c:
            await c.execute(sql, *sql_build.values)
