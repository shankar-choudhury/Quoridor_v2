from collections import deque
from typing import Dict, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed

from .models import Game, PlayerState, Fence, Device
from .mqtt_publisher import QuoridorMQTTPublisher

import time
import threading
import traceback


class QuoridorEngine:
    """Core game engine for Quoridor, handling game logic and state management."""
    
    BOARD_SIZE = 9
    DIRECTIONS = [(0, 1), (1, 0), (0, -1), (-1, 0)]  
    MAX_PATHFINDING_STEPS = 500

    def __init__(self, game_id: int):
        """Initialize game engine with existing game state."""
        self.game = Game.objects.get(id=game_id)
        self.player_states = self._load_player_states()
        self.fences = list(Fence.objects.filter(game=self.game))
        self._fence_cache = None
        self._lock = threading.RLock()

    def _load_player_states(self) -> Dict[str, PlayerState]:
        """Load and return player states as a dictionary."""
        return {
            str(self.game.player1_id): PlayerState.objects.get(
                game=self.game, 
                player_id=self.game.player1_id
            ),
            str(self.game.player2_id): PlayerState.objects.get(
                game=self.game,
                player_id=self.game.player2_id
            )
        }
    
    def _get_fence_cache(self):
        """Thread-safe fence cache access"""
        with self._lock:
            if self._fence_cache is None:
                self._fence_cache = {
                    'H': {(f.x, f.y) for f in self.fences if f.orientation == 'H'},
                    'V': {(f.x, f.y) for f in self.fences if f.orientation == 'V'}
                }
            return self._fence_cache

    def get_state(self) -> dict:
        """Return complete game state as a dictionary."""
        with self._lock:
            return {
                'players': {
                    player_id: self._player_state(player_id)
                    for player_id in [self.game.player1_id, self.game.player2_id]
                },
                'fences': [self._serialize_fence(f) for f in self.fences],
                'current_player': str(self.game.current_player_id),
                'status': self.game.status,
                'winner': self.game.winner_id
            }

    def _serialize_fence(self, fence: Fence) -> dict:
        """Serialize fence object to dictionary."""
        return {
            'x': fence.x,
            'y': fence.y,
            'orientation': fence.orientation,
            'player_id': str(fence.player_id)
        }

    def _player_state(self, player_id: str) -> dict:
        """Return serialized player state."""
        state = self.player_states[str(player_id)]
        return {
            'position': [state.pawn_position_x, state.pawn_position_y],
            'fences_remaining': state.remaining_fences,
            'goal': state.goal_side
        }

    def is_valid_move(self, player_id: str, new_x: int, new_y: int) -> bool:
        """Check if a pawn move is valid."""
        current = self.player_states[str(player_id)]
        opponent = self._get_opponent_state(player_id)

        if not self._is_within_bounds(new_x, new_y):
            return False

        if (new_x, new_y) == (opponent.pawn_position_x, opponent.pawn_position_y):
            return self._is_valid_jump(player_id, new_x, new_y)

        return self._is_valid_orthogonal_move(current, new_x, new_y)

    def _is_within_bounds(self, x: int, y: int) -> bool:
        """Check if coordinates are within game board bounds."""
        return 0 <= x < self.BOARD_SIZE and 0 <= y < self.BOARD_SIZE

    def _is_valid_orthogonal_move(self, current: PlayerState, new_x: int, new_y: int) -> bool:
        """Check validity of standard orthogonal moves."""
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

    def _is_valid_jump(self, player_id: str, jump_x: int, jump_y: int) -> bool:
        """Check if jumping over opponent is valid."""
        current = self.player_states[str(player_id)]
        
        if not self._is_adjacent(current.pawn_position_x, current.pawn_position_y, jump_x, jump_y):
            return False
            
        landing_x, landing_y = self._calculate_jump_landing(current, jump_x, jump_y)
        
        return (self._is_within_bounds(landing_x, landing_y) and
                not self._is_blocked(jump_x, jump_y, landing_x, landing_y))

    def _is_adjacent(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        """Check if two positions are adjacent."""
        return abs(x1 - x2) <= 1 and abs(y1 - y2) <= 1

    def _calculate_jump_landing(self, current: PlayerState, jump_x: int, jump_y: int) -> Tuple[int, int]:
        """Calculate landing position after a jump."""
        return (
            jump_x + (jump_x - current.pawn_position_x),
            jump_y + (jump_y - current.pawn_position_y)
        )

    def _is_blocked(self, from_x: int, from_y: int, to_x: int, to_y: int) -> bool:
        """Check if movement between positions is blocked by a fence."""
        fence_cache = self._get_fence_cache()
        
        if from_y == to_y:  # Horizontal move
            min_x = min(from_x, to_x)
            return (
                (min_x, from_y) in fence_cache['V'] or
                (min_x, from_y-1) in fence_cache['V']
            )
        else:  # Vertical move
            min_y = min(from_y, to_y)
            return (
                (from_x, min_y) in fence_cache['H'] or
                (from_x-1, min_y) in fence_cache['H']
            )

    def _get_opponent_state(self, player_id: str) -> PlayerState:
        """Get the opponent's PlayerState."""
        opponent_id = (
            self.game.player2_id if str(player_id) == str(self.game.player1_id)
            else self.game.player1_id
        )
        return self.player_states[str(opponent_id)]
    
    def _get_player_device(self, player_id: str) -> Optional[Device]:
        """Get the device associated with a player."""
        return (
            self.game.player1_device if str(player_id) == str(self.game.player1_id)
            else self.game.player2_device
        )
    
    def move_pawn(self, player_id: str, new_x: int, new_y: int) -> bool:
        with self._lock:
            if not self._is_players_turn(player_id):
                self._notify_invalid_move(player_id)
                return False

            current = self.player_states[str(player_id)]
            if self._is_same_position(current, new_x, new_y):
                self._notify_invalid_move(player_id)
                return False

            if self._attempt_jump_move(player_id, current, new_x, new_y):
                self._handle_successful_move(player_id)
                return True

            if self._attempt_normal_move(player_id, current, new_x, new_y):
                self._handle_successful_move(player_id)
                return True

            self._notify_invalid_move(player_id)
            return False

    def _is_players_turn(self, player_id: str) -> bool:
        """Check if it's the player's turn."""
        return str(self.game.current_player_id) == str(player_id)

    def _is_same_position(self, current: PlayerState, x: int, y: int) -> bool:
        """Check if position matches current position."""
        return (x, y) == (current.pawn_position_x, current.pawn_position_y)

    def _attempt_jump_move(self, player_id: str, current: PlayerState, x: int, y: int) -> bool:
        """Attempt to execute a jump move if valid."""
        opponent = self._get_opponent_state(player_id)
        
        if (x, y) != (opponent.pawn_position_x, opponent.pawn_position_y):
            return False

        if not self._is_valid_jump(player_id, x, y):
            return False

        landing_x, landing_y = self._calculate_jump_landing(current, x, y)
        current.pawn_position_x = landing_x
        current.pawn_position_y = landing_y
        return True

    def _attempt_normal_move(self, player_id: str, current: PlayerState, x: int, y: int) -> bool:
        """Attempt to execute a normal move if valid."""
        if not self.is_valid_move(player_id, x, y):
            return False
        current.pawn_position_x = x
        current.pawn_position_y = y
        return True

    def _notify_invalid_move(self, player_id: str) -> None:
        """Notify player of invalid move."""
        if device := self._get_player_device(player_id):
            QuoridorMQTTPublisher.publish_move_validity(device, False)

    def _handle_successful_move(self, player_id: str) -> None:
        """Handle successful move operations."""
        current = self.player_states[str(player_id)]
        current.save()
        self._check_win_condition(player_id)
        
        if device := self._get_player_device(player_id):
            QuoridorMQTTPublisher.publish_move_validity(device, True)

        time.sleep(0.7)
        self._switch_turns()
    
    def _check_win_condition(self, player_id: str) -> None:
        """Check if player has won the game."""
        state = self.player_states[str(player_id)]
        
        if (state.goal_side == 'TOP' and state.pawn_position_y == self.BOARD_SIZE-1) or \
           (state.goal_side == 'BOTTOM' and state.pawn_position_y == 0):
            self._declare_winner(player_id)

    def _declare_winner(self, player_id: str) -> None:
        """Handle game win conditions."""
        self.game.winner_id = player_id
        self.game.status = 'FINISHED'
        self.game.save()
        self._notify_game_result()

    def _notify_game_result(self) -> None:
        """Notify both players of game result."""
        winner_str = str(self.game.winner_id)
        
        if self.game.player1_device:
            QuoridorMQTTPublisher.publish_game_result(
                self.game.player1_device,
                winner_str == str(self.game.player1_id)
            )
            
        if self.game.player2_device:
            QuoridorMQTTPublisher.publish_game_result(
                self.game.player2_device,
                winner_str == str(self.game.player2_id)
            )

    def _switch_turns(self) -> None:
        """Switch turns between players and notify devices."""
        with self._lock:
            self.game.current_player_id = (
                self.game.player2_id if str(self.game.current_player_id) == str(self.game.player1_id)
                else self.game.player1_id
            )
            self.game.save()

        threading.Thread(
            target=self._notify_turn_change,
            daemon=True
        ).start()

    def _notify_turn_change(self) -> None:
        """Notify players about turn changes."""
        current_id = str(self.game.current_player_id)
        
        if self.game.player1_device:
            QuoridorMQTTPublisher.publish_turn(
                self.game.player1_device,
                current_id == str(self.game.player1_id)
            )
            
        if self.game.player2_device:
            QuoridorMQTTPublisher.publish_turn(
                self.game.player2_device,
                current_id == str(self.game.player2_id)
            )

    def place_fence(self, player_id: str, x: int, y: int, orientation: str) -> bool:
        """Place a fence if valid."""
        if not self._validate_fence_placement(player_id, x, y, orientation):
            self._notify_invalid_move(player_id)
            return False

        new_fence = Fence(
            game=self.game,
            player_id=player_id,
            x=x,
            y=y,
            orientation=orientation
        )
        
        with self._lock:
            self.fences.append(new_fence)
            self._fence_cache = None
                
            if not self._validate_paths_after_fence():
                self.fences.remove(new_fence)
                self._fence_cache = None
                self._notify_invalid_move(player_id)
                return False
                    
            new_fence.save()
            self._update_player_fences(player_id)
            self._handle_successful_move(player_id)
            return True
            
    def _validate_fence_placement(self, player_id: str, x: int, y: int, orientation: str) -> bool:
        """Check fence placement validity."""
        if not self._is_within_fence_bounds(x, y):
            return False
            
        if self._is_fence_overlapping(x, y, orientation):
            return False
            
        player_state = self.player_states[str(player_id)]
        if player_state.remaining_fences <= 0:
            return False
            
        return True

    def _is_within_fence_bounds(self, x: int, y: int) -> bool:
        """Check if fence coordinates are valid."""
        return 0 <= x < self.BOARD_SIZE-1 and 0 <= y < self.BOARD_SIZE-1

    def _is_fence_overlapping(self, x: int, y: int, orientation: str) -> bool:
        """Check for overlapping or invalid fence placements."""
        fence_cache = self._get_fence_cache()
        if orientation == 'H':
            return (x, y) in fence_cache['H'] or (x+1, y) in fence_cache['H']
        else:
            return (x, y) in fence_cache['V'] or (x, y+1) in fence_cache['V']

    def _update_player_fences(self, player_id: str) -> None:
        """Update player's remaining fence count."""
        player_state = self.player_states[str(player_id)]
        player_state.remaining_fences -= 1
        player_state.save()

    def _validate_paths_after_fence(self) -> bool:
        """Thread-safe path validation using state snapshots."""
        with self._lock:
            fence_snapshot = list(self.fences)
            player_states = {k: v for k, v in self.player_states.items()}
        
        try:
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = {
                    executor.submit(self._check_path_with_snapshot, pid, state, fence_snapshot)
                    for pid, state in player_states.items()
                }
                
                for future in as_completed(futures, timeout=2.0):
                    if not future.result():
                        return False
                return True
                
        except TimeoutError:
            return False

    def _check_path_with_snapshot(self, pid, state, fence_snapshot):
        """Thread-safe path checking using snapshot"""
        temp_cache = {
            'H': {(f.x, f.y) for f in fence_snapshot if f.orientation == 'H'},
            'V': {(f.x, f.y) for f in fence_snapshot if f.orientation == 'V'}
        }
        return self._path_exists_with_cache(state, temp_cache)

    def _path_exists_with_cache(self, state, cache):
        """BFS using provided cache"""
        start = (state.pawn_position_x, state.pawn_position_y)
        goal_y = self.BOARD_SIZE - 1 if state.goal_side == 'TOP' else 0
        
        visited = set([start])
        queue = deque([start])
        
        while queue:
            x, y = queue.popleft()
            
            for dx, dy in self.DIRECTIONS:
                nx, ny = x + dx, y + dy
                
                if (0 <= nx < self.BOARD_SIZE and 0 <= ny < self.BOARD_SIZE and
                    not self._is_blocked_with_cache(x, y, nx, ny, cache) and
                    (nx, ny) not in visited):
                    
                    if ny == goal_y:
                        return True
                        
                    visited.add((nx, ny))
                    queue.append((nx, ny))
        
        return False

    def _is_blocked_with_cache(self, from_x, from_y, to_x, to_y, cache):
        """Check blockage using provided cache"""
        if from_y == to_y:  # Horizontal
            min_x = min(from_x, to_x)
            return ((min_x, from_y) in cache['V'] or 
                    (min_x, from_y-1) in cache['V'])
        else:  # Vertical
            min_y = min(from_y, to_y)
            return ((from_x, min_y) in cache['H'] or 
                    (from_x-1, min_y) in cache['H'])