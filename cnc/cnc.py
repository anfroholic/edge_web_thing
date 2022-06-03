
def web_page():


  html = """
<html>
    <head>
        <title>Evezor Web Interface</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="icon" href="data:,">
        <style>html{font-family: Helvetica; display:inline-block; margin: 0px auto; text-align: center;}
  h1{color: #0F3376; padding: 2vh;}p{font-size: 1.5rem;}.button{display: inline-block; background-color: #e7bd3b; border: none;
  border-radius: 4px; color: white; padding: 16px 40px; text-decoration: none; font-size: 30px; margin: 2px; cursor: pointer;}
  .button2{background-color: #4286f4;}.button3{background-color: #06876f;}.button4{background-color: #E1341E;}</style>
    </head>
    <body>
    <h1>Evezor Web Interface</h1>
    


    <p><a href="/home"><button class="button button2">home</button></a>
    <a href="/led=off"><button class="button button2">neo off</button></a><a href="/?led=on"><button class="button">neo on</button></a>
    <a href="/connect"><button class="button button2">unmount sd</button></a><a href="/?run"><button class="button button2">run</button></a></p>

    <p><a href="/?get_state"><button class="button button3">get_state</button></a><a href="/?unlock"><button class="button button3">unlock</button></a>
    <a href="/?sleep"><button class="button button3">sleep</button></a><a href="/?wake_up"><button class="button button3">wake up</button></a></p>

    <p><a href="/?homex"><button class="button button2">homex</button></a><a href="/?homey"><button class="button button2">homey</button></a>
    <a href="/?homexy"><button class="button button2">homexy</button></a><a href="/?homez"><button class="button button2">homez</button></a>
    <a href="/?homea"><button class="button button2">homea</button></a><a href="/?homeb"><button class="button button2">homeb</button></a></p>
    <p><a href="/?mount_sd"><button class="button button3">mount sd</button></a><a href="/?nuke"><button class="button button4">NUKE</button></a><a href="/?get_line"><button class="button button3">get_line</button></a></p>

    <p><a href="/?ring_on"><button class="button button2">ring_on</button></a><a href="/?ring_off"><button class="button button2">ring_off</button></a>
    <a href="/?suck_on"><button class="button button2">suck_on</button></a><a href="/?suck_off"><button class="button button2">suck_off</button></a></p>

    <p><a href="/?spindle_on"><button class="button button2">spindle_on</button></a><a href="/?spindle_off"><button class="button button2">spindle_off</button></a>
    <a href="/?vise_open"><button class="button button2">vise_open</button></a><a href="/?vise_close"><button class="button button2">vise_close</button></a></p>

    <p><a href="/?coolant_on"><button class="button button2">coolant_on</button></a><a href="/?coolant_off"><button class="button button2">coolant_off</button></a><a href="/?run_export"><button class="button button2">run_export.txt</button></a></p>

    <br><br>
    <p><strong>Move Machine</strong></p>

    <form action="/move.php">
    <label for="send_x">X:</label>
    <input type="text" id="x" name="x"><br><br>
    <label for="send_y">Y:</label>
    <input type="text" id="y" name="y"><br><br>
    <label for="send_z">Z:</label>
    <input type="text" id="z" name="z"><br><br>
    <label for="send_a">A:</label>
    <input type="text" id="a" name="a"><br><br>
    <input type="submit" value="Submit">
    </form>

    <p><strong>file</strong></p>
    <form action="/file.php">
    <label for="file">file:</label>
    <input type="text" id="file" name="file"><br><br>
    <input type="submit" value="Submit">
    </form>

    <p><strong>direct</strong></p>
    <form action="/direct.php">
    <label for="direct">direct:</label>
    <input type="text" id="direct" name="direct"><br><br>
    <input type="submit" value="Submit">
    </form>

    <p><strong>feeder</strong></p>
    <form action="/feeder.php">
    <label for="feeder">feeder:</label>
    <input type="text" id="feeder" name="feeder"><br><br>
    <input type="submit" value="Submit">
    </form>
    </body></html>"""
  return html

