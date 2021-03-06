.. _development-documentation:

=============
Documentation
=============

The documentation here is generated by way of sphinx and a few other dependencies.
You can generally cd into the docs folder, install requirements, and then build:

.. ::code-block console

    $ git clone git@github.com:spack/spack-monitor.git
    $ cd spack-monitor/docs
    # create a new Python environment here if desired
    $ pip install -r requirements.txt
    $ make html 
   
After build, the documentation will be in the ``_build/html`` folder. You can
cd to that location and deploy a local webserver to view it:

.. ::code-block console

    $ cd _build/html
    $ python -m http.server 9999
    
    
For the above, you would open to port 9999 to see the rendered docs.
