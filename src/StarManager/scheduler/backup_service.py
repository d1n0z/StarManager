import asyncio
import tempfile
from datetime import datetime
from pathlib import Path

import yadisk
from loguru import logger

from StarManager.core.config import settings
from StarManager.tgbot.bot import bot as tgbot


class BackupService:
    def __init__(self):
        self.backup_lock = asyncio.Lock()

    async def create_backup(self) -> None:
        if self.backup_lock.locked():
            logger.warning("Backup already in progress, skipping")
            return

        async with self.backup_lock:
            now = datetime.now().isoformat(timespec="seconds").replace(":", "-")
            filename = f"{settings.database.name}-{now}.sql.gz"
            temp_dir = Path(tempfile.gettempdir())
            backup_path = temp_dir / filename

            try:
                proc = await asyncio.create_subprocess_shell(
                    f'PGPASSWORD="{settings.database.password}" '
                    f'pg_dump -h {settings.database.host} -p {settings.database.port} '
                    f'-U {settings.database.user} {settings.database.name} | gzip > {backup_path}',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                _, stderr = await proc.communicate()

                if proc.returncode != 0 or not backup_path.exists() or backup_path.stat().st_size < 1000:
                    raise Exception(f"pg_dump failed: {stderr.decode() if stderr else 'empty file'}")

                drive = yadisk.AsyncClient(token=settings.yandex.token)
                async with drive:
                    await drive.upload(
                        str(backup_path),
                        f"/StarManager/backups/{filename}",
                        timeout=36000,
                    )
                    link = await drive.get_download_link(f"/StarManager/backups/{filename}")

                backup_path.unlink()
                await self._cleanup_old_backups()

                await tgbot.send_message(
                    chat_id=settings.telegram.chat_id,
                    message_thread_id=settings.telegram.backup_thread_id,
                    text=f"<a href='{link}'>{filename}</a>",
                    parse_mode="HTML",
                )
            except Exception:
                logger.exception("Backup failed")
                if backup_path.exists():
                    backup_path.unlink()

    async def _cleanup_old_backups(self) -> None:
        try:
            drive = yadisk.AsyncClient(token=settings.yandex.token)
            async with drive:
                files = []
                async for item in drive.listdir("/StarManager/backups"):
                    if item.name and item.name.endswith(".sql.gz"):
                        files.append((item.name, item.created))

                files.sort(key=lambda x: x[1], reverse=True)

                if len(files) > 7:
                    for filename, _ in files[7:]:
                        await drive.remove(f"/StarManager/backups/{filename}")
        except Exception:
            logger.exception("Failed to cleanup old backups")


backup_service = BackupService()