import requests
import re

BASE = "http://localhost:8000"

print("[1] Obteniendo lista de pacientes...")
r = requests.get(f"{BASE}/pacientes")
print("LIST STATUS", r.status_code)

text = r.text
print("RESPONSE LENGTH", len(text))

# Buscar pacientes en la lista (href="/pacientes/{id}">nombre</a> ... <span>DNI</span>)
matches = re.findall(r'href="/pacientes/(\d+)[^>]*>\s*([^<]+)[\s\S]*?<span>([^<]+)</span>', text)
print("FOUND", len(matches), "pacientes")

if matches:
    pid, name, dni = matches[0]
    print(f"\n[2] Primer paciente: id={pid} name='{name.strip()}' dni='{dni.strip()}'")
    
    dni_clean = dni.strip()
    print(f"\n[3] Buscando por DNI exacto: {dni_clean}")
    r2 = requests.get(f"{BASE}/pacientes?q={dni_clean}", allow_redirects=False)
    print("SEARCH STATUS", r2.status_code)
    print("LOCATION HEADER", r2.headers.get("location"))
    
    if r2.status_code in (302, 303):
        print("✓ REDIRECT DETECTADO - búsqueda funciona!")
    else:
        print("✗ SIN REDIRECT - búsqueda retorna lista")
        print("RESPONSE SNIPPET", r2.text[:500])
else:
    print("\n✗ No se encontraron pacientes en la lista")
    print("RESPONSE:", text[:1000])
