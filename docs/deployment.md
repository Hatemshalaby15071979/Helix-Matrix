# Deployment

Helix-Matrix is a local, loopback-only tool. It is not a network service: there is
deliberately no public endpoint, no TLS configuration and no remote auth to set up.
"Deployment" means putting a checkout on a machine and running the server from it.

## Run from a checkout

```bash
python3 server/os_server.py
# or, detached with a log:
./scripts/serve.sh
```

## systemd (Linux, auto-start at login)

An example user unit is provided at `deploy/helix-matrix.service`.

```bash
mkdir -p ~/.config/systemd/user
cp deploy/helix-matrix.service ~/.config/systemd/user/
# point WorkingDirectory/ExecStart at your checkout:
sed -i "s|/path/to/helix-matrix|$PWD|" ~/.config/systemd/user/helix-matrix.service
systemctl --user daemon-reload
systemctl --user enable --now helix-matrix
journalctl --user -u helix-matrix -f
```

The unit runs the server in the background and restarts it if it exits. Because the app
binds `127.0.0.1`, it is not reachable from the network even while a unit keeps it alive.

## Desktop entry

A ready `.desktop` file is provided at `deploy/helix-matrix.desktop`.

```bash
mkdir -p ~/.local/share/applications
cp deploy/helix-matrix.desktop ~/.local/share/applications/
# point the Path= line at your checkout if it differs:
sed -i "s|/path/to/helix-matrix|$PWD|" ~/.local/share/applications/helix-matrix.desktop
```

The desktop entry calls `scripts/launch.sh`, which starts the server (leaving an
already-live one alone) and opens the browser.

## Uninstall

```bash
systemctl --user disable --now helix-matrix 2>/dev/null || true
rm ~/.config/systemd/user/helix-matrix.service
rm ~/.local/share/applications/helix-matrix.desktop
# remove the checkout and, if you no longer need your records, learning-records/
```
