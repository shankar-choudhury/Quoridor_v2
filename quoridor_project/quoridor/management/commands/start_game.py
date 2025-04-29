from django.core.management.base import BaseCommand
from ...models import Game, Device

class Command(BaseCommand):
    help = 'Starts a new Quoridor game'

    def add_arguments(self, parser):
        parser.add_argument('--player1-device', type=str, default=None, help='Device ID for player 1 (optional)')
        parser.add_argument('--player2-device', type=str, default=None, help='Device ID for player 2 (optional)')

    def handle(self, *args, **options):
        # Handle player1 device (optional)
        player1_device = None
        if options['player1_device']:
            player1_device = Device.objects.get_or_create(
                device_id=options['player1_device'],
                defaults={'name': f'Player 1 Device ({options["player1_device"]})'}
            )[0]
        
        # Handle player2 device (optional)
        player2_device = None
        if options['player2_device']:
            player2_device = Device.objects.get_or_create(
                device_id=options['player2_device'],
                defaults={'name': f'Player 2 Device ({options["player2_device"]})'}
            )[0]

        # Create game
        game = Game.objects.create(
            player1_id='player1',
            player2_id='player2',
            status='IN_PROGRESS',
            player1_device=player1_device,
            player2_device=player2_device
        )
        
        output = [
            f"Game {game.id} ready!",
            f"Player 1 ID: {game.player1_id}",
            f"Player 1 Device: {player1_device.device_id if player1_device else 'None'}",
            f"Player 2 ID: {game.player2_id}",
            f"Player 2 Device: {player2_device.device_id if player2_device else 'None'}",
            f"Current player: {game.current_player_id}"
        ]
        
        self.stdout.write("\n".join(output))