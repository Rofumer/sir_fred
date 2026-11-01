; ---------------------------------------------------------------------------
; Patch A: tolerant rope / vine grab                          (QOL_ROPE)
;
; Original 879A..87BB (called every game tick while Fred is airborne):
;     CALL $8751            ; cell window around Fred, HL = map pointer
;     LD A,($84A7) ...      ; pick window offset 7 (right) or 5 (left) and
;     LD ($87B4),A          ;   self-modify the next instruction
;     LD A,(IX+n)           ; ONE map cell: row Y/8, column (X+16)/8 or X/8
;     LD C,A / AND $C5 / CP $04 / JR NZ,$87AD
; X moves in 2px steps, so the rope is caught only in an 8px window
; (4 positions) - the main source of "pixel hunting".
;
; New: scan pixel by pixel from (edge - ROPE_BACK) to (edge + ROPE_FWD),
; edge = X+16 facing right or X facing left, in ROPE_ROWS character rows
; from the head row down. The scan runs outward from Fred and stops at the
; first solid cell, so ropes behind walls are never grabbed. Addressing is
; relative to the map pointer returned by $8751 (row Y/8-1, column X/8-1),
; exactly like the game's own window. With ROPE_FWD = ROPE_BACK = 0 and
; ROPE_ROWS = 1 the result is identical to the original test.
;
; Everything after a successful test (87BC..) is original code: it picks
; the rope segment by Y and snaps Fred onto the rope, so the wider window
; never leaves Fred hanging in the air.
; ---------------------------------------------------------------------------

        ASSERT QR_FWD >= 0 && QR_FWD <= 8
        ASSERT QR_BACK >= 0 && QR_BACK <= 8
        ASSERT QR_ROWS >= 1 && QR_ROWS <= 3

        EXPECT $879A, $CD               ; CALL $8751
        EXPECT $879D, $3A               ; LD A,($84A7)
        EXPECT $87A8, $32               ; LD ($87B4),A
        EXPECT $87AB, $18               ; JR $87B2
        EXPECT $87AD, $AF               ; XOR A        (kept: "no rope" exit)
        EXPECT $87B2, $DD               ; LD A,(IX+n)
        EXPECT $87BA, $20               ; JR NZ,$87AD
        EXPECT $87BC, $3E               ; LD A,$01     (grab path, kept)
        ORG $879D
        call qol_rope_scan              ; Z and C = cell value if grabbable
        jr nz,$87AD
        jr $87BC
        ASSERT $ == I1_START            ; 87A4..87AC and 87B2..87BB now unused

        ORG F1_PTR
qol_rope_scan:                          ; HL = map ptr from $8751
        ld de,32
        add hl,de                       ; head row, column X/8-1
        ld a,(FRED_DIR)
        neg                             ; 0 / $FF
        and 24-QR_BACK-8-QR_BACK    ; right: +16-2*BACK relative to left
        add a,8+QR_BACK               ; left start: (X&7)+8+BACK
        ld c,a
        ld a,(FRED_X)
        and 7
        add a,c
        ld c,a                          ; C = first pixel (relative)
        ld a,(FRED_DIR)
        and a
        ld d,$FF                        ; step -1 (facing left: outward = left)
        jr z,.go
        ld d,1                          ; step +1
.go:    ld b,QR_ROWS
.row:   push bc
        push hl
        ld b,QR_BACK+QR_FWD+1
.px:    push hl
        ld a,c
        rrca
        rrca
        rrca
        and $1F
        add a,l
        ld l,a
        jr nc,.nc
        inc h
.nc:    ld e,(hl)
        pop hl
        ld a,e
        and CELL_GRAB_MASK
        cp CELL_GRAB_VAL
        jr z,.found
        bit 0,e                         ; CELL_SOLID: wall between Fred and rope
        jr nz,.next
        ld a,c
        add a,d
        ld c,a
        djnz .px
.next:  pop hl
        pop bc
        ld a,l
        add a,32
        ld l,a
        jr nc,.nc2
        inc h
.nc2:   djnz .row
        or 1                            ; NZ: nothing to grab
        ret
.found: pop hl
        pop hl
        ld c,e                          ; C = rope cell (87BC.. needs it)
        cp a                            ; Z
        ret
F1_PTR = $
