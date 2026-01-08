from .models import *



def general(request):
    gen = SkBank.objects.get(pk=1)

    context = {
   	 'gen': gen,
   	}

    return context