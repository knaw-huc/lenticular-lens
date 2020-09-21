import re


def bloothooft_reduct(input, type):
    result = bloothooft(input, type)
    result = result.upper()

    if type != 'first_name' and len(result) > 4:
        result = re.sub(r"(?<=S)D$", r'', result)  # 40
        result = re.sub(r"(?<=S)N$", r'', result)  # 41
        result = re.sub(r"DR$", r'', result)  # 42
        result = re.sub(r"(?<=[EYUIOAR]S)E$", r'', result)  # 43
        result = re.sub(r"(?<=[^EYUIOAR])SE$", r'', result)  # 45
        if len(result) > 5:
            result = re.sub(r"(?<=[EYUIOAR]S)[EO]N$", r'', result)  # 46
            result = re.sub(r"(?<=[^EYUIOAR])S[EO]N$", r'', result)  # 48
        if len(result) > 6:
            result = re.sub(r"(?<=[EYUIOAR]S)[EO]NS$", r'', result)  # 49
            result = re.sub(r"(?<=[^EYUIOAR])S[EO]NS$", r'', result)  # 51
            result = re.sub(r"SO[HO]N$", r'', result)  # 52
        if len(result) > 8:
            result = re.sub(r"DO[XG]TER$", r'', result)  # 53

    if len(result) > 3:
        result = re.sub(r"(?<=[EYUIOAKR])S$", r'', result)  # 54

    if type != 'family_name':
        if len(result) > 4 or re.search(r"[EYUIOA]{2}.{2}", result) is not None:
            result = re.sub(r"TRUS$", r'ER', result)  # 56
            result = re.sub(r"(?<=[QWRTPSDFGHJKLZXCVBNM])[IY][UÜ]S$", r'', result)  # 57
            result = re.sub(r"S[KC][UÜ]S$", r'S', result)  # 58
            result = re.sub(r"(?<=[QWRTPSDFGHJKLZXCVBNM])[UÜ]S$", r'', result)  # 59
            result = re.sub(r"(?:(?<=[QWRTPSDFGHJKLZXCVBNM])[IEÖ]S$)|(?:(?<=[QWRTPSDFGHJKLZXCVBNM])[EYUIOA]ÖS$)", r'',
                            result)  # 60

        if len(result) > 4 or (len(result) == 4 and re.search(r"[QWRTPSDFGHJKLZXCVBNM]", result) is not None):
            result = re.sub(r"[EYUIOA]$", r'', result)  # 61

        if len(result) > 2:
            result = re.sub(r"(.)\1$", r'\1', result)  # 38

        if len(result) > 5:
            result = re.sub(r"(?<=^.)([QWRTPSDFGHJKLZXCVBNM])\1E(?=(?:[BHVH]|[QWRTPSDFGHJKLZXCVBNM][EYUIOA]))", r'\1',
                            result)  # 62
        if len(result) > 6:
            result = re.sub(r"(?<=^..)([QWRTPSDFGHJKLZXCVBNM])\1E(?=(?:[BHVH]|[QWRTPSDFGHJKLZXCVBNM][EYUIOA]))", r'\1',
                            result)  # 63

        if len(result) > 3:
            result = re.sub(r"(?<=[EYUIOAR][GX])[IEY]N$", r'', result)  # 64
            result = re.sub(r"(?<=[QWRTPSDFGHJKLZXCVBNM])[^EYUIOAR][GX][IEY]N$", r'',
                            result)  # 65 A lot of interpretation was needed
            result = re.sub(r"(?<=[BFKLNPSV])EN$", r'', result)  # 66
        if len(result) > 4:
            result = re.sub(r"(?<=[EYUIOA][DRT])EN$", r'', result)  # 68
        if len(result) > 5:
            result = re.sub(r"JE[NRS]$", r'', result)  # 67

        if len(result) > 3:
            result = re.sub(r"(?<=IN)[GK]$", r'', result)  # 69
            result = re.sub(r"(?<=N)G$", r'', result)  # 69a

        if len(result) > 5:
            result = re.sub(r"ERL$", r'E', result)  # 71

        if len(result) > 2:
            result = re.sub(r"(?<=[QWRTPSDFGHJKLZXCVBNM])J$", r'', result)  # 72
            result = re.sub(r"(?<=[^EYUIOARNL])[GX]$", r'', result)  # 73

        if len(result) > 3:
            result = re.sub(r"(?<=[^EYUIOAR])[CKPS]$", r'', result)  # 74
            result = re.sub(r"(?<=[BFNVW])T$", r'', result)  # 75

            result = re.sub(r"(?<=[^EYUIOAL])EK$", r'', result)  # 76

        result = re.sub(r"(?<=[^EYUIOABHVW])[IY][DGKLNSTX]$", r'', result)  # 77
        result = re.sub(r"(?<=[^EYUIOADGMRTX])[IY][DGKLTX]$", r'', result)  # 77a
        if len(result) > 4:
            result = re.sub(r"(?<=[^EYUIOAR])KE.$", r'', result)  # 78

        if len(result) > 5:
            result = re.sub(r"(?<=[EYUIOA][^EYUIOAR])[IY][AÆæ±].$", r'', result)  # 79
        if len(result) > 6:
            result = re.sub(r"(?<=[EYUIOA][^EYUIOAR])[IY][AÆæ±][AÆæ±].$", r'', result)  # 80

        if len(result) > 3:
            result = re.sub(r"([EYUIOA]T$|[EYUIOA]RT$|[EYUIOA]GT$|[^E]LT$)|T$", r'\1', result)  # 82

        if len(result) > 2:
            result = re.sub(r"(?<=[^EYUIOACP])H$", r'', result)  # 83

        if len(result) > 5:
            result = re.sub(r"(.+[EYUIOA].+)(?<=[^EYUIOABGHMRVWX])ET$", r'\1', result)  # 84
            result = re.sub(r"(.+[EYUIOA].+)(?<=[^EYUIOAGHMNRVWX])EL$", r'\1', result)  # 85
        if len(result) > 4:
            result = re.sub(r"(?<=[EYUIOA]([QWRTPSDFGHJKLZXCVBNM]))\1E[^MRW]$", r'', result)  # 86
        if len(result) > 2:
            result = re.sub(r"(.)\1$", r'\1', result)  # 38
    result = re.sub(r"(?<=^[EYUIOA][QWRTPSDFGHJKLZXCVBNM])[EYUIOA]$", r'', result)  # 61

    if type != 'family_name':
        if len(result) > 2:
            result = re.sub(r"(?<=[DFMW])K$", r'', result)  # 101
        result = re.sub(r"(?<=[EYUIOA]S)K$", r'', result)  # 102
        if len(result) > 2:
            result = re.sub(r"(?<=[^EYUIOALR])T[NS]$", r'', result)  # 95
        if len(result) > 3:
            result = re.sub(r"(?<=[^EYUIOA][^EYUIOAR])[NS]$", r'', result)  # 96
        if len(result) > 2:
            result = re.sub(r"(?<=E[DT])S$", r'', result)  # 97

        if len(result) > 4:
            result = re.sub(r"(?<![EYUIOA])D$", r'T', result)  # 129

        result = re.sub(r"H(?=[QWRTPSDFGHJKLZXCVBNM])", r'', result)  # 30
        result = re.sub(r"(?<=^[QWRTPSDFGHJKLZXCVBNM])H", r'', result)  # 32

    if len(result) > 3:
        result = re.sub(r"(?<=[^EYUIOAR])S", r'', result)  # 54

    if len(result) > 2:
        result = re.sub(r"(.)\1$", r'\1', result)  # 38
    if type == 'family_name':
        result = re.sub(r"PH$", r'F', result)  # 160

        if len(result) > 2:
            result = re.sub(r"PH$", r'F', result)  # 160

            result = re.sub(r"(?<=[QWRTPSDFGHJKLZXCVBNM])J.$", r'', result)  # 90
        if len(result) > 5:
            result = re.sub(r"(?<=[QWRTPSDFGHJKLZXCVBNM])JE[NRS]$", r'', result)  # 91
        if len(result) > 6:
            result = re.sub(r"(?<=[QWRTPSDFGHJKLZXCVBNM])JERS$", r'', result)  # 92

        if len(result) > 5:
            result = re.sub(r"[IY]US$", r'', result)  # 93
        result = re.sub(r"(?<=[^K][DKLMNPRSX])US$", r'', result)  # 94

    if len(result) > 4:
        result = re.sub(r"D$", r'T', result)  # 129

    if type == 'family_name':
        if len(result) > 2:
            result = re.sub(r"CS$", r'K', result)  # 110
        result = re.sub(r"CS", r'S', result)  # 122

    if len(result) > 4:
        result = re.sub(r"INK$", r'ING', result)  # 112

    if len(result) > 3:
        result = re.sub(r"(?<=[^EYUIOAR])S", r'', result)  # 54
    if type == 'family_name':
        result = re.sub(r"PH$", r'F', result)  # 160
    if len(result) > 2:
        result = re.sub(r"(.)\1$", r'\1', result)  # 38

    result = re.sub(r"C$", r'K', result)  # 8
    result = re.sub(r"(?<=[^GLMNST])X$", r'G', result)  # 106

    if len(result) > 2:
        result = re.sub(r"TD$", r'T', result)  # 99
    result = re.sub(r"(?<=[QWRTPSDFGHJKLZXCVBNM])SK$", r'', result)  # 103
    result = re.sub(r"(?<=[FST])N$", r'', result)  # 104
    result = re.sub(r"(?<=[EYUIOA])VW$", r'', result)  # 105
    result = re.sub(r"V$", r'F', result)  # 109

    if len(result) > 2:
        result = re.sub(r"(.)\1$", r'\1', result)  # 38

    return result


