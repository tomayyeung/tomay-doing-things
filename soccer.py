import pygame, sys, random
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
BLACK = (0, 0, 0)

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
BALL_MASS = 8
BALL_SIZE = 10
PLAYER_MASS = 30
PLAYER_SIZE = 20
FRAG_MASS = 15
FRAG_SIZE = 3
MAX_FRAG_SIZE = 10
FRAG_VEL = FPS * 0.45
SELECTED_THICKNESS = 5
MAX_VEL = FPS*0.2 # yo idk what these numbers mean don't ask about units lmao
AIM_TWEAK = 10 # smaller number = less difference bt big aim and small aim
RESISTANCE = 0.97 # throw this onto stuff to simulate friction/air resistance/physics??

SPAWNS = ((FIELD_WIDTH/5, FIELD_HEIGHT/3), (FIELD_WIDTH/5,FIELD_HEIGHT*2/3), (FIELD_WIDTH/3, FIELD_HEIGHT/2))

# ---------------------- define classes
class PhysicalObject:
    def __init__(self, x, y, mass, size, color, type=""):
        self.x = x
        self.y = y
        self.mass = mass
        self.size = size # radius of circle
        self.color = color
        self.type = type

        self.v = pygame.Vector2()
        self.moving = self.v.magnitude() > 0.001

    def draw(self, surf):
        pygame.draw.circle(surf, self.color, (self.x, self.y), self.size)

    def updatePos(self):
        self.x += self.v.x
        self.y += self.v.y

        self.v *= RESISTANCE

        self.moving = self.v.magnitude() > 0.001

    # does NOT check for collision, only handles it
    def handleCollision(self, other):
        # detect if they're inside each other first ---------------------
        ang = angle(other.x, other.y, self.x, self.y)
        radii = self.size+other.size
        xDist, yDist = radii*np.cos(ang) - (self.x-other.x), radii*np.sin(ang) - (self.y-other.y)
        self.x += xDist/2
        self.y += yDist/2
        other.x -= xDist/2
        other.y -= yDist/2

        # collision physics ---------------------
        selfPrevAngle = self.v.as_polar()[1]
        otherPrevAngle = other.v.as_polar()[1]
        # calculate "surface" at which they collide
        normalVSelf = pygame.math.Vector2(0.001, 0)
        normalVSelf.rotate(np.atan2(self.y-other.y, self.x-other.x))
        normalVOther = normalVSelf.rotate(180) # flip 180 as the collision is opposite for other

        # if not moving, set initial angle to perpendicular facing into surface
        if not self.moving:
            self.v = normalVSelf.rotate(180)
        if not other.moving:
            other.v = normalVOther.rotate(180)

        # apply collision angle
        selfNewAngle = self.v.reflect(normalVSelf).as_polar()[1]
        otherNewAngle = other.v.reflect(normalVOther).as_polar()[1]

        # apply collision magnitude
        selfRatio = np.log10(self.mass/other.mass+1)
        otherRatio = np.log10(other.mass/self.mass+1)
        # new magnitude is based on: current magnitude; angle of collision * mass ratio * other's magnitude
        angleDiff = np.abs(otherPrevAngle-self.v.as_polar()[1])
        #selfNewMagnitude = self.v.magnitude()*0.5*self.mass/other.mass + angleDiff/180 * other.mass/self.mass * other.v.magnitude()*0.35
        selfNewMagnitude = (self.v.magnitude() * 0.8) + (angleDiff/180 * other.v.magnitude() * otherRatio)
        selfNewMagnitude = min(selfNewMagnitude, MAX_VEL) # limit magnitude to max
        self.v.from_polar((selfNewMagnitude, selfNewAngle)) # set the final new vel

        oAngleDiff = np.abs(selfPrevAngle-other.v.as_polar()[1])
        #otherNewMagnitude = other.v.magnitude()*0.5*other.mass/self.mass + oAngleDiff/180 * self.mass/other.mass * self.v.magnitude()*0.35
        otherNewMagnitude = (other.v.magnitude() * 0.8) + (oAngleDiff/180 * self.v.magnitude() * selfRatio)
        otherNewMagnitude = min(otherNewMagnitude, MAX_VEL)
        other.v.from_polar((otherNewMagnitude, otherNewAngle))
    
    # detects and handles collision with the wall
    def handleWallCollision(self):
        # field walls
        if (self.y-self.size < Y_GAP): # top
            self.v.y = -self.v.y
            self.y = Y_GAP + self.size
        if (self.y+self.size > Y_GAP+FIELD_HEIGHT): # bottom
            self.v.y = -self.v.y
            self.y = Y_GAP + FIELD_HEIGHT - self.size
        # take into account the goal for left/right
        if (self.y-self.size < GOAL_TOP or self.y+self.size > GOAL_BOTTOM):
            if (self.x-self.size < X_GAP): # left
                self.v.x = -self.v.x # reflect velocity horizontally
                self.x = X_GAP + self.size # move it out of the wall
            if (self.x+self.size > X_GAP+FIELD_WIDTH): # right
                self.v.x = -self.v.x
                self.x = X_GAP + FIELD_WIDTH - self.size
        
        # goal walls
        if (self.x-self.size < LEFT_GOAL_BACK): # left goal back
            self.v.x = -self.v.x
            self.x = LEFT_GOAL_BACK + self.size
        if (self.x+self.size > RIGHT_GOAL_BACK): # right goal back
            self.v.x = -self.v.x
            self.x = RIGHT_GOAL_BACK - self.size
        # take into account object has to be inside goal
        if (self.x < X_GAP or self.x > X_GAP + FIELD_WIDTH):
            if (self.y-self.size < GOAL_TOP): # goal top
                self.v.y = -self.v.y
                self.y = GOAL_TOP + self.size
            if (self.y+self.size > GOAL_BOTTOM): # goal bottom
                self.v.y = -self.v.y
                self.y = GOAL_BOTTOM - self.size


