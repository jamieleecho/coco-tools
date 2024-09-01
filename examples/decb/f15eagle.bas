10 REM =========================
20 REM =     F-15 EAGLE        =
30 REM =   "GROUND ASSAULT"    =
40 REM =                       =
50 REM = WRITTEN BY: ERIC WOLF =
60 REM = 1630 N. JOHNSON STREET=
70 REM = SOUTH BEND, INDIANA   =
80 REM =                  46628=
90 REM =========================
100 REM
110 CLEAR1000
120 PALETTE RGB:WIDTH 40:CLEAR2000:POKE 65497,0
130 FORY=1TO5:HBUFF Y,275:NEXTY:HBUFF 6,100:HBUFF 7,100:HBUFF 8,100
140 ON BRK GOTO 990
150 FORY=0TO15:PALETTEY,0:NEXTY:POKE &HFF9A,0:HSCREEN2
160 HCLS0:HDRAW"C15;BM2,2;R4L2U1L4R8L4U1L1R2":HGET(0,0)-(8,2),6
170 HCLS13:PL$="S4;BM20,6;NL8NR8U1NL6NR6U1NL2NR2NL12NR12U1NL10NR10U1NL7NR7U1NL2NR2U1NL1NR1":HDRAW "C11"+PL$:HCOLOR14:HSET(17,6):HSET(18,6):HSET(22,6):HSET(23,6):HGET(0,0)-(40,6),3:HCLS13
180 PM$="S3;BM10,10;NG8NE8L2NG6NE6U2NG12NE12L2NG10NE10U2NE7NG7L2NG2NE2U2NG2NE1":HDRAW "C11"+PM$:HSET(8,12,14):HSET(12,8,14):HGET(0,0)-(18,18),4:HCLS 13
190 PM$="S3;BM8,10;NF8NH8R2NF6NH6U2NF12NH12R2NF10NH10U2NF7NH7R2NF2NH2U2NF2NH1":HDRAW "C11"+PM$:HSET(6,8,14):HSET(10,12,14):HGET(0,0)-(18,18),5
200 HCLS13:HDRAW"C8"+PL$:HGET(0,0)-(40,6),1
210 HCLS
220 HCOLOR4:FORY=0TO320STEP10:HLINE(Y,0)-(Y,192),PSET:NEXTY:FORY=0TO192STEP12:HLINE(0,Y)-(319,Y),PSET:NEXTY
230 P$(1)="R8F8L2F12R4M+8,-4;M-6,-16R1M-8,-4L6U2M+6,-1U8M-6,-1U1R6U2L6U1M+6,-1U8M-6,-1;U2R6M+8,-4L1M+6,-16M-8,-4L4G12R2G8L8U20M+4,-20;M-16,-6L4M-40,46;BR55BD36D20M+4,20;M-16,6L4M-40,-46"
240 P$(2)="M-28,-4NR20L12U7R4U2L32;M-8,-2;H2U2E2;M+8,-2;R32U2L4U7R32L20M+28,-4;"
250 P$(3)="U16E2R16F2D4G2L8D4R8F2D4G2L8D12G2L6H2U24BR26BD6E2R8F2D4G2L8H2U4D4F2R8BR8D12F2R6E2U30H2L6G2D30BR16NU4F2R20E2U16H2L13U6R13E2U4H2L20G2D15F2R13D6L13G2
260 P$(4)="BR48D5F2R24E2U4H2L16U5R16E2U4H2L16U5R16E2U4H2L24G2D24BR34D6F2R8E2U6R4D6F2R8E2U30H2L24G2D24BR12BU8R4U8L4D8
270 P$(5)="BR22D14F2R28E2U16H2L16G2D4F2R8D4L10H2U14E2R16E2U4H2L26G2D24BR38D6F2R28E2U6H2L16H2U20H2L8G2D28BR38D2F2R24E2U4H2L16U5R16E2U4H2L16U5R16E2U4H2L24G2D28
280 FORY=0TO0:FORX=0TO1:HDRAW"BM"+STR$(138+X)+","+STR$(146+Y)+";C3;"+P$(1):HDRAW P$(2):NEXTX,Y
290 HPRINT(8,6),"Written By Eric A. Wolf"
300 HPAINT(80,130),2,3
310 HPRINT(23,11),"Range: 4000":HPRINT(23,12),"Speed: 0- Mach 2":HPRINT(23,13),"Fuel:  20000 lbs"
320 HPRINT(23,14),"Ceiling: 85000 ft":HPRINT(23,15),"Armourment:":HPRINT(24,16),"- Sidewinders"
330 HPRINT(24,17),"- Sparrows":HPRINT(24,18),"- GBU 15 bombs":HPRINT(24,19),"- 30 mm Gun Pods"
340 HPRINT(23,20),"Thrust: 25000 lbs"
350 X1=20:Y1=20:HDRAW"C1;BM"+STR$(X1)+","+STR$(Y1)+";"+P$(3):HDRAW P$(4):HDRAW P$(5):HPAINT(X1+4,Y1+4):HPAINT(X1+32,Y1-4):HPAINT(X1+52,Y1+4):HPAINT(X1+64,Y1+9):HPAINT(X1+112,Y1+9)
360 HPAINT(X1+150,Y1+9):HPAINT(X1+180,Y1+9):HPAINT(X1+218,Y1+9):HPAINT(X1+258,Y1+9)
370 X1=24:Y1=24:HDRAW"C3;BM"+STR$(X1)+","+STR$(Y1)+";"+P$(3):HDRAW P$(4):HDRAW P$(5):HPAINT(X1+4,Y1+4):HPAINT(X1+32,Y1-4):HPAINT(X1+52,Y1+4):HPAINT(X1+64,Y1+9):HPAINT(X1+112,Y1+9)
380 HPAINT(X1+150,Y1+9):HPAINT(X1+180,Y1+9):HPAINT(X1+218,Y1+9):HPAINT(X1+258,Y1+9)
390 '*     DELETE LINE 420 IF YOU    *
400 '* ARE USING A CMP MONITOR OR TV *
410 '
420 GOTO 480
430 '
440 '**** CMP COLOR PALETTES *****
450 PALETTE0,0:PALETTE1,16:PALETTE2,32:PALETTE3,63:PALETTE4,13:PALETTE5,21:PALETTE6,36:PALETTE8,0:PALETTE9,14:PALETTE10,32:PALETTE11,63:PALETTE12,32:PALETTE13,36:PALETTE14,7
460 GOTO 490
470 '**** RGB COLOR PALETTES *****
480 PALETTE0,0:PALETTE1,7:PALETTE2,56:PALETTE3,63:PALETTE4,8:PALETTE5,34:PALETTE6,54:PALETTE8,0:PALETTE9,3:PALETTE10,56:PALETTE11,63:PALETTE12,56:PALETTE13,48:PALETTE14,32
490 POKE65496,0:PLAY"V20;T2;L8;A;O4;L16;C;L4;C;O3;L16;B-;L16;A;L8;G;L4;A;L4;B-;L4;B;O4;L4;C;L8;D;L16;F;L4;F;L16;G;L16;F;L8;D;L4;C":POKE65497,0:T=0
500 T=T+1:IF T>1000 THEN 520 ELSE IF BUTTON(0)<>0 THEN 520
510 IFINKEY$="" THEN 500
520 HSCREEN0:POKE &HFF9A,0:ATTR3,0:CLS:PRINTTAB(5)"F-15 Ground Assault Simulator":ATTR2,0:PRINTTAB(7)"Written By: Eric A. Wolf":ATTR1,0:PRINTSTRING$(40,"-");
530 LOCATE6,12:ATTR2,0:PRINT"Enter Difficulty Level (0-9)"
540 LOCATE19,14:ATTR3,0
550 A$=INKEY$:IFA$<"0" ORA$>"9" THEN 550 ELSE PRINTA$;:SOUND200,1
560 ATTR3,0:LOCATE7,22:PRINT"Stand by.... For Level "+A$:LV$=A$:LV=VAL(A$)
570 POKE &HE6,2 'SETUP FOR HSCREEN 2
580 HCLS0:HCOLOR3:HDRAW"BM0,0;BF6BU2BR4NG4E4R292F8D118G8L292H8U118":HPRINT(0,17),"Thrust":HPRINT(8,17),"Radar":FORY=146 TO 192 STEP11.5:HLINE(8,Y)-(12,Y),PSET:HLINE(10,Y+5.75)-(12,Y+5.75),PSET:NEXTY
590 HLINE(54,146)-(110,192),PSET,B:HLINE(16,146)-(26,192),PSET,B:HCOLOR14:HLINE(17,169)-(25,190),PSET,BF:HCOLOR3:HPRINT(15,23),"Fuel":HLINE(160,184)-(319,192),PSET,B:HPAINT(168,188),6,3:HCIRCLE(160,158),20
600 HPRINT(28,17),"F-15 Ground":HPRINT(30,18),"Assault"
610 FORY=138 TO 178 STEP 8:HLINE(132,Y)-(136,Y),PSET:HLINE(184,Y)-(188,Y),PSET:NEXTY
620 HPRINT(28,21),"Play Level "+LV$:HLINE(7,46)-(313,46),PSET:HPAINT(160,45),4,3
630 HCOLOR5:HLINE(7,58)-(7,46),PSET:FORY=7 TO 313 STEP 16:HLINE-(Y,RND(16)+30),PSET:NEXTY:HLINE-(313,58),PSET:HLINE(7,58)-(313,58),PSET:HPAINT(160,57)
640 HCOLOR12:HLINE(7,58)-(7,50),PSET:FORY=7 TO 313 STEP 12:HLINE-(Y,RND(16)+40),PSET:NEXTY:HLINE-(313,58),PSET:HLINE(7,58)-(313,58),PSET:HPAINT(160,57):HCOLOR3:HLINE(7,58)-(313,58),PSET:HPAINT(160,59),13,3
650 P2=130:Y=59:T=2:F=318:X1=7:X2=313:GOSUB660:GOTO690
660 HCOLOR7:HLINE(X1,Y)-(X2,Y),PSET:HCOLOR15:IF Y+(T/2)<128 OR Y+(T/2)<P2 THEN HLINE(X1,Y+(T/2))-(X2,Y+(T/2)),PSET
670 Y=Y+T:T=T+(T/2):IF Y>128 THEN 680 ELSE 660
680 RETURN
690 FOR X=55 TO 110STEP3:HSET(X,150,2):HSET(X,160,2):HSET(X,170,2):HSET(X,180,2):HSET(X,190,2):NEXTX
700 FORX=147 TO 191 STEP3:HSET(55,X,2):HSET(65,X,2):HSET(75,X,2):HSET(85,X,2):HSET(95,X,2):HSET(105,X,2):NEXTX
710 HDRAW"BM82,168;C3;NG4F4U1H4G4"
720 POKE &HE6C6,18:POKE &HE6C7,18:HSCREEN2:TH=21:L=1:L1=PEEK(&HFFBD):L2=PEEK(&HFFB5):SW=0:PLAY"T255L255;V31;":PO=1:PN=1:TIMER=0:P1=140:P2=96:M1=PEEK(&HFFB6):M2=PEEK(&HFFBE):HT=0:TT=1:E1=130
730 PLAY"T255L255":FORY=31 TO 1 STEP-1:PLAY "V"+STR$(Y)+";FBFCFD":NEXTY:PLAY"V31"
740 HGET(E1,56)-(E1+8,58),7
750 SW=SW+1:IF SW>((46-TH)/9) THEN SW=0:IF L3=0 THEN POKE &HFFBF,L1:POKE &HFFB7,L2:L3=1 ELSE L3=0:POKE &HFFBF,L2:POKE &HFFB7,L1
760 ON L GOSUB 1000,1060,1200,1120,800,840,870,1100
770 L=L+1:IF L>8 THEN L=1
780 GOTO 750
790 GOTO790
800 IFPEEK(341)=247 THEN TI=2 ELSE IFPEEK(342)=247 THEN TI=-1:HCOLOR0:HLINE(17,190-TH)-(25,190-TH),PSET ELSE RETURN
810 TH=TH+TI:IF TH<0 THEN TH=0 ELSE IF TH>43 THEN TH=43
820 HCOLOR14:HLINE(17,190-TH)-(25,191-TH),PSET,BF
830 RETURN
840 F1=F1+1:IF F1<(48-TH)/6 THEN RETURN ELSE IF F>210 THEN 850 ELSE IF CF=1 THEN CF=0:POKE &HFFB6,M1 ELSE CF=1:POKE &HFFB6,M2
850 F1=0:HLINE(F,185)-(F,190),PRESET:PLAY"CC":F=F-1:IF F>160 THEN RETURN
860 GOTO 910
870 IF G=1 THEN G=0:GOTO 1120 ELSE G=1
880 A=PO:HCOLOR0:GOSUB890:A=PN:HCOLOR3:GOSUB890:PO=PN:RETURN
890 IF A=1 THEN HDRAW"BM160,158;NG12NE12BF4G4E8" ELSE IFA=2 THEN HDRAW"BM160,158;NL16NR16BD4L4R8" ELSE HDRAW"BM160,158;NF12NH12BG4H4F8"
900 RETURN
910 T=TIMER:HSCREEN0:CLS:ATTR3,0,B:PRINTTAB(4)"<<==- YOU RAN OUT OF FUEL ! -==>>":GOTO930
920 T=TIMER:HSCREEN0:CLS:ATTR3,0,B:PRINTTAB(4)"<<==- YOU WERE SHOT DOWN -==>>"
930 POKE&HFF9A,0:PLAY"T255L255;V31;":FORY=1TO5:FORX=1TO12:PLAY STR$(X):NEXTX,Y:ATTR2,0:LOCATE0,5:PRINT"Flight Time":LOCATE30,5:PRINTINT(T/3600);":";INT((T-INT(T/3600)*3600)/60);:LOCATE0,7:PRINT"Hit/Miss Rating"
940 IF TT=0 THEN I=0 ELSE I=INT(100*(HT/(TT-1)))
950 LOCATE30,7:PRINTI;"%"
951 LOCATE0,9::PRINT"Total Score:":LOCATE30,9:PRINT(I*10*(LV+1)):FORY=1TO1000:NEXTY
960 LOCATE10,16:PRINT"Play another game ?"
970 A$=INKEY$:IF BUTTON(0)=0 AND A$="" THEN 970
980 IF BUTTON(0)<>0 THEN 150 ELSE IF A$="Y" THEN 150 ELSE IF A$="N" THEN CLS:END ELSE 970
990 ATTR0,0:PALETTE RGB:STOP
1000 P3=JOYSTK(0):P4=JOYSTK(1):P4=63-P4:IF P3<16 THEN PN=1:P1=P1-4:P1=P1-(TH/11) ELSE IF P3>48 THEN P1=P1+4:P1=P1+(TH/11):PN=3 ELSE PN=2
1010 P1=INT(P1):IF P1<15 THEN P1=15 ELSE IF P1>265 THEN P1=265
1020 IFP4<26 THEN P2=P2-4:P2=P2-(TH/22) ELSE IF P4>36 THEN P2=P2+4:P2=P2+(TH/22)
1030 P2=INT(P2):IF P2<64 THEN P2=64 ELSE IF P2>107 THEN P2=107
1040 HPUT(P1,126)-(P1+40,132),1,PSET
1050 RETURN
1060 ON PN GOTO 1070,1080,1090
1070 HGET(P1+10,P2)-(P1+28,P2+18),2:HPUT(P1+10,P2)-(P1+28,P2+18),4,PSET:RETURN
1080 HGET(P1,P2)-(P1+40,P2+6),2:HPUT(P1,P2)-(P1+40,P2+6),3,PSET:RETURN
1090 HGET(P1+10,P2)-(P1+28,P2+18),2:HPUT(P1+10,P2)-(P1+28,P2+18),5,PSET:RETURN
1100 IF PN=2 THEN HPUT(P1,P2)-(P1+40,P2+6),2,PSET:RETURN ELSE HPUT(P1+10,P2)-(P1+28,P2+18),2,PSET:RETURN
1110 RETURN
1120 IF BUTTON(0)=0 THEN RETURN ELSE TT=TT+1
1130 HCOLOR 14:ON PN GOSUB 1170,1180,1190
1140 PLAY"F":HCOLOR 13:ON PN GOSUB 1170,1180,1190
1150 IF FP<E1 OR FP>E1+6 THEN RETURN ELSE HT=HT+1:SOUND100,1:HDRAW"BM"+STR$(INT(54+(E1/6)))+",152;C0;U1R1D1L1":HPUT(E1,56)-(E1+8,58),7,PSET:E1=RND(250)+25:HGET(E1,56)-(E1+8,58),7:RETURN
1160 RETURN
1170 HLINE(P1+9,P2+18)-(P1+18,60),PSET:HLINE-(P1+27,P2),PSET:FP=P1+18:RETURN
1180 HLINE(P1+6,P2+4)-(P1+20,60),PSET:HLINE-(P1+32,P2+4),PSET:FP=P1+20:RETURN
1190 HLINE(P1+9,P2)-(P1+18,60),PSET:HLINE-(P1+27,P2+17),PSET:FP=P1+18:RETURN
1200 HDRAW"BM"+STR$(INT(54+(E1/6)))+",152;C0;U1R1D1L1":HPUT(E1,56)-(E1+8,58),7,PSET:E2=INT(RND(LV)*3.5):IF RND(2)=1 THEN E1=E1+E2 ELSE E1=E1-E2
1210 IF E1<18 THEN E1=18 ELSE IF E1>274 THEN E1=274
1220 HGET(E1,56)-(E1+8,58),7:HPUT(E1,56)-(E1+8,58),6,OR:HDRAW"BM"+STR$(INT(54+(E1/6)))+",152;C3;U1R1D1L1"
1230 IF RND(11-LV)<>1 THEN RETURN ELSE IF E1+4<P1-4 THEN RETURN ELSE IF E1+4>P1+24 THEN RETURN
1240 HGET(E1+4,56)-(E1+4,P2+8),8:HCOLOR15:HLINE(E1+4,56)-(E1+4,P2+8),PSET:PLAY"AB"
1250 IF (E1+4<P1+10 OR E1+4>P1+30) THEN HPUT(E1+4,56)-(E1+4,P2+8),8,PSET:RETURN ELSE PALETTE14,32:FORY=31 TO 1 STEP-1:HCIRCLE(E1+4,P2+8),(31-Y),14:PLAY"V"+STR$(Y)+";CDCD;P30":PALETTE 11,RND(64)-1:FORX=1TO15:NEXTX:NEXTY:PALETTE11,63:GOTO920
 