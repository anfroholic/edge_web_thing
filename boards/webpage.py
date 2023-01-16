import boards.iris as iris
import uasyncio as asyncio
import lego
import boards.wifi as wifi

wifi.wifi_connect('Grammys_IoT', 'AAGI96475')

connections = ''

cnc_callback = None

def web_page():
    global connections

    html = """
<html>
    <head>
        <title>Evezor Web Interface</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="icon" href="data:,">
        <style>html{font-family: Trebuchet MS; display:inline-block; margin: 0px auto; text-align: center;}
  h1{color: #0F3376; padding: 2vh;}p{font-size: 1.5rem;}.button{display: inline-block; background-color: #e7bd3b; border: none;
  border-radius: 4px; color: white; padding: 16px 40px; text-decoration: none; font-size: 30px; margin: 2px; cursor: pointer;}
  .button2{background-color: #4286f4;}.button3{background-color: #06876f;}.button4{background-color: #eb3440;}</style>
    </head>
    <body>
    <h1>Evezor Web Interface</h1>
    <p>Connections:</p> <strong>""" + connections + """</strong>
    <p>SD Contents:</p> <strong>""" + 'sd_files' + """</strong>


    <p><a href="/led=off"><button class="button button2">neo off</button></a>
    <a href="/led=on"><button class="button">neo on</button></a>
    <a href="/?mount_sd"><button class="button button4">mount sd</button></a>
    </p>

    <p>
    <a href="/reset"><button class="button button3">reset</button></a>
    <a href="/light_show"><button class="button button3">light show</button></a>
    <a href="/broadcast"><button class="button button3">broadcast</button></a>
    <a href="/!broadcast"><button class="button button3">!broadcast</button></a>
    <a href="/auto"><button class="button button2">auto</button></a>
    </p>
    <a href="/close_clamp"><button class="button button3">close_clamp</button></a>
    <a href="/open_clamp"><button class="button button3">open_clamp</button></a>
    <a href="/home_x"><button class="button button3">home_x</button></a>
    <a href="/unlock"><button class="button button3">unlock</button></a>
    <a href="/start_lego"><button class="button button3">start_lego</button></a>
    <a href="/test"><button class="button button3">test</button></a>
    <br><br>
    
    <div style="display: flex;">
    <div style="width: 49%;">
    <p><strong>Send CAN Message</strong></p>
    <form action="/can">
    <label for="send_arb">ARB:</label>
    <input type="text" id="send_arb" name="send_arb"><br><br>
    <label for="m0">m0:</label>
    <input type="text" id="m0" name="m0"><br>

    <label for="m1">m1:</label>
    <input type="text" id="m1" name="m1"><br>

    <label for="m2">m2:</label>
    <input type="text" id="m2" name="m2"><br>

    <label for="m3">m3:</label>
    <input type="text" id="m3" name="m3"><br>

    <label for="m4">m4:</label>
    <input type="text" id="m4" name="m4"><br>

    <label for="m5">m5:</label>
    <input type="text" id="m5" name="m5"><br>

    <label for="m6">m6:</label>
    <input type="text" id="m6" name="m6"><br>

    <label for="m7">m7:</label>
    <input type="text" id="m7" name="m7"><br>
    <input type="submit" value="Submit"></form>

    <br><br><p><strong>Create Subscriber</strong></p>

    <form action="/sub">
    <label for="sub_pid">Broadcast ID:</label>
    <input type="text" id="sub_pid" name="sub_pid"><br><br>
    <label for="pub_pid">Subscriber ID:</label>
    <input type="text" id="pub_pid" name="pub_id"><br><br>
    <input type="submit" value="Submit">
    </form>
    </div>
    <div style="width: 49%;">
    <br><br><p><strong>Upload Program</strong></p>

    <form action="/prog">
    <label for="prog">Program:</label>
    <input type="text" id="prog" name="prog"><br><br>
    <input type="submit" value="Submit">
    </form>
    
    
    <br><br><p><strong>Send Float</strong></p>
    
    <form action="/float">
    <label for="sub_pid">Arb ID:</label>
    <input type="text" id="arb_id" name="arb_id"><br><br>
    <label for="pub_pid">Float:</label>
    <input type="text" id="float" name="float"><br><br>
    <input type="submit" value="Submit">
    </form>
    
    <br><br><p><strong>Send String</strong></p>
    
    <form action="/string">
    <label for="sub_pid">Arb ID:</label>
    <input type="text" id="arb_id" name="arb_id"><br><br>
    <label for="pub_pid">String:</label>
    <input type="text" id="string" name="string"><br><br>
    <input type="submit" value="Submit">
    </form>
    
    <br><br><p><strong>Run Script</strong></p>
    
    <form action="/run_script">
    <label for="script">Script</label>
    <input type="text" id="script" name="script"><br><br>
    <input type="submit" value="Submit">
    </form>
    
    </div>
    </div>
    
    <form id="uploadbanner" enctype="multipart/form-data" method="post" action="file_upload">
   <input id="fileupload" name="myfile" type="file" />
   <input type="submit" value="submit" id="submit" />
    </form>

    </body></html>"""
    return html

    # -------------------------------------------------

def unquote_plus(s):

    s = s.replace("+", " ")
    arr = s.split("%")
    arr2 = [chr(int(x[:2], 16)) + x[2:] for x in arr[1:]]
    return arr[0] + "".join(arr2)

