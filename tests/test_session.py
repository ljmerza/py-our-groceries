"""Session, re-login and timeout tests against a local fake of the OurGroceries site.

Nothing here talks to the real service. Run with:

    python -m unittest discover -s tests -p 'test_session.py'
"""
import asyncio
import unittest
from unittest import mock

import aiohttp
from aiohttp import web

import ourgroceries
from ourgroceries import OurGroceries

LISTS_PAGE = (
    'g_teamId = "TEAM";\n'
    'g_staticMetalist = [{"listType": "CATEGORY", "id": "CAT"}];\n'
    'g_masterListUrl = "/your-lists/list/MASTER"\n'
)
SIGN_IN_PAGE = '<html>please sign in</html>'


class FakeOurGroceries:
    """The three endpoints the client uses, with switches for the failures under test."""

    def __init__(self):
        self.valid_keys = set()
        self.sign_ins = 0
        self.lists_page_hits = 0
        self.api_hits = 0
        # switches
        self.reject_sign_in = False
        self.reject_every_command = False
        self.break_lists_page = False
        self.stall_commands = False
        self.stall_lists_page = False
        # set every time the lists page is requested
        self.lists_page_requested = asyncio.Event()
        # command number (1 based) -> event its response waits for
        self.command_gates = {}
        # stalled requests hang until the server stops
        self._stopping = asyncio.Event()
        self._runner = None
        self.base_url = None

    async def start(self):
        app = web.Application()
        app.add_routes([
            web.post('/sign-in', self._sign_in),
            web.get('/your-lists/', self._lists_page),
            web.post('/your-lists/', self._command),
        ])
        self._runner = web.AppRunner(app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, '127.0.0.1', 0)
        await site.start()
        port = self._runner.addresses[0][1]
        # the client's cookie jar ignores cookies from bare IP addresses, so use the name
        self.base_url = 'http://localhost:{}'.format(port)

    async def stop(self):
        self._stopping.set()
        await self._runner.cleanup()

    def expire_sessions(self):
        self.valid_keys.clear()

    async def _sign_in(self, request):
        self.sign_ins += 1
        if self.reject_sign_in:
            # a wrong password gets the sign in page again and no session cookie
            return web.Response(text=SIGN_IN_PAGE, content_type='text/html')
        key = 'KEY{}'.format(self.sign_ins)
        self.valid_keys.add(key)
        response = web.Response(text='ok')
        response.set_cookie(ourgroceries.COOKIE_KEY_SESSION, key)
        return response

    async def _lists_page(self, request):
        self.lists_page_hits += 1
        self.lists_page_requested.set()
        if self.stall_lists_page:
            await self._stopping.wait()
        # let the other requests in flight make progress before answering
        await asyncio.sleep(0.02)
        signed_in = request.cookies.get(ourgroceries.COOKIE_KEY_SESSION) in self.valid_keys
        if self.break_lists_page or not signed_in:
            return web.Response(text=SIGN_IN_PAGE, content_type='text/html')
        return web.Response(text=LISTS_PAGE, content_type='text/html')

    async def _command(self, request):
        self.api_hits += 1
        gate = self.command_gates.get(self.api_hits)
        key = request.cookies.get(ourgroceries.COOKIE_KEY_SESSION)
        payload = await request.json()
        if self.stall_commands:
            await self._stopping.wait()
        if gate:
            await gate.wait()
        if self.reject_every_command or key not in self.valid_keys:
            # what the real site answers for an expired session: 401 with an empty body
            return web.Response(status=401)
        return web.json_response({'command': payload.get('command'), 'teamId': payload.get('teamId'), 'key': key})


def point_client_at(test, base_url):
    """Sends the client's requests to base_url for the rest of the test."""
    for name, value in (
        ('BASE_URL', base_url),
        ('SIGN_IN', '{}/sign-in'.format(base_url)),
        ('YOUR_LISTS', '{}/your-lists/'.format(base_url)),
    ):
        patcher = mock.patch.object(ourgroceries, name, value)
        patcher.start()
        test.addCleanup(patcher.stop)


class SessionTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.server = FakeOurGroceries()
        await self.server.start()
        self.addAsyncCleanup(self.server.stop)
        point_client_at(self, self.server.base_url)
        self.og = OurGroceries('user', 'password', timeout=0.5)

    async def login_reaches_lists_page(self):
        """Waits until a login in flight has its session cookie and is asking for the lists page."""
        await asyncio.wait_for(self.server.lists_page_requested.wait(), timeout=5)

    async def test_first_call_logs_in(self):
        result = await self.og.get_my_lists()

        self.assertEqual(result['teamId'], 'TEAM')
        self.assertEqual(self.server.sign_ins, 1)

    async def test_valid_session_is_reused(self):
        await self.og.login()

        await self.og.get_my_lists()
        await self.og.get_my_lists()

        self.assertEqual(self.server.sign_ins, 1)

    async def test_expired_session_logs_in_again_once(self):
        await self.og.login()
        self.server.expire_sessions()

        result = await self.og.get_my_lists()

        self.assertEqual(result['key'], 'KEY2')
        self.assertEqual(result['teamId'], 'TEAM')
        self.assertEqual(self.server.sign_ins, 2)

    async def test_second_401_raises_after_one_more_login(self):
        await self.og.login()
        self.server.reject_every_command = True

        with self.assertRaises(aiohttp.ClientResponseError) as raised:
            await self.og.get_my_lists()

        self.assertEqual(raised.exception.status, 401)
        self.assertEqual(self.server.sign_ins, 2)
        self.assertEqual(self.server.api_hits, 2)

    async def test_wrong_password_raises_invalid_login(self):
        self.server.reject_sign_in = True

        with self.assertRaises(ourgroceries.InvalidLoginException):
            await self.og.get_my_lists()

        self.assertIsNone(self.og._session_key)

    async def test_changed_password_raises_invalid_login_when_the_session_expires(self):
        await self.og.login()
        self.server.expire_sessions()
        self.server.reject_sign_in = True

        with self.assertRaises(ourgroceries.InvalidLoginException):
            await self.og.get_my_lists()

    async def test_stalled_request_times_out_and_next_call_works(self):
        await self.og.login()
        self.server.stall_commands = True

        with self.assertRaises(asyncio.TimeoutError):
            await self.og.get_my_lists()

        self.server.stall_commands = False
        result = await self.og.get_my_lists()
        self.assertEqual(result['teamId'], 'TEAM')
        self.assertEqual(self.server.sign_ins, 1)

    async def test_login_is_timed_out_too(self):
        self.server.stall_lists_page = True

        with self.assertRaises(asyncio.TimeoutError):
            await self.og.login()

        self.assertIsNone(self.og._session_key)

    async def test_failed_login_leaves_no_session_and_next_call_recovers(self):
        self.server.break_lists_page = True

        with self.assertRaises(IndexError):
            await self.og.login()

        self.assertIsNone(self.og._session_key)

        self.server.break_lists_page = False
        result = await self.og.get_my_lists()
        self.assertEqual(result['teamId'], 'TEAM')

    async def test_cancelled_login_leaves_no_session_and_next_call_recovers(self):
        self.server.stall_lists_page = True

        login = asyncio.ensure_future(self.og.login())
        await self.login_reaches_lists_page()
        login.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await login

        self.assertIsNone(self.og._session_key)

        self.server.stall_lists_page = False
        result = await self.og.get_my_lists()
        self.assertEqual(result['teamId'], 'TEAM')

    async def test_concurrent_first_calls_share_one_login(self):
        results = await asyncio.gather(self.og.get_my_lists(), self.og.get_my_lists(), self.og.get_my_lists())

        self.assertEqual([result['teamId'] for result in results], ['TEAM'] * 3)
        self.assertEqual(self.server.sign_ins, 1)

    async def test_concurrent_calls_share_one_login_when_the_session_expires(self):
        await self.og.login()
        self.server.expire_sessions()

        results = await asyncio.gather(self.og.get_my_lists(), self.og.get_my_lists(), self.og.get_my_lists())

        self.assertEqual([result['key'] for result in results], ['KEY2'] * 3)
        self.assertEqual(self.server.sign_ins, 2)

    async def test_late_401_does_not_break_a_login_in_flight(self):
        """One call is half way through logging in again when another call's 401 arrives."""
        await self.og.login()
        self.server.expire_sessions()
        self.server.lists_page_requested.clear()
        # the second command's 401 is held back until the first call's new login reaches the lists page
        self.server.command_gates[2] = self.server.lists_page_requested

        results = await asyncio.gather(self.og.get_my_lists(), self.og.get_my_lists())

        self.assertEqual([result['key'] for result in results], ['KEY2', 'KEY2'])
        self.assertEqual([result['teamId'] for result in results], ['TEAM', 'TEAM'])
        self.assertEqual(self.server.sign_ins, 2)

    async def test_call_waits_for_a_login_in_flight(self):
        """A call made while the first login is half done must not go out without a team id."""
        login = asyncio.ensure_future(self.og.login())
        await self.login_reaches_lists_page()

        result = await self.og.get_my_lists()
        await login

        self.assertEqual(result['teamId'], 'TEAM')
        self.assertEqual(self.server.sign_ins, 1)


class EventLoopTests(unittest.TestCase):
    def test_one_client_works_across_event_loops(self):
        """The README calls the same client from more than one asyncio.run()."""
        og = OurGroceries('user', 'password', timeout=0.5)

        async def concurrent_calls():
            server = FakeOurGroceries()
            await server.start()
            point_client_at(self, server.base_url)
            try:
                return await asyncio.gather(og.get_my_lists(), og.get_my_lists())
            finally:
                await server.stop()

        # each run starts a new server, so the second one rejects the first one's session
        for _ in range(2):
            results = asyncio.run(concurrent_calls())
            self.assertEqual([result['teamId'] for result in results], ['TEAM', 'TEAM'])


if __name__ == '__main__':
    unittest.main()
