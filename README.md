# Spack Monitoring 

Also referred to as *spackmon*

![docs/images/spackmon-triangle-text-large.gif](docs/images/spackmon-triangle-text-large.gif)

This is the build database for spack, or specifically, a monitoring database
that can be run alongside spack to collect output and error, build specs,
status codes, and other metadata around a build. It's original design will run
with docker-compose (containers), but it could also be installed and run natively
using a hosted database elsewhere, if necessary. You can read the [documentation](https://spack-monitor.readthedocs.io/)
to get started, but keep in mind this is under development. 👇️

⚠️ *This respository is under development! All is subject to change. Use at your own risk!* ⚠️

## Next TODO

1. Update spack to include build environment information
2. Create endpoint to accept a new spec, and build environment, should return a build ID
3. Update spack monitor to be able to reference the build id for endpoints instead of spec full_hash
4. Create simple endpoint to retrieve a build_id based on a spec, spack_version, and environment.

5. Develop separate tool to parse libabigail xml
6. Somehow get list of files that are objects generated, send them to Spack Monitor (even if we don't have ABI yet)

## License

 * Free software: Apache License 2.0 or MIT. See the LICENSE files and COPYRIGHT notice files in the root folder, and [AUTHORS](AUTHORS) for a list of contributions and maintainers.
