import random
import os
import string
import datetime
import time
import json

#constants

#sympols used to draw board
SYMBOLS = {
    'water': '~',
    'ship': 'O',
    'hit': 'X',
    'miss': '.',
    'sunk': '#'
}

#number of ships
SHIPS_NUM ={
    'battleship' : 1,
    'cruiser' : 2,
    'destroyer' : 3,
    'submarine' : 4
}

#lengths of each ship
SHIPS_LEN ={
    'battleship' : 4,
    'cruiser' : 3,
    'destroyer' : 2,
    'submarine' : 1
}

#size of the game board
BOARD_SIZE = 10


ORIENTATIONS = ['H' , 'V']

SAVE_PATH = "saves"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

#Class that represents ship. Holds info about a ship: coordinates, name(type of this) and length.
#Also contains set, to track all coordinates where ship was hitted.
class Ship:
    #Constructor.
    def __init__(self, name, length, coords, orientation):
        self.name = name
        self.length = length
        self.coords = coords
        self.hits  = set()
        self.orientation = orientation

    #Function to check if the ship is sunk by checking if all parts of ship was hitted.
    def is_sunk(self):
        return len(self.hits) >= self.length

    #Save hit coordinates
    def hit(self, coord):
        if coord in self.coords:
            self.hits.add(coord)
            return True
        return False


#Class that represents board.
class Board:
    #construstor for board
    def __init__(self):
        #empty grid filled with water
        self.grid = [
                    [SYMBOLS['water'] for _ in range(BOARD_SIZE)]
                    for _ in range(BOARD_SIZE)
                    ]
        #list to collect ships
        self.ships = []

    #Function to place ship on the board
    def place_ship(self, ship):
        for (x, y) in ship.coords:

            #Check if ship's cooordinates are right
            if not (0<=x<BOARD_SIZE and 0<=y<BOARD_SIZE):
                raise Exception("Wrong placement")

            #checking if there a no collides with other ships
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    x1, y1 = x + dx, y+dy
                    if 0<=x1<BOARD_SIZE and 0<=y1<BOARD_SIZE:
                        if (self.grid[x1][y1] == SYMBOLS['ship']):
                            raise Exception("ships collide")

        #place
        for (x,y) in ship.coords:
            self.grid[x][y] = SYMBOLS['ship']
        self.ships.append(ship)

    #function to check if all ships on the board is sunk
    def all_sunk(self):
        return all(ship.is_sunk() for ship in self.ships)

    #Function that return string representation of the board
    def get_board(self, reveal=False):
        header = '  ' + ' '.join(string.ascii_uppercase[:BOARD_SIZE])
        rows = [header]

        #using enumerate to go through each element and
        #also tracking index
        for i, row in enumerate(self.grid):
            b_row = []
            for cell in row:
                if cell == SYMBOLS['ship'] and not reveal:
                    b_row.append(SYMBOLS['water'])
                else:
                    b_row.append(cell)
            rows.append(f"{i+1:2} " + ' '.join(b_row))

        return '\n'.join(rows)

    #function to process shot on the board
    def shot(self, coords):
        x, y = coords

        current = self.grid[x][y]

        #check if hit is not at the already hitted cells
        if current in (SYMBOLS['hit'], SYMBOLS['miss'], SYMBOLS['sunk']):
            return "Try again"

        #proccess hit
        for ship in self.ships:
            if coords in ship.coords:
                ship.hit(coords)
                self.grid[x][y] = SYMBOLS['hit']
                if ship.is_sunk():
                    for xy in ship.coords:
                        self.grid[xy[0]][xy[1]] = SYMBOLS['sunk']
                    self.mark_missed(ship)
                    return f"Sunk {ship.name}"
                return "Hit"

        self.grid[x][y] = SYMBOLS['miss']
        return "Miss"

    def mark_missed(self, ship):
        for x,y in ship.coords:
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    new_x, new_y = x+dx, y+dy
                    if 0<=new_x<BOARD_SIZE and 0<= new_y < BOARD_SIZE:
                        if self.grid[new_x][new_y] == SYMBOLS['water']:
                            self.grid[new_x][new_y] = SYMBOLS['miss']


#class that represents Player and saves it's name, board and opponents board
class Player:
    def __init__(self, name):
        #User's name
        self.name = name
        #user's board
        self.board = Board()
        #empty board to represent opponent's board
        self.opponent_board = Board()

    #I don't know if there are abstract methods, so i did this
    def place_ships(self):
        raise NotImplementedError()

    def make_amove(self):
        raise NotImplementedError()


    def display_board(self):
        print(self.board.get_board(reveal=False))




