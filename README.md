# Spack Monitoring 

Also referred to as *spackmon*

![docs/images/spackmon-triangle-text-large.gif](docs/images/spackmon-triangle-text-large.gif)

This is the build database for spack, or specifically, a monitoring database
that can be run alongside spack to collect output and error, build specs,
status codes, and other metadata around a build. It's original design will run
with docker-compose (containers), but it could also be installed and run natively
using a hosted database elsewhere, if necessary. You can read the [documentation](https://spack-monitor.readthedocs.io/)
to get started, but keep in mind this is under development. 👇️

## Which version should I use?

 - [1.0.0](https://github.com/spack/spack-monitor/releases/tag/1.0.0) is suggested for before September 2021, before the spec format was changed from json to yaml.
 - *main* (or current) is required for after September 2021.

## License

 * Free software: Apache License 2.0 or MIT. See the LICENSE files and COPYRIGHT notice files in the root folder, and [AUTHORS](AUTHORS) for a list of contributions and maintainers.
