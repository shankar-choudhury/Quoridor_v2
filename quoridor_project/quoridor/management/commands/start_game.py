from django.core.management.base import BaseCommand
from quoridor.models import Game
import uuid

class Command(BaseCommand):
    help = 'Starts a new Quoridor game'

    def handle(self, *args, **options):
        # Create game with auto-generated IDs
        game = Game.objects.create(
            player1_id='player1',
            player2_id='player2',  # Generate second player ID
            status='IN_PROGRESS'     # Start immediately
        )
        
        self.stdout.write(f"""
        Game {game.id} ready!
        Player 1 ID: {game.player1_id}
        Player 2 ID: {game.player2_id}
        Current player: {game.current_player_id}
        """)