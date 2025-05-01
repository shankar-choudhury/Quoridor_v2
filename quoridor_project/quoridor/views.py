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
            print(f"Parsed data: {data}")

            engine = QuoridorEngine(game_id)
            old_state = engine.get_state()  
            print(f"Old state type: {type(old_state)}")
            
            success = engine.move_pawn(data["player_id"], data["x"], data["y"])
            print(f"Move result: {success} (type: {type(success)})")
            
            if success:
                new_state = engine.get_state()
                print(f"New state type: {type(new_state)}")
            else:
                print("Move failed, returning original state")
            
            # ADD THIS DEBUG HERE (right before return)
            print("Final state check:")
            import pprint
            pprint.pprint(old_state if not success else new_state)
            
            return JsonResponse({
                "success": success,
                "state": old_state if not success else new_state,
                "message": "" if success else "Invalid move"
            }, status=200 if success else 400)
                
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        
        except Exception as e:
            print(f"EXCEPTION: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({"error": str(e)}, status=400)

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