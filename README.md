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
python main.py generate --manifest fixtures/manifest.yaml --out gen
cd gen
bazelisk run //:python3_9_server
bazelisk run //:python3_10_server

# option 2)
python main.py run --manifest fixtures/manifest.yaml --target //:python3_9_server
python main.py run --manifest fixtures/manifest.yaml --target //:python3_10_server
```

## Roadmap

- [x] Proof-of-concept that lets you assemble a server of out many small endpoints.
      Scoped to:
      - Python.
      - A single ASGI server + framework (uvicorn & fastAPI).
- [x] Groundwork to make it scalable across multiple ecosystems.
      Separate codegen into classes which are specialized per-ecosystem.
- [x] Move over to a more scalable templating system (e.g. `jinja2`).
- [x] Improve styling of templates.
- [ ] Move server templating into standard templating.
- [ ] Standardize parameter generation so that it's easier to make sure everything aligns.
- [ ] Make server dependency generation a special case of normal target generation.
- [ ] Proof-of-concept implementation for Golang.
- [ ] Let people plug + play with their ASGI server + framework.
- [ ] Let people plug + play with their Go server + framework.

## License

MIT License. See: [LICENSE](/LICENSE).
