140 CLEAR
150 CLS0:FORZ=0TO10:PRINT@32*Z,"               ";:NEXTZ
160 REM CALL

170 Z=RND(-(PEEK(9)*256+PEEK(10)))
180 FORZ=1TORND(12):SOUNDRND(200),1
190 NEXTZ

200 R$=CHR$(92)
270 X=INT(RND(0)*14)
280 Y=0
290 SH=100
300 T=1000
350 A$=INKEY$
360 T=T-1
370 PRINT@8*32,"TIME"T/10;
380 IFT<1THEN740
390 IFA$<>""THEN560
430 XX=X
440 YY=Y
450 X=X+INT(RND(0)*3-1)
460 IFX<0THENX=0
461 IFX>14THENX=14
470 Y=Y+INT(RND(0)*3-1)
480 IFY<1THENY=1
481 IFY>7THENY=7
490 PRINT@X+32*Y,"#";
500 PRINT@XX+32*YY," ";
510 PRINT@32*4+7,"+";
520 GOTO350
560 PRINT@X+32*Y," ";
570 SH=SH-1
580 IFSH=0THEN740
590 PRINT@32*7+4,"/     "R$;
600 PRINT@32*6+5,"/   "R$;
610 PRINT@32*5+6,"/ "R$;
620 Z=X+32*Y
631 IFZ=135THENPRINT@135,"*";:SOUND99,2:S=S+1:X=1:Y=1:GOTO640
632 IFZ=228THENPRINT@228,"*";:SOUND99,2:S=S+1:X=1:Y=1:GOTO640
633 IFZ=197THENPRINT@197,"*";:SOUND99,2:S=S+1:X=1:Y=1:GOTO640
634 IFZ=166THENPRINT@166,"*";:SOUND99,2:S=S+1:X=1:Y=1:GOTO640
635 IFZ=201THENPRINT@201,"*";:SOUND99,2:S=S+1:X=1:Y=1:GOTO640
636 IFZ=234THENPRINT@234,"*";:SOUND99,2:S=S+1:X=1:Y=1:GOTO640
637 IFZ=168THENPRINT@168,"*";:SOUND99,2:S=S+1:X=1:Y=1:GOTO640
638 SOUND1,1
640 PRINT@32*7+4,"       ";
650 PRINT@32*6+5,"     ";
660 PRINT@32*5+6,"   ";
670 PRINT@32*9,"HITS"S;
680 PRINT@32*10,"AMMO"SH;
690 IFS=10THEN830
700 GOTO350
740 PRINT@33,"game over.";
760 PRINT@65,"you lose.";
770 FORZ=1TO2500
780 NEXT Z
790 GOTO140
830 PRINT@33,"you win!!!";
840 FORZ=1TO2500
850 NEXTZ
860 GOTO140
900 REM     ALIEN ATTACK
901 REM  BY DAVID W STEWART
903 REM  PPR DECEMBER 1985
902 REM MC-10 EDITS JIM GERRIE