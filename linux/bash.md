# bash
## get parameters from line command
```bash
#!/bin/bash

showhelp()
{
   # Display Help
   echo "Syntax: -h HOSTEDZONEID -n SUBDOMAIN"
   echo "-h|--help         Show help"
   echo "-n|--name         Name of customer"
   echo "-s|--surname      Surname of customer"
   echo "-v|--verbose      Set verbose mode"
   echo
}

opts=$(getopt -l "help,name:,surname:,verbose" -o "hn:s:v" -a -- "$@")
eval set -- "$opts"

while true
do
case "$1" in
-h|--help) 
    showhelp
    exit 0
    ;;
-n|--name) 
    shift
    name="$1"
    ;;
-s|--surname)
    shift
    surname="$1"
    ;;
-v|--verbose)
    set verbose=1
    ;;
--)
    shift
    break;;
esac
shift
done

if [[ ! -n "$name" || ! -n "$surname" ]]; then
    echo "Wrong parameters."
    exit 1
fi

echo "NAME: $name, SURNAME: $surname"
```
