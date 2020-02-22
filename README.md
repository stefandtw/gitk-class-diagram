gitk-class-diagram
==================

Extends gitk to show a class diagram based on all files that were modified in a given commit, highlighting any changes.

![java](https://user-images.githubusercontent.com/1097029/72220334-f22dd580-354f-11ea-8f14-5f70c065972e.png)*gitk showing some Java classes from [mockito](https://github.com/mockito/mockito)*

![c](https://user-images.githubusercontent.com/1097029/72220351-1984a280-3550-11ea-9e0c-552da0af854e.png)*C may not have classes, but putting together structs, enums, and functions per file can still make a useful diagram ([htop](https://github.com/hishamhm/htop))*

![python](https://user-images.githubusercontent.com/1097029/72220353-230e0a80-3550-11ea-8ede-8215c55ae474.png)*Python: comparing two minor releases of [flake8](https://gitlab.com/pycqa/flake8)*

Usage
-----

* Whenever you select a commit, a class diagram is created and displayed on the bottom right
* The diagram can also span multiple commits if you compare two revisions
* If you exclude files with gitk's filter, they will not appear in the diagram either

Interaction
-----------

* Left-click on a class to scroll to its file in gitk's diff view
* Left-click on any text in the diagram to search for it in gitk's diff view
* Options if the image is too big:
  * Use the mouse wheel to zoom out
  * Hold the left mouse button to move around
  * Right-click and select "Open PNG"

Visual aspects
--------------

* Red background indicates a removed file, class, attribute, operation, relationship
* Green background indicates an added file, class, attribute, operation, relationship
* Light blue background indicates a changed operation
* A dashed border indicates that the element is not a real class, but rather the global scope of a file
* If a file contains multiple classes, they are clustered within a dotted border
* A blue border indicates the file that is currently shown in gitk's diff view

Language support
----------------

How well a language works depends on its support in universal-ctags. See:

```
ctags --list-languages
ctags --list-kinds-full=<language>
```

List of what is recognized in popular languages:

* **Python** — classes, functions, inheritance, function body changes, references to imported files and classes
* **Java** — classes, functions, inheritance, function body changes, references to imported classes of other packages
* **C** — structs, functions, attribute types, function body changes, references to included files
* **Ruby** — classes, functions
* **JavaScript** — classes, functions
* **C++** — most classes are not recognized (ctags provides tags, but gitk-class-diagram does not handle them well enough)
* **Go** — structs, functions, attribute types

How to get more associations between classes
--------------------------------------------

Put a file like [classref.ctags](doc/classref.ctags) in *$HOME/.ctags.d/* to produce associations based on regular expressions. The example file will instruct ctags to record any words in Java source code starting with an upper-case letter (and containing lower-case letters). These words will automatically be interpreted as references to other classes. This works pretty well with some languages. Of course, it's not as reliable as a parser that understands the language. It's also slower.

How to add your own language
----------------------------

Use ctags' optlib and create the tag kinds `class`, `field` and `function`.

Installation
------------

```
pip install gitk-class-diagram
```

Your existing gitk binary remains as it is. Start the extended version with:

```
gitk-cl
```

Dependencies
------------

* [graphviz](https://www.graphviz.org/)
* [universal-ctags](https://ctags.io/)
* python >= 3.7

If you are on Windows, make sure that graphviz, python and ctags are in your PATH.

Configuration
-------------

Open gitk's preferences dialog. At the bottom there is an input field which accepts python code. Copy any settings from [config.py](classdiff/config.py) in there and change the values.

Unfortunately, due to gitk's saving mechanism, the configuration is lost every time you start the original gitk without the extension.

