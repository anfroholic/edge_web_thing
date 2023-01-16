import boards.iris as iris
import struct
import uasyncio
import utime

index = 0
current_callback = None

def send(msg, arb):
    iris.can.send(msg, arb)


def do_it(*args):
    global the_do_it
    current_callback()

def do_head_clamp(*args):
    global current_callback
    global index
    print('doing head clamp')

    iris.can.subs.pop(1051)
    
     # stack light
    send(b'\x00', 996)
    utime.sleep_ms(15)
    send(b'\x01', 995)
    
    # illum buttons
    send(b'\x00', 1091)
    utime.sleep_ms(15)
    
    # move clamp
    send(b'\x01', 1192)
    utime.sleep_ms(2500)
    send(b'\x00', 1192)
    utime.sleep_ms(1000)
    
    # stack light
    send(b'\x01', 996)
    utime.sleep_ms(15)
    send(b'\x00', 995)
    utime.sleep_ms(15)
    send(b'\x01', 999)
    utime.sleep_ms(500)
    send(b'\x00', 999)
    utime.sleep_ms(15)
    
    index += 1
    
    send(b'\x00\x00\x00', 1692)
    send(b'assem', 790)
    utime.sleep_ms(15)
    send(b'bly', 791)
    utime.sleep_ms(15)
    send(b'comp', 792)
    utime.sleep_ms(15)
    send(b'lete', 793)
    utime.sleep_ms(15)


def do_legs_clamp(*args):
    global current_callback
    global index
    
    print('getting ready to do leg clamp')
    iris.can.subs.pop(1052)
    
    # stack light
    send(b'\x00', 996)
    utime.sleep_ms(15)
    send(b'\x01', 995)
    
    # illum buttons
    send(b'\x00', 1092)
    utime.sleep_ms(15)
    
    # move clamp
    send(struct.pack('f', 0), 286)
    utime.sleep_ms(15)
    send(struct.pack('f', 50), 286)
    utime.sleep(5)
    
    # stack light
    send(b'\x01', 996)
    utime.sleep_ms(15)
    send(b'\x00', 995)
    utime.sleep_ms(15)
    
    # illum buttons
    send(b'\x01', 1091)
    utime.sleep_ms(15)
    
    # lcd
    send(b'pick_', 790)
    utime.sleep_ms(15)
    send(b'head', 791)
    utime.sleep_ms(15)
    send(b'place_', 792)
    utime.sleep_ms(15)
    send(b'body', 793)
    utime.sleep_ms(15)

    current_callback = do_head_clamp
    iris.can.subs[1051] = 69
    print('finished leg clamp')
    

async def start_lego():
    global index
    global current_callback
    print('starting lego')
    # set stacklight
    send(b'\x01', 996)
    send(struct.pack('BBB', index, index, index), 1695)
    await uasyncio.sleep_ms(15)
    send(b'pick_', 790)
    await uasyncio.sleep_ms(15)
    send(b'legs', 791)
    await uasyncio.sleep_ms(15)
    send(b'pick_', 792)
    await uasyncio.sleep_ms(15)
    send(b'torso', 793)
    await uasyncio.sleep_ms(15)
    send(b'\x01', 1092)
    
    current_callback = do_legs_clamp
    iris.can.subs[1052] = 69
    
    