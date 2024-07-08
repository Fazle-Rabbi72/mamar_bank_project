from django.db import models
from django.contrib.auth.models import User
from .constants import ACCOUNT_TYPE,GENDER_TYPE
#django amader k build in user make korar facility diye thake jeta amra User theke pacci

# Create your models here.

class UserBankAccount(models.Model):
    user=models.OneToOneField(User,related_name='account',on_delete=models.CASCADE)
    account_type=models.CharField(max_length=10,choices=ACCOUNT_TYPE)
    account_no=models.IntegerField(unique=True)#account no all time alada hobe.
    birth_date=models.DateField(null=True,blank=True)
    gender=models.CharField(max_length=10,choices=GENDER_TYPE)
    initial_deposite_date=models.DateField(auto_now_add=True)
    balance=models.DecimalField(default=0,max_digits=12,decimal_places=2)#akjon user maximum 12 degit porjonto tk rakhte parbe ar decimal place holo dosomik number ar por dui ta number use korte parbe like as 1000.40
    def __str__(self):
        return str(self.account_no)
    
class UserAddress(models.Model):
    user=models.OneToOneField(User,related_name='address',on_delete=models.CASCADE)#akhane related name ar dara amra user ar name email first or last name access korte parbo tar jonno related name use kora hocce.
    street_address=models.CharField(max_length=100)
    city=models.CharField(max_length=100)
    postal_code=models.IntegerField()
    country=models.CharField(max_length=100)

    def __str__(self):
        return str(self.user.email)