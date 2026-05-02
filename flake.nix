{
  description = "JECT infrastructure environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = {
    self,
    nixpkgs,
  }: let
    supportedSystems = ["x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin"];
    forEachSupportedSystem = f:
      nixpkgs.lib.genAttrs supportedSystems (system:
        f {
          pkgs = import nixpkgs {inherit system;};
        });
  in {
    devShells = forEachSupportedSystem ({pkgs}: {
      default = pkgs.mkShell {
        shellHook = ''
          export KUBECONFIG="$PWD/kubeconfig"
        '';
        packages = with pkgs; let
          kseal = python3Packages.buildPythonApplication rec {
            pname = "kseal";
            version = "2.0.2";
            pyproject = true;
            src = fetchFromGitHub {
              owner = "eznix86";
              repo = "kseal";
              rev = "v${version}";
              sha256 = "09v9vcy2qh6dczz8k0fbmj3hkb5p7p1b9wkilrvisv86wy1ydaaf";
            };
            nativeBuildInputs = with python3Packages; [
              hatchling
            ];
            propagatedBuildInputs = with python3Packages; [
              click
              httpx
              kubernetes
              packaging
              pydantic
              rich
              ruamel-yaml
            ];
            # Pas de tests dans le repo github pour cette version
            doCheck = false;
          };
        in [
          (wrapHelm kubernetes-helm {
            plugins = with pkgs.kubernetes-helmPlugins; [
              helm-diff
              helm-git
              helm-secrets
              helm-s3
            ];
          })
          helmfile
          kubectl
          kubectl-cnpg
          cmctl
          k9s
          k3s
          kubectx
          stern
          python3
          kubeseal
          argocd
          kseal
        ];
      };
    });
  };
}
