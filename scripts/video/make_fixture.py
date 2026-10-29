import sys
from openpyxl import Workbook
wb = Workbook(); ws = wb.active; ws.title = "Items"
ws.append(["PIEZA","DESCRIPCION","ORIGEN","CANTIDAD","VALOR UNITARIO","PESO UNITARIO"])
ws.append(["84713012","Notebook 14'' Core i5 8GB RAM 256GB SSD","CN",40,420.00,1.50])
ws.append(["84713012","Notebook 15.6'' Core i7 16GB RAM 512GB SSD","CN",25,690.00,1.90])
ws.append(["84713012","Notebook 17'' Core i7 16GB RAM 1TB SSD","CN",10,830.00,2.40])
wb.save(sys.argv[1])
