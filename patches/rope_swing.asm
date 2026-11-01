; ---------------------------------------------------------------------------
; Patch G: rope swing simplification                          (QOL_SWING)
;
; The original rope is a damped pendulum: each reversal consumes the "life"
; counter in ROPE_TABLE+6, so the swing dies out quickly and the player has
; very little time to jump to a neighbouring ledge.  This patch makes the
; swing persistent and/or more powerful.
;
; All changes are single-byte or short-sequence patches; every feature can be
; switched off individually, and with all switches off the build equals the
; original.
; ---------------------------------------------------------------------------

        IF QOL_SWING

        ; ---- G1: remove damping -------------------------------------------
        ; At $888E the update routine does DEC (IX+$06) when the swing turns
        ; around while the phase is still small.  NOP it out and the rope
        ; keeps swinging forever (or until Fred falls off).
        IF SWING_NO_DAMPING
            EXPECT $888E, $DD
            EXPECT $888F, $35
            EXPECT $8890, $06
            ORG $888E
            nop
            nop
            nop
        ENDIF

        ; ---- G2: raise the initial phase cap -------------------------------
        ; On landing on a rope with speed, $89DE..$8A36 computes a starting
        ; phase and clamps it to 5.  A larger phase lets the amplitude climb
        ; higher before turning back.  The shape table at $C9E7 only has 8
        ; valid entries (0..7), so the safe maximum phase is 8 (giving max
        ; amplitude 7).  The original code is:
        ;   $8A1A: CP $06      ; if phase+B >= 6
        ;   $8A1E: LD A,$05    ; clamp to 5
        IF SWING_MAX_PHASE != 5
            ASSERT SWING_MAX_PHASE >= 1 && SWING_MAX_PHASE <= 8
            EXPECT $8A1A, $FE
            EXPECT $8A1B, $06
            EXPECT $8A1E, $3E
            EXPECT $8A1F, $05
            ORG $8A1A
            cp SWING_MAX_PHASE + 1
            ORG $8A1E
            ld a, SWING_MAX_PHASE
        ENDIF

        ; ---- G3: raise the manual-pump cap ---------------------------------
        ; Pressing left/right on the rope can increase the phase, but the
        ; original caps it at 7 (CP $08 after INC A).  Raise the cap to match
        ; SWING_MAX_PHASE.
        IF SWING_PUMP_CAP != 7
            ASSERT SWING_PUMP_CAP >= 1 && SWING_PUMP_CAP <= 8
            EXPECT $8B14, $FE
            EXPECT $8B15, $08
            ORG $8B14
            cp SWING_PUMP_CAP + 1
        ENDIF

        ; ---- G4: lower the speed threshold for starting a swing ------------
        ; $89DE checks FRED_SPEED >= $0A before it will start the swing at
        ; all.  Lowering it (e.g. to 1) makes the rope swing even after a
        ; slow grab.
        IF SWING_SPEED_THRESHOLD != 10
            ASSERT SWING_SPEED_THRESHOLD >= 1 && SWING_SPEED_THRESHOLD <= 255
            EXPECT $89E1, $FE
            EXPECT $89E2, $0A
            ORG $89E1
            cp SWING_SPEED_THRESHOLD
        ENDIF

        ENDIF
