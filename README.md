# wordcounting
Scripts for extracting (wordcount, date) from a git repository, and plotting the results.

`wordcount.py` assumes the current directory is a git repository tracking some
PDF document (assumed to be called thesis.pdf or main.pdf) and extracts the
wordcount of that document for each commit. It generates a cache (wordcount.json)
so that the document must only be compiled once for each revision.
