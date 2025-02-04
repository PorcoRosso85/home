source $HOME/secret.sh

read_files=(
)
read_options=""
for file in "${read_files[@]}"; do
  read_options+="-f ${file} "
done


edit_files=(
  ./.bash_profile
  ./.bashrc
  ./_.bashrc
  ./.profile
  ./_.profile
)
edit_options=""
for file in "${edit_files[@]}"; do
  edit_options+="-f ${file} "
done

prompts=(
  あなたはソフトウェアのエキスパートであり
  英語で思考し日本語で回答する
  特に指定がない限り以下のファイル群を参照し端的に回答して
)
prompt=""
for p in "${prompts[@]}"; do
  prompt+="${p}"
done

AICHAT_PLATFORM=gemini aichat \
  --prompt ${prompt} \
  ${read_options} ${edit_options} \
