import machine
import config
import uasyncio as asyncio
import boards.iris as iris

machine.freq(240000000)
import gc
gc.collect()


_board = __import__('boards.' + config.config['board'])
board = getattr(_board, config.config['board'])
print(f'{config.config["board"]} {config.config["version"]} imported on id {config.config["id"]}')

loop = asyncio.get_event_loop()

loop.create_task(iris.do_hbt())
loop.create_task(iris.can.chk())
loop.create_task(board.hw_chk())
loop.create_task(iris.fnc_chk())
gc.collect()
loop.run_forever()