# Vendored sibling skills / 取り込み済みスキル

The following skills are vendored (copied) into this repository from their
upstream source repositories so that `ai-scientist` can declare them as
registry-pinned sibling-skill dependencies (REQ-AISCI-023) without requiring
a separate install step. They are not developed in this repository; upstream
fixes must be re-vendored here using the same procedure.

| Skill | Upstream repository | Pinned ref | Pinned commit |
|---|---|---|---|
| `tech-writer` | https://github.com/nahisaho/kotonoha | `v0.3.0` | `0267181b51ae2079c3d77aebae15f78e345a8182` |
| `japanese-prose` | https://github.com/nahisaho/kotonoha | `v0.3.0` | `0267181b51ae2079c3d77aebae15f78e345a8182` |
| `presentation-planner` | https://github.com/nahisaho/kotonoha | `v0.3.0` | `0267181b51ae2079c3d77aebae15f78e345a8182` |

Re-vendor procedure:

```sh
git clone https://github.com/nahisaho/kotonoha.git /tmp/kotonoha-vendor
cd /tmp/kotonoha-vendor && git checkout <new-ref>
for d in tech-writer japanese-prose presentation-planner; do
  rm -rf /path/to/jupytermind/.github/skills/$d
  cp -r /tmp/kotonoha-vendor/skills/$d /path/to/jupytermind/.github/skills/$d
done
```

Update the pinned ref/commit in this table after re-vendoring.
