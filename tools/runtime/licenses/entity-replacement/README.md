# Replacement entity inputs

The two source files here are the exact bytes reproduced by GitHub Actions run
40787575362 at revision 691e9bc46dbf47557ac78f2db2d7c8bda9c03c83.
`../../source-lock.json` binds their hashes, their upstream predecessors and the
complete modified Graphviz source tree. The Graphviz version remains 16.1.0.

`inputs.json` records the WHATWG snapshot, the three modern W3C XHTML selectors,
their licenses and the two explicit compatibility adjustments (`lang`/`rang`).
The complete inputs and license texts are preserved in `inputs/`. The generated
data and C header comments preserve the BSD three-clause terms for WHATWG
portions incorporated in source code and W3C software/document 2002 terms for
the selectors, with a dated description of changes. Graphviz's own generator
and other sources retain their original terms.

Builds apply only these two substitutions. Source packages include the modified
Graphviz archive and these replacement inputs; they exclude the original entity
table and the historical HTML 4.01 entity reference snapshots. Source replay
authenticates the logical modified tree, not an upstream hash assigned to new
bytes. The upstream URL/hash continue to identify only the original download.

The Actions evaluation independently regenerates both replacements, compares all
252 names and values and the C declarations against the original, and exercises
the production source export/replay. Candidate workflows still require their
build, package, corpus, offline, recovery and license checks.
