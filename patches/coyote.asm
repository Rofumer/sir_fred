; ---------------------------------------------------------------------------
; Patch E: coyote time                                        (QOL_COYOTE)
;
; Walking off a ledge goes through 828D: JUMP_VEL=$20, FRED_AIR=$20,
; speed/4, JUMP_RISING=0, X nudged 6-8px forward. From then on the main
; loop sends every tick to the airborne handler (EAC3 -> ... -> JP $90F5)
; and the jump key is ignored.
;
; New: 828D also loads a counter with COYOTE_TICKS. While it runs, a jump
; key press during the fall starts a normal jump (the ground-jump code at
; 90E5: CALL $CC6F / fall counter reset / JP $8206). Speed is multiplied
; by 4 first, undoing the walk-off division, so the jump carries the same
; momentum as one started on the ledge. Every ground tick (EAD7) clears the
; counter, so it can never leak into a later fall.
;
; The airborne part is split over several tiny free areas (I1..I4, F1, F5)
; joined by JPs - the game has no larger free block left.
; ---------------------------------------------------------------------------

        ASSERT COYOTE_TICKS >= 1 && COYOTE_TICKS <= 16

        ; --- 828D walk-off: arm the counter ------------------------------
        EXPECT $828D, $3E
        EXPECT $828E, $20
        EXPECT $828F, $32
        EXPECT $8290, $31
        EXPECT $8291, $84
        ORG $828D
        call qol_walkoff
        nop
        nop

        ORG F4_PTR
qol_walkoff:
        ld a,COYOTE_TICKS
        ld (qol_coyote),a
        ld a,$20                        ; original
        ld (JUMP_VEL),a
        ret
qol_coyote:
        db 0
F4_PTR = $

        ; --- EAD7 ground tick: XOR A / LD ($923A),A ----------------------
        EXPECT $EAD7, $AF
        EXPECT $EAD8, $32
        EXPECT $EAD9, $3A
        EXPECT $EADA, $92
        ORG $EAD7
        call qol_ground
        nop

        ORG F1_PTR
qol_ground:
        xor a
        ld (FALL_TICKS),a               ; original
        ld (qol_coyote),a
        ret
F1_PTR = $

        ; --- EAD4 airborne tick: JP $90F5 ---------------------------------
        EXPECT $EAD4, $C3
        EXPECT $EAD5, $F5
        EXPECT $EAD6, $90
        ORG $EAD4
        jp qol_air1

        ORG F5_PTR
qol_air1:
        ld a,(qol_coyote)
        and a
        jp z,AIR_HANDLER
        dec a
        ld (qol_coyote),a
        jp qol_air2
F5_PTR = $

        ORG I2_PTR
qol_air2:
        ld a,(JUMP_RISING)
        and a
        jp nz,AIR_HANDLER
        jp qol_air3
I2_PTR = $

        ORG I1_PTR
qol_air3:
        call KEY_UP
        jp nz,AIR_HANDLER
        jp qol_air4
I1_PTR = $

        ORG F1_PTR
qol_air4:
        xor a
        ld (qol_coyote),a
        jp qol_air5
F1_PTR = $

        ORG I3_PTR
qol_air5:
        ld a,(FRED_SPEED)
        add a,a
        jp qol_air6
I3_PTR = $

        ORG I4_PTR
qol_air6:
        add a,a                         ; speed * 4 (<= 252: walk-off left <= 63)
        ld (FRED_SPEED),a
        jp JUMP_FROM_GROUND
I4_PTR = $
