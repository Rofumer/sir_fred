; ---------------------------------------------------------------------------
; Patch C: item pick-up tolerance                             (QOL_PICKUP)
;
; 9A32 (called from the pick-up key handler 99DB for every item in the room
; list at ($9981), 3-byte entries X,Y,type):
;     |FredX - itemX| < 16  and  itemY-FredY < 16 (item lower)
;                              /  FredY-itemY < 24 (item higher)
; Only the immediates change. PICK_Y_HIGH stays 24 by default: larger
; values could reach an item on a ledge above Fred's head.
; ---------------------------------------------------------------------------
        IF QOL_PICKUP
        ASSERT PICK_X >= 16 && PICK_X <= 24
        ASSERT PICK_Y_LOW >= 16 && PICK_Y_LOW <= 24
        ASSERT PICK_Y_HIGH >= 24 && PICK_Y_HIGH <= 28
        EXPECT $9A47, $FE
        EXPECT $9A48, $10
        EXPECT $9A50, $FE
        EXPECT $9A51, $10
        EXPECT $9A5B, $FE
        EXPECT $9A5C, $10
        EXPECT $9A64, $FE
        EXPECT $9A65, $18
        ORG $9A48
        db PICK_X                       ; item left of Fred
        ORG $9A51
        db PICK_X                       ; item right of Fred
        ORG $9A5C
        db PICK_Y_LOW                   ; item lower than Fred's top
        ORG $9A65
        db PICK_Y_HIGH                  ; item higher than Fred's top
        ENDIF

; ---------------------------------------------------------------------------
; Patch D: item USE tolerance                                 (QOL_USE)
;
; Item handlers (dispatched by type from the table at EB6E when FIRE is
; pressed) test "is Fred at the target" with the rectangle overlap
; B773 using Fred's box from B78F (X,Y,16x24). Only the four handlers that
; do this get a box grown by USE_TOL pixels on every side; enemy / hazard
; collisions (B7E2, BCBF, CD6F, ED54, ...) keep the original box.
;     5F10  item types 14 (CCE5 -> 5F00) and 11 (CBA5 -> 5F17 -> 5F0C)
;     5FD5  item type 7  (handler 68EE -> 6900 -> 5FCE)
;     6421  item type 10 (handler 6419)
;     64A6  item type 12 (handler 6494)
; ---------------------------------------------------------------------------
        IF QOL_USE
        ASSERT USE_TOL >= 1 && USE_TOL <= 6
        MACRO USE_SITE site
            EXPECT site, $CD
            EXPECT site+1, $8F
            EXPECT site+2, $B7
            ORG site+1
            dw qol_use_box
        ENDM
        USE_SITE $5F10
        USE_SITE $5FD5
        USE_SITE $6421
        USE_SITE $64A6

        ORG F1_PTR
qol_use_box:
        call FRED_BOX
        push bc
        ld bc,((256-USE_TOL-1) << 8) | (256-USE_TOL)
        add hl,bc                       ; X-TOL, Y-TOL (carry from L>=TOL)
        ex de,hl
        ld bc,((2*USE_TOL) << 8) | (2*USE_TOL)
        add hl,bc                       ; height+2*TOL, width+2*TOL
        ex de,hl
        pop bc
        ret
F1_PTR = $
        ENDIF
