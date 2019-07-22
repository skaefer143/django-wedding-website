from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^secret-sneak-peek/$', views.sneak_peek, name='sneak_peek'),
    url(r'^wip/$', views.wip, name='wip'),
]
