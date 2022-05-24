from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .models import CustomUser
from django.contrib import auth
from yeelight import discover_bulbs, Bulb


# Create your views here.
bulb_ip = ""

def login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect("home")
        else:
            return render(request, "login.html", {"validity": 0})
    else:
        return render(request, "login.html", {"validity": 1})


def signup(request):
    if request.method == "POST":
        try:
            if CustomUser.objects.filter(username=request.POST['username']).exists():
                return render(request, "signup.html", {"registered": 1, "validity": 1, "filled": 1})
            elif request.POST["password1"] == request.POST["password2"]:
                user = CustomUser.objects.create_user(
                    username=request.POST["username"], password=request.POST["password1"])
                auth.login(request, user)
                return redirect('home')
            else:
                return render(request, "signup.html", {"registered": 0, "validity": 0, "filled": 1})
        except Exception as e:
            print(e)
            return render(request, "signup.html", {"registered": 0, "validity": 1, "filled": 0})
    return render(request, 'signup.html', {"registered": 0, "validity": 1, "filled": 1})


def logout(request):
    auth.logout(request)
    return redirect("home")


# @login_required
def mypage(request):
    return render(request, 'mypage.html')


def register_bulb(request):
    global bulb_ip
    bulb_data = discover_bulbs() #딕셔너리 형태로 저장

    #수현 수정 시작
    # register = 0
    # try:
    #     bulb_ip = bulb_data[0]['ip']
    #     bulb = Bulb(bulb_ip)
    #     # RED = [255, 0, 0]
    #     # bulb.set_rgb(*RED)
    #     register = 1
    # except Exception as err:
    #     pass
    #수현 수정 끝

    #기존 코드 시작
    register = 0
    for bulb in bulb_data:
        try:
            bulb_ip = bulb['ip']
            register = 1
            bulb = Bulb(bulb_ip)
            # RED = [255, 0, 0]
            # bulb.set_rgb(*RED)
        except Exception as err:
            pass
    #기존 코드 끝
    
    return render(request, "mypage.html", {"register": register});



