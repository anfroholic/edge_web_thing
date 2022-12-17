import webrepl
import network
import utime


networks = {'evezor': 'drinkmaker', 'Grammys_IoT':'AAGI96475', 'Herrmann': 'storage18', 'PumpingStationOne': 'ps1frocks'}

def connect() -> bool:
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    aps = wlan.scan()
    for ap in aps:
        net = ap[0].decode('ascii')
        if net in networks:
            print('connecting to ' + net)
            wlan.connect(net, networks[net])

    timeout = utime.ticks_add(utime.ticks_ms(), 5000)
    while not wlan.isconnected():
        if utime.ticks_diff(timeout, utime.ticks_ms()) <= 0:
            print('wlan  connect failed')
            return False

        print(".", end = "")
        utime.sleep_ms(250)
    print('Connection successful')
    print(wlan.ifconfig())
    webrepl.start()
    return True
