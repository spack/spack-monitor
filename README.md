# Spack Monitor

Also referred to as *spackmon*

![docs/images/spackmon-triangle-text-large.gif](docs/images/spackmon-triangle-text-large.gif)

This is the build database for spack, or specifically, a monitoring database
that can be run alongside spack to collect output and error, build specs,
status codes, and other metadata around a build. It can be run with docker-compose
or on Kubernetes. It's original design was intended just for storing entire logs,
and the refactored version here is optimized for running [online machine learning](https://riverml.xyz/latest/)
to be able to classify types of errors.

Read the ⭐️ [documentation](https://spack-monitor.readthedocs.io/) ⭐️ to get started.

## Which version should I use?

 - [1.0.0](https://github.com/spack/spack-monitor/releases/tag/1.0.0) is suggested for before September 2021, before the spec format was changed from json to yaml.
 - [2.0.1](https://github.com/spack/spack-monitor/releases/tag/2.0.1) is for after September 2021, but before the release of any 3.x version (still under development) 
 - *main* (or current) is being worked on for this new version.

## TODO

 - refactor diff/matrix view to be more efficient
 - license strings

## License

 * Free software: Apache License 2.0 or MIT. See the LICENSE files and COPYRIGHT notice files in the root folder, and [AUTHORS](AUTHORS) for a list of contributions and maintainers.
