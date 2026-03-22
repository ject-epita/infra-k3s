{
  description = "Thivillon homelab environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      supportedSystems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forEachSupportedSystem = f: nixpkgs.lib.genAttrs supportedSystems (system: f {
        pkgs = import nixpkgs { inherit system; };
      });
    in
    {
      devShells = forEachSupportedSystem ({ pkgs }: {
        default = pkgs.mkShell {
          shellHook = ''
            export KUBECONFIG="$PWD/kubeconfig"
          '';
          packages = with pkgs; [
            (wrapHelm kubernetes-helm {
              plugins = with pkgs.kubernetes-helmPlugins; [
                helm-diff
                helm-secrets
                helm-s3
              ];
            })
            helmfile
            kubectl
            k9s
	    k3s
            kubectx
            stern
            velero
            python3
          ];
        };
      });
    };
}
