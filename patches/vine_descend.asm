; ---------------------------------------------------------------------------
; Patch B: tolerant "climb down onto a vine" with position correction
;                                                          (QOL_DESCEND)
; Original 964F (pressing DOWN while standing):
;     CALL $8751 / LD B,(IX+$0D) or (IX+$0F) / LD A,B / CP $44 / RET NZ
;     LD A,$96 / LD ($923C),A          ; start the descend animation
; i.e. ONE cell at the feet row: column X/8 facing left, (X+16)/8 facing
; right. The window is 8px wide and the ledge edge leaves even less room.
;
; New: probe pixels edge-DESC_TOL .. edge+DESC_TOL (step 2, the X step).
; On a hit at offset d the first animation step (9689) is told to behave
; as if Fred stood at X+d: it already snaps X to the cell grid, so the
; whole descent - and the vine grab at its end - is the original one,
; started from the corrected position. The sprite erase uses the true old
; position, so no artefacts. DESC_TOL = 0 gives the original behaviour.
; ---------------------------------------------------------------------------

        ASSERT DESC_TOL >= 0 && DESC_TOL <= 6 && (DESC_TOL & 1) == 0

        ; --- 964F..9668 (26 bytes, entire original routine) ---------------
        EXPECT $964F, $CD               ; CALL $8751
        EXPECT $9660, $FE               ; CP $44
        EXPECT $9661, $44
        EXPECT $9668, $C9               ; RET
        EXPECT $9669, $3A               ; LD A,($923C) - animation, kept
        ORG $964F
qol_descend:
        call WINDOW                     ; HL = map ptr (row Y/8-1, col X/8-1)
        ld de,96
        add hl,de                       ; feet row Y/8+2
        ld a,(FRED_DIR)
        neg
        and 16                          ; right: test the cell past X+16
        ld c,a
        ld a,(FRED_X)
        and 7
        add a,c
        add a,8-DESC_TOL                ; first probe, relative to column X/8-1
        jp qol_descend2
        ASSERT $ == $9669

        ORG F2_PTR
qol_descend2:
        ld c,a
        ld b,DESC_TOL+1
.lp:    ld a,c
        rrca
        rrca
        rrca
        and $1F
        add a,l
        ld e,a
        ld a,h
        adc a,0
        ld d,a
        ld a,(de)
        cp CELL_VINE_TOP
        jr z,.hit
        inc c
        inc c
        djnz .lp
        ret
.hit:   ld a,b                          ; offset = TOL + 2 - 2*B
        add a,a
        neg
        add a,DESC_TOL+2
        ld (qol_desc_dx),a
        ld a,$96
        ld (DESCEND_ANIM),a
        ret
F2_PTR = $

        ; --- 969D: first animation step, X snap --------------------------
        ; 9691 LD HL,($8496) / LD ($8498),HL / LD A,L / JR Z,+3 / ADD A,8
        ; 969D AND $F8 / LD L,A / LD ($8496),HL
        EXPECT $969D, $E6
        EXPECT $969E, $F8
        EXPECT $969F, $6F
        EXPECT $96A0, $22
        ORG $969D
        call qol_desc_fix

        ORG F3_PTR
qol_desc_fix:
        push hl
        ld hl,qol_desc_dx
        add a,(hl)                      ; apply the correction once
        ld (hl),0
        pop hl
        and $F8                         ; original
        ld l,a
        ret
qol_desc_dx:
        db 0
F3_PTR = $
