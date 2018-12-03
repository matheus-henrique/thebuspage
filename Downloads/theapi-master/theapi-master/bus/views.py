from django.shortcuts import render
from django.http import HttpResponse,HttpResponseRedirect
from datetime import datetime
from geopy.distance import great_circle

from rest_framework.response import Response
from rest_framework import status
from haversine import haversine
from django.core import serializers

from django.contrib.auth import authenticate, login,logout

from .models import Reclamacao,Veiculo,Linha,LinhaOnibus,Paradas,OnibusInfoArAdpt
from .serializers import ReclamacaoSerializers,LinhaSerializers,LinhaOnibusSerializers,ParadasSerializers
from rest_framework.decorators import api_view
from geopy.geocoders import Nominatim
from django.contrib.auth.decorators import login_required
import requests
import json
import time
import ssl

init = datetime.now()

dados = {"email": "matheusbynickzinho@hotmail.com", "password": "bv0sdq2wb8"}
cb = {"Content-Type": "application/json", "Accept-Language": "en", "Date": "Wed, 13 Apr 2016 12:07:37 GMT", "X-Api-Key":"b4dadc9bd9284ea9afcc5889ba80f04a"}

cadeirantes = ['02194','02200','02196','02186','02148','02555','02128','02501','02563','02511','02521','02134','02773','04391','04402','04415','04451','04435','04349','04372','04401',
'04433','04366','04388','04441','04443','04417','04454','04431','04379','04385','04397','04446','04387','04374','04453','03404','04411','04380','04381','03257','03250','03067','03258',
'03429','03068','03468','03071','03234','03239','03254','01056','01073','01087','01072','01379','03405','03237','01076','01071','01381','01067','01080','01090','01065','01408',
'01220','01077','01393','01405','01074','04425','04365','04351','04398','04414','04452','03065','03066','03026','03448','03445','03454','03460','03451','03457','03469','03472','03416',
'03425','03437','03461','03406','03435','03447','03433','03403','03471','03455','03401','03417','03450','03422','03466','03459','03465','04410','04421','04438','04448','04371','04352',
'04390','04450','04362','04436','04439','01075','01402','01372','01396','01400','01387','01309','01070','01054','04429','04423','04428','04337','04406','04447','02529','02777','02525',
'02551','02789','02531','02782','02527','03072','03037','02783','02774','02788','02559','02519','02509','02505','02198','02212','02204','04407','04424','04358','04440','04404','04449',
'04412','04419','04422','04367','04455','04392','04361','04355','04369','04378','04413','04354','02784','02523','01059','01132','01397','01078','03251','04444','04399','04360','04382',
'04426','04395','04299','04347','01385','01378','01386','04364','04396','04356','04353','02130','02778','04393','02780','02781','04370','04430','04368','04389','01398','01390','01053',
'02190','02557','02547','04445','04357','04405','03069','03070','03242','04427','04376','03418','03462','04442','04386','02549','02553','02776','03233','01066','01069','01089','02154',
'02152','02202','02214','02150','02503','02775','04437','04408','04348','04363','02182','02188','02210','04350','04432','04400','03456','03432','03444','04434','04359','04384','04409',
'03430','02507','03255','04403','03412','04406','03074','03241','02226','02224','04373','02192','02779','02216','03453','03260','03151','01411','01384','01375','03458','03411','03452',
'03436','04420','02533','03252','02771','03031','03240','02772','02222','04416','03446','03256','03147','01062','01138','03147','02228','02208','03243','03238','01060','04383','03431',
'02787','03038','02768','02792','02770','02791','02790','']

sem_info = ['04373','04338','04341','04333','01349','00198','00157','00183','00172','00197','00176','00194','00189','00145','00173','']

ar = ['02563','04451','04454','04446','04453','03258','03468','04452','03469','03472','03461','03471','03466','03465','04448','04450','04447','04449','04455','04444','04445','03462','03074','02226','02224','03260','02222','02228','03038','02792','02791','02790']


def pegar_token():
	print("Iniciando requisição");
	data = requests.post('https://api.inthegra.strans.teresina.pi.gov.br/v1/signin', data=json.dumps(dados),headers = cb)
	cb['X-Auth-Token'] = json.loads(data.text)['token']
	return data


token = 'matheus henrique';
token = pegar_token()
cb['X-Auth-Token'] = json.loads(token.text)['token']
ssl._create_default_https_context = ssl._create_unverified_context



