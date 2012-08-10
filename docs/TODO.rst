****
Todo
****

* Add greater support for resuming from crashes:
  Currently, ``exquires-update`` depends on a backup of your project file to
  determine how to modify the database. If ``exquires-update`` is interrupted,
  the original database file is restored. Version 1.0 will retain the changes
  made to the database file and will be able to resume the update operation.

* Add report output formats:
  Currently, ``exquires-report`` and ``exquires-correlate`` can produce
  plaintext or latex output. Other formats will be added as demand arises.

* Add Kendall's rank correlation:
  Currently, ``exquires-correlate`` produces cross-correlation matrices using
  Spearman's rank correlation. Kendall's rank correlation is more complicated
  than Spearman's rank correlation, but the result is more informative, so it
  will eventually be added.

* Add unit tests:
  Every module should have a unit test written for it. Version 1.0 will
  introduce unit tests.
