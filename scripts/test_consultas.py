import urllib.request, urllib.parse, json, sys, re
base='http://127.0.0.1:8000'
# 1) Crear paciente vía API
paciente = {
  'nombre':'Paciente Test','dni':'TEST12345','fecha_nacimiento':'1990-01-01','telefono':'12345678','tipo_piel':'media'
}
req = urllib.request.Request(base+'/pacientes/api', data=json.dumps(paciente).encode('utf-8'), headers={'Content-Type':'application/json'})
with urllib.request.urlopen(req, timeout=10) as r:
    pp = json.load(r)
print('Paciente creado:', pp['id'])
pid=pp['id']
# 2) Crear consulta vía formulario
form = {
 'fecha':'2026-06-29','motivo':'Prueba lesion','diagnostico':'Dermatitis','zona_afectada':'brazo','tipo_lesion':'placa','duracion':'3 dias','severidad':'leve','evolucion':'estable','observaciones_clinicas':'observ','tratamiento':'crema','recomendaciones':'evitar sol','notas':'ninguna'
}
data=urllib.parse.urlencode(form).encode()
req = urllib.request.Request(base+f'/consultas/pacientes/{pid}', data=data)
with urllib.request.urlopen(req, timeout=10) as r:
    print('Crear consulta status:', r.getcode(), '->', r.geturl())
# 3) Obtener la ficha de paciente y extraer consulta id from HTML
with urllib.request.urlopen(base+f'/pacientes/{pid}', timeout=10) as r:
    html=r.read().decode('utf-8')
print('Ficha paciente length', len(html))
# try to find consulta id in href /consultas/{id}/editar
m=re.search(r'/consultas/(\d+)/editar', html)
if not m:
    print('No consulta found')
    sys.exit(1)
cid=m.group(1)
print('Encontrada consulta id', cid)
# 4) GET detalle consulta
with urllib.request.urlopen(base+f'/consultas/{cid}', timeout=10) as r:
    print('/consultas/{cid} status', r.getcode())
    detalle=r.read().decode('utf-8')
print('Detalle length', len(detalle))
# 5) Editar consulta
form_edit = form.copy()
form_edit['motivo']='Prueba modificada'
data=urllib.parse.urlencode(form_edit).encode()
req=urllib.request.Request(base+f'/consultas/{cid}/editar', data=data)
with urllib.request.urlopen(req, timeout=10) as r:
    print('Editar consulta status', r.getcode(), '->', r.geturl())
# 6) Verificar cambio en detalle
with urllib.request.urlopen(base+f'/consultas/{cid}', timeout=10) as r:
    html2=r.read().decode('utf-8')
print('Motivo ahora presente?', 'Prueba modificada' in html2)
