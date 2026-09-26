# Automatic publication from main

The existing `j2s-deploy.timer` polls main every two minutes. On a new commit,
`site/deploy.sh` fetches main, installs changed build dependencies, builds the site
in staging, then publishes the completed output. GitHub verification results are
not consulted. Content/link checks are available manually and do not gate publishing.
The automatic Repository verification workflow has been removed.

An existing `site/out` directory is adopted automatically: it is retained under
`.releases/legacy-*` and replaced by the new release pointer. No manual migration,
maintenance approval, or deletion of the existing website is required. This first
adoption uses two renames, so the path can be briefly absent between them.
Subsequent updates switch the symlink in one rename. Failure during the switch
restores the previous release. A failed build leaves the live website unchanged.

Server-local tracked and untracked changes are saved in a local git stash before
checking out main, rather than blocking the deployment or discarding the changes.
Ignored build output and dependencies stay in place. The publication branch is main.

Every release includes `/version.json` containing the published commit SHA.
The normal HTML cache policy requests revalidation. To identify the published
version, fetch that endpoint rather than inferring deployment from a CI email.

Manual server command, if the timer needs restarting or immediate execution:

```bash
systemctl --user start j2s-deploy.service
journalctl --user -u j2s-deploy.service -n 40 --no-pager
```

The newest ten releases remain available for rollback and fingerprinted assets
(`J2S_KEEP_RELEASES` changes the number). Older ones are removed after each
successful publication, never the release that was live just before it, so a
hand rollback to an old release survives the next deploy. Until 2026-09-26 every
release was kept; they share almost no bytes, and 46 of them (3.5 GB) filled the
box's disk to 93%. A failure to remove one is logged and does not fail the
publication. The only publication prerequisites are a successful build, a usable
output directory and working filesystem operations.
