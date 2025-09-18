{
  description = "Successful React 19 SSR deployment reference for Cloudflare Workers";
  goal = [
    "Provide proven deployment configuration for React 19 + Cloudflare Workers"
    "Serve as reference implementation with verified success factors"
    "Enable developers to replicate successful deployment patterns"
    "Demonstrate optimal bundle size (25KB) and performance (10ms startup)"
  ];
  nonGoal = [
    "Complex feature development"
    "Backend service integration"
    "Advanced state management"
    "Multi-environment configuration beyond basic dev/prod"
  ];
  meta = {
    owner = [ "@project-maintainers" ];
    lifecycle = "stable";
  };
  output = {
    packages = [ "react-ssr-worker" ];
    apps = [ "deploy" "dev-worker-remote" "test" ];
    modules = [ ];
    overlays = [ ];
    devShells = [ "default" ];
  };
  usage = {
    quickStart = "nix run .#deploy";
    development = [
      "nix develop"
      "npm install"
      "nix run .#dev-worker-remote"
    ];
  };
  features = [
    "React 19 SSR on Cloudflare Workers"
    "Minimal bundle size optimization (25KB)"
    "Direct HTML string rendering (no renderToString complications)"
    "Proven deployment configuration"
  ];
  techStack = [
    "React 19.0.0"
    "Node.js 22"
    "Cloudflare Workers"
    "Vite build system"
    "Nix Flake management"
  ];
}