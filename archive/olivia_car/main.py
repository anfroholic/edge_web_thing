from OpenGL.GL import *
from OpenGL.GLU import *
import pygame
import Numeric
import sys
from pygame.locals import *

class DrawObject:
    def __init__(self):
        self.color = [0.0, 0.0, 0.0, 1.0]
        self.translate = [0.0, 0.0, 0.0]
        self.rotate = [0.0, 0.0, 0.0, 1.0]
        self.scale = [1.0, 1.0, 1.0]
        self.type = None
        self.filled = False
        self.pts = []

    def draw(self):
        """Draws the object.

        This could probably made faster if self.type was not a string
        """
        glColor(self.color)
        glTranslate(self.translate[0], self.translate[1], self.translate[2])
        glRotate(self.rotate[0], self.rotate[1], self.rotate[2], self.rotate[3])
        glScale(self.scale[0], self.scale[1], self.scale[2])
        if self.type == "RECT":
            if self.filled:
                glBegin(GL_POLYGON);
            else:
                glBegin(GL_LINE_LOOP);
            glVertex(self.pts[0], self.pts[1])
            glVertex(self.pts[2], self.pts[1])
            glVertex(self.pts[2], self.pts[3])
            glVertex(self.pts[0], self.pts[3])
            glEnd()
        elif self.type == "CIRC":
            if self.filled:
                glBegin(GL_POLYGON)
            else:
                glBegin(GL_LINE_LOOP)
            circleSections = 100;
            for x in xrange(circleSections):
                angle = 2 * Numeric.pi * x / circleSections
                glVertex2f(self.pts[0]+Numeric.cos(angle)*self.pts[2],
                           self.pts[1]+Numeric.sin(angle)*self.pts[2])
            glEnd()
        elif self.type == "PLINE":
            glBegin(GL_LINE_STRIP)
            for x in xrange(0,len(self.pts),2):
                glVertex(self.pts[x], self.pts[x+1])
            glEnd()
        elif self.type == "POLY":
            if self.filled:
                glBegin(GL_POLYGON)
            else:
                glBegin(GL_LINE_LOOP)
            for x in xrange(0, len(self.pts),2):
                glVertex(self.pts[x], self.pts[x+1])
            glEnd()

    def __repr__(self):
        return "<DrawObject:%s color=%r translate=%r rotate=%r pts=%r>" % (self.type, self.color, self.translate, self.rotate, self.pts)




def load(filename):
    """Reads in a file.

    Here are the valid commands for the file:

    # Add a rectangle:
    ar <ll-corner-x> <ll-corner-y> <ur-corner-x> <ur-corner-y>

    # Add a circle:
    ac <center-x> <center-y> <radius>

    # Add a polyline:
    al <num-vertices> <v1-x> <v1-y> <v2-x> <v2-y> ...

    # Add a polygon:
    ap <num-vertices> <v1-x> <v1-y> <v2-x> <v2-y> ...

    # Set color:
    sc <R> <G> <B>

    # Set fill mode:
    sf <0.0|1.0>

    # Set translation:
    st <trans-x> <trans-y>

    # Set rotation:
    sr <deg-angle>

    # Set scale:
    ss <scale-x> <scale-y>

    The translations carry over until the next object but are NOT cumulative.  Thus
    doing a "st 1.0 1.0" twice in a row does NOT do the same as "st 2.0 2.0".

    @type  filename: string
    @param filename: name of the file to load

    @rtype: list
    @return: list of DrawObject
    """

    f = open(filename)
    currentColor = [0.0, 0.0, 0.0, 1.0]
    currentTranslate = [0.0, 0.0, 0.0]
    currentFilled = False
    currentRotate = [0.0, 0.0, 0.0, 1.0]
    currentScale = [1.0, 1.0, 1.0]
    retArr = []
    for thisline in f.xreadlines():
        cmd = thisline.split()
        if len(cmd) != 0 and thisline[0] != "#":
            o = None
            args = [float(x) for x in cmd[1:]]
            cmd = cmd[0].lower()
            if cmd == "sc":
                currentColor[0:3] = args[0:3]
            elif cmd == "st":
                currentTranslate[0:2] = args[0:2]
            elif cmd == "sr":
                currentRotate[0] = args[0]
            elif cmd == "sf":
                if args[0] > 0.5:
                    currentFilled = True
                else:
                    currentFilled = False
            elif cmd == "ss":
                currentScale[0:2] = args[0:2]
            elif cmd == "ar":
                o = DrawObject()
                o.type = "RECT"
            elif cmd == "ac":
                o = DrawObject()
                o.type = "CIRC"
            elif cmd == "al":
                o = DrawObject()
                o.type = "PLINE"
                args = args[len(args)%2:]
            elif cmd == "ap":
                o = DrawObject()
                o.type = "POLY"
                args = args[len(args)%2:]
            if o:
                for x in xrange(len(currentColor)):
                    o.color[x] = currentColor[x]
                for x in xrange(len(currentTranslate)):
                    o.translate[x] = currentTranslate[x]
                o.filled = currentFilled
                for x in xrange(len(currentRotate)):
                    o.rotate[x] = currentRotate[x]
                o.pts = args
                for x in xrange(len(currentScale)):
                    o.scale[x] = currentScale[x]
                retArr.append(o)
    f.close()
    return retArr


def draw(objList):
    """Draws all the objects in the list

    @type  objList: list
    @param objList: list of objects to draw
    """
    glClear(GL_COLOR_BUFFER_BIT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(-10.0, 10.0, -10.0, 10.0, -1.0, 1.0)
    glMatrixMode(GL_MODELVIEW)

    for mem in objList:
        glPushMatrix()
        mem.draw()
        glPopMatrix()

    glFlush()

def resize((width, height)):
    """Handles a resize of the display

    @type  width: int
    @param width: new width of display
    @type  height: int
    @param heignt: int
    """
    if height == 0:
        height = 1
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(-10.0, 10.0, -10.0, 10.0, -1.0, 1.0)
    glViewport(0, 0, width, height)

def init():
    """Initializes the OpenGL display
    """
    glShadeModel(GL_SMOOTH)
    glClearColor(0.0, 0.0, 0.0, 0.0)
    glClearDepth(1.0)
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
    glLineWidth(2.0)

def main(infile):
    """Runs the main program

    The program is quit by hitting ESCAPE or closing the window

    @type infile: string
    @param infile: name of file to load
    """
    pygame.init()
    pygame.display.set_mode((500,500), OPENGL|DOUBLEBUF)
    pygame.display.set_caption(sys.argv[0])
    resize((500,500))
    init()
    objects = load(infile)

    frames = 0
    ticks = pygame.time.get_ticks()
    while 1:
        event = pygame.event.poll()
        if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
            break;
        draw(objects)
        pygame.display.flip()
        frames = frames + 1

    print "fps:  %d" % ((frames * 1000) / (pygame.time.get_ticks() - ticks))


if __name__ == "__main__":
    main(sys.argv[1])
