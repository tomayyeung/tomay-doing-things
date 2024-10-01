import pygame, sys, math
from pygame.locals import *

# ---------------------- define constants
# pygame
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400
FPS = 60

# colors
GREEN = (0, 170, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
WHITE = (255, 255, 255)

# game constants
PLAYER_MASS = 30
PLAYER_SIZE = 20
SELECTED_THICKNESS = 5
MAX_VEL = FPS*2/3 # yo idk what these numbers mean don't ask about units lmao
RESISTANCE = 0.9 # throw this onto stuff to simulate friction/air resistance/physics??

# ---------------------- define classes
class PhysicalObject:
    def __init__(self, x, y, mass, size, color):
        self.x = x
        self.y = y
        self.mass = mass
        self.size = size
        self.color = color

        self.velX = 0
        self.velY = 0

    def draw(self, surf):
        pygame.draw.circle(surf, self.color, (self.x, self.y), self.size)

    def updatePos(self):
        self.x += self.velX
        self.y += self.velY

        self.velX *= RESISTANCE
        self.velY *= RESISTANCE

    # does NOT check for collision, only handles it
    def handleCollision(self, other):
        # define initial values
        velAX, velAY = self.velX, self.velY
        velBX, velBY = other.velX, other.velY
        collisionAngle = angle(self.x, self.y, other.x, other.y)

        # -------- angle calculation
        # with other object mass = 0, new velocity direction doesn't change
        # with other object mass = inf, new velocity direction reflects off other object
        selfOriginalAngle = angle(velAX, velAY, 0, 0)
        selfMaxAngle = math.pi+collisionAngle+(collisionAngle-selfOriginalAngle)
        angleDiff = selfMaxAngle-selfOriginalAngle
        selfFinalAngle = selfOriginalAngle + (-1/(other.mass/self.mass) + 1)*angleDiff

        # -------- magnitude calculation
        # the more directly it hits the other object, the less velocity it keeps & the more it transfers
        selfMagnitude = abs(collisionAngle-selfOriginalAngle)/math.pi * 5 * other.mass/self.mass * RESISTANCE
        otherMagnitude = abs(selfMagnitude-xyToVector(self.velX,self.velY)[0]) * 1.5 * self.mass/other.mass * RESISTANCE

        self.velX, self.velY = vectorToXY(selfMagnitude, selfFinalAngle)
        other.velX, other.velY = vectorToXY(otherMagnitude, collisionAngle)

class Player(PhysicalObject):
    selected = False
    def __init__(self, x, y, color):
        super().__init__(x, y, PLAYER_MASS, PLAYER_SIZE, color)

    def draw(self, surf):
        super().draw(surf)
        if self.selected:
            pygame.draw.circle(surf, WHITE, (self.x, self.y), self.size, SELECTED_THICKNESS)

# ---------------------- define functions
def distance(x1, y1, x2, y2):
    return math.sqrt( (x1-x2)**2 + (y1-y2)**2 )

def angle(x1, y1, x2, y2):
    return math.atan2( (y2-y1), (x2-x1) )

def xyToVector(velX, velY):
    magnitude = distance(0, 0, velX, velY)
    direction = angle(0, 0, velX, velY)
    return magnitude, direction

def vectorToXY(magnitude, direction):
    x = math.cos(direction)*magnitude
    y = math.sin(direction)*magnitude
    return x, y

def main():
    # initialize pygame
    pygame.init()
    DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    DISPLAYSURF.fill(GREEN)
    pygame.display.set_caption("Soccer")
    clock = pygame.time.Clock()

    # create objects
    player1 = Player(100, 100, BLUE)
    player2 = Player(200, 180, RED)

    while 1:
        # handle input
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_a:
                    player1.velX = 25
                    player1.velY = 25

        mouseX, mouseY = pygame.mouse.get_pos()

        player1.selected = distance(mouseX, mouseY, player1.x, player1.y) <= PLAYER_SIZE
        player2.selected = distance(mouseX, mouseY, player2.x, player2.y) <= PLAYER_SIZE

        if distance(player1.x, player1.y, player2.x, player2.y) <= PLAYER_SIZE*2:
            player1.handleCollision(player2)

        player1.updatePos()
        player2.updatePos()

        # display
        DISPLAYSURF.fill(GREEN)
        player1.draw(DISPLAYSURF)
        player2.draw(DISPLAYSURF)

        # update window
        pygame.display.update()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
    