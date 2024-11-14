## virtual env
### how to use *args and **kwargs
```
def sum(*args):
    z = 1
    for num in args:
        z += num
    print(z)

sum(4, 5) => 9
sum(2, 4, 4) => 10
```
```
def print_kwargs(**kwargs):
    for key, value in kwargs.items():
        print("The value of {} is {}".format(key, value))

print_values(name="Nicola", nickname="Babbo Natale")

The value of name is Nicola
The value of nickname is Babbo Natale
```
### get version of libraries when using virtual enviroment
```
ls -d *.dist-info
```
## environment variables
### How to Set and Get Environment Variables in Python
https://able.bio/rhett/how-to-set-and-get-environment-variables-in-python--274rgt5
### Python Env Vars – How to Get an Environment Variable in Python
https://www.freecodecamp.org/news/python-env-vars-how-to-get-an-environment-variable-in-python/
### Python: Get Environment Variables Step-by-Step
https://ioflood.com/blog/python-get-environment-variable/
