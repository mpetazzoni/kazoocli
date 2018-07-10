# Command-line ZooKeeper client

A rich, interactive command-line client for ZooKeeper written in Python,
using the Kazoo library. Features command history, command completion
and path completion and offers a Unix filesystem-like navigation into
the zNode tree.

## Installation

```
$ pip install --upgrade git+https://github.com/mpetazzoni/kazoocli
```

## Usage

```
$ kz <server>
Connecting to <server>:2181...
Connected; server <server>:2181 has version 3.4.6 and reports imok.
/> help
cat: Display the contents of a zNode.
cd: Enter the given zNode.
connect: Connect to the current server, or to a new server.
disconnect: Disconnect from the current server.
exit: Exit the program.
get: Display the contents of a zNode.
help: Get help.
hex: Display the contents of a zNode as an hexadecimal dump.
ls: Lists zNodes under the current zNode.
lsr: Recursively display zNodes under the current zNode.
mkdir: Create an empty zNode.
quit: Exit the program.
rm: Remove a zNode.
rmr: Recursively remove a zNode and all of its children.
set: Set (or create) a zNode to the given value.
stat: Display information about a Znode.
state: Show the current connection state.
/> help -h
Get help.

Usage: help [command]

When invoked without arguments, displays a list of all available
commands. When a command is given as an argument, detailed help for
this command is shown instead.
/> ls
zookeeper/...
> cd zookeeper
/zookeeper> stat
created : Thu May 21 22:11:21 2015 UTC
modified: Thu May 21 22:11:21 2015 UTC
children: 1
```

## JSON values

Kazoocli automatically recognizes JSON dictionary values and can
pretty-print them. By default, `get` will display a compact JSON
representation. Passing a non-empty second argument to `get` will make
it pretty-print with indentation. Alternatively, `pget` will default to
pretty-printing. Both commands always sort the keys alphabetically.

```
/> set test '{"foo":"bar","animal":"dog"}'
/> get test
{"animal":"dog","foo":"bar"}
/> get test true
{
  "animal": "dog",
  "foo": "bar"
}
/> pget test
{
  "animal": "dog",
  "foo": "bar"
}
```
