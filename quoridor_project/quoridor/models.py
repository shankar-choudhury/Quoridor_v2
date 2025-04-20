from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

class Game(models.Model):
    """
    Self-contained Quoridor game that auto-initializes
    """
    STATUS_CHOICES = [
        ('WAITING', 'Waiting for players'),
        ('IN_PROGRESS', 'In progress'),
        ('FINISHED', 'Finished'),
    ]
    
    # Auto-generated player IDs
    player1_id = models.CharField(max_length=20, default='player1', editable=False)
    player2_id = models.CharField(max_length=20, default='player2', editable=False)
    current_player_id = models.CharField(max_length=20, null=True)
    
    # Game state
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='WAITING')
    created_at = models.DateTimeField(auto_now_add=True)
    winner_id = models.CharField(max_length=20, null=True)
    
    def __str__(self):
        return f"Game {self.id} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        """Override save to auto-initialize game state"""
        is_new = not self.pk
        super().save(*args, **kwargs)
        
        if is_new:
            self._initialize_game()

    def _initialize_game(self):
        """Create all game components automatically"""
        # Set current player
        self.current_player_id = self.player1_id
        self.save()
        
        # Create player states
        PlayerState.objects.create(
            game=self,
            player_id=self.player1_id,
            pawn_position_x=4,
            pawn_position_y=0,
            goal_side='TOP',
            remaining_fences=10
        )
        
        PlayerState.objects.create(
            game=self,
            player_id=self.player2_id,
            pawn_position_x=4,
            pawn_position_y=8,
            goal_side='BOTTOM',
            remaining_fences=10
        )

class PlayerState(models.Model):
    class Meta:
        unique_together = ('game', 'player_id')
    """Tracks player-specific game state"""
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    player_id = models.CharField(max_length=20)
    pawn_position_x = models.IntegerField(default=4, validators=[MinValueValidator(0), MaxValueValidator(8)])
    pawn_position_y = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(8)])
    remaining_fences = models.IntegerField(default=10)
    goal_side = models.CharField(max_length=10, choices=[('TOP', 'Top'), ('BOTTOM', 'Bottom')])

class Fence(models.Model):
    """Represents placed fences"""
    ORIENTATION_CHOICES = [('H', 'Horizontal'), ('V', 'Vertical')]
    
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    player_id = models.CharField(max_length=20)
    x = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(7)])
    y = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(7)])
    orientation = models.CharField(max_length=1, choices=ORIENTATION_CHOICES)