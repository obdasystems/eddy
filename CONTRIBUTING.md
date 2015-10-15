# How to contribute

Third party patches are essential to keep Open Source projects great! There are a few guidelines that we need 
contributors to follow so that we can have a chance of keeping this project as clean and organized as possible.

****************

## Contributing Issues

Issues submitted on Github must be technically documented with the aim that any contributor trying to fix your issue 
should have enough information to understand and reproduce the issue and validate the fix.

* Make sure you have a [GitHub account](https://github.com/signup/free).
* Search for a **similar issue**: duplicating an issue is slower for both parties so search through open 
  and closed issues to see if what you’re running into has been addressed already.
* **Clearly** describe the issue including:
    * Steps to reproduce.
    * Expected results.
    * Actual results.
* **Submit** your issue, assuming one does not already exist.
* Make sure you specify your **system details** when submitting an issue.
* Make sure you fill in the earliest version number of GrapholEd that you know has the issue.

## Contributing Code

We prefer contributors to submit their code change throught GitHub [pull requests](http://help.github.com/send-pull-requests/). 

* Make sure you have a [GitHub account](https://github.com/signup/free).
* [Fork](https://github.com/danielepantaleone/grapholed) this repository on GitHub.
* Create a topic branch from where you want to base your work.
    * This is **NOT** the `master` branch. You should push your changes to a `release` branch. 
    * Please avoid working directly on the `master` branch.
* Make sure your code follows our [coding style](#coding-style)
* Make commits of logical units.
* Make sure your commit messages are in the **proper format** (example below): 
```
   widgets: this commit is meant to fix an issue in a widget

   You can put a description of the changes being carried by the commit in the body of the 
   commit message while keeping the first line of the commit message as short as possible. 
   The first line is a real life imperative statement which may contain the link to the 
   issue being fixed by the commit. The body describes the behavior without the patch, why 
   this is a problem, and how the patch fixes the problem when applied.
```
* Make sure you have added all the necessary **tests** for your changes.
* Make sure that all the **provided tests** pass before sending a pull request.
* **Squash** multiple trivial commits into a single commit.

# Submitting Your Changes

* **Push** your changes to a **topic branch** in your fork of the repository.
* Submit a **pull request** to the GrapholEd repository.
* **Update the issue** to mark that you have submitted code and are ready for it to be reviewed.
* A pull request should contain a single feature/bugfix. If you need to send **multiple features/bugfixes** please
  use **separate pull requests**.

## Coding Style

Different programmers use to write code in different ways. Without the usage of coding conventions, a project 
source code may become unreadable and eventually not understandable. While GrapholEd doesn't strictly follows 
PEP-8 coding conventions, it is required that your code follows the following guidelines:

* **Break long lines** after `110` characters: PEP-8 enforces a shorter length (72-99 characters), however 
  new screens' resolution allow longer lines to stay visibile without the need of horizontal scrolling.
* Do not indent using `TAB`: use **4 spaces** to indent your code.
* Do not use python built-in names to name your variables.
* **Document** your code (example below):
```python
def myFunc(self, param1, param2):
   """
   Put the description here.
   :type param1: The type of the first parameter (i.e: int, str, bool, ...).
   :type param2: The type of the second parameter (i.e: int, str, bool, ...).
   :param param1: The first parameter.
   :param param2: The second parameter.
   :raise MyError: The exception class if your function may raise an exception.
   :rtype: The return typw of your function (i.e: int, str, bool, ...)
   :return: The return value of your function.
   """"
   ...
```
* Always use `self` for the first argument to instance methods.
* Always use `cls` for the first argument to class methods.
* When catching exceptions, **mention specific exception** whenever possible instead of using only the `except` keyword.
* When you add new python modules remember to place the licensing on the top of the file.
* Last but not least: **comment your code**!

****************

# Additional Resources

* [Bug tracker](https://github.com/danielepantaleone/grapholed/issues)
* [General GitHub documentation](http://help.github.com/)
* [GitHub pull request documentation](http://help.github.com/send-pull-requests/)