# 📰 Frontpage
A self-hosted, privacy-focused publishing platform built for censorship resilience.

![ddos-update](https://github.com/scidsg/frontpage/assets/28545431/c30b0672-ba9b-45c4-8b8c-7c1b45f5f318)

## Features
- Invite-only user registration
- Add download links
  - Primary
  - Magnet
  - Torrent
- Multi-user
- Article types
- Source attribution
- Compose in markdown or plaintext
- Tor integration
- Mobile-ready
- Auto-renewing HTTPS certificates
- Hardened CSP
- Custom nginx logging removes IP address and country code of visitors
- Team page
  - User accounts
  - Upload an avatar, set a bio, and include a personal URL
- Easy global and contextual navigation

## Development

You will need `poetry` to manage the dependencies and the virtual environment.
Run `make run` to launch the app.

## Deployment

- Clone this repo to a server
- `./install.sh` on that server
