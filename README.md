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

## About

Frontpage is a free and open-source publishing platform for independent and autonomous newsrooms by Science & Design, Inc., a 501(c)(3) product development organization.

In the last 20 years, over 36% of small newsrooms have closed [1], and spending on advertising today is roughly the same as it was back in the mid-1970s [2]. As the economics of newsrooms have been shifting, so too have the needs of publishers. The platforms that power these publishers must be resilient and cost-effective, not requiring entire teams just for maintenance, and Frontpage offers journalists a free and open-source platform that can be tailored specifically to the unique needs of their newsrooms.

Built for the needs of Distributed Denial of Secrets, Frontpage is a wellspring of data serving the needs of newsrooms worldwide. Publications from DDoSecrets have been used in stories reported on by Organized Crime and Corruption Reporting Project, 404 Media, The New Republic, Bloomberg, Columbia Journalism Review, Wired, DailyDot, The Intercept, The Guardian, Cyberscoop, The Verge, and more.

Distributed Denial of Secrets is also the largest repository of hacked and leaked data that serves a public interest. What differentiates the work of DDoSecrets is the ethical framework in which the group operates. Over 30% of the data published by the collective is restricted to journalists and researchers, not available to the public because of sensitive data including personally identifiable information.

Among the impactful journalism by Distributed Denial of Secrets is the publication of BlueLeaks [3], exposing police misconduct in the United States, ongoing Russian data leaks totaling over 12 million documents on government operations and the geopolitical landscape [4], and 29 Leaks, a leak of 400GB exposing money laundering across many countries [5].

### References
1. https://apnews.com/article/newspapers-closing-jobs-lost-digital-fa82ebfdefdde058a1cbfaea1a59fb69
2. https://www.pewresearch.org/journalism/fact-sheet/newspapers/
3. https://ddosecrets.com/article/blueleaks
4. https://ddosecrets.com/country/Russian%20Federation
5. https://ddosecrets.com/article/29-leaks