def verifica_token():
	global token
	global init
	now = datetime.now()
	dif = now - init
	print(dif.total_seconds())
	if (dif.total_seconds() >= 540):
		init = datetime.now()
		token = pegar_token()
	else:
		print("Nao precisa de nova requisicao")

@api_view(['GET', 'POST'])
def reclamacoes(request):
	if request.method == 'GET':
		reclamacoes = Reclamacao.objects.all()
		print(reclamacoes)
		serializer = ReclamacaoSerializers(reclamacoes, many=True)
		print(serializer)
		return Response(serializer.data)

@api_view(['GET', 'POST'])
def linhas(request):
	horas = datetime.now()
	verifica_token()
	url = "https://api.inthegra.strans.teresina.pi.gov.br/v1/veiculos"
	data = requests.get(url, data=json.dumps(dados),headers = cb)
	vec = json.loads(data.text)
	linha = ''
	veiculo = ''

	for x in vec:
		codigo_linhav = str(x['Linha']['CodigoLinha'])
		if codigo_linhav[0] == '0':
				codigo_linhav = codigo_linhav[1:4]
		else:
			codigo_linhav = str(x['Linha']['CodigoLinha'])
		if Linha.objects.filter(CodigoLinha=codigo_linhav).exists():
			linha = Linha.objects.get(CodigoLinha=codigo_linhav)
		else:
			num = str(x['Linha']['CodigoLinha'])
			zona = LinhaOnibus.objects.filter(Numero=num[1::])
			if(zona.exists()):
				nome_zona = zona[0].Zona
			else:
				nome_zona = "Outros"
				print("Nao existe : " + num)

			
			codigo_linha = str(x['Linha']['CodigoLinha'])
			if codigo_linha[0] == '0':
				codigo_linha = codigo_linha[1:4]
			else:
				codigo_linha = str(x['Linha']['CodigoLinha'])
			linha = Linha.objects.create(CodigoLinha=codigo_linha,Origem=x['Linha']['Origem'],Retorno=x['Linha']['Retorno'],Denomicao=x['Linha']['Denomicao'], Zona=nome_zona)

		for y in x['Linha']['Veiculos']:
			hora = y['Hora']
			hora = hora[0:2]
			minuto = y['Hora']
			minuto = minuto[3:5]
			segundos = y['Hora']
			segundos = segundos[6:10]
			if(int(hora) == int(horas.hour) and int(minuto) > int(horas.minute)):
				hora_sistema = str(horas.hour)+":"+str(horas.minute)+":"+str(segundos)
			elif(int(hora) == int(horas.hour) and int(minuto) == int(horas.minute) and int(segundos) > int(horas.second)):
				hora_sistema = str(horas.hour)+":"+str(horas.minute)+":"+str(horas.second)
			else:
				hora_sistema = y['Hora']

			if Veiculo.objects.filter(CodigoVeiculo=y['CodigoVeiculo']).exists():
				veiculo = Veiculo.objects.get(CodigoVeiculo=y['CodigoVeiculo'])
				if(veiculo.Lat != y['Lat'] and veiculo.Long != y['Long']):
					veiculo.Lat = y['Lat']
					veiculo.Long = y['Long']
					veiculo.Hora = hora_sistema
					#veiculo.Hora = str(hora.hour)+":"+str(hora.minute)+":"+str(hora.second)
				veiculo.Cadeirante= verifica_onibus_adaptado(veiculo.CodigoVeiculo)
				veiculo.save()
			else:
				veiculo = Veiculo.objects.create(CodigoVeiculo=y['CodigoVeiculo'],Lat=y['Lat'],Long=y['Long'],Hora=hora_sistema,Linha=linha,Cadeirante=verifica_onibus_adaptado(y['CodigoVeiculo']))		
	if request.method == 'GET':
		linha = Linha.objects.all()
		serializer = LinhaSerializers(linha, many=True)
		return Response(serializer.data)



