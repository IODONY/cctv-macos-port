# Clip Match Evaluation Report

- Clips manifest: `data/labels/clips.csv`
- Pair labels: `data/labels/pair_labels.csv`
- Evaluated pairs: `148`

## Summary

- Outcomes: `{'matched': 22, 'ambiguous': 97, 'no_match': 29}`
- Evaluation status: `{'correct': 51, 'uncertain': 97}`
- Same-camera weights: `{'top': 1.5, 'bottom': 0.9, 'bag': 0.8, 'is_long_sleeve': 0.6, 'is_long_pants': 0.4, 'torso_ratio': 1.0, 'brightness_ratio': 0.7}`
- Cross-camera weights: `{'top': 1.9, 'bottom': 0.35, 'bag': 0.7, 'is_long_sleeve': 0.45, 'is_long_pants': 0.25, 'torso_ratio': 1.25, 'brightness_ratio': 0.2}`

- Match threshold: `0.72`
- Ambiguous threshold: `0.25`
- Minimum available weight: `2.8`
- Allow provisional profiles: `True`

| pair_id | label | mode | outcome | score | available_weight | status | clip_a | clip_b |
| --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| pair_000001 | 1 | cross_camera | matched | 0.7901 | 5.1 | correct | person_001_cam_1_01 | person_001_cam_2_01 |
| pair_000002 | 1 | cross_camera | matched | 0.8207 | 5.1 | correct | person_001_cam_1_01 | person_001_cam_2_02 |
| pair_000003 | 1 | cross_camera | ambiguous | 0.2891 | 5.1 | uncertain | person_001_cam_1_02 | person_001_cam_2_01 |
| pair_000004 | 1 | cross_camera | ambiguous | 0.2532 | 5.1 | uncertain | person_001_cam_1_02 | person_001_cam_2_02 |
| pair_000005 | 1 | same_camera | ambiguous | 0.3091 | 5.9 | uncertain | person_001_cam_1_01 | person_001_cam_1_02 |
| pair_000006 | 1 | same_camera | ambiguous | 0.6765 | 5.9 | uncertain | person_001_cam_2_01 | person_001_cam_2_02 |
| pair_000007 | 1 | cross_camera | matched | 0.8725 | 5.1 | correct | person_002_cam_1_01 | person_002_cam_2_01 |
| pair_000008 | 1 | cross_camera | matched | 0.8725 | 5.1 | correct | person_002_cam_1_01 | person_002_cam_2_02 |
| pair_000009 | 1 | cross_camera | matched | 0.7219 | 5.1 | correct | person_002_cam_1_01 | person_002_cam_2_03 |
| pair_000010 | 1 | cross_camera | matched | 0.8109 | 5.1 | correct | person_002_cam_1_01 | person_002_cam_2_04 |
| pair_000011 | 1 | cross_camera | ambiguous | 0.6102 | 4.85 | uncertain | person_002_cam_1_01 | person_002_cam_3_01 |
| pair_000012 | 1 | cross_camera | matched | 0.7252 | 5.1 | correct | person_002_cam_1_01 | person_002_cam_4_01 |
| pair_000013 | 1 | cross_camera | ambiguous | 0.6242 | 4.85 | uncertain | person_002_cam_2_01 | person_002_cam_3_01 |
| pair_000014 | 1 | cross_camera | matched | 0.8013 | 5.1 | correct | person_002_cam_2_01 | person_002_cam_4_01 |
| pair_000015 | 1 | cross_camera | ambiguous | 0.6242 | 4.85 | uncertain | person_002_cam_2_02 | person_002_cam_3_01 |
| pair_000016 | 1 | cross_camera | matched | 0.8013 | 5.1 | correct | person_002_cam_2_02 | person_002_cam_4_01 |
| pair_000017 | 1 | cross_camera | matched | 0.7413 | 4.85 | correct | person_002_cam_2_03 | person_002_cam_3_01 |
| pair_000018 | 1 | cross_camera | ambiguous | 0.646 | 5.1 | uncertain | person_002_cam_2_03 | person_002_cam_4_01 |
| pair_000019 | 1 | cross_camera | ambiguous | 0.6337 | 4.85 | uncertain | person_002_cam_2_04 | person_002_cam_3_01 |
| pair_000020 | 1 | cross_camera | matched | 0.7408 | 5.1 | correct | person_002_cam_2_04 | person_002_cam_4_01 |
| pair_000021 | 1 | cross_camera | matched | 0.7609 | 4.85 | correct | person_002_cam_3_01 | person_002_cam_4_01 |
| pair_000022 | 1 | same_camera | matched | 1.0 | 5.9 | correct | person_002_cam_2_01 | person_002_cam_2_02 |
| pair_000023 | 1 | same_camera | matched | 0.7812 | 5.9 | correct | person_002_cam_2_01 | person_002_cam_2_03 |
| pair_000024 | 1 | same_camera | ambiguous | 0.7147 | 5.9 | uncertain | person_002_cam_2_01 | person_002_cam_2_04 |
| pair_000025 | 1 | same_camera | matched | 0.7812 | 5.9 | correct | person_002_cam_2_02 | person_002_cam_2_03 |
| pair_000026 | 1 | same_camera | ambiguous | 0.7147 | 5.9 | uncertain | person_002_cam_2_02 | person_002_cam_2_04 |
| pair_000027 | 1 | same_camera | ambiguous | 0.5602 | 5.9 | uncertain | person_002_cam_2_03 | person_002_cam_2_04 |
| pair_000028 | 1 | cross_camera | matched | 0.7215 | 5.1 | correct | person_003_cam_1_01 | person_003_cam_2_01 |
| pair_000029 | 1 | cross_camera | ambiguous | 0.282 | 5.1 | uncertain | person_003_cam_1_01 | person_003_cam_3_01 |
| pair_000030 | 1 | cross_camera | ambiguous | 0.3736 | 5.1 | uncertain | person_003_cam_1_01 | person_003_cam_4_01 |
| pair_000031 | 1 | cross_camera | matched | 0.8347 | 5.1 | correct | person_003_cam_1_02 | person_003_cam_2_01 |
| pair_000032 | 1 | cross_camera | ambiguous | 0.3664 | 5.1 | uncertain | person_003_cam_1_02 | person_003_cam_3_01 |
| pair_000033 | 1 | cross_camera | ambiguous | 0.3982 | 5.1 | uncertain | person_003_cam_1_02 | person_003_cam_4_01 |
| pair_000034 | 1 | cross_camera | matched | 0.7568 | 5.1 | correct | person_003_cam_1_03 | person_003_cam_2_01 |
| pair_000035 | 1 | cross_camera | ambiguous | 0.3002 | 5.1 | uncertain | person_003_cam_1_03 | person_003_cam_3_01 |
| pair_000036 | 1 | cross_camera | ambiguous | 0.4462 | 5.1 | uncertain | person_003_cam_1_03 | person_003_cam_4_01 |
| pair_000037 | 1 | cross_camera | matched | 0.7228 | 4.85 | correct | person_003_cam_1_04 | person_003_cam_2_01 |
| pair_000038 | 1 | cross_camera | ambiguous | 0.3052 | 4.85 | uncertain | person_003_cam_1_04 | person_003_cam_3_01 |
| pair_000039 | 1 | cross_camera | ambiguous | 0.3685 | 4.85 | uncertain | person_003_cam_1_04 | person_003_cam_4_01 |
| pair_000040 | 1 | cross_camera | ambiguous | 0.4221 | 5.1 | uncertain | person_003_cam_2_01 | person_003_cam_3_01 |
| pair_000041 | 1 | cross_camera | ambiguous | 0.4079 | 5.1 | uncertain | person_003_cam_2_01 | person_003_cam_4_01 |
| pair_000042 | 1 | cross_camera | ambiguous | 0.3096 | 5.1 | uncertain | person_003_cam_3_01 | person_003_cam_4_01 |
| pair_000043 | 1 | same_camera | ambiguous | 0.6548 | 5.9 | uncertain | person_003_cam_1_01 | person_003_cam_1_02 |
| pair_000044 | 1 | same_camera | matched | 0.8687 | 5.9 | correct | person_003_cam_1_01 | person_003_cam_1_03 |
| pair_000045 | 1 | same_camera | matched | 0.8885 | 5.5 | correct | person_003_cam_1_01 | person_003_cam_1_04 |
| pair_000046 | 1 | same_camera | ambiguous | 0.6648 | 5.9 | uncertain | person_003_cam_1_02 | person_003_cam_1_03 |
| pair_000047 | 1 | same_camera | ambiguous | 0.6284 | 5.5 | uncertain | person_003_cam_1_02 | person_003_cam_1_04 |
| pair_000048 | 1 | same_camera | matched | 0.9302 | 5.5 | correct | person_003_cam_1_03 | person_003_cam_1_04 |
| pair_000049 | 0 | same_camera | ambiguous | 0.3318 | 5.9 | uncertain | person_001_cam_1_01 | person_002_cam_1_01 |
| pair_000050 | 0 | same_camera | ambiguous | 0.2893 | 5.9 | uncertain | person_001_cam_1_01 | person_003_cam_1_01 |
| pair_000051 | 0 | same_camera | ambiguous | 0.4863 | 5.9 | uncertain | person_001_cam_1_01 | person_003_cam_1_02 |
| pair_000052 | 0 | same_camera | ambiguous | 0.3247 | 5.9 | uncertain | person_001_cam_1_01 | person_003_cam_1_03 |
| pair_000053 | 0 | same_camera | ambiguous | 0.25 | 5.5 | uncertain | person_001_cam_1_01 | person_003_cam_1_04 |
| pair_000054 | 0 | same_camera | ambiguous | 0.6104 | 5.9 | uncertain | person_001_cam_1_02 | person_002_cam_1_01 |
| pair_000055 | 0 | same_camera | ambiguous | 0.3738 | 5.9 | uncertain | person_001_cam_1_02 | person_003_cam_1_01 |
| pair_000056 | 0 | same_camera | ambiguous | 0.3797 | 5.9 | uncertain | person_001_cam_1_02 | person_003_cam_1_02 |
| pair_000057 | 0 | same_camera | ambiguous | 0.3628 | 5.9 | uncertain | person_001_cam_1_02 | person_003_cam_1_03 |
| pair_000058 | 0 | same_camera | ambiguous | 0.3196 | 5.5 | uncertain | person_001_cam_1_02 | person_003_cam_1_04 |
| pair_000059 | 0 | same_camera | ambiguous | 0.424 | 5.9 | uncertain | person_001_cam_2_01 | person_002_cam_2_01 |
| pair_000060 | 0 | same_camera | ambiguous | 0.424 | 5.9 | uncertain | person_001_cam_2_01 | person_002_cam_2_02 |
| pair_000061 | 0 | same_camera | no_match | 0.2865 | 5.9 | correct | person_001_cam_2_01 | person_002_cam_2_03 |
| pair_000062 | 0 | same_camera | ambiguous | 0.2988 | 5.9 | uncertain | person_001_cam_2_01 | person_002_cam_2_04 |
| pair_000063 | 0 | same_camera | no_match | 0.2472 | 5.9 | correct | person_001_cam_2_01 | person_003_cam_2_01 |
| pair_000064 | 0 | same_camera | ambiguous | 0.309 | 5.9 | uncertain | person_001_cam_2_02 | person_002_cam_2_01 |
| pair_000065 | 0 | same_camera | ambiguous | 0.309 | 5.9 | uncertain | person_001_cam_2_02 | person_002_cam_2_02 |
| pair_000066 | 0 | same_camera | no_match | 0.1573 | 5.9 | correct | person_001_cam_2_02 | person_002_cam_2_03 |
| pair_000067 | 0 | same_camera | ambiguous | 0.4592 | 5.9 | uncertain | person_001_cam_2_02 | person_002_cam_2_04 |
| pair_000068 | 0 | same_camera | ambiguous | 0.2878 | 5.9 | uncertain | person_001_cam_2_02 | person_003_cam_2_01 |
| pair_000069 | 0 | same_camera | ambiguous | 0.5201 | 5.9 | uncertain | person_002_cam_1_01 | person_003_cam_1_01 |
| pair_000070 | 0 | same_camera | ambiguous | 0.4697 | 5.9 | uncertain | person_002_cam_1_01 | person_003_cam_1_02 |
| pair_000071 | 0 | same_camera | ambiguous | 0.5405 | 5.9 | uncertain | person_002_cam_1_01 | person_003_cam_1_03 |
| pair_000072 | 0 | same_camera | ambiguous | 0.4935 | 5.5 | uncertain | person_002_cam_1_01 | person_003_cam_1_04 |
| pair_000073 | 0 | same_camera | ambiguous | 0.4656 | 5.9 | uncertain | person_002_cam_2_01 | person_003_cam_2_01 |
| pair_000074 | 0 | same_camera | ambiguous | 0.4656 | 5.9 | uncertain | person_002_cam_2_02 | person_003_cam_2_01 |
| pair_000075 | 0 | same_camera | no_match | 0.2888 | 5.9 | correct | person_002_cam_2_03 | person_003_cam_2_01 |
| pair_000076 | 0 | same_camera | ambiguous | 0.3608 | 5.9 | uncertain | person_002_cam_2_04 | person_003_cam_2_01 |
| pair_000077 | 0 | same_camera | no_match | 0.1683 | 5.5 | correct | person_002_cam_3_01 | person_003_cam_3_01 |
| pair_000078 | 0 | same_camera | ambiguous | 0.3714 | 5.9 | uncertain | person_002_cam_4_01 | person_003_cam_4_01 |
| pair_000079 | 0 | cross_camera | ambiguous | 0.4307 | 5.1 | uncertain | person_001_cam_1_01 | person_002_cam_2_01 |
| pair_000080 | 0 | cross_camera | ambiguous | 0.4307 | 5.1 | uncertain | person_001_cam_1_01 | person_002_cam_2_02 |
| pair_000081 | 0 | cross_camera | no_match | 0.2409 | 5.1 | correct | person_001_cam_1_01 | person_002_cam_2_03 |
| pair_000082 | 0 | cross_camera | ambiguous | 0.274 | 5.1 | uncertain | person_001_cam_1_01 | person_002_cam_2_04 |
| pair_000083 | 0 | cross_camera | no_match | 0.1448 | 4.85 | correct | person_001_cam_1_01 | person_002_cam_3_01 |
| pair_000084 | 0 | cross_camera | no_match | 0.3421 | 5.1 | correct | person_001_cam_1_01 | person_002_cam_4_01 |
| pair_000085 | 0 | cross_camera | ambiguous | 0.3427 | 5.1 | uncertain | person_001_cam_1_01 | person_003_cam_2_01 |
| pair_000086 | 0 | cross_camera | no_match | 0.2298 | 5.1 | correct | person_001_cam_1_01 | person_003_cam_3_01 |
| pair_000087 | 0 | cross_camera | ambiguous | 0.4118 | 5.1 | uncertain | person_001_cam_1_01 | person_003_cam_4_01 |
| pair_000088 | 0 | cross_camera | ambiguous | 0.6893 | 5.1 | uncertain | person_001_cam_1_02 | person_002_cam_2_01 |
| pair_000089 | 0 | cross_camera | ambiguous | 0.6893 | 5.1 | uncertain | person_001_cam_1_02 | person_002_cam_2_02 |
| pair_000090 | 0 | cross_camera | ambiguous | 0.5495 | 5.1 | uncertain | person_001_cam_1_02 | person_002_cam_2_03 |
| pair_000091 | 0 | cross_camera | ambiguous | 0.7072 | 5.1 | uncertain | person_001_cam_1_02 | person_002_cam_2_04 |
| pair_000092 | 0 | cross_camera | ambiguous | 0.5363 | 4.85 | uncertain | person_001_cam_1_02 | person_002_cam_3_01 |
| pair_000093 | 0 | cross_camera | ambiguous | 0.6485 | 5.1 | uncertain | person_001_cam_1_02 | person_002_cam_4_01 |
| pair_000094 | 0 | cross_camera | ambiguous | 0.3805 | 5.1 | uncertain | person_001_cam_1_02 | person_003_cam_2_01 |
| pair_000095 | 0 | cross_camera | ambiguous | 0.3263 | 5.1 | uncertain | person_001_cam_1_02 | person_003_cam_3_01 |
| pair_000096 | 0 | cross_camera | ambiguous | 0.34 | 5.1 | uncertain | person_001_cam_1_02 | person_003_cam_4_01 |
| pair_000097 | 0 | cross_camera | no_match | 0.2412 | 5.1 | correct | person_001_cam_2_01 | person_002_cam_1_01 |
| pair_000098 | 0 | cross_camera | no_match | 0.0745 | 4.85 | correct | person_001_cam_2_01 | person_002_cam_3_01 |
| pair_000099 | 0 | cross_camera | no_match | 0.279 | 5.1 | correct | person_001_cam_2_01 | person_002_cam_4_01 |
| pair_000100 | 0 | cross_camera | ambiguous | 0.2773 | 5.1 | uncertain | person_001_cam_2_01 | person_003_cam_1_01 |
| pair_000101 | 0 | cross_camera | ambiguous | 0.308 | 5.1 | uncertain | person_001_cam_2_01 | person_003_cam_1_02 |
| pair_000102 | 0 | cross_camera | ambiguous | 0.2522 | 5.1 | uncertain | person_001_cam_2_01 | person_003_cam_1_03 |
| pair_000103 | 0 | cross_camera | no_match | 0.2238 | 4.85 | correct | person_001_cam_2_01 | person_003_cam_1_04 |
| pair_000104 | 0 | cross_camera | no_match | 0.1771 | 5.1 | correct | person_001_cam_2_01 | person_003_cam_3_01 |
| pair_000105 | 0 | cross_camera | ambiguous | 0.2621 | 5.1 | uncertain | person_001_cam_2_01 | person_003_cam_4_01 |
| pair_000106 | 0 | cross_camera | ambiguous | 0.3603 | 5.1 | uncertain | person_001_cam_2_02 | person_002_cam_1_01 |
| pair_000107 | 0 | cross_camera | no_match | 0.2446 | 4.85 | correct | person_001_cam_2_02 | person_002_cam_3_01 |
| pair_000108 | 0 | cross_camera | no_match | 0.3629 | 5.1 | correct | person_001_cam_2_02 | person_002_cam_4_01 |
| pair_000109 | 0 | cross_camera | ambiguous | 0.3747 | 5.1 | uncertain | person_001_cam_2_02 | person_003_cam_1_01 |
| pair_000110 | 0 | cross_camera | ambiguous | 0.289 | 5.1 | uncertain | person_001_cam_2_02 | person_003_cam_1_02 |
| pair_000111 | 0 | cross_camera | ambiguous | 0.505 | 5.1 | uncertain | person_001_cam_2_02 | person_003_cam_1_03 |
| pair_000112 | 0 | cross_camera | ambiguous | 0.3879 | 4.85 | uncertain | person_001_cam_2_02 | person_003_cam_1_04 |
| pair_000113 | 0 | cross_camera | no_match | 0.2096 | 5.1 | correct | person_001_cam_2_02 | person_003_cam_3_01 |
| pair_000114 | 0 | cross_camera | ambiguous | 0.3832 | 5.1 | uncertain | person_001_cam_2_02 | person_003_cam_4_01 |
| pair_000115 | 0 | cross_camera | ambiguous | 0.4898 | 5.1 | uncertain | person_002_cam_1_01 | person_003_cam_2_01 |
| pair_000116 | 0 | cross_camera | ambiguous | 0.3517 | 5.1 | uncertain | person_002_cam_1_01 | person_003_cam_3_01 |
| pair_000117 | 0 | cross_camera | ambiguous | 0.4037 | 5.1 | uncertain | person_002_cam_1_01 | person_003_cam_4_01 |
| pair_000118 | 0 | cross_camera | ambiguous | 0.3498 | 5.1 | uncertain | person_002_cam_2_01 | person_003_cam_1_01 |
| pair_000119 | 0 | cross_camera | ambiguous | 0.5156 | 5.1 | uncertain | person_002_cam_2_01 | person_003_cam_1_02 |
| pair_000120 | 0 | cross_camera | ambiguous | 0.3874 | 5.1 | uncertain | person_002_cam_2_01 | person_003_cam_1_03 |
| pair_000121 | 0 | cross_camera | ambiguous | 0.3321 | 4.85 | uncertain | person_002_cam_2_01 | person_003_cam_1_04 |
| pair_000122 | 0 | cross_camera | ambiguous | 0.3359 | 5.1 | uncertain | person_002_cam_2_01 | person_003_cam_3_01 |
| pair_000123 | 0 | cross_camera | ambiguous | 0.4229 | 5.1 | uncertain | person_002_cam_2_01 | person_003_cam_4_01 |
| pair_000124 | 0 | cross_camera | ambiguous | 0.3498 | 5.1 | uncertain | person_002_cam_2_02 | person_003_cam_1_01 |
| pair_000125 | 0 | cross_camera | ambiguous | 0.5156 | 5.1 | uncertain | person_002_cam_2_02 | person_003_cam_1_02 |
| pair_000126 | 0 | cross_camera | ambiguous | 0.3874 | 5.1 | uncertain | person_002_cam_2_02 | person_003_cam_1_03 |
| pair_000127 | 0 | cross_camera | ambiguous | 0.3321 | 4.85 | uncertain | person_002_cam_2_02 | person_003_cam_1_04 |
| pair_000128 | 0 | cross_camera | ambiguous | 0.3359 | 5.1 | uncertain | person_002_cam_2_02 | person_003_cam_3_01 |
| pair_000129 | 0 | cross_camera | ambiguous | 0.4229 | 5.1 | uncertain | person_002_cam_2_02 | person_003_cam_4_01 |
| pair_000130 | 0 | cross_camera | no_match | 0.2012 | 5.1 | correct | person_002_cam_2_03 | person_003_cam_1_01 |
| pair_000131 | 0 | cross_camera | no_match | 0.4148 | 5.1 | correct | person_002_cam_2_03 | person_003_cam_1_02 |
| pair_000132 | 0 | cross_camera | no_match | 0.2251 | 5.1 | correct | person_002_cam_2_03 | person_003_cam_1_03 |
| pair_000133 | 0 | cross_camera | no_match | 0.1705 | 4.85 | correct | person_002_cam_2_03 | person_003_cam_1_04 |
| pair_000134 | 0 | cross_camera | no_match | 0.2462 | 5.1 | correct | person_002_cam_2_03 | person_003_cam_3_01 |
| pair_000135 | 0 | cross_camera | no_match | 0.247 | 5.1 | correct | person_002_cam_2_03 | person_003_cam_4_01 |
| pair_000136 | 0 | cross_camera | ambiguous | 0.5685 | 5.1 | uncertain | person_002_cam_2_04 | person_003_cam_1_01 |
| pair_000137 | 0 | cross_camera | ambiguous | 0.341 | 5.1 | uncertain | person_002_cam_2_04 | person_003_cam_1_02 |
| pair_000138 | 0 | cross_camera | ambiguous | 0.4522 | 5.1 | uncertain | person_002_cam_2_04 | person_003_cam_1_03 |
| pair_000139 | 0 | cross_camera | ambiguous | 0.4616 | 4.85 | uncertain | person_002_cam_2_04 | person_003_cam_1_04 |
| pair_000140 | 0 | cross_camera | ambiguous | 0.2783 | 5.1 | uncertain | person_002_cam_2_04 | person_003_cam_3_01 |
| pair_000141 | 0 | cross_camera | ambiguous | 0.3698 | 5.1 | uncertain | person_002_cam_2_04 | person_003_cam_4_01 |
| pair_000142 | 0 | cross_camera | no_match | 0.2196 | 4.85 | correct | person_002_cam_3_01 | person_003_cam_1_01 |
| pair_000143 | 0 | cross_camera | no_match | 0.1894 | 4.85 | correct | person_002_cam_3_01 | person_003_cam_1_02 |
| pair_000144 | 0 | cross_camera | no_match | 0.3292 | 4.85 | correct | person_002_cam_3_01 | person_003_cam_1_03 |
| pair_000145 | 0 | cross_camera | no_match | 0.2712 | 4.85 | correct | person_002_cam_3_01 | person_003_cam_1_04 |
| pair_000146 | 0 | cross_camera | no_match | 0.1982 | 4.85 | correct | person_002_cam_3_01 | person_003_cam_2_01 |
| pair_000147 | 0 | cross_camera | no_match | 0.2615 | 4.85 | correct | person_002_cam_3_01 | person_003_cam_4_01 |
| pair_000148 | 0 | cross_camera | ambiguous | 0.3487 | 5.1 | uncertain | person_002_cam_4_01 | person_003_cam_1_01 |
