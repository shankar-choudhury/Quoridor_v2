from .models import Game, PlayerState, Fence
from collections import deque

class QuoridorEngine:
    BOARD_SIZE = 9
    
    def __init__(self, game_id):
        self.game = Game.objects.get(id=game_id)
        self.player_states = {
            str(self.game.player1_id): PlayerState.objects.get(game=self.game, player_id=self.game.player1_id),
            str(self.game.player2_id): PlayerState.objects.get(game=self.game, player_id=self.game.player2_id)
        }
        self.fences = list(Fence.objects.filter(game=self.game))  # Load all fences
        self.BOARD_SIZE = 9

    def get_state(self):
        """Return complete game state"""
        return {
            'players': {
                str(self.game.player1_id): self._player_state(self.game.player1_id),
                str(self.game.player2_id): self._player_state(self.game.player2_id),
            },
            'fences': [{
                'x': f.x,
                'y': f.y,
                'orientation': f.orientation,
                'player_id': str(f.player_id)
            } for f in self.fences],
            'current_player': str(self.game.current_player_id),
            'status': self.game.status
        }

    def _player_state(self, player_id):
        state = self.player_states[str(player_id)]
        return {
            'position': [state.pawn_position_x, state.pawn_position_y],
            'fences_remaining': state.remaining_fences,
            'goal': state.goal_side
        }

    def is_valid_move(self, player_id, new_x, new_y):
        """Check if a pawn move is valid, including jumps"""
        current = self.player_states[str(player_id)]
        opponent = self._get_opponent_state(player_id)
        
        # Basic validation
        if not (0 <= new_x < self.BOARD_SIZE and 0 <= new_y < self.BOARD_SIZE):
            return False
        
        # Check if moving to opponent's position (for jump moves)
        if (new_x, new_y) == (opponent.pawn_position_x, opponent.pawn_position_y):
            return self._is_valid_jump(player_id, new_x, new_y)
            
        # Normal orthogonal move
        dx = abs(new_x - current.pawn_position_x)
        dy = abs(new_y - current.pawn_position_y)
        
        if (dx == 1 and dy == 0) or (dx == 0 and dy == 1):
            return not self._is_blocked(
                current.pawn_position_x,
                current.pawn_position_y,
                new_x,
                new_y
            )
        return False
    
    def _is_valid_jump(self, player_id, jump_x, jump_y):
        """Check if jumping over opponent is valid"""
        current = self.player_states[str(player_id)]
        opponent = self._get_opponent_state(player_id)
        
        # Must be directly adjacent first
        if not (abs(current.pawn_position_x - jump_x) <= 1 and 
                abs(current.pawn_position_y - jump_y) <= 1):
            return False
            
        # Calculate landing position (2 squares in same direction)
        landing_x = jump_x + (jump_x - current.pawn_position_x)
        landing_y = jump_y + (jump_y - current.pawn_position_y)
        
        # Check landing position is valid and not blocked
        return (0 <= landing_x < self.BOARD_SIZE and 
                0 <= landing_y < self.BOARD_SIZE and
                not self._is_blocked(jump_x, jump_y, landing_x, landing_y))
    
    def _is_blocked(self, from_x, from_y, to_x, to_y):
        """Check if there's a fence blocking the move"""
        # Horizontal move (left/right)
        if from_y == to_y:
            min_x = min(from_x, to_x)
            for fence in self.fences:
                if fence.orientation == 'V':
                    if (fence.x == min_x and fence.y in [from_y-1, from_y]):
                        return True
        # Vertical move (up/down)
        else:
            min_y = min(from_y, to_y)
            for fence in self.fences:
                if fence.orientation == 'H':
                    if (fence.y == min_y and fence.x in [from_x-1, from_x]):
                        return True
        return False
    
    def _get_opponent_state(self, player_id):
        """Get the opponent's PlayerState"""
        opponent_id = self.game.player2_id if str(player_id) == str(self.game.player1_id) else self.game.player1_id
        return self.player_states[str(opponent_id)]
    
    def move_pawn(self, player_id, new_x, new_y):
        """Execute a pawn move if valid, including jumps"""
        if str(self.game.current_player_id) != str(player_id):
            return False
            
        current = self.player_states[str(player_id)]

        # Prevent moving to current position
        if (new_x, new_y) == (current.pawn_position_x, current.pawn_position_y):
            return False

        opponent = self._get_opponent_state(player_id)
        
        # Handle jump moves
        if (new_x, new_y) == (opponent.pawn_position_x, opponent.pawn_position_y):
            if not self._is_valid_jump(player_id, new_x, new_y):
                return False
                
            # Calculate jump landing position
            landing_x = new_x + (new_x - current.pawn_position_x)
            landing_y = new_y + (new_y - current.pawn_position_y)
            
            current.pawn_position_x = landing_x
            current.pawn_position_y = landing_y
        else:
            # Normal move
            if not self.is_valid_move(player_id, new_x, new_y):
                return False
                
            current.pawn_position_x = new_x
            current.pawn_position_y = new_y
        
        current.save()
        self._check_win_condition(player_id)
        self._switch_turns()
        return True
    
    def _check_win_condition(self, player_id):
        """Check if player has reached their goal"""
        state = self.player_states[str(player_id)]
        if (state.goal_side == 'TOP' and state.pawn_position_y == self.BOARD_SIZE-1) or \
           (state.goal_side == 'BOTTOM' and state.pawn_position_y == 0):
            self.game.winner_id = player_id
            self.game.status = 'FINISHED'
            self.game.save()
            print(f"Game over! {player_id} wins!")
    
    def _switch_turns(self):
        """Alternate turns between players"""
        self.game.current_player_id = (
            self.game.player2_id if str(self.game.current_player_id) == str(self.game.player1_id)
            else self.game.player1_id
        )
        self.game.save()

    def place_fence(self, player_id, x, y, orientation):
        """Place a fence if valid"""
        if str(self.game.current_player_id) != str(player_id):
            return False
            
        player_state = self.player_states[str(player_id)]
        if player_state.remaining_fences <= 0:
            return False
            
        if not (0 <= x < self.BOARD_SIZE-1 and 0 <= y < self.BOARD_SIZE-1):
            return False
            
        for existing in self.fences:
            if existing.orientation == orientation:
                if orientation == 'H':
                    if y == existing.y and (x == existing.x or x == existing.x + 1 or x == existing.x - 1):
                        return False
                else:
                    if x == existing.x and (y == existing.y or y == existing.y + 1 or y == existing.y - 1):
                        return False
            else:
                # Check for crossing fences (H and V intersecting)
                if orientation == 'H' and existing.orientation == 'V':
                    if (x == existing.x - 1 and y == existing.y) or (x == existing.x and y == existing.y):
                        return False
                elif orientation == 'V' and existing.orientation == 'H':
                    if (x == existing.x and y == existing.y - 1) or (x == existing.x and y == existing.y):
                        return False
            
        # Create the fence object but don't save to DB yet
        new_fence = Fence(
            game=self.game,
            player_id=player_id,
            x=x,
            y=y,
            orientation=orientation
        )
        
        self.fences.append(new_fence)
        
        try:
            # Check if both players still have a path to their goals
            if not self._validate_paths_after_fence():
                return False
                
            # If paths are valid, save to database
            new_fence.save()
            
            player_state.remaining_fences -= 1
            player_state.save()
            self._switch_turns()
            return True
        finally:
            # Ensure the fence is removed from the list if validation fails
            if new_fence.pk is None:  # Wasn't saved to DB
                self.fences.remove(new_fence)
    
    def _validate_paths_after_fence(self):
        """Check both players have a path to their goals after fence placement"""
        for player_id, state in self.player_states.items():
            if not self._path_exists_to_goal(state):
                return False
        return True
    
    def _path_exists_to_goal(self, player_state):
        """Check if a path exists from player's position to their goal using BFS"""
        start = (player_state.pawn_position_x, player_state.pawn_position_y)
        visited = set()
        queue = deque([start])
        visited.add(start)
        
        goal_y = self.BOARD_SIZE - 1 if player_state.goal_side == 'TOP' else 0
        
        while queue:
            x, y = queue.popleft()
            
            # Check if reached goal row
            if y == goal_y:
                return True
                
            # Check all 4 possible directions
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                # Check within bounds
                if 0 <= nx < self.BOARD_SIZE and 0 <= ny < self.BOARD_SIZE:
                    # Check if move is not blocked and not visited
                    if not self._is_blocked(x, y, nx, ny) and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        queue.append((nx, ny))
        
        return False
