import asyncio
from contextlib import suppress


def patch_aiobale():
    """Monkey-patch aiobale to fix known bugs."""
    try:
        from aiobale.client.client import Client, _CLIENTS
        from aiobale.logger import logger

        original_stop = Client.stop

        async def patched_stop(self):
            if self._stopped:
                return

            self._stopped = True

            client_id = self._me.id if self._me else "unknown"
            logger.info(f"Stopping client (Client: {client_id})...")

            if self._ping_task:
                self._ping_task.cancel()
                with suppress(asyncio.CancelledError):
                    await self._ping_task
                self._ping_task = None

            for task in list(self._tasks):
                task.cancel()

            for task in list(self._tasks):
                with suppress(asyncio.CancelledError):
                    await task

            if self.session and not self.session.is_closed():
                await self.session.close()

            if self in _CLIENTS:
                _CLIENTS.remove(self)

            logger.info(f"Client stopped cleanly (Client: {client_id}).")

        Client.stop = patched_stop

        original_start = Client.start

        async def patched_start(self, run_in_background: bool = False, signal_handling: bool = False):
            self._stopped = False
            await self._ensure_token_exists()

            loop = asyncio.get_running_loop()

            from aiobale.client.client import _install_global_signal_handlers
            if signal_handling:
                _install_global_signal_handlers(loop)

            async with self._lifespan(self):
                try:
                    while not self._stopped:
                        await self._cleanup_session()

                        async with self._lock:
                            try:
                                client_id = self._me.id if self._me else "unknown"
                                logger.info(f"Trying to connect... (Client: {client_id})")
                                await self.session.connect(self._Client__token)
                                await self.session.handshake_request()
                                logger.info(f"Connected successfully. (Client: {client_id})")

                                self._ping_task = self._create_task(self._ping_loop())
                                listen_task = self._create_task(self._safe_listen())
                            except Exception as e:
                                client_id = self._me.id if self._me else "unknown"
                                logger.error(f"Connection failed (Client: {client_id}): {e}")
                                await asyncio.sleep(5)
                                continue

                        if run_in_background:
                            return
                        else:
                            try:
                                await listen_task
                            except asyncio.CancelledError:
                                client_id = self._me.id if self._me else "unknown"
                                logger.info(f"Listening task cancelled (Client: {client_id}).")
                                break

                except KeyboardInterrupt:
                    client_id = self._me.id if self._me else "unknown"
                    logger.info(f"KeyboardInterrupt received, stopping client (Client: {client_id})...")
                    await self.stop()
                except Exception as e:
                    client_id = self._me.id if self._me else "unknown"
                    logger.error(f"Unhandled exception in start (Client: {client_id}): {e}")
                    await self.stop()
                    raise
                finally:
                    if self in _CLIENTS:
                        _CLIENTS.remove(self)

        Client.start = patched_start

    except ImportError:
        pass
