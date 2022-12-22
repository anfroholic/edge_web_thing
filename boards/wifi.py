
my_ip = None

def wifi_connect(*args):
    print('begin wifi')
    import network
    import machine
    import utime
    global my_ip
    if args:
        _ssid, password = args
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        if not wlan.isconnected():
            print('connecting to network...')
            wlan.connect(_ssid, password)
        while not wlan.isconnected():
            utime.sleep(.5)
            print('.', end='')
        print('.')
        my_ip = wlan.ifconfig()[0]
    else:
        print('creating access point')
        ap = network.WLAN(network.AP_IF) # create access-point interface
        utime.sleep_ms(100)
        try:
            ap.config(essid='evezor') # set the SSID of the access point
        except OSError:
            import machine
            machine.reset()
        utime.sleep_ms(100)
        ap.active(True)         # activate the interface
        my_ip = ap.ifconfig()[0]
    print(f'my ip address is: http://{my_ip}')