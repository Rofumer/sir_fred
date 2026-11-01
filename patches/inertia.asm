; ---------------------------------------------------------------------------
; Patch F: turn-around skid threshold                         (QOL_INERTIA)
;
; Walking handlers 8E68 (right) / 8F28 (left):
;     LD A,($849B) / CP $08 / JR NC,...   ; speed >= 8: keep sliding on
; Holding the opposite direction only brakes while momentum >= 8.
; TURN_SPEED sets that threshold; 8 is the original value, a larger one
; lets Fred turn round sooner. Acceleration and top speed are untouched.
; ---------------------------------------------------------------------------
        ASSERT TURN_SPEED >= 1 && TURN_SPEED <= 32
        EXPECT $8EAA, $3A
        EXPECT $8EAD, $FE
        EXPECT $8EAE, $08
        EXPECT $8F6A, $3A
        EXPECT $8F6D, $FE
        EXPECT $8F6E, $08
        ORG $8EAE
        db TURN_SPEED
        ORG $8F6E
        db TURN_SPEED
