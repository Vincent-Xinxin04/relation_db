# urls.py
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views

from core.utils.performance import performance_log
from core.views import order_manage, order_create, order_update_status, order_delete, customer_detail, update_customer, delete_customer, create_customer

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', performance_log(auth_views.LoginView.as_view(template_name='login.html')), name='login'),
    path('logout/', performance_log(auth_views.LogoutView.as_view(next_page='login')), name='logout'),
    path('', order_manage, name='order_manage'),
    path('order/create/', order_create, name='order_create'),
    path('order/update_status/', order_update_status, name='order_update_status'),
    path('order/delete/', order_delete, name='order_delete'),
    path('customer/<int:customer_id>/', customer_detail, name='customer_detail'),
    path('customer/<int:customer_id>/update/', update_customer, name='update_customer'),
    path('customer/<int:customer_id>/delete/', delete_customer, name='delete_customer'),
    path('customer/create/', create_customer, name='create_customer'),
]