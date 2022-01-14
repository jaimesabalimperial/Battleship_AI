import random

from battleship.board import Board
from battleship.convert import CellConverter

class Player:
    """Class representing the player."""
    
    count = 0  # for keeping track of number of players
    
    def __init__(self, board=None, name=None):
        """Initialise a new player with its board.

        Args:
            board (Board): The player's board. If not provided, then a board
                will be generated automatically
            name (str): Player's name
        """
        if board is None:
            self.board = Board()
        else:
            self.board = board
        
        Player.count += 1
        if name is None:
            self.name = f"Player {self.count}"
        else:
            self.name = name
    
    def __str__(self):
        """."""
        return self.name
    
    def select_target(self):
        """Select target coordinates to attack.
        
        Abstract method that should be implemented by any subclasses of Player.
        
        Returns:
            tuple[int, int] : (x, y) cell coordinates at which to launch the 
                next attack
        """
        raise NotImplementedError
    
    def receive_result(self, is_ship_hit, has_ship_sunk):
        """Receive results of latest attack.
        
        Player receives notification on the outcome of the latest attack by the 
        player, on whether the opponent's ship is hit, and whether it has been 
        sunk. 
        
        This method does not do anything by default, but can be overridden by a subclass to do something useful, for example to record a successful or failed attack.
        
        Returns:
            None
        """
        return None
    
    def has_lost(self):
        """Check whether player has lost the game.
        
        Returns:
            bool: True if and only if all the ships of the player have sunk.
        """
        return self.board.have_all_ships_sunk()


class ManualPlayer(Player):
    """A player playing manually via the terminal."""
    
    def __init__(self, board, name=None):
        """Initialise the player with a board and other attributes.
        
        Args:
            board (Board): The player's board. If not provided, then a board
                will be generated automatically
            name (str): Player's name
        """
        super().__init__(board=board, name=name)
        self.converter = CellConverter((board.width, board.height))
        
    def select_target(self):
        """Read coordinates from user prompt.
               
        Returns:
            tuple[int, int] : (x, y) cell coordinates at which to launch the 
                next attack
        """
        print(f"It is now {self}'s turn.")

        while True:
            try:
                coord_str = input('coordinates target = ')
                x, y = self.converter.from_str(coord_str)
                return x, y
            except ValueError as error:
                print(error)


class RandomPlayer(Player):
    """A Player that plays at random positions.

    However, it does not play at the positions:
    - that it has previously attacked
    """
    
    def __init__(self, name=None):
        """Initialise the player with an automatic board and other attributes.
        
        Args:
            name (str): Player's name
        """
        # Initialise with a board with ships automatically arranged.
        super().__init__(board=Board(), name=name)
        self.tracker = set()

    def select_target(self):
        """Generate a random cell that has previously not been attacked.
        
        Also adds cell to the player's tracker.
        
        Returns:
            tuple[int, int] : (x, y) cell coordinates at which to launch the 
                next attack
        """
        target_cell = self.generate_random_target()
        self.tracker.add(target_cell)
        return target_cell

    def generate_random_target(self):
        """Generate a random cell that has previously not been attacked.
               
        Returns:
            tuple[int, int] : (x, y) cell coordinates at which to launch the 
            next attack.
        """
        has_been_attacked = True
        random_cell = None
        
        while has_been_attacked:
            random_cell = self.get_random_coordinates()
            has_been_attacked = random_cell in self.tracker

        return random_cell

    def get_random_coordinates(self):
        """Generate random coordinates.
               
        Returns:
            tuple[int, int] : (x, y) cell coordinates at which to launch the 
            next attack.
        """
        x = random.randint(1, self.board.width)
        y = random.randint(1, self.board.height)
        return (x, y)


