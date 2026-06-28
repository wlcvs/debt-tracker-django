from django.urls import include, path
from . import views

dashboard_patterns = [
    path("", views.dashboard, name="dashboard"),

    path("person/<uuid:pk>/", views.person_detail, name="person_detail"),
    path("person/<uuid:pk>/edit/", views.edit_person, name="edit_person"),
    path("person/<uuid:pk>/delete/", views.delete_person, name="delete_person"),

    path("person/<uuid:pk>/debt/add/", views.add_debt, name="add_debt"),
    path("person/<uuid:pk>/debt/<int:debt_id>/edit/", views.edit_debt, name="edit_debt"),
    path("person/<uuid:pk>/debt/<int:debt_id>/delete/", views.delete_debt, name="delete_debt"),

    path("person/<uuid:pk>/payment/add/", views.add_payment, name="add_payment"),
    path("person/<uuid:pk>/payment/<int:payment_id>/edit/", views.edit_payment, name="edit_payment"),
    path("person/<uuid:pk>/payment/<int:payment_id>/delete/", views.delete_payment, name="delete_payment"),

    path("credit-card/add/", views.add_credit_card, name="add_credit_card"),
    path("credit-card/<int:card_id>/edit/", views.edit_credit_card, name="edit_credit_card"),
    path("credit-card/<int:card_id>/delete/", views.delete_credit_card, name="delete_credit_card"),
]

urlpatterns = [
    path("", views.home_redirect, name="home"),
    path("dashboard/", include(dashboard_patterns)),
    path("login/", views.AppLoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("public/", views.public_landing, name="public_landing"),
    path("public/<uuid:pk>/", views.public_view, name="public_view"),

    path("<path:unknown>/", views.custom_404),
]