def bloothooft(input, type):
    result = input
    result = result.upper()
    result = re.sub(r"[Ééèëê]", 'E', result, flags=re.I)
    result = re.sub(r"[áàâäª]", 'A', result, flags=re.I)
    result = re.sub(r"[ÄäÆæ]", 'æ', result, flags=re.I)
    result = re.sub(r"[Üúùü]", 'U', result, flags=re.I)
    result = re.sub(r"[ìíïî]", 'I', result, flags=re.I)
    result = re.sub(r"[óòôº]", 'O', result, flags=re.I)
    result = re.sub(r"[ÿ]", 'Y', result, flags=re.I)

    result = re.sub(r"(.)\1{2,}", r'\1\1', result)  # 134

    result = re.sub(r"AJ$", 'Æ', result)  # 137
    if len(result) > 2:
        result = re.sub(r"(?<=[^AI])J$", '', result)  # 126
        result = re.sub(r"NTJ$", 'N', result)  # 100
    result = re.sub(r"([^I])J([QWRTPSDFGHJKLZXCVBNM])", r'\1I\2', result)  # 127

    result = re.sub(r"IE(?!U)|E[IY]|I[IJY]|Y[IJY]", r'Y', result)  # 89
    result = re.sub(r"Aæ|AE(?!U)|EA(?![EU])", r'æ', result)  # 145
    result = re.sub(r"AU|OU|Aα|Oα", r'α', result)  # 224
    result = re.sub(r"OA|AO|ÅA", r'Å', result)  # 143
    result = re.sub(r"AI|AY|AÆ|æI|æY", r'Æ', result)  # 146
    result = re.sub(r"EU|AEU|EÖ", r'Ö', result)  # 153
    result = re.sub(r"OE", r'û', result)  # 150
    result = re.sub(r"UI|UY|UÜ", r'Ü', result)  # 154
    if type != 'family_name':
        result = re.sub(r"([QWRTPSDFGHJKLZXCVBNM])YE(.)$", r'\1Y\2', result)  # 89

    if type != 'family_name':
        result = re.sub(r"PH", r'F', result)  # 70
    else:
        result = re.sub(r"^PH(?=[IYL])", r'F', result)  # 189
        result = re.sub(r"PH$", r'F', result)  # 160
        result = re.sub(r"PHUS$", r'F', result)  # 161
        result = re.sub(r"PHER$", r'FER', result)  # 162
        result = re.sub(r"PHERS$", r'FERS', result)  # 163
        result = re.sub(r"PH(?=[QWRTPSDFGHJKLZXCVBNM])", r'F', result)  # 164
        result = re.sub(r"(^[^OU])PH", r'\1F', result)  # 165
        result = re.sub(r"(^.[LMPRS])PH", r'\1F', result)  # 166
        result = re.sub(r"([^EYUIOALMPRS])PH", r'\1F', result)  # 166a
        result = re.sub(r"([QWRTPSDFGHJKLZXCVBNM][LMPRS])PH", r'\1F', result)  # 167
        result = re.sub(r"PH(?=[QWRTPSDFGHJKLZXCVBNM]+$|[EYUIOA]+$)", r'F', result)  # 169

    result = re.sub(r"^TSJ", r'TJ', result)  # 2

    result = re.sub(r"Z", r'S', result)  # 3

    result = re.sub(r"^QU(?=[EYUIOA])", r'KW', result)  # 4
    if type != 'family_name':
        result = re.sub(r"Q(?=.{0,2}$)", r'K', result)  # 5
    result = re.sub(r"QU(?=[EYUIOA])", r'K', result)  # 6
    result = re.sub(r"Q(?!U[EYUIOA])", r'K', result)  # 7
    result = re.sub(r"UI|UY|UÜ", r'Ü', result)  # 154

    result = re.sub(r"C$", r'K', result)  # 8
    result = re.sub(r"SC(?=[EYUIOA])", r'SK', result)  # 9
    result = re.sub(r"COI", r'SOI', result)  # 130
    result = re.sub(r"C(?![æEHIKSXY])", r'K', result)  # 10
    result = re.sub(r"CEES", r'KEES', result)  # 131
    result = re.sub(r"CæT", r'KæT', result)  # 132
    result = re.sub(r"C(?=[æÖEIY])", r'S', result)  # 11
    result = re.sub(r"^CS", r'S', result)  # 12

    result = re.sub(r"KXS", r'KS', result)  # 13
    result = re.sub(r"KX(?=[^S]$)", r'KS', result)  # 14
    result = re.sub(r"KX$", r'KS', result)  # 15
    if len(result) > 2:
        result = re.sub(r"([αÖÆS]|OI)X$", r'\1', result)  # 16
    result = re.sub(r"^X", r'S', result)  # 123
    result = re.sub(r"X", r'KS', result)  # 17

    result = re.sub(r"(?<=[EYUIOA])CK(?=[EYUIOA])", r'KK', result)  # 18
    result = re.sub(r"(?<=[QWRTPSDFGHJKLZXCVBNM])CK|CK(?=[QWRTPSDFGHJKLZXCVBNM])", r'K', result)  # 19
    result = re.sub(r"CK$", r'K', result)  # 20

    result = re.sub(r"^CHR", r'KR', result)  # 21
    result = re.sub(r"(?<=[GTS])CH$", r'', result)  # 22
    result = re.sub(r"(?<![GLMNST])CH$", r'G', result)  # 23
    if len(result) > 4:
        if type == 'family_name':
            result = re.sub(r"(?<=[EYUIOA])SCH(?=[EYUIOA]$)", r'SS', result)  # 113
        else:
            result = re.sub(r"(?<=[EYUIOA])SCH(?=[EYUIOA]$)", r'SJ', result)  # 140
        result = re.sub(r"(?<=[QWRTPSDFGHJKLZXCVBNM])SCH(?=[EYUIOA]$)", r'S', result)  # 114
        result = re.sub(r"(?!(?<=[EYUIOA])CH(?=[EYUIOA]))(?<=[^N])CH(?=.$)", r'G', result)  # 25
    if len(result) > 5:
        result = re.sub(r"(?<=[EYUIOA]S)CH(?=E.$)", r'S', result)  # 115
        result = re.sub(r"(?<=[QWRTPSDFGHJKLZXCVBNM]S)CH(?=E.$)", r'', result)  # 116
    if len(result) > 6:
        result = re.sub(r"(?<=[EYUIOA]S)CH(?=E.S$)", r'S', result)  # 117
        result = re.sub(r"(?<=[QWRTPSDFGHJKLZXCVBNM]S)CH(?=E.S$)", r'', result)  # 118
    result = re.sub(r"(?<=S)CH(?![EYUIOA]R)", r'', result)  # 26
    result = re.sub(r"(?<=[EYUIOA]S)CH(?=E)", r'S', result)  # 119
    result = re.sub(r"(?<=S)SCH(?=E)", r'S', result)  # 120
    result = re.sub(r"^SCH", r'SG', result)  # 27
    result = re.sub(r"(<=[QWRTPSDFGHJKLZXCVBNM])CH|CH(?=[QWRTPSDFGHJKLZXCVBNM])", r'G', result)  # 28
    result = re.sub(r"CH", r'X', result)  # 88

    if len(result) > 2:
        result = re.sub(r"H$", r'', result)  # 29
    result = re.sub(r"H(?=[QWRTPSDFGHJKLZXCVBNM])", r'', result)  # 30
    if type == 'family_name':
        result = re.sub(r"^D(?=H)", r'', result)  # 31
    result = re.sub(r"(?<=^[QWRTPSDFGHJKLZXCVBNM])H", r'', result)  # 32
    result = re.sub(r"(?<=[GT])H(?=.)", r'', result)  # 141
    result = re.sub(r"SH(?=.$)", r'SJ', result)  # 142
    if type != 'family_name':
        result = re.sub(r"(?<=[GT])H(?=..$)", r'', result)  # 133
    else:
        result = re.sub(r"(?<=[LNREYUIOA]G)H", r'', result)  # 33

    result = re.sub(r"(?<!^)D(?![EYUIOADHRW]|$)", r'T', result)  # 124

    if len(result) > 5:
        result = re.sub(r"^GUAL", r'WAL', result)  # 35
        result = re.sub(r"^GÜL", r'WIL', result)  # 35a

    if len(result) > 2:
        result = re.sub(r"^[IY](?=[æ±ÅÆAIYOûUÜÖ])", r'J', result)  # 125
    result = re.sub(r"I$", r'Y', result)  # 136
    result = re.sub(r"I(?=[EYUIOA])", r'Y', result)  # 138
    result = re.sub(r"I(?=[QWRTPSDFGHJKLZXCVBNM][EYUIOA])", r'Y', result)  # 139

    if len(result) > 2:
        result = re.sub(r"(.)(?=\1$)", r'', result)  # 38

    return result
