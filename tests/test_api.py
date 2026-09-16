

import asyncio
from ourgroceries import OurGroceries, make_delete_item_edit_record

username = ''
password = ''

og = OurGroceries(username, password)
asyncio.run(og.login())

my_lists = asyncio.run(og.get_my_lists())
print(my_lists)

list_id = ''
my_todo_list = asyncio.run(og.get_list_items(list_id=list_id))
print(my_todo_list)

# Delete all crossed-off (done) items.
crossed_off_item_ids = [item["id"] for item in my_todo_list["list"]["items"] if "crossedOffAt" in item]
print(crossed_off_item_ids)

result = asyncio.run(og.edit_items(list_id, [make_delete_item_edit_record(item_id)
                                             for item_id in crossed_off_item_ids]))
print(result)
