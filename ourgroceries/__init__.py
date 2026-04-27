#!/usr/bin/env python

import re
import json
import aiohttp
import logging

from .exceptions import InvalidLoginException


_LOGGER = logging.getLogger(__name__)

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
FORM_VALUE_ACTION = 'sign-in'

# actions to preform on post api
ACTION_GET_LIST = 'getList'
ACTION_GET_LISTS = 'getLists'

ACTION_ITEM_CROSSED_OFF = 'setItemCrossedOff'
ACTION_ITEM_ADD = 'insertItem'
ACTION_ITEM_ADD_ITEMS = 'insertItems'
ACTION_ITEM_REMOVE = 'deleteItem'
ACTION_ITEM_RENAME = 'changeItemValue'

ACTION_LIST_CREATE = 'createList'
ACTION_LIST_REMOVE = 'deleteList'
ACTION_LIST_RENAME = 'renameList'

ACTION_GET_MASTER_LIST = 'getMasterList'
ACTION_GET_CATEGORY_LIST = 'getCategoryList'
ACTION_GET_ITEM_CATEGORY = 'getItemCategory'

ACTION_ITEM_CHANGE_VALUE = 'changeItemValue'
ACTION_LIST_DELETE_ALL_CROSSED_OFF = 'deleteAllCrossedOffItems'
REGEX_MASTER_LIST_ID = r'g_masterListUrl = "/your-lists/list/(\S*)"'
ATTR_CATEGORY_ID = 'categoryId'  # same key as ATTR_ITEM_CATEGORY; kept for master-list helpers
ATTR_ITEM_NEW_VALUE = 'newValue'

# regex to get team id
REGEX_TEAM_ID = r'g_teamId = "(.*)";'
REGEX_STATIC_METALIST = r'g_staticMetalist = (\[.*\]);'

# post body attributes
ATTR_LIST_ID = 'listId'
ATTR_LIST_NAME = 'name'
ATTR_LIST_TYPE = 'listType'

ATTR_ITEM_ID = 'itemId'
ATTR_ITEM_CROSSED = 'crossedOff'
ATTR_ITEM_VALUE = 'value'
ATTR_ITEM_CATEGORY = 'categoryId'
ATTR_ITEM_NOTE = 'note'
ATTR_ITEM_NAME = 'itemName'
ATTR_ITEMS = 'items'
ATTR_COMMAND = 'command'
ATTR_TEAM_ID = 'teamId'
ATTR_SHARE_ID = 'shareId'
ATTR_LOCALE = 'locale'
ATTR_GUESS = 'guess'
ATTR_IS_FROM_RECIPE = 'isFromRecipe'
ATTR_KNOWN_LISTS = 'knownLists'

# properties of returned data
PROP_LIST = 'list'
PROP_ITEMS = 'items'


def add_crossed_off_prop(item):
    """Adds crossed off prop to any items that don't have it."""
    item[ATTR_ITEM_CROSSED] = item.get(ATTR_ITEM_CROSSED, False)
    return item


def list_item_to_payload(item, list_id):
    """Maps a list item (scalar value or a tuple (value, category, note)) to payload"""
    if isinstance(item, str):
        payload = {
            ATTR_ITEM_VALUE: item
        }
    else:
        item = item + (None, None)
        payload = {
            ATTR_ITEM_VALUE: item[0],
            ATTR_ITEM_CATEGORY: item[1],
            ATTR_ITEM_NOTE: item[2]
        }
    payload[ATTR_LIST_ID] = list_id
    return payload


class OurGroceries():
    def __init__(self, username, password, locale='en-US'):
        """Set Our Groceries username and password."""
        self._username = username
        self._password = password
        self._session_key = None
        self._team_id = None
        self._locale = locale

    async def login(self):
        """Logs into Our Groceries."""
        await self._get_session_cookie()
        await self._get_team_id()
        await self._get_master_list_id()
        _LOGGER.debug('ourgroceries logged in')
        return True

    async def _get_session_cookie(self):
        """Gets the session cookie value."""
        _LOGGER.debug('ourgroceries _get_session_cookie')
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
                        _LOGGER.debug('ourgroceries found _session_key {}'.format(self._session_key))
                if not self._session_key:
                    _LOGGER.error('ourgroceries Could not find cookie session')
                    raise InvalidLoginException('Could not find session cookie')

    async def _get_team_id(self):
        """Gets the team id for a user."""
        _LOGGER.debug('ourgroceries _get_team_id')
        cookies = {COOKIE_KEY_SESSION: self._session_key}
        async with aiohttp.ClientSession(cookies=cookies) as session:
            async with session.get(YOUR_LISTS) as resp:
                responseText = await resp.text()
                self._team_id = re.findall(REGEX_TEAM_ID, responseText)[0]
                _LOGGER.debug('ourgroceries found team_id {}'.format(self._team_id))
                static_metalist = json.loads(re.findall(REGEX_STATIC_METALIST, responseText)[0])
                categoryList = [list for list in static_metalist if list['listType'] == 'CATEGORY'][0]
                self._category_id = categoryList['id']
                _LOGGER.debug('ourgroceries found category_id {}'.format(self._category_id))

    async def _get_master_list_id(self):
        """Gets the master list id for a user."""
        _LOGGER.debug('ourgroceries _get_master_list_id')
        cookies = {COOKIE_KEY_SESSION: self._session_key}
        async with aiohttp.ClientSession(cookies=cookies) as session:
            async with session.get(YOUR_LISTS) as resp:
                responseText = await resp.text()
                self._master_list_id = re.findall(REGEX_MASTER_LIST_ID, responseText)[0]
                _LOGGER.debug('ourgroceries found master_list_id {}'.format(self._master_list_id))

    async def get_my_lists(self, known_lists=None):
        """
        Get our grocery lists.

        The current API expects ``knownLists`` (like the web client): an array of
        ``{listId, versionId}`` for lists the client already knows. Pass ``[]`` or
        omit for a full refresh (same as first page load).
        """
        _LOGGER.debug('ourgroceries get_my_lists')
        if known_lists is None:
            kl = []
        else:
            kl = []
            for i in known_lists:
                lid = i.get('id') or i.get('listId')
                if not lid:
                    continue
                has_items = i.get('itemsSet', False)
                ver = (i.get('versionId') or '') if has_items else ''
                kl.append({'listId': lid, 'versionId': ver})
        return await self._post(ACTION_GET_LISTS, {ATTR_KNOWN_LISTS: kl})

    async def get_item_category(self, item_name, note='', guess=True):
        """
        Ask the server which category fits this item (same as the web UI when auto-categorize is on).

        :param item_name: Item text (same as insertItem ``value``).
        :param note: Note string; use '' to match the web client.
        :param guess: Must be True for automatic guessing.
        :return: Parsed JSON; expect ``categoryId`` when a category was resolved.
        """
        _LOGGER.debug('ourgroceries get_item_category')
        other_payload = {
            ATTR_ITEM_NAME: item_name,
            ATTR_ITEM_NOTE: '' if note is None else note,
            ATTR_GUESS: bool(guess),
            ATTR_SHARE_ID: None,
            ATTR_LOCALE: self._locale,
        }
        return await self._post(ACTION_GET_ITEM_CATEGORY, other_payload)

    async def get_category_items(self):
        """Get category items."""
        _LOGGER.debug('ourgroceries get_category_items')
        other_payload = {ATTR_LIST_ID: self._category_id}
        data = await self._post(ACTION_GET_LIST, other_payload)
        return data

    async def get_list_items(self, list_id):
        """Get an our grocery list's items."""
        _LOGGER.debug('ourgroceries get_list_items')
        other_payload = {ATTR_LIST_ID: list_id}
        data = await self._post(ACTION_GET_LIST, other_payload)
        data[PROP_LIST][PROP_ITEMS] = list(map(add_crossed_off_prop, data[PROP_LIST][PROP_ITEMS]))
        return data

    async def create_list(self, name, list_type='SHOPPING'):
        """Create a new shopping list."""
        _LOGGER.debug('ourgroceries create_list')
        other_payload = {
            ATTR_LIST_NAME: name,
            ATTR_LIST_TYPE: list_type.upper(),
        }
        return await self._post(ACTION_LIST_CREATE, other_payload)

    async def create_category(self, name):
        """Create a new category."""
        _LOGGER.debug('ourgroceries create_category')
        other_payload = {
            ATTR_ITEM_VALUE: name,
            ATTR_LIST_ID: self._category_id,
        }
        return await self._post(ACTION_ITEM_ADD, other_payload)

    async def toggle_item_crossed_off(self, list_id, item_id, cross_off=False):
        """Toggles a lists's item's crossed off property."""
        _LOGGER.debug('ourgroceries toggle_item_crossed_off')
        other_payload = {
            ATTR_LIST_ID: list_id,
            ATTR_ITEM_ID: item_id,
            ATTR_ITEM_CROSSED: cross_off,
        }
        return await self._post(ACTION_ITEM_CROSSED_OFF, other_payload)

    async def add_item_to_list(self, list_id, value, category="uncategorized", auto_category=False, note=None):
        """Add a new item to a list.

        When ``auto_category`` is True, calls ``getItemCategory`` with ``guess=True`` (same as the
        current web app), then ``insertItem`` with the returned ``categoryId``. If no category is
        returned, falls back to omitting ``categoryId`` on insert (legacy behavior).
        """
        _LOGGER.debug('ourgroceries add_item_to_list')
        note_str = '' if note is None else note

        if auto_category:
            guessed = await self.get_item_category(value, note_str, True)
            category_resolved = None
            if isinstance(guessed, dict):
                category_resolved = guessed.get(ATTR_ITEM_CATEGORY)

            other_payload = {
                ATTR_LIST_ID: list_id,
                ATTR_ITEM_VALUE: value,
                ATTR_ITEM_NOTE: note_str,
                ATTR_IS_FROM_RECIPE: False,
                ATTR_SHARE_ID: None,
                ATTR_LOCALE: self._locale,
            }
            if category_resolved:
                other_payload[ATTR_ITEM_CATEGORY] = category_resolved
            else:
                _LOGGER.warning(
                    'ourgroceries getItemCategory returned no categoryId; insertItem omits categoryId',
                )

            return await self._post(ACTION_ITEM_ADD, other_payload)

        other_payload = {
            ATTR_LIST_ID: list_id,
            ATTR_ITEM_VALUE: value,
            ATTR_ITEM_CATEGORY: category,
            ATTR_ITEM_NOTE: note,
        }
        return await self._post(ACTION_ITEM_ADD, other_payload)

    async def add_items_to_list(self, list_id, items):
        """
        Add many items to a list.

        :param items sequence of items, each being just a value, or a tuple (value, category, note).
        """
        _LOGGER.debug('ourgroceries add_items_to_list')
        other_payload = {
            ATTR_ITEMS: [list_item_to_payload(i, list_id) for i in items]
        }
        return await self._post(ACTION_ITEM_ADD_ITEMS, other_payload)

    async def remove_item_from_list(self, list_id, item_id):
        """Remove an item from a list."""
        _LOGGER.debug('ourgroceries remove_item_from_list')
        other_payload = {
            ATTR_LIST_ID: list_id,
            ATTR_ITEM_ID: item_id,
        }
        return await self._post(ACTION_ITEM_REMOVE, other_payload)

    async def get_master_list(self):
        """Get an our grocery list's items."""
        _LOGGER.debug('ourgroceries get_list_items')
        other_payload = {ATTR_LIST_ID: self._master_list_id}
        return await self._post(ACTION_GET_LIST, other_payload)

    async def get_category_list(self):
        """Get our grocery lists."""
        _LOGGER.debug('ourgroceries get_master_list')
        other_payload = {ATTR_TEAM_ID: self._team_id}
        return await self._post(ACTION_GET_CATEGORY_LIST, other_payload)

    async def delete_list(self, list_id):
        """Create a new shopping list."""
        _LOGGER.debug('ourgroceries create_list')
        other_payload = {
            ATTR_LIST_ID: list_id,
            ATTR_TEAM_ID: self._team_id,
        }
        return await self._post(ACTION_LIST_REMOVE, other_payload)

    async def delete_all_crossed_off_from_list(self, list_id):
        """delete all crossed off itemsn from a list."""
        _LOGGER.debug('ourgroceries remove_item_from_list')
        other_payload = {
            ATTR_LIST_ID: list_id,
        }
        return await self._post(ACTION_LIST_DELETE_ALL_CROSSED_OFF, other_payload)

    async def add_item_to_master_list(self, value, category_id):
        """Add a new item to a list."""
        _LOGGER.debug('ourgroceries add_item_to_list')
        other_payload = {
            ATTR_LIST_ID: self._master_list_id,
            ATTR_ITEM_VALUE: value,
            ATTR_CATEGORY_ID: category_id,
        }
        return await self._post(ACTION_ITEM_ADD, other_payload)

    async def change_item_on_list(self, list_id, item_id, category_id, value):
        """Add a new item to a list."""
        _LOGGER.debug('ourgroceries add_item_to_list')
        other_payload = {
            ATTR_ITEM_ID: item_id,
            ATTR_LIST_ID: list_id,
            ATTR_ITEM_NEW_VALUE: value,
            ATTR_CATEGORY_ID: category_id,
            ATTR_TEAM_ID: self._team_id,
        }
        return await self._post(ACTION_ITEM_CHANGE_VALUE, other_payload)

    async def _post(self, command, other_payload=None):
        """Post a command to the API."""
        if not self._session_key:
            await self.login()

        cookies = {COOKIE_KEY_SESSION: self._session_key}
        payload = {ATTR_COMMAND: command}

        if self._team_id:
            payload[ATTR_TEAM_ID] = self._team_id

        if other_payload:
            payload = {**payload, **other_payload}

        async with aiohttp.ClientSession(cookies=cookies) as session:
            async with session.post(YOUR_LISTS, data=payload) as resp:
                resp.raise_for_status()
                # Site responses may omit or vary Content-Type; still JSON body.
                return await resp.json(content_type=None)
