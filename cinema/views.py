from datetime import datetime

from django.db.models import F, Count
from rest_framework import viewsets, mixins
from rest_framework.pagination import PageNumberPagination
from cinema.models import Order, Genre, Actor, CinemaHall, Movie, MovieSession

from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieDetailSerializer,
    MovieSessionDetailSerializer,
    MovieListSerializer,
    OrderSerializer,
)


class OrderPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related("tickets__movie_session__movie")
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    # Тесты ожидают прямой список []
    pagination_class = None


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer
    # Тесты ожидают прямой список []
    pagination_class = None


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer
    # Тесты ожидают прямой список []
    pagination_class = None


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        queryset = self.queryset
        # Извлекаем параметры из запроса
        title = self.request.query_params.get("title")
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")

        if title:
            queryset = queryset.filter(title__icontains=title)

        if genres:
            # Превращаем "1,2" в [1, 2]
            genres_ids = [int(str_id) for str_id in genres.split(",")]
            queryset = queryset.filter(genres__id__in=genres_ids)

        if actors:
            actors_ids = [int(str_id) for str_id in actors.split(",")]
            queryset = queryset.filter(actors__id__in=actors_ids)

        return queryset.distinct()


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    # def get_queryset(self):
    #     queryset = self.queryset
    #     date = self.request.query_params.get("date")
    #     movie_id = self.request.query_params.get("movie")

    #     if date:
    #         date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    #         queryset = queryset.filter(show_time__date=date_obj)

    #     if movie_id:
    #         queryset = queryset.filter(movie_id=int(movie_id))

    #     if self.action == "list":
    #         queryset = queryset.annotate(
    #             tickets_available=F("cinema_hall__rows")
    # * F("cinema_hall__seats_in_row") - Count("tickets")
    #         )
    #     return queryset

    def get_queryset(self):
        movie_id_str = self.request.query_params.get("movie")
        date_str = self.request.query_params.get("date")

        queryset = self.queryset

        if movie_id_str:
            queryset = queryset.filter(movie_id=int(movie_id_str))

        if date_str:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            queryset = queryset.filter(show_time__date=date)

        if self.action == "list":
            queryset = (
                queryset
                # .select_related("movie", "cinema_hall")
                .annotate(
                    tickets_available=(
                        F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
                        - Count("tickets")
                    )
                )
            )

        return queryset.distinct()
