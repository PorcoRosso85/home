command! -nargs=0 -range AI <line1>,<line2>call AI()
function! AI() range
    " ファイルタイプの読み替え設定を好みで
    let lang_name = {
                \ "sh": "bash",
                \ "tf": "terraform",
                \ }
    let lines = getline(a:firstline, a:lastline)
    if has_key(lang_name, &ft)
        let question = join([ lang_name[&ft] .. "で" ] + lines, "")
    else
        let question = join([ &ft .. "で" ] + lines, "")
    endif
    echomsg "to openai: " .. question
    " 上記スクリプトを置いたパスに変更
    let result = systemlist("$HOME/.config/nvim/openai.mjs", question)
    call append(a:lastline, result)
    execute(a:firstline .. "," .. a:lastline .. "delete")
endfunction
