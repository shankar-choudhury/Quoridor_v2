from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .game import QuoridorEngine
from .models import Game

# Create your views here.
def home(request):
    return render(request, "index.html")

def get_game_state(request, game_id):
    try:
        engine = QuoridorEngine(game_id)
        return JsonResponse(engine.get_state())
    except Game.DoesNotExist:
        return JsonResponse({"error": "Game not found"}, status=404)

@csrf_exempt
def move_pawn(request, game_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            engine = QuoridorEngine(game_id)
            success = engine.move_pawn(data["player_id"], data["x"], data["y"])
            return JsonResponse({"success": success, "state": engine.get_state()})
        except Exception as e:
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