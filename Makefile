.PHONY: verify build build-example clean

# Build the bundled exampleSite (used by CI)
build-example:
	cd exampleSite && hugo --minify --logLevel info

# Alias matching PR template 'hugo --minify in exampleSite/'
build: build-example

# Headless verify (light + dark)
verify:
	BASE_URL="http://localhost:1313" python dark-check.py --theme light --out-dir artifacts
	BASE_URL="http://localhost:1313" python dark-check.py --theme dark  --out-dir artifacts

# Regenerate og.png from og.svg (used by gen-og)
og:
	node scripts/gen-og.mjs

# Full local check (requires hugo + running server)
serve: build-example
	cd exampleSite && hugo server

clean:
	rm -rf exampleSite/public exampleSite/resources