def distancia_raio(request):
	latitude = request.META['HTTP_LATITUDE']
	longitude = request.META['HTTP_LONGITUDE']
	raio = request.META['HTTP_RAIO']
	origem = (float(latitude), float(longitude))
	paradas = Paradas.objects.all()
	paradas_dentro_raio = []
	for x in paradas:
		destino = (float(x.Lat), float(x.Long))
		distancia = great_circle(origem, destino)
		print("Raio : "+ raio)
		teste = str(distancia.km)
		lala = list(teste)

		lala[1] = lala[4]
		lala[4] = "."
		teste = ''.join(lala)
		print(teste)
		a = float(teste)
		print(a)
		
		print(x.Lat+":"+x.Long+" Distancia : "+str(distancia))
		if (a <= float(raio)):
			print(str(distancia.km) + " < " + raio)
			print(x.Lat+":"+x.Long+" Ta dentro")
		else:
			print(x.Lat+":"+x.Long+" Ta fora")



def loginpage(request):
	if request.user.is_authenticated:
		return HttpResponseRedirect("/administracao/")
	else:
		return render(request,'bus/login.html',{})


@login_required(login_url="/login/")
def sair(request):
	logout(request)
	return HttpResponseRedirect("/login/")

@login_required(login_url="/login/")
def resetar(request):
	Linha.objects.all().delete()
	return HttpResponseRedirect("/administracao/")

@login_required(login_url="/login/")
def administracao(request):
	veiculos = Veiculo.objects.all()
	linhas = Linha.objects.all()
	paradas = Paradas.objects.all()
	data = requests.get("https://inthegra.strans.teresina.pi.gov.br/")
	return render(request, 'bus/index.html', {'veiculos' : veiculos, 'linhas' : linhas, 'paradas' : paradas, 'status' : data.status_code})

def validarlogin(request):
	 username = request.POST['username']
	 password = request.POST['password']
	 print(password)
	 user = authenticate(username=username, password=password)
	 if user is not None:
	 	login(request, user)
	 	return HttpResponseRedirect("/administracao/")
	 else:
	 	return HttpResponseRedirect("/login")

def post_list(request):
	global token
	now = datetime.now().minute
	if (now - init >= 9):
		token = pegar_token()
	else:
		print("Nao precisa de nova requisicao")

	return HttpResponse(token.text)



def distancia_onibus_user(request):
	url = "https://maps.googleapis.com/maps/api/distancematrix/json?origins=-5.082728,-42.799080&destinations=-5.096149,-42.757065&mode=bicycling&language=pt-BR&key=AIzaSyAXjVVb85BzbZ3GRIFH6rO2WGmBylGG-0c"
	data = requests.get(url)
	return HttpResponse(data.text)


@api_view(['GET', 'POST'])
def parada_especifica(request,pk):
	url = "https://api.inthegra.strans.teresina.pi.gov.br/v1/paradasLinha?busca="+pk
	verifica_token()
	data = requests.get(url, data=json.dumps(dados),headers = cb)
	lin = json.loads(data.text)
	paradas = json.loads(data.text)

	if data.status_code == 404:
		content = {'please move along': 'nothing to see here'}
		return Response(content, status=status.HTTP_404_NOT_FOUND)
	else:
		return HttpResponse(data.text)




def preecher_pardas(request):
	url = "https://api.inthegra.strans.teresina.pi.gov.br/v1/paradas"
	verifica_token()
	data = requests.get(url, data=json.dumps(dados),headers = cb)
	paradas = json.loads(data.text)
	for x in paradas:
		if(x['Endereco'] != None):
			Paradas.objects.create(CodigoParada=x['CodigoParada'],Denomicao=x['Denomicao'],Endereco=x['Endereco'],Lat=x['Lat'],Long=x['Long'])
	return HttpResponse("OK")

