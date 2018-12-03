from django.contrib import admin
from .models import Reclamacao,Veiculo,Linha,LinhaOnibus,Paradas,OnibusInfoArAdpt

# Register your models here.

admin.site.register(Reclamacao)
admin.site.register(Veiculo)
admin.site.register(Linha)
admin.site.register(LinhaOnibus)
admin.site.register(Paradas)
admin.site.register(OnibusInfoArAdpt)