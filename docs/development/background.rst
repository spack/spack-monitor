.. _development-background:

====================
Design of the Models
====================

This document provides background information as to the technique that was used
to design the original models.


Early Discussion
================

The first discussion between `vsoch <https://github.com/vsoch>_` and `tgamblin <https://github.com/tgamblin>_`
talked about how spack doesn't currently allow deployment of something it wasn't built with (but it's a 
`work in progress <https://github.com/spack/spack/pull/20262>_`. We'd want to do something called splicing,
or cloning a node spec and then pointing it to a different dependency version, all the while preserving
the provenance. Once this works, we would be able to do combinatorial builds and deployments.
The discussion then moved into how we'd want to be able to put "all this stuff" into a database
with some indexing and query strategy.
On a high level, we want to say:

 - Every graph is a configuration
 - We can query by all dependencies that share dependency, or other parameters for a spec
 - We want to index by, for example, the cray json document

An example query might be:

> Get me all records built with this version of package, deployed with this other version of package.

And it was also noted that eventually we will have database for abi, although
this is another thing entirely. Later discussion with more team members we identified
experiment information that would be important to represent:

 - at least the spec
 - status (success, or failure)
 - the phase it failed
 - errors and warnings
 - parse environment to make models
 - not the prefix, but possibly the hash
 - .spack hidden folder in a package directory (note that if a build fails, we don't get a lot of metadata out.)
 - granularity should be on level of package


For example, for each stage in configure, build, and test, we likely would want to store
a spec,error, output, and possibly repos (or urls to them). For the install component,
if it is successful, we might then have a manifest.

.. ::code-block console

    stage: output, error spec, repos?
    configure: output, error spec, repos?
    build: output, error spec, repos?
    test: output, error spec, repos?
    install: output, error spec, repos? + manifest

An `example script <https://github.com/spack/spack-buildspace-exploration/blob/main/spack_generate_random_specs.py>_`
was provided that shows how to generate a random spec, and we modified this for
the repository here to just save the spec to the filesystem. If you use this script,
you should first have the spack bin on your path so the ``spack-python`` interpreter
can be found. Then run the script providing a library name and output directory. E.g.,

.. ::code-block console

     git clone git@github.com:spack/spack-monitor.git
     cd spack-monitor
     mkdir -p specs
                                     # lib       # outdir
    ./script/generate_random_spec.py singularity specs
    ...
    wont include py-cython due to variant constraint +python
    Success! Saving to /home/vanessa/Desktop/Code/spack-monitor/specs/singularity-3.6.4.json
    
We now have a spec (in json) that can be used to develop the models! The first goal
would be to generate an endpoint that allows for uploading a model into the database.
Once this basic structure is defined, we would want to review the models and discuss:

 - Are the unique constraints appropriate for each model?
 - Is the level of granularity appropriate (e.g., one model == one table, allowing for query)
 - Are the ``ON_DELETE`` actions appropriate? (e.g., if I delete a model that depends on another, what happens?)
 - Are the unique constraints appropriate? (e.g., this is what Django uses to tell if something already exists)
 - Are the CharField lengths appropriate?
 - Do any of the models need a "catch all" extra json field?