class Player(PhysicalObject):
    hovered = False
    def __init__(self, x, y, color):
        super().__init__(x, y, PLAYER_MASS, PLAYER_SIZE, color)

    def draw(self, surf):
        super().draw(surf)
        if self.hovered:
            pygame.draw.circle(surf, WHITE, (self.x, self.y), self.size, SELECTED_THICKNESS)

class Fragment(PhysicalObject):
    def __init__(self, x, y, mass, size, color):
        super().__init__(x, y, mass, size, color, "frag")

    def updatePos(self):
        if self.size < MAX_FRAG_SIZE:
            self.size += 1
        super().updatePos()
        
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

def spawnGrenade(objects, x, y):
    for i in range(0, 8):
        frag = Fragment(x, y, FRAG_MASS, FRAG_SIZE, BLACK)
        vel = pygame.math.Vector2()
        vel.scale_to_length(FRAG_VEL)
        vel.rotate_rad_ip(np.pi*i/4)
        frag.v = vel
        
        objects.append(frag)

def main():
    # initialize pygame
    pygame.init()
    DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    DISPLAYSURF.fill(GREEN)
    pygame.display.set_caption("Soccer")
    clock = pygame.time.Clock()
    pygame.font.init()
    displayFont = pygame.font.SysFont("krungthep", 80)
    scoreFont = pygame.font.SysFont("menlo", 30)

    # create objects
    # ball = PhysicalObject(SCREEN_WIDTH/2, SCREEN_HEIGHT/2, BALL_MASS, BALL_SIZE, WHITE)
    # objects = [ball]
    # for spawn in SPAWNS:
    #     objects.append(Player(X_GAP + spawn[0], Y_GAP + spawn[1], BLUE))
    #     objects.append(Player(SCREEN_WIDTH - X_GAP - spawn[0], Y_GAP + spawn[1], RED))

    # freshObjects = objects.copy()

    # players = objects[1:]
    objects = []

    blueScore = 0
    redScore = 0
    scored = True

    selected = None
    startingX, startingY, = 0,0

    #aimX = 0
    #aimY = 0
    turn = BLUE
    while 1:
        
        # let it run until everything stops moving, then reset
        if scored:
            stoppedMoving = True
            for obj in objects:
                if obj.v.magnitude() > 0.001:
                    stoppedMoving = False
                    break
            
            if stoppedMoving:
                ball = PhysicalObject(SCREEN_WIDTH/2, SCREEN_HEIGHT/2, BALL_MASS, BALL_SIZE, WHITE)
                objects = [ball]
                for spawn in SPAWNS:
                    objects.append(Player(X_GAP + spawn[0], Y_GAP + spawn[1], BLUE))
                    objects.append(Player(SCREEN_WIDTH - X_GAP - spawn[0], Y_GAP + spawn[1], RED))

                #freshObjects = objects.copy()

                players = objects[1:]
                
                scored = False
                continue

        # handle input
        # hold click & drag to aim
        mouseX, mouseY = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.locals.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.locals.KEYDOWN:
                if event.key == pygame.locals.K_a:
                    #spawnGrenade(objects, random.randint(X_GAP, X_GAP + FIELD_WIDTH), random.randint(Y_GAP, Y_GAP+FIELD_HEIGHT))
                    spawnGrenade(objects, mouseX, mouseY)
            
            
            if event.type == pygame.locals.MOUSEBUTTONDOWN:
                # on click, check if anything's selected
                # if not, check the cursor is on any player to mark it as selected
                if selected is None:
                    for player in players:
                        if player.color == turn and distance(mouseX, mouseY, player.x, player.y) <= PLAYER_SIZE:
                            # distance from any player is within the player size = mouse is on the circle
                            startingX, startingY = mouseX, mouseY
                            player.hovered = True # mark to draw the circle around it
                            selected = player
                            break
            
            if event.type == pygame.locals.MOUSEBUTTONUP:
                # on unclick, check if anything's selected
                # if so, check if the cursor's outside the player
                if selected and distance(mouseX, mouseY, selected.x, selected.y) > PLAYER_SIZE: # THANKS ALEX
                    # # Calculate the drag distance (difference between release and starting point)
                    # deltaX = mouseX - startingX
                    # deltaY = mouseY - startingY
                
                    # # Calculate the velocity to be applied based on the drag distance
                    # aimX = deltaX / AIM_TWEAK
                    # aimY = deltaY / AIM_TWEAK

                    # # Limit the velocity to MAX_VEL
                    # magnitude = min(np.sqrt(aimX**2 + aimY**2), MAX_VEL)
                    # direction = np.atan2(aimY, aimX)

                    # # Apply the velocity
                    # selected.velX = -magnitude * np.cos(direction)
                    # selected.velY = -magnitude * np.sin(direction)

                    # calculate drag distance, applying a slight tweak
                    vel = pygame.math.Vector2(-(mouseX-startingX)/AIM_TWEAK, -(mouseY-startingY)/AIM_TWEAK)
                    
                    # limit velocity to MAX_VEL
                    if vel.magnitude_squared() > MAX_VEL**2: # can use vel.clamp_magnitude_ip(), but is experimental
                        vel.scale_to_length(MAX_VEL)
                    
                    selected.v = vel

                    player.hovered = False
                    selected = None

                    if turn == RED:
                        turn = BLUE
                    else:
                        turn = RED
                # if not, unselect the thing
                else:
                    player.hovered = False
                    selected = None

        fragsToRemove = []
        # check for wall collision
        for obj in objects:
            # update twice to handle goal corners!
            obj.handleWallCollision()
            obj.updatePos()
