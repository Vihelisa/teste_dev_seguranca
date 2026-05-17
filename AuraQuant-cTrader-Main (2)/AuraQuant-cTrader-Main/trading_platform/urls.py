from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    healthcheck,
    login_user,
    register_user,
    verify_email,
    get_current_user,
    password_reset_request,
    password_reset_confirm,
    change_password,
    TradingAccountViewSet,
    StrategyViewSet,
    ActiveRobotInstanceViewSet,
    account_pulse,
    get_trade_history,
    get_equity_history,
    get_market_data,
    TaskStatusView,
    TradeLogViewSet,
    UserProfileViewSet,
    NotificationViewSet,
    FavoriteTickersView,
    StartAnalysisView,
    AnalysisStatusView,
    SafetyStatusView,
)

app_name = 'trading_platform'

router = DefaultRouter()
router.register(r'accounts', TradingAccountViewSet, basename='mt5account')
router.register(r'strategies', StrategyViewSet, basename='strategy')
router.register(r'instances', ActiveRobotInstanceViewSet, basename='activerobotinstance')
router.register(r'trade-logs', TradeLogViewSet, basename='tradelog')
router.register(r'profile', UserProfileViewSet, basename='userprofile')
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    # Healthcheck and Auth
    path('healthcheck/', healthcheck, name='healthcheck'),
    path('login/', login_user, name='login'),
    path('register/', register_user, name='register'),
    path('verify-email/', verify_email, name='verify_email'),
    path('user/', get_current_user, name='get_current_user'),
    path('password-reset/', password_reset_request, name='password_reset_request'),
    path('password-reset-confirm/', password_reset_confirm, name='password_reset_confirm'),
    path('change-password/', change_password, name='change_password'),

    # Data endpoints
    path('account-pulse/', account_pulse, name='account_pulse'),
    path('trade-history/', get_trade_history, name='get_trade_history'),
    path('equity-history/', get_equity_history, name='get_equity_history'),
    path('market-data/', get_market_data, name='get_market_data'),
    path('safety-status/', SafetyStatusView.as_view(), name='safety_status'),
    
    # Aura Portfolio AI
    path('analysis/start/', StartAnalysisView.as_view(), name='start_analysis'),
    path('analysis/status/<uuid:analysis_id>/', AnalysisStatusView.as_view(), name='analysis_status'),

    # Other endpoints
    path('task-status/<str:task_id>/', TaskStatusView.as_view(), name='task_status'),
    path('favorite-tickers/', FavoriteTickersView.as_view(), name='user-favorite-tickers'),
    
    # Router URLs
    path('', include(router.urls)),
]