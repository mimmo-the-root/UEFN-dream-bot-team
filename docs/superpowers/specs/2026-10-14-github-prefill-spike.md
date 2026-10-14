# Spike: GitHub pre-filled "new file" URL (throwaway answer)

Date: 2026-10-14. Decision: **PREFILL = url** (the fallback issue form is not needed for v1).

- Template: `https://github.com/<owner>/<repo>/new/main?filename=contributions/<genre>/<pattern_id>/<handle>.json&value=<url-encoded JSON>`
- Tested in the built-in browser on this repo (read only, nothing submitted): the editor opened with the JSON already in
  the file body, and the file name field showed the file name. `filename` is documented by GitHub (2012 blog post:
  non-collaborators get a fork + pull request flow); `value` is NOT in the official docs but works today, so it can
  change without notice. Task 5 must keep the fallback in mind (copy-to-clipboard + open the new-file page).
- Not verified: the fork flow with a non-collaborator account (the owner has write access, so he sees the direct
  commit form), and the maximum URL length. A contribution is at most ~700 characters of JSON (about 1.2 KB encoded),
  far below the usual 8 KB limit of URLs; Task 5 asserts the generated URL stays under 3000 characters and refuses
  otherwise.
- Handle placeholder: the creator's handle is unknown to the kit, so the file name uses `<your-handle>` and the
  Action rejects a path whose last segment differs from the PR author (Task 4); the preview tells the creator to
  rename the file to their GitHub handle before proposing.
