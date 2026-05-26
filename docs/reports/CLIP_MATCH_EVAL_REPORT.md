# Clip Match Evaluation Report

- Clips manifest: `data/labels/clips.csv`
- Pair labels: `data/labels/pair_labels.csv`
- Evaluated pairs: `148`

## Summary

- Outcomes: `{'matched': 9, 'low_confidence': 93, 'ambiguous': 9, 'no_match': 37}`
- Evaluation status: `{'correct': 46, 'uncertain': 102}`
- Weights: `{'top': 1.4, 'bottom': 1.0, 'bag': 0.8, 'is_long_sleeve': 0.7, 'is_long_pants': 0.5, 'torso_ratio': 1.0, 'brightness_ratio': 0.8}`

- Match threshold: `0.75`
- Ambiguous threshold: `0.6`
- Allow provisional profiles: `True`

| pair_id | label | outcome | score | status | clip_a | clip_b |
| --- | --- | --- | ---: | --- | --- | --- |
| pair_000001 | 1 | matched | 0.8871 | correct | person_001_cam_1_01 | person_001_cam_2_01 |
| pair_000002 | 1 | matched | 0.7608 | correct | person_001_cam_1_01 | person_001_cam_2_02 |
| pair_000003 | 1 | low_confidence | 0.0 | uncertain | person_001_cam_1_02 | person_001_cam_2_01 |
| pair_000004 | 1 | low_confidence | 0.0 | uncertain | person_001_cam_1_02 | person_001_cam_2_02 |
| pair_000005 | 1 | low_confidence | 0.0 | uncertain | person_001_cam_1_01 | person_001_cam_1_02 |
| pair_000006 | 1 | matched | 0.785 | correct | person_001_cam_2_01 | person_001_cam_2_02 |
| pair_000007 | 1 | low_confidence | 0.0 | uncertain | person_002_cam_1_01 | person_002_cam_2_01 |
| pair_000008 | 1 | low_confidence | 0.0 | uncertain | person_002_cam_1_01 | person_002_cam_2_02 |
| pair_000009 | 1 | low_confidence | 0.0 | uncertain | person_002_cam_1_01 | person_002_cam_2_03 |
| pair_000010 | 1 | low_confidence | 0.0 | uncertain | person_002_cam_1_01 | person_002_cam_2_04 |
| pair_000011 | 1 | low_confidence | 0.0 | uncertain | person_002_cam_1_01 | person_002_cam_3_01 |
| pair_000012 | 1 | low_confidence | 0.0 | uncertain | person_002_cam_1_01 | person_002_cam_4_01 |
| pair_000013 | 1 | low_confidence | 0.0 | uncertain | person_002_cam_2_01 | person_002_cam_3_01 |
| pair_000014 | 1 | low_confidence | 0.0 | uncertain | person_002_cam_2_01 | person_002_cam_4_01 |
| pair_000015 | 1 | low_confidence | 0.0 | uncertain | person_002_cam_2_02 | person_002_cam_3_01 |
| pair_000016 | 1 | low_confidence | 0.0 | uncertain | person_002_cam_2_02 | person_002_cam_4_01 |
| pair_000017 | 1 | low_confidence | 0.0 | uncertain | person_002_cam_2_03 | person_002_cam_3_01 |
| pair_000018 | 1 | low_confidence | 0.0 | uncertain | person_002_cam_2_03 | person_002_cam_4_01 |
| pair_000019 | 1 | low_confidence | 0.0 | uncertain | person_002_cam_2_04 | person_002_cam_3_01 |
| pair_000020 | 1 | low_confidence | 0.0 | uncertain | person_002_cam_2_04 | person_002_cam_4_01 |
| pair_000021 | 1 | low_confidence | 0.0 | uncertain | person_002_cam_3_01 | person_002_cam_4_01 |
| pair_000022 | 1 | matched | 1.0 | correct | person_002_cam_2_01 | person_002_cam_2_02 |
| pair_000023 | 1 | matched | 0.8295 | correct | person_002_cam_2_01 | person_002_cam_2_03 |
| pair_000024 | 1 | matched | 0.7794 | correct | person_002_cam_2_01 | person_002_cam_2_04 |
| pair_000025 | 1 | matched | 0.8295 | correct | person_002_cam_2_02 | person_002_cam_2_03 |
| pair_000026 | 1 | matched | 0.7794 | correct | person_002_cam_2_02 | person_002_cam_2_04 |
| pair_000027 | 1 | ambiguous | 0.6267 | uncertain | person_002_cam_2_03 | person_002_cam_2_04 |
| pair_000028 | 1 | ambiguous | 0.6862 | uncertain | person_003_cam_1_01 | person_003_cam_2_01 |
| pair_000029 | 1 | low_confidence | 0.0 | uncertain | person_003_cam_1_01 | person_003_cam_3_01 |
| pair_000030 | 1 | low_confidence | 0.4677 | uncertain | person_003_cam_1_01 | person_003_cam_4_01 |
| pair_000031 | 1 | ambiguous | 0.7251 | uncertain | person_003_cam_1_02 | person_003_cam_2_01 |
| pair_000032 | 1 | low_confidence | 0.0 | uncertain | person_003_cam_1_02 | person_003_cam_3_01 |
| pair_000033 | 1 | low_confidence | 0.4849 | uncertain | person_003_cam_1_02 | person_003_cam_4_01 |
| pair_000034 | 1 | ambiguous | 0.6953 | uncertain | person_003_cam_1_03 | person_003_cam_2_01 |
| pair_000035 | 1 | low_confidence | 0.0 | uncertain | person_003_cam_1_03 | person_003_cam_3_01 |
| pair_000036 | 1 | low_confidence | 0.4388 | uncertain | person_003_cam_1_03 | person_003_cam_4_01 |
| pair_000037 | 1 | low_confidence | 0.0 | uncertain | person_003_cam_1_04 | person_003_cam_2_01 |
| pair_000038 | 1 | low_confidence | 0.0 | uncertain | person_003_cam_1_04 | person_003_cam_3_01 |
| pair_000039 | 1 | low_confidence | 0.0 | uncertain | person_003_cam_1_04 | person_003_cam_4_01 |
| pair_000040 | 1 | low_confidence | 0.0 | uncertain | person_003_cam_2_01 | person_003_cam_3_01 |
| pair_000041 | 1 | low_confidence | 0.4819 | uncertain | person_003_cam_2_01 | person_003_cam_4_01 |
| pair_000042 | 1 | low_confidence | 0.0 | uncertain | person_003_cam_3_01 | person_003_cam_4_01 |
| pair_000043 | 1 | matched | 0.7518 | correct | person_003_cam_1_01 | person_003_cam_1_02 |
| pair_000044 | 1 | ambiguous | 0.6801 | uncertain | person_003_cam_1_01 | person_003_cam_1_03 |
| pair_000045 | 1 | low_confidence | 0.0 | uncertain | person_003_cam_1_01 | person_003_cam_1_04 |
| pair_000046 | 1 | ambiguous | 0.705 | uncertain | person_003_cam_1_02 | person_003_cam_1_03 |
| pair_000047 | 1 | low_confidence | 0.0 | uncertain | person_003_cam_1_02 | person_003_cam_1_04 |
| pair_000048 | 1 | low_confidence | 0.0 | uncertain | person_003_cam_1_03 | person_003_cam_1_04 |
| pair_000049 | 0 | low_confidence | 0.0 | uncertain | person_001_cam_1_01 | person_002_cam_1_01 |
| pair_000050 | 0 | no_match | 0.3344 | correct | person_001_cam_1_01 | person_003_cam_1_01 |
| pair_000051 | 0 | no_match | 0.5462 | correct | person_001_cam_1_01 | person_003_cam_1_02 |
| pair_000052 | 0 | no_match | 0.3509 | correct | person_001_cam_1_01 | person_003_cam_1_03 |
| pair_000053 | 0 | low_confidence | 0.0 | uncertain | person_001_cam_1_01 | person_003_cam_1_04 |
| pair_000054 | 0 | low_confidence | 0.0 | uncertain | person_001_cam_1_02 | person_002_cam_1_01 |
| pair_000055 | 0 | low_confidence | 0.0 | uncertain | person_001_cam_1_02 | person_003_cam_1_01 |
| pair_000056 | 0 | low_confidence | 0.0 | uncertain | person_001_cam_1_02 | person_003_cam_1_02 |
| pair_000057 | 0 | low_confidence | 0.0 | uncertain | person_001_cam_1_02 | person_003_cam_1_03 |
| pair_000058 | 0 | low_confidence | 0.0 | uncertain | person_001_cam_1_02 | person_003_cam_1_04 |
| pair_000059 | 0 | no_match | 0.5007 | correct | person_001_cam_2_01 | person_002_cam_2_01 |
| pair_000060 | 0 | no_match | 0.5007 | correct | person_001_cam_2_01 | person_002_cam_2_02 |
| pair_000061 | 0 | no_match | 0.361 | correct | person_001_cam_2_01 | person_002_cam_2_03 |
| pair_000062 | 0 | no_match | 0.3776 | correct | person_001_cam_2_01 | person_002_cam_2_04 |
| pair_000063 | 0 | no_match | 0.3146 | correct | person_001_cam_2_01 | person_003_cam_2_01 |
| pair_000064 | 0 | no_match | 0.3473 | correct | person_001_cam_2_02 | person_002_cam_2_01 |
| pair_000065 | 0 | no_match | 0.3473 | correct | person_001_cam_2_02 | person_002_cam_2_02 |
| pair_000066 | 0 | no_match | 0.2048 | correct | person_001_cam_2_02 | person_002_cam_2_03 |
| pair_000067 | 0 | no_match | 0.5589 | correct | person_001_cam_2_02 | person_002_cam_2_04 |
| pair_000068 | 0 | no_match | 0.3252 | correct | person_001_cam_2_02 | person_003_cam_2_01 |
| pair_000069 | 0 | low_confidence | 0.0 | uncertain | person_002_cam_1_01 | person_003_cam_1_01 |
| pair_000070 | 0 | low_confidence | 0.0 | uncertain | person_002_cam_1_01 | person_003_cam_1_02 |
| pair_000071 | 0 | low_confidence | 0.0 | uncertain | person_002_cam_1_01 | person_003_cam_1_03 |
| pair_000072 | 0 | low_confidence | 0.0 | uncertain | person_002_cam_1_01 | person_003_cam_1_04 |
| pair_000073 | 0 | no_match | 0.4862 | correct | person_002_cam_2_01 | person_003_cam_2_01 |
| pair_000074 | 0 | no_match | 0.4862 | correct | person_002_cam_2_02 | person_003_cam_2_01 |
| pair_000075 | 0 | no_match | 0.3423 | correct | person_002_cam_2_03 | person_003_cam_2_01 |
| pair_000076 | 0 | no_match | 0.4368 | correct | person_002_cam_2_04 | person_003_cam_2_01 |
| pair_000077 | 0 | low_confidence | 0.0 | uncertain | person_002_cam_3_01 | person_003_cam_3_01 |
| pair_000078 | 0 | low_confidence | 0.0 | uncertain | person_002_cam_4_01 | person_003_cam_4_01 |
| pair_000079 | 0 | no_match | 0.5318 | correct | person_001_cam_1_01 | person_002_cam_2_01 |
| pair_000080 | 0 | no_match | 0.5318 | correct | person_001_cam_1_01 | person_002_cam_2_02 |
| pair_000081 | 0 | no_match | 0.4343 | correct | person_001_cam_1_01 | person_002_cam_2_03 |
| pair_000082 | 0 | no_match | 0.3337 | correct | person_001_cam_1_01 | person_002_cam_2_04 |
| pair_000083 | 0 | low_confidence | 0.0 | uncertain | person_001_cam_1_01 | person_002_cam_3_01 |
| pair_000084 | 0 | low_confidence | 0.0 | uncertain | person_001_cam_1_01 | person_002_cam_4_01 |
| pair_000085 | 0 | no_match | 0.36 | correct | person_001_cam_1_01 | person_003_cam_2_01 |
| pair_000086 | 0 | low_confidence | 0.0 | uncertain | person_001_cam_1_01 | person_003_cam_3_01 |
| pair_000087 | 0 | low_confidence | 0.4209 | uncertain | person_001_cam_1_01 | person_003_cam_4_01 |
| pair_000088 | 0 | low_confidence | 0.0 | uncertain | person_001_cam_1_02 | person_002_cam_2_01 |
| pair_000089 | 0 | low_confidence | 0.0 | uncertain | person_001_cam_1_02 | person_002_cam_2_02 |
| pair_000090 | 0 | low_confidence | 0.0 | uncertain | person_001_cam_1_02 | person_002_cam_2_03 |
| pair_000091 | 0 | low_confidence | 0.0 | uncertain | person_001_cam_1_02 | person_002_cam_2_04 |
| pair_000092 | 0 | low_confidence | 0.0 | uncertain | person_001_cam_1_02 | person_002_cam_3_01 |
| pair_000093 | 0 | low_confidence | 0.0 | uncertain | person_001_cam_1_02 | person_002_cam_4_01 |
| pair_000094 | 0 | low_confidence | 0.0 | uncertain | person_001_cam_1_02 | person_003_cam_2_01 |
| pair_000095 | 0 | low_confidence | 0.0 | uncertain | person_001_cam_1_02 | person_003_cam_3_01 |
| pair_000096 | 0 | low_confidence | 0.0 | uncertain | person_001_cam_1_02 | person_003_cam_4_01 |
| pair_000097 | 0 | low_confidence | 0.0 | uncertain | person_001_cam_2_01 | person_002_cam_1_01 |
| pair_000098 | 0 | low_confidence | 0.0 | uncertain | person_001_cam_2_01 | person_002_cam_3_01 |
| pair_000099 | 0 | low_confidence | 0.0 | uncertain | person_001_cam_2_01 | person_002_cam_4_01 |
| pair_000100 | 0 | no_match | 0.3592 | correct | person_001_cam_2_01 | person_003_cam_1_01 |
| pair_000101 | 0 | no_match | 0.4854 | correct | person_001_cam_2_01 | person_003_cam_1_02 |
| pair_000102 | 0 | no_match | 0.2986 | correct | person_001_cam_2_01 | person_003_cam_1_03 |
| pair_000103 | 0 | low_confidence | 0.0 | uncertain | person_001_cam_2_01 | person_003_cam_1_04 |
| pair_000104 | 0 | low_confidence | 0.0 | uncertain | person_001_cam_2_01 | person_003_cam_3_01 |
| pair_000105 | 0 | low_confidence | 0.4213 | uncertain | person_001_cam_2_01 | person_003_cam_4_01 |
| pair_000106 | 0 | low_confidence | 0.0 | uncertain | person_001_cam_2_02 | person_002_cam_1_01 |
| pair_000107 | 0 | low_confidence | 0.0 | uncertain | person_001_cam_2_02 | person_002_cam_3_01 |
| pair_000108 | 0 | low_confidence | 0.0 | uncertain | person_001_cam_2_02 | person_002_cam_4_01 |
| pair_000109 | 0 | no_match | 0.5418 | correct | person_001_cam_2_02 | person_003_cam_1_01 |
| pair_000110 | 0 | no_match | 0.3352 | correct | person_001_cam_2_02 | person_003_cam_1_02 |
| pair_000111 | 0 | no_match | 0.3053 | correct | person_001_cam_2_02 | person_003_cam_1_03 |
| pair_000112 | 0 | low_confidence | 0.0 | uncertain | person_001_cam_2_02 | person_003_cam_1_04 |
| pair_000113 | 0 | low_confidence | 0.0 | uncertain | person_001_cam_2_02 | person_003_cam_3_01 |
| pair_000114 | 0 | low_confidence | 0.409 | uncertain | person_001_cam_2_02 | person_003_cam_4_01 |
| pair_000115 | 0 | low_confidence | 0.0 | uncertain | person_002_cam_1_01 | person_003_cam_2_01 |
| pair_000116 | 0 | low_confidence | 0.0 | uncertain | person_002_cam_1_01 | person_003_cam_3_01 |
| pair_000117 | 0 | low_confidence | 0.0 | uncertain | person_002_cam_1_01 | person_003_cam_4_01 |
| pair_000118 | 0 | no_match | 0.454 | correct | person_002_cam_2_01 | person_003_cam_1_01 |
| pair_000119 | 0 | ambiguous | 0.6431 | uncertain | person_002_cam_2_01 | person_003_cam_1_02 |
| pair_000120 | 0 | no_match | 0.4365 | correct | person_002_cam_2_01 | person_003_cam_1_03 |
| pair_000121 | 0 | low_confidence | 0.0 | uncertain | person_002_cam_2_01 | person_003_cam_1_04 |
| pair_000122 | 0 | low_confidence | 0.0 | uncertain | person_002_cam_2_01 | person_003_cam_3_01 |
| pair_000123 | 0 | low_confidence | 0.5138 | uncertain | person_002_cam_2_01 | person_003_cam_4_01 |
| pair_000124 | 0 | no_match | 0.454 | correct | person_002_cam_2_02 | person_003_cam_1_01 |
| pair_000125 | 0 | ambiguous | 0.6431 | uncertain | person_002_cam_2_02 | person_003_cam_1_02 |
| pair_000126 | 0 | no_match | 0.4365 | correct | person_002_cam_2_02 | person_003_cam_1_03 |
| pair_000127 | 0 | low_confidence | 0.0 | uncertain | person_002_cam_2_02 | person_003_cam_1_04 |
| pair_000128 | 0 | low_confidence | 0.0 | uncertain | person_002_cam_2_02 | person_003_cam_3_01 |
| pair_000129 | 0 | low_confidence | 0.5138 | uncertain | person_002_cam_2_02 | person_003_cam_4_01 |
| pair_000130 | 0 | no_match | 0.3083 | correct | person_002_cam_2_03 | person_003_cam_1_01 |
| pair_000131 | 0 | no_match | 0.5206 | correct | person_002_cam_2_03 | person_003_cam_1_02 |
| pair_000132 | 0 | no_match | 0.3255 | correct | person_002_cam_2_03 | person_003_cam_1_03 |
| pair_000133 | 0 | low_confidence | 0.0 | uncertain | person_002_cam_2_03 | person_003_cam_1_04 |
| pair_000134 | 0 | low_confidence | 0.0 | uncertain | person_002_cam_2_03 | person_003_cam_3_01 |
| pair_000135 | 0 | low_confidence | 0.3565 | uncertain | person_002_cam_2_03 | person_003_cam_4_01 |
| pair_000136 | 0 | ambiguous | 0.6497 | uncertain | person_002_cam_2_04 | person_003_cam_1_01 |
| pair_000137 | 0 | no_match | 0.4382 | correct | person_002_cam_2_04 | person_003_cam_1_02 |
| pair_000138 | 0 | no_match | 0.4127 | correct | person_002_cam_2_04 | person_003_cam_1_03 |
| pair_000139 | 0 | low_confidence | 0.0 | uncertain | person_002_cam_2_04 | person_003_cam_1_04 |
| pair_000140 | 0 | low_confidence | 0.0 | uncertain | person_002_cam_2_04 | person_003_cam_3_01 |
| pair_000141 | 0 | low_confidence | 0.4716 | uncertain | person_002_cam_2_04 | person_003_cam_4_01 |
| pair_000142 | 0 | low_confidence | 0.0 | uncertain | person_002_cam_3_01 | person_003_cam_1_01 |
| pair_000143 | 0 | low_confidence | 0.0 | uncertain | person_002_cam_3_01 | person_003_cam_1_02 |
| pair_000144 | 0 | low_confidence | 0.0 | uncertain | person_002_cam_3_01 | person_003_cam_1_03 |
| pair_000145 | 0 | low_confidence | 0.0 | uncertain | person_002_cam_3_01 | person_003_cam_1_04 |
| pair_000146 | 0 | low_confidence | 0.0 | uncertain | person_002_cam_3_01 | person_003_cam_2_01 |
| pair_000147 | 0 | low_confidence | 0.0 | uncertain | person_002_cam_3_01 | person_003_cam_4_01 |
| pair_000148 | 0 | low_confidence | 0.0 | uncertain | person_002_cam_4_01 | person_003_cam_1_01 |
