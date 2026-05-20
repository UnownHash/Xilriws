{
  description = "Xilriws development shell";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { nixpkgs, ... }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };

      ungoogledChromiumPortable = pkgs.stdenv.mkDerivation {
        pname = "ungoogled-chromium-portable";
        version = "146.0.7680.177-1";

        src = pkgs.fetchurl {
          url = "https://github.com/ungoogled-software/ungoogled-chromium-portablelinux/releases/download/146.0.7680.177-1/ungoogled-chromium-146.0.7680.177-1-x86_64_linux.tar.xz";
          hash = "sha256-+Jya5ixEZWm//4qplU5PF8uG2twnJiYIbCo+Fep5DjY=";
        };

        nativeBuildInputs = with pkgs; [
          autoPatchelfHook
          makeWrapper
        ];

        buildInputs = with pkgs; [
          alsa-lib
          at-spi2-atk
          at-spi2-core
          cairo
          cups
          dbus
          expat
          fontconfig
          freetype
          glib
          gtk3
          libdrm
          libgbm
          libGL
          libx11
          libxcb
          libxcomposite
          libxdamage
          libxext
          libxfixes
          libxkbcommon
          libxrandr
          libxshmfence
          libxtst
          nspr
          nss
          pango
          udev
        ];

        autoPatchelfIgnoreMissingDeps = [
          "libQt5Core.so.5"
          "libQt5Gui.so.5"
          "libQt5Widgets.so.5"
          "libQt6Core.so.6"
          "libQt6Gui.so.6"
          "libQt6Widgets.so.6"
        ];

        installPhase = ''
          runHook preInstall

          mkdir -p $out/opt/ungoogled-chromium
          cp -r ./* $out/opt/ungoogled-chromium/

          mkdir -p $out/bin
          makeWrapper $out/opt/ungoogled-chromium/chrome $out/bin/ungoogled-chromium \
            --set CHROME_DEVEL_SANDBOX ""

          runHook postInstall
        '';
      };
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        packages = with pkgs; [
          python312
          uv
          ungoogledChromiumPortable
        ];

        shellHook = ''
          export CHROME_PATH=${ungoogledChromiumPortable}/bin/ungoogled-chromium
        '';
      };
    };
}
