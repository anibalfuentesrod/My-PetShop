from django.shortcuts import render, redirect
from django.http import HttpResponse
# Create your views here.


def hello_names(request):
    return HttpResponse('hola anibal y kryss')


