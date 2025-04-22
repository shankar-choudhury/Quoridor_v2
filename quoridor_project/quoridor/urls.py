from django.urls import path
from . import views

urlpatterns = [
    path("api/game/<int:game_id>/state/", views.get_game_state, name="get_game_state"),
    path("api/game/<int:game_id>/move/", views.move_pawn, name="move_pawn"),
    path("api/game/<int:game_id>/fence/", views.place_fence, name="place_fence"),
]
