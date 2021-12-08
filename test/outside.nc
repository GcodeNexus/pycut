G21         ; Set units to mm
G90         ; Absolute positioning
G1 Z2.54 F2540      ; Move to clearance level

; Start the spindle
M3 S1000

;
; Operation:    0
; Name:         op3
; Type:         Outside
; Paths:        1
; Direction:    Conventional
; Cut Depth:    3.175
; Pass Depth:   3.175
; Plunge rate:  127
; Cut rate:     1016
;

; Path 0
; Rapid to initial position
G1 X39.9999 Y-18.4125 F2540
G1 Z0.0000
; ramp
G1 X20.0000 Y-18.4125 Z-1.5875 F1016.0000
G1 X39.9999 Y-18.4125 Z-3.1750
; cut
G1 X20.0000 Y-18.4125 F1016
G1 X19.9311 Y-18.4140
G1 X19.8415 Y-18.4203
G1 X19.7526 Y-18.4318
G1 X19.6642 Y-18.4483
G1 X19.5770 Y-18.4699
G1 X19.4912 Y-18.4963
G1 X19.4069 Y-18.5273
G1 X19.3246 Y-18.5633
G1 X19.2446 Y-18.6037
G1 X19.1668 Y-18.6487
G1 X19.0917 Y-18.6980
G1 X19.0195 Y-18.7513
G1 X18.9504 Y-18.8087
G1 X18.8849 Y-18.8702
G1 X18.8227 Y-18.9349
G1 X18.7645 Y-19.0033
G1 X18.7101 Y-19.0746
G1 X18.6599 Y-19.1491
G1 X18.6139 Y-19.2263
G1 X18.5722 Y-19.3058
G1 X18.5354 Y-19.3876
G1 X18.5031 Y-19.4714
G1 X18.4755 Y-19.5570
G1 X18.4528 Y-19.6439
G1 X18.4353 Y-19.7317
G1 X18.4226 Y-19.8206
G1 X18.4150 Y-19.9103
G1 X18.4125 Y-20.0000
G1 X18.4125 Y-39.9999
G1 X18.4140 Y-40.0688
G1 X18.4203 Y-40.1584
G1 X18.4318 Y-40.2473
G1 X18.4483 Y-40.3357
G1 X18.4699 Y-40.4228
G1 X18.4963 Y-40.5087
G1 X18.5273 Y-40.5930
G1 X18.5633 Y-40.6753
G1 X18.6037 Y-40.7553
G1 X18.6487 Y-40.8330
G1 X18.6980 Y-40.9082
G1 X18.7513 Y-40.9804
G1 X18.8087 Y-41.0494
G1 X18.8702 Y-41.1150
G1 X18.9349 Y-41.1772
G1 X19.0033 Y-41.2354
G1 X19.0746 Y-41.2897
G1 X19.1491 Y-41.3400
G1 X19.2263 Y-41.3860
G1 X19.3058 Y-41.4277
G1 X19.3876 Y-41.4645
G1 X19.4714 Y-41.4967
G1 X19.5570 Y-41.5244
G1 X19.6439 Y-41.5470
G1 X19.7317 Y-41.5646
G1 X19.8206 Y-41.5773
G1 X19.9103 Y-41.5849
G1 X20.0000 Y-41.5874
G1 X39.9999 Y-41.5874
G1 X40.0688 Y-41.5859
G1 X40.1584 Y-41.5795
G1 X40.2473 Y-41.5681
G1 X40.3357 Y-41.5516
G1 X40.4228 Y-41.5300
G1 X40.5087 Y-41.5036
G1 X40.5930 Y-41.4726
G1 X40.6753 Y-41.4365
G1 X40.7553 Y-41.3962
G1 X40.8330 Y-41.3512
G1 X40.9082 Y-41.3019
G1 X40.9804 Y-41.2486
G1 X41.0494 Y-41.1912
G1 X41.1150 Y-41.1297
G1 X41.1772 Y-41.0649
G1 X41.2354 Y-40.9966
G1 X41.2897 Y-40.9252
G1 X41.3400 Y-40.8508
G1 X41.3860 Y-40.7736
G1 X41.4277 Y-40.6941
G1 X41.4645 Y-40.6123
G1 X41.4967 Y-40.5285
G1 X41.5244 Y-40.4429
G1 X41.5470 Y-40.3560
G1 X41.5646 Y-40.2681
G1 X41.5773 Y-40.1792
G1 X41.5849 Y-40.0896
G1 X41.5874 Y-39.9999
G1 X41.5874 Y-20.0000
G1 X41.5859 Y-19.9311
G1 X41.5795 Y-19.8415
G1 X41.5681 Y-19.7526
G1 X41.5516 Y-19.6642
G1 X41.5300 Y-19.5770
G1 X41.5036 Y-19.4912
G1 X41.4726 Y-19.4069
G1 X41.4365 Y-19.3246
G1 X41.3962 Y-19.2446
G1 X41.3512 Y-19.1668
G1 X41.3019 Y-19.0917
G1 X41.2486 Y-19.0195
G1 X41.1912 Y-18.9504
G1 X41.1297 Y-18.8849
G1 X41.0649 Y-18.8227
G1 X40.9966 Y-18.7645
G1 X40.9252 Y-18.7101
G1 X40.8508 Y-18.6599
G1 X40.7736 Y-18.6139
G1 X40.6941 Y-18.5722
G1 X40.6123 Y-18.5354
G1 X40.5285 Y-18.5031
G1 X40.4429 Y-18.4755
G1 X40.3560 Y-18.4528
G1 X40.2681 Y-18.4353
G1 X40.1792 Y-18.4226
G1 X40.0896 Y-18.4150
G1 X39.9999 Y-18.4125
; Retract
G1 Z2.5400 F2540 

; Stop the spindle
M5 