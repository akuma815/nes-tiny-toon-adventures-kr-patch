; Replaces FE8C..FEB1 in the COPIED final fixed PRG bank only.
; Original NMI already saves/restores A/X/Y and P via RTI.
; No shared RAM. Mask IRQ while temporarily mapping the selector at A000.
    LDY $57
    BEQ @DONE
    PHP
    SEI
    LDX $8000
    INX
    TXA
    PHA
    LDA #@SELECTOR_BANK
    STA $A000
    JSR @SELECTOR_ENTRY
    PLA
    STA $A000
    PLP
DONE:
    RTS
