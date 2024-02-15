docker_service() {
  # Define colors
  RED='\033[0;31m'
  GREEN='\033[0;32m'
  YELLOW='\033[1;33m'
  NC='\033[0m' # No Color
  
  echo -e "${YELLOW}start installing docker service and client${NC}"

  echo -e "${YELLOW}remove old docker${NC}"
  for pkg in docker.io docker-doc docker-compose podman-docker containerd runc; do sudo apt-get remove $pkg; done

  echo -e "${YELLOW}apt-get update, upgrade${NC}"
  sudo apt-get update && sudo apt-get upgrade -y

  echo -e "${YELLOW}install ca-certificates, gnupg${NC}"
  sudo apt-get install ca-certificates curl gnupg

  echo -e "${YELLOW}install -m 0755 -d /etc/apt/keyrings${NC}"
  sudo install -m 0755 -d /etc/apt/keyrings

  echo -e "${YELLOW}install gpg${NC}"
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  sudo chmod a+r /etc/apt/keyrings/docker.gpg
  echo \
    "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

  echo -e "${YELLOW}install binaries${NC}"
  sudo apt-get update
  sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y
  # nix profile install nixpkgs#docker
}

# expose docker port
expose_docker_port() {
  echo -e "${YELLOW}expose docker port${NC}"
  echo -e "${YELLOW}refer https://gist.github.com/sz763/3b0a5909a03bf2c9c5a057d032bd98b7 ${NC}"
  sudo mkdir -p /etc/systemd/system/docker.service.d
  echo -e "[Service]\nExecStart=\nExecStart=/usr/bin/dockerd --host=tcp://0.0.0.0:2375 --host=unix:///var/run/docker.sock" | sudo tee /etc/systemd/system/docker.service.d/override.conf > /dev/null

  echo -e "${YELLOW}restart docker${NC}"
  sudo systemctl daemon-reload
  sudo systemctl restart docker
  
  # # [Service]
  # sudo ufw allow 2375/tcp
  # sudo ufw reload
  
  echo -e "${YELLOW}press ctrl+c${NC}"
}

# permission
permission_docker() {
  echo -e "${YELLOW}add user to docker group${NC}"
  sudo usermod -aG docker $USER
  
  echo -e "${YELLOW}check docker group${NC}"
  grep docker /etc/group

  # echo -e "${YELLOW}reboot${NC}"
  # sudo reboot
}

docker_service
expose_docker_port
permission_docker
