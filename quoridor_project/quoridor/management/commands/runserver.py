from io import StringIO
from django.core.management.commands.runserver import Command as RunserverCommand
from quoridor.models import Game
from quoridor.management.commands.start_game import Command as StartGameCommand

class Command(RunserverCommand):
    def handle(self, *args, **options):
        print("Custom runserver loaded!")
        if not Game.objects.exists():
            self.stdout.write("Creating initial game...")
            start_game = StartGameCommand()
            start_game.stdout = StringIO()
            start_game.handle()
            self.stdout.write("Initial game created successfully!")
        
        super().handle(*args, **options)