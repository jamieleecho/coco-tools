10 HSCREEN 2
20 A$ = "LDRUL5D10R10U15L15D20R20U25L20"
30 B$ = "E10F10G10H15E15F20G20H25E20"
40 C$ = "M+0,+20;M-10,0;M+10,-20"
50 D$ = "M+0,-20;M+10,0;M-10,+20"
60 E$ = "NM+0,-20;NM+10,0;NM-10,+20"
70 F$ = "NL10NR10NU10ND10"
80 G$ = "NE10NF10NG10NH10"
90 H$ = "LBDRUBL5D10BR10U15BL15D20BR20U25BL20"
100 I$ = "EFGHE5BF10G10BH15E15BF20G20BH25E20"
110 XX$ = "BM159,95;"
200 HDRAW "S1A1C1" + XX$ + A$
210 HDRAW "S2A2C1" + XX$ + A$
220 HDRAW "S3A3C1" + XX$ + A$
230 HDRAW "S4A0C1" + XX$ + A$
240 HDRAW "S5A1C2" + XX$ + A$
250 HDRAW "S6A2C2" + XX$ + A$
260 HDRAW "S7A3C2" + XX$ + A$
270 HDRAW "S8A0C2" + XX$ + A$
280 HSET(0, 0, 5)
290 HCOLOR 3
300 HLINE-(40, 40), PRESET
310 HDRAW "S20A0" + A$
320 HLINE-(300, 180), PRESET
330 HDRAW "C3S30A1" + A$
340 HDRAW "C4S3BM100,100" + B$
350 HDRAW "C5S2BM200,100" + C$
360 HDRAW "C6S1BM250,100" + D$
370 HDRAW "C7S1BM250,125" + E$
380 HDRAW "C8S1BM100,150" + F$
390 HDRAW "C9S1BM150,150" + G$
400 HDRAW "C0S1BM200,150" + H$
410 HDRAW "C15S2BM220,170" + I$
1000 GOTO 1000