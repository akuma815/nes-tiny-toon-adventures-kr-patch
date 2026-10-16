; Two entry points within the original 38-byte FE8C routine in copied bank31.
; Mode/result lives on stack; helper bank17 runs at 8000, data bank18 at A000.
FONT_ENTRY:
    LDY $57
    BEQ @RETURN
    LDA #$00
    BEQ @COMMON
READ_ENTRY:
    LDA #$01
COMMON:
    PHP
    SEI
    PHA
    LDA $8000
    PHA
    LDA #$11
    STA $8000
    JSR $8001
    PLA
    STA $8000
    BCC @POP_RESULT
    JSR $D1FF
POP_RESULT:
    PLA
    PLP
RETURN:
    RTS
