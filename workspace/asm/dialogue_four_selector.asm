; Standalone PRG bank 17, CPU A000. Y is the native dialogue-mode flag.
; BF/C0 are the common script base; 07A9 is its original reader cursor.
; Switch only AFTER first glyph of a new page is consumed, after F9 clearing.
    LDA $BF
    CMP #@COMMON_LOW
    BNE @RETURNED
    LDA $C0
    CMP #@COMMON_HIGH
    BEQ @COMMON_MATCH
    JMP @ORIGINAL
COMMON_MATCH:
    LDA $07A9
    CMP #@THIRD_THRESHOLD
    BCS @PAGE_THREE
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
RETURNED:
    ; F3 resumes six caller bases at cursor 1, then FA or F7 46/F9.
    ; Preserve page 3 through wait and clearing; release after next glyph.
    LDA $C0
    CMP #@COMMON_HIGH
    BNE @ORIGINAL
    LDA $BF
    CMP #$FB
    BNE @RETURN_COMMON
    LDA $07A9
    CMP #$03
    BCC @PAGE_THREE
    LDA #$06
    LDX #$08
    STA $B000
    STX $B004
    LDA #$07
    LDX #$08
    JMP @WRITE_SECOND
RETURN_COMMON:
    LDA $07A9
    CMP #$05
    BCS @ORIGINAL
    LDA $BF
    CMP #$18
    BEQ @PAGE_THREE
    CMP #$1C
    BEQ @PAGE_THREE
    CMP #$45
    BEQ @PAGE_THREE
    CMP #$6E
    BEQ @PAGE_THREE
    CMP #$93
    BEQ @PAGE_THREE
    CMP #$97
    BNE @ORIGINAL
PAGE_THREE:
    LDA #$04
    LDX #$08
    STA $B000
    STX $B004
    LDA #$05
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
