
#Requires AutoHotkey v2.0

LControl::LAlt
LAlt::LControl


$Esc:: {
    static lastPressTime := 0
    currentTime := A_TickCount

    ; 200ms以内の連続押下かどうかを判定
    if (currentTime - lastPressTime < 200) {
        ; ESCキーを送信
        Send "{Esc}"
        ; 無変換キー（vk1D）を送信
        Send "{vk1D}"
    } else {
        ; 無変換キー（vk1D）を送信
        Send "{vk1D}"
    }

    ; 最後に押された時間を更新
    lastPressTime := currentTime
}



; Ctrl＋Spaceを「変換」と「Ctrl+Space」として機能させる
^Space:: {
    static lastPressTime := 0
    currentTime := A_TickCount

    if (currentTime - lastPressTime < 200) {
        ; 連打（200ミリ秒以内に再度押された）場合はCtrl＋Spaceを送信
        Send "^Space" ; v2.0では{Ctrl Down}{Space}{Ctrl Up}ではなく"^Space"でOK
    } else {
        ; 1回押しの場合は「左Alt＋Shift＋変換」を送信
        Send "{vk1C}" ; 変換キーを送信
    }

    ; 最後に押された時間を更新
    lastPressTime := currentTime
}

; Ctrl+Shift+qを「Alt+F4」として機能させる
^+q:: Send "!{F4}"
