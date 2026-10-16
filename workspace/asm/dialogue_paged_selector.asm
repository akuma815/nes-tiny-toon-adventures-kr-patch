; Standalone PRG bank 17, CPU A000. Y is the native dialogue-mode flag.
; BF/C0 are the common script base; 07A9 is its original reader cursor.
; Switch only AFTER first glyph of a new page is consumed, after F9 clearing.
    LDA $BF
    CMP #@COMMON_LOW
    BNE @ORIGINAL
    LDA $C0
    CMP #@COMMON_HIGH
    BNE @ORIGINAL
    LDA $07A9
    CMP #@THIRD_THRESHOLD
    BCS @ORIGINAL
    CMP #@SECOND_THRESHOLD
    BCS @PAGE_TWO
PAGE_ONE:
    LDA #$00
    LDX #$08
    STA $B000
    STX $B004
    LDA #$01
    LDX #$08
    JMP @WRITE_SECOND
PAGE_TWO:
    LDA #$02
    LDX #$08
    STA $B000
    STX $B004
    LDA #$03
    LDX #$08
    JMP @WRITE_SECOND
ORIGINAL:
    LDA #$08
    LDX #$07
    STA $B000
    STX $B004
    LDA #$0A
    LDX #$06
WRITE_SECOND:
    STA $B008
    STX $B00C
    DEY
    BEQ @DONE
    LDA #$09
    LDX #$07
    STA $C008
    STX $C00C
DONE:
    RTS