@api_view(['GET', 'POST'])
def qualquer_distancia_dois_pontos(request):
	longitude = request.META['HTTP_LONGITUDE']
	latitude = request.META['HTTP_LATITUDE']
	linha = request.META.get('HTTP_LINHA', None)
	paradas_proximas = []
	paradas_m_proximas = {}
	origem = (float(latitude),float(longitude))
	index = 0
	lala = 0
	i = 0
	if linha:
		url = "https://api.inthegra.strans.teresina.pi.gov.br/v1/paradasLinha?busca="+linha
		verifica_token()
		data = requests.get(url, data=json.dumps(dados),headers = cb)
		paradas = json.loads(data.text)
		paradas = paradas['Paradas']
	else:
		paradas = Paradas.objects.all()
	for x in paradas:
		if linha:
			destino = (float(x['Lat']),float(x['Long']))
		else:
			destino = (float(x.Lat),float(x.Long))
		if index == 0:
			maior = haversine(origem,destino)
			menor = haversine(origem,destino)
			menor_model = x
			maior_model = x

		if (haversine(origem,destino) > maior):
			maior_model = x
			maior = haversine(origem,destino)
		if (haversine(origem,destino) < menor):
			menor_model = x
			menor = haversine(origem,destino)
		index = index + 1

	if linha:
		content = {'CodigoParada' : menor_model['CodigoParada'], 'Denomicao' : menor_model['Denomicao'], 'Endereco' : menor_model['Endereco'], 'Lat' : menor_model['Lat'], 'Long' : menor_model['Long']}
	else:
		content = {'CodigoParada' : menor_model.CodigoParada, 'Denomicao' : menor_model.Denomicao,'Denomicao' : menor_model.Denomicao, 'Endereco' : menor_model.Endereco, 'Lat' : menor_model.Lat, 'Long' : menor_model.Long}
	return Response(content)



@api_view(['GET', 'POST'])
def mostrar_paradas(request):
	if request.method == "GET":
		paradas = Paradas.objects.all()
		serializer = ParadasSerializers(paradas,many=True)
		return Response(serializer.data)


