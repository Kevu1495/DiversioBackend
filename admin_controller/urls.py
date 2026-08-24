from django.urls import path

from .views import health, csv_parser

urlpatterns = [
    path("health", health, name="health"),
    path("csv-parser", csv_parser, name="csv_parser"),

]