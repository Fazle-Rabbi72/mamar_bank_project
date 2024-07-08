from django.shortcuts import render, redirect
from django.views.generic import FormView, View
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth import login, logout
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from .forms import UserRegistrationForm, UserUpdateForm

class UserRegistrationView(FormView):
    template_name = 'accounts/user_registration.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('login')
    
    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, 'Registration successful. You are now logged in.')
        return super().form_valid(form)

class UserLoginView(LoginView):
    template_name = 'accounts/user_login.html'

    def get_success_url(self):
        messages.success(self.request, 'Logged in successfully.')
        return reverse_lazy('home')

class UserLogoutView(LogoutView):
    def get_success_url(self):
        if self.request.user.is_authenticated:
            logout(self.request)
            messages.success(self.request, 'Logged out successfully.')
        return reverse_lazy('home')
    
class UserBankAccountUpdateView(View):
    template_name = 'accounts/profile.html'

    def get(self, request):
        form = UserUpdateForm(instance=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')  # Redirect to the user's profile page
        return render(request, self.template_name, {'form': form})    

class UserPasswordChangeView(PasswordChangeView):
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        subject='Password Changed Successfully'
        message = render_to_string('accounts/password_change_email.html', {
            'user': self.request.user,
        })
        to_email=self.request.user.email
        send_mail=EmailMultiAlternatives(subject,'',to=[to_email])
        send_mail.attach_alternative(message,"text/html")
        send_mail.send()
        messages.success(self.request, 'Password changed successfully. An email notification has been sent.')
        return super().form_valid(form)
