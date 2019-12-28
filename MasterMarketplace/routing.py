from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter, ChannelNameRouter
from channels.security.websocket import AllowedHostsOriginValidator

import support.routing
import projects.routing
import tracking.routing
import virustotal.consumers

application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                support.routing.websocket_urlpatterns +
                tracking.routing.websocket_urlpatterns +
                projects.routing.websocket_urlpatterns
            )
        )
    ),
    'channel': ChannelNameRouter({
        'virustotal': virustotal.consumers.VirustotalProcess
    })
})
