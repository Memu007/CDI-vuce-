/* Fuente: TABLA PAISES V.0 25082010.xlsx. Código oficial MARIA + denominación. */
(function () {
    'use strict';
    const CDI = window.CDI = window.CDI || {};

    const COUNTRIES = [{"code":"101","name":"BURKINA FASO"},{"code":"102","name":"ARGELIA"},{"code":"103","name":"BOTSWANA"},{"code":"104","name":"BURUNDI"},{"code":"105","name":"CAMERUN"},{"code":"107","name":"REP. CENTROAFRICANA."},{"code":"108","name":"CONGO"},{"code":"109","name":"REP.DEMOCRAT.DEL CONGO EX ZAIRE"},{"code":"110","name":"COSTA DE MARFIL"},{"code":"111","name":"CHAD"},{"code":"112","name":"BENIN"},{"code":"113","name":"EGIPTO"},{"code":"115","name":"GABON"},{"code":"116","name":"GAMBIA"},{"code":"117","name":"GHANA"},{"code":"118","name":"GUINEA"},{"code":"119","name":"GUINEA ECUATORIAL"},{"code":"120","name":"KENYA"},{"code":"121","name":"LESOTHO"},{"code":"122","name":"LIBERIA"},{"code":"123","name":"LIBIA"},{"code":"124","name":"MADAGASCAR"},{"code":"125","name":"MALAWI"},{"code":"126","name":"MALI"},{"code":"127","name":"MARRUECOS"},{"code":"128","name":"MAURICIO,ISLAS"},{"code":"129","name":"MAURITANIA"},{"code":"130","name":"NIGER"},{"code":"131","name":"NIGERIA"},{"code":"132","name":"ZIMBABWE"},{"code":"133","name":"RWANDA"},{"code":"134","name":"SENEGAL"},{"code":"135","name":"SIERRA LEONA"},{"code":"136","name":"SOMALIA"},{"code":"137","name":"SWAZILANDIA"},{"code":"138","name":"SUDAN"},{"code":"139","name":"TANZANIA"},{"code":"140","name":"TOGO"},{"code":"141","name":"TUNEZ"},{"code":"142","name":"UGANDA"},{"code":"143","name":"REPUBLICA DE SUDAFRICA"},{"code":"144","name":"ZAMBIA"},{"code":"145","name":"TERRIT.VINCULADOS AL R UNIDO"},{"code":"146","name":"TERRIT.VINCULADOS A ESPAÑA"},{"code":"147","name":"TERRIT.VINCULADOS A FRANCIA"},{"code":"148","name":"TERRIT.VINCULADOS A PORTUGAL"},{"code":"149","name":"ANGOLA"},{"code":"150","name":"CABO VERDE"},{"code":"151","name":"MOZAMBIQUE"},{"code":"152","name":"SEYCHELLES"},{"code":"153","name":"DJIBOUTI"},{"code":"155","name":"COMORAS"},{"code":"156","name":"GUINEA BISSAU"},{"code":"157","name":"STO.TOME Y PRINCIPE"},{"code":"158","name":"NAMIBIA"},{"code":"159","name":"SUDAFRICA"},{"code":"160","name":"ERITREA"},{"code":"161","name":"ETIOPIA"},{"code":"197","name":"RESTO (AFRICA)"},{"code":"198","name":"INDETERMINADO (AFRICA)"},{"code":"200","name":"ARGENTINA"},{"code":"201","name":"BARBADOS"},{"code":"202","name":"BOLIVIA"},{"code":"203","name":"BRASIL"},{"code":"204","name":"CANADA"},{"code":"205","name":"COLOMBIA"},{"code":"206","name":"COSTA RICA"},{"code":"207","name":"CUBA"},{"code":"208","name":"CHILE"},{"code":"209","name":"DOMINICANA,REP."},{"code":"210","name":"ECUADOR"},{"code":"211","name":"EL SALVADOR"},{"code":"212","name":"ESTADOS UNIDOS"},{"code":"213","name":"GUATEMALA"},{"code":"214","name":"GUYANA"},{"code":"215","name":"HAITI"},{"code":"216","name":"HONDURAS"},{"code":"217","name":"JAMAICA"},{"code":"218","name":"MEXICO"},{"code":"219","name":"NICARAGUA"},{"code":"220","name":"PANAMA"},{"code":"221","name":"PARAGUAY"},{"code":"222","name":"PERU"},{"code":"223","name":"PUERTO RICO"},{"code":"224","name":"TRINIDAD Y -TOBAGO"},{"code":"225","name":"URUGUAY"},{"code":"226","name":"VENEZUELA"},{"code":"227","name":"TERRIT.VINCULADO AL R.UNIDO"},{"code":"228","name":"TER.VINCULADOS A DINAMARCA"},{"code":"229","name":"TERRIT.VINCULADOS A FRANCIA AMERIC."},{"code":"230","name":"TERRIT. HOLANDESES"},{"code":"231","name":"TER.VINCULADOS A ESTADOS UNIDOS"},{"code":"232","name":"SURINAME"},{"code":"233","name":"DOMINICA"},{"code":"234","name":"SANTA LUCIA"},{"code":"235","name":"SAN VICENTE Y LAS GRANADINS"},{"code":"236","name":"BELICE"},{"code":"237","name":"ANTIGUA Y BARBUDA"},{"code":"238","name":"S.CRISTOBAL Y NEVIS"},{"code":"239","name":"BAHAMAS"},{"code":"240","name":"GRANADA"},{"code":"241","name":"ANTILLAS HOLANDESAS"},{"code":"242","name":"ARUBA"},{"code":"250","name":"TIERRA DEL FUEGO"},{"code":"251","name":"ZF LA PLATA"},{"code":"252","name":"ZF JUSTO DARACT"},{"code":"253","name":"ZF RIO GALLEGOS"},{"code":"254","name":"ISLAS MALVINAS"},{"code":"255","name":"ZF TUCUMAN"},{"code":"256","name":"ZF CORDOBA"},{"code":"257","name":"ZF MENDOZA"},{"code":"258","name":"ZF GENERAL PICO"},{"code":"259","name":"ZF COMODORO RIVADAVIA"},{"code":"260","name":"ZF IQUIQUE"},{"code":"261","name":"ZF PUNTA ARENAS"},{"code":"262","name":"ZF SALTA"},{"code":"263","name":"ZF PASO DE LOS LIBRES"},{"code":"264","name":"ZF PUERTO IGUAZU"},{"code":"265","name":"SECTOR ANTARTICO ARG."},{"code":"270","name":"ZF COLON"},{"code":"271","name":"ZF WINNER (STA. C.DE LA SIERRA"},{"code":"280","name":"ZF COLONIA"},{"code":"281","name":"ZF FLORIDA"},{"code":"282","name":"ZF LIBERTAD"},{"code":"283","name":"ZF ZONAMERICA"},{"code":"284","name":"ZF NUEVA HELVECIA"},{"code":"285","name":"ZF NUEVA PALMIRA"},{"code":"286","name":"ZF RIO NEGRO"},{"code":"287","name":"ZF RIVERA"},{"code":"288","name":"ZF SAN JOSE"},{"code":"291","name":"ZF MANAOS"},{"code":"295","name":"MAR ARG ZONA ECO.EX"},{"code":"296","name":"RIOS ARG NAVEG INTER"},{"code":"297","name":"RESTO AMERICA"},{"code":"298","name":"INDETERMINADO.(AMERICA)"},{"code":"301","name":"AFGANISTAN"},{"code":"302","name":"ARABIA SAUDITA"},{"code":"303","name":"BAHREIN"},{"code":"304","name":"MYANMAR(EX-BIRMANIA)"},{"code":"305","name":"BUTAN"},{"code":"306","name":"CAMBODYA(EX-KAMPUCHE"},{"code":"307","name":"SRI LANKA"},{"code":"308","name":"COREA DEMOCRATICA"},{"code":"309","name":"COREA REPUBLICANA"},{"code":"310","name":"CHINA"},{"code":"311","name":"CHIPRE"},{"code":"312","name":"FILIPINAS"},{"code":"313","name":"TAIWAN"},{"code":"314","name":"GAZA"},{"code":"315","name":"INDIA"},{"code":"316","name":"INDONESIA"},{"code":"317","name":"IRAK"},{"code":"318","name":"IRAN"},{"code":"319","name":"ISRAEL"},{"code":"320","name":"JAPON"},{"code":"321","name":"JORDANIA"},{"code":"322","name":"QATAR"},{"code":"323","name":"KUWAIT"},{"code":"324","name":"LAOS"},{"code":"325","name":"LIBANO"},{"code":"326","name":"MALASIA"},{"code":"327","name":"MALDIVAS ISLAS"},{"code":"328","name":"OMAN"},{"code":"329","name":"MONGOLIA"},{"code":"330","name":"NEPAL"},{"code":"331","name":"EMIRATOS ARABES,UNID"},{"code":"332","name":"PAKISTAN"},{"code":"333","name":"SINGAPUR"},{"code":"334","name":"SIRIA"},{"code":"335","name":"THAILANDIA"},{"code":"336","name":"TURQUIA"},{"code":"337","name":"VIETNAM"},{"code":"341","name":"HONG KONG"},{"code":"344","name":"MACAO"},{"code":"345","name":"BANGLADESH"},{"code":"346","name":"BRUNEI"},{"code":"348","name":"REPUBLICA DE YEMEN"},{"code":"349","name":"ARMENIA"},{"code":"350","name":"AZERBAIJAN"},{"code":"351","name":"GEORGIA"},{"code":"352","name":"KAZAJSTAN"},{"code":"353","name":"KIRGUIZISTAN"},{"code":"354","name":"TAYIKISTAN"},{"code":"355","name":"TURKMENISTAN"},{"code":"356","name":"UZBEKISTAN"},{"code":"357","name":"TERR. AU. PALESTINOS"},{"code":"358","name":"TIMOR ORIENTAL"},{"code":"397","name":"RESTO DE ASIA"},{"code":"398","name":"INDET.(ASIA)"},{"code":"401","name":"ALBANIA"},{"code":"402","name":"ALEMANIA FEDERAL"},{"code":"403","name":"ALEMANIA ORIENTAL"},{"code":"404","name":"ANDORRA"},{"code":"405","name":"AUSTRIA"},{"code":"406","name":"BELGICA"},{"code":"407","name":"BULGARIA"},{"code":"408","name":"CHECOSLOVAQUIA"},{"code":"409","name":"DINAMARCA"},{"code":"410","name":"ESPAÑA"},{"code":"411","name":"FINLANDIA"},{"code":"412","name":"FRANCIA"},{"code":"413","name":"GRECIA"},{"code":"414","name":"HUNGRIA"},{"code":"415","name":"IRLANDA"},{"code":"416","name":"ISLANDIA"},{"code":"417","name":"ITALIA"},{"code":"418","name":"LIECHTENSTEIN"},{"code":"419","name":"LUXEMBURGO"},{"code":"420","name":"MALTA"},{"code":"421","name":"MONACO"},{"code":"422","name":"NORUEGA"},{"code":"423","name":"PAISES BAJOS"},{"code":"424","name":"POLONIA"},{"code":"425","name":"PORTUGAL"},{"code":"426","name":"REINO UNIDO"},{"code":"427","name":"RUMANIA"},{"code":"428","name":"SAN MARINO"},{"code":"429","name":"SUECIA"},{"code":"430","name":"SUIZA"},{"code":"431","name":"VATICANO(SANTA SEDE)"},{"code":"432","name":"YUGOSLAVIA"},{"code":"433","name":"POS.BRIT.(EUROPA)"},{"code":"435","name":"CHIPRE"},{"code":"436","name":"TURQUIA"},{"code":"438","name":"ALEMANIA,REP.FED."},{"code":"439","name":"BIELORRUSIA"},{"code":"440","name":"ESTONIA"},{"code":"441","name":"LETONIA"},{"code":"442","name":"LITUANIA"},{"code":"443","name":"MOLDAVIA"},{"code":"444","name":"RUSIA"},{"code":"445","name":"UCRANIA"},{"code":"446","name":"BOSNIA HERZEGOVINA"},{"code":"447","name":"CROACIA"},{"code":"448","name":"ESLOVAQUIA"},{"code":"449","name":"ESLOVENIA"},{"code":"450","name":"MACEDONIA"},{"code":"451","name":"REP. CHECA"},{"code":"452","name":"FED. SER Y MONT YOGOE"},{"code":"453","name":"MONTENEGRO"},{"code":"454","name":"SERBIA"},{"code":"497","name":"RESTO EUROPA"},{"code":"498","name":"INDET.(EUROPA)"},{"code":"501","name":"AUSTRALIA"},{"code":"503","name":"NAURU"},{"code":"504","name":"NUEVA ZELANDIA"},{"code":"505","name":"VANATU"},{"code":"506","name":"SAMOA OCCIDENTAL"},{"code":"507","name":"TERRITORIO VINCULADOS A AUSTRALIA"},{"code":"508","name":"TERRITORIOS VINCULADOS AL R. UNIDO"},{"code":"509","name":"TERRITORIOS VINCULADOS A FRANCIA"},{"code":"510","name":"TER VINCULADOS A NUEVA. ZELANDA"},{"code":"511","name":"TER. VINCULADOS A ESTADOS UNIDOS"},{"code":"512","name":"FIJI, ISLAS"},{"code":"513","name":"PAPUA NUEVA GUINEA"},{"code":"514","name":"KIRIBATI, ISLAS"},{"code":"515","name":"MICRONESIA,EST.FEDER"},{"code":"516","name":"PALAU"},{"code":"517","name":"TUVALU"},{"code":"518","name":"SALOMON,ISLAS"},{"code":"519","name":"TONGA"},{"code":"520","name":"MARSHALL,ISLAS"},{"code":"521","name":"MARIANAS,ISLAS"},{"code":"597","name":"RESTO OCEANIA"},{"code":"598","name":"INDET.(OCEANIA)"},{"code":"601","name":"URSS"},{"code":"652","name":"ANGUILA (TERRITORIO NO AUTONOMO DEL R. UNIDO)"},{"code":"659","name":"ANTILLAS HOLANDESAS (TERRITORIO DE PAISES BAJOS)"},{"code":"653","name":"ARUBA (TERRITORIO DE PAISES BAJOS)"},{"code":"662","name":"ASCENCION"},{"code":"663","name":"BERMUDAS (TERRITORIO NO AUTONOMO DEL R UNIDO)"},{"code":"664","name":"CAMPIONE DITALIA"},{"code":"665","name":"COLONIA DE GIBRALTAR"},{"code":"666","name":"GROENLANDIA"},{"code":"667","name":"GUAM (TERRITORIO NO AUTONOMO DE LOS ESTADO UNIDOS"},{"code":"668","name":"HONG KONG (TERRITORIO DE CHINA)"},{"code":"669","name":"ISLAS AZORES"},{"code":"670","name":"ISLAS DEL CANAL (GUERNESEY, JERSEY, ALDERNEY,G.STARK, L.SARK, ETC)"},{"code":"671","name":"ISLAS CAIMAN (TERRITORIO NO AUTONOMO DE R UNIDO)"},{"code":"672","name":"ISLA CHRISTMAS"},{"code":"673","name":"ISLA DE COCOS O KEELING"},{"code":"654","name":"ISLA DE COOK (TERRITORIO AUTONOMO ASOCIADO A NUEVA ZELANDA)"},{"code":"676","name":"ISLA DE MAN (TERRITORIO DEL REINO UNIDO)"},{"code":"677","name":"ISLA DE NORFOLK (TERRITORIO DEL R UNIDO)"},{"code":"678","name":"ISALAS TURKAS Y CAICOS (TERRITORIO NO AUTONOMO DEL REINO UNIDO)"},{"code":"679","name":"ISLAS PACIFICO"},{"code":"680","name":"ISLAS DE SAN PEDRO Y MIGUELON"},{"code":"681","name":"ISLA QESHM"},{"code":"682","name":"ISLAS VIRGENES BRITANICAS (TERRITORIO NO AUTONOMO DEL REINO UNIDO)"},{"code":"683","name":"ISLAS VIRGENES DE ESTADOS UNIDOS DE AMERICA"},{"code":"684","name":"LABUAM"},{"code":"685","name":"MADEIRA (TERRITORIO DE PORTUGAL)"},{"code":"686","name":"MONSERRAT (TERRITORIO NO AUTONOMO DEL REINO UNIDO)"},{"code":"687","name":"NIUE"},{"code":"655","name":"PATAU"},{"code":"690","name":"PITCAIRN"},{"code":"656","name":"POLINESI FRANCESA (TERRITORIO DE ULTRAMAR DE FRANCIA)"},{"code":"693","name":"REGIMEN APLICABLE A LAS SA FINANCIERAS (LEY 11073 DE LA ROU)"},{"code":"694","name":"SANTA ELENA"},{"code":"695","name":"SAMAO AMERICANA (TERRITORIO NO AUTONOMO DE LOS ESTADOS UNIDOS)"},{"code":"696","name":"ARCHIPIELAGO DE SVBALBARD"},{"code":"697","name":"TRISTAN DACUNHA"},{"code":"698","name":"TRIESTE (ITALIA)"},{"code":"699","name":"TOKELAU"},{"code":"700","name":"ZONA LIBRE DE OSTRAVA (CIUDAD DE LA ATIGUA CHECOSLOVAQUIA)"},{"code":"997","name":"RESTO CONTINENTE"},{"code":"998","name":"INDET.(CONTINENTE)"},{"code":"999","name":"OTROS PAISES"}];
    const ALIASES = {"BURKINA FASO":"101","ARGELIA":"102","BOTSWANA":"103","BURUNDI":"104","CAMERUN":"105","REP CENTROAFRICANA":"107","CONGO":"108","REP DEMOCRAT DEL CONGO EX ZAIRE":"109","COSTA DE MARFIL":"110","CHAD":"111","BENIN":"112","EGIPTO":"113","GABON":"115","GAMBIA":"116","GHANA":"117","GUINEA":"118","GUINEA ECUATORIAL":"119","KENYA":"120","LESOTHO":"121","LIBERIA":"122","LIBIA":"123","MADAGASCAR":"124","MALAWI":"125","MALI":"126","MARRUECOS":"127","MAURICIO,ISLAS":"128","MAURITANIA":"129","NIGER":"130","NIGERIA":"131","ZIMBABWE":"132","RWANDA":"133","SENEGAL":"134","SIERRA LEONA":"135","SOMALIA":"136","SWAZILANDIA":"137","SUDAN":"138","TANZANIA":"139","TOGO":"140","TUNEZ":"141","UGANDA":"142","REPUBLICA DE SUDAFRICA":"143","ZAMBIA":"144","TERRIT VINCULADOS AL R UNIDO":"145","TERRIT VINCULADOS A ESPANA":"146","TERRIT VINCULADOS A FRANCIA":"147","TERRIT VINCULADOS A PORTUGAL":"148","ANGOLA":"149","CABO VERDE":"150","MOZAMBIQUE":"151","SEYCHELLES":"152","DJIBOUTI":"153","COMORAS":"155","GUINEA BISSAU":"156","STO TOME Y PRINCIPE":"157","NAMIBIA":"158","SUDAFRICA":"159","ERITREA":"160","ETIOPIA":"161","RESTO (AFRICA)":"197","INDETERMINADO (AFRICA)":"198","ARGENTINA":"200","BARBADOS":"201","BOLIVIA":"202","BRASIL":"203","CANADA":"204","COLOMBIA":"205","COSTA RICA":"206","CUBA":"207","CHILE":"208","DOMINICANA,REP":"209","ECUADOR":"210","EL SALVADOR":"211","ESTADOS UNIDOS":"212","GUATEMALA":"213","GUYANA":"214","HAITI":"215","HONDURAS":"216","JAMAICA":"217","MEXICO":"218","NICARAGUA":"219","PANAMA":"220","PARAGUAY":"221","PERU":"222","PUERTO RICO":"223","TRINIDAD Y -TOBAGO":"224","TRINIDAD Y TOBAGO":"224","URUGUAY":"225","VENEZUELA":"226","TERRIT VINCULADO AL R UNIDO":"227","TER VINCULADOS A DINAMARCA":"228","TERRIT VINCULADOS A FRANCIA AMERIC":"229","TERRIT HOLANDESES":"230","TER VINCULADOS A ESTADOS UNIDOS":"231","SURINAME":"232","DOMINICA":"233","SANTA LUCIA":"234","SAN VICENTE Y LAS GRANADINS":"235","SAN VICENTE Y LAS GRANADINAS":"235","BELICE":"236","ANTIGUA Y BARBUDA":"237","S CRISTOBAL Y NEVIS":"238","BAHAMAS":"239","GRANADA":"240","ANTILLAS HOLANDESAS":"241","ARUBA":"242","TIERRA DEL FUEGO":"250","ZF LA PLATA":"251","ZF JUSTO DARACT":"252","ZF RIO GALLEGOS":"253","ISLAS MALVINAS":"254","ZF TUCUMAN":"255","ZF CORDOBA":"256","ZF MENDOZA":"257","ZF GENERAL PICO":"258","ZF COMODORO RIVADAVIA":"259","ZF IQUIQUE":"260","ZF PUNTA ARENAS":"261","ZF SALTA":"262","ZF PASO DE LOS LIBRES":"263","ZF PUERTO IGUAZU":"264","SECTOR ANTARTICO ARG":"265","ZF COLON":"270","ZF WINNER (STA C DE LA SIERRA":"271","ZF COLONIA":"280","ZF FLORIDA":"281","ZF LIBERTAD":"282","ZF ZONAMERICA":"283","ZF NUEVA HELVECIA":"284","ZF NUEVA PALMIRA":"285","ZF RIO NEGRO":"286","ZF RIVERA":"287","ZF SAN JOSE":"288","ZF MANAOS":"291","MAR ARG ZONA ECO EX":"295","RIOS ARG NAVEG INTER":"296","RESTO AMERICA":"297","INDETERMINADO (AMERICA)":"298","AFGANISTAN":"301","ARABIA SAUDITA":"302","BAHREIN":"303","MYANMAR(EX-BIRMANIA)":"304","BUTAN":"305","CAMBODYA(EX-KAMPUCHE":"306","SRI LANKA":"307","COREA DEMOCRATICA":"308","COREA REPUBLICANA":"309","CHINA":"310","CHIPRE":"311","FILIPINAS":"312","TAIWAN":"313","GAZA":"314","INDIA":"315","INDONESIA":"316","IRAK":"317","IRAN":"318","ISRAEL":"319","JAPON":"320","JORDANIA":"321","QATAR":"322","KUWAIT":"323","LAOS":"324","LIBANO":"325","MALASIA":"326","MALDIVAS ISLAS":"327","OMAN":"328","MONGOLIA":"329","NEPAL":"330","EMIRATOS ARABES,UNID":"331","PAKISTAN":"332","SINGAPUR":"333","SIRIA":"334","THAILANDIA":"335","TURQUIA":"336","VIETNAM":"337","HONG KONG":"341","REG ADM ESP DE CHINA":"341","MACAO":"344","MACAO(REG ADM ESPEC)":"344","BANGLADESH":"345","BRUNEI":"346","REPUBLICA DE YEMEN":"348","ARMENIA":"349","AZERBAIJAN":"350","GEORGIA":"351","KAZAJSTAN":"352","KIRGUIZISTAN":"353","TAYIKISTAN":"354","TURKMENISTAN":"355","UZBEKISTAN":"356","TERR AU PALESTINOS":"357","TIMOR ORIENTAL":"358","RESTO DE ASIA":"397","INDET (ASIA)":"398","ALBANIA":"401","ALEMANIA FEDERAL":"402","ALEMANIA ORIENTAL":"403","ANDORRA":"404","AUSTRIA":"405","BELGICA":"406","BULGARIA":"407","CHECOSLOVAQUIA":"408","DINAMARCA":"409","ESPANA":"410","FINLANDIA":"411","FRANCIA":"412","GRECIA":"413","HUNGRIA":"414","IRLANDA":"415","ISLANDIA":"416","ITALIA":"417","LIECHTENSTEIN":"418","LUXEMBURGO":"419","MALTA":"420","MONACO":"421","NORUEGA":"422","PAISES BAJOS":"423","POLONIA":"424","PORTUGAL":"425","REINO UNIDO":"426","RUMANIA":"427","SAN MARINO":"428","SUECIA":"429","SUIZA":"430","VATICANO(SANTA SEDE)":"431","YUGOSLAVIA":"432","POS BRIT (EUROPA)":"433","HOLANDA":"423","ALEMANIA,REP FED":"438","BIELORRUSIA":"439","ESTONIA":"440","LETONIA":"441","LITUANIA":"442","MOLDAVIA":"443","RUSIA":"444","UCRANIA":"445","BOSNIA HERZEGOVINA":"446","CROACIA":"447","ESLOVAQUIA":"448","ESLOVENIA":"449","MACEDONIA":"450","REP CHECA":"451","FED SER Y MONT YOGOE":"452","MONTENEGRO":"453","SERBIA":"454","RESTO EUROPA":"497","INDET (EUROPA)":"498","AUSTRALIA":"501","NAURU":"503","NUEVA ZELANDIA":"504","VANATU":"505","SAMOA OCCIDENTAL":"506","TERRITORIO VINCULADOS A AUSTRALIA":"507","TERRITORIOS VINCULADOS AL R UNIDO":"508","TERRITORIOS VINCULADOS A FRANCIA":"509","TER VINCULADOS A NUEVA ZELANDA":"510","FIJI, ISLAS":"512","PAPUA NUEVA GUINEA":"513","KIRIBATI, ISLAS":"514","MICRONESIA,EST FEDER":"515","PALAU":"516","TUVALU":"517","SALOMON,ISLAS":"518","TONGA":"519","MARSHALL,ISLAS":"520","MARIANAS,ISLAS":"521","RESTO OCEANIA":"597","INDET (OCEANIA)":"598","URSS":"601","ANGUILA (TERRITORIO NO AUTONOMO DEL R UNIDO)":"652","ANTILLAS HOLANDESAS (TERRITORIO DE PAISES BAJOS)":"659","ARUBA (TERRITORIO DE PAISES BAJOS)":"653","ASCENCION":"662","BERMUDAS (TERRITORIO NO AUTONOMO DEL R UNIDO)":"663","CAMPIONE DITALIA":"664","COLONIA DE GIBRALTAR":"665","GROENLANDIA":"666","GUAM (TERRITORIO NO AUTONOMO DE LOS ESTADO UNIDOS":"667","HONG KONG (TERRITORIO DE CHINA)":"668","ISLAS AZORES":"669","ISLAS DEL CANAL (GUERNESEY, JERSEY, ALDERNEY,G STARK, L SARK, ETC)":"670","ISLAS CAIMAN (TERRITORIO NO AUTONOMO DE R UNIDO)":"671","ISLA CHRISTMAS":"672","ISLA DE COCOS O KEELING":"673","ISLA DE COOK (TERRITORIO AUTONOMO ASOCIADO A NUEVA ZELANDA)":"654","ISLA DE MAN (TERRITORIO DEL REINO UNIDO)":"676","ISLA DE NORFOLK (TERRITORIO DEL R UNIDO)":"677","ISALAS TURKAS Y CAICOS (TERRITORIO NO AUTONOMO DEL REINO UNIDO)":"678","ISLAS PACIFICO":"679","ISLAS DE SAN PEDRO Y MIGUELON":"680","ISLA QESHM":"681","ISLAS VIRGENES BRITANICAS (TERRITORIO NO AUTONOMO DEL REINO UNIDO)":"682","ISLAS VIRGENES DE ESTADOS UNIDOS DE AMERICA":"683","LABUAM":"684","MADEIRA (TERRITORIO DE PORTUGAL)":"685","MONSERRAT (TERRITORIO NO AUTONOMO DEL REINO UNIDO)":"686","NIUE":"687","PATAU":"655","PITCAIRN":"690","POLINESI FRANCESA (TERRITORIO DE ULTRAMAR DE FRANCIA)":"656","REGIMEN APLICABLE A LAS SA FINANCIERAS (LEY 11073 DE LA ROU)":"693","SANTA ELENA":"694","SAMAO AMERICANA (TERRITORIO NO AUTONOMO DE LOS ESTADOS UNIDOS)":"695","ARCHIPIELAGO DE SVBALBARD":"696","TRISTAN DACUNHA":"697","TRIESTE (ITALIA)":"698","TOKELAU":"699","ZONA LIBRE DE OSTRAVA (CIUDAD DE LA ATIGUA CHECOSLOVAQUIA)":"700","RESTO CONTINENTE":"997","INDET (CONTINENTE)":"998","OTROS PAISES":"999","BF":"101","DZ":"102","BW":"103","BI":"104","CM":"105","CF":"107","CG":"108","CD":"109","CI":"110","TD":"111","BJ":"112","EG":"113","GA":"115","GM":"116","GH":"117","GN":"118","GQ":"119","KE":"120","LS":"121","LR":"122","LY":"123","MG":"124","MW":"125","ML":"126","MA":"127","MU":"128","MR":"129","NE":"130","NG":"131","ZW":"132","RW":"133","SN":"134","SL":"135","SO":"136","SZ":"137","SD":"138","TZ":"139","TG":"140","TN":"141","UG":"142","ZM":"144","AO":"149","MZ":"151","SC":"152","DJ":"153","KM":"155","GW":"156","ST":"157","NA":"158","ZA":"159","ER":"160","ET":"161","AR":"200","BB":"201","BO":"202","BR":"203","CA":"204","CO":"205","CR":"206","CU":"207","CL":"208","DO":"209","EC":"210","SV":"211","US":"212","USA":"212","EEUU":"212","GT":"213","GY":"214","HT":"215","HN":"216","JM":"217","MX":"218","NI":"219","PA":"220","PY":"221","PE":"222","TT":"224","UY":"225","VE":"226","SR":"232","DM":"233","LC":"234","VC":"235","BZ":"236","AG":"237","KN":"238","BS":"239","GD":"240","AF":"301","SA":"302","BH":"303","MM":"304","BT":"305","KH":"306","LK":"307","KP":"308","KR":"309","CN":"310","CY":"311","PH":"312","TW":"313","IN":"315","ID":"316","IQ":"317","IR":"318","IL":"319","JP":"320","JO":"321","QA":"322","KW":"323","LA":"324","LB":"325","MY":"326","MV":"327","OM":"328","MN":"329","NP":"330","AE":"331","PK":"332","SG":"333","SY":"334","TH":"335","TR":"336","VN":"337","HK":"341","MO":"344","BD":"345","BN":"346","YE":"348","AM":"349","AZ":"350","GE":"351","KZ":"352","KG":"353","TJ":"354","TM":"355","UZ":"356","AL":"401","AD":"404","AT":"405","BE":"406","BG":"407","DK":"409","ES":"410","FI":"411","FR":"412","GR":"413","HU":"414","IE":"415","IS":"416","IT":"417","LI":"418","LU":"419","MT":"420","MC":"421","NO":"422","NL":"423","PL":"424","PT":"425","GB":"426","UK":"426","RO":"427","SM":"428","SE":"429","CH":"430","DE":"438","BY":"439","EE":"440","LV":"441","LT":"442","MD":"443","RU":"444","UA":"445","BA":"446","HR":"447","SK":"448","SI":"449","MK":"450","CZ":"451","ME":"453","RS":"454","AU":"501","NR":"503","NZ":"504","VU":"505","WS":"506","FJ":"512","PG":"513","KI":"514","FM":"515","PW":"516","TV":"517","SB":"518","TO":"519","MH":"520","MP":"521","BRAZIL":"203","GERMANY":"438","JAPAN":"320","SPAIN":"410","FRANCE":"412","ITALY":"417","ENGLAND":"426","GREAT BRITAIN":"426","UNITED KINGDOM":"426","KOREA":"309","SOUTH KOREA":"309","NORTH KOREA":"308","CHINA (MAINLAND)":"310","MAINLAND CHINA":"310","P R CHINA":"310","PR CHINA":"310","RP CHINA":"310","REPUBLICA POPULAR CHINA":"310","ESTADOS UNIDOS DE AMERICA":"212","UNITED STATES OF AMERICA":"212","EE UU":"212","ALEMANIA":"438","TAILANDIA":"335","THAILAND":"335","MALAYSIA":"326","COREA":"309","COREA DEL SUR":"309","COREA DEL NORTE":"308","AFG":"301","AGO":"149","ALB":"401","AND":"404","ARE":"331","ARG":"200","ARM":"349","ATG":"237","AUS":"501","AUT":"405","AZE":"350","BDI":"104","BEL":"406","BEN":"112","BFA":"101","BGD":"345","BGR":"407","BHR":"303","BHS":"239","BIH":"446","BLR":"439","BLZ":"236","BOL":"202","BRA":"203","BRB":"201","BRN":"346","BTN":"305","BWA":"103","CAF":"107","CAN":"204","CHE":"430","CHL":"208","CHN":"310","CIV":"110","CMR":"105","COD":"109","COG":"108","COL":"205","COM":"155","CRI":"206","CUB":"207","CYP":"311","CZE":"451","DEU":"438","DJI":"153","DMA":"233","DNK":"409","DOM":"209","DZA":"102","ECU":"210","EGY":"113","ERI":"160","ESP":"410","EST":"440","ETH":"161","FIN":"411","FJI":"512","FRA":"412","FSM":"515","GAB":"115","GBR":"426","GEO":"351","GHA":"117","GIN":"118","GMB":"116","GNB":"156","GNQ":"119","GRC":"413","GRD":"240","GTM":"213","GUY":"214","HKG":"341","HND":"216","HRV":"447","HTI":"215","HUN":"414","IDN":"316","IND":"315","IRL":"415","IRN":"318","IRQ":"317","ISL":"416","ISR":"319","ITA":"417","JAM":"217","JOR":"321","JPN":"320","KAZ":"352","KEN":"120","KGZ":"353","KHM":"306","KIR":"514","KNA":"238","KOR":"309","KWT":"323","LAO":"324","LBN":"325","LBR":"122","LBY":"123","LCA":"234","LIE":"418","LKA":"307","LSO":"121","LTU":"442","LUX":"419","LVA":"441","MAC":"344","MAR":"127","MCO":"421","MDA":"443","MDG":"124","MDV":"327","MEX":"218","MHL":"520","MKD":"450","MLI":"126","MLT":"420","MMR":"304","MNE":"453","MNG":"329","MNP":"521","MOZ":"151","MRT":"129","MUS":"128","MWI":"125","MYS":"326","NAM":"158","NER":"130","NGA":"131","NIC":"219","NLD":"423","NOR":"422","NPL":"330","NRU":"503","NZL":"504","OMN":"328","PAK":"332","PAN":"220","PER":"222","PHL":"312","PLW":"516","PNG":"513","POL":"424","PRK":"308","PRT":"425","PRY":"221","QAT":"322","ROU":"427","RUS":"444","RWA":"133","SAU":"302","SDN":"138","SEN":"134","SGP":"333","SLB":"518","SLE":"135","SLV":"211","SMR":"428","SOM":"136","SRB":"454","STP":"157","SUR":"232","SVK":"448","SVN":"449","SWE":"429","SWZ":"137","SYC":"152","SYR":"334","TCD":"111","TGO":"140","THA":"335","TJK":"354","TKM":"355","TON":"519","TTO":"224","TUN":"141","TUR":"336","TUV":"517","TWN":"313","TZA":"139","UGA":"142","UKR":"445","URY":"225","UZB":"356","VCT":"235","VEN":"226","VNM":"337","VUT":"505","WSM":"506","YEM":"348","ZAF":"159","ZMB":"144","ZWE":"132"};
    // Generado por scripts/datos/generar_nombres_paises.py (pycountry 26.2.16): no editar a mano.
    const NOMBRES = {
        "101": {"en": ["Burkina Faso"], "es": ["Burquina Faso"]},
        "102": {"en": ["Algeria", "People's Democratic Republic of Algeria"], "es": ["Algeria", "República Democrática Popular de Argelia"]},
        "103": {"en": ["Botswana", "Republic of Botswana"], "es": ["Botsuana", "República de Botsuana"]},
        "104": {"en": ["Burundi", "Republic of Burundi"], "es": ["Burundi", "República de Burundi"]},
        "105": {"en": ["Cameroon", "Republic of Cameroon"], "es": ["Camerún", "República del Camerún"]},
        "107": {"en": ["Central African Republic"], "es": ["República Centroafricana"]},
        "108": {"en": ["Congo", "Republic of the Congo"], "es": ["Congo", "República del Congo"]},
        "109": {"en": ["Congo, The Democratic Republic of the", "Democratic Republic of the Congo", "DR Congo"], "es": ["Congo, República Democrática del", "República Democrática del Congo"]},
        "110": {"en": ["Côte d'Ivoire", "Republic of Côte d'Ivoire", "Ivory Coast"], "es": ["Costa de Marfíl", "República de Costa de Marfíl", "Costa de Marfil"]},
        "111": {"en": ["Chad", "Republic of Chad"], "es": ["Chad", "República del Chad"]},
        "112": {"en": ["Benin", "Republic of Benin"], "es": ["Benín", "República de Benín"]},
        "113": {"en": ["Egypt", "Arab Republic of Egypt"], "es": ["Egipto", "República Árabe de Egipto"]},
        "115": {"en": ["Gabon", "Gabonese Republic"], "es": ["Gabón", "República Gabonesa"]},
        "116": {"en": ["Gambia", "Republic of the Gambia"], "es": ["Gambia", "República de Gambia"]},
        "117": {"en": ["Ghana", "Republic of Ghana"], "es": ["Ghana", "República de Ghana"]},
        "118": {"en": ["Guinea", "Republic of Guinea"], "es": ["Guinea", "República de Guinea"]},
        "119": {"en": ["Equatorial Guinea", "Republic of Equatorial Guinea"], "es": ["Guinea Ecuatorial", "República de Guinea Ecuatorial"]},
        "120": {"en": ["Kenya", "Republic of Kenya"], "es": ["Kenia", "República de Kenia"]},
        "121": {"en": ["Lesotho", "Kingdom of Lesotho"], "es": ["Lesoto", "Reino de Lesoto"]},
        "122": {"en": ["Liberia", "Republic of Liberia"], "es": ["Liberia", "República de Liberia"]},
        "123": {"en": ["Libya"], "es": ["Libia"]},
        "124": {"en": ["Madagascar", "Republic of Madagascar"], "es": ["Madagascar", "República de Madagascar"]},
        "125": {"en": ["Malawi", "Republic of Malawi"], "es": ["Malaui", "República de Malawi"]},
        "126": {"en": ["Mali", "Republic of Mali"], "es": ["Malí", "República de Mali"]},
        "127": {"en": ["Morocco", "Kingdom of Morocco"], "es": ["Marruecos", "Reino de Marruecos"]},
        "128": {"en": ["Mauritius", "Republic of Mauritius"], "es": ["Mauricio", "República de Mauricio"]},
        "129": {"en": ["Mauritania", "Islamic Republic of Mauritania"], "es": ["Mauritania", "República Islámica de Mauritania"]},
        "130": {"en": ["Niger", "Republic of the Niger"], "es": ["Niger", "República del Níger"]},
        "131": {"en": ["Nigeria", "Federal Republic of Nigeria"], "es": ["Nigeria", "República Federal de Nigeria"]},
        "132": {"en": ["Zimbabwe", "Republic of Zimbabwe"], "es": ["Zimbabue", "República de Zimbabue"]},
        "133": {"en": ["Rwanda", "Rwandese Republic"], "es": ["Ruanda", "República de Ruanda"]},
        "134": {"en": ["Senegal", "Republic of Senegal"], "es": ["Senegal", "República del Senegal"]},
        "135": {"en": ["Sierra Leone", "Republic of Sierra Leone"], "es": ["Sierra Leona", "República de Sierra Leona"]},
        "136": {"en": ["Somalia", "Federal Republic of Somalia"], "es": ["Somalia", "República Federal de Somalia"]},
        "137": {"en": ["Eswatini", "Kingdom of Eswatini", "Swaziland"], "es": ["Esuatini", "Reino de Esuatini", "Suazilandia"]},
        "138": {"en": ["Sudan", "Republic of the Sudan"], "es": ["Sudán", "República de Sudán"]},
        "139": {"en": ["Tanzania, United Republic of", "United Republic of Tanzania", "Tanzania"], "es": ["Tanzania, República unida de", "República Unida de Tanzania"]},
        "140": {"en": ["Togo", "Togolese Republic"], "es": ["Togo", "República Togolesa"]},
        "141": {"en": ["Tunisia", "Republic of Tunisia"], "es": ["Tunez", "República de Túnez"]},
        "142": {"en": ["Uganda", "Republic of Uganda"], "es": ["Uganda", "República de Uganda"]},
        "144": {"en": ["Zambia", "Republic of Zambia"], "es": ["Zambia", "República de Zambia"]},
        "149": {"en": ["Angola", "Republic of Angola"], "es": ["Angola", "República de Angola"]},
        "150": {"en": ["Cabo Verde", "Republic of Cabo Verde", "Cape Verde"], "es": ["Cabo Verde", "República de Cabo Verde"]},
        "151": {"en": ["Mozambique", "Republic of Mozambique"], "es": ["Mozambique", "República de Mozambique"]},
        "152": {"en": ["Seychelles", "Republic of Seychelles"], "es": ["Seychelles", "República de las Seychelles"]},
        "153": {"en": ["Djibouti", "Republic of Djibouti"], "es": ["Yibuti", "República de Yibuti"]},
        "155": {"en": ["Comoros", "Union of the Comoros"], "es": ["Comores, Islas", "Unión de las Comores"]},
        "156": {"en": ["Guinea-Bissau", "Republic of Guinea-Bissau"], "es": ["Guinea-Bisáu", "República de Guinea-Bissau"]},
        "157": {"en": ["Sao Tome and Principe", "Democratic Republic of Sao Tome and Principe"], "es": ["Santo Tomé y Príncipe", "República Democrática de Santo Tomé y Príncipe"]},
        "158": {"en": ["Namibia", "Republic of Namibia"], "es": ["Namibia", "República de Namibia"]},
        "159": {"en": ["South Africa"], "es": ["Sudáfrica"]},
        "160": {"en": ["Eritrea", "the State of Eritrea"], "es": ["Eritrea", "Estado de Eritrea"]},
        "161": {"en": ["Ethiopia", "Federal Democratic Republic of Ethiopia"], "es": ["Etiopía", "República Federal Democrática de Etiopía"]},
        "200": {"en": ["Argentina", "Argentine Republic"], "es": ["Argentina", "República Argentina"]},
        "201": {"en": ["Barbados"], "es": ["Barbados"]},
        "202": {"en": ["Bolivia, Plurinational State of", "Plurinational State of Bolivia", "Bolivia"], "es": ["Bolivia, Estado plurinacional de", "Estado plurinacional de Bolivia"]},
        "203": {"en": ["Brazil", "Federative Republic of Brazil"], "es": ["Brasil", "República Federativa de Brasil"]},
        "204": {"en": ["Canada"], "es": ["Canadá"]},
        "205": {"en": ["Colombia", "Republic of Colombia"], "es": ["Colombia", "República de Colombia"]},
        "206": {"en": ["Costa Rica", "Republic of Costa Rica"], "es": ["Costa Rica", "República de Costa Rica"]},
        "207": {"en": ["Cuba", "Republic of Cuba"], "es": ["Cuba", "República de Cuba"]},
        "208": {"en": ["Chile", "Republic of Chile"], "es": ["Chile", "República de Chile"]},
        "209": {"en": ["Dominican Republic"], "es": ["República Dominicana"]},
        "210": {"en": ["Ecuador", "Republic of Ecuador"], "es": ["Ecuador", "República del Ecuador"]},
        "211": {"en": ["El Salvador", "Republic of El Salvador"], "es": ["El Salvador", "República de El Salvador"]},
        "212": {"en": ["United States", "United States of America", "USA", "U.S.A."], "es": ["Estados Unidos", "Estados Unidos de América", "EE.UU.", "EEUU", "E.E.U.U.", "Estados Unidos de Norteamérica"]},
        "213": {"en": ["Guatemala", "Republic of Guatemala"], "es": ["Guatemala", "República de Guatemala"]},
        "214": {"en": ["Guyana", "Republic of Guyana"], "es": ["Guyana", "República de Guyana"]},
        "215": {"en": ["Haiti", "Republic of Haiti"], "es": ["Haití", "República de Haití"]},
        "216": {"en": ["Honduras", "Republic of Honduras"], "es": ["Honduras", "República de Honduras"]},
        "217": {"en": ["Jamaica"], "es": ["Jamaica"]},
        "218": {"en": ["Mexico", "United Mexican States"], "es": ["México", "Estados Unidos Mexicanos"]},
        "219": {"en": ["Nicaragua", "Republic of Nicaragua"], "es": ["Nicaragua", "República de Nicaragua"]},
        "220": {"en": ["Panama", "Republic of Panama"], "es": ["Panamá", "República de Panamá"]},
        "221": {"en": ["Paraguay", "Republic of Paraguay"], "es": ["Paraguay", "República del Paraguay"]},
        "222": {"en": ["Peru", "Republic of Peru"], "es": ["Perú", "República del Perú"]},
        "223": {"en": ["Puerto Rico"], "es": ["Puerto Rico"]},
        "224": {"en": ["Trinidad and Tobago", "Republic of Trinidad and Tobago"], "es": ["Trinidad y Tobago", "República de Trinidad y Tobago"]},
        "225": {"en": ["Uruguay", "Eastern Republic of Uruguay"], "es": ["Uruguay", "República Oriental del Uruguay"]},
        "226": {"en": ["Venezuela, Bolivarian Republic of", "Bolivarian Republic of Venezuela", "Venezuela"], "es": ["Venezuela, República Bolivariana de", "República Bolivariana de Venezuela"]},
        "232": {"en": ["Suriname", "Republic of Suriname"], "es": ["Surinám", "República de Surinam"]},
        "233": {"en": ["Dominica", "Commonwealth of Dominica"], "es": ["Dominica", "Commonwealth de Dominica"]},
        "234": {"en": ["Saint Lucia"], "es": ["Santa Lucía"]},
        "235": {"en": ["Saint Vincent and the Grenadines"], "es": ["San Vicente y las Granadinas"]},
        "236": {"en": ["Belize"], "es": ["Belice"]},
        "237": {"en": ["Antigua and Barbuda"], "es": ["Antigua y Barbuda"]},
        "238": {"en": ["Saint Kitts and Nevis"], "es": ["San Cristóbal y Nieves"]},
        "239": {"en": ["Bahamas", "Commonwealth of the Bahamas"], "es": ["Bahamas", "Commonwealth de las Bahamas"]},
        "240": {"en": ["Grenada"], "es": ["Granada"]},
        "241": {"en": ["Netherlands Antilles"], "es": ["Netherlands Antilles", "Antillas Neerlandesas"]},
        "242": {"en": ["Aruba"], "es": ["Aruba"]},
        "254": {"en": ["Falkland Islands (Malvinas)", "Falkland Islands"], "es": ["Islas Falkland (Malvinas)", "Islas Malvinas", "Malvinas"]},
        "301": {"en": ["Afghanistan", "Islamic Republic of Afghanistan"], "es": ["Afganistán", "República Islámica de Afganistán"]},
        "302": {"en": ["Saudi Arabia", "Kingdom of Saudi Arabia"], "es": ["Arabia Saudí", "Reino de Arabia Saudí", "Arabia Saudita"]},
        "303": {"en": ["Bahrain", "Kingdom of Bahrain"], "es": ["Baréin", "Reino de Baréin"]},
        "304": {"en": ["Myanmar", "Republic of Myanmar", "Burma"], "es": ["Birmania", "República de la Unión de Myanmar"]},
        "305": {"en": ["Bhutan", "Kingdom of Bhutan"], "es": ["Bután", "Reino de Bután"]},
        "306": {"en": ["Cambodia", "Kingdom of Cambodia"], "es": ["Camboya", "Reino de Camboya"]},
        "307": {"en": ["Sri Lanka", "Democratic Socialist Republic of Sri Lanka"], "es": ["Sri Lanka", "República Socialista Democrática de Sri Lanka"]},
        "308": {"en": ["Korea, Democratic People's Republic of", "Democratic People's Republic of Korea", "North Korea"], "es": ["Corea, República Democrática Popular de", "República Popular Democrática de Corea", "Corea del Norte"]},
        "309": {"en": ["Korea, Republic of", "South Korea", "Republic of Korea"], "es": ["Corea, República de", "República de Corea"]},
        "310": {"en": ["China", "People's Republic of China"], "es": ["China", "República Popular China"]},
        "311": {"en": ["Cyprus", "Republic of Cyprus"], "es": ["Chipre", "República de Chipre"]},
        "312": {"en": ["Philippines", "Republic of the Philippines"], "es": ["Filipinas", "República de Filipinas"]},
        "313": {"en": ["Taiwan, Province of China", "Taiwan"], "es": ["Taiwán, Provincia de China", "Taiwán"]},
        "315": {"en": ["India", "Republic of India"], "es": ["India", "República de la India"]},
        "316": {"en": ["Indonesia", "Republic of Indonesia"], "es": ["Indonesia", "República de Indonesia"]},
        "317": {"en": ["Iraq", "Republic of Iraq"], "es": ["Irak", "República de Irak"]},
        "318": {"en": ["Iran, Islamic Republic of", "Islamic Republic of Iran", "Iran"], "es": ["Irán, República islámica de", "República Islámica de Irán", "Irán"]},
        "319": {"en": ["Israel", "State of Israel"], "es": ["Israel", "Estado de Israel"]},
        "320": {"en": ["Japan"], "es": ["Japón"]},
        "321": {"en": ["Jordan", "Hashemite Kingdom of Jordan"], "es": ["Jordania", "Reino Hachemí de Jordania"]},
        "322": {"en": ["Qatar", "State of Qatar"], "es": ["Catar", "Estado de Qatar"]},
        "323": {"en": ["Kuwait", "State of Kuwait"], "es": ["Kuwait", "Estado de Kuwait"]},
        "324": {"en": ["Lao People's Democratic Republic", "Laos"], "es": ["República Democrática Popular de Lao"]},
        "325": {"en": ["Lebanon", "Lebanese Republic"], "es": ["Líbano", "República Libanesa"]},
        "326": {"en": ["Malaysia"], "es": ["Malasia"]},
        "327": {"en": ["Maldives", "Republic of Maldives"], "es": ["Islas Maldivas", "República de Maldivas"]},
        "328": {"en": ["Oman", "Sultanate of Oman"], "es": ["Omán", "Sultanato de Omán"]},
        "329": {"en": ["Mongolia"], "es": ["Mongolia"]},
        "330": {"en": ["Nepal", "Federal Democratic Republic of Nepal"], "es": ["Nepal", "República Federal Democrática de Nepal"]},
        "331": {"en": ["United Arab Emirates", "UAE", "U.A.E."], "es": ["Emiratos Árabes Unidos", "Emiratos Árabes"]},
        "332": {"en": ["Pakistan", "Islamic Republic of Pakistan"], "es": ["Pakistán", "República Islámica de Pakistán"]},
        "333": {"en": ["Singapore", "Republic of Singapore"], "es": ["Singapur", "República de Singapur"]},
        "334": {"en": ["Syrian Arab Republic", "Syria"], "es": ["República árabe de Siria"]},
        "335": {"en": ["Thailand", "Kingdom of Thailand"], "es": ["Tailandia", "Reino de Tailandia"]},
        "336": {"en": ["Türkiye", "Republic of Türkiye", "Turkey"], "es": ["Turquía", "República de Turquía"]},
        "337": {"en": ["Viet Nam", "Socialist Republic of Viet Nam", "Vietnam"], "es": ["Vietnam", "República Socialista de Vietnam"]},
        "341": {"en": ["Hong Kong", "Hong Kong Special Administrative Region of China"], "es": ["Hong Kong", "Región Administrativa Especial China de Hong Kong"]},
        "344": {"en": ["Macao", "Macao Special Administrative Region of China", "Macau"], "es": ["Macao", "Región Administrativa Especial China de Macao"]},
        "345": {"en": ["Bangladesh", "People's Republic of Bangladesh"], "es": ["Bangladés", "República Popular de Bangladés"]},
        "346": {"en": ["Brunei Darussalam", "Brunei"], "es": ["Brunei Darussalam", "Brunéi"]},
        "348": {"en": ["Yemen", "Republic of Yemen"], "es": ["Yemen", "República del Yemen"]},
        "349": {"en": ["Armenia", "Republic of Armenia"], "es": ["Armenia", "República de Armenia"]},
        "350": {"en": ["Azerbaijan", "Republic of Azerbaijan"], "es": ["Azerbaiyán", "República de Azerbaiyán"]},
        "351": {"en": ["Georgia"], "es": ["Georgia"]},
        "352": {"en": ["Kazakhstan", "Republic of Kazakhstan"], "es": ["Kazajistán", "República de Kazajistán"]},
        "353": {"en": ["Kyrgyzstan", "Kyrgyz Republic"], "es": ["Kirguistán", "República Kirguiza"]},
        "354": {"en": ["Tajikistan", "Republic of Tajikistan"], "es": ["Tayikistán", "República de Tayikistán"]},
        "355": {"en": ["Turkmenistan"], "es": ["Turkmenistán"]},
        "356": {"en": ["Uzbekistan", "Republic of Uzbekistan"], "es": ["Uzbekistán", "República de Uzbekistán"]},
        "357": {"en": ["Palestine, State of", "the State of Palestine", "Palestine"], "es": ["Palestina, Estado de", "Estado de Palestina", "Palestina"]},
        "358": {"en": ["Timor-Leste", "Democratic Republic of Timor-Leste", "East Timor"], "es": ["Timor Oriental", "República Democrática de Timor Oriental"]},
        "401": {"en": ["Albania", "Republic of Albania"], "es": ["Albania", "República de Albania"]},
        "404": {"en": ["Andorra", "Principality of Andorra"], "es": ["Andorra", "Principado de Andorra"]},
        "405": {"en": ["Austria", "Republic of Austria"], "es": ["Austria", "República de Austria"]},
        "406": {"en": ["Belgium", "Kingdom of Belgium"], "es": ["Bélgica", "Reino de Bélgica"]},
        "407": {"en": ["Bulgaria", "Republic of Bulgaria"], "es": ["Bulgaria", "República de Bulgaria"]},
        "409": {"en": ["Denmark", "Kingdom of Denmark"], "es": ["Dinamarca", "Reino de Dinamarca"]},
        "410": {"en": ["Spain", "Kingdom of Spain"], "es": ["España", "Reino de España"]},
        "411": {"en": ["Finland", "Republic of Finland"], "es": ["Finlandia", "República de Finlandia"]},
        "412": {"en": ["France", "French Republic"], "es": ["Francia", "República Francesa"]},
        "413": {"en": ["Greece", "Hellenic Republic"], "es": ["Grecia", "República Helénica"]},
        "414": {"en": ["Hungary"], "es": ["Hungría"]},
        "415": {"en": ["Ireland"], "es": ["Irlanda"]},
        "416": {"en": ["Iceland", "Republic of Iceland"], "es": ["Islandia", "República de Islandia"]},
        "417": {"en": ["Italy", "Italian Republic"], "es": ["Italia", "República Italiana"]},
        "418": {"en": ["Liechtenstein", "Principality of Liechtenstein"], "es": ["Liechtenstein", "Principado de Liechtenstein"]},
        "419": {"en": ["Luxembourg", "Grand Duchy of Luxembourg"], "es": ["Luxemburgo", "Gran Ducado de Luxemburgo"]},
        "420": {"en": ["Malta", "Republic of Malta"], "es": ["Malta", "República de Malta"]},
        "421": {"en": ["Monaco", "Principality of Monaco"], "es": ["Mónaco", "Principado de Mónaco"]},
        "422": {"en": ["Norway", "Kingdom of Norway"], "es": ["Noruega", "Reino de Noruega"]},
        "423": {"en": ["Netherlands", "Kingdom of the Netherlands", "Holland", "The Netherlands"], "es": ["Países Bajos", "Reino de los Países Bajos", "Holanda"]},
        "424": {"en": ["Poland", "Republic of Poland"], "es": ["Polonia", "República de Polonia"]},
        "425": {"en": ["Portugal", "Portuguese Republic"], "es": ["Portugal", "República Portuguesa"]},
        "426": {"en": ["United Kingdom", "United Kingdom of Great Britain and Northern Ireland", "Great Britain", "England", "Northern Ireland"], "es": ["Reino Unido", "Reino Unido de Gran Bretaña e Irlanda del Norte", "Inglaterra", "Gran Bretaña", "Irlanda del Norte"]},
        "427": {"en": ["Romania"], "es": ["Rumanía"]},
        "428": {"en": ["San Marino", "Republic of San Marino"], "es": ["San Marino", "República de San Marino"]},
        "429": {"en": ["Sweden", "Kingdom of Sweden"], "es": ["Suecia", "Reino de Suecia"]},
        "430": {"en": ["Switzerland", "Swiss Confederation"], "es": ["Suiza", "Confederación Suiza"]},
        "431": {"en": ["Holy See (Vatican City State)", "Vatican", "Vatican City"], "es": ["Santa Sede (Ciudad Estado del Vaticano)", "Vaticano", "Ciudad del Vaticano"]},
        "438": {"en": ["Germany", "Federal Republic of Germany"], "es": ["Alemania", "República Federal de Alemania"]},
        "439": {"en": ["Belarus", "Republic of Belarus"], "es": ["Bielorrusia", "República de Bielorrusia"]},
        "440": {"en": ["Estonia", "Republic of Estonia"], "es": ["Estonia", "República de Estonia"]},
        "441": {"en": ["Latvia", "Republic of Latvia"], "es": ["Letonia", "República de Letonia"]},
        "442": {"en": ["Lithuania", "Republic of Lithuania"], "es": ["Lituania", "República de Lituania"]},
        "443": {"en": ["Moldova, Republic of", "Republic of Moldova", "Moldova"], "es": ["Moldavia, República de", "República de Moldavia"]},
        "444": {"en": ["Russian Federation", "Russia"], "es": ["Federación Rusa", "Rusia"]},
        "445": {"en": ["Ukraine"], "es": ["Ucrania"]},
        "446": {"en": ["Bosnia and Herzegovina", "Republic of Bosnia and Herzegovina"], "es": ["Bosnia y Herzegovina", "República de Bosnia y Hercegovina"]},
        "447": {"en": ["Croatia", "Republic of Croatia"], "es": ["Croacia", "República de Croacia"]},
        "448": {"en": ["Slovakia", "Slovak Republic"], "es": ["Eslovaquia", "República Eslovaca"]},
        "449": {"en": ["Slovenia", "Republic of Slovenia"], "es": ["Eslovenia", "República de Eslovenia"]},
        "450": {"en": ["North Macedonia", "Republic of North Macedonia", "Macedonia"], "es": ["Macedonia del Norte", "República de Macedonia del Norte"]},
        "451": {"en": ["Czechia", "Czech Republic"], "es": ["Chequia", "República Checa"]},
        "453": {"en": ["Montenegro"], "es": ["Montenegro"]},
        "454": {"en": ["Serbia", "Republic of Serbia"], "es": ["Serbia", "República de Serbia"]},
        "501": {"en": ["Australia"], "es": ["Australia"]},
        "503": {"en": ["Nauru", "Republic of Nauru"], "es": ["Nauru", "República de Nauru"]},
        "504": {"en": ["New Zealand"], "es": ["Nueva Zelanda"]},
        "505": {"en": ["Vanuatu", "Republic of Vanuatu"], "es": ["Vanuatu", "República de Vanuatu"]},
        "506": {"en": ["Samoa", "Independent State of Samoa"], "es": ["Samoa", "Estado Independiente de Samoa"]},
        "512": {"en": ["Fiji", "Republic of Fiji"], "es": ["Fiyi", "República de Fiyi"]},
        "513": {"en": ["Papua New Guinea", "Independent State of Papua New Guinea"], "es": ["Papúa Nueva Guinea", "Estado Independiente de Papúa Nueva Guinea"]},
        "514": {"en": ["Kiribati", "Republic of Kiribati"], "es": ["Kiribati", "República de Kiribati"]},
        "515": {"en": ["Micronesia, Federated States of", "Federated States of Micronesia", "Micronesia"], "es": ["Micronesia, Estados Federados de", "Estados Federados de Micronesia", "Micronesia"]},
        "516": {"en": ["Palau", "Republic of Palau"], "es": ["Palaos", "República de Palau"]},
        "517": {"en": ["Tuvalu"], "es": ["Tuvalu"]},
        "518": {"en": ["Solomon Islands"], "es": ["Islas Salomón"]},
        "519": {"en": ["Tonga", "Kingdom of Tonga"], "es": ["Tonga", "Reino de Tonga"]},
        "520": {"en": ["Marshall Islands", "Republic of the Marshall Islands"], "es": ["Islas Marshall", "República de las Islas Marshall"]},
        "521": {"en": ["Northern Mariana Islands", "Commonwealth of the Northern Mariana Islands"], "es": ["Islas Marianas del Norte", "Commonwealth de las Islas Marianas del Norte"]},
        "652": {"en": ["Anguilla"], "es": ["Anguila"]},
        "654": {"en": ["Cook Islands"], "es": ["Islas Cook"]},
        "656": {"en": ["French Polynesia"], "es": ["Polinesia Francesa"]},
        "663": {"en": ["Bermuda"], "es": ["Islas Bermudas"]},
        "665": {"en": ["Gibraltar"], "es": ["Gibraltar"]},
        "666": {"en": ["Greenland"], "es": ["Groenlandia"]},
        "667": {"en": ["Guam"], "es": ["Guam"]},
        "671": {"en": ["Cayman Islands"], "es": ["Islas Caimán"]},
        "672": {"en": ["Christmas Island"], "es": ["Isla de Navidad"]},
        "673": {"en": ["Cocos (Keeling) Islands"], "es": ["Islas Cocos (Keeling)"]},
        "676": {"en": ["Isle of Man"], "es": ["Isla de Man"]},
        "677": {"en": ["Norfolk Island"], "es": ["Isla Norfolk"]},
        "678": {"en": ["Turks and Caicos Islands"], "es": ["Islas Turcas y Caicos"]},
        "680": {"en": ["Saint Pierre and Miquelon"], "es": ["San Pedro y Miquelon"]},
        "682": {"en": ["Virgin Islands, British", "British Virgin Islands"], "es": ["Islas Vírgenes, Británicas", "Islas Vírgenes Británicas"]},
        "683": {"en": ["Virgin Islands, U.S.", "Virgin Islands, US", "Virgin Islands of the United States", "United States Virgin Islands", "US Virgin Islands"], "es": ["Islas Vírgenes de los Estados Unidos"]},
        "686": {"en": ["Montserrat"], "es": ["Montserrat"]},
        "687": {"en": ["Niue"], "es": ["Niue"]},
        "690": {"en": ["Pitcairn"], "es": ["Pitcairn"]},
        "694": {"en": ["Saint Helena, Ascension and Tristan da Cunha", "Saint Helena"], "es": ["Santa Elena, Ascensión y Tristán de Acuña"]},
        "695": {"en": ["American Samoa"], "es": ["Samoa Estadounidense", "Samoa Americana"]},
        "696": {"en": ["Svalbard and Jan Mayen"], "es": ["Svalbard y Jan Mayen"]},
        "699": {"en": ["Tokelau"], "es": ["Tokelau"]}
    };
    // Códigos de la tabla que salen como otro: 434 (HOLANDA) es Países Bajos.
    const REEMPLAZOS = {"434":"423"};
    const byCode = new Map(COUNTRIES.map(country => [country.code, country]));

    // Los espacios de str.isspace del servidor: JavaScript no cuenta \x1c-\x1f ni \x85 y sí \ufeff.
    const ESPACIO = '[\\t-\\r\\x1c-\\x20\\x85\\xa0\\u1680\\u2000-\\u200a\\u2028\\u2029\\u202f\\u205f\\u3000]';
    const ESPACIOS = new RegExp(ESPACIO + '+', 'g');
    const CODIGO = new RegExp('^0?([0-9]{3})(?:' + ESPACIO + '*[·-]' + ESPACIO + '*([^\\n]+))?$');

    function strip(value) {
        return value.replace(new RegExp('^' + ESPACIO + '+|' + ESPACIO + '+$', 'g'), '');
    }

    function normalize(value) {
        return strip(String(value || '').normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toUpperCase().replace(/\./g, ' ').replace(ESPACIOS, ' '));
    }

    // Un nombre corriente no le cambia el país a un alias de la tabla.
    for (const [code, idiomas] of Object.entries(NOMBRES)) {
        for (const nombre of [...idiomas.en, ...idiomas.es]) ALIASES[normalize(nombre)] ??= code;
    }

    // Mismo criterio que codigo_de_pais del servidor: dos letras tienen que ser ASCII («ＢＲ», «ÉS»).
    function resolve(value) {
        const raw = strip(String(value || '').normalize('NFC'));
        if ([...raw].length <= 2 && !/^[A-Za-z]+$/.test(raw)) return '';
        const code = raw.match(CODIGO);
        if (!code) return ALIASES[normalize(raw)] || '';
        const numero = REEMPLAZOS[code[1]] || code[1];
        const country = byCode.get(numero);
        if (!country) return '';
        const nombre = code[2] === undefined ? null : normalize(code[2]);
        return nombre === null || nombre === normalize(country.name) || ALIASES[nombre] === numero ? numero : '';
    }

    function label(value) {
        const code = resolve(value);
        const country = byCode.get(code);
        return country ? country.code + ' · ' + country.name : '';
    }

    // Un país se ve con el código y el nombre que salen en el TXT; lo demás, como vino, sin blancos en los bordes.
    function etiqueta(value) {
        return label(value) || String(value || '').trim();
    }

    // Los campos angostos cortan la etiqueta: al pasar el mouse se ve entero lo que tienen ahora.
    function alPasarElMouse(campo) {
        const mostrar = () => { campo.title = campo.value; };
        mostrar();
        campo.addEventListener('input', mostrar);
    }

    function optionMarkup() {
        return COUNTRIES.map(country => '<option value="' + country.code + ' · ' + country.name.replace(/&/g, '&amp;').replace(/"/g, '&quot;') + '"></option>').join('');
    }

    CDI.paisesMaria = Object.freeze({ countries: COUNTRIES, resolve, label, etiqueta, alPasarElMouse, optionMarkup });
})();

