=======================================
Cecilia5 - the audio processing toolbox
=======================================

.. image:: doc-en/source/images/Cecilia_splash.png
     :align: center

Cecilia is an audio signal processing environment. Cecilia lets you create 
your own GUI (grapher, sliders, toggles, popup menus) using a simple syntax. 
Cecilia comes with many original builtin modules for sound effects and synthesis.

Previously written in tcl/tk, Cecilia (version 4, named Cecilia4) was entirely 
rewritten in Python/wxPython and uses the Csound API for communicating between 
the interface and the audio engine. At this time, version 4.2 is the last 
release of this branch.

Cecilia5 now uses the pyo audio engine created for the Python programming 
language. pyo allows a much more powerfull integration of the audio engine to 
the graphical interface. Since it's a standard python module, there is no need 
to use an API to communicate with the interface.

User documentation
------------------

To consult the user online documentation, go to
`documentation <https://belangeo.github.io/cecilia5/>`_.

Requirements
------------

* Install `Python <https://www.python.org/downloads/>`_ (3.8, 3.9 or 3.10)

The programming language used to code the application.

* Install `Git <https://git-scm.com/downloads>`_

The tool needed to clone Cecilia5 source code (or you can just download a zip of the sources).

* Install dependencies (pyo, wxPython and numpy)

Windows::

    py -3 -m pip install --user pyo wxPython numpy

MacOS::

    python3 -m pip install --user pyo wxPython numpy


Launch the application
----------------------

Open a terminal (a Command Prompt on Windows), go to the `cecilia5` folder, and launch the application.

Windows::

    cd path\to\cecilia5
    py -3 Cecilia5.py

MacOS::

    cd path/to/cecilia5
    python3 Cecilia5.py


Screenshot
----------

.. image:: doc-en/source/images/snapshot.png
     :width: 100%


License
-------

Cecilia5 is licensed under the terms of the GNU General Public License version 3. See the `LICENSE` file for the full license text.