class GRBL:
    def __init__(self, sd, can, uart):
        self.sd = sd
        self.can = can
        self.uart = uart
        
        self.connection_state = 'connected'
        self.is_running = 'False'

        self.to_parse = ''
        self.index = 0
        self.line = ''
        self.state = ''
        self.sd_state = 'unmounted'
        self.file_blurb = ''

        self.blurb_index = 0
        self.j_blurb = {}
        self.f = None
        self.queue = {}
        self.modal = ['move.linear', 'move.rapid', 'sleep']

    def parse_move(self, request):
        """
        parse move that came from web socket
        """
        end = request.find(' HTTP')
        action = request[14:end]
        action += '&'
        # print('parsing request')
        # print(action)
        axes = ['x', 'y', 'z', 'a']
        parsed = {}
        for axis in axes:
            index = action.find('&')
            if action[2: index] != '':
                parsed[axis] = action[2: index]
            action = action[(index + 1):]
        # print(parsed)
        parsed['command'] = 'move.linear'
        parsed['feed'] = 2000
        return parsed

    def send(self, message):
        """
        send message to grbl board
        """
        if self.connection_state == 'connected':
            self.uart.write(message + '\n')
        else:
            print(message)

    def get_line(self):
        """
        find line in text from grbl over uart
        """
        if self.to_parse != '':
            # print('trying to parse')
            self.index = self.to_parse.find('\r')
            # print(self.to_parse)
            # print(self.index)
            if len(self.to_parse) > 0: # check for empty line
                if self.index > 0:
                    self.line = self.to_parse[0:self.index]
                    self.to_parse = self.to_parse[(self.index + 2):]
                else:
                    self.to_parse = self.to_parse[2:]
                self.handler(self.line)

    def handler(self, line):
        """
        handler for incomming uart comms from grbl
        this also will send blurbs to grbl when running file from sd card
        """
        # print(line)
        if line == 'ok':
            if self.is_running == 'True':
                # print('todo: finish handler')
                self.get_next()
        elif line[0] == '<':
            print('update machine info')
            print(line)
            seg = line.split('|')
            grbl.state = seg[0][1:]
        elif line == '[MSG:Evezor]':
            print('got evezor message')
        else:
            print(line)
            # print('maybe need some other command thing')

    def get_next(self):
        """
        gets next line from sd card file
        """
        if self.queue:
            # if a message is in queue it probably means it's a can bus message.
            # a dwell has been sent in it's place last round and now it should send
            print('message in queue')
            print(self.queue)
            mess = [self.queue['val']]
            can.send(mess, the_conversions[self.queue['command']])
            self.queue = {}

        if len(self.file_blurb) < 200:
            self.file_blurb += self.f.read(100)

        self.blurb_index = self.file_blurb.find('\r')
        if len(self.file_blurb) > 0:
            if self.blurb_index > 0:
                self.j_blurb = json.loads(self.file_blurb[0:self.blurb_index])
                self.file_blurb = self.file_blurb[(self.blurb_index + 2):]
                # self.j_blurb = json.loads(self.blurb)
                # print(self.j_blurb)
                self.parse_message(self.j_blurb)
        else:
            print('must be the end of the file, maybe consider stop running')
            if self.queue:
                print('oops, guess there was one more command')
                self.get_next()
            else:
                self.is_running = 'False'
                print('closing file')
                self.f.close()
                # print('unmounting sd')
                # uos.umount('/sd')


    def parse_message(self, msg):
        """
        send message to converter or handle canbus requests
        """
        # print('parser')
        if msg['command'] in self.modal:
            # print('modal command')
            self.send(convert(**msg))
        elif 'command' in msg:
            # we need to wait until grbl is finished working on modal commands
            # and returns ok
            # print('pausing')
            self.queue = msg
            self.send('G4 P.01')
        else:
            print(msg)
            self.get_next()

    def can_send(self, mess, arb):
        can.send(mess, arb)