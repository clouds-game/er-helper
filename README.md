Unpack
=======
1. init submodule: `git submodule update --init --recursive`
2. install dependencies: `pixi install`
3. copy necessary files via scripts: `pixi run python scripts/patch.py`
4. build dotnet library: `dotnet build`
5. edit config file: `cp config.example.toml config.toml`
6. run unpack script: `pixi run python scripts/unpack.py`
