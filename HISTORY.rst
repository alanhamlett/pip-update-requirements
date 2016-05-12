
History
-------


3.0.3 (2016-05-12)
++++++++++++++++++

- Fix bug where SSL cert verification failed because requests cert file not
  included in distribution.


3.0.2 (2016-05-11)
++++++++++++++++++

- New --force option to update packages even when a package has no version
  specified in the input requirements.txt file.
- Bundle pip to prevent overwriting system pip.


3.0.1 (2016-05-10)
++++++++++++++++++

- Fix usage example in readme.


3.0.0 (2016-05-10)
++++++++++++++++++

- Using -r or --requirement option for input requirements.txt file to be more
  like pip.
- New --skip option to prevent packages from being updated.


2.0.6 (2016-05-10)
++++++++++++++++++

- Default to using requirements.txt file in current folder if one is not
  specified.
- New --nonzero-exit-code option to change the exit code from zero on success
  to 10 when no packages updated and 11 when some packages were updated.


2.0.5 (2016-05-09)
++++++++++++++++++

- Fix to preserve comments.


2.0.4 (2016-05-09)
++++++++++++++++++

- Support for git+git url schemes.


2.0.3 (2016-05-09)
++++++++++++++++++

- Fix installation from pypi.


2.0.0 (2016-05-09)
++++++++++++++++++

- Fix cli entry point.


1.0.1 (2016-05-09)
++++++++++++++++++

- Fix animated cat gif on pypi.


1.0.0 (2016-05-09)
++++++++++++++++++

- Birth.
