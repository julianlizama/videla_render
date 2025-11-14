from .models import SiteConfig

def site_config(request):
    config = SiteConfig.objects.first()
    return {"site_config": config}
