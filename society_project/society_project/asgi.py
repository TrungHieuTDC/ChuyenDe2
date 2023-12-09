# asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
# Đảm bảo thay thế 'myapp' bằng tên thực sự của ứng dụng của bạn
from social_network import routing as app_routing
from social_network.routing import websocket_urlpatterns
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'society_project.settings')
import social_network.routing
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})