class HumanPlayer(Player):

    #overriden method for player to place ships
    def place_ships(self):
        print(f"Hello, {self.name}! Now You need to place you ships!")

        for ship_name, count in SHIPS_NUM.items():
            for i in range (count):

                length = SHIPS_LEN[ship_name]

                while True:
                    try:
                        self.display_board()

                        coords, orientation = self.get_ship_placement(ship_name, length)
                        print(coords)

                        ship = Ship(ship_name, length, coords, orientation)
                        self.board.place_ship(ship)

                        clear_screen()
                        break

                    except Exception as e:
                        clear_screen()
                        print(e)

    #Method to get coordinates of the ship  placement
    def get_ship_placement(self, ship_name, length):
        inp = input(f"Enter start and orientation (H or V) for {ship_name} (length {length}), e.g. A5 H: ")
        start, orientation = self.parse_coords(inp, (length==1))
        coords = self.generate_start(start, orientation, length)
        return coords, orientation

    #Method to parse user's input ot get coords
    def parse_coords(self, input_val, is_battleship):
        tokens = input_val.split()

        if len(tokens) !=2 and not is_battleship:
            raise Exception("Wrong input")

        if tokens[0][0].upper() not in string.ascii_uppercase[:BOARD_SIZE]:
            raise Exception("Column letter out of bounds")

        col = string.ascii_uppercase.index(tokens[0][0].upper())
        row = int(tokens[0][1:]) - 1
        ori = tokens[1].upper() if not is_battleship else 'H'

        if not (0 <= row < BOARD_SIZE):
            raise Exception("Row out of bounds")

        return(row, col), ori

    #function to calculate start coordinates
    def generate_start(self, start, ori, length):
        if ori not in ORIENTATIONS:
           raise Exception("Wrong orientation!")
        row, col = start

        coords = []
        for i in range(length):

            x = row + (-i if (row+length>BOARD_SIZE and ori == 'V') else i if ori == 'V' else 0)
            y = col + (-i if (col+length>BOARD_SIZE and ori =='H') else i if ori == 'H' else 0)

            if not (0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE):
                raise Exception("Ship out of bounds.")
            coords.append((x, y))

        return coords


    #overriden method for user(human) to see own ships
    def display_board(self):
        print(self.board.get_board(reveal=True))


    #overriden method to make a move
    def make_amove(self):
        while True:
            try:
                inp = input("Enter coordinates to fire (ex. A1) : ")

                #user can provide instructions to save game
                if inp == "save":
                    return "save"


                col = string.ascii_uppercase.index(inp[0].upper())
                row = int(inp[1:])-1
                if not (0<=row<BOARD_SIZE and 0<=col<BOARD_SIZE): raise ValueError
                return (row, col)
            except:
                print("wrong coordinates")



class ComputerPlayer(Player):

    #override constructor, to create a list with all possible coordinates
    def __init__(self, name="Computer"):
        #call super to set name autimatically
        super().__init__(name)
        self.possible_moves = [
            (x, y) for x in range(BOARD_SIZE)
                    for y in range(BOARD_SIZE)
        ]

        random.shuffle(self.possible_moves)

    #override placement and make it randm
    def place_ships(self):
        for ship_name, count in SHIPS_NUM.items():
            for _ in range(count):
                length = SHIPS_LEN[ship_name]
                while True:
                    orientation = random.choice(ORIENTATIONS)
                    x, y = random.randint(0, BOARD_SIZE-1), random.randint(0, BOARD_SIZE-1)
                    coords = [(x + (j if orientation == 'V' else 0),
                              y + (j if orientation == 'H' else 0))
                              for j in range(length)]
                    try:
                        ship = Ship(ship_name, length, coords, orientation)
                        self.board.place_ship(ship)
                        break
                    except Exception:
                        continue

    #override method to make a move to choosing a random move from the list with possible moves
    def make_amove(self):
        move = random.choice(self.possible_moves)
        self.possible_moves.remove(move)
        return move


class GameHistory:

    #consttructor create all class fields that'll be saved
    def __init__(self, username, filename=None):
        self.moves = []
        self.start_time = datetime.datetime.now()
        self.end_time = None
        self.result = None
        self.winner = None
        self.filename = filename or f"game_{username}_{int(time.time())}.json"

    def add_move(self, name, coord, res):
        self.moves.append({
            'player': name,
            'coord' : coord,
            'res' : res,
            'time' : datetime.datetime.now().isoformat()
        })


    #method to save game to .json file
    def save(self, player, ai, winner=None, final=False):
        if final:
            self.end_time = datetime.datetime.now().isoformat()
            self.winner = winner

        #inner function to serialize players(stuck it in to the dictionary)
        def ser_player(p, is_ai=False):
            return {
                "name" : p.name,
                "is_ai" : is_ai,
                "ships": [
                    {
                        "name": ship.name,
                        "length":ship.length,
                        "coords": ship.coords,
                        "hits" : list(ship.hits),
                        "orientation" : ship.orientation

                    }for ship in p.board.ships
                ],
                "board_grid" : p.board.grid
            }

        game_data = {
            "start_time": self.start_time.isoformat(),
            "end_time" : self.end_time if self.end_time is None else self.end_time.isoformat(),
            "moves" : self.moves,
            "winner" : self.winner,
            "players":  [
                ser_player(player),
                ser_player(ai, is_ai=True)
            ]

        }

        if not os.path.exists(SAVE_PATH):
            os.makedirs(SAVE_PATH)

        path = os.path.join(SAVE_PATH, self.filename)

        with open(path, "w") as file:
            json.dump(game_data, file, indent=4)


    @staticmethod
    def list_games():
        #if there are no saved games return epty list
        if not os.path.exists(SAVE_PATH):
            return []
        #otherwise, return list with names of all saved games files
        return [f for f in os.listdir(SAVE_PATH) if f.endswith('.json')]

    @staticmethod
    def load_game(filename):
        path = os.path.join(SAVE_PATH, filename)
        with open(path, "r") as file:
            return json.load(file)

#class that represents game
class BattleshipGame:

    def __init__(self, name):
        self.player = HumanPlayer(name)
        self.ai = ComputerPlayer()
        #choose who start game randomly
        self.current = random.choice([self.player, self.ai])
        self.history = GameHistory(name)

    def setup(self):
        self.ai.place_ships()
        self.player.place_ships()

    def draw_game(self):
        print(f"{self.player.name}'s board: ")
        print(self.player.board.get_board(reveal=True))
        print("Opponent's board: ")
        print(self.ai.board.get_board())

    #switch current player
    def switch_player(self):
        self.current = self.player if self.current == self.ai else self.ai

    #play function
    def play(self, is_loaded=False):
        if not is_loaded:
            self.setup()

        #Game loop
        while True:
            self.draw_game()
            coord = self.current.make_amove()

            if coord == "save":
                self.history.save(self.player, self.ai, final=False)
                clear_screen()
                print("Game Saved!")
                continue

            if coord == "menu" or coord == "exit":
                break


            res = (
                self.ai.board.shot(coord)
                if self.current == self.player
                else self.player.board.shot(coord)
            )




            print(f"{self.current.name} fires at {coord}: {res}")

            time.sleep(3)

            clear_screen()
            #check
            if res == "Try again":
                print("You've already fired there! Try a different spot.")
                continue


            self.history.add_move(self.current.name, coord, res)

            if(self.ai.board.all_sunk() or self.player.board.all_sunk()):
                winner = self.current.name
                print(f"Game Over! {winner} wins!")
                self.process_save()
                break
            if 'Hit' not in res:
                self.switch_player()



    def process_save(self, winner):
        while True:
            inp = input("Do u want to save game? Y/n").lower()

            if(inp == "y" ):
                self.history.save(self.player, self.ai, winner=winner, final=True)
                break
            elif(inp == "n"):
                break
            else:
                print("Wrong input!")


    #method to load game. Returns recreated game
    @staticmethod
    def load_game(filepath):

        game_data = GameHistory.load_game(filepath)

        u_name = game_data["players"][0]["name"]
        game = BattleshipGame(u_name)

        #setting up game's history
        game.history = GameHistory(u_name, filename=filepath)
        game.history.moves = game_data["moves"]
        game.history.start_time = datetime.datetime.fromisoformat(game_data["start_time"])
        game.history.end_time = (datetime.datetime.fromisoformat(game_data["end_time"])
                                 if game_data["end_time"] else None)
        game.history.winner = game_data["winner"]


        #recreate player's movements
        for player in game_data["players"]:
            p = game.player if not player["is_ai"] else game.ai
            p.name = player["name"]
            p.board = Board()

            for ship in player["ships"]:
                coords = [tuple(coord) for coord in ship["coords"]]
                hits = set(tuple(hit) for hit in ship["hits"])

                g_ship = Ship(ship["name"], ship["length"], coords, ship["orientation"])
                g_ship.hits = hits
                p.board.place_ship(g_ship)


            p.board.grid = player["board_grid"]

        #check whose turn now
        if game_data["moves"]:
            last_player_name = game_data["moves"][-1]["player"]

            game.current = game.player if last_player_name == game.ai.name else game.ai
        else:
            game.current = random.choice(game.ai, game.player)

        return game





'''
Part with main menu implementation

'''

def print_options():
    clear_screen()
    print("1.New game")
    print("2.Load game")
    print("3.Stats")
    print("4.Manual")
    print("5.Exit")

def print_manual():
    print("1.To place a ship you need to provide coordinates and orienatation. (e.g. a1 h)\n" \
    "For an 1x1 ships orientation is not neccessary. Ships fitted automaticly\n" \
    "2.To hit you just provide coordinates in format column+row (e.g. a1, b10, etc.).\n" \
    "3.To SAVE game instead of your move write save.")


def print_saved(files):
    clear_screen()
    i = 1
    for file in files:
        print(f"{i}. {file}")
        i+=1


def load():
    files = GameHistory.list_games()

    if not files:
        print("No saved games.")
        return

    print_saved(files)

    inp = input("Choose number of the game you want to load \nor write \'exit\' to exit: ")

    if inp == 'exit':
        return

    game = BattleshipGame.load_game(files[int(inp)-1])
    game.play(is_loaded=True)
    pass

def start_game():
    u_name = input("Enter your name: ")
    game = BattleshipGame(u_name)
    game.play()


def main_menu():
    while True:
        print_options()
        option = input("Select an option: ")

        if(option == '1'):
            start_game()
        elif (option == '2'):
            load()
        elif(option == '3'):
            pass
        elif(option == '4'):
            print_manual()
        elif (option == '5'):
            break
        else:
            print("Wrong option!")



if __name__ == '__main__':
    main_menu()