def parse_qs(s):
    res = {}
    if s:
        pairs = s.split("&")
        for p in pairs:
            vals = [unquote_plus(x) for x in p.split("=", 1)]
            if len(vals) == 1:
                vals.append(True)
            old = res.get(vals[0])
            if old is not None:
                if not isinstance(old, list):
                    old = [old]
                    res[vals[0]] = old
                old.append(vals[1])
            else:
                res[vals[0]] = vals[1]
    return res
      
    # -------------------------------------------------

def send_can(action):
    # example action
    # /can?send_arb=123&m0=1&m1=2&m2=3&m3=4&m4=4&m5=&m6=&m7=

    act = [a.split('=')[1] for a in action.split('&')]
    arb_id = int(act.pop(0))
    data = act[:act.index('')]
    data = [int(d) for d in data]
    print('sending', arb_id, data)
    iris.can.can.send(data, arb_id)

def make_sub(publisher, subscriber):
    global connections
    connections += f'<p>{publisher}: {subscriber}'
    board = (subscriber//100 * 100)
    if board == config.config['id']:
        iris.can.subs[publisher] = subscriber
    else:
        data = struct.pack('II', publisher, subscriber)
        iris.can.send(arb_id=board + 49, data=data)
        print(data, list(data))
        
def parse_sub(action):
    # example action
    # /sub?sub_pid=123&pub_id=456
    sub = [int(a.split('=')[1]) for a in action.split('&')]
    print(sub)
    make_sub(*sub)
    
def parse_float(action):
    # example action
    # /float?arb_id=163&float=-1563.5
    arb_id, data = [a.split('=')[1] for a in action.split('&')]
    arb_id, data = int(arb_id), struct.pack('f', float(data))
    print(arb_id, data)
    iris.can.send(arb_id=arb_id, data=data)
    
def parse_string(action):
    # example action
    # /string?arb_id=790&string=this
    arb_id, data = [a.split('=')[1] for a in action.split('&')]
    arb_id, data = int(arb_id), data.encode()
    print(arb_id, data)
    iris.can.send(arb_id=arb_id, data=data)

def parse_program(action):
    # example action
    # /prog?prog=126211941253119112521192126311951264049112650492125109951250099612520
    prog = action.split('=')[1]
    while(len(prog) > 0):
        make_sub(int(prog[:4]), int(prog[4:8]))
        # print(int(prog[:4]), int(prog[4:8]))
        prog = prog[8:]
        
def parse_script(action):
    # example action
    # /run_script?script=script.csv
    script = action.split('=')[1]
    # print(script)
    cnc_callback(script)
    

async def do_auto():
    print('auto starting')
    await asyncio.sleep_ms(1000)
    print('in the middle of auto1')
    await asyncio.sleep_ms(1000)
    print('in the middle of auto2')
    await asyncio.sleep_ms(1000)
    print('in the middle of auto3')
    await asyncio.sleep_ms(1000)
    print('in the middle of auto4')
    await asyncio.sleep_ms(1000)
    print('auto finished')

    # -------------------------------------------------

actions = {
    '/led=on': lambda: iris.neo_status.fill(0, 25, 0),
    '/led=off': lambda: iris.neo_status.fill(0, 0, 0),
    '/light_show': lambda: iris.can.can.send([1], 1),
    '/close_clamp': lambda: iris.can.send(b'\x01', 1192),
    '/open_clamp': lambda: iris.can.send(b'\x00', 1192),
    '/home_x': lambda: iris.can.send(b'\x01', 283),
    '/unlock': lambda: iris.can.send(b'\x01', 280)
    }


async def handle_client(reader, writer):
    request = (await reader.read(1024)).decode('ascii')
    # print(request)
    end = request.find(' HTTP')
    action = request[4:end]
    print(action)
    # process request
    if request.find('/can') == 4:
        send_can(action)
    elif request.find('/sub') == 4:
        parse_sub(action)
    elif request.find('/prog') == 4:
        parse_program(action)
    elif request.find('/float') == 4:
        parse_float(action)
    elif request.find('/string') == 4:
        parse_string(action)
    elif request.find('/run_script') == 4:
        parse_script(action)

    elif action == '/reset':
        # reset all boards
        global connections
        connections = ''
        iris.can.can.send([1], 2)

        
    elif action == '/broadcast':
        iris.can.can.send([1], 4)
        iris.broadcast_state = True
        iris.neo_status.fill(0, 12, 3)
    elif action == '/!broadcast':
        iris.can.can.send([0], 4)
        iris.broadcast_state = False
        iris.neo_status.fill(0, 0, 0)
    elif action == '/auto':
        this = asyncio.get_event_loop()
        this.create_task(do_auto())
    elif action == '/start_lego':
        loop = asyncio.get_event_loop()
        loop.create_task(lego.start_lego())
    elif action in actions:
        actions[action]()




# elif action == '/demo_1':
    #     demo_1()
    #
    # elif action.find('/item') == 0:
    #     load_file(action)
    #
    # elif action == '/?mount_sd':
    #     mount_sd()


    await writer.awrite(
        b'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n')
    await writer.awrite(web_page())
    await writer.aclose()
    return True

loop = asyncio.get_event_loop()
loop.create_task(asyncio.start_server(handle_client, wifi.my_ip, 80))

