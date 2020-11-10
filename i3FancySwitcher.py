from i3ipc import Connection, Event

i3 = Connection()

tree = await i3.get_tree()
print(tree)
