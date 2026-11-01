; Addresses in the original Sir Fred image that the patches rely on.
; Every one of these was confirmed in the emulator (see docs/REVERSE_ENGINEERING.md).

; ---- Fred state ----------------------------------------------------------
FRED_X          EQU $8496       ; X, pixels (left edge of 16px sprite), step 2
FRED_Y          EQU $8497       ; Y, pixels (top of 24px sprite)
FRED_OLDX       EQU $8498       ; position the sprite is currently drawn at
FRED_SPEED      EQU $849B       ; horizontal momentum
FRED_AIR        EQU $849C       ; non-zero while airborne
FRED_DIR        EQU $84A7       ; facing: 0 = left, 1 = right
JUMP_VEL        EQU $8431       ; vertical speed (fixed point)
JUMP_RISING     EQU $8432       ; 1 while going up in a jump
FALL_TICKS      EQU $923A       ; ticks spent falling (fall damage at $14)
DESCEND_ANIM    EQU $923C       ; "climb down onto vine" animation counter
ROPE_ON         EQU $8719       ; non-zero while hanging on a rope / vine

; ---- engine routines -----------------------------------------------------
WINDOW          EQU $8751       ; build 4x5 cell window, HL = map ptr (row Y/8-1, col X/8-1)
KEY_UP          EQU $9FE1       ; redefinable key test "up/jump": Z = pressed
FRED_BOX        EQU $B78F       ; HL = Fred (X,Y), D = height, E = width
TICK_END        EQU $8206       ; common end of a game tick
JUMP_FROM_GROUND EQU $90E5      ; CALL $CC6F (start jump + sound) / XOR A / LD ($923A),A / JP $8206
AIR_HANDLER     EQU $90F5       ; per-tick airborne movement

ROOM_MAP        EQU $B3B0       ; 32x20 collision map, 1 byte per character cell
MAP_ROWS        EQU 20

; map cell bits
CELL_SOLID      EQU $01         ; bit 0: wall / floor
CELL_GRAB_MASK  EQU $C5         ; (cell & $C5) == $04 -> rope / vine cell
CELL_GRAB_VAL   EQU $04
CELL_VINE_TOP   EQU $44         ; cell above a vine you can climb down onto

; ---- free space (see docs, section "Свободная память") --------------------
; F1  8692..8706  dead stub 8692..869B (self-recursive, unreferenced) + 107 zeros
; F2  6509..6536  stale copy of the input dispatcher (unreferenced) + 4 zeros
; F3  67C8..67D5  freed by compacting the window builder tail 67B9..67D5
; F4  A21E..A22A  13 zeros between JP trampolines and the A22B target
; F5  E842..E850  unreachable CALL $E8DE + 12 zeros
; I1  87A4..87AC  original rope test, unreachable after patch A
; I2  87B2..87BB  original rope test, unreachable after patch A
; I3  8EA3..8EA9  unreachable fragment after JP $6CE8
; I4  9293..9299  unreachable fragment after JP $8206
F1_START EQU $8692
F1_END   EQU $8707
F2_START EQU $6509
F2_END   EQU $6537
F3_START EQU $67C8
F3_END   EQU $67D6
F4_START EQU $A21E
F4_END   EQU $A22B
F5_START EQU $E842
F5_END   EQU $E851
I1_START EQU $87A4
I1_END   EQU $87AD
I2_START EQU $87B2
I2_END   EQU $87BC
I3_START EQU $8EA3
I3_END   EQU $8EAA
I4_START EQU $9293
I4_END   EQU $929A
