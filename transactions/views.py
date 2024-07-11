# transactions/views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.http import HttpResponse
from django.views.generic import CreateView, ListView
from transactions.constants import DEPOSIT, WITHDRAWAL, LOAN, LOAN_PAID
from datetime import datetime
from django.db.models import Sum
from django.core.mail import EmailMultiAlternatives,send_mail
from django.template.loader import render_to_string
from django.conf import settings
from transactions.forms import (
    DepositForm,
    WithdrawForm,
    LoanRequestForm,
    TransferForm
)
from transactions.models import Transaction
from django.contrib.auth.models import User
from accounts.models import UserBankAccount

def send_transaction_mail(user,amount,subject,template):
    
        massage=render_to_string(template,{
            'user':user,
            'amount':amount,
        })
        send_email=EmailMultiAlternatives(subject,'',to=[user.email])
        send_email.attach_alternative(massage,"text/html")
        send_email.send()

def send_transaction_mail2(user, recipient, amount):
    subject = "Money Transfer Notification"
    sender_email = settings.DEFAULT_FROM_EMAIL
    sender_message = render_to_string('transactions/transfer_mail_sender.html', {
        'user': user,
        'amount': amount,
        'recipient': recipient
    })
    recipient_message = render_to_string('transactions/transfer_mail_recipient.html', {
        'user': user,
        'amount': amount,
        'recipient': recipient
    })
    
    send_email_to_sender = EmailMultiAlternatives(subject, '', sender_email, [user.email])
    send_email_to_sender.attach_alternative(sender_message, "text/html")
    send_email_to_sender.send()
    
    send_email_to_recipient = EmailMultiAlternatives(subject, '', sender_email, [recipient.email])
    send_email_to_recipient.attach_alternative(recipient_message, "text/html")
    send_email_to_recipient.send()


class TransactionCreateMixin(LoginRequiredMixin, CreateView):
    template_name = 'transactions/transaction_form.html'
    model = Transaction
    title = ''
    success_url = reverse_lazy('transaction_report')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'account': self.request.user.account
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': self.title
        })
        return context

class DepositMoneyView(TransactionCreateMixin):
    form_class = DepositForm
    title = 'Deposit'

    def get_initial(self):
        initial = {'transaction_type': DEPOSIT}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.account
        account.balance += amount
        account.save(update_fields=['balance'])
        messages.success(self.request, f'{"{:,.2f}".format(float(amount))}$ was deposited to your account successfully')
        send_transaction_mail(self.request.user, amount, "Deposite Massege","transactions/deposite_mail.html")
        return super().form_valid(form)
    

class WithdrawMoneyView(TransactionCreateMixin):
    form_class = WithdrawForm
    title = 'Withdraw Money'

    def get_initial(self):
        initial = {'transaction_type': WITHDRAWAL}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.account
        # Check if the bank is bankrupt
        if Transaction.objects.filter(is_bankrupt=True).exists():
            messages.error(self.request, 'The bank is bankrupt. Withdrawal not allowed.')
        elif amount <= account.balance:
            account.balance -= amount
            account.save(update_fields=['balance'])
            messages.success(self.request, f'Successfully withdrawn {"{:,.2f}".format(float(amount))}$ from your account')
            send_transaction_mail(self.request.user, amount, "Withdrawal Massege","transactions/Withdrawal_mail.html")
        else:
            messages.error(self.request, 'The bank is bankrupt.')    
        return super().form_valid(form)

class LoanRequestView(TransactionCreateMixin):
    form_class = LoanRequestForm
    title = 'Request For Loan'

    def get_initial(self):
        initial = {'transaction_type': LOAN}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        current_loan_count = Transaction.objects.filter(account=self.request.user.account, transaction_type=LOAN, loan_approve=True).count()
        if current_loan_count >= 3:
            return HttpResponse("You have crossed the loan limits")
        messages.success(self.request, f'Loan request for {"{:,.2f}".format(float(amount))}$ submitted successfully')
        send_transaction_mail(self.request.user, amount, "Loan Request Massege","transactions/loan_mail.html")
        return super().form_valid(form)

class TransactionReportView(LoginRequiredMixin, ListView):
    template_name = 'transactions/transaction_report.html'
    model = Transaction
    balance = 0

    def get_queryset(self):
        queryset = super().get_queryset().filter(account=self.request.user.account)
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            queryset = queryset.filter(timestamp__date__gte=start_date, timestamp__date__lte=end_date)
            self.balance = Transaction.objects.filter(timestamp__date__gte=start_date, timestamp__date__lte=end_date).aggregate(Sum('amount'))['amount__sum']
        else:
            self.balance = self.request.user.account.balance
        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'account': self.request.user.account
        })
        return context

class PayLoanView(LoginRequiredMixin, View):
    def get(self, request, loan_id):
        loan = get_object_or_404(Transaction, id=loan_id)
        if loan.loan_approve:
            user_account = loan.account
            if loan.amount <= user_account.balance:
                user_account.balance -= loan.amount
                loan.balance_after_transaction = user_account.balance
                user_account.save()
                loan.transaction_type = LOAN_PAID
                loan.save()
                return redirect('loan_list')
            else:
                messages.error(self.request, 'Loan amount is greater than available balance')
        return redirect('loan_list')

class LoanListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'transactions/loan_request.html'
    context_object_name = 'loans'

    def get_queryset(self):
        user_account = self.request.user.account
        queryset = Transaction.objects.filter(account=user_account, transaction_type=LOAN)
        return queryset

@login_required
def transfer_money(request):
    if request.method == 'POST':
        form = TransferForm(request.POST)
        if form.is_valid():
            recipient_account_number = form.cleaned_data['recipient_account_number']
            amount = form.cleaned_data['amount']
            try:
                recipient_account = UserBankAccount.objects.get(account_no=recipient_account_number)
                if request.user.account.balance >= amount:
                    request.user.account.balance -= amount
                    recipient_account.balance += amount
                    request.user.account.save()
                    recipient_account.save()
                    Transaction.objects.create(
                        account=request.user.account,
                        recipient_account=recipient_account,
                        amount=amount,
                        balance_after_transaction=request.user.account.balance,
                        transaction_type=5
                    )
                    send_transaction_mail2(request.user, recipient_account.user, amount)
                    messages.success(request, 'Transfer successful.')
                else:
                    messages.error(request, 'Insufficient balance.')
            except UserBankAccount.DoesNotExist:
                messages.error(request, 'Recipient account not found.')
            return redirect('transfer_money')
    else:
        form = TransferForm()
    return render(request, 'transactions/transfer.html', {'form': form})

