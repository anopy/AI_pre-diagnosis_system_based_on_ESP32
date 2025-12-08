def do_connect():
    import network
    wlan1 = network.WLAN(network.STA_IF)
    wlan1.active(True)
    if not wlan1.isconnected():
        print('connecting to network...')
        wlan1.connect('iPhone 16', '0d000721')
        while not wlan1.isconnected():
            pass
    print('WLAN connected')
do_connect()