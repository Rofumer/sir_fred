; Sir Fred: Quality of Life Edition - patch master file.
;
; Assembled by tools/build.py with sjasmplus. The original 48K RAM image is
; loaded first, every patch overwrites only its own sites, and each site is
; guarded with EXPECT so a patch can never land on unexpected bytes.
; Feature switches and tuning values come in as -D defines (see qol.cfg);
; with every feature off the output equals the original byte for byte.

        DEVICE ZXSPECTRUM48
        ORG $4000
        INCBIN "../original/Sir_Fred_RAM_48K_verified.bin"

        MACRO EXPECT addr, val
            ASSERT {b addr} == val
        ENDM

        INCLUDE "symbols.asm"

        ; ---- defaults (overridden from qol.cfg) ----
        IFNDEF QOL_ROPE
QOL_ROPE        EQU 1
        ENDIF
        IFNDEF ROPE_FWD
ROPE_FWD        EQU 4
        ENDIF
        IFNDEF ROPE_BACK
ROPE_BACK       EQU 4
        ENDIF
        IFNDEF ROPE_ROWS
ROPE_ROWS       EQU 2
        ENDIF
        IFNDEF QOL_DESCEND
QOL_DESCEND     EQU 1
        ENDIF
        IFNDEF DESC_TOL
DESC_TOL        EQU 4
        ENDIF
        IFNDEF QOL_PICKUP
QOL_PICKUP      EQU 1
        ENDIF
        IFNDEF PICK_X
PICK_X          EQU 20
        ENDIF
        IFNDEF PICK_Y_LOW
PICK_Y_LOW      EQU 20
        ENDIF
        IFNDEF PICK_Y_HIGH
PICK_Y_HIGH     EQU 24
        ENDIF
        IFNDEF QOL_USE
QOL_USE         EQU 1
        ENDIF
        IFNDEF USE_TOL
USE_TOL         EQU 4
        ENDIF
        IFNDEF QOL_COYOTE
QOL_COYOTE      EQU 1
        ENDIF
        IFNDEF COYOTE_TICKS
COYOTE_TICKS    EQU 6
        ENDIF
        IFNDEF QOL_INERTIA
QOL_INERTIA     EQU 0
        ENDIF
        IFNDEF TURN_SPEED
TURN_SPEED      EQU 8
        ENDIF
        IFNDEF QOL_SWING
QOL_SWING       EQU 1
        ENDIF
        IFNDEF SWING_NO_DAMPING
SWING_NO_DAMPING        EQU 1
        ENDIF
        IFNDEF SWING_MAX_PHASE
SWING_MAX_PHASE         EQU 8
        ENDIF
        IFNDEF SWING_PUMP_CAP
SWING_PUMP_CAP          EQU 8
        ENDIF
        IFNDEF SWING_SPEED_THRESHOLD
SWING_SPEED_THRESHOLD   EQU 1
        ENDIF

F1_PTR = F1_START
F2_PTR = F2_START
F3_PTR = F3_START
F4_PTR = F4_START
F5_PTR = F5_START
I1_PTR = I1_START
I2_PTR = I2_START
I3_PTR = I3_START
I4_PTR = I4_START

        ; Coyote time lives partly in the bytes the rope patch frees. With
        ; QOL_ROPE=0 the scanner is installed in its exact-original mode
        ; (FWD=BACK=0, ROWS=1), proven identical by tests/test_rope.py.
        IF QOL_ROPE || QOL_COYOTE
            IF QOL_ROPE == 0
QR_FWD    EQU 0
QR_BACK   EQU 0
QR_ROWS   EQU 1
            ELSE
QR_FWD    EQU ROPE_FWD
QR_BACK   EQU ROPE_BACK
QR_ROWS   EQU ROPE_ROWS
            ENDIF
            INCLUDE "rope_grab.asm"
        ENDIF

        IF QOL_DESCEND
            INCLUDE "window_compact.asm"
            INCLUDE "vine_descend.asm"
        ENDIF

        INCLUDE "items.asm"

        IF QOL_COYOTE
            INCLUDE "coyote.asm"
        ENDIF

        IF QOL_INERTIA
            INCLUDE "inertia.asm"
        ENDIF

        IF QOL_SWING
            INCLUDE "rope_swing.asm"
        ENDIF

        ; ---- no block may overflow ----
        ASSERT F1_PTR <= F1_END
        ASSERT F2_PTR <= F2_END
        ASSERT F3_PTR <= F3_END
        ASSERT F4_PTR <= F4_END
        ASSERT F5_PTR <= F5_END
        ASSERT I1_PTR <= I1_END
        ASSERT I2_PTR <= I2_END
        ASSERT I3_PTR <= I3_END
        ASSERT I4_PTR <= I4_END

        SAVEBIN "../build/patched_ram.bin", $4000, $C000
