# Forgejo
[Forgejo](https://forgejo.org/) is a community-driven fork of Gitea that is
the perfect Git service for homelabs. I don't use any kind of Git workflows
outside of GitHub, but I like to mirror my repositories locally as a backup.
Combined with [Gickup](https://gickup.dev/), I'm able to automatically mirror
repositories from GitHub to Forgejo.

### Can't Forgejo/Gitea automatically mirror GitHub repositories?
Yes, but they can't *discover* repositories, I need to manually add them to
the service and configure them as a mirror. Gickup does this by scanning the
GitHub API for repositories that I own and then automatically creating the
mirrors in Forgejo. This is a lot more convenient than having to manually add
each repository.

### Setup
- Forgejo is running through their Helm chart, configured with OIDC
- Gickup runs as a `CronJob`, only discovering new repositories every 3 hours
