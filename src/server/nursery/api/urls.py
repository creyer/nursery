from django.conf.urls import patterns, url

from api import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    #init a new repo config
    url(r'^(?P<repo>[\w+\-.]+)/init/$', views.init, name='init'),
    #manually deploy something
    url(r'^(?P<repo>[\w+\-.]+)/deploy/$', views.deploy, name='deploy'),
    #get the status for the branch on repo
    url(r'^(?P<repo>[\w+\-.]+)/status/$', views.status, name='status'),
    #rollback to some hash version
    url(r'^(?P<repo>[\w+\-.]+)/(?P<branch>[\w+\-.]+)/rollback/$', views.rollback, name='rollback'),
    #modify some configuration
    url(r'^(?P<repo>[\w+\-.]+)/(?P<branch>[\w+\-.]+)/modify/$', views.modify, name='modify'),
    #get info from the past who di what
    url(r'^(?P<repo>[\w+\-.]+)/(?P<branch>[\w+\-.]+)/audit/(?:(?P<history_length>))$', views.audit, name='audit'),
)