from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .game import QuoridorEngine
from .models import Game

# Create your views here.
@csrf_exempt
def home(request):
    game = Game.objects.first()
    return render(request, "index.html", {"game_id": game.id})

@csrf_exempt
def get_game_state(request, game_id):
    try:
        engine = QuoridorEngine(game_id)
        return JsonResponse(engine.get_state())
    except Game.DoesNotExist:
        return JsonResponse({"error": "Game not found"}, status=404)

@csrf_exempt
def move_pawn(request, game_id):
    print("Raw request body:", request.body)
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            print("Parsed JSON data:", data)
            engine = QuoridorEngine(game_id)
            
            # Store the initial state in case the move fails
            initial_state = engine.get_state()
            
            success = engine.move_pawn(data["player_id"], data["x"], data["y"])
            
            if success:
                return JsonResponse({
                    "success": True,
                    "state": engine.get_state()
                })
            else:
                return JsonResponse({
                    "success": False,
                    "state": initial_state,
                    "message": "Invalid move"
                }, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except KeyError as e:
            return JsonResponse({"error": f"Missing field: {str(e)}"}, status=400)
        except Exception as e:
            print("Error:", e)
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
def place_fence(request, game_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            engine = QuoridorEngine(game_id)
            success = engine.place_fence(
                data["player_id"],
                data["x"],
                data["y"],
                data["orientation"]
            )
            return JsonResponse({"success": success, "state": engine.get_state()})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid request method"}, status=405)