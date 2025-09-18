{ pkgs, ... }:
{
  project.name = "poc05";
  
  services.nginx = {
    image.command = [ "${pkgs.nginx}/bin/nginx" "-c" "/etc/nginx/nginx.conf" "-g" "daemon off;" ];
    image.contents = [ pkgs.nginx ];
    service.ports = [ "8080:80" ];
    service.volumes = [ "./nginx.conf:/etc/nginx/nginx.conf:ro" ];
    service.depends_on = [ "app-1" "app-2" ];
    service.restart = "unless-stopped";
  };
  
  services.app-1 = {
    image.command = [ "${pkgs.deno}/bin/deno" "run" "--allow-net" "--allow-env" "/app.ts" ];
    image.contents = [ pkgs.deno ];
    service.volumes = [ "./app.ts:/app.ts:ro" ];
    service.environment = {
      CONTAINER_ID = "app-1";
      PORT = "3001";
    };
    service.expose = [ "3001" ];
    service.restart = "unless-stopped";
    service.healthcheck = {
      test = [ "CMD" "${pkgs.curl}/bin/curl" "-f" "http://localhost:3001/health" ];
      interval = "10s";
      timeout = "5s";
      retries = 3;
      start_period = "30s";
    };
  };
  
  services.app-2 = {
    image.command = [ "${pkgs.deno}/bin/deno" "run" "--allow-net" "--allow-env" "/app.ts" ];
    image.contents = [ pkgs.deno ];
    service.volumes = [ "./app.ts:/app.ts:ro" ];
    service.environment = {
      CONTAINER_ID = "app-2";
      PORT = "3002";
    };
    service.expose = [ "3002" ];
    service.restart = "unless-stopped";
    service.healthcheck = {
      test = [ "CMD" "${pkgs.curl}/bin/curl" "-f" "http://localhost:3002/health" ];
      interval = "10s";
      timeout = "5s";
      retries = 3;
      start_period = "30s";
    };
  };
  
  networks.default = {
    driver = "bridge";
  };
}