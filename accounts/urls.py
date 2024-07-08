from django.contrib.auth.decorators import login_required
from django.urls import path
from .views import UserRegistrationView,UserLoginView,UserLogoutView,UserBankAccountUpdateView,UserPasswordChangeView
urlpatterns = [
   path('register/',UserRegistrationView.as_view(),name='register'),
   path('login/', UserLoginView.as_view(), name='login'),
   path('logout/', UserLogoutView.as_view(), name='logout'),
   path('profile/', UserBankAccountUpdateView.as_view(), name='profile' ),
   path('change-password/', login_required(UserPasswordChangeView.as_view()), name='change_password'),
]