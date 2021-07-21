mkdir -p dumps
python ../manage.py dumpdata main.BuildWarning > dumps/build-warning.json
python ../manage.py dumpdata main.BuildError > dumps/build-error.json
python ../manage.py dumpdata main.BuildEvent > dumps/build-event.json
python ../manage.py dumpdata main.Build > dumps/build.json
python ../manage.py dumpdata main.InstallFile > dumps/install-file.json
python ../manage.py dumpdata main.BuildPhase > dumps/build-phase.json
python ../manage.py dumpdata main.Spec > dumps/spec.json
python ../manage.py dumpdata main.BuildEnvironment > dumps/build-environment.json
python ../manage.py dumpdata main.Attribute > dumps/attribute.json
python ../manage.py dumpdata main.EnvironmentVariable > dumps/environment-variable.json
python ../manage.py dumpdata main.Architecture > dumps/architecture.json
python ../manage.py dumpdata main.Compiler > dumps/compiler.json
python ../manage.py dumpdata main.Target > dumps/target.json
python ../manage.py dumpdata main.Dependency > dumps/dependency.json
python ../manage.py dumpdata main.Feature > dumps/feature.json
