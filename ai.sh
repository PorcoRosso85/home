source $HOME/secret.sh

read_files=(
)
read_options=""
for file in "${read_files[@]}"; do
  read_options+="-f ${file} "
done


edit_files=(
  ./.bashrc
)
edit_options=""
for file in "${edit_files[@]}"; do
  edit_options+="-f ${file} "
done

prompts=(
  あなたはソフトウェアのエキスパートであり, 
  特に指定がない限り回答は端的に日本語で行うこと, 
)
prompt=""
for p in "${prompts[@]}"; do
  prompt+="${p}"
done

prompt="--prompt ${prompt}"

AICHAT_PLATFORM=gemini aichat \
  --model gemini:gemini-2.0-flash-thinking-exp \
  ${prompt} \
  ${read_options} \
  ${edit_options} \
  "$@"
