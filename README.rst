===============================
Porekit
===============================

A pythonic toolkit for working with Oxford Nanopore Data

.. image:: https://readthedocs.org/projects/porekit-python/badge/?version=latest
        :target: https://readthedocs.org/projects/porekit-python/?badge=latest
        :alt: Documentation Status


This is a kit of tools for handling data from Oxford Nanopore Technologies' sequencers,
built for integration into the scientific Python ecosystem, including Jupyter
Notebook.

This library is meant for use both as an interactive toolkit for use in Jupyter
notebooks, as well as custom scripts. In the future a command line tool may be
added as well.

Feature requests and bug reports are wellcome. Please use the github issues.


Notes from original author and maintainer:
    * I am not affiliated with Oxford Nanopore Technologies
    * This work has been done without any "official documentation", and I don't
      even know if there is such a thing
    * The documentation of porekit represents my best guess about how MinION
      sequencing and the file format works. It probably contains many factual
      errors or misinterpretations!
    * For me, porekit is mainly an educational effort to learn about nanopore
      sequencing without having access to it.


Main features
-------------

* Gathering Metadata about reads
    * Use as Pandas DataFrame
    * Export to many different formats
    * Helper functions for custom scripts
* Plots http://porekit-python.readthedocs.org/en/latest/02_Plots.html
    * Read length distribution
    * Channel Occupancy over time
    * reads over time
    * Yield over time
    * template length vs complement length
    * squiggle dots


* Documentation: https://porekit-python.readthedocs.org.

Planned
------------

* Tighter Jupyter integration
    * Interactive squiggle viewer


Credits
---------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
