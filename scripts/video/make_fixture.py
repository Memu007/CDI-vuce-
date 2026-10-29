import sys
from openpyxl import Workbook
wb = Workbook(); ws = wb.active; ws.title = "Items"
# Encabezados como los escribe un cliente: CDI aprende el mapeo por cliente.
ws.append(["Partida arancelaria","Producto","País de origen","Unidades","Precio unitario (USD)","Peso unitario (kg)"])
ws.append(["84713012","Notebook 14'' Core i5 8GB RAM 256GB SSD","CN",40,420.00,1.50])
ws.append(["84713012","Notebook 15.6'' Core i7 16GB RAM 512GB SSD","CN",25,690.00,1.90])
ws.append(["84713012","Notebook 17'' Core i7 16GB RAM 1TB SSD","CN",10,830.00,2.40])
wb.save(sys.argv[1])

# Planilla de clientes para «Traer mis clientes» (CUIT con dígito verificador
# válido, obviamente ficticios). Textil Andina ya existe: muestra «existentes».
if len(sys.argv) > 2:
    import csv
    with open(sys.argv[2], "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Razón social", "CUIT", "Domicilio", "Email", "Teléfono"])
        w.writerow(["Textil Andina S.R.L.", "30-00000001-5", "Ruta 9 km 12, Córdoba", "compras@textilandina.test", "351 400 0000"])
        w.writerow(["Metalúrgica Litoral S.A.", "30-00000002-3", "Parque Industrial, Rosario", "importaciones@mlitoral.test", "341 400 0000"])
        w.writerow(["Agroinsumos Pampa S.A.", "30-00000003-1", "Av. San Martín 980, Junín", "admin@agropampa.test", "236 400 0000"])
        w.writerow(["Distribuidora Norte S.R.L.", "30-00000005-8", "Ruta 34 km 5, Salta", "info@dnorte.test", "387 400 0000"])
