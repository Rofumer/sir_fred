; ---------------------------------------------------------------------------
; Support: compact the tail of the cell-window builder (frees F3 = 67C8..67D5)
;
; Original 67B9..67D5, reached only by JP $67B9 from 8794:
;     POP HL / POP BC / PUSH BC / LD IX,$841B / LD A,C / CP 8 / LD DE,4
;     LD B,5 / POP BC / LD IX,$841B / LD A,B / CP 8 / LD DE,1 / LD B,4 / RET
; The middle part is overwritten before use; the net result is
;     HL = map ptr, BC = (4, X), IX = $841B, A = Y, flags of CP 8, DE = 1.
; The replacement produces exactly the same registers, flags and SP.
; Verified for every X,Y by tests/test_window.py.
; ---------------------------------------------------------------------------

        EXPECT $67B9, $E1
        EXPECT $67BA, $C1
        EXPECT $67BB, $C5
        EXPECT $67BC, $DD
        EXPECT $67C8, $C1
        EXPECT $67C9, $DD
        EXPECT $67D3, $06
        EXPECT $67D4, $04
        EXPECT $67D5, $C9
        EXPECT $67D6, $DD               ; next routine (67D6..67DE) kept
        ORG $67B9
        pop hl
        pop bc
        ld ix,$841B
        ld a,b
        cp 8
        ld de,1
        ld b,4
        ret
        ASSERT $ == F3_START
        ; fill the freed bytes with the original values until used
