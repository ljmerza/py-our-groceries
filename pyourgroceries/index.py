import re

import aiohttp
from bs4 import BeautifulSoup
from lxml import html


# urls used
BASE_URL = 'https://www.ourgroceries.com'
SIGN_IN = '{}/sign-in'.format(BASE_URL)
YOUR_LISTS = '{}/your-lists/'.format(BASE_URL)

# cookies
COOKIE_KEY_SESSION = 'ourgroceries-auth'

# form fields when logging in
FORM_KEY_USERNAME = 'emailAddress'
FORM_KEY_PASSWORD = 'password'
FORM_KEY_ACTION = 'action'
FORM_VALUE_ACTION = 'sign-me-in'

# actions to preform on post api
ACTION_GET_LIST = 'getList'
ACTION_GET_LISTS = 'getOverview'

# regex to get team id
REGEX_TEAM_ID = r'g_teamId = "(.*)";'

# post body attributes
ATTR_LIST_ID = 'listId'
ATTR_COMMAND = 'command'
ATTR_TEAM_ID = 'teamId'


class OurGroceries():
    def __init__(self, username, password):
        """Set Our Groceries username and password."""
        self._username = username
        self._password = password
        self._session_key = None
        self._team_id = None

    async def login(self):
        """Logs into Our Groceries."""
        await self._get_session_cookie()
        await self._get_team_id()

    async def _get_session_cookie(self):
        """Gets the session cookie value."""
        form_data = aiohttp.FormData()
        form_data.add_field(FORM_KEY_USERNAME, self._username)
        form_data.add_field(FORM_KEY_PASSWORD, self._password)
        form_data.add_field(FORM_KEY_ACTION, FORM_VALUE_ACTION)
        async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
            async with session.post(SIGN_IN, data=form_data):
                cookies = session.cookie_jar.filter_cookies(BASE_URL)
                for key, cookie in cookies.items():
                    if key == COOKIE_KEY_SESSION:
                        self._session_key = cookie.value
                if not self._session_key:
                    raise Exception('Could not find cookie session')

    async def _get_team_id(self):
        """Gets the team id for a user."""
        cookies = {COOKIE_KEY_SESSION: self._session_key}
        async with aiohttp.ClientSession(cookies=cookies) as session:
            async with session.get(YOUR_LISTS) as resp:
                responseText = await resp.text()
                for team_id in re.findall(REGEX_TEAM_ID, responseText):
                    self._team_id = team_id
                if not self._team_id:
                    raise Exception('Could not find team id')

    async def get_my_lists(self):
        """Get our grocery lists."""
        return await self._post(ACTION_GET_LISTS)

    async def get_list_items(self, list_id):
        """Get an our grocery list's items."""
        other_payload = {ATTR_LIST_ID: list_id}
        return await self._post(ACTION_GET_LIST, other_payload)
        
    async def _post(self, command, other_payload=None):
        """Post a command to the API."""
        if not self._session_key or not self._team_id:
            await self.login()

        cookies = {COOKIE_KEY_SESSION: self._session_key}
        payload = {ATTR_COMMAND: command, ATTR_TEAM_ID: self._team_id}
        if other_payload:
            payload = {**payload, **other_payload}

        async with aiohttp.ClientSession(cookies=cookies) as session:
            async with session.post(YOUR_LISTS, json=payload) as resp:
                return await resp.json()



# import asyncio
# username = ''
# password = ''
# og = OurGroceries(username, password)
# loop = asyncio.get_event_loop()
# loop.run_until_complete(og.get_my_lists())