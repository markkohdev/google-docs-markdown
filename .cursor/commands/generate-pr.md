---
description: "Create and submit or update a pull request on GitHub for the current branch. Append DRAFT or REGULAR to skip the draft/regular prompt."
---

# Generate Pull Request

## Context

- Current branch: !`git branch --show-current`
- Current directory: !`pwd`

## Your Task

Create or update a pull request for the current branch. Follow these steps:

### 1. Gather Branch Information

- Get the current branch name: `git branch --show-current`
- Get the default branch (usually `main` or `master`): `git remote show origin | grep "HEAD branch"` or check for `origin/main`/`origin/master`
- Get commit history: `git log <default-branch>..HEAD --oneline`
- Get file statistics: `git diff <default-branch>...HEAD --stat`
- Get full diff: `git diff <default-branch>...HEAD` (to understand changes)

### 2. Check for Existing PR

- Check if a PR already exists for this branch: `gh pr list --head <branch-name> --json number,state,title,url,body,updatedAt`
- If a PR exists, note the PR number and state, and ask the user if they want to:
  - Update the existing title/description
  - Create a new title/description from scratch
  - Abort the process

### 3. Read PR Template

- Read `.cursor/commands/claude_pull_request_template.md` to understand the required format
- Note all sections that need to be filled out

### 4. Analyze Changes

- Review the diff to understand what changed
- Identify:
  - New files created
  - Files modified
  - Files deleted
  - Key features/fixes added
  - Test coverage added
  - Documentation updates
  - Breaking changes (if any)

### 5. Create PR Description

Create a comprehensive PR description following the template format in `.github/pull_request_template.md`

**Description Section:**

- Provide a clear, concise summary of changes
- Use bullet points for major changes
- Include specific details about new features, refactoring, tests, etc.

**Testing Section:**

- Describe tests added/updated
- List test files created/modified
- Note any manual testing performed
- Check the testing checkboxes

**Checklist:**

- Review each item and check if completed
- Add notes for any exceptions or important context

**Additional Notes:**

- Include key implementation details
- Note any dependencies changed
- Mention any important context for reviewers

**PR Generation Tag:**

At the bottom of the PR description, add the following tag (with the correct tool name):

_This PR was generated using the /generate-pr command via <Claude Code/Cursor/> using the `generate-pr` skill._

### 6. Create or Update PR

**If no PR exists:**

- Write the PR description to a temporary file (e.g., `<REPO_ROOT>/.chat-outputs/<CHAT_SESSION_START_DATETIME>/pr_body.md`)
- **Determine draft vs. regular:** Check the user's input for the keywords `DRAFT` or `REGULAR` (case-insensitive). If the user included `DRAFT`, create a draft PR. If the user included `REGULAR`, create a regular PR. If neither keyword was provided, ask the user whether they want a **Pull Request** or a **Draft Pull Request**.
- Create PR:
  - For a regular PR: `gh pr create --title "<descriptive-title>" --body-file pr_body.md --base <default-branch> --head <current-branch>`
  - For a draft PR: `gh pr create --draft --title "<descriptive-title>" --body-file pr_body.md --base <default-branch> --head <current-branch>`
- Verify PR was created: `gh pr view <pr-number> --json title,body --jq '.body' | head -20`
- Clean up temporary file

**If PR already exists:**

- Write the updated PR description to a temporary file
- Update PR: `gh pr edit <pr-number> --body-file pr_body.md` (and `--title` if title was updated)
- **Do not change the draft/non-draft state** of the existing PR—only update the title and body as requested
- Verify PR was updated: `gh pr view <pr-number> --json title,body --jq '.body' | head -20`
- Clean up temporary file

### 7. Provide Summary

- Share the PR URL with the user as a link in markdown format `[PR URL](<PR URL>)`
- Confirm that the description was properly formatted and submitted
- Note any important details about the PR

## Important Notes

- Always use the default branch (usually `master`, not `main`) for comparison
- The PR title should be descriptive and follow conventional commit message style if applicable
- Ensure all checkboxes in the template are properly marked (use `[x]` for checked, `[ ]` for unchecked)
- If commands are stubs or not yet implemented, note this clearly
- Clean up any temporary files created during the process
- Verify the PR was created/updated correctly before completing

## Example PR Title Format

- "fix(my-feature): Fix authentication error handling in API client"
- "refactor(my-feature): Refactor document parsing logic and add tests"
- "feat(my-feature): Add support for XYZ"
- "chore(my-feature): Update dependencies in <component>"
- "docs(my-feature): Update documentation for <component/tool/etc>"
- "test(my-feature): Add tests for <component/tool/etc>"
- etc.
