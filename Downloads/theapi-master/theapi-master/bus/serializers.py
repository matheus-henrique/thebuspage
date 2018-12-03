from rest_framework import serializers
from .models import Reclamacao,Veiculo,Linha,LinhaOnibus,Paradas



class ReclamacaoSerializers(serializers.ModelSerializer):
	class Meta:
		model = Reclamacao
		fields = ('id','user','texto','img')


class VeiculoSerializers(serializers.ModelSerializer):
	class Meta:
		model = Veiculo
		fields = ('CodigoVeiculo','Lat','Long','Hora','Cadeirante')

class LinhaSerializers(serializers.ModelSerializer):
	Veiculos = VeiculoSerializers(many=True)
	class Meta:
		model = Linha
		fields = ('CodigoLinha','Origem','Retorno','Denomicao','Veiculos','Zona')



class ParadasSerializers(serializers.ModelSerializer):	
	class Meta:
		model = Paradas
		fields = ('CodigoParada','Denomicao','Endereco','Lat','Long')


class LinhaOnibusSerializers(serializers.ModelSerializer):
	class Meta:
		model = LinhaOnibus
		fields = ('Numero','Denomicao','Zona') 









