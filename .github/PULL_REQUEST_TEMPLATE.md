## 📝 Description

<!-- 1–3 sentences: what & why. Link the issue it closes: Fixes #N -->

Fixes #

## 🔖 Type of Change

<!-- Pick **one** — delete the rest -->

- [ ] 🐛 Bug fix
- [ ] ✨ New feature
- [ ] 💥 Breaking change
- [ ] 📝 Documentation only
- [ ] 🎨 Style / CSS polish
- [ ] ♻️ Refactor
- [ ] ⚡ Performance
- [ ] 🧪 Test / CI only

## 📍 Affected Area

<!-- Pick all that apply -->

- [ ] `layouts/` (Go templates)
- [ ] `assets/css/`
- [ ] `assets/js/`
- [ ] `static/`
- [ ] `README.md` / `README.zh.md` / `CONTRIBUTING.md`
- [ ] `hugo.toml` / `theme.toml`
- [ ] Front matter / content schema
- [ ] Build / tooling
- [ ] Other: ___

## 🧪 Testing Done

- [ ] `hugo --minify` in `exampleSite/` runs clean
- [ ] Affected pages checked on **desktop** (≥ 1024px)
- [ ] Affected pages checked on **mobile** (≤ 480px)
- [ ] Light + dark mode both verified (if visual change)
- [ ] Browser console is clean (no new errors / warnings)

## 📸 Screenshots

<!-- Required for visual changes; skip if N/A -->

| Before | After |
| --- | --- |
|  |  |

## 📚 Docs Updated?

- [ ] Yes (describe or link)
- [ ] N/A — no public-facing change

## ⚠️ Breaking Changes

- [ ] None
- [ ] Yes — describe migration steps below:

<!-- Users running existing sites must do: -->

## ♿ Accessibility Impact

<!-- Leave "None" unless this PR changes color, focus, keyboard, or screen-reader behavior -->

- [ ] None — no a11y-relevant change
- [ ] Affects color contrast, focus visibility, keyboard navigation, or screen reader semantics
- [ ] Tested with VoiceOver / NVDA / keyboard-only (note result below)

<!-- If "Affects…" is checked, describe what changed and how it was verified. -->

## ✅ Pre-submit Checklist

- [ ] Branch rebased on latest `main` (`git fetch && git rebase origin/main`)
- [ ] Commits are squashed or logically grouped
- [ ] Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/)
- [ ] One concern per PR — no unrelated changes mixed in
- [ ] No formatting churn (whitespace, line endings, file modes)
