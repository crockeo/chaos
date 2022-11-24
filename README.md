# chaos

`chaos` is a build tool that lets you assemble servers out of many disjoint endpoints.
Instead of coupling the logic of your application with the infrastructure of hosting it,
you can define your endpoints and let `chaos` take care of the rest.
Nice!

## Example

```shell
# clone the repository
git clone https://github.com/crockeo/chaos

# set up a venv
cd chaos
python3.11 -mvenv venv
. ./venv/bin/activate
pip install -r dev_requirements.txt

# two options:
# 1) generate a build dir and run builds yourself
# 2) generate and run a target in one command

# option 1)
python main.py generate --manifest fixtures/manifest.yaml --output-dir gen --language python3.9
cd gen
bazelisk run //:server

# option 2)
python main.py run --manifest fixtures/manifest.yaml --language python3.9
python main.py run --manifest fixtures/manifest.yaml --language python3.10
```

## License

MIT License. See: [LICENSE](/LICENSE).