class AutomaticPlayer(Player):
    """Player playing automatically using a strategy."""
    
    def __init__(self, name=None):
        """Initialise the player with an automatic board and other attributes.
        
        Args:
            name (str): Player's name
        """
        # Initialise with a board with ships automatically arranged.
        super().__init__(board=Board(), name=name)
        
        self.tracker = {}
        self.prev_move = None
        self.grid_locs = [(i, j) for i in range(1, self.board.width+1) for j in range(1, self.board.height+1)]
        self.available_locs = self.grid_locs
        self.curr_ship_locs = []
        self.attacking_steps = [(1,0), (0,1),
                                (-1,0), (0,-1)]

        self.curr_step = None
        self.attempted_steps = []

    @property
    def all_moves(self):
        """Function called when self.all_moves attribute is called --> returns list of all moves made."""
        return list(self.tracker.keys())

    def is_near_cell(self, cell, min_edge, max_edge):
        """ Check whether the ship is near an (x,y) cell coordinate.

        In the example below:
        - There is a ship of length 3 represented by the letter S.
        - The positions 1, 2, 3 and 4 are near the ship
        - The positions 5 and 6 are NOT near the ship

        --------------------------
        |   |   |   |   | 3 |   |
        -------------------------
        |   | S | S | S | 4 | 5 |
        -------------------------
        | 1 |   | 2 |   |   |   |
        -------------------------
        |   |   | 6 |   |   |   |
        -------------------------

        Args:
            cell (tuple[int, int]): tuple of 2 positive integers representing
                the (x, y) cell coordinates to compare

        Returns:
            bool : returns True if and only if the (x, y) coordinate is at most
                one cell from any part of the ship OR is at the corner of the ship. Returns False otherwise.
        """
        return (min_edge[0]-1 <= cell[0] <= max_edge[0]+1 
                and min_edge[1]-1 <= cell[1] <= max_edge[1]+1)

    def disregard_nearby_cells(self):
        """Removes cells that are nearby to sunken ship (according to definition in battleship.ship) 
           from self.available_locations."""
        #get edges of ship (maximum and minimum values of position wrt ship orientation)
        if len(self.curr_ship_locs) == 1:
            #if ship has length 1, set edges to be the same
            min_edge = self.curr_ship_locs[0]
            max_edge = self.curr_ship_locs[0] 
        else:
            if self.ship_is_vertical(): 
                min_edge = min(self.curr_ship_locs, key=lambda loc: loc[1])
                max_edge = max(self.curr_ship_locs, key=lambda loc: loc[1])
            else: 
                min_edge = min(self.curr_ship_locs, key=lambda loc: loc[0])
                max_edge = max(self.curr_ship_locs, key=lambda loc: loc[0])
        
        for grid_cell in self.available_locs:
            if self.is_near_cell(grid_cell, min_edge, max_edge) and grid_cell in self.available_locs:
                self.available_locs.remove(grid_cell)


    def ship_is_vertical(self):
        """ Check whether the ship is vertical.
        
        Returns:
            bool : True if the ship is vertical. False otherwise.
        """
        return int(abs(self.curr_step[1]))

    def step_is_legal(self, step, loc):
        """Check wether taking step from loc results in the consequent position being an available location.
        
        Returns: 
            bool: True if next position is available. False otherwise."""
        return (loc[0] + step[0], loc[1] + step[1]) in self.available_locs

    def receive_result(self, is_ship_hit, has_ship_sunk):
        """Record result of last move on self.tracker."""

        self.tracker[self.prev_move] = (is_ship_hit, has_ship_sunk)

    def select_target(self):
        """ Select target coordinates to attack.
        
        Returns:
            tuple[int, int] : (x, y) cell coordinates at which to launch the 
                next attack
        """
        #first target location should be in the center of the board where
        #there is a highest probability of a ship being placed (i.e having a cell)
        if len(self.all_moves) == 0:
            target_cell = (self.board.width//2 + 1, self.board.height//2 + 1)
            self.prev_move = target_cell
            return target_cell

        #if ship was hit but not sunk
        if self.tracker[self.prev_move] == (True, False):
            self.curr_ship_locs.append(self.prev_move)

            hit_loc = self.prev_move
            #if ship has only been hit once, choose next target from random step from all four directions
            #if this condition isn't met, follow successful step once again
            if len(self.curr_ship_locs) == 1:
                possible_steps = [step for step in self.attacking_steps if self.step_is_legal(step, hit_loc)] #only choose from legal steps
                self.curr_step = random.choice(possible_steps)

            else:
                #edge case --> check if player will run into edge before sinking ship 
                if not self.step_is_legal(step=self.curr_step, loc=self.prev_move):
                    hit_loc = self.curr_ship_locs[0]
                    self.curr_step = tuple([-step for step in self.curr_step])

            target_cell = (hit_loc[0] + self.curr_step[0], hit_loc[1] + self.curr_step[1]) #update target cell

        #if ship was hit and sunk
        elif self.tracker[self.prev_move] == (True, True):
            self.curr_ship_locs.append(self.prev_move) #append last ship location to list

            self.disregard_nearby_cells() #disregard cells surrounding ships for next random guesses
            self.curr_ship_locs = [] #reinitialise target ship locs list
            self.curr_step = None
            self.attempted_steps = []

            target_cell = random.choice(self.available_locs) #choose random target from available locations

        #if miss
        else:
            #account for case where a ship is in the radar (i.e hit on previous to previous move but not sunk)
            if len(self.curr_ship_locs) == 1:
                self.attempted_steps.append(self.curr_step)

                #make step from hit location
                hit_loc = self.curr_ship_locs[0]

                #retrieve steps that haven't been tried yet and choose a random one of them that is legal
                possible_steps = [step for step in self.attacking_steps if step not in self.attempted_steps and self.step_is_legal(step, hit_loc)]
                self.curr_step = random.choice(possible_steps)
                target_cell = (hit_loc[0] + self.curr_step[0], hit_loc[1] + self.curr_step[1])

            #if miss but hit more than once, just have to reverse step and take it from first hit location
            elif len(self.curr_ship_locs) > 1: 
                first_hit_loc = self.curr_ship_locs[0]
                self.curr_step = tuple([-step for step in self.curr_step])
                target_cell = (first_hit_loc[0] + self.curr_step[0], first_hit_loc[1] + self.curr_step[1])

            #if no ship is in radar and previous hit was a miss
            else: 
                self.available_locs.remove(self.prev_move)  #remove miss loc from available locations 
                target_cell = random.choice(self.available_locs)  #choose a random location out of available locations

        self.prev_move = target_cell
        return target_cell

