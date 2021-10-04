












some_thing_state = 1
some_thing_can_id = 1
some_thing = Pin(22, Pin.IN, Pin.PULL_UP)

if some_thing.value() != some_thing_state:
    some_thing_state = not some_thing_state
    arb = self_broadcast + some_thing_can_id
    print('some_thing state: ' + str(some_thing_state))
    send(arb, [reverse(some_thing_state)])




some_thing_prev = 0
some_thing_state = 0
some_thing_can_id = 7  # this id is counting from 50 for broadcasts
some_thing = ADC(Pin(34))
some_thing.atten(ADC.ATTN_11DB)
some_thing.width(ADC.WIDTH_12BIT)

some_thing_state = int(round(some_thing.read())/16)
if abs(some_thing_prev - some_thing_state) > 1:
    some_thing_prev = some_thing_state
    send(some_thing_can_id + self_broadcast, [some_thing_state])