def linhas_estaticas(request):
	verifica_token()
	url = "https://api.inthegra.strans.teresina.pi.gov.br/v1/linhas"
	data = requests.get(url, data=json.dumps(dados),headers = cb)
	lin = json.loads(data.text)
	index = 0;
	s = 0;
	l = 0;
	n = 0;
	su = 0;
	t = 0;
	for x in lin:
		zona = '';
		if (lin[index]['CodigoLinha'] == '0100' or lin[index]['CodigoLinha'] == '0504' or lin[index]['CodigoLinha'] == '0505' or 
			lin[index]['CodigoLinha'] == '0506' or lin[index]['CodigoLinha'] == '0507' or lin[index]['CodigoLinha'] == '0508' or 
			lin[index]['CodigoLinha'] == '0509' or lin[index]['CodigoLinha'] == '0510' or lin[index]['CodigoLinha'] == '0515' or 
			lin[index]['CodigoLinha'] == '0516' or lin[index]['CodigoLinha'] == '0517' or lin[index]['CodigoLinha'] == '0519' or 
			lin[index]['CodigoLinha'] == '0520' or lin[index]['CodigoLinha'] == '0601' or lin[index]['CodigoLinha'] == '0602' or 
			lin[index]['CodigoLinha'] == '0603' or lin[index]['CodigoLinha'] == '0604' or lin[index]['CodigoLinha'] == '0611' or 
			lin[index]['CodigoLinha'] == '0612' or lin[index]['CodigoLinha'] == '0619' or lin[index]['CodigoLinha'] == '0702' or 
			lin[index]['CodigoLinha'] == '0703' or lin[index]['CodigoLinha'] == '0704' or lin[index]['CodigoLinha'] == '0705' or 
			lin[index]['CodigoLinha'] == '0710' or lin[index]['CodigoLinha'] == '0004' or lin[index]['CodigoLinha'] == '0327'):
				print("Sudeste")
				zona = "Sudeste"
				s = s + 1;

		if( lin[index]['CodigoLinha'] == '0245' or lin[index]['CodigoLinha'] == '0401' or lin[index]['CodigoLinha'] == '0402' or 
			lin[index]['CodigoLinha'] == '0403' or lin[index]['CodigoLinha'] == '0404' or lin[index]['CodigoLinha'] == '0405' or 
			lin[index]['CodigoLinha'] == '0406' or lin[index]['CodigoLinha'] == '0501' or lin[index]['CodigoLinha'] == '0502' or 
			lin[index]['CodigoLinha'] == '0503' or lin[index]['CodigoLinha'] == '0512' or lin[index]['CodigoLinha'] == '0513' or 
			lin[index]['CodigoLinha'] == '0518' or lin[index]['CodigoLinha'] == '0521' or lin[index]['CodigoLinha'] == '0522' or
			lin[index]['CodigoLinha'] == '0523' or lin[index]['CodigoLinha'] == '0610' or lin[index]['CodigoLinha'] == '0365'):
				print("leste")
				zona = "Leste"
				l = l + 1;

		if( lin[index]['CodigoLinha'] == '0101' or lin[index]['CodigoLinha'] == '0106' or lin[index]['CodigoLinha'] == '0202' or 
			lin[index]['CodigoLinha'] == '0102' or lin[index]['CodigoLinha'] == '0107' or lin[index]['CodigoLinha'] == '0203' or 
			lin[index]['CodigoLinha'] == '0103' or lin[index]['CodigoLinha'] == '0108' or lin[index]['CodigoLinha'] == '0204' or 
			lin[index]['CodigoLinha'] == '0104' or lin[index]['CodigoLinha'] == '0109' or lin[index]['CodigoLinha'] == '0205' or 
			lin[index]['CodigoLinha'] == '0105' or lin[index]['CodigoLinha'] == '0201' or lin[index]['CodigoLinha'] == '0206' or
			lin[index]['CodigoLinha'] == '0301' or lin[index]['CodigoLinha'] == '0302' or lin[index]['CodigoLinha'] == '0303' or
			lin[index]['CodigoLinha'] == '0304' or lin[index]['CodigoLinha'] == '0730' or lin[index]['CodigoLinha'] == '0563'):
				print("norte")
				zona = "Norte"
				n = n + 1;
		if( lin[index]['CodigoLinha'] == '0605' or lin[index]['CodigoLinha'] == '0606' or lin[index]['CodigoLinha'] == '0607' or 
			lin[index]['CodigoLinha'] == '0608' or lin[index]['CodigoLinha'] == '0609' or lin[index]['CodigoLinha'] == '0613' or 
			lin[index]['CodigoLinha'] == '0614' or lin[index]['CodigoLinha'] == '0615' or lin[index]['CodigoLinha'] == '0616' or 
			lin[index]['CodigoLinha'] == '0617' or lin[index]['CodigoLinha'] == '0618' or lin[index]['CodigoLinha'] == '0620' or
			lin[index]['CodigoLinha'] == '0621' or lin[index]['CodigoLinha'] == '0622' or lin[index]['CodigoLinha'] == '0623' or
			lin[index]['CodigoLinha'] == '0624' or lin[index]['CodigoLinha'] == '0625' or lin[index]['CodigoLinha'] == '0626' or
			lin[index]['CodigoLinha'] == '0627' or lin[index]['CodigoLinha'] == '0688' or lin[index]['CodigoLinha'] == '0706' or
			lin[index]['CodigoLinha'] == '0709' or lin[index]['CodigoLinha'] == '0711' or lin[index]['CodigoLinha'] == '0712' or
			lin[index]['CodigoLinha'] == '0713' or lin[index]['CodigoLinha'] == '0714' or lin[index]['CodigoLinha'] == '0715' or
			lin[index]['CodigoLinha'] == '0716' or lin[index]['CodigoLinha'] == '0801' or lin[index]['CodigoLinha'] == '0802' or
			lin[index]['CodigoLinha'] == '0901' or lin[index]['CodigoLinha'] == '0902' or lin[index]['CodigoLinha'] == '0360' or
			lin[index]['CodigoLinha'] == '0723' or lin[index]['CodigoLinha'] == '0170' or lin[index]['CodigoLinha'] == '0270' or
			lin[index]['CodigoLinha'] == '716' or lin[index]['CodigoLinha'] == '902'):
				print("sul")
				zona = "Sul"
				su = su + 1;
		if( lin[index]['CodigoLinha'] == 'A602' or lin[index]['CodigoLinha'] == 'T501' or lin[index]['CodigoLinha'] == 'A604' or 
			lin[index]['CodigoLinha'] == 'A601' or lin[index]['CodigoLinha'] == 'A505' or lin[index]['CodigoLinha'] == 'A504' or 
			lin[index]['CodigoLinha'] == 'T503' or lin[index]['CodigoLinha'] == 'T502' or lin[index]['CodigoLinha'] == 'T602' or 
			lin[index]['CodigoLinha'] == 'A503' or lin[index]['CodigoLinha'] == 'A502' or lin[index]['CodigoLinha'] == 'A531' or
			lin[index]['CodigoLinha'] == 'T531' or lin[index]['CodigoLinha'] == 'A535' or lin[index]['CodigoLinha'] == 'T532' or
			lin[index]['CodigoLinha'] == 'A534' or lin[index]['CodigoLinha'] == 'A532' or lin[index]['CodigoLinha'] == 'T533' or
			lin[index]['CodigoLinha'] == 'IT01' or lin[index]['CodigoLinha'] == 'A501' or lin[index]['CodigoLinha'] == 'A632' or
			lin[index]['CodigoLinha'] == 'T632' or lin[index]['CodigoLinha'] == 'A634' or lin[index]['CodigoLinha'] == 'A631' or
			lin[index]['CodigoLinha'] == 'T631' or lin[index]['CodigoLinha'] == 'A537' or lin[index]['CodigoLinha'] == 'IT02' or
			lin[index]['CodigoLinha'] == 'A638' or lin[index]['CodigoLinha'] == 'A538' or lin[index]['CodigoLinha'] == 'A637' or
			lin[index]['CodigoLinha'] == 'A636' or lin[index]['CodigoLinha'] == 'A536' or lin[index]['CodigoLinha'] == 'TRLV001'):
				print("terminal")
				zona = "Terminal"
				t = t + 1;

		
		if(not(zona == '')):
			numero = str(lin[index]['CodigoLinha'])
			codigo = ''
			i = 0;
			if (not( zona == "Terminal")):
				for x in numero:
					if (i > 0):
						codigo = codigo + x
					i = i + 1;

				print(codigo)
			else:
				codigo = lin[index]['CodigoLinha']

			if(LinhaOnibus.objects.filter(Numero=codigo).exists()):
				print("Ja Existe")
			else:
				LinhaOnibus.objects.create(Numero=codigo,Denomicao=lin[index]['Denomicao'],Zona=zona)
		index = index + 1
	print("Sudeste "+ str(s))
	print("Leste "+str(l))
	print("Norte "+str(n))
	print("Sul "+str(su))
	print("Terminal "+str(t))


	return HttpResponse("Ok")


