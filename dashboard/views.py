# from django.shortcuts import render

# Create your views here.

import random
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from .forms import SignUpForm, EmailAuthenticationForm
from .models import Stock, Subscription


SUPPORTED_STOCKS = ['GOOG', 'TSLA', 'AMZN', 'META', 'NVDA']


def seed_stocks():
    """
    Helper to ensure our 5 stocks exist in the DB.
    You can call this from any view once; it will not duplicate.
    """
    names = {
        'GOOG': 'Alphabet Inc.',
        'TSLA': 'Tesla Inc.',
        'AMZN': 'Amazon.com Inc.',
        'META': 'Meta Platforms Inc.',
        'NVDA': 'NVIDIA Corporation',
    }
    for ticker in SUPPORTED_STOCKS:
        Stock.objects.get_or_create(
            ticker=ticker,
            defaults={'name': names.get(ticker, ticker)}
        )


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully. Please log in.")
            return redirect('login')
    else:
        form = SignUpForm()

    return render(request, 'dashboard/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid email or password.")
    else:
        form = EmailAuthenticationForm()

    return render(request, 'dashboard/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard_view(request):
    # ensure base stocks exist
    seed_stocks()

    stocks = Stock.objects.filter(ticker__in=SUPPORTED_STOCKS)
    user_subscriptions = Subscription.objects.filter(user=request.user)
    subscribed_tickers = set(sub.stock.ticker for sub in user_subscriptions)

    context = {
        'stocks': stocks,
        'subscribed_tickers': subscribed_tickers,
    }
    return render(request, 'dashboard/dashboard.html', context)


@login_required
def toggle_subscription(request, ticker):
    """
    Called when user clicks Subscribe/Unsubscribe button.
    """
    if request.method == 'POST':
        stock = get_object_or_404(Stock, ticker=ticker)
        sub, created = Subscription.objects.get_or_create(
            user=request.user,
            stock=stock
        )
        if not created:
            # already existed -> unsubscribe
            sub.delete()
            messages.info(request, f"Unsubscribed from {ticker}.")
        else:
            messages.success(request, f"Subscribed to {ticker}.")
    return redirect('dashboard')


def generate_random_price(ticker):
    """
    Generate a pseudo-random price per ticker.
    You can customize ranges per stock.
    """
    base_prices = {
        'GOOG': 1500,
        'TSLA': 700,
        'AMZN': 3200,
        'META': 300,
        'NVDA': 800,
    }
    base = base_prices.get(ticker, 100)
    # random fluctuation
    return round(base + random.uniform(-50, 50), 2)


@login_required
def api_prices(request):
    """
    Return JSON: {ticker: price} for currently subscribed stocks of the user.
    Called via JavaScript every second.
    """
    user_subscriptions = Subscription.objects.filter(user=request.user)
    data = {}
    for sub in user_subscriptions:
        ticker = sub.stock.ticker
        data[ticker] = generate_random_price(ticker)

    return JsonResponse(data)