#            obj.handleWallCollision()
#            obj.updatePos()

            if (obj.type == "frag"):
                if (obj.v.magnitude() < 0.001):
                    fragsToRemove.append(obj)
        
        for frag in fragsToRemove:
            objects.remove(frag)


        pairs = [(a, b) for i, a in enumerate(objects) for b in objects[i+1:]]
        for i in range(2):
            for obj1, obj2 in pairs:
                if distance(obj1.x, obj1.y, obj2.x, obj2.y) <= obj1.size+obj2.size:
                    obj1.handleCollision(obj2)
        
        # display
        DISPLAYSURF.fill(GREEN)
        pygame.draw.rect(DISPLAYSURF, WHITE, pygame.Rect(X_GAP, Y_GAP, FIELD_WIDTH, FIELD_HEIGHT), 1) # field lines
        pygame.draw.rect(DISPLAYSURF, BLUE, pygame.Rect(LEFT_GOAL_BACK, GOAL_TOP, GOAL_DEPTH, GOAL_HEIGHT), 1) # left goal
        pygame.draw.rect(DISPLAYSURF, RED, pygame.Rect(X_GAP+FIELD_WIDTH, GOAL_TOP, GOAL_DEPTH, GOAL_HEIGHT), 1) # right goal
        pygame.draw.line(DISPLAYSURF, YELLOW, (X_GAP, GOAL_TOP), (X_GAP, GOAL_BOTTOM), 4) # left goal line
        pygame.draw.line(DISPLAYSURF, YELLOW, (X_GAP+FIELD_WIDTH, GOAL_TOP), (X_GAP+FIELD_WIDTH, GOAL_BOTTOM), 4) # right goal line
        
        # draw objects
        for obj in objects:
            obj.draw(DISPLAYSURF)
        if selected:
            pygame.draw.line(DISPLAYSURF, WHITE, (selected.x, selected.y), (mouseX, mouseY), SELECTED_THICKNESS)
        
        # detect for scoring
        if (ball.x < X_GAP and not scored):
            displayText = displayFont.render("RED SCORE", True, WHITE)
            displayTextRect = displayText.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
            redScore += 1
            scored = True
            scoreTime = pygame.time.get_ticks()
            turn = BLUE
        if (ball.x > X_GAP+FIELD_WIDTH and not scored):
            displayText = displayFont.render("BLUE SCORE", True, WHITE)
            displayTextRect = displayText.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
            blueScore += 1
            scored = True
            turn = RED
            scoreTime = pygame.time.get_ticks()
        
        if scored and scoreTime > 5000: # keep SCORED text on at least 5 seconds after score
            DISPLAYSURF.blit(displayText, displayTextRect)


        DISPLAYSURF.blit(scoreFont.render("Blue score: " + str(blueScore), True, BLUE), (0,0))
        redScoreText = scoreFont.render("Red score: " + str(redScore), True, RED)
        redScoreRect = redScoreText.get_rect(topright = (SCREEN_WIDTH, 0))
        DISPLAYSURF.blit(redScoreText, redScoreRect)

        # update window
        pygame.display.update()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
    