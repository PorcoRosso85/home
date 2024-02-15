# staging
git status --ignored
git rm -r [files]

git reset HEAD^

# committing
git reset --soft [destination]

python3.11 -m pip

docker image rm
docker container ls -a
docker container rm
docker system purge

docker run -it --rm --name="draw" -p 8080:8080 -p 8443:8443 jgraph/drawio
docker run -ti --rm -v ~/.ssh:$HOME/.ssh -v ~/.aws:$HOME/.aws -v $(pwd):/apps -w /apps alpine/ansible ansible
docker run -it --rm --user "$(id -u):$(id -g)" -v "$PWD":/usr/src/app -w /usr/src/app django django-admin.py startproject 
docker start
docker run -ti --rm -v ~/.ssh:$HOME/.ssh -v ~/.aws:$HOME/.aws -v $(pwd):/apps -w /apps alpine/ansible ansible-playbook
python3 -m venv venv
source venv/bin/activate
source $HOME/.zshrc
apt clean && apt update
nvim $HOME/.profile_common
ansible-playbook -i inventory.yml playbook.yml -vvvv
aws cloudformation create-stack --stack-name
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
exercism submit 
python -m pytest 
fzf --preview 'bat --style=numbers --color=always --line-range :500 {}'
aws cloudformation delete-stack --stack-name ${STACK_NAME}
aws cloudformation create-stack --stack-name $STACK_NAME --template-body $VPC_TEMPLATE_PATH
aws cloudformation validate-template --template-body $VPC_TEMPLATE_PATH
docker container commit
git clone -b [branch]
docker commit # avoid/ignore dir
docker push

$ aws --profile stg_yonekawa --region us-west-1 logs tail --since 60m --follow /aws/lambda/csdx-dev-api 2>&1 | tee csdx-dev-$(date +%Y%m%d-%H%M%S).log
# CloudWatch Logsに流れているログをずっとtailして、ついでにファイルに書くやつ

$ aws --profile stg_yonekawa --region ap-northeast-1 logs tail --since 60m --follow /aws/lambda/csdx-stg-api 2>&1 | tee csdx-stg-$(date +%Y%m%d-%H%M%S).log
# CloudWatch Logsに流れているログをずっとtailして、ついでにファイルに書く、stg用
docker image ls
docker container commit dev01 porcorosso85/dev

docker
docker
docker push porcorosso85/dev
cd $HOME/mount/project/
cd /workspaces/CookSuntoryServer/
export DISPLAY=:0
xhost +
systemctl status xorg


ps -ef | grep Xorg
ls -l /dev/tty
apt autoremove && apt system prune
git remote add origin git@github.com:PorcoRosso85/JournalLog.git
docker run --volume $PWD:$HOME --name 01nixos -it nixos/nix bash
docker run --volume $PWD:$HOME --name 01nixos -it nixos/nix bash
docker run --volume /var/run/docker.sock:/var/run/docker.sock --volume $PWD:$HOME --name 03nixos -it nixos/nix bash
ff . $HOME/Documents/dev/ echos
docker run --rm -it -v $(pwd):/work jauderho/visidata:latest __
source $HOME/Documents/dev/project/python_venv/.env/bin/activate
nvim /workspaces/CookSuntoryServer/tmp/echos
cp -rf /workspaces/CookSuntoryServer/tmp $HOME/Documents/dev/
sh sync.sh /workspaces/CookSuntoryServer/tmp2
nix-env -if $HOME/Documents/dev/project/nix_dir/02init.nix

python ~/.extension/python/git.py
nix-env -if $HOME/mount/project/nix_dir/04init.nix
nix-env -e nixpkgs.
cd $HOME/mount/project/nix_dir/
docker commit n01 porcorosso85/nix01
nix-collect-garbage -d
