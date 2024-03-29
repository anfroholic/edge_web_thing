
page = None

def web_page(connections, sd_files=None):

    html = """
<html>
    <head>
        <title>Evezor Web Interface</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="icon" href="data:,">
        <style>html{font-family: Helvetica; display:inline-block; margin: 0px auto; text-align: center;}
  h1{color: #0F3376; padding: 2vh;}p{font-size: 1.5rem;}.button{display: inline-block; background-color: #e7bd3b; border: none;
  border-radius: 4px; color: white; padding: 16px 40px; text-decoration: none; font-size: 30px; margin: 2px; cursor: pointer;}
  .button2{background-color: #4286f4;}.button3{background-color: #06876f;}.button4{background-color: #eb3440;}</style>
    </head>
    <body>
    <h1>Evezor Web Interface</h1>
    <p>SD Contents:</p> <strong>""" + sd_files + """</strong>

    <p>
    <a href="/cnc"><button class="button button2">cnc</button></a>
    <a href="/led=off"><button class="button button2">neo off</button></a>
    <a href="/led=on"><button class="button">neo on</button></a>
    <a href="/?mount_sd"><button class="button button4">mount sd</button></a>
    </p>
    
    <p>
    <a href="/reset"><button class="button button3">reset</button></a>
    <a href="/light_show"><button class="button button3">light show</button></a>
    <a href="/broadcast"><button class="button button3">broadcast</button></a>
    <a href="/!broadcast"><button class="button button3">!broadcast</button></a>
    <a href="/demo_1"><button class="button button2">demo_1</button></a>
    </p>
    <br><br>
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
    <label for="sub_num">Broadcast ID:</label>
    <input type="text" id="sub_num" name="sub_num"><br><br>
    <label for="send_id">Subscriber ID:</label>
    <input type="text" id="send_id" name="send_id"><br><br>
    <input type="submit" value="Submit">
    </form>

    <br><br><p><strong>Upload Program</strong></p>

    <form action="/prog">
    <label for="prog">Program:</label>
    <input type="text" id="prog" name="prog"><br><br>
    <input type="submit" value="Submit">
    </form>
    <p><strong>Connections:</strong></p> """ + connections + """
</html>
"""
    return html

def parse_can(action):
    mess = [b.split('=')[1] for b in action.split('&')]
    arb_id = mess.pop(0)
    return {'mess': mess, 'arb_id': arb_id}

def parse_sub(action):
    sub = [b.split('=')[1] for b in action.split('&')]
    return {'brdcst': sub[0], 'sub': sub[1]}
    
