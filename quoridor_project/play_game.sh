#!/bin/bash

# Reset the database and migrations
rm -f db.sqlite3
python manage.py makemigrations
python manage.py migrate

# Start Django shell with pre-loaded commands
python manage.py shell <<EOF
from quoridor.models import Game
from quoridor.game import QuoridorEngine
game = Game.objects.create()
engine = QuoridorEngine(game.id)
print("\n\033[1;32mQuoridor game ready!\033[0m")
print(f"Game ID: {game.id}")
print(f"Player 1: {game.player1_id}")
print(f"Player 2: {game.player2_id}")
print("Type 'engine.get_state()' to view game state\n")

engine.move_pawn('player1', 4, 1)
engine.place_fence('player2', 4, 1, 'H')

engine.move_pawn('player1', 4, 2)
engine.move_pawn('player1', 3, 1)

engine.move_pawn('player2', 4, 7)
engine.move_pawn('player1', 3, 2)
engine.move_pawn('player2', 4, 6)
engine.move_pawn('player1', 4, 2)
engine.move_pawn('player2', 4, 5)
engine.move_pawn('player1', 4, 3)
engine.move_pawn('player2', 4, 4)
engine.move_pawn('player1', 4, 5)

EOF
