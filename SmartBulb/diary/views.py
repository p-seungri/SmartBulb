from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import datetime
from pathlib import Path
from accounts.models import CustomUser
from accounts.views import bulb_ip
from .models import Sentiment, Diary
from .form import DiaryPost
import pandas as pd
from yeelight import discover_bulbs, Bulb
import random
# from soynlp.normalizer import *
# from hanspell import spell_checker
import os
import sys
# Create your views here.

BASE_DIR = Path(__file__).resolve().parent.parent
filename = os.path.join(BASE_DIR, 'diary', 'sentiment.csv')
bulb_reqeust = False
bulb_on = 0
sentiment_to_light = {
    "긍정": [[0, 0, 255], [129, 193, 71]],
    "중립": [[255, 127, 0], [255, 0, 0]],
    "부정": [[255, 212, 0], [255, 212, 0]]
}

def analyze_sentiment(sentence):
    sentiment = Sentiment.objects.get(sentiment="부정")

    return sentiment


def init_db(request):
    data = pd.read_csv(filename, encoding='utf-8')

    data = data['sentiment']

    for sent in data:
        sentiment = Sentiment()
        sentiment.sentiment = sent
        sentiment.save()

    return redirect('home')


def main_diary(request):
    if not request.user.is_authenticated:
        return render(request, "main_diary.html", {"validity": 0})

    return render(request, "main_diary.html")


@login_required
def save_diary(request, year, month, day):
    diaries = Diary.objects.filter(user=request.user.id)
    user = CustomUser.objects.filter(username=str(request.user))
    date_time_str = str(year) + '-' + str(month) + '-' + str(day)
    date_time_str = datetime.datetime.strptime(date_time_str, '%Y-%m-%d')

    if diaries is not None:
        for diary in diaries:
            i = 0
            pub_date_converted = str(diary.pub_date)
            date_time_str = str(date_time_str)
            date_time_str = date_time_str[:len(pub_date_converted)]

            if pub_date_converted == date_time_str:
                return redirect("view_diary", str(diary.id))

    if request.method == "POST":
        form = DiaryPost(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = user[0]
            post.pub_date = date_time_str
            post.sentiment = analyze_sentiment(post.text)
            post.save()
            return redirect("view_diary", str(post.id))
    else:
        form = DiaryPost()
        return render(request, "new.html", {'form': form, 'year': year, 'month': month, 'day': day})


@login_required
def view_diary(request, diary_id):
    global bulb_reqeust, bulb_on
    diary = Diary.objects.filter(user=request.user.id)
    diary_text = get_object_or_404(diary, pk=diary_id)

    if bulb_reqeust:
        bulb_reqeust = False
        return render(request, "diary.html", {'diary': diary_text, 'bulb_on': bulb_on})
    else:
        return render(request, "diary.html", {'diary': diary_text})


@login_required
def delete_diary(request, diary_id):
    diary = Diary.objects.filter(user=request.user.id)
    diary_text = get_object_or_404(diary, pk=diary_id)
    diary_text.delete()
    return redirect("main_diary")


@login_required
def edit_diary(request, diary_id):
    diary = Diary.objects.filter(user=request.user.id)
    diary_text = get_object_or_404(diary, pk=diary_id)

    if request.method == "POST":
        form = DiaryPost(request.POST)
        if form.is_valid():
            diary_text.title = form.cleaned_data['title']
            diary_text.text = form.cleaned_data['text']
            diary_text.sentiment = analyze_sentiment(diary_text.text)
            diary_text.save()
            return redirect("view_diary", str(diary_text.id))
    else:
        form = DiaryPost(instance=diary_text)
        context = {
            'form': form,
            'writing': True,
            'now': 'edit',
            'diary': diary_text,
        }
        return render(request, "edit.html", context)


def statistics(request, year, month):
    diaries = Diary.objects.filter(user=request.user.id)

    sentiment_dict = {}

    max_value = 0
    max_sentiment = ""

    if not diaries:
        return render(request, "statistics.html", {'sentiment_dict': 0})
    else:

        for diary in diaries:
            try:
                sentiment_dict[diary.sentiment] += 1
            except Exception as err:
                sentiment_dict[diary.sentiment] = 1

        for k, v in sentiment_dict.items():
            if max_value < v:
                max_value = v
                max_sentiment = k

        return render(request, "statistics.html", {'sentiment_dict': sentiment_dict, 'freq_sent': max_sentiment})


def turn_on_bulbs(request, diary_id):
    global bulb_reqeust, bulb_on
    
    #기존 코드 시작
    # bulb_reqeust = True
    # if not bulb_ip:
    #     bulb_on = 0
    #     return redirect("view_diary", str(diary_id))
    # else:
    #     diary = Diary.objects.filter(user=request.user.id)
    #     diary_text = get_object_or_404(diary, pk=diary_id)

    #     bulb_on = 1
    #     index = random.randint(0, 1)

    #     bulb = Bulb(bulb_ip)
    #     bulb.set_rgb(sentiment_to_light[diary_text.sentiment][index])

    #     bulb.toggle()
    #기존 코드 끝

    #수현 테스트 시작
    bulb_data = discover_bulbs()
    bulb_ip = bulb_data[0]['ip']

    bulb_reqeust = True
    if not bulb_ip:
        bulb_on = 0
        return redirect("view_diary", str(diary_id))
    else:
        diary = Diary.objects.filter(user=request.user.id)
        diary_text = get_object_or_404(diary, pk=diary_id)

        bulb_on = 1
        index = random.randint(0, 1)

        #전구 연결
        bulb = Bulb(bulb_ip)

        #전구가 꺼져있을 때 켜기
        if bulb.get_properties()['power'] == 'off':
            bulb.turn_on()
        
        bulb.set_rgb(*(sentiment_to_light["부정"][index])) #sentiment 불러오는 게 아직 안돼서 작동이 안되는지 모르겠음
    #수현 테스트 끝


        return redirect("view_diary", str(diary_id))
