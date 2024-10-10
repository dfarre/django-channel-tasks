"""To be imported as a Django setup step before model loading."""
from django.core.asgi import get_asgi_application

application = get_asgi_application()
