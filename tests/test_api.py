

import asyncio
from ourgroceries import OurGroceries

username = ''
password = ''

og = OurGroceries(username, password)
asyncio.run(og.login())

my_lists = asyncio.run(og.get_my_lists())
print(my_lists)

my_todo_list = asyncio.run(og.get_list_items(list_id=''))
print(my_todo_list)