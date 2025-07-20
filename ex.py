import random
import string
import json
import os
import time
from datetime import datetime

# Constants
BOARD_SIZE = 10
SHIP_SPECS = {
    'Battleship': 4,
    'Cruiser': 3,
    'Destroyer': 2,
    'Submarine': 1
}
SHIP_COUNTS = {
    'Battleship': 1,
    'Cruiser': 2,
    'Destroyer': 3,
    'Submarine': 4
}
SYMBOLS = {
    'water': '~',
    'ship': 'O',
    'hit': 'X',
    'miss': '.',
    'sunk': '#'
}
SAVE_DIR = 'saves'
STATS_FILE = os.path.join(SAVE_DIR, 'stats.json')

# Exceptions
class PlacementError(Exception): pass
class LoadError(Exception): pass

# Ship class
class Ship:
    def __init__(self, name, length, coords):
        self.name = name
        self.length = length
        self.coords = coords  # list of (r,c)
        self.hits = set()

    def is_sunk(self):
        return len(self.hits) >= self.length

    def register_hit(self, coord):
        if coord in self.coords:
            self.hits.add(coord)
            return True
        return False

# Board class
class Board:
    def __init__(self):
        self.grid = [[SYMBOLS['water'] for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.ships = []

    def place_ship(self, ship):
        # validate placement
        for (r, c) in ship.coords:
            if not (0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE):
                raise PlacementError(f"Out of bounds: {(r,c)}")
            if self.grid[r][c] != SYMBOLS['water']:
                raise PlacementError(f"Collision at {(r,c)}")
        # ensure no-touch rule
        for (r, c) in ship.coords:
            for dr in (-1,0,1):
                for dc in (-1,0,1):
                    rr, cc = r+dr, c+dc
                    if 0 <= rr < BOARD_SIZE and 0 <= cc < BOARD_SIZE:
                        if self.grid[rr][cc] == SYMBOLS['ship']:
                            raise PlacementError(f"Ships too close at {(r,c)} vs {(rr,cc)}")
        # place
        for (r, c) in ship.coords:
            self.grid[r][c] = SYMBOLS['ship']
        self.ships.append(ship)

    def receive_shot(self, coord):
        r, c = coord
        current = self.grid[r][c]
        if current in (SYMBOLS['hit'], SYMBOLS['miss'], SYMBOLS['sunk']):
            return 'Repeat'
        # check hit
        for ship in self.ships:
            if coord in ship.coords:
                ship.register_hit(coord)
                self.grid[r][c] = SYMBOLS['hit']
                if ship.is_sunk():
                    for rc in ship.coords:
                        self.grid[rc[0]][rc[1]] = SYMBOLS['sunk']
                    return f'Sunk {ship.name}'
                return 'Hit'
        self.grid[r][c] = SYMBOLS['miss']
        return 'Miss'

    def all_sunk(self):
        return all(ship.is_sunk() for ship in self.ships)

    def display(self, reveal=False):
        header = '  ' + ' '.join(string.ascii_uppercase[:BOARD_SIZE])
        rows = [header]
        for i, row in enumerate(self.grid):
            disp_row = []
            for cell in row:
                if cell == SYMBOLS['ship'] and not reveal:
                    disp_row.append(SYMBOLS['water'])
                else:
                    disp_row.append(cell)
            rows.append(f"{i+1:2} " + ' '.join(disp_row))
        return '\n'.join(rows)

# Player classes
class Player:
    def __init__(self, name):
        self.name = name
        self.board = Board()
        self.opponent_board = Board()

    def place_ships(self):
        raise NotImplementedError

    def make_move(self):
        raise NotImplementedError

class HumanPlayer(Player):
    def place_ships(self):
        print(f"{self.name}, place your ships.")
        for ship_name, count in SHIP_COUNTS.items():
            for i in range(count):
                length = SHIP_SPECS[ship_name]
                while True:
                    try:
                        inp = input(f"Enter start and orientation (H/V) for {ship_name} (length {length}), e.g. A5 H: ")
                        parts = inp.split()
                        if len(parts) != 2:
                            raise ValueError
                        col = string.ascii_uppercase.index(parts[0][0].upper())
                        row = int(parts[0][1:]) -1
                        ori = parts[1].upper()
                        if ori not in ('H','V'):
                            raise ValueError
                        coords = []
                        for j in range(length):
                            r = row + (j if ori=='V' else 0)
                            c = col + (j if ori=='H' else 0)
                            coords.append((r,c))
                        ship = Ship(ship_name, length, coords)
                        self.board.place_ship(ship)
                        print(self.board.display(reveal=True))
                        break
                    except Exception as e:
                        print(f"Invalid placement: {e}")

    def make_move(self):
        while True:
            try:
                inp = input("Enter coordinate to fire (e.g. B7): ")
                col = string.ascii_uppercase.index(inp[0].upper())
                row = int(inp[1:]) -1
                if not (0<=row<BOARD_SIZE and 0<=col<BOARD_SIZE): raise ValueError
                return (row, col)
            except:
                print("Invalid coordinate.")

class ComputerPlayer(Player):
    def __init__(self, name="Computer"):
        super().__init__(name)
        self.possible_moves = [(r,c) for r in range(BOARD_SIZE) 
        for c in range(BOARD_SIZE)]
        random.shuffle(self.possible_moves)

    def place_ships(self):
        for ship_name, count in SHIP_COUNTS.items():
            for _ in range(count):
                length = SHIP_SPECS[ship_name]
                while True:
                    ori = random.choice(['H','V'])
                    row = random.randint(0, BOARD_SIZE-1)
                    col = random.randint(0, BOARD_SIZE-1)
                    coords = [(row + (j if ori=='V' else 0),
                                col + (j if ori=='H' else 0)) for j in range(length)]
                    try:
                        ship = Ship(ship_name, length, coords)
                        self.board.place_ship(ship)
                        break
                    except PlacementError:
                        continue

    def make_move(self):
        return self.possible_moves.pop()

# Game history
class GameHistory:
    def __init__(self, filename=None):
        self.moves = []
        self.start_time = datetime.datetime.now()
        self.end_time = None
        self.result = None
        self.filename = filename or f"game_{int(time.time())}.json"
        if not os.path.exists(SAVE_DIR):
            os.makedirs(SAVE_DIR)

    def record(self, player, coord, outcome):
        self.moves.append({'player': player, 'coord': coord, 'outcome': outcome})

    def finish(self, result):
        self.end_time = datetime.now()
        self.result = result
        data = {
            'start': self.start_time.isoformat(),
            'end': self.end_time.isoformat(),
            'result': self.result,
            'moves': self.moves
        }
        path = os.path.join(SAVE_DIR, self.filename)
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        # update stats
        stats = {'games': []}
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE) as f:
                stats = json.load(f)
        stats['games'].append(data)
        with open(STATS_FILE, 'w') as f:
            json.dump(stats, f, indent=2)

    @staticmethod
    def list_games():
        if not os.path.exists(SAVE_DIR): return []
        return [f for f in os.listdir(SAVE_DIR) if f.endswith('.json')]

    @staticmethod
    def load(filename):
        path = os.path.join(SAVE_DIR, filename)
        if not os.path.exists(path):
            raise LoadError("Save file not found")
        with open(path) as f:
            data = json.load(f)
        return data

# Main game loop
class BattleshipGame:
    def __init__(self, name):
        self.human = HumanPlayer(name)
        self.comp = ComputerPlayer()
        self.history = GameHistory()
        self.current = self.human

    def setup(self):
        # place ships
        self.human.place_ships()
        self.comp.place_ships()
        print("All ships placed. Let the battle begin!")

    def switch(self):
        self.current = self.comp if self.current == self.human else self.human

    def play(self):
        self.setup()
        while True:
            print(f"{self.human.name} Board:")
            print(self.human.board.display(reveal=True))
            print("Opponent Board:")
            print(self.human.opponent_board.display())

            coord = self.current.make_move()
            outcome = (self.comp.board if self.current==self.human else self.human.board).receive_shot(coord)
            self.history.record(self.current.name, coord, outcome)
            print(f"{self.current.name} fires at {coord}: {outcome}")

            # update opponent_board view
            sym = SYMBOLS['hit'] if 'Hit' in outcome or 'Sunk' in outcome else SYMBOLS['miss']
            self.current.opponent_board.grid[coord[0]][coord[1]] = sym
            if (self.comp.board.all_sunk() or self.human.board.all_sunk()):
                winner = self.current.name
                print(f"Game Over! {winner} wins!")
                self.history.finish(winner)
                break
            if 'Hit' not in outcome:
                self.switch()

# Menu
def main_menu():
    while True:
        print("1. New Game")
        print("2. Load Game")
        print("3. View Statistics")
        print("4. Quit")
        choice = input("Select an option: ")
        if choice == '1':
            game = BattleshipGame()
            game.play()
        elif choice == '2':
            files = GameHistory.list_games()
            if not files:
                print("No saved games.")
                continue
            for i, fname in enumerate(files):
                print(f"{i+1}. {fname}")
            sel = int(input("Select file: "))-1
            try:
                data = GameHistory.load(files[sel])
                print(json.dumps(data, indent=2))
            except LoadError as e:
                print(e)
        elif choice == '3':
            if os.path.exists(STATS_FILE):
                with open(STATS_FILE) as f:
                    stats = json.load(f)
                total = len(stats['games'])
                hits = sum(sum(1 for m in g['moves'] if m['outcome'] in ('Hit', 'Sunk') ) for g in stats['games'])
                shots = sum(len(g['moves']) for g in stats['games'])
                print(f"Games played: {total}")
                print(f"Overall hit rate: {hits/shots*100:.1f}%")
            else:
                print("No statistics available.")
        elif choice == '4':
            print("Goodbye!")
            break
        else:
            print("Invalid option.")

if __name__ == '__main__':
    main_menu()
