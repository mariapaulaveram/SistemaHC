import urllib.request, urllib.parse, json, re
base='http://127.0.0.1:8000'
# create paciente
paciente={'nombre':'PacienteEdit','dni':'EDIT123','fecha_nacimiento':'1980-01-01'}
req=urllib.request.Request(base+'/pacientes/api', data=json.dumps(paciente).encode('utf-8'), headers={'Content-Type':'application/json'})
with urllib.request.urlopen(req, timeout=10) as r:
    pp=json.load(r)
print('pid',pp['id'])
pid=pp['id']
# create consulta
form={'fecha':'2026-06-29','motivo':'MotivoOriginal','diagnostico':'X'}
data=urllib.parse.urlencode(form).encode()
req=urllib.request.Request(base+f'/consultas/pacientes/{pid}', data=data)
with urllib.request.urlopen(req, timeout=10) as r:
    print('created consulta redirect to', r.geturl())
# get patient page and find consulta id
html=urllib.request.urlopen(base+f'/pacientes/{pid}', timeout=10).read().decode()
m=re.search(r'/consultas/(\d+)/editar', html)
if not m:
    print('no consulta id')
    raise SystemExit(1)
cid=m.group(1)
print('cid',cid)
# edit consulta
form2={'fecha':'2026-06-30','motivo':'MotivoEditado','diagnostico':'Y'}
req=urllib.request.Request(base+f'/consultas/{cid}/editar', data=urllib.parse.urlencode(form2).encode())
with urllib.request.urlopen(req, timeout=10) as r:
    print('edit redirect to', r.geturl())
# verify change on patient page
html2=urllib.request.urlopen(base+f'/pacientes/{pid}', timeout=10).read().decode()
print('Edited present?', 'MotivoEditado' in html2)
