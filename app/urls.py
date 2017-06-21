from django.conf.urls import url
from app import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^login/$', views.Login.as_view(), name='login'),
    url(r'^home/$', views.home, name='home'),
    url(r'^stock/$', views.stock, name='stock'),
    url(r'^stats/$', views.stats, name='stats'),
    url(r'^test/$', views.test, name='test'),
    url(r'^signup/$', views.SignUp.as_view(), name='signup'),
    url(r'^logout/', views.logout, name='logout'),
    url(r'^stock/$', views.stock, name='stock'),
    url(r'^stats/$', views.stats, name='stats'),
    url(r'^edit_account$', views.EditAccount.as_view(), name='edit_account'),
    url(r'^agregar_producto$', views.AgregarProducto.as_view(), name='add_product'),
    url(r'^edit_product/(?P<pid>[0-9]+)/$', views.EditProduct.as_view(), name='edit_products'),
    url(r'^vendor/(?P<pid>[0-9]+)/$', views.vendor_info, name='vendor_info'),
    url(r'^ajax/like/$', views.like, name='like'),
    url(r'^ajax/check_in/$', views.check_in, name='check_in'),
    url(r'^ajax/delete_product/$', views.delete_product, name='del_p'),
    url(r'^ajax/delete_account/$', views.delete_account, name='del_a'),
    url(r'^ajax/stock/$', views.adm_stock, name='adm_stock'),
    url(r'^ajax/stats/$', views.interval_chart, name='interval_chart'),
    url(r'^ajax/alerta/$', views.alerta, name='alerta'),
]
