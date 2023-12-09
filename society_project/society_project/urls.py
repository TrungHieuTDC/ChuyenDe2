from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from social_profile import views as profile_views
from social_network import views as network_views
urlpatterns = [
    # path("chat/", include("social_network.urls")),
    path("admin/", admin.site.urls),
    path('profile/', include('social_profile.urls')),
    path('fanpage/', include('social_fanpage.urls')),
    path('', include('social_network.urls')),
    
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
