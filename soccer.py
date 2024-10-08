import pygame, sys
import pygame.locals
import numpy as np

# ---------------------- define constants
# pygame
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# colors
GREEN = (0, 170, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (190, 190, 0)

# game constants
FIELD_WIDTH = 600
FIELD_HEIGHT = 400
X_GAP = (SCREEN_WIDTH-FIELD_WIDTH)/2
Y_GAP = (SCREEN_HEIGHT-FIELD_HEIGHT)/2
GOAL_DEPTH = 45
GOAL_HEIGHT = 100
GOAL_TOP = Y_GAP+FIELD_HEIGHT/2-GOAL_HEIGHT/2
GOAL_BOTTOM = GOAL_TOP+GOAL_HEIGHT
LEFT_GOAL_BACK = X_GAP-GOAL_DEPTH
RIGHT_GOAL_BACK = SCREEN_WIDTH-X_GAP+GOAL_DEPTH
BALL_MASS = 15
BALL_SIZE = 10
PLAYER_MASS = 30
PLAYER_SIZE = 20
SELECTED_THICKNESS = 5
MAX_VEL = FPS*0.2 # yo idk what these numbers mean don't ask about units lmao
AIM_TWEAK = 10 # smaller number = less difference bt big aim and small aim
RESISTANCE = 0.95 # throw this onto stuff to simulate friction/air resistance/physics??

# ---------------------- define classes
class PhysicalObject:
    def __init__(self, x, y, mass, size, color):
        self.x = x
        self.y = y
        self.mass = mass
        self.size = size # radius of circle
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
        # we handle the moving object differently from the stationary object :skull:
        if (self.velX, self.velY) == (0, 0):
            a = self
            b = other
        else:
            a = other
            b = self
        # if two moving objects collide then the physics will die but is okay!

        # define initial values
        velAX, velAY = a.velX, a.velY
        #velBX, velBY = other.velX, other.velY
        collisionAngle = angle(a.x, a.y, b.x, b.y)

        # -------- angle calculation
        # with other object mass = 0, new velocity direction doesn't change
        # with other object mass = inf, new velocity direction reflects off other object
        aOriginalAngle = angle(velAX, velAY, 0, 0)
        aMaxAngle = np.pi+collisionAngle+(collisionAngle-aOriginalAngle)
        angleDiff = aMaxAngle-aOriginalAngle
        aFinalAngle = aOriginalAngle + (-1/(b.mass/a.mass) + 1)*angleDiff

        # -------- magnitude calculation
        # the more directly it hits the other object, the less velocity it keeps & the more it transfers
        aMagnitude = abs(collisionAngle-aOriginalAngle)/np.pi * 5 * b.mass/a.mass * RESISTANCE
        bMagnitude = abs(aMagnitude-xyToVector(a.velX,a.velY)[0]) * 1.5 * a.mass/b.mass * RESISTANCE

        a.velX, a.velY = vectorToXY(aMagnitude, aFinalAngle)
        b.velX, b.velY = vectorToXY(bMagnitude, collisionAngle)
    
    # detects and handles collision with the wall
    def handleWallCollision(self):
        # field walls
        # left/right, take into account goal
        if (self.x-self.size < X_GAP or self.x+self.size > X_GAP+FIELD_WIDTH) and (self.y-self.size < GOAL_TOP or self.y+self.size > GOAL_BOTTOM):
            self.velX = -self.velX
        # top/bottom
        if (self.y-self.size < Y_GAP or self.y+self.size > Y_GAP+FIELD_HEIGHT):
            self.velY = -self.velY
        
        # goal walls
        # back walls
        if (self.x-self.size < LEFT_GOAL_BACK or self.x+self.size > RIGHT_GOAL_BACK):
            self.velX = -self.velX
        # top/bottom walls, take into account object has to be inside goal
        if (self.y-self.size < GOAL_TOP or self.y+self.size > GOAL_BOTTOM) and (self.x < X_GAP or self.x > X_GAP + FIELD_WIDTH):
            self.velY = -self.velY


class Player(PhysicalObject):
    hovered = False
    def __init__(self, x, y, color):
        super().__init__(x, y, PLAYER_MASS, PLAYER_SIZE, color)

    def draw(self, surf):
        super().draw(surf)
        if self.hovered:
            pygame.draw.circle(surf, WHITE, (self.x, self.y), self.size, SELECTED_THICKNESS)

# ---------------------- define functions
def distance(x1, y1, x2, y2):
    return np.sqrt( (x1-x2)**2 + (y1-y2)**2 )

def angle(x1, y1, x2, y2):
    return np.atan2( (y2-y1), (x2-x1) )

def xyToVector(velX, velY):
    magnitude = distance(0, 0, velX, velY)
    direction = angle(0, 0, velX, velY)
    return magnitude, direction

def vectorToXY(magnitude, direction):
    x = np.cos(direction)*magnitude
    y = np.sin(direction)*magnitude
    return x, y

def main():
    # initialize pygame
    pygame.init()
    DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    DISPLAYSURF.fill(GREEN)
    pygame.display.set_caption("Soccer")
    clock = pygame.time.Clock()
    pygame.font.init()
    displayFont = pygame.font.SysFont("Comic Sans MS", 80)

    # create objects
    ball = PhysicalObject(600, 400, BALL_MASS, BALL_SIZE, WHITE)
    player1 = Player(200, 200, BLUE)
    player2 = Player(200, 460, RED)

    objects = [ball, player1, player2]
    players = objects[1:]

    selected = None
    startingX, startingY, = 0,0
    #aimX = 0
    #aimY = 0
    while 1:
        # handle input
        # hold click & drag to aim
        mouseX, mouseY = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.locals.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.locals.KEYDOWN:
                if event.key == pygame.locals.K_a:
                    player1.velX = 30
                    player1.velY = 30
            
            if event.type == pygame.locals.MOUSEBUTTONDOWN:
                # on click, check if anything's selected
                # if not, check the cursor is on any player to mark it as selected
                if selected is None:
                    for player in players:
                        if distance(mouseX, mouseY, player.x, player.y) <= PLAYER_SIZE:
                            # distance from any player is within the player size = mouse is on the circle
                            startingX, startingY = mouseX, mouseY
                            player.hovered = True # mark to draw the circle around it
                            selected = player
                            break
            
            if event.type == pygame.locals.MOUSEBUTTONUP:
                # on unclick, check if anything's selected
                # if so, check if the cursor's outside the player
                if selected: # THANKS ALEX
                    # Calculate the drag distance (difference between release and starting point)
                    deltaX = mouseX - startingX
                    deltaY = mouseY - startingY
                
                    # Calculate the velocity to be applied based on the drag distance
                    aimX = deltaX / AIM_TWEAK
                    aimY = deltaY / AIM_TWEAK

                    # Limit the velocity to MAX_VEL
                    magnitude = min(np.sqrt(aimX**2 + aimY**2), MAX_VEL)
                    direction = np.atan2(aimY, aimX)

                    # Apply the velocity
                    selected.velX = -magnitude * np.cos(direction)
                    selected.velY = -magnitude * np.sin(direction)

                    player.hovered = False
                    selected = None
                # if not, unselect the thing
                else:
                    player.hovered = False
                    selected = None

        # check for wall collision
        for obj in objects:
            # update twice to handle goal corners!
            obj.handleWallCollision()
            obj.updatePos()
            obj.handleWallCollision()
            obj.updatePos()

        pairs = [(a, b) for i, a in enumerate(objects) for b in objects[i+1:]]
        for obj1, obj2 in pairs:
            if distance(obj1.x, obj1.y, obj2.x, obj2.y) <= obj1.size+obj2.size:
                obj1.handleCollision(obj2)
        

        # display
        DISPLAYSURF.fill(GREEN)
        pygame.draw.rect(DISPLAYSURF, WHITE, pygame.Rect(X_GAP, Y_GAP, FIELD_WIDTH, FIELD_HEIGHT), 1) # field lines
        pygame.draw.rect(DISPLAYSURF, WHITE, pygame.Rect(LEFT_GOAL_BACK, GOAL_TOP, GOAL_DEPTH, GOAL_HEIGHT), 1) # left goal
        pygame.draw.rect(DISPLAYSURF, WHITE, pygame.Rect(X_GAP+FIELD_WIDTH, GOAL_TOP, GOAL_DEPTH, GOAL_HEIGHT), 1) # right goal
        pygame.draw.line(DISPLAYSURF, YELLOW, (X_GAP, GOAL_TOP), (X_GAP, GOAL_BOTTOM), 4) # left goal line
        pygame.draw.line(DISPLAYSURF, YELLOW, (X_GAP+FIELD_WIDTH, GOAL_TOP), (X_GAP+FIELD_WIDTH, GOAL_BOTTOM), 4) # right goal line
        for obj in objects:
            obj.draw(DISPLAYSURF)
        if selected:
            pygame.draw.line(DISPLAYSURF, WHITE, (selected.x, selected.y), (mouseX, mouseY), SELECTED_THICKNESS)
        if (ball.x < 0):
            displayText = displayFont.render("RED SCORE", True, WHITE)
            DISPLAYSURF.blit(displayText, (100, 100))
        if (ball.x > X_GAP+FIELD_WIDTH):
            displayText = displayFont.render("BLUE SCORE", True, WHITE)
            DISPLAYSURF.blit(displayText, (100, 100))

        # update window
        pygame.display.update()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
    