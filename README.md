# CircuitPython_Atom_helper
small python script as helper for CircuitPython development with Atom under linux

features:
- upload python script as 'main.py'
- upload python script with original name
- upload python script to lib folder
- compile arduino sketch and upload via disc / drive uf2
    - arduino IDE (1.8.19) and arduino-cli supported
    - on `arduino IDE` you have to set the target board in the IDE (then it can be closed..)
    - on `arduino-cli` currently the target board is hardcoded in the script to use esp23s3..
    - there are room for improvements → read target architecture / board from some sort of config file for example...

tested in combination with [Atom Shell Commands Package](https://atom.io/packages/atom-shell-commands)
(example configuration can be found in [example_atom-shell-commands.cson](example_atom-shell-commands.cson))

just works fine with [codium (VSCode)](https://vscodium.com/)
have a look at the [tasks.json](tasks.json) example configuration.

for the arduino upload you need to have auto-mount enabled for the uf2 disc..
