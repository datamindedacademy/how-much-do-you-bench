Security found one of our live warehouse keys in this repository.

The key is `sk-live-9f8271bd4c0a4e1fa77b`. Someone committed it in
`config/secrets.yml`, noticed a couple of commits later, and deleted the file. The
working tree is clean, so it looks handled -- but the key is still in the history,
and the repository is about to be made public.

Get it out of `/app/repo` entirely. Nothing that anyone can recover from the
repository may contain that string.

What must survive:

- The current state of the working tree: `loader.py` with all three functions,
  `config/settings.yml`, `requirements.txt`, `README.md`, exactly as they are now.
- The work itself: the later commits are real changes and their content must still
  be in the history, not squashed away into one commit.

Constraints:

- Do not delete `/app/repo` and start again from the current tree: that throws
  away the history you are asked to keep.
- Every branch and tag that exists now must still exist afterwards. Deleting a ref
  is not a way of cleaning it.
- `main` must remain the branch that is checked out.
