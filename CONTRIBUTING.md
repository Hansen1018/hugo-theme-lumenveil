# Contributing to Lumenveil

Thanks for using — and improving — [Lumenveil](https://github.com/Hansen1018/hugo-theme-lumenveil). Every report, idea, and PR helps the theme get better.

## 📋 Quick Start

| What you want to do | Where to go |
|---|---|
| Report a bug or regression | 🐛 **Bug Report** form |
| Request a feature | ✨ **Feature Request** form |
| Discuss an idea / design | 💬 **Discussion** form |
| Fix a typo, improve docs | Pull Request (no issue needed) |
| Report a security issue | [GitHub Security Advisories](https://github.com/Hansen1018/hugo-theme-lumenveil/security/advisories/new) — do **not** open a public issue |

## 🐛 Reporting Bugs

Use the 🐛 **Bug Report** form. To get a fast fix:

1. **Search** existing issues for duplicates first.
2. **Upgrade** to the latest release and confirm the bug still happens.
3. Fill in every required dropdown:
   - **Feedback Type** — what kind of bug
   - **Affected Area** — which part of the theme (`layouts/`, `assets/css/`, etc.)
   - **Hugo Version** — exact version from `hugo version`
4. Provide:
   - **Steps to reproduce** — minimal, numbered
   - **Expected vs actual behavior**
   - **Screenshots / browser console / `hugo --logLevel info` output**

Bug reports without a reproduction may be closed with `needs-info` after 14 days.

## ✨ Requesting Features

Use the ✨ **Feature Request** form. A strong request describes:

1. **Problem / use case** — what you're trying to do (not just "I want X")
2. **Proposed solution** — how you imagine it working
3. **Alternatives considered** — and why they're worse

The maintainer may close duplicates, wontfixes, or out-of-scope requests. Don't take it personally — feature scope is what keeps a theme focused.

## 💬 Discussions / Ideas

Use the 💬 **Discussion** form for:

- Design feedback on existing features
- Brainstorming future direction
- Showcasing sites built with Lumenveil
- Roadmap questions

For usage questions ("how do I…"), check the [README](https://github.com/Hansen1018/hugo-theme-lumenveil#readme) first.

## 🏷 Labels

Every issue should carry:

- At least **one `type:*` label** (kind of feedback)
- At least **one `area:*` label** (where in the theme)

Maintainers add `priority:*` during triage:

| Priority | When |
|---|---|
| `priority:high` | Blocks a published feature, security issue, broken install |
| `priority:medium` | Visible defect or significant gap |
| `priority:low` | Minor polish, nice-to-have |

Status labels:

- `needs-info` — waiting on reporter
- `in-progress` — actively being worked on
- `blocked` — depends on something external
- `wontfix` — closed without action
- `duplicate` — already tracked elsewhere

## 🔒 Security

For security vulnerabilities, **do not** open a public issue. Use [GitHub Security Advisories](https://github.com/Hansen1018/hugo-theme-lumenveil/security/advisories/new) or email the maintainer privately. You'll get credit once a fix ships.

## 📦 Code Contributions (PRs)

Small fixes (typos, one-line CSS) don't need an issue. For larger changes:

1. Open an issue first to discuss scope (use 💬 Discussion if unsure).
2. Fork + branch from `main`.
3. Keep changes scoped — **one feature per PR**.
4. Test locally:
   ```bash
   hugo --minify
   # visit the affected page; check mobile + desktop, light + dark
   ```
5. Follow existing style: **2-space indent**, **kebab-case** file names, scoped CSS classes.
6. Update docs / `README.md` / `README.zh.md` if you change public-facing config or front matter.
7. **Use the [PR template](.github/PULL_REQUEST_TEMPLATE.md)** — it covers type, affected area, testing, screenshots, breaking changes, and the pre-submit checklist.
8. Squash commits and reference the issue (`Closes #N`) in the PR body.

### Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/) so history is scannable and `standard-version` / release-please can auto-generate the changelog:

| Prefix | Use for |
|---|---|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation only |
| `style:` | CSS / formatting polish, no logic change |
| `refactor:` | Neither fixes a bug nor adds a feature |
| `perf:` | Performance improvement |
| `test:` | Add or fix tests |
| `chore:` | Tooling, deps, build |
| `ci:` | CI configuration |

Add a scope when it helps: `feat(hero):`, `fix(single):`, `docs(readme):`.

Examples:
```
feat(hero): add aurora opacity setting
fix(single): correct share-button data-* attrs
docs(readme): update screenshot dimensions
chore(deps): bump Hugo to 0.145
```

## 🤝 Code of Conduct

Be kind. Disagree on ideas, not on people. No harassment, no spam, no personal attacks. Maintainers may remove comments or close issues that don't follow these norms.

## 📜 License

By contributing, you agree your contributions are licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) — the same license as the theme.

---

Thanks for helping make Lumenveil better. 🦞
