# Spack Monitoring 

Also referred to as *spackmon*

![docs/images/spackmon-triangle-text-large.gif](docs/images/spackmon-triangle-text-large.gif)

This is the build database for spack, or specifically, a monitoring database
that can be run alongside spack to collect output and error, build specs,
status codes, and other metadata around a build. It's original design will run
with docker-compose (containers), but it could also be installed and run natively
using a hosted database elsewhere, if necessary.

⚠️ *This respository is under development! All is subject to change. Use at your own risk!* ⚠️

## Development Plan

1. Develop the base models for a spec
2. Get a working container orchestration (database and application)
3. Create endpoint for uploading simple spec (akin to cray's)
4. Identify locations in spack where we want to ping the server with an update
5. Create API endpoints for doing so

## License

 * Free software: Apache License