def adicionar_onibus_adpt_banco(request):
	for x in ar:
		if (OnibusInfoArAdpt.objects.filter(linha=x).exists()):
			onibus = OnibusInfoArAdpt.objects.get(linha=x)
			onibus.ar = True
			onibus.save()
	return HttpResponse("Ok")

def verifica_onibus_adaptado(num):
	if(OnibusInfoArAdpt.objects.filter(linha=num).exists()):
		return True
	return False

@api_view(['GET', 'POST'])
def converter_lat_long_in_address(request):
	longitude = request.META['HTTP_LONGITUDE']
	latitude = request.META['HTTP_LATITUDE']
	#teste = str(latitude)+","+str(longitude)
	geo = Nominatim()
	#print(teste)
	location = geo.reverse(""+str(latitude)+","+str(longitude)+"",timeout=None)
	print(location.address)
	content = {"Endereco" : location.address}
	return Response(content)



def adicionar_vec_adpt(request):
	if(OnibusInfoArAdpt.objects.filter(linha=request.POST.get('linha')).exists()):
		vec = OnibusInfoArAdpt.objects.get(linha=request.POST.get('linha'))
		vec.adptado = True
		if (request.POST.get('ar') == None):
			vec.ar = False
		else:
			vec.ar = True	
	else:
		if (request.POST.get('ar') == None):
			OnibusInfoArAdpt.objects.create(linha=request.POST.get('linha'),adptado=True, ar=False)
		else:
			OnibusInfoArAdpt.objects.create(linha=request.POST.get('linha'),adptado=True, ar=True)
	return HttpResponseRedirect("/administracao/")


@api_view(['GET', 'POST'])
def todas_linhas_estaticas(request):
	verifica_token()
	if request.method == 'GET':
		linha = LinhaOnibus.objects.all()
		serializer = LinhaOnibusSerializers(linha, many=True)
		return Response(serializer.data)

@api_view(['GET', 'POST'])
def veiculo_especifico(request,pk):
	print("aqui")
	verifica_token()
	if request.method == 'GET':
		linha = Linha.objects.filter(CodigoLinha=pk)
		serializer = LinhaSerializers(linha, many=True)
		return Response(serializer.data)

@api_view(['GET', 'POST'])
def linhas_por_zona(request,pk):
	verifica_token()
	if request.method == 'GET':
		linha = LinhaOnibus.objects.filter(Zona=pk)
		serializer = LinhaOnibusSerializers(linha, many=True)
		return Response(serializer.data)

def excluir_parada(request):
	Linha.objects.all().delete()
	return HttpResponse("Ok")