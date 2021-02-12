.. _getting_started-settings:


========
Settings
========

Settings are defined in the settings.yml file, and are automatically populated 
into Spack Monitor.


.. list-table:: Title
   :widths: 25 65 10
   :header-rows: 1

   * - Name
     - Description
     - Default
   * - GOOGLE_ANALYTICS_SITE
     - The url of your website for Google Analytics, if desired
     - None
   * - GOOGLE_ANALYTICS_ID
     - The identifier for Google Analytics, if desired
     - None
   * - TWITTER_USERNAME
     - A Twitter username to link to in the footer.
     - spackpm
   * - GITHUB_REPOSITORY
     - A GitHub repository to link to in the footer
     - https://github.com/spack/spack-monitor
   * - GITHUB_DOCUMENTATION
     - GitHub documentation (or other) to link to in the footer
     - https://spack-monitor.readthedocs.io
   * - USE_SQLITE
     - Use an sqlite database instead of the postgres container (set to non null)
     - true
   * - DISABLE_AUTHENTICATION
     - Don't require the user to provide a token in requests (set to non null)
     - None
   * - ENVIRONMENT
     - The global name for the deployment environment (provided in service info metadata)
     - test
   * - SENDGRID_API_KEY
     - Not in use yet, will allow sending email notifications
     - None
   * - SENDGRID_SENDER_EMAIL
     - Not in use yet, will allow sending email notifications
     - None
   * - DOMAIN_NAME
     - The server domain name, defaults to a localhost address
     - http://127.0.0.1
   * - CACHE_DIR
     - Path to directory to use for cache, defaults to "cache" in root of directory
     - None
   * - API_URL_PREFIX
     - The prefix to use for the API
     - ms1
   * - API_TOKEN_EXPIRES_SECONDS
     - The expiration (in seconds) of an API token granted
     - ms1
   * - AUTH_SERVER
     - Set to non null to define a custom authentication server
     - None